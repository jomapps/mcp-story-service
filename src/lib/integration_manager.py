"""Integration service coordinators for Brain, Auto-Movie, and Task services with fail-fast behavior."""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel, ValidationError

from .error_handler import ErrorHandler, ErrorCategory, ErrorSeverity, ErrorContext
from ..models.analysis import AnalysisResult
from ..models.story import StoryData


class ServiceEndpoint(BaseModel):
    """Configuration for external service endpoint."""
    name: str
    base_url: str
    api_key: Optional[str] = None
    timeout_seconds: int = 30
    max_retries: int = 3
    health_check_path: str = "/health"
    enabled: bool = True


class IntegrationConfig(BaseModel):
    """Configuration for service integrations."""
    brain_service: ServiceEndpoint
    auto_movie_service: ServiceEndpoint
    task_service: ServiceEndpoint
    fail_fast: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    batch_size: int = 10
    concurrent_requests: int = 5


class ServiceHealth(BaseModel):
    """Health status of an external service."""
    service_name: str
    is_healthy: bool
    last_check: datetime
    response_time_ms: float
    error_message: Optional[str] = None
    consecutive_failures: int = 0


class IntegrationRequest(BaseModel):
    """Request to external service."""
    service_name: str
    endpoint: str
    method: str = "POST"
    data: Dict[str, Any]
    headers: Dict[str, str] = {}
    timeout: Optional[int] = None


class IntegrationResponse(BaseModel):
    """Response from external service."""
    service_name: str
    endpoint: str
    success: bool
    status_code: int
    data: Dict[str, Any] = {}
    error_message: Optional[str] = None
    response_time_ms: float
    timestamp: datetime


