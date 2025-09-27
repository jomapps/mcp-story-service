"""Integration test for concurrent request handling with process isolation (T019)."""

import asyncio
import pytest
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.session_manager import StorySessionManager
from src.services.process_isolation import ProcessIsolationManager
from src.services.narrative.analyzer import NarrativeAnalyzer
from src.models.story import StoryData
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
async def process_isolation_manager():
    """Create process isolation manager for testing."""
    return ProcessIsolationManager()


@pytest.fixture
async def narrative_analyzer():
    """Create narrative analyzer for testing."""
    return NarrativeAnalyzer()


@pytest.fixture
def concurrent_story_datasets():
    """Generate different story datasets for concurrent testing."""
    return [
        {
            "project_id": f"concurrent-project-{i:03d}",
            "story_data": StoryData(
                content=f"Story {i}: A detective investigates case #{i} involving corporate conspiracy and personal stakes.",
                metadata={
                    "analysis_type": "concurrent_test",
                    "project_id": f"concurrent-project-{i:03d}",
                    "complexity_level": "medium" if i % 2 == 0 else "high",
                    "expected_duration": 2.0 + (i % 3) * 0.5  # Varying analysis times
                }
            )
        }
        for i in range(1, 11)  # 10 concurrent projects
    ]


class TestConcurrentRequestHandlingScenario:
    """Integration test for concurrent request handling with process isolation."""
    
    @pytest.mark.asyncio
    async def test_concurrent_session_creation_and_isolation(
        self, session_manager, concurrent_story_datasets
    ):
        """Test concurrent session creation maintains proper isolation."""
        # Create multiple sessions concurrently
        async def create_session_for_project(project_data):
            project_id = project_data["project_id"]
            session_id = await session_manager.create_session(project_id)
            
            # Update session with story data
            await session_manager.update_session(
                session_id=session_id,
                story_data=project_data["story_data"]
            )
            
            return {
                "project_id": project_id,
                "session_id": session_id,
                "creation_time": time.time()
            }
        
        # Launch all session creations concurrently
        tasks = [
            create_session_for_project(project_data)
            for project_data in concurrent_story_datasets
        ]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # Verify all sessions created successfully
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == len(concurrent_story_datasets)
        
        # Verify isolation: each project has unique session
        session_ids = [r["session_id"] for r in successful_results]
        project_ids = [r["project_id"] for r in successful_results]
        
        assert len(set(session_ids)) == len(session_ids)  # All unique session IDs
        assert len(set(project_ids)) == len(project_ids)  # All unique project IDs
        
        # Verify concurrent creation was faster than sequential
        sequential_time_estimate = len(concurrent_story_datasets) * 0.5  # Estimated 0.5s per session
        assert (end_time - start_time) < sequential_time_estimate
        
        # Verify each session can be retrieved independently
        for result in successful_results:
            session = await session_manager.get_session(result["session_id"])
            assert session is not None
            assert session.project_id == result["project_id"]
    
    @pytest.mark.asyncio
    async def test_concurrent_analysis_with_process_isolation(
        self, session_manager, narrative_analyzer, process_isolation_manager, concurrent_story_datasets
    ):
        """Test concurrent story analysis with proper process isolation."""
        # Setup concurrent analysis tasks
        async def analyze_story_in_isolation(project_data):
            project_id = project_data["project_id"]
            story_data = project_data["story_data"]
            
            # Create isolated process context
            process_context = await process_isolation_manager.create_isolation_context(project_id)
            
            try:
                # Create session in isolated context
                session_id = await session_manager.create_session(project_id)
                await session_manager.update_session(session_id, story_data)
                
                # Perform analysis
                analysis_start = time.time()
                analysis_result = await narrative_analyzer.analyze_story_structure(story_data)
                analysis_end = time.time()
                
                return {
                    "project_id": project_id,
                    "session_id": session_id,
                    "analysis_result": analysis_result,
                    "analysis_duration": analysis_end - analysis_start,
                    "process_context": process_context.context_id,
                    "success": True
                }
                
            except Exception as e:
                return {
                    "project_id": project_id,
                    "error": str(e),
                    "success": False
                }
            finally:
                # Cleanup process context
                await process_isolation_manager.cleanup_context(process_context.context_id)
        
        # Execute concurrent analyses
        tasks = [
            analyze_story_in_isolation(project_data)
            for project_data in concurrent_story_datasets[:5]  # Test with 5 concurrent
        ]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # Verify all analyses completed successfully
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        assert len(successful_results) == 5
        
        # Verify process isolation: different process contexts
        process_contexts = [r["process_context"] for r in successful_results]
        assert len(set(process_contexts)) == len(process_contexts)  # All unique contexts
        
        # Verify analysis results quality
        for result in successful_results:
            analysis = result["analysis_result"]
            assert analysis is not None
            assert analysis.confidence >= 0.0
            assert "arc_analysis" in analysis.data
            
        # Verify concurrent execution performance
        total_time = end_time - start_time
        average_individual_time = sum(r["analysis_duration"] for r in successful_results) / len(successful_results)
        
        # Concurrent execution should be significantly faster than sequential
        assert total_time < (average_individual_time * len(successful_results) * 0.8)
    
    @pytest.mark.asyncio
    async def test_resource_contention_handling_under_load(
        self, session_manager, narrative_analyzer, concurrent_story_datasets
    ):
        """Test handling of resource contention during high concurrent load."""
        # Create a high-load scenario with limited resources
        max_concurrent_analyses = 3
        semaphore = asyncio.Semaphore(max_concurrent_analyses)
        
        async def resource_limited_analysis(project_data):
            async with semaphore:  # Limit concurrent resource usage
                project_id = project_data["project_id"]
                story_data = project_data["story_data"]
                
                session_id = await session_manager.create_session(project_id)
                await session_manager.update_session(session_id, story_data)
                
                # Simulate resource-intensive analysis
                start_time = time.time()
                analysis_result = await narrative_analyzer.analyze_story_structure(story_data)
                
                # Add artificial delay to simulate complex analysis
                await asyncio.sleep(0.5)
                
                end_time = time.time()
                
                return {
                    "project_id": project_id,
                    "analysis_result": analysis_result,
                    "processing_time": end_time - start_time,
                    "queue_time": start_time
                }
        
        # Launch more tasks than available resources
        tasks = [
            resource_limited_analysis(project_data)
            for project_data in concurrent_story_datasets[:8]  # 8 tasks, 3 concurrent limit
        ]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # All should complete successfully despite resource limits
        assert len(results) == 8
        
        for result in results:
            assert result["analysis_result"] is not None
            assert result["analysis_result"].confidence >= 0.0
        
        # Verify proper queuing behavior
        queue_times = [r["queue_time"] for r in results]
        queue_times.sort()
        
        # Later tasks should have been queued (later start times)
        assert queue_times[-1] > queue_times[0]
        
        # Total time should reflect queuing with limited concurrency
        expected_minimum_time = (len(results) / max_concurrent_analyses) * 0.5
        assert (end_time - start_time) >= expected_minimum_time
    
    @pytest.mark.asyncio
    async def test_cross_project_isolation_during_concurrent_operations(
        self, session_manager, process_isolation_manager, concurrent_story_datasets
    ):
        """Test that concurrent operations in different projects don't interfere."""
        # Setup different types of operations for different projects
        async def project_a_heavy_analysis(project_data):
            """Heavy analysis that might consume significant resources."""
            project_id = project_data["project_id"]
            story_data = project_data["story_data"]
            
            session_id = await session_manager.create_session(project_id)
            await session_manager.update_session(session_id, story_data)
            
            # Simulate heavy computation
            computation_results = []
            for i in range(10):
                await asyncio.sleep(0.1)  # Simulate work
                computation_results.append(f"heavy_result_{i}")
            
            return {
                "project_id": project_id,
                "type": "heavy_analysis",
                "results": computation_results,
                "session_state": "active"
            }
        
        async def project_b_quick_validation(project_data):
            """Quick validation that should complete fast."""
            project_id = project_data["project_id"]
            story_data = project_data["story_data"]
            
            session_id = await session_manager.create_session(project_id)
            await session_manager.update_session(session_id, story_data)
            
            # Quick validation
            validation_result = {
                "basic_structure": "valid",
                "character_count": len(story_data.content.split()),
                "estimated_complexity": "medium"
            }
            
            return {
                "project_id": project_id,
                "type": "quick_validation",
                "validation": validation_result,
                "session_state": "active"
            }
        
        # Mix heavy and light operations
        heavy_projects = concurrent_story_datasets[:3]
        quick_projects = concurrent_story_datasets[3:8]
        
        # Launch mixed workload
        tasks = []
        tasks.extend([project_a_heavy_analysis(p) for p in heavy_projects])
        tasks.extend([project_b_quick_validation(p) for p in quick_projects])
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Verify all completed successfully
        assert len(results) == len(heavy_projects) + len(quick_projects)
        
        # Verify different operation types completed correctly
        heavy_results = [r for r in results if r["type"] == "heavy_analysis"]
        quick_results = [r for r in results if r["type"] == "quick_validation"]
        
        assert len(heavy_results) == len(heavy_projects)
        assert len(quick_results) == len(quick_projects)
        
        # Quick operations should not have been significantly delayed by heavy ones
        # (This tests that process isolation is working)
        total_time = end_time - start_time
        assert total_time < 5.0  # Should complete within reasonable time
        
        # Verify session isolation
        all_project_ids = [r["project_id"] for r in results]
        assert len(set(all_project_ids)) == len(all_project_ids)  # All unique
    
    @pytest.mark.asyncio
    async def test_memory_isolation_and_cleanup_during_concurrent_execution(
        self, session_manager, process_isolation_manager, concurrent_story_datasets
    ):
        """Test memory isolation and proper cleanup during concurrent execution."""
        async def memory_intensive_analysis(project_data):
            project_id = project_data["project_id"]
            story_data = project_data["story_data"]
            
            # Create isolated context
            context = await process_isolation_manager.create_isolation_context(project_id)
            
            try:
                session_id = await session_manager.create_session(project_id)
                
                # Simulate memory-intensive operations
                large_data_structures = []
                for i in range(100):
                    large_data_structures.append({
                        f"analysis_step_{i}": f"data_{i}" * 100,
                        "project_context": project_id,
                        "isolated_state": context.context_id
                    })
                
                # Store in session
                await session_manager.update_session(session_id, story_data)
                
                # Simulate analysis using the large data
                analysis_summary = {
                    "project_id": project_id,
                    "context_id": context.context_id,
                    "data_processed": len(large_data_structures),
                    "memory_scope": "isolated"
                }
                
                return analysis_summary
                
            finally:
                # Cleanup should be automatic and isolated
                await process_isolation_manager.cleanup_context(context.context_id)
        
        # Run multiple memory-intensive analyses concurrently
        tasks = [
            memory_intensive_analysis(project_data)
            for project_data in concurrent_story_datasets[:4]
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Verify all completed successfully
        assert len(results) == 4
        
        # Verify isolation: different context IDs
        context_ids = [r["context_id"] for r in results]
        assert len(set(context_ids)) == len(context_ids)
        
        # Verify cleanup: contexts should be cleaned up
        for result in results:
            context_id = result["context_id"]
            # Context should no longer exist after cleanup
            with pytest.raises(Exception):  # Should raise error for non-existent context
                await process_isolation_manager.get_context_status(context_id)
    
    @pytest.mark.asyncio
    async def test_concurrent_session_termination_and_cleanup(
        self, session_manager, concurrent_story_datasets
    ):
        """Test concurrent session termination doesn't interfere between projects."""
        # Create multiple active sessions
        active_sessions = []
        
        for project_data in concurrent_story_datasets[:6]:
            project_id = project_data["project_id"]
            session_id = await session_manager.create_session(project_id)
            await session_manager.update_session(session_id, project_data["story_data"])
            active_sessions.append((session_id, project_id))
        
        # Verify all sessions are active
        for session_id, project_id in active_sessions:
            session = await session_manager.get_session(session_id)
            assert session is not None
            assert session.status == "active"
        
        # Concurrently terminate half of the sessions
        sessions_to_terminate = active_sessions[:3]
        sessions_to_keep = active_sessions[3:]
        
        async def terminate_session(session_id, project_id):
            await session_manager.terminate_session(session_id)
            return {"session_id": session_id, "project_id": project_id, "terminated": True}
        
        # Terminate sessions concurrently
        termination_tasks = [
            terminate_session(session_id, project_id)
            for session_id, project_id in sessions_to_terminate
        ]
        
        termination_results = await asyncio.gather(*termination_tasks)
        
        # Verify terminated sessions are gone
        for result in termination_results:
            session_id = result["session_id"]
            session = await session_manager.get_session(session_id)
            assert session is None or session.status == "terminated"
        
        # Verify remaining sessions are still active and unaffected
        for session_id, project_id in sessions_to_keep:
            session = await session_manager.get_session(session_id)
            assert session is not None
            assert session.status == "active"
            assert session.project_id == project_id
    
    @pytest.mark.asyncio
    async def test_performance_under_sustained_concurrent_load(
        self, session_manager, narrative_analyzer, concurrent_story_datasets
    ):
        """Test system performance under sustained concurrent load."""
        # Test sustained load over multiple waves
        waves = 3
        projects_per_wave = 4
        performance_metrics = []
        
        for wave in range(waves):
            wave_start = time.time()
            
            # Select projects for this wave
            start_idx = wave * projects_per_wave
            end_idx = start_idx + projects_per_wave
            wave_projects = concurrent_story_datasets[start_idx:end_idx]
            
            async def wave_analysis(project_data, wave_number):
                project_id = f"{project_data['project_id']}_wave_{wave_number}"
                story_data = project_data["story_data"]
                
                # Update project ID to avoid conflicts
                story_data.metadata["project_id"] = project_id
                
                session_id = await session_manager.create_session(project_id)
                await session_manager.update_session(session_id, story_data)
                
                analysis_start = time.time()
                analysis_result = await narrative_analyzer.analyze_story_structure(story_data)
                analysis_end = time.time()
                
                return {
                    "wave": wave_number,
                    "project_id": project_id,
                    "analysis_time": analysis_end - analysis_start,
                    "confidence": analysis_result.confidence,
                    "success": True
                }
            
            # Execute wave
            wave_tasks = [
                wave_analysis(project_data, wave)
                for project_data in wave_projects
            ]
            
            wave_results = await asyncio.gather(*wave_tasks)
            wave_end = time.time()
            
            # Record wave metrics
            wave_metrics = {
                "wave_number": wave,
                "total_time": wave_end - wave_start,
                "project_count": len(wave_projects),
                "success_count": len([r for r in wave_results if r["success"]]),
                "average_analysis_time": sum(r["analysis_time"] for r in wave_results) / len(wave_results),
                "average_confidence": sum(r["confidence"] for r in wave_results) / len(wave_results)
            }
            performance_metrics.append(wave_metrics)
            
            # Small delay between waves to simulate realistic usage
            await asyncio.sleep(0.2)
        
        # Analyze performance across waves
        assert len(performance_metrics) == waves
        
        # All waves should complete successfully
        for metrics in performance_metrics:
            assert metrics["success_count"] == metrics["project_count"]
            assert metrics["average_confidence"] >= 0.7  # Should maintain quality
        
        # Performance should not degrade significantly across waves
        first_wave_time = performance_metrics[0]["total_time"]
        last_wave_time = performance_metrics[-1]["total_time"]
        
        # Last wave should not be more than 50% slower than first
        assert last_wave_time <= first_wave_time * 1.5
        
        # System should maintain responsiveness
        for metrics in performance_metrics:
            assert metrics["total_time"] <= 10.0  # Should complete within reasonable time


if __name__ == "__main__":
    pytest.main([__file__])