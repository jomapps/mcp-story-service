"""Error handling and logging configuration with confidence impact tracking."""

import asyncio
import json
import logging
import sys
import traceback
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ErrorCategory(str, Enum):
    """Error categories for classification."""
    ANALYSIS = "analysis"
    VALIDATION = "validation"
    PROCESSING = "processing"
    INTEGRATION = "integration"
    CONFIGURATION = "configuration"
    NETWORK = "network"
    STORAGE = "storage"
    AUTHENTICATION = "authentication"
    PERMISSION = "permission"
    RESOURCE = "resource"
    UNKNOWN = "unknown"


class ConfidenceImpact(BaseModel):
    """Impact of error on confidence scoring."""
    original_confidence: float
    adjusted_confidence: float
    impact_factor: float
    impact_reason: str
    recovery_possible: bool


class ErrorContext(BaseModel):
    """Context information for error tracking."""
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    analysis_type: Optional[str] = None
    component: Optional[str] = None
    operation: Optional[str] = None
    user_data: Dict[str, Any] = {}


class StoryServiceError(BaseModel):
    """Structured error information for story service."""
    error_id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    details: str
    component: str
    operation: Optional[str] = None
    context: Optional[ErrorContext] = None
    confidence_impact: Optional[ConfidenceImpact] = None
    stack_trace: Optional[str] = None
    recovery_actions: List[str] = []
    metadata: Dict[str, Any] = {}