class CircuitBreaker:
    """Circuit breaker for external service calls."""
    
    def __init__(self, failure_threshold: int = 5, timeout_seconds: int = 60):
        """Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout_seconds: Timeout before attempting to close circuit
        """
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "closed"  # closed, open, half_open
        self.logger = logging.getLogger(__name__)
    
    def can_execute(self) -> bool:
        """Check if request can be executed.
        
        Returns:
            True if request can proceed
        """
        if self.state == "closed":
            return True
        
        if self.state == "open":
            if self.last_failure_time:
                time_since_failure = datetime.now() - self.last_failure_time
                if time_since_failure.total_seconds() > self.timeout_seconds:
                    self.state = "half_open"
                    self.logger.info("Circuit breaker moving to half-open state")
                    return True
            return False
        
        # half_open state
        return True
    
    def record_success(self):
        """Record successful execution."""
        if self.state == "half_open":
            self.state = "closed"
            self.failure_count = 0
            self.logger.info("Circuit breaker closed after successful call")
        
        if self.state == "closed":
            self.failure_count = max(0, self.failure_count - 1)
    
    def record_failure(self):
        """Record failed execution."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            self.logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


class ServiceIntegrator:
    """Base class for service integration."""
    
    def __init__(
        self,
        config: ServiceEndpoint,
        error_handler: ErrorHandler,
        circuit_breaker: Optional[CircuitBreaker] = None
    ):
        """Initialize service integrator.
        
        Args:
            config: Service endpoint configuration
            error_handler: Error handler instance
            circuit_breaker: Optional circuit breaker
        """
        self.config = config
        self.error_handler = error_handler
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.logger = logging.getLogger(__name__)
        
        # HTTP client
        self.client = httpx.AsyncClient(
            timeout=config.timeout_seconds,
            headers={"Authorization": f"Bearer {config.api_key}"} if config.api_key else {}
        )
        
        # Health tracking
        self.health_status = ServiceHealth(
            service_name=config.name,
            is_healthy=True,
            last_check=datetime.now(),
            response_time_ms=0.0
        )
    
    async def health_check(self) -> ServiceHealth:
        """Perform health check on service.
        
        Returns:
            Service health status
        """
        start_time = datetime.now()
        
        try:
            if not self.config.enabled:
                self.health_status.is_healthy = False
                self.health_status.error_message = "Service disabled"
                return self.health_status
            
            url = urljoin(self.config.base_url, self.config.health_check_path)
            response = await self.client.get(url, timeout=10)
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            self.health_status.is_healthy = response.status_code == 200
            self.health_status.last_check = datetime.now()
            self.health_status.response_time_ms = response_time
            self.health_status.error_message = None
            self.health_status.consecutive_failures = 0 if self.health_status.is_healthy else self.health_status.consecutive_failures + 1
            
            if self.health_status.is_healthy:
                self.circuit_breaker.record_success()
            else:
                self.circuit_breaker.record_failure()
            
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            self.health_status.is_healthy = False
            self.health_status.last_check = datetime.now()
            self.health_status.response_time_ms = response_time
            self.health_status.error_message = str(e)
            self.health_status.consecutive_failures += 1
            
            self.circuit_breaker.record_failure()
            
            self.error_handler.handle_error(
                error=e,
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.INTEGRATION,
                component=self.config.name,
                operation="health_check"
            )
        
        return self.health_status
    
    async def make_request(self, request: IntegrationRequest) -> IntegrationResponse:
        """Make request to external service.
        
        Args:
            request: Integration request
            
        Returns:
            Integration response
        """
        start_time = datetime.now()
        
        # Check circuit breaker
        if not self.circuit_breaker.can_execute():
            return IntegrationResponse(
                service_name=request.service_name,
                endpoint=request.endpoint,
                success=False,
                status_code=503,
                error_message="Circuit breaker open",
                response_time_ms=0.0,
                timestamp=start_time
            )
        
        try:
            url = urljoin(self.config.base_url, request.endpoint)
            timeout = request.timeout or self.config.timeout_seconds
            
            # Make request based on method
            if request.method.upper() == "GET":
                response = await self.client.get(
                    url,
                    params=request.data,
                    headers=request.headers,
                    timeout=timeout
                )
            elif request.method.upper() == "POST":
                response = await self.client.post(
                    url,
                    json=request.data,
                    headers=request.headers,
                    timeout=timeout
                )
            elif request.method.upper() == "PUT":
                response = await self.client.put(
                    url,
                    json=request.data,
                    headers=request.headers,
                    timeout=timeout
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {request.method}")
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Parse response
            try:
                response_data = response.json() if response.content else {}
            except json.JSONDecodeError:
                response_data = {"raw_response": response.text}
            
            success = 200 <= response.status_code < 300
            
            if success:
                self.circuit_breaker.record_success()
            else:
                self.circuit_breaker.record_failure()
            
            return IntegrationResponse(
                service_name=request.service_name,
                endpoint=request.endpoint,
                success=success,
                status_code=response.status_code,
                data=response_data,
                error_message=None if success else f"HTTP {response.status_code}",
                response_time_ms=response_time,
                timestamp=start_time
            )
            
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            self.circuit_breaker.record_failure()
            
            # Handle error
            self.error_handler.handle_error(
                error=e,
                severity=ErrorSeverity.HIGH,
                category=ErrorCategory.INTEGRATION,
                component=request.service_name,
                operation=f"{request.method} {request.endpoint}"
            )
            
            return IntegrationResponse(
                service_name=request.service_name,
                endpoint=request.endpoint,
                success=False,
                status_code=0,
                error_message=str(e),
                response_time_ms=response_time,
                timestamp=start_time
            )
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


class BrainServiceIntegrator(ServiceIntegrator):
    """Integration with Brain service for semantic analysis."""
    
    async def analyze_story_semantics(
        self,
        story_data: StoryData,
        analysis_type: str = "comprehensive"
    ) -> Optional[Dict[str, Any]]:
        """Analyze story using Brain service.
        
        Args:
            story_data: Story data to analyze
            analysis_type: Type of semantic analysis
            
        Returns:
            Semantic analysis results or None if failed
        """
        request = IntegrationRequest(
            service_name=self.config.name,
            endpoint="/api/analyze/story",
            method="POST",
            data={
                "content": story_data.content,
                "analysis_type": analysis_type,
                "metadata": story_data.metadata
            }
        )
        
        response = await self.make_request(request)
        
        if response.success:
            return response.data
        else:
            self.logger.error(f"Brain service analysis failed: {response.error_message}")
            return None
    
    async def get_semantic_similarity(
        self,
        text1: str,
        text2: str
    ) -> Optional[float]:
        """Get semantic similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0.0 to 1.0) or None if failed
        """
        request = IntegrationRequest(
            service_name=self.config.name,
            endpoint="/api/similarity",
            method="POST",
            data={
                "text1": text1,
                "text2": text2
            }
        )
        
        response = await self.make_request(request)
        
        if response.success and "similarity" in response.data:
            return response.data["similarity"]
        
        return None


class AutoMovieServiceIntegrator(ServiceIntegrator):
    """Integration with Auto-Movie service for visual analysis."""
    
    async def generate_scene_visualization(
        self,
        scene_description: str,
        style_preferences: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """Generate visual representation of a scene.
        
        Args:
            scene_description: Text description of scene
            style_preferences: Visual style preferences
            
        Returns:
            Visualization data or None if failed
        """
        request = IntegrationRequest(
            service_name=self.config.name,
            endpoint="/api/visualize/scene",
            method="POST",
            data={
                "description": scene_description,
                "style": style_preferences or {},
                "format": "metadata"  # Just metadata, not actual images
            }
        )
        
        response = await self.make_request(request)
        
        if response.success:
            return response.data
        
        return None
    
    async def analyze_story_visual_potential(
        self,
        story_data: StoryData
    ) -> Optional[Dict[str, Any]]:
        """Analyze story for visual adaptation potential.
        
        Args:
            story_data: Story data to analyze
            
        Returns:
            Visual potential analysis or None if failed
        """
        request = IntegrationRequest(
            service_name=self.config.name,
            endpoint="/api/analyze/visual-potential",
            method="POST",
            data={
                "content": story_data.content,
                "metadata": story_data.metadata
            }
        )
        
        response = await self.make_request(request)
        
        if response.success:
            return response.data
        
        return None


class TaskServiceIntegrator(ServiceIntegrator):
    """Integration with Task service for workflow management."""
    
    async def create_analysis_task(
        self,
        task_type: str,
        story_data: StoryData,
        priority: str = "normal"
    ) -> Optional[str]:
        """Create analysis task in Task service.
        
        Args:
            task_type: Type of analysis task
            story_data: Story data for analysis
            priority: Task priority
            
        Returns:
            Task ID or None if failed
        """
        request = IntegrationRequest(
            service_name=self.config.name,
            endpoint="/api/tasks",
            method="POST",
            data={
                "type": task_type,
                "priority": priority,
                "payload": {
                    "story_content": story_data.content,
                    "metadata": story_data.metadata
                },
                "service_source": "story_service"
            }
        )
        
        response = await self.make_request(request)
        
        if response.success and "task_id" in response.data:
            return response.data["task_id"]
        
        return None
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of analysis task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task status or None if failed
        """
        request = IntegrationRequest(
            service_name=self.config.name,
            endpoint=f"/api/tasks/{task_id}",
            method="GET",
            data={}
        )
        
        response = await self.make_request(request)
        
        if response.success:
            return response.data
        
        return None


