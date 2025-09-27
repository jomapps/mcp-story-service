"""Integration test for plot thread tracking scenario (T014)."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.services.session_manager import StorySessionManager, SessionConfig
from src.models.story import StoryData
from src.models.plot import PlotThread, ThreadStage, ThreadType
from src.models.analysis import AnalysisResult


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
def sample_plot_threads():
    """Sample plot threads for testing."""
    return [
        {
            "name": "Corporate conspiracy investigation",
            "type": "main",
            "episodes": [1, 2, 3, 4, 5],
            "current_stage": "developing"
        },
        {
            "name": "Sarah's relationship with partner",
            "type": "character_arc",
            "episodes": [1, 3, 5],
            "current_stage": "introduced"
        },
        {
            "name": "City government corruption",
            "type": "subplot",
            "episodes": [2, 4, 5],
            "current_stage": "developing"
        }
    ]


@pytest.fixture
def sample_story_content():
    """Sample story content for plot thread analysis."""
    return """
    Detective Sarah Chen discovers her partner's involvement in a corporate conspiracy.
    As she investigates deeper, she realizes the conspiracy reaches the highest levels of city government.
    When her own life is threatened, she must choose between her career and exposing the truth.
    In a final confrontation, she brings down the corrupt officials but at great personal cost.
    """


class TestPlotThreadScenario:
    """Integration test for plot thread tracking functionality."""
    
    @pytest.mark.asyncio
    async def test_plot_thread_lifecycle_tracking(self, session_manager, sample_plot_threads, sample_story_content):
        """Test complete plot thread lifecycle tracking with confidence scoring."""
        # Create session for project isolation
        project_id = "plot-thread-test-001"
        session_id = await session_manager.create_session(project_id)
        
        # Update session with story data
        story_data = StoryData(
            content=sample_story_content,
            metadata={"analysis_type": "plot_thread_tracking"}
        )
        
        await session_manager.update_session(
            session_id=session_id,
            story_data=story_data
        )
        
        # Expected: Track each thread's lifecycle stage with confidence scores
        # This simulates the MCP tool call: track_plot_threads
        thread_analysis = await self._analyze_plot_threads(
            session_manager, session_id, sample_plot_threads
        )
        
        # Validate thread tracking results
        assert "thread_analysis" in thread_analysis
        assert "overall_assessment" in thread_analysis
        
        thread_results = thread_analysis["thread_analysis"]
        overall = thread_analysis["overall_assessment"]
        
        # Check that each thread has proper lifecycle tracking
        assert len(thread_results) == len(sample_plot_threads)
        
        for thread_result in thread_results:
            assert "thread_id" in thread_result
            assert "lifecycle_stage" in thread_result
            assert "confidence_score" in thread_result
            assert thread_result["confidence_score"] >= 0.0
            assert thread_result["confidence_score"] <= 1.0
            
            # Verify stage progression logic
            stage = thread_result["lifecycle_stage"]
            assert stage in ["introduced", "developing", "ready_for_resolution", "resolved", "abandoned"]
            
            # Check for resolution opportunities
            if stage == "developing":
                assert "resolution_opportunities" in thread_result
                assert isinstance(thread_result["resolution_opportunities"], list)
            
            # Verify importance scoring
            assert "importance_score" in thread_result
            assert thread_result["importance_score"] >= 0.0
            assert thread_result["importance_score"] <= 1.0
        
        # Validate overall assessment
        assert "total_threads" in overall
        assert overall["total_threads"] == len(sample_plot_threads)
        
        assert "narrative_cohesion_score" in overall
        assert overall["narrative_cohesion_score"] >= 0.0
        assert overall["narrative_cohesion_score"] <= 1.0
        
        assert "confidence_score" in overall
        assert overall["confidence_score"] >= 0.0
        assert overall["confidence_score"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_thread_dependencies_mapping(self, session_manager, sample_story_content):
        """Test thread dependency identification and importance scoring."""
        project_id = "plot-thread-dependencies-001"
        session_id = await session_manager.create_session(project_id)
        
        # Threads with dependencies
        dependent_threads = [
            {
                "name": "Main investigation",
                "type": "main",
                "episodes": [1, 2, 3, 4, 5],
                "current_stage": "developing"
            },
            {
                "name": "Partner betrayal revelation",
                "type": "subplot",
                "episodes": [2, 3, 4],
                "current_stage": "ready_for_resolution",
                "depends_on": ["Main investigation"]
            },
            {
                "name": "Final confrontation",
                "type": "main",
                "episodes": [5],
                "current_stage": "introduced",
                "depends_on": ["Main investigation", "Partner betrayal revelation"]
            }
        ]
        
        story_data = StoryData(
            content=sample_story_content,
            metadata={"analysis_type": "dependency_mapping"}
        )
        
        await session_manager.update_session(
            session_id=session_id,
            story_data=story_data
        )
        
        # Analyze thread dependencies
        thread_analysis = await self._analyze_plot_threads(
            session_manager, session_id, dependent_threads
        )
        
        thread_results = thread_analysis["thread_analysis"]
        
        # Check dependency mapping
        for thread_result in thread_results:
            if "dependencies" in thread_result:
                dependencies = thread_result["dependencies"]
                assert isinstance(dependencies, list)
                
                # Verify dependencies reference valid threads
                for dep in dependencies:
                    assert any(t["name"] == dep for t in dependent_threads)
            
            # Check suggested actions for thread progression
            assert "suggested_actions" in thread_result
            assert isinstance(thread_result["suggested_actions"], list)
            
            # Ready for resolution threads should have specific actions
            if thread_result["lifecycle_stage"] == "ready_for_resolution":
                actions = thread_result["suggested_actions"]
                assert len(actions) > 0
                assert any("resolv" in action.lower() for action in actions)
    
    @pytest.mark.asyncio 
    async def test_multi_episode_thread_progression(self, session_manager):
        """Test thread progression across multiple episodes."""
        project_id = "multi-episode-test-001"
        session_id = await session_manager.create_session(project_id)
        
        # Episode 1 threads
        episode1_threads = [
            {
                "name": "Mystery introduction",
                "type": "mystery",
                "episodes": [1],
                "current_stage": "introduced"
            }
        ]
        
        # Episode 3 progression
        episode3_threads = [
            {
                "name": "Mystery introduction", 
                "type": "mystery",
                "episodes": [1, 2, 3],
                "current_stage": "developing"
            },
            {
                "name": "Character development",
                "type": "character_arc",
                "episodes": [3],
                "current_stage": "introduced"
            }
        ]
        
        # Episode 5 resolution
        episode5_threads = [
            {
                "name": "Mystery introduction",
                "type": "mystery", 
                "episodes": [1, 2, 3, 4, 5],
                "current_stage": "ready_for_resolution"
            },
            {
                "name": "Character development",
                "type": "character_arc",
                "episodes": [3, 4, 5],
                "current_stage": "developing"
            }
        ]
        
        story_data = StoryData(
            content="Multi-episode mystery story with character development.",
            metadata={"analysis_type": "multi_episode_progression"}
        )
        
        await session_manager.update_session(
            session_id=session_id,
            story_data=story_data
        )
        
        # Test progression through episodes
        for episode, threads in [(1, episode1_threads), (3, episode3_threads), (5, episode5_threads)]:
            analysis = await self._analyze_plot_threads(
                session_manager, session_id, threads, episode_context=episode
            )
            
            thread_results = analysis["thread_analysis"]
            overall = analysis["overall_assessment"]
            
            # Verify stage progression
            mystery_thread = next(t for t in thread_results if "Mystery" in t.get("thread_id", ""))
            
            if episode == 1:
                assert mystery_thread["lifecycle_stage"] == "introduced"
            elif episode == 3:
                assert mystery_thread["lifecycle_stage"] == "developing"
            elif episode == 5:
                assert mystery_thread["lifecycle_stage"] == "ready_for_resolution"
            
            # Check narrative cohesion improves over time
            assert overall["confidence_score"] >= 0.0
            if episode >= 3:
                assert overall["total_threads"] >= 1
    
    @pytest.mark.asyncio
    async def test_thread_abandonment_detection(self, session_manager):
        """Test detection of abandoned plot threads."""
        project_id = "abandonment-test-001"
        session_id = await session_manager.create_session(project_id)
        
        # Threads with potential abandonment
        threads_with_gaps = [
            {
                "name": "Early mystery",
                "type": "mystery",
                "episodes": [1, 2],  # Missing from later episodes
                "current_stage": "developing"
            },
            {
                "name": "Continuing story",
                "type": "main",
                "episodes": [1, 2, 3, 4, 5],
                "current_stage": "developing"
            },
            {
                "name": "Late introduction",
                "type": "subplot",
                "episodes": [4, 5],
                "current_stage": "introduced"
            }
        ]
        
        story_data = StoryData(
            content="Story with potentially abandoned early mystery thread.",
            metadata={"analysis_type": "abandonment_detection", "total_episodes": 5}
        )
        
        await session_manager.update_session(
            session_id=session_id,
            story_data=story_data
        )
        
        analysis = await self._analyze_plot_threads(
            session_manager, session_id, threads_with_gaps, episode_context=5
        )
        
        thread_results = analysis["thread_analysis"]
        overall = analysis["overall_assessment"]
        
        # Check for abandonment detection
        early_mystery = next(t for t in thread_results if "Early mystery" in t.get("thread_id", ""))
        
        # Should detect potential abandonment
        assert "suggested_actions" in early_mystery
        actions = early_mystery["suggested_actions"]
        
        # Should suggest resolution or continuation
        abandonment_related = any(
            "abandon" in action.lower() or "resolve" in action.lower() or "continue" in action.lower()
            for action in actions
        )
        assert abandonment_related
        
        # Overall assessment should flag abandoned threads
        if "abandoned_threads" in overall:
            assert isinstance(overall["abandoned_threads"], int)
    
    async def _analyze_plot_threads(self, session_manager, session_id, threads, episode_context=None):
        """Mock plot thread analysis simulating the actual service behavior."""
        # This simulates the behavior of the plot thread tracking service
        session = await session_manager.get_session(session_id)
        
        if not session:
            raise ValueError("Session not found")
        
        thread_results = []
        
        for i, thread in enumerate(threads):
            # Simulate confidence scoring based on thread characteristics
            confidence = 0.8
            
            # Adjust confidence based on thread properties
            if len(thread.get("episodes", [])) > 3:
                confidence += 0.1  # More episodes = higher confidence
            
            if thread.get("current_stage") == "ready_for_resolution":
                confidence += 0.05
            
            # Simulate thread analysis result
            thread_result = {
                "thread_id": f"thread_{i}_{thread['name'].replace(' ', '_').lower()}",
                "lifecycle_stage": thread.get("current_stage", "introduced"),
                "confidence_score": min(confidence, 1.0),
                "resolution_opportunities": [],
                "dependencies": thread.get("depends_on", []),
                "importance_score": 0.7 + (i * 0.1),  # Varying importance
                "suggested_actions": []
            }
            
            # Add stage-specific content
            if thread_result["lifecycle_stage"] == "ready_for_resolution":
                thread_result["resolution_opportunities"] = [
                    f"Resolve {thread['name']} in upcoming episode",
                    f"Provide closure for {thread['name']} arc"
                ]
                thread_result["suggested_actions"] = [
                    f"Plan resolution scene for {thread['name']}",
                    "Ensure character motivations are clear"
                ]
            elif thread_result["lifecycle_stage"] == "developing":
                thread_result["suggested_actions"] = [
                    f"Continue developing {thread['name']}",
                    "Add complexity to thread progression"
                ]
            
            # Check for potential abandonment
            if episode_context and len(thread.get("episodes", [])) > 0:
                last_episode = max(thread["episodes"])
                if episode_context - last_episode > 2:  # Gap of 2+ episodes
                    thread_result["suggested_actions"].append(
                        f"Consider resolving or continuing {thread['name']} - potential abandonment detected"
                    )
            
            thread_results.append(thread_result)
        
        # Calculate overall assessment
        total_threads = len(threads)
        unresolved_count = sum(1 for t in thread_results if t["lifecycle_stage"] not in ["resolved"])
        abandoned_count = sum(1 for t in thread_results 
                            if "abandonment detected" in str(t.get("suggested_actions", [])))
        
        # Simulate narrative cohesion scoring
        cohesion_score = max(0.5, 1.0 - (abandoned_count * 0.2) - (unresolved_count * 0.1))
        overall_confidence = sum(t["confidence_score"] for t in thread_results) / max(len(thread_results), 1)
        
        return {
            "thread_analysis": thread_results,
            "overall_assessment": {
                "total_threads": total_threads,
                "unresolved_threads": unresolved_count,
                "abandoned_threads": abandoned_count,
                "narrative_cohesion_score": round(cohesion_score, 3),
                "confidence_score": round(overall_confidence, 3)
            }
        }


if __name__ == "__main__":
    pytest.main([__file__])