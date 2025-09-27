"""ContentAnalysisResult model for malformed content handling.

This model handles analysis results with comprehensive malformed content
support per Clarification B.

Constitutional Compliance:
- Library-First (I): Uses pydantic for data validation
- Simplicity (III): Clear result structure for all content types
- LLM Declaration (VI): Structured for analysis result workflows
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum

from pydantic import BaseModel, Field, validator, root_validator


class ContentQuality(str, Enum):
    """Content quality classifications."""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    MALFORMED = "malformed"
    EMPTY = "empty"


class ProcessingStatus(str, Enum):
    """Processing status for content analysis."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    ERROR = "error"


class ContentIssue(BaseModel):
    """Individual content issue identification."""
    issue_type: str = Field(..., description="Type of content issue")
    severity: str = Field(..., description="Severity level (low, medium, high, critical)")
    description: str = Field(..., description="Description of the issue")
    position: Optional[float] = Field(None, ge=0.0, le=1.0, description="Position in content where issue occurs")
    suggested_fix: Optional[str] = Field(None, description="Suggested fix for the issue")
    affects_analysis: bool = Field(True, description="Whether issue affects analysis quality")


class PreprocessingStep(BaseModel):
    """Record of preprocessing steps applied."""
    step_name: str = Field(..., description="Name of preprocessing step")
    description: str = Field(..., description="What this step does")
    applied: bool = Field(..., description="Whether step was applied")
    success: bool = Field(..., description="Whether step succeeded")
    changes_made: List[str] = Field(default_factory=list, description="Changes made by this step")
    warnings: List[str] = Field(default_factory=list, description="Warnings from this step")


class AnalysisAttempt(BaseModel):
    """Record of individual analysis attempt."""
    attempt_number: int = Field(..., description="Attempt number")
    analysis_type: str = Field(..., description="Type of analysis attempted")
    success: bool = Field(..., description="Whether attempt succeeded")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in results")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    partial_results: Optional[Dict[str, Any]] = Field(None, description="Partial results if available")


class FallbackStrategy(BaseModel):
    """Fallback strategy for handling problematic content."""
    strategy_name: str = Field(..., description="Name of fallback strategy")
    trigger_condition: str = Field(..., description="What triggered this fallback")
    description: str = Field(..., description="Description of fallback approach")
    success: bool = Field(..., description="Whether fallback succeeded")
    results_quality: ContentQuality = Field(..., description="Quality of fallback results")