class IntegrationManager:
    """Manages integrations with external services."""
    
    def __init__(self, config: IntegrationConfig, error_handler: ErrorHandler):
        """Initialize integration manager.
        
        Args:
            config: Integration configuration
            error_handler: Error handler instance
        """
        self.config = config
        self.error_handler = error_handler
        self.logger = logging.getLogger(__name__)
        
        # Initialize service integrators
        self.brain_service = BrainServiceIntegrator(
            config.brain_service,
            error_handler,
            CircuitBreaker(config.circuit_breaker_threshold, config.circuit_breaker_timeout)
        )
        
        self.auto_movie_service = AutoMovieServiceIntegrator(
            config.auto_movie_service,
            error_handler,
            CircuitBreaker(config.circuit_breaker_threshold, config.circuit_breaker_timeout)
        )
        
        self.task_service = TaskServiceIntegrator(
            config.task_service,
            error_handler,
            CircuitBreaker(config.circuit_breaker_threshold, config.circuit_breaker_timeout)
        )
        
        self.integrators = {
            "brain": self.brain_service,
            "auto_movie": self.auto_movie_service,
            "task": self.task_service
        }
    
    async def health_check_all(self) -> Dict[str, ServiceHealth]:
        """Perform health checks on all services.
        
        Returns:
            Health status for all services
        """
        health_tasks = {
            name: integrator.health_check()
            for name, integrator in self.integrators.items()
        }
        
        results = await asyncio.gather(*health_tasks.values(), return_exceptions=True)
        
        health_status = {}
        for (name, _), result in zip(health_tasks.items(), results):
            if isinstance(result, Exception):
                health_status[name] = ServiceHealth(
                    service_name=name,
                    is_healthy=False,
                    last_check=datetime.now(),
                    response_time_ms=0.0,
                    error_message=str(result)
                )
            else:
                health_status[name] = result
        
        return health_status
    
    async def enhanced_story_analysis(
        self,
        story_data: StoryData,
        analysis_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Perform enhanced story analysis using multiple services.
        
        Args:
            story_data: Story data to analyze
            analysis_type: Type of analysis to perform
            
        Returns:
            Combined analysis results
        """
        results = {
            "primary_analysis": None,
            "semantic_analysis": None,
            "visual_analysis": None,
            "task_tracking": None,
            "integration_status": {}
        }
        
        # Create tasks for parallel execution
        tasks = []
        
        # Brain service semantic analysis
        if self.config.brain_service.enabled:
            tasks.append(self._safe_brain_analysis(story_data, analysis_type))
        
        # Auto-Movie visual analysis
        if self.config.auto_movie_service.enabled:
            tasks.append(self._safe_visual_analysis(story_data))
        
        # Task service workflow
        if self.config.task_service.enabled:
            tasks.append(self._safe_task_creation(story_data, analysis_type))
        
        # Execute tasks based on fail-fast setting
        if self.config.fail_fast:
            # Fail-fast: stop on first failure
            try:
                task_results = await asyncio.gather(*tasks)
                
                # Assign results
                if len(task_results) >= 1 and self.config.brain_service.enabled:
                    results["semantic_analysis"] = task_results[0]
                
                if len(task_results) >= 2 and self.config.auto_movie_service.enabled:
                    results["visual_analysis"] = task_results[1]
                
                if len(task_results) >= 3 and self.config.task_service.enabled:
                    results["task_tracking"] = task_results[2]
                
            except Exception as e:
                self.error_handler.handle_error(
                    error=e,
                    severity=ErrorSeverity.HIGH,
                    category=ErrorCategory.INTEGRATION,
                    component="integration_manager",
                    operation="enhanced_analysis"
                )
                results["integration_status"]["fail_fast_error"] = str(e)
        
        else:
            # Best-effort: continue despite failures
            task_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results with error handling
            result_index = 0
            
            if self.config.brain_service.enabled:
                if isinstance(task_results[result_index], Exception):
                    results["integration_status"]["brain_error"] = str(task_results[result_index])
                else:
                    results["semantic_analysis"] = task_results[result_index]
                result_index += 1
            
            if self.config.auto_movie_service.enabled:
                if isinstance(task_results[result_index], Exception):
                    results["integration_status"]["auto_movie_error"] = str(task_results[result_index])
                else:
                    results["visual_analysis"] = task_results[result_index]
                result_index += 1
            
            if self.config.task_service.enabled:
                if isinstance(task_results[result_index], Exception):
                    results["integration_status"]["task_error"] = str(task_results[result_index])
                else:
                    results["task_tracking"] = task_results[result_index]
        
        return results
    
    async def _safe_brain_analysis(
        self,
        story_data: StoryData,
        analysis_type: str
    ) -> Optional[Dict[str, Any]]:
        """Safely perform brain service analysis."""
        try:
            return await self.brain_service.analyze_story_semantics(story_data, analysis_type)
        except Exception as e:
            self.logger.error(f"Brain service analysis failed: {e}")
            return None
    
    async def _safe_visual_analysis(
        self,
        story_data: StoryData
    ) -> Optional[Dict[str, Any]]:
        """Safely perform visual analysis."""
        try:
            return await self.auto_movie_service.analyze_story_visual_potential(story_data)
        except Exception as e:
            self.logger.error(f"Visual analysis failed: {e}")
            return None
    
    async def _safe_task_creation(
        self,
        story_data: StoryData,
        analysis_type: str
    ) -> Optional[str]:
        """Safely create analysis task."""
        try:
            return await self.task_service.create_analysis_task(analysis_type, story_data)
        except Exception as e:
            self.logger.error(f"Task creation failed: {e}")
            return None
    
    async def get_integration_stats(self) -> Dict[str, Any]:
        """Get integration statistics and health status.
        
        Returns:
            Integration statistics
        """
        health_status = await self.health_check_all()
        
        stats = {
            "services": {},
            "overall_health": True,
            "enabled_services": 0,
            "healthy_services": 0,
            "circuit_breaker_status": {}
        }
        
        for name, integrator in self.integrators.items():
            service_health = health_status.get(name)
            
            stats["services"][name] = {
                "enabled": integrator.config.enabled,
                "healthy": service_health.is_healthy if service_health else False,
                "response_time_ms": service_health.response_time_ms if service_health else 0,
                "consecutive_failures": service_health.consecutive_failures if service_health else 0,
                "last_check": service_health.last_check.isoformat() if service_health else None
            }
            
            if integrator.config.enabled:
                stats["enabled_services"] += 1
                
                if service_health and service_health.is_healthy:
                    stats["healthy_services"] += 1
                else:
                    stats["overall_health"] = False
            
            # Circuit breaker status
            stats["circuit_breaker_status"][name] = {
                "state": integrator.circuit_breaker.state,
                "failure_count": integrator.circuit_breaker.failure_count,
                "last_failure": integrator.circuit_breaker.last_failure_time.isoformat() if integrator.circuit_breaker.last_failure_time else None
            }
        
        return stats
    
    async def close(self):
        """Close all service integrations."""
        close_tasks = [
            integrator.close() for integrator in self.integrators.values()
        ]
        
        await asyncio.gather(*close_tasks, return_exceptions=True)
        self.logger.info("All service integrations closed")


# Configuration helper
def create_integration_config_from_env() -> IntegrationConfig:
    """Create integration configuration from environment variables.
    
    Returns:
        Integration configuration
    """
    import os
    
    return IntegrationConfig(
        brain_service=ServiceEndpoint(
            name="brain_service",
            base_url=os.getenv("BRAIN_SERVICE_URL", "http://localhost:8001"),
            api_key=os.getenv("BRAIN_SERVICE_API_KEY"),
            enabled=os.getenv("BRAIN_SERVICE_ENABLED", "true").lower() == "true"
        ),
        auto_movie_service=ServiceEndpoint(
            name="auto_movie_service",
            base_url=os.getenv("AUTO_MOVIE_SERVICE_URL", "http://localhost:8002"),
            api_key=os.getenv("AUTO_MOVIE_SERVICE_API_KEY"),
            enabled=os.getenv("AUTO_MOVIE_SERVICE_ENABLED", "true").lower() == "true"
        ),
        task_service=ServiceEndpoint(
            name="task_service",
            base_url=os.getenv("TASK_SERVICE_URL", "http://localhost:8003"),
            api_key=os.getenv("TASK_SERVICE_API_KEY"),
            enabled=os.getenv("TASK_SERVICE_ENABLED", "true").lower() == "true"
        ),
        fail_fast=os.getenv("INTEGRATION_FAIL_FAST", "true").lower() == "true",
        circuit_breaker_threshold=int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "5")),
        circuit_breaker_timeout=int(os.getenv("CIRCUIT_BREAKER_TIMEOUT", "60"))
    )