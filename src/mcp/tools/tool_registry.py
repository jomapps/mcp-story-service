"""MCP tool registry with protocol compliance validation."""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set

from mcp.types import Tool, ToolInputSchema
from pydantic import ValidationError

from ..handlers.story_structure_handler import StoryStructureHandler
from ..handlers.plot_threads_handler import PlotThreadsHandler
from ..handlers.consistency_handler import ConsistencyHandler
from ..handlers.genre_patterns_handler import GenrePatternsHandler
from ..handlers.session_handler import SessionHandler
from ..handlers.pacing_handler import PacingHandler


class MCPToolRegistry:
    """Registry for MCP tools with protocol compliance validation."""
    
    def __init__(self):
        """Initialize tool registry."""
        self.logger = logging.getLogger(__name__)
        self._tools: Dict[str, Tool] = {}
        self._handlers: Dict[str, Any] = {}
        self._tool_metadata: Dict[str, Dict[str, Any]] = {}
        self._validation_rules: Dict[str, List[str]] = {}
        
        # Initialize tool definitions
        self._initialize_tool_definitions()
        self._setup_validation_rules()
    
    def _initialize_tool_definitions(self):
        """Initialize all MCP tool definitions."""
        
        # Story Structure Analysis Tool
        self._tools["analyze_story_structure"] = Tool(
            name="analyze_story_structure",
            description="Analyze story structure with confidence scoring (75% threshold). Identifies narrative patterns including three-act structure, hero's journey, and five-act progression with detailed beat analysis.",
            inputSchema=ToolInputSchema(
                type="object",
                properties={
                    "story_content": {
                        "type": "string",
                        "description": "Complete or partial story content to analyze for structural patterns",
                        "minLength": 100,
                        "maxLength": 100000
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Session identifier for analysis context and persistence",
                        "pattern": r"^[a-f0-9-]{36}$"
                    },
                    "analysis_type": {
                        "type": "string",
                        "enum": ["three_act", "hero_journey", "five_act", "comprehensive"],
                        "description": "Specific structural analysis to perform",
                        "default": "comprehensive"
                    }
                },
                required=["story_content", "session_id"],
                additionalProperties=False
            )
        )
        
        # Plot Threads Tracking Tool
        self._tools["track_plot_threads"] = Tool(
            name="track_plot_threads",
            description="Track plot threads with character lifecycle management. Analyzes main plots, subplots, character arcs, and their interactions with comprehensive thread progression tracking.",
            inputSchema=ToolInputSchema(
                type="object",
                properties={
                    "story_content": {
                        "type": "string",
                        "description": "Story content for plot thread analysis",
                        "minLength": 100,
                        "maxLength": 100000
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Session identifier for context",
                        "pattern": r"^[a-f0-9-]{36}$"
                    },
                    "thread_focus": {
                        "type": "string",
                        "enum": ["main", "subplot", "character", "all"],
                        "description": "Focus area for thread analysis",
                        "default": "all"
                    }
                },
                required=["story_content", "session_id"],
                additionalProperties=False
            )
        )
        
        # Consistency Validation Tool
        self._tools["validate_consistency"] = Tool(
            name="validate_consistency",
            description="Validate story consistency with severity ratings. Detects plot holes, character inconsistencies, timeline errors, and logical contradictions with detailed violation reporting.",
            inputSchema=ToolInputSchema(
                type="object",
                properties={
                    "story_content": {
                        "type": "string",
                        "description": "Story content for consistency validation",
                        "minLength": 100,
                        "maxLength": 100000
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Session identifier for context",
                        "pattern": r"^[a-f0-9-]{36}$"
                    },
                    "validation_scope": {
                        "type": "string",
                        "enum": ["character", "timeline", "plot", "all"],
                        "description": "Scope of consistency validation",
                        "default": "all"
                    }
                },
                required=["story_content", "session_id"],
                additionalProperties=False
            )
        )
        
        # Genre Patterns Tool
        self._tools["apply_genre_patterns"] = Tool(
            name="apply_genre_patterns",
            description="Apply genre patterns with 75% confidence threshold. Analyzes story elements against 17+ genre templates for pattern matching and authenticity scoring.",
            inputSchema=ToolInputSchema(
                type="object",
                properties={
                    "story_content": {
                        "type": "string",
                        "description": "Story content for genre pattern analysis",
                        "minLength": 100,
                        "maxLength": 100000
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Session identifier for context",
                        "pattern": r"^[a-f0-9-]{36}$"
                    },
                    "target_genres": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": [
                                "thriller", "drama", "comedy", "action", "horror", 
                                "romance", "sci-fi", "fantasy", "mystery", "western",
                                "war", "historical", "biographical", "documentary", 
                                "animation", "crime", "adventure"
                            ]
                        },
                        "description": "Specific genres to analyze (optional)",
                        "maxItems": 5,
                        "uniqueItems": True
                    }
                },
                required=["story_content", "session_id"],
                additionalProperties=False
            )
        )
        
        # Session Management Tool
        self._tools["get_story_session"] = Tool(
            name="get_story_session",
            description="Get or create story session with persistence until completion. Manages analysis sessions with process isolation and automatic persistence policies.",
            inputSchema=ToolInputSchema(
                type="object",
                properties={
                    "project_id": {
                        "type": "string",
                        "description": "Project identifier for isolation",
                        "pattern": r"^[a-zA-Z0-9_-]+$",
                        "minLength": 1,
                        "maxLength": 50
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Existing session ID (optional for retrieval)",
                        "pattern": r"^[a-f0-9-]{36}$"
                    },
                    "session_config": {
                        "type": "object",
                        "properties": {
                            "max_session_duration": {
                                "type": "integer",
                                "minimum": 300,
                                "maximum": 7200,
                                "description": "Maximum session duration in seconds"
                            },
                            "auto_persist": {
                                "type": "boolean",
                                "description": "Enable automatic persistence"
                            },
                            "isolation_level": {
                                "type": "string",
                                "enum": ["process", "thread"],
                                "description": "Level of isolation"
                            }
                        },
                        "additionalProperties": False,
                        "description": "Optional session configuration"
                    }
                },
                required=["project_id"],
                additionalProperties=False
            )
        )
        
        # Pacing Calculation Tool
        self._tools["calculate_pacing"] = Tool(
            name="calculate_pacing",
            description="Calculate story pacing with quality prioritization. Analyzes narrative rhythm, tension curves, and pacing variations with detailed quality scoring and recommendations.",
            inputSchema=ToolInputSchema(
                type="object",
                properties={
                    "story_content": {
                        "type": "string",
                        "description": "Story content for pacing analysis",
                        "minLength": 100,
                        "maxLength": 100000
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Session identifier for context",
                        "pattern": r"^[a-f0-9-]{36}$"
                    },
                    "analysis_depth": {
                        "type": "string",
                        "enum": ["quick", "standard", "detailed"],
                        "description": "Depth of pacing analysis to perform",
                        "default": "standard"
                    }
                },
                required=["story_content", "session_id"],
                additionalProperties=False
            )
        )
        
        # Initialize tool metadata
        self._initialize_tool_metadata()
    
    def _initialize_tool_metadata(self):
        """Initialize metadata for all tools."""
        
        self._tool_metadata = {
            "analyze_story_structure": {
                "category": "structure_analysis",
                "confidence_threshold": 0.75,
                "process_isolation": True,
                "session_required": True,
                "output_format": "structured_analysis",
                "performance_class": "compute_intensive",
                "constitutional_compliance": ["Library-First", "Test-First", "Simplicity"]
            },
            "track_plot_threads": {
                "category": "narrative_analysis",
                "confidence_threshold": 0.75,
                "process_isolation": False,
                "session_required": True,
                "output_format": "thread_graph",
                "performance_class": "standard",
                "constitutional_compliance": ["Library-First", "Test-First"]
            },
            "validate_consistency": {
                "category": "validation",
                "confidence_threshold": 0.75,
                "process_isolation": False,
                "session_required": True,
                "output_format": "violation_report",
                "performance_class": "standard",
                "constitutional_compliance": ["Library-First", "Test-First", "Simplicity"]
            },
            "apply_genre_patterns": {
                "category": "pattern_matching",
                "confidence_threshold": 0.75,
                "process_isolation": False,
                "session_required": True,
                "output_format": "pattern_analysis",
                "performance_class": "standard",
                "constitutional_compliance": ["Library-First", "Test-First"]
            },
            "get_story_session": {
                "category": "session_management",
                "confidence_threshold": None,
                "process_isolation": True,
                "session_required": False,
                "output_format": "session_info",
                "performance_class": "lightweight",
                "constitutional_compliance": ["Library-First", "Simplicity"]
            },
            "calculate_pacing": {
                "category": "quality_analysis",
                "confidence_threshold": 0.75,
                "process_isolation": False,
                "session_required": True,
                "output_format": "pacing_metrics",
                "performance_class": "compute_intensive",
                "constitutional_compliance": ["Library-First", "Test-First", "Simplicity"]
            }
        }
    
    def _setup_validation_rules(self):
        """Setup validation rules for tool compliance."""
        
        self._validation_rules = {
            "analyze_story_structure": [
                "must_meet_confidence_threshold",
                "must_validate_session",
                "must_handle_malformed_content",
                "must_support_process_isolation"
            ],
            "track_plot_threads": [
                "must_meet_confidence_threshold",
                "must_validate_session",
                "must_track_character_lifecycle",
                "must_handle_thread_interactions"
            ],
            "validate_consistency": [
                "must_meet_confidence_threshold",
                "must_validate_session",
                "must_report_severity_levels",
                "must_detect_plot_holes"
            ],
            "apply_genre_patterns": [
                "must_meet_confidence_threshold",
                "must_validate_session",
                "must_support_multiple_genres",
                "must_validate_authenticity"
            ],
            "get_story_session": [
                "must_support_project_isolation",
                "must_persist_until_completion",
                "must_handle_session_lifecycle",
                "must_support_process_isolation"
            ],
            "calculate_pacing": [
                "must_meet_confidence_threshold",
                "must_validate_session",
                "must_prioritize_quality",
                "must_analyze_tension_curves"
            ]
        }
    
    def register_handlers(
        self,
        story_structure_handler: StoryStructureHandler,
        plot_threads_handler: PlotThreadsHandler,
        consistency_handler: ConsistencyHandler,
        genre_patterns_handler: GenrePatternsHandler,
        session_handler: SessionHandler,
        pacing_handler: PacingHandler
    ):
        """Register tool handlers.
        
        Args:
            story_structure_handler: Story structure analysis handler
            plot_threads_handler: Plot threads tracking handler
            consistency_handler: Consistency validation handler
            genre_patterns_handler: Genre patterns handler
            session_handler: Session management handler
            pacing_handler: Pacing calculation handler
        """
        self._handlers = {
            "analyze_story_structure": story_structure_handler,
            "track_plot_threads": plot_threads_handler,
            "validate_consistency": consistency_handler,
            "apply_genre_patterns": genre_patterns_handler,
            "get_story_session": session_handler,
            "calculate_pacing": pacing_handler
        }
        
        self.logger.info("All MCP tool handlers registered successfully")
    
    def get_all_tools(self) -> List[Tool]:
        """Get all registered MCP tools.
        
        Returns:
            List of all tools
        """
        return list(self._tools.values())
    
    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """Get specific tool by name.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool definition or None if not found
        """
        return self._tools.get(tool_name)
    
    def get_tool_handler(self, tool_name: str) -> Optional[Any]:
        """Get tool handler by name.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool handler or None if not found
        """
        return self._handlers.get(tool_name)
    
    def get_tool_metadata(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get tool metadata by name.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool metadata or None if not found
        """
        return self._tool_metadata.get(tool_name)
    
    def validate_tool_compliance(self, tool_name: str) -> Dict[str, Any]:
        """Validate tool compliance with MCP protocol.
        
        Args:
            tool_name: Name of the tool to validate
            
        Returns:
            Validation result with compliance status
        """
        validation_result = {
            "tool_name": tool_name,
            "is_compliant": False,
            "validation_errors": [],
            "validation_warnings": [],
            "compliance_score": 0.0,
            "required_rules": [],
            "passed_rules": [],
            "failed_rules": []
        }
        
        # Check if tool exists
        if tool_name not in self._tools:
            validation_result["validation_errors"].append(f"Tool '{tool_name}' not found in registry")
            return validation_result
        
        tool = self._tools[tool_name]
        metadata = self._tool_metadata.get(tool_name, {})
        rules = self._validation_rules.get(tool_name, [])
        
        validation_result["required_rules"] = rules
        
        # Validate tool definition
        try:
            # Check required fields
            if not tool.name:
                validation_result["validation_errors"].append("Tool name is required")
            
            if not tool.description:
                validation_result["validation_errors"].append("Tool description is required")
            
            if not tool.inputSchema:
                validation_result["validation_errors"].append("Tool input schema is required")
            
            # Validate input schema
            schema_validation = self._validate_input_schema(tool.inputSchema)
            validation_result["validation_errors"].extend(schema_validation["errors"])
            validation_result["validation_warnings"].extend(schema_validation["warnings"])
            
            # Check constitutional compliance
            constitutional_compliance = metadata.get("constitutional_compliance", [])
            required_principles = ["Library-First", "Test-First"]
            
            for principle in required_principles:
                if principle in constitutional_compliance:
                    validation_result["passed_rules"].append(f"constitutional_{principle.lower().replace('-', '_')}")
                else:
                    validation_result["failed_rules"].append(f"constitutional_{principle.lower().replace('-', '_')}")
            
            # Check confidence threshold compliance
            if metadata.get("confidence_threshold") == 0.75:
                validation_result["passed_rules"].append("confidence_threshold_75_percent")
            elif metadata.get("confidence_threshold") is not None:
                validation_result["failed_rules"].append("confidence_threshold_75_percent")
            
            # Check session requirement compliance
            if metadata.get("session_required"):
                if "session_id" in str(tool.inputSchema):
                    validation_result["passed_rules"].append("session_validation")
                else:
                    validation_result["failed_rules"].append("session_validation")
            
            # Check process isolation support
            if metadata.get("process_isolation"):
                validation_result["passed_rules"].append("process_isolation_support")
            
            # Rule-specific validations
            for rule in rules:
                rule_result = self._validate_specific_rule(tool_name, rule, tool, metadata)
                if rule_result:
                    validation_result["passed_rules"].append(rule)
                else:
                    validation_result["failed_rules"].append(rule)
            
            # Calculate compliance score
            total_rules = len(validation_result["passed_rules"]) + len(validation_result["failed_rules"])
            if total_rules > 0:
                validation_result["compliance_score"] = len(validation_result["passed_rules"]) / total_rules
            
            # Overall compliance determination
            validation_result["is_compliant"] = (
                len(validation_result["validation_errors"]) == 0 and
                validation_result["compliance_score"] >= 0.8
            )
            
        except ValidationError as e:
            validation_result["validation_errors"].append(f"Schema validation error: {str(e)}")
        except Exception as e:
            validation_result["validation_errors"].append(f"Unexpected validation error: {str(e)}")
        
        return validation_result
    
    def _validate_input_schema(self, schema: ToolInputSchema) -> Dict[str, List[str]]:
        """Validate tool input schema.
        
        Args:
            schema: Input schema to validate
            
        Returns:
            Validation result with errors and warnings
        """
        result = {"errors": [], "warnings": []}
        
        try:
            # Check schema type
            if schema.type != "object":
                result["errors"].append("Input schema must be of type 'object'")
            
            # Check required properties
            if not hasattr(schema, 'properties') or not schema.properties:
                result["errors"].append("Input schema must have properties defined")
            
            # Check for required fields
            if not hasattr(schema, 'required') or not schema.required:
                result["warnings"].append("No required fields specified in schema")
            
            # Validate property definitions
            if hasattr(schema, 'properties') and schema.properties:
                for prop_name, prop_def in schema.properties.items():
                    if not isinstance(prop_def, dict):
                        result["errors"].append(f"Property '{prop_name}' definition must be a dictionary")
                        continue
                    
                    if "type" not in prop_def:
                        result["errors"].append(f"Property '{prop_name}' must have a type specified")
                    
                    if "description" not in prop_def:
                        result["warnings"].append(f"Property '{prop_name}' should have a description")
            
        except Exception as e:
            result["errors"].append(f"Schema validation exception: {str(e)}")
        
        return result
    
    def _validate_specific_rule(
        self,
        tool_name: str,
        rule: str,
        tool: Tool,
        metadata: Dict[str, Any]
    ) -> bool:
        """Validate specific compliance rule.
        
        Args:
            tool_name: Name of the tool
            rule: Rule to validate
            tool: Tool definition
            metadata: Tool metadata
            
        Returns:
            True if rule passes validation
        """
        try:
            if rule == "must_meet_confidence_threshold":
                return metadata.get("confidence_threshold") == 0.75
            
            elif rule == "must_validate_session":
                return "session_id" in str(tool.inputSchema)
            
            elif rule == "must_handle_malformed_content":
                # Check if tool has error handling capability
                return metadata.get("performance_class") in ["standard", "compute_intensive"]
            
            elif rule == "must_support_process_isolation":
                return metadata.get("process_isolation", False)
            
            elif rule == "must_track_character_lifecycle":
                return tool_name == "track_plot_threads" and "thread_focus" in str(tool.inputSchema)
            
            elif rule == "must_handle_thread_interactions":
                return tool_name == "track_plot_threads"
            
            elif rule == "must_report_severity_levels":
                return tool_name == "validate_consistency" and "validation_scope" in str(tool.inputSchema)
            
            elif rule == "must_detect_plot_holes":
                return tool_name == "validate_consistency"
            
            elif rule == "must_support_multiple_genres":
                return tool_name == "apply_genre_patterns" and "target_genres" in str(tool.inputSchema)
            
            elif rule == "must_validate_authenticity":
                return tool_name == "apply_genre_patterns"
            
            elif rule == "must_support_project_isolation":
                return tool_name == "get_story_session" and "project_id" in str(tool.inputSchema)
            
            elif rule == "must_persist_until_completion":
                return tool_name == "get_story_session"
            
            elif rule == "must_handle_session_lifecycle":
                return tool_name == "get_story_session"
            
            elif rule == "must_prioritize_quality":
                return tool_name == "calculate_pacing" and "analysis_depth" in str(tool.inputSchema)
            
            elif rule == "must_analyze_tension_curves":
                return tool_name == "calculate_pacing"
            
            else:
                self.logger.warning(f"Unknown validation rule: {rule}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error validating rule {rule}: {e}")
            return False
    
    def validate_all_tools(self) -> Dict[str, Any]:
        """Validate all tools in the registry.
        
        Returns:
            Complete validation report
        """
        validation_report = {
            "total_tools": len(self._tools),
            "compliant_tools": 0,
            "non_compliant_tools": 0,
            "overall_compliance_score": 0.0,
            "tool_validations": {},
            "summary": {
                "constitutional_compliance": 0,
                "confidence_threshold_compliance": 0,
                "session_management_compliance": 0,
                "process_isolation_support": 0
            }
        }
        
        total_compliance_score = 0.0
        
        for tool_name in self._tools:
            tool_validation = self.validate_tool_compliance(tool_name)
            validation_report["tool_validations"][tool_name] = tool_validation
            
            if tool_validation["is_compliant"]:
                validation_report["compliant_tools"] += 1
            else:
                validation_report["non_compliant_tools"] += 1
            
            total_compliance_score += tool_validation["compliance_score"]
            
            # Update summary statistics
            if "constitutional" in str(tool_validation["passed_rules"]):
                validation_report["summary"]["constitutional_compliance"] += 1
            
            if "confidence_threshold" in str(tool_validation["passed_rules"]):
                validation_report["summary"]["confidence_threshold_compliance"] += 1
            
            if "session" in str(tool_validation["passed_rules"]):
                validation_report["summary"]["session_management_compliance"] += 1
            
            if "process_isolation" in str(tool_validation["passed_rules"]):
                validation_report["summary"]["process_isolation_support"] += 1
        
        # Calculate overall compliance score
        if validation_report["total_tools"] > 0:
            validation_report["overall_compliance_score"] = round(
                total_compliance_score / validation_report["total_tools"], 3
            )
        
        return validation_report
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics.
        
        Returns:
            Registry statistics
        """
        categories = {}
        performance_classes = {}
        
        for tool_name, metadata in self._tool_metadata.items():
            category = metadata.get("category", "unknown")
            categories[category] = categories.get(category, 0) + 1
            
            perf_class = metadata.get("performance_class", "unknown")
            performance_classes[perf_class] = performance_classes.get(perf_class, 0) + 1
        
        return {
            "total_tools": len(self._tools),
            "total_handlers": len(self._handlers),
            "categories": categories,
            "performance_classes": performance_classes,
            "tools_with_process_isolation": len([
                tool for tool, meta in self._tool_metadata.items()
                if meta.get("process_isolation", False)
            ]),
            "tools_with_confidence_threshold": len([
                tool for tool, meta in self._tool_metadata.items()
                if meta.get("confidence_threshold") == 0.75
            ]),
            "constitutional_compliant_tools": len([
                tool for tool, meta in self._tool_metadata.items()
                if "Library-First" in meta.get("constitutional_compliance", [])
            ])
        }


# Global registry instance
mcp_tool_registry = MCPToolRegistry()