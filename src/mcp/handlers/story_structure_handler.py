"""Story structure analysis tool handler with confidence scoring."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from mcp.types import CallToolResult

from ...models.story import StoryData
from ...models.analysis import AnalysisResult
from ...services.narrative.analyzer import NarrativeAnalyzer
from ...services.session_manager import StorySessionManager
from ...services.process_isolation import ProcessIsolationManager, ProcessConfig


class StoryStructureHandler:
    """Handler for story structure analysis MCP tool."""
    
    def __init__(
        self,
        session_manager: StorySessionManager,
        process_manager: ProcessIsolationManager
    ):
        """Initialize story structure handler.
        
        Args:
            session_manager: Story session manager
            process_manager: Process isolation manager
        """
        self.session_manager = session_manager
        self.process_manager = process_manager
        self.narrative_analyzer = NarrativeAnalyzer()
        self.logger = logging.getLogger(__name__)
    
    async def handle(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle story structure analysis tool call.
        
        Args:
            arguments: Tool call arguments
            
        Returns:
            MCP tool call result
        """
        try:
            # Extract arguments
            story_content = arguments.get("story_content", "")
            session_id = arguments.get("session_id", "")
            analysis_type = arguments.get("analysis_type", "three_act")
            
            if not story_content or not session_id:
                return CallToolResult(
                    content=[{
                        "type": "text",
                        "text": "Error: story_content and session_id are required"
                    }],
                    isError=True
                )
            
            # Get session
            session = await self.session_manager.get_session(session_id)
            if not session:
                return CallToolResult(
                    content=[{
                        "type": "text",
                        "text": f"Error: Session {session_id} not found"
                    }],
                    isError=True
                )
            
            # Create story data
            story_data = StoryData(
                content=story_content,
                metadata={"analysis_type": analysis_type}
            )
            
            # Perform analysis in isolated process if needed
            if len(story_content) > 10000:  # Use process isolation for large content
                result = await self._analyze_in_process(
                    story_data=story_data,
                    session=session,
                    analysis_type=analysis_type
                )
            else:
                # Direct analysis for smaller content
                result = await self._analyze_direct(
                    story_data=story_data,
                    analysis_type=analysis_type
                )
            
            # Update session with results
            await self.session_manager.update_session(
                session_id=session_id,
                story_data=story_data,
                analysis_result=result
            )
            
            # Format response
            response_content = {
                "analysis_type": analysis_type,
                "confidence": result.confidence,
                "structure": result.data.get("structure", {}),
                "beats": result.data.get("beats", []),
                "recommendations": result.data.get("recommendations", []),
                "metadata": result.metadata
            }
            
            return CallToolResult(
                content=[{
                    "type": "text",
                    "text": json.dumps(response_content, indent=2)
                }]
            )
            
        except Exception as e:
            self.logger.error(f"Story structure analysis error: {e}")
            return CallToolResult(
                content=[{
                    "type": "text",
                    "text": f"Error analyzing story structure: {str(e)}"
                }],
                isError=True
            )
    
    async def _analyze_direct(
        self,
        story_data: StoryData,
        analysis_type: str
    ) -> AnalysisResult:
        """Perform direct story structure analysis.
        
        Args:
            story_data: Story data to analyze
            analysis_type: Type of analysis to perform
            
        Returns:
            Analysis result
        """
        if analysis_type == "three_act":
            return await self.narrative_analyzer.analyze_three_act_structure(story_data)
        elif analysis_type == "hero_journey":
            return await self.narrative_analyzer.analyze_hero_journey(story_data)
        elif analysis_type == "five_act":
            return await self.narrative_analyzer.analyze_five_act_structure(story_data)
        else:
            # Default to comprehensive analysis
            return await self.narrative_analyzer.analyze_story_structure(story_data)
    
    async def _analyze_in_process(
        self,
        story_data: StoryData,
        session: Any,
        analysis_type: str
    ) -> AnalysisResult:
        """Perform story structure analysis in isolated process.
        
        Args:
            story_data: Story data to analyze
            session: Story session
            analysis_type: Type of analysis to perform
            
        Returns:
            Analysis result
        """
        # Create process configuration
        process_config = ProcessConfig(
            process_id=f"story_structure_{session.session_id}_{asyncio.get_event_loop().time()}",
            project_id=session.project_id,
            session_id=session.session_id,
            max_memory_mb=256,
            timeout_seconds=120
        )
        
        # Prepare analysis command
        analysis_script = f"""
import asyncio
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.story import StoryData
from src.services.narrative.analyzer import NarrativeAnalyzer

async def main():
    # Load input data
    with open('{process_config.env_vars.get("INPUT_FILE", "")}', 'r') as f:
        input_data = json.load(f)
    
    story_data = StoryData(**input_data['story_data'])
    analysis_type = input_data['analysis_type']
    
    # Perform analysis
    analyzer = NarrativeAnalyzer()
    if analysis_type == "three_act":
        result = await analyzer.analyze_three_act_structure(story_data)
    elif analysis_type == "hero_journey":
        result = await analyzer.analyze_hero_journey(story_data)
    elif analysis_type == "five_act":
        result = await analyzer.analyze_five_act_structure(story_data)
    else:
        result = await analyzer.analyze_story_structure(story_data)
    
    # Save output
    with open('{process_config.env_vars.get("OUTPUT_FILE", "")}', 'w') as f:
        json.dump(result.dict(), f, indent=2, default=str)

if __name__ == "__main__":
    asyncio.run(main())
"""
        
        # Prepare input data
        input_data = {
            "story_data": story_data.dict(),
            "analysis_type": analysis_type
        }
        
        # Start isolated process
        process_id = await self.process_manager.start_isolated_process(
            config=process_config,
            command=f"python -c \"{analysis_script}\"",
            input_data=input_data
        )
        
        if not process_id:
            raise RuntimeError("Failed to start isolated analysis process")
        
        # Wait for completion
        timeout = 120
        while timeout > 0:
            process_state = await self.process_manager.get_process_status(process_id)
            if not process_state:
                raise RuntimeError("Process state not found")
            
            if process_state.status in ["completed", "failed", "killed"]:
                break
            
            await asyncio.sleep(1)
            timeout -= 1
        
        if timeout <= 0:
            await self.process_manager.terminate_process(process_id)
            raise RuntimeError("Analysis process timed out")
        
        # Get results
        if process_state.status == "completed":
            output_data = await self.process_manager.get_process_output(process_id)
            if output_data:
                return AnalysisResult(**output_data)
        
        # Handle process failure
        error_output = await self.process_manager.get_process_error(process_id)
        raise RuntimeError(f"Analysis process failed: {error_output}")
    
    def _validate_confidence_threshold(self, result: AnalysisResult) -> bool:
        """Validate analysis meets 75% confidence threshold.
        
        Args:
            result: Analysis result to validate
            
        Returns:
            True if confidence threshold is met
        """
        return result.confidence >= 0.75
    
    def _enhance_low_confidence_result(self, result: AnalysisResult) -> AnalysisResult:
        """Enhance low confidence results with recommendations.
        
        Args:
            result: Low confidence analysis result
            
        Returns:
            Enhanced result with recommendations
        """
        if result.confidence < 0.75:
            # Add recommendations for improving confidence
            recommendations = result.data.get("recommendations", [])
            recommendations.extend([
                "Consider providing more story content for higher confidence analysis",
                "Ensure story follows clear structural patterns",
                "Check for missing key story elements (setup, conflict, resolution)"
            ])
            
            result.data["recommendations"] = recommendations
            result.metadata["confidence_enhancement"] = {
                "original_confidence": result.confidence,
                "enhancement_applied": True,
                "threshold": 0.75
            }
        
        return result