class ContentAnalysisResult(BaseModel):
    """
    Content analysis result model for comprehensive malformed content handling.
    
    Provides detailed results, error handling, and quality assessment
    for all types of content per Clarification B.
    """
    
    # Core identification
    analysis_id: str = Field(..., description="Unique analysis identifier")
    session_id: str = Field(..., description="Session context")
    content_hash: str = Field(..., description="Hash of analyzed content for caching")
    
    # Processing status
    status: ProcessingStatus = Field(..., description="Overall processing status")
    content_quality: ContentQuality = Field(..., description="Assessed content quality")
    
    # Content metadata
    original_content_length: int = Field(..., ge=0, description="Original content length")
    processed_content_length: int = Field(..., ge=0, description="Processed content length")
    encoding_detected: Optional[str] = Field(None, description="Detected character encoding")
    format_detected: Optional[str] = Field(None, description="Detected content format")
    language_detected: Optional[str] = Field(None, description="Detected language")
    
    # Quality assessment
    content_issues: List[ContentIssue] = Field(default_factory=list, description="Identified content issues")
    preprocessing_steps: List[PreprocessingStep] = Field(default_factory=list, description="Applied preprocessing")
    
    # Analysis attempts and results
    analysis_attempts: List[AnalysisAttempt] = Field(default_factory=list, description="All analysis attempts")
    fallback_strategies: List[FallbackStrategy] = Field(default_factory=list, description="Applied fallback strategies")
    
    # Final results
    primary_results: Optional[Dict[str, Any]] = Field(None, description="Primary analysis results")
    partial_results: List[Dict[str, Any]] = Field(default_factory=list, description="Partial analysis results")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in results")
    
    # Quality metrics
    completeness_score: float = Field(..., ge=0.0, le=1.0, description="How complete the analysis is")
    reliability_score: float = Field(..., ge=0.0, le=1.0, description="How reliable the results are")
    usability_score: float = Field(..., ge=0.0, le=1.0, description="How usable the results are")
    
    # Error handling
    errors_encountered: List[str] = Field(default_factory=list, description="Errors encountered during processing")
    warnings_generated: List[str] = Field(default_factory=list, description="Warnings generated")
    recovery_actions: List[str] = Field(default_factory=list, description="Recovery actions taken")
    
    # Performance metadata
    total_processing_time_ms: float = Field(..., description="Total processing time")
    memory_usage_mb: Optional[float] = Field(None, description="Peak memory usage")
    cpu_usage_percent: Optional[float] = Field(None, description="CPU usage during processing")
    
    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Analysis start time")
    completed_at: Optional[datetime] = Field(None, description="Analysis completion time")
    
    # Recommendations and next steps
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for improvement")
    alternative_approaches: List[str] = Field(default_factory=list, description="Alternative analysis approaches")
    
    # Metadata
    analysis_version: str = Field(default="1.0", description="Analysis version")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "analysis_id": "analysis_123",
                "session_id": "session_456",
                "status": "partial_success",
                "content_quality": "poor",
                "confidence_score": 0.45,
                "completeness_score": 0.60,
                "reliability_score": 0.70,
                "content_issues": [
                    {
                        "issue_type": "encoding_problems",
                        "severity": "medium",
                        "description": "Non-UTF8 characters detected",
                        "affects_analysis": True
                    }
                ]
            }
        }

    @validator('completed_at', always=True)
    def set_completion_time(cls, v, values):
        """Set completion time for completed analyses."""
        status = values.get('status')
        if status in [ProcessingStatus.SUCCESS, ProcessingStatus.PARTIAL_SUCCESS, 
                     ProcessingStatus.FAILED, ProcessingStatus.ERROR] and v is None:
            return datetime.utcnow()
        return v

    @root_validator
    def validate_result_consistency(cls, values):
        """Validate consistency between status and results."""
        status = values.get('status')
        primary_results = values.get('primary_results')
        confidence = values.get('confidence_score', 0.0)
        
        if status == ProcessingStatus.SUCCESS and not primary_results:
            raise ValueError("SUCCESS status requires primary_results")
        
        if status == ProcessingStatus.FAILED and confidence > 0.1:
            raise ValueError("FAILED status should have very low confidence")
        
        if status == ProcessingStatus.SUCCESS and confidence < 0.5:
            raise ValueError("SUCCESS status should have reasonable confidence")
        
        return values

    def add_content_issue(self, issue_type: str, severity: str, description: str,
                         position: Optional[float] = None, suggested_fix: Optional[str] = None,
                         affects_analysis: bool = True) -> None:
        """Add a content issue to the analysis."""
        issue = ContentIssue(
            issue_type=issue_type,
            severity=severity,
            description=description,
            position=position,
            suggested_fix=suggested_fix,
            affects_analysis=affects_analysis
        )
        self.content_issues.append(issue)

    def add_preprocessing_step(self, step_name: str, description: str, applied: bool,
                             success: bool, changes_made: List[str] = None,
                             warnings: List[str] = None) -> None:
        """Record a preprocessing step."""
        step = PreprocessingStep(
            step_name=step_name,
            description=description,
            applied=applied,
            success=success,
            changes_made=changes_made or [],
            warnings=warnings or []
        )
        self.preprocessing_steps.append(step)

    def add_analysis_attempt(self, attempt_number: int, analysis_type: str, success: bool,
                           confidence: float, processing_time_ms: float,
                           error_message: Optional[str] = None,
                           partial_results: Optional[Dict[str, Any]] = None) -> None:
        """Record an analysis attempt."""
        attempt = AnalysisAttempt(
            attempt_number=attempt_number,
            analysis_type=analysis_type,
            success=success,
            confidence=confidence,
            processing_time_ms=processing_time_ms,
            error_message=error_message,
            partial_results=partial_results
        )
        self.analysis_attempts.append(attempt)

    def add_fallback_strategy(self, strategy_name: str, trigger_condition: str,
                            description: str, success: bool,
                            results_quality: ContentQuality) -> None:
        """Record use of a fallback strategy."""
        strategy = FallbackStrategy(
            strategy_name=strategy_name,
            trigger_condition=trigger_condition,
            description=description,
            success=success,
            results_quality=results_quality
        )
        self.fallback_strategies.append(strategy)

    def get_quality_assessment(self) -> Dict[str, Any]:
        """Get comprehensive quality assessment."""
        return {
            "overall_quality": self.content_quality.value,
            "confidence": self.confidence_score,
            "completeness": self.completeness_score,
            "reliability": self.reliability_score,
            "usability": self.usability_score,
            "issues": {
                "total_issues": len(self.content_issues),
                "critical_issues": len([i for i in self.content_issues if i.severity == "critical"]),
                "high_severity": len([i for i in self.content_issues if i.severity == "high"]),
                "affects_analysis": len([i for i in self.content_issues if i.affects_analysis])
            },
            "processing": {
                "status": self.status.value,
                "attempts": len(self.analysis_attempts),
                "successful_attempts": len([a for a in self.analysis_attempts if a.success]),
                "fallback_used": len(self.fallback_strategies) > 0
            }
        }

    def get_issue_summary(self) -> Dict[str, Any]:
        """Get summary of content issues."""
        if not self.content_issues:
            return {"has_issues": False, "summary": "No content issues detected"}
        
        issues_by_type = {}
        issues_by_severity = {}
        
        for issue in self.content_issues:
            # Group by type
            if issue.issue_type not in issues_by_type:
                issues_by_type[issue.issue_type] = []
            issues_by_type[issue.issue_type].append(issue)
            
            # Group by severity
            if issue.severity not in issues_by_severity:
                issues_by_severity[issue.severity] = 0
            issues_by_severity[issue.severity] += 1
        
        return {
            "has_issues": True,
            "total_issues": len(self.content_issues),
            "by_type": {
                issue_type: {
                    "count": len(issues),
                    "descriptions": [i.description for i in issues]
                }
                for issue_type, issues in issues_by_type.items()
            },
            "by_severity": issues_by_severity,
            "analysis_impact": len([i for i in self.content_issues if i.affects_analysis]),
            "suggestions": [i.suggested_fix for i in self.content_issues if i.suggested_fix]
        }

    def get_processing_summary(self) -> Dict[str, Any]:
        """Get summary of processing steps and attempts."""
        return {
            "status": self.status.value,
            "preprocessing": {
                "steps_applied": len([s for s in self.preprocessing_steps if s.applied]),
                "steps_successful": len([s for s in self.preprocessing_steps if s.applied and s.success]),
                "total_changes": sum(len(s.changes_made) for s in self.preprocessing_steps),
                "warnings": sum(len(s.warnings) for s in self.preprocessing_steps)
            },
            "analysis_attempts": {
                "total_attempts": len(self.analysis_attempts),
                "successful_attempts": len([a for a in self.analysis_attempts if a.success]),
                "average_confidence": (
                    sum(a.confidence for a in self.analysis_attempts) / 
                    max(len(self.analysis_attempts), 1)
                ),
                "total_processing_time": sum(a.processing_time_ms for a in self.analysis_attempts)
            },
            "fallback_strategies": {
                "strategies_used": len(self.fallback_strategies),
                "successful_fallbacks": len([f for f in self.fallback_strategies if f.success])
            },
            "performance": {
                "total_time_ms": self.total_processing_time_ms,
                "memory_usage_mb": self.memory_usage_mb,
                "cpu_usage_percent": self.cpu_usage_percent
            }
        }

    def get_recommendations_summary(self) -> Dict[str, Any]:
        """Get comprehensive recommendations."""
        all_recommendations = self.recommendations.copy()
        
        # Add issue-based recommendations
        critical_issues = [i for i in self.content_issues if i.severity == "critical"]
        if critical_issues:
            all_recommendations.append("Address critical content issues before reanalysis")
        
        encoding_issues = [i for i in self.content_issues if "encoding" in i.issue_type.lower()]
        if encoding_issues:
            all_recommendations.append("Ensure content is properly encoded in UTF-8")
        
        if self.confidence_score < 0.75:
            all_recommendations.append("Content quality may be too low for reliable analysis")
        
        if len(self.fallback_strategies) > 0:
            all_recommendations.append("Consider improving content quality to avoid fallback strategies")
        
        return {
            "total_recommendations": len(all_recommendations),
            "recommendations": all_recommendations,
            "alternative_approaches": self.alternative_approaches,
            "priority_actions": [
                rec for rec in all_recommendations 
                if any(word in rec.lower() for word in ["critical", "must", "required"])
            ]
        }

    def is_usable_for_analysis(self) -> bool:
        """Determine if results are usable for further analysis."""
        return (
            self.status in [ProcessingStatus.SUCCESS, ProcessingStatus.PARTIAL_SUCCESS] and
            self.confidence_score >= 0.3 and  # Minimum usability threshold
            self.usability_score >= 0.5 and
            len([i for i in self.content_issues if i.severity == "critical"]) == 0
        )

    def meets_quality_threshold(self, threshold: float = 0.75) -> bool:
        """Check if analysis meets quality threshold."""
        return (
            self.confidence_score >= threshold and
            self.status == ProcessingStatus.SUCCESS and
            self.reliability_score >= 0.7
        )

    def get_best_available_results(self) -> Optional[Dict[str, Any]]:
        """Get the best available results regardless of completeness."""
        if self.primary_results:
            return self.primary_results
        
        # Look for best partial results
        if self.partial_results:
            # Return partial results with highest confidence
            best_partial = max(
                self.partial_results,
                key=lambda x: x.get('confidence', 0.0),
                default=None
            )
            return best_partial
        
        # Look for results in successful attempts
        successful_attempts = [a for a in self.analysis_attempts if a.success and a.partial_results]
        if successful_attempts:
            best_attempt = max(successful_attempts, key=lambda x: x.confidence)
            return best_attempt.partial_results
        
        return None

    def to_mcp_response(self) -> Dict[str, Any]:
        """Convert to MCP tool response format."""
        return {
            "analysis_id": self.analysis_id,
            "status": self.status.value,
            "results": self.get_best_available_results(),
            "confidence": self.confidence_score,
            "quality": self.get_quality_assessment(),
            "issues": self.get_issue_summary(),
            "processing": self.get_processing_summary(),
            "recommendations": self.get_recommendations_summary(),
            "metadata": {
                "session_id": self.session_id,
                "content_quality": self.content_quality.value,
                "original_length": self.original_content_length,
                "processed_length": self.processed_content_length,
                "format_detected": self.format_detected,
                "language_detected": self.language_detected,
                "processing_time_ms": self.total_processing_time_ms,
                "started_at": self.started_at.isoformat(),
                "completed_at": self.completed_at.isoformat() if self.completed_at else None
            }
        }

    def create_partial_success_response(self, available_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create response for partial success scenarios."""
        self.status = ProcessingStatus.PARTIAL_SUCCESS
        self.partial_results.append(available_data)
        
        # Adjust confidence based on completeness
        completeness_factor = min(self.completeness_score, 0.8)  # Cap impact
        self.confidence_score = self.confidence_score * completeness_factor
        
        return self.to_mcp_response()

    @classmethod
    def create_failure_result(cls, analysis_id: str, session_id: str, content_length: int,
                            error_message: str, content_hash: str = "") -> "ContentAnalysisResult":
        """Create a failure result for completely failed analysis."""
        return cls(
            analysis_id=analysis_id,
            session_id=session_id,
            content_hash=content_hash,
            status=ProcessingStatus.FAILED,
            content_quality=ContentQuality.MALFORMED,
            original_content_length=content_length,
            processed_content_length=0,
            confidence_score=0.0,
            completeness_score=0.0,
            reliability_score=0.0,
            usability_score=0.0,
            total_processing_time_ms=0.0,
            errors_encountered=[error_message],
            recommendations=["Content appears to be malformed or unprocessable"],
            completed_at=datetime.utcnow()
        )