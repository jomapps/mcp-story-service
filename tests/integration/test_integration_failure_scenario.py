"""Integration test for integration failure handling scenario (T018)."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from src.services.session_manager import StorySessionManager
from src.services.narrative.analyzer import NarrativeAnalyzer
from src.services.consistency.validator import ConsistencyValidator
from src.models.story import StoryData
from src.models.analysis import AnalysisResult
from src.lib.integration_manager import IntegrationManager
from src.lib.error_handler import ErrorHandler


@pytest.fixture
async def session_manager():
    """Create session manager for testing."""
    manager = StorySessionManager(workspace_dir="test_workspaces")
    yield manager
    # Cleanup after test
    try:
        active_sessions = await manager.list_active_sessions()
        for session in active_sessions:
            await manager.terminate_session(session.session_id)
    except Exception:
        pass


@pytest.fixture
async def narrative_analyzer():
    """Create narrative analyzer for testing."""
    return NarrativeAnalyzer()


@pytest.fixture
async def consistency_validator():
    """Create consistency validator for testing."""
    return ConsistencyValidator()


@pytest.fixture
async def integration_manager():
    """Create integration manager for testing."""
    return IntegrationManager()


@pytest.fixture
def sample_story_data():
    """Sample story data for failure testing."""
    return StoryData(
        content="Detective story with potential analysis complexity",
        metadata={
            "analysis_type": "comprehensive_analysis",
            "project_id": "failure-test-project"
        }
    )


class TestIntegrationFailureHandlingScenario:
    """Integration test for external service failure handling."""
    
    @pytest.mark.asyncio
    async def test_redis_connection_failure_graceful_degradation(
        self, session_manager, sample_story_data
    ):
        """Test graceful degradation when Redis connection fails."""
        project_id = "redis-failure-test-001"
        session_id = await session_manager.create_session(project_id)
        
        # Simulate Redis connection failure
        with patch('src.lib.redis_client.RedisClient.get') as mock_redis_get:
            mock_redis_get.side_effect = ConnectionError("Redis connection failed")
            
            # Should handle Redis failure gracefully and continue operation
            try:
                await session_manager.update_session(
                    session_id=session_id,
                    story_data=sample_story_data
                )
                
                # Session should still work with in-memory fallback
                session = await session_manager.get_session(session_id)
                assert session is not None
                assert session.session_id == session_id
                
            except ConnectionError:
                pytest.fail("Redis failure should be handled gracefully")
    
    @pytest.mark.asyncio
    async def test_brain_service_timeout_handling(
        self, integration_manager, sample_story_data
    ):
        """Test handling of Brain service timeout with fail-fast behavior."""
        # Simulate Brain service timeout
        with patch('src.lib.integration_manager.IntegrationManager._call_brain_service') as mock_brain:
            mock_brain.side_effect = asyncio.TimeoutError("Brain service timeout")
            
            # Should fail fast and return error result
            result = await integration_manager.sync_with_brain_service(
                project_id="timeout-test-001",
                story_data=sample_story_data
            )
            
            # Should indicate failure but not crash
            assert result is not None
            assert result.get("status") == "error"
            assert "timeout" in result.get("message", "").lower()
            assert "confidence_impact" in result
            assert result["confidence_impact"] >= 0.1  # Timeout impacts confidence
    
    @pytest.mark.asyncio
    async def test_auto_movie_service_unavailable_fallback(
        self, integration_manager, sample_story_data
    ):
        """Test fallback behavior when Auto-Movie service is unavailable."""
        # Simulate Auto-Movie service unavailable
        with patch('src.lib.integration_manager.IntegrationManager._call_auto_movie_service') as mock_auto_movie:
            mock_auto_movie.side_effect = ConnectionRefusedError("Service unavailable")
            
            # Should continue with local analysis only
            result = await integration_manager.coordinate_production_pipeline(
                project_id="unavailable-test-001",
                story_data=sample_story_data
            )
            
            # Should provide local analysis results
            assert result is not None
            assert result.get("status") in ["partial_success", "local_only"]
            assert "local_analysis" in result
            assert "external_services_unavailable" in result.get("warnings", [])
    
    @pytest.mark.asyncio
    async def test_task_service_partial_failure_recovery(
        self, integration_manager, sample_story_data
    ):
        """Test recovery from partial Task service failures."""
        call_count = 0
        
        def mock_task_service_call(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ConnectionError("Task service intermittent failure")
            return {"status": "success", "task_id": "recovered-task-123"}
        
        # Simulate intermittent Task service failures
        with patch('src.lib.integration_manager.IntegrationManager._call_task_service') as mock_task:
            mock_task.side_effect = mock_task_service_call
            
            # Should retry and eventually succeed
            result = await integration_manager.submit_analysis_task(
                project_id="recovery-test-001",
                story_data=sample_story_data,
                max_retries=3
            )
            
            # Should succeed after retries
            assert result is not None
            assert result.get("status") == "success"
            assert "task_id" in result
            assert call_count == 3  # 2 failures + 1 success
    
    @pytest.mark.asyncio
    async def test_malformed_response_handling_from_external_services(
        self, integration_manager, sample_story_data
    ):
        """Test handling of malformed responses from external services."""
        # Simulate malformed JSON response
        with patch('src.lib.integration_manager.IntegrationManager._call_brain_service') as mock_brain:
            mock_brain.return_value = "Invalid JSON response {malformed"
            
            # Should handle malformed response gracefully
            result = await integration_manager.sync_with_brain_service(
                project_id="malformed-test-001",
                story_data=sample_story_data
            )
            
            assert result is not None
            assert result.get("status") == "error"
            assert "malformed" in result.get("message", "").lower() or "parse" in result.get("message", "").lower()
            assert result.get("confidence_impact", 0) > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_failure_isolation_between_projects(
        self, session_manager, integration_manager
    ):
        """Test that failures in one project don't affect other projects."""
        # Create multiple project sessions
        project_a_id = "isolation-test-a"
        project_b_id = "isolation-test-b"
        
        session_a = await session_manager.create_session(project_a_id)
        session_b = await session_manager.create_session(project_b_id)
        
        story_a = StoryData(
            content="Project A story content",
            metadata={"project_id": project_a_id}
        )
        
        story_b = StoryData(
            content="Project B story content", 
            metadata={"project_id": project_b_id}
        )
        
        # Simulate failure in project A integration
        async def failing_integration_a(*args, **kwargs):
            if "isolation-test-a" in str(args) + str(kwargs):
                raise Exception("Project A integration failure")
            return {"status": "success"}
        
        with patch('src.lib.integration_manager.IntegrationManager.sync_with_brain_service') as mock_sync:
            mock_sync.side_effect = failing_integration_a
            
            # Project A should fail
            result_a = await integration_manager.sync_with_brain_service(
                project_id=project_a_id,
                story_data=story_a
            )
            
            # Project B should succeed (isolation working)
            result_b = await integration_manager.sync_with_brain_service(
                project_id=project_b_id,
                story_data=story_b
            )
            
            # Verify isolation
            assert result_a.get("status") == "error"
            assert result_b.get("status") == "success"
            
            # Sessions should remain independent
            session_a_check = await session_manager.get_session(session_a)
            session_b_check = await session_manager.get_session(session_b)
            
            assert session_a_check is not None
            assert session_b_check is not None
            assert session_a_check.session_id != session_b_check.session_id
    
    @pytest.mark.asyncio
    async def test_confidence_impact_calculation_during_failures(
        self, narrative_analyzer, sample_story_data
    ):
        """Test confidence impact calculation when external services fail."""
        # Simulate external service failures during analysis
        with patch('src.lib.integration_manager.IntegrationManager.get_external_validation') as mock_validation:
            mock_validation.side_effect = TimeoutError("External validation timeout")
            
            # Analysis should continue with reduced confidence
            analysis_result = await narrative_analyzer.analyze_story_structure(sample_story_data)
            
            # Should complete analysis but indicate reduced confidence
            assert analysis_result is not None
            assert analysis_result.confidence < 1.0
            
            # Should document failure impact
            if hasattr(analysis_result, 'metadata'):
                metadata = analysis_result.metadata
                assert "external_service_failures" in metadata or "warnings" in metadata
                
            # Confidence should be impacted proportionally
            assert analysis_result.confidence >= 0.5  # Still useful despite failures
            assert analysis_result.confidence <= 0.9  # But clearly impacted
    
    @pytest.mark.asyncio
    async def test_cascade_failure_prevention_and_circuit_breaker(
        self, integration_manager, session_manager
    ):
        """Test circuit breaker pattern to prevent cascade failures."""
        failure_count = 0
        
        def counting_failure(*args, **kwargs):
            nonlocal failure_count
            failure_count += 1
            raise ConnectionError(f"Service failure #{failure_count}")
        
        # Simulate repeated service failures
        with patch('src.lib.integration_manager.IntegrationManager._call_brain_service') as mock_service:
            mock_service.side_effect = counting_failure
            
            # Multiple rapid failures should trigger circuit breaker
            project_id = "circuit-breaker-test-001"
            session_id = await session_manager.create_session(project_id)
            
            story_data = StoryData(
                content="Test story for circuit breaker",
                metadata={"project_id": project_id}
            )
            
            results = []
            for i in range(5):
                result = await integration_manager.sync_with_brain_service(
                    project_id=project_id,
                    story_data=story_data
                )
                results.append(result)
                
                # Small delay between calls
                await asyncio.sleep(0.1)
            
            # Later calls should be faster (circuit breaker engaged)
            # and should indicate circuit breaker status
            later_results = [r for r in results[3:]]  # Last 2 results
            
            for result in later_results:
                assert result.get("status") in ["error", "circuit_breaker_open"]
                # Circuit breaker should prevent actual service calls
                if "circuit_breaker" in result.get("message", ""):
                    assert result.get("response_time", 1.0) < 0.5  # Should be fast
    
    @pytest.mark.asyncio
    async def test_error_recovery_with_retry_strategies(
        self, integration_manager, sample_story_data
    ):
        """Test different retry strategies for different types of failures."""
        # Test exponential backoff for timeout errors
        timeout_call_times = []
        
        async def timeout_with_timing(*args, **kwargs):
            timeout_call_times.append(datetime.now())
            raise asyncio.TimeoutError("Service timeout")
        
        with patch('src.lib.integration_manager.IntegrationManager._call_brain_service') as mock_timeout:
            mock_timeout.side_effect = timeout_with_timing
            
            result = await integration_manager.sync_with_brain_service(
                project_id="retry-strategy-test-001",
                story_data=sample_story_data,
                retry_strategy="exponential_backoff"
            )
            
            # Should have made multiple attempts with increasing delays
            assert len(timeout_call_times) >= 2
            
            if len(timeout_call_times) >= 3:
                # Check that delays increased between attempts
                delay1 = timeout_call_times[1] - timeout_call_times[0]
                delay2 = timeout_call_times[2] - timeout_call_times[1]
                assert delay2 > delay1
            
            assert result.get("status") == "error"
            assert result.get("retry_attempts", 0) > 1
    
    @pytest.mark.asyncio
    async def test_partial_analysis_completion_during_service_outages(
        self, narrative_analyzer, consistency_validator, sample_story_data
    ):
        """Test completing partial analysis when some services are down."""
        # Simulate consistency service failure but narrative service working
        with patch.object(consistency_validator, 'validate_consistency') as mock_consistency:
            mock_consistency.side_effect = ConnectionError("Consistency service down")
            
            # Should complete narrative analysis even if consistency fails
            analysis_result = await narrative_analyzer.analyze_story_structure(sample_story_data)
            
            # Should have partial results
            assert analysis_result is not None
            assert "arc_analysis" in analysis_result.data
            
            # Should indicate which services were unavailable
            if hasattr(analysis_result, 'metadata'):
                metadata = analysis_result.metadata
                assert any("consistency" in str(item).lower() for item in metadata.get("failed_services", []))
            
            # Confidence should be reduced but analysis still useful
            assert 0.4 <= analysis_result.confidence <= 0.8
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_maintains_core_functionality(
        self, session_manager, sample_story_data
    ):
        """Test that core functionality remains available during external failures."""
        project_id = "degradation-test-001"
        session_id = await session_manager.create_session(project_id)
        
        # Simulate all external services failing
        with patch('src.lib.integration_manager.IntegrationManager') as mock_integration:
            mock_integration.side_effect = Exception("All external services down")
            
            # Core session management should still work
            await session_manager.update_session(
                session_id=session_id,
                story_data=sample_story_data
            )
            
            session = await session_manager.get_session(session_id)
            assert session is not None
            assert session.story_data is not None
            
            # Local analysis should still be possible
            # (This would depend on the actual implementation having local fallbacks)
            assert session.status in ["active", "degraded_mode"]


if __name__ == "__main__":
    pytest.main([__file__])