class ErrorHandler:
    """Centralized error handling with confidence impact tracking."""
    
    def __init__(
        self,
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        enable_console: bool = True
    ):
        """Initialize error handler.
        
        Args:
            log_level: Logging level
            log_file: Optional log file path
            enable_console: Enable console logging
        """
        self.log_level = getattr(logging, log_level.upper())
        self.log_file = log_file
        self.enable_console = enable_console
        
        # Error tracking
        self.error_history: List[StoryServiceError] = []
        self.error_counts: Dict[str, int] = {}
        self.confidence_adjustments: Dict[str, List[ConfidenceImpact]] = {}
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Error severity to confidence impact mapping
        self.severity_impact_map = {
            ErrorSeverity.CRITICAL: 0.4,  # 40% confidence reduction
            ErrorSeverity.HIGH: 0.25,     # 25% confidence reduction
            ErrorSeverity.MEDIUM: 0.15,   # 15% confidence reduction
            ErrorSeverity.LOW: 0.05,      # 5% confidence reduction
            ErrorSeverity.INFO: 0.0       # No confidence impact
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration.
        
        Returns:
            Configured logger
        """
        logger = logging.getLogger("story_service")
        logger.setLevel(self.log_level)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        if self.enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # File handler
        if self.log_file:
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def handle_error(
        self,
        error: Exception,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        component: str = "unknown",
        operation: Optional[str] = None,
        context: Optional[ErrorContext] = None,
        original_confidence: Optional[float] = None
    ) -> StoryServiceError:
        """Handle and track an error with confidence impact.
        
        Args:
            error: Exception that occurred
            severity: Error severity level
            category: Error category
            component: Component where error occurred
            operation: Operation being performed
            context: Additional context information
            original_confidence: Original confidence score to adjust
            
        Returns:
            Structured error information
        """
        # Generate error ID
        error_id = f"{category.value}_{component}_{int(datetime.now().timestamp())}"
        
        # Calculate confidence impact
        confidence_impact = None
        if original_confidence is not None:
            confidence_impact = self._calculate_confidence_impact(
                original_confidence, severity, category, str(error)
            )
        
        # Create structured error
        structured_error = StoryServiceError(
            error_id=error_id,
            timestamp=datetime.now(),
            severity=severity,
            category=category,
            message=str(error),
            details=self._extract_error_details(error),
            component=component,
            operation=operation,
            context=context,
            confidence_impact=confidence_impact,
            stack_trace=traceback.format_exc(),
            recovery_actions=self._suggest_recovery_actions(error, category),
            metadata={
                "error_type": type(error).__name__,
                "error_module": getattr(error, "__module__", "unknown")
            }
        )
        
        # Track error
        self._track_error(structured_error)
        
        # Log error
        self._log_error(structured_error)
        
        return structured_error
    
    def handle_validation_error(
        self,
        validation_errors: List[str],
        component: str,
        context: Optional[ErrorContext] = None,
        original_confidence: Optional[float] = None
    ) -> StoryServiceError:
        """Handle validation errors specifically.
        
        Args:
            validation_errors: List of validation error messages
            component: Component where validation failed
            context: Additional context
            original_confidence: Original confidence score
            
        Returns:
            Structured error information
        """
        error_message = f"Validation failed: {'; '.join(validation_errors)}"
        
        # Create mock exception for consistency
        validation_exception = ValueError(error_message)
        
        return self.handle_error(
            error=validation_exception,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.VALIDATION,
            component=component,
            operation="validation",
            context=context,
            original_confidence=original_confidence
        )
    
    def handle_confidence_threshold_failure(
        self,
        actual_confidence: float,
        required_threshold: float,
        analysis_type: str,
        context: Optional[ErrorContext] = None
    ) -> StoryServiceError:
        """Handle confidence threshold failures.
        
        Args:
            actual_confidence: Actual confidence achieved
            required_threshold: Required confidence threshold
            analysis_type: Type of analysis that failed
            context: Additional context
            
        Returns:
            Structured error information
        """
        error_message = (
            f"Confidence threshold not met for {analysis_type}: "
            f"{actual_confidence:.3f} < {required_threshold:.3f}"
        )
        
        threshold_exception = ValueError(error_message)
        
        return self.handle_error(
            error=threshold_exception,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.ANALYSIS,
            component="confidence_validator",
            operation="threshold_check",
            context=context,
            original_confidence=actual_confidence
        )
    
    def _calculate_confidence_impact(
        self,
        original_confidence: float,
        severity: ErrorSeverity,
        category: ErrorCategory,
        error_message: str
    ) -> ConfidenceImpact:
        """Calculate impact of error on confidence score.
        
        Args:
            original_confidence: Original confidence score
            severity: Error severity
            category: Error category
            error_message: Error message
            
        Returns:
            Confidence impact information
        """
        # Base impact from severity
        base_impact = self.severity_impact_map.get(severity, 0.1)
        
        # Category-specific adjustments
        category_multipliers = {
            ErrorCategory.ANALYSIS: 1.2,      # Analysis errors have higher impact
            ErrorCategory.VALIDATION: 1.1,    # Validation errors moderate impact
            ErrorCategory.PROCESSING: 1.0,    # Processing errors standard impact
            ErrorCategory.INTEGRATION: 0.8,   # Integration errors lower impact
            ErrorCategory.CONFIGURATION: 0.6, # Config errors minimal impact
            ErrorCategory.NETWORK: 0.5,       # Network errors minimal impact
            ErrorCategory.STORAGE: 0.5        # Storage errors minimal impact
        }
        
        category_multiplier = category_multipliers.get(category, 1.0)
        
        # Calculate final impact
        impact_factor = base_impact * category_multiplier
        adjusted_confidence = max(original_confidence - impact_factor, 0.0)
        
        # Determine recovery possibility
        recovery_possible = self._assess_recovery_possibility(severity, category, error_message)
        
        return ConfidenceImpact(
            original_confidence=original_confidence,
            adjusted_confidence=adjusted_confidence,
            impact_factor=impact_factor,
            impact_reason=f"{severity.value} {category.value} error",
            recovery_possible=recovery_possible
        )
    
    def _assess_recovery_possibility(
        self,
        severity: ErrorSeverity,
        category: ErrorCategory,
        error_message: str
    ) -> bool:
        """Assess if recovery is possible from this error.
        
        Args:
            severity: Error severity
            category: Error category
            error_message: Error message
            
        Returns:
            True if recovery is likely possible
        """
        # Critical errors are generally not recoverable
        if severity == ErrorSeverity.CRITICAL:
            return False
        
        # Category-based recovery assessment
        recoverable_categories = {
            ErrorCategory.NETWORK,
            ErrorCategory.STORAGE,
            ErrorCategory.CONFIGURATION,
            ErrorCategory.RESOURCE
        }
        
        if category in recoverable_categories:
            return True
        
        # Check for specific recoverable error patterns
        recoverable_patterns = [
            "timeout", "connection", "temporary", "retry", "rate limit"
        ]
        
        error_lower = error_message.lower()
        return any(pattern in error_lower for pattern in recoverable_patterns)
    
    def _extract_error_details(self, error: Exception) -> str:
        """Extract detailed error information.
        
        Args:
            error: Exception to analyze
            
        Returns:
            Detailed error description
        """
        details = [f"Error type: {type(error).__name__}"]
        
        # Add error arguments if available
        if hasattr(error, 'args') and error.args:
            details.append(f"Arguments: {error.args}")
        
        # Add specific attributes for common exception types
        if hasattr(error, 'errno'):
            details.append(f"Error number: {error.errno}")
        
        if hasattr(error, 'filename'):
            details.append(f"Filename: {error.filename}")
        
        if hasattr(error, 'lineno'):
            details.append(f"Line number: {error.lineno}")
        
        return "; ".join(details)
    
    def _suggest_recovery_actions(
        self,
        error: Exception,
        category: ErrorCategory
    ) -> List[str]:
        """Suggest recovery actions based on error type and category.
        
        Args:
            error: Exception that occurred
            category: Error category
            
        Returns:
            List of suggested recovery actions
        """
        actions = []
        error_str = str(error).lower()
        
        # Category-specific recovery actions
        if category == ErrorCategory.NETWORK:
            actions.extend([
                "Check network connectivity",
                "Verify service endpoints",
                "Retry with exponential backoff"
            ])
        
        elif category == ErrorCategory.STORAGE:
            actions.extend([
                "Check storage permissions",
                "Verify disk space",
                "Validate file paths"
            ])
        
        elif category == ErrorCategory.VALIDATION:
            actions.extend([
                "Validate input data format",
                "Check required fields",
                "Review data constraints"
            ])
        
        elif category == ErrorCategory.ANALYSIS:
            actions.extend([
                "Review story content quality",
                "Check confidence thresholds",
                "Consider alternative analysis methods"
            ])
        
        elif category == ErrorCategory.CONFIGURATION:
            actions.extend([
                "Review configuration settings",
                "Check environment variables",
                "Validate configuration file syntax"
            ])
        
        # Pattern-specific recovery actions
        if "timeout" in error_str:
            actions.append("Increase timeout settings")
        
        if "permission" in error_str or "access" in error_str:
            actions.append("Check file/directory permissions")
        
        if "memory" in error_str:
            actions.append("Check available memory and resource limits")
        
        if "connection" in error_str:
            actions.extend([
                "Verify service availability",
                "Check connection parameters"
            ])
        
        return actions or ["Review error details and consult documentation"]
    
    def _track_error(self, error: StoryServiceError):
        """Track error for analytics and monitoring.
        
        Args:
            error: Structured error to track
        """
        # Add to error history
        self.error_history.append(error)
        
        # Update error counts
        error_key = f"{error.category}_{error.severity}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Track confidence adjustments
        if error.confidence_impact and error.context and error.context.session_id:
            session_id = error.context.session_id
            if session_id not in self.confidence_adjustments:
                self.confidence_adjustments[session_id] = []
            self.confidence_adjustments[session_id].append(error.confidence_impact)
        
        # Limit history size
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-500:]  # Keep last 500 errors
    
    def _log_error(self, error: StoryServiceError):
        """Log error with appropriate level.
        
        Args:
            error: Structured error to log
        """
        # Prepare log message
        log_message = f"[{error.error_id}] {error.message}"
        
        if error.context:
            context_info = []
            if error.context.session_id:
                context_info.append(f"session={error.context.session_id}")
            if error.context.project_id:
                context_info.append(f"project={error.context.project_id}")
            if error.context.component:
                context_info.append(f"component={error.context.component}")
            
            if context_info:
                log_message += f" [{', '.join(context_info)}]"
        
        # Log with appropriate level
        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif error.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        elif error.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        elif error.severity == ErrorSeverity.LOW:
            self.logger.info(log_message)
        else:  # INFO
            self.logger.debug(log_message)
        
        # Log stack trace for high severity errors
        if error.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH] and error.stack_trace:
            self.logger.error(f"Stack trace for {error.error_id}:\n{error.stack_trace}")
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics and analytics.
        
        Returns:
            Error statistics
        """
        total_errors = len(self.error_history)
        
        # Count by severity
        severity_counts = {}
        for severity in ErrorSeverity:
            severity_counts[severity.value] = sum(
                1 for error in self.error_history if error.severity == severity
            )
        
        # Count by category
        category_counts = {}
        for category in ErrorCategory:
            category_counts[category.value] = sum(
                1 for error in self.error_history if error.category == category
            )
        
        # Recent errors (last hour)
        recent_cutoff = datetime.now().timestamp() - 3600
        recent_errors = sum(
            1 for error in self.error_history
            if error.timestamp.timestamp() > recent_cutoff
        )
        
        # Average confidence impact
        impacts = [
            error.confidence_impact.impact_factor
            for error in self.error_history
            if error.confidence_impact
        ]
        avg_confidence_impact = sum(impacts) / len(impacts) if impacts else 0.0
        
        return {
            "total_errors": total_errors,
            "recent_errors_1h": recent_errors,
            "severity_breakdown": severity_counts,
            "category_breakdown": category_counts,
            "average_confidence_impact": round(avg_confidence_impact, 3),
            "total_confidence_adjustments": len(impacts),
            "error_rate_per_hour": recent_errors,
            "most_common_errors": self._get_most_common_errors()
        }
    
    def _get_most_common_errors(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get most common error patterns.
        
        Args:
            limit: Maximum number of patterns to return
            
        Returns:
            List of common error patterns
        """
        # Group by error message pattern
        message_counts = {}
        for error in self.error_history:
            # Simplified pattern extraction (first 50 chars)
            pattern = error.message[:50]
            message_counts[pattern] = message_counts.get(pattern, 0) + 1
        
        # Sort by frequency
        sorted_patterns = sorted(
            message_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {"pattern": pattern, "count": count}
            for pattern, count in sorted_patterns[:limit]
        ]
    
    def clear_error_history(self):
        """Clear error history and statistics."""
        self.error_history.clear()
        self.error_counts.clear()
        self.confidence_adjustments.clear()
        self.logger.info("Error history cleared")


# Global error handler instance
error_handler = ErrorHandler()


def setup_error_handling(
    log_level: str = "INFO",
    log_file: Optional[str] = "logs/story_service.log",
    enable_console: bool = True
) -> ErrorHandler:
    """Setup global error handling configuration.
    
    Args:
        log_level: Logging level
        log_file: Log file path
        enable_console: Enable console logging
        
    Returns:
        Configured error handler
    """
    global error_handler
    error_handler = ErrorHandler(
        log_level=log_level,
        log_file=log_file,
        enable_console=enable_console
    )
    
    return error_handler


def handle_story_error(
    error: Exception,
    **kwargs
) -> StoryServiceError:
    """Convenience function to handle errors with global handler.
    
    Args:
        error: Exception to handle
        **kwargs: Additional arguments for error handling
        
    Returns:
        Structured error information
    """
    return error_handler.handle_error(error, **kwargs)