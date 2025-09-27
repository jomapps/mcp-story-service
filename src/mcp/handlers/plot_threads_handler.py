"""Plot threads tracking tool handler with lifecycle management."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from mcp.types import CallToolResult

from ...models.story import StoryData
from ...models.analysis import AnalysisResult
from ...services.session_manager import StorySessionManager
from ...services.process_isolation import ProcessIsolationManager, ProcessConfig


class PlotThreadsHandler:
    """Handler for plot threads tracking MCP tool."""
    
    def __init__(
        self,
        session_manager: StorySessionManager,
        process_manager: ProcessIsolationManager
    ):
        """Initialize plot threads handler.
        
        Args:
            session_manager: Story session manager
            process_manager: Process isolation manager
        """
        self.session_manager = session_manager
        self.process_manager = process_manager
        self.logger = logging.getLogger(__name__)
    
    async def handle(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle plot threads tracking tool call.
        
        Args:
            arguments: Tool call arguments
            
        Returns:
            MCP tool call result
        """
        try:
            # Extract arguments
            story_content = arguments.get("story_content", "")
            session_id = arguments.get("session_id", "")
            thread_focus = arguments.get("thread_focus", "all")
            
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
                metadata={"thread_focus": thread_focus}
            )
            
            # Perform plot thread analysis
            result = await self._track_plot_threads(
                story_data=story_data,
                session=session,
                thread_focus=thread_focus
            )
            
            # Update session with results
            await self.session_manager.update_session(
                session_id=session_id,
                story_data=story_data,
                analysis_result=result
            )
            
            # Format response
            response_content = {
                "thread_focus": thread_focus,
                "confidence": result.confidence,
                "threads": result.data.get("threads", []),
                "character_arcs": result.data.get("character_arcs", {}),
                "thread_interactions": result.data.get("thread_interactions", []),
                "lifecycle_analysis": result.data.get("lifecycle_analysis", {}),
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
            self.logger.error(f"Plot threads tracking error: {e}")
            return CallToolResult(
                content=[{
                    "type": "text",
                    "text": f"Error tracking plot threads: {str(e)}"
                }],
                isError=True
            )
    
    async def _track_plot_threads(
        self,
        story_data: StoryData,
        session: Any,
        thread_focus: str
    ) -> AnalysisResult:
        """Track plot threads with lifecycle management.
        
        Args:
            story_data: Story data to analyze
            session: Story session
            thread_focus: Focus of thread tracking
            
        Returns:
            Analysis result with plot thread data
        """
        # Extract plot threads based on focus
        threads = await self._extract_plot_threads(story_data, thread_focus)
        character_arcs = await self._analyze_character_arcs(story_data, threads)
        thread_interactions = await self._analyze_thread_interactions(threads)
        lifecycle_analysis = await self._analyze_thread_lifecycle(threads)
        
        # Calculate confidence based on thread clarity and completeness
        confidence = self._calculate_thread_confidence(threads, character_arcs)
        
        # Generate recommendations
        recommendations = self._generate_thread_recommendations(
            threads, character_arcs, confidence
        )
        
        return AnalysisResult(
            analysis_type="plot_threads",
            confidence=confidence,
            data={
                "threads": threads,
                "character_arcs": character_arcs,
                "thread_interactions": thread_interactions,
                "lifecycle_analysis": lifecycle_analysis,
                "recommendations": recommendations
            },
            metadata={
                "thread_focus": thread_focus,
                "total_threads": len(threads),
                "active_characters": len(character_arcs),
                "analysis_timestamp": asyncio.get_event_loop().time()
            }
        )
    
    async def _extract_plot_threads(
        self,
        story_data: StoryData,
        thread_focus: str
    ) -> List[Dict[str, Any]]:
        """Extract plot threads from story content.
        
        Args:
            story_data: Story data to analyze
            thread_focus: Focus of thread extraction
            
        Returns:
            List of plot threads
        """
        content = story_data.content.lower()
        threads = []
        
        # Simple pattern-based thread extraction
        # In a real implementation, this would use NLP or LLM analysis
        
        if thread_focus in ["main", "all"]:
            # Main plot thread detection
            main_keywords = ["protagonist", "main character", "hero", "conflict", "goal"]
            if any(keyword in content for keyword in main_keywords):
                threads.append({
                    "id": "main_plot",
                    "type": "main",
                    "title": "Main Plot Thread",
                    "description": "Primary narrative storyline",
                    "status": "active",
                    "confidence": 0.85,
                    "key_events": self._extract_key_events(content, "main"),
                    "characters": self._extract_thread_characters(content, "main"),
                    "progression": "rising"
                })
        
        if thread_focus in ["subplot", "all"]:
            # Subplot detection
            subplot_indicators = ["subplot", "secondary", "romance", "friendship", "family"]
            for i, indicator in enumerate(subplot_indicators):
                if indicator in content:
                    threads.append({
                        "id": f"subplot_{i}",
                        "type": "subplot",
                        "title": f"{indicator.title()} Subplot",
                        "description": f"Secondary storyline involving {indicator}",
                        "status": "active",
                        "confidence": 0.70,
                        "key_events": self._extract_key_events(content, indicator),
                        "characters": self._extract_thread_characters(content, indicator),
                        "progression": "developing"
                    })
        
        if thread_focus in ["character", "all"]:
            # Character-specific threads
            character_names = self._extract_character_names(content)
            for char_name in character_names[:5]:  # Limit to top 5 characters
                threads.append({
                    "id": f"character_{char_name.lower()}",
                    "type": "character",
                    "title": f"{char_name} Character Arc",
                    "description": f"Character development arc for {char_name}",
                    "status": "active",
                    "confidence": 0.75,
                    "key_events": self._extract_character_events(content, char_name),
                    "characters": [char_name],
                    "progression": "evolving"
                })
        
        return threads
    
    async def _analyze_character_arcs(
        self,
        story_data: StoryData,
        threads: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze character development arcs.
        
        Args:
            story_data: Story data
            threads: Extracted plot threads
            
        Returns:
            Character arc analysis
        """
        character_arcs = {}
        
        # Extract all characters mentioned in threads
        all_characters = set()
        for thread in threads:
            all_characters.update(thread.get("characters", []))
        
        for character in all_characters:
            character_arcs[character] = {
                "character_name": character,
                "arc_type": self._determine_arc_type(story_data.content, character),
                "development_stage": self._analyze_development_stage(story_data.content, character),
                "key_moments": self._extract_character_moments(story_data.content, character),
                "relationships": self._analyze_character_relationships(story_data.content, character),
                "motivation": self._extract_character_motivation(story_data.content, character),
                "conflict": self._extract_character_conflict(story_data.content, character),
                "growth_trajectory": "positive"  # Simplified for demo
            }
        
        return character_arcs
    
    async def _analyze_thread_interactions(
        self,
        threads: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze interactions between plot threads.
        
        Args:
            threads: List of plot threads
            
        Returns:
            Thread interaction analysis
        """
        interactions = []
        
        for i, thread1 in enumerate(threads):
            for j, thread2 in enumerate(threads[i+1:], i+1):
                # Check for character overlap
                chars1 = set(thread1.get("characters", []))
                chars2 = set(thread2.get("characters", []))
                
                if chars1 & chars2:  # Characters in common
                    interactions.append({
                        "thread1_id": thread1["id"],
                        "thread2_id": thread2["id"],
                        "interaction_type": "character_overlap",
                        "shared_characters": list(chars1 & chars2),
                        "strength": len(chars1 & chars2) / max(len(chars1), len(chars2)),
                        "impact": "moderate"
                    })
                
                # Check for event overlap (simplified)
                events1 = set(thread1.get("key_events", []))
                events2 = set(thread2.get("key_events", []))
                
                if events1 & events2:
                    interactions.append({
                        "thread1_id": thread1["id"],
                        "thread2_id": thread2["id"],
                        "interaction_type": "event_overlap",
                        "shared_events": list(events1 & events2),
                        "strength": len(events1 & events2) / max(len(events1), len(events2)),
                        "impact": "high"
                    })
        
        return interactions
    
    async def _analyze_thread_lifecycle(
        self,
        threads: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze lifecycle stages of plot threads.
        
        Args:
            threads: List of plot threads
            
        Returns:
            Thread lifecycle analysis
        """
        lifecycle_stages = {
            "introduction": [],
            "development": [],
            "climax": [],
            "resolution": []
        }
        
        for thread in threads:
            progression = thread.get("progression", "unknown")
            
            if progression in ["rising", "developing"]:
                lifecycle_stages["development"].append(thread["id"])
            elif progression == "climactic":
                lifecycle_stages["climax"].append(thread["id"])
            elif progression == "resolved":
                lifecycle_stages["resolution"].append(thread["id"])
            else:
                lifecycle_stages["introduction"].append(thread["id"])
        
        return {
            "stages": lifecycle_stages,
            "completion_rate": len(lifecycle_stages["resolution"]) / max(len(threads), 1),
            "active_threads": len(lifecycle_stages["development"]) + len(lifecycle_stages["climax"]),
            "thread_balance": self._calculate_thread_balance(lifecycle_stages)
        }
    
    def _calculate_thread_confidence(
        self,
        threads: List[Dict[str, Any]],
        character_arcs: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for thread analysis.
        
        Args:
            threads: Extracted plot threads
            character_arcs: Character arc analysis
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        if not threads:
            return 0.0
        
        # Base confidence from thread clarity
        avg_thread_confidence = sum(t.get("confidence", 0.5) for t in threads) / len(threads)
        
        # Bonus for character development
        character_bonus = min(len(character_arcs) * 0.1, 0.2)
        
        # Bonus for thread interactions
        interaction_bonus = min(len(threads) * 0.05, 0.15)
        
        total_confidence = min(avg_thread_confidence + character_bonus + interaction_bonus, 1.0)
        
        return round(total_confidence, 3)
    
    def _generate_thread_recommendations(
        self,
        threads: List[Dict[str, Any]],
        character_arcs: Dict[str, Any],
        confidence: float
    ) -> List[str]:
        """Generate recommendations for plot thread improvement.
        
        Args:
            threads: Plot threads
            character_arcs: Character arcs
            confidence: Current confidence score
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        if confidence < 0.75:
            recommendations.append("Consider clarifying plot thread connections and character motivations")
        
        if len(threads) < 2:
            recommendations.append("Consider adding subplot or secondary storylines for narrative depth")
        
        if len(character_arcs) < 3:
            recommendations.append("Develop more character arcs to strengthen story engagement")
        
        # Check for unresolved threads
        unresolved = [t for t in threads if t.get("status") == "active"]
        if len(unresolved) > len(threads) * 0.7:
            recommendations.append("Plan resolution for active plot threads to avoid loose ends")
        
        if not recommendations:
            recommendations.append("Plot thread structure is well-balanced and engaging")
        
        return recommendations
    
    # Helper methods (simplified implementations for demo)
    
    def _extract_key_events(self, content: str, context: str) -> List[str]:
        """Extract key events for a thread context."""
        # Simplified - would use NLP in real implementation
        return [f"Event related to {context}", f"Development in {context}"]
    
    def _extract_thread_characters(self, content: str, context: str) -> List[str]:
        """Extract characters involved in a thread."""
        # Simplified - would use NER in real implementation
        return ["Protagonist", "Supporting Character"]
    
    def _extract_character_names(self, content: str) -> List[str]:
        """Extract character names from content."""
        # Simplified - would use NER in real implementation
        return ["Alice", "Bob", "Charlie"]
    
    def _extract_character_events(self, content: str, character: str) -> List[str]:
        """Extract events specific to a character."""
        return [f"{character} introduction", f"{character} conflict"]
    
    def _determine_arc_type(self, content: str, character: str) -> str:
        """Determine character arc type."""
        return "growth"  # Simplified
    
    def _analyze_development_stage(self, content: str, character: str) -> str:
        """Analyze character development stage."""
        return "developing"  # Simplified
    
    def _extract_character_moments(self, content: str, character: str) -> List[str]:
        """Extract key character moments."""
        return [f"{character} key moment"]
    
    def _analyze_character_relationships(self, content: str, character: str) -> Dict[str, str]:
        """Analyze character relationships."""
        return {"ally": "Supporting Character"}
    
    def _extract_character_motivation(self, content: str, character: str) -> str:
        """Extract character motivation."""
        return "Achieve goal"
    
    def _extract_character_conflict(self, content: str, character: str) -> str:
        """Extract character conflict."""
        return "Internal struggle"
    
    def _calculate_thread_balance(self, lifecycle_stages: Dict[str, List[str]]) -> float:
        """Calculate balance across thread lifecycle stages."""
        stage_counts = [len(stages) for stages in lifecycle_stages.values()]
        if not stage_counts or max(stage_counts) == 0:
            return 1.0
        
        # Calculate variance normalized by mean
        mean_count = sum(stage_counts) / len(stage_counts)
        variance = sum((count - mean_count) ** 2 for count in stage_counts) / len(stage_counts)
        
        # Convert to balance score (lower variance = higher balance)
        balance = max(0.0, 1.0 - (variance / (mean_count ** 2)) if mean_count > 0 else 1.0)
        
        return round(balance, 3)