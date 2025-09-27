"""Performance tests for concurrent request handling (10 simultaneous with process isolation) (T051)."""

import asyncio
import pytest
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch

from src.services.session_manager import StorySessionManager
from src.services.process_isolation import ProcessIsolationManager
from src.services.narrative.analyzer import NarrativeAnalyzer
from src.services.consistency.validator import ConsistencyValidator
from src.services.genre.analyzer import GenreAnalyzer
from src.models.story import StoryData


class TestConcurrentPerformance:
    """Performance tests for concurrent request handling."""
    
    @pytest.fixture
    async def session_manager(self):
        """Create session manager for performance testing."""
        return StorySessionManager(workspace_dir="test_workspaces_perf")
    
    @pytest.fixture
    async def process_isolation_manager(self):
        """Create process isolation manager for testing."""
        return ProcessIsolationManager()
    
    @pytest.fixture
    async def narrative_analyzer(self):
        """Create narrative analyzer for testing."""
        return NarrativeAnalyzer()
    
    @pytest.fixture
    async def consistency_validator(self):
        """Create consistency validator for testing."""
        return ConsistencyValidator()
    
    @pytest.fixture
    async def genre_analyzer(self):
        """Create genre analyzer for testing."""
        return GenreAnalyzer()
    
    @pytest.fixture
    def performance_story_datasets(self):
        """Generate story datasets with varying complexity for performance testing."""
        datasets = []
        
        # Simple stories (fast processing)
        for i in range(5):
            datasets.append({
                "project_id": f"simple-perf-{i:03d}",
                "complexity": "simple",
                "story_data": StoryData(
                    content=f"Simple story {i}: A person does something and it works out.",
                    metadata={
                        "project_id": f"simple-perf-{i:03d}",
                        "complexity": "simple",
                        "expected_duration": 0.5
                    }
                )
            })
        
        # Medium complexity stories
        for i in range(3):
            datasets.append({
                "project_id": f"medium-perf-{i:03d}",
                "complexity": "medium",
                "story_data": StoryData(
                    content=f"""
                    Medium story {i}: Detective investigates case {i} involving corporate conspiracy.
                    As investigation deepens, personal stakes increase and danger escalates.
                    Final confrontation resolves the mystery but at significant personal cost.
                    """,
                    metadata={
                        "project_id": f"medium-perf-{i:03d}",
                        "complexity": "medium",
                        "expected_duration": 1.0
                    }
                )
            })
        
        # Complex stories (slower processing)
        for i in range(2):
            datasets.append({
                "project_id": f"complex-perf-{i:03d}",
                "complexity": "complex",
                "story_data": StoryData(
                    content=f"""
                    Complex story {i}: Multi-layered narrative with interconnected character arcs.
                    Act I establishes the world and introduces complex character relationships.
                    Act II develops multiple plot threads with escalating conflicts and revelations.
                    Act III brings together all threads for complex resolution with multiple outcomes.
                    Themes include redemption, betrayal, justice, and the cost of truth.
                    """,
                    metadata={
                        "project_id": f"complex-perf-{i:03d}",
                        "complexity": "complex",
                        "expected_duration": 2.0
                    }
                )
            })
        
        return datasets
    
    @pytest.mark.asyncio
    async def test_concurrent_session_creation_performance(
        self, session_manager, performance_story_datasets
    ):
        """Test performance of concurrent session creation (10 simultaneous)."""
        async def create_session_with_timing(project_data):
            start_time = time.time()
            
            project_id = project_data["project_id"]
            session_id = await session_manager.create_session(project_id)
            
            await session_manager.update_session(
                session_id=session_id,
                story_data=project_data["story_data"]
            )
            
            end_time = time.time()
            
            return {
                "project_id": project_id,
                "session_id": session_id,
                "creation_time": end_time - start_time,
                "complexity": project_data["complexity"]
            }
        
        # Test with 10 concurrent session creations
        tasks = [
            create_session_with_timing(project_data)
            for project_data in performance_story_datasets
        ]
        
        overall_start = time.time()
        results = await asyncio.gather(*tasks)
        overall_end = time.time()
        
        # Performance assertions
        total_time = overall_end - overall_start
        creation_times = [r["creation_time"] for r in results]
        
        # All sessions should be created successfully
        assert len(results) == len(performance_story_datasets)
        
        # Individual session creation should be fast
        max_creation_time = max(creation_times)
        assert max_creation_time < 1.0  # No single session should take more than 1 second
        
        # Average creation time should be reasonable
        avg_creation_time = statistics.mean(creation_times)
        assert avg_creation_time < 0.5  # Average should be under 0.5 seconds
        
        # Concurrent execution should be faster than sequential
        estimated_sequential_time = sum(creation_times)
        assert total_time < estimated_sequential_time * 0.6  # At least 40% improvement
        
        # Performance should be consistent
        creation_time_std = statistics.stdev(creation_times)
        assert creation_time_std < 0.3  # Low variance in creation times
    
    @pytest.mark.asyncio
    async def test_concurrent_story_analysis_performance(
        self, session_manager, narrative_analyzer, performance_story_datasets
    ):
        """Test performance of concurrent story analysis operations."""
        async def analyze_story_with_timing(project_data):
            start_time = time.time()
            
            project_id = project_data["project_id"]
            story_data = project_data["story_data"]
            
            # Create session
            session_id = await session_manager.create_session(project_id)
            await session_manager.update_session(session_id, story_data)
            
            # Perform analysis
            analysis_start = time.time()
            analysis_result = await narrative_analyzer.analyze_story_structure(story_data)
            analysis_end = time.time()
            
            end_time = time.time()
            
            return {
                "project_id": project_id,
                "total_time": end_time - start_time,
                "analysis_time": analysis_end - analysis_start,
                "complexity": project_data["complexity"],
                "confidence": analysis_result.confidence,
                "success": True
            }
        
        # Run 10 concurrent analyses
        tasks = [
            analyze_story_with_timing(project_data)
            for project_data in performance_story_datasets
        ]
        
        overall_start = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        overall_end = time.time()
        
        # Filter successful results
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        
        # All analyses should complete successfully
        assert len(successful_results) >= 8  # At least 80% success rate under load
        
        # Performance by complexity
        simple_times = [r["analysis_time"] for r in successful_results if r["complexity"] == "simple"]
        medium_times = [r["analysis_time"] for r in successful_results if r["complexity"] == "medium"]
        complex_times = [r["analysis_time"] for r in successful_results if r["complexity"] == "complex"]
        
        # Simple stories should be fastest
        if simple_times:
            avg_simple_time = statistics.mean(simple_times)
            assert avg_simple_time < 1.0
        
        # Medium stories should be moderate
        if medium_times:
            avg_medium_time = statistics.mean(medium_times)
            assert avg_medium_time < 2.0
        
        # Complex stories should still complete reasonably fast
        if complex_times:
            avg_complex_time = statistics.mean(complex_times)
            assert avg_complex_time < 3.0
        
        # Overall concurrent execution should be efficient
        total_time = overall_end - overall_start
        assert total_time < 5.0  # All 10 analyses should complete within 5 seconds
        
        # Quality should not be significantly impacted by concurrency
        confidences = [r["confidence"] for r in successful_results]
        avg_confidence = statistics.mean(confidences)
        assert avg_confidence >= 0.5  # Quality should not degrade too much under load
    
    @pytest.mark.asyncio
    async def test_process_isolation_performance_overhead(
        self, session_manager, process_isolation_manager, narrative_analyzer, performance_story_datasets
    ):
        """Test performance overhead of process isolation."""
        # Test with process isolation
        async def analyze_with_isolation(project_data):
            project_id = project_data["project_id"]
            story_data = project_data["story_data"]
            
            isolation_start = time.time()
            
            # Create isolated context
            context = await process_isolation_manager.create_isolation_context(project_id)
            
            try:
                session_id = await session_manager.create_session(project_id)
                await session_manager.update_session(session_id, story_data)
                
                analysis_result = await narrative_analyzer.analyze_story_structure(story_data)
                
                isolation_end = time.time()
                
                return {
                    "project_id": project_id,
                    "time_with_isolation": isolation_end - isolation_start,
                    "context_id": context.context_id,
                    "success": True
                }
            finally:
                await process_isolation_manager.cleanup_context(context.context_id)
        
        # Test without process isolation
        async def analyze_without_isolation(project_data):
            project_id = f"{project_data['project_id']}_no_isolation"
            story_data = project_data["story_data"]
            # Update project ID to avoid conflicts
            story_data.metadata["project_id"] = project_id
            
            no_isolation_start = time.time()
            
            session_id = await session_manager.create_session(project_id)
            await session_manager.update_session(session_id, story_data)
            
            analysis_result = await narrative_analyzer.analyze_story_structure(story_data)
            
            no_isolation_end = time.time()
            
            return {
                "project_id": project_id,
                "time_without_isolation": no_isolation_end - no_isolation_start,
                "success": True
            }
        
        # Run tests with first 5 datasets
        test_datasets = performance_story_datasets[:5]
        
        # Test with isolation
        isolation_tasks = [analyze_with_isolation(pd) for pd in test_datasets]
        isolation_results = await asyncio.gather(*isolation_tasks)
        
        # Test without isolation
        no_isolation_tasks = [analyze_without_isolation(pd) for pd in test_datasets]
        no_isolation_results = await asyncio.gather(*no_isolation_tasks)
        
        # Compare performance
        isolation_times = [r["time_with_isolation"] for r in isolation_results if r["success"]]
        no_isolation_times = [r["time_without_isolation"] for r in no_isolation_results if r["success"]]
        
        assert len(isolation_times) == len(test_datasets)
        assert len(no_isolation_times) == len(test_datasets)
        
        avg_isolation_time = statistics.mean(isolation_times)
        avg_no_isolation_time = statistics.mean(no_isolation_times)
        
        # Isolation overhead should be reasonable (less than 100% overhead)
        overhead_ratio = avg_isolation_time / avg_no_isolation_time
        assert overhead_ratio < 2.0  # Less than 2x overhead
        
        # Both should still complete within reasonable time
        assert avg_isolation_time < 3.0
        assert avg_no_isolation_time < 2.0
    
    @pytest.mark.asyncio
    async def test_concurrent_multi_service_analysis_performance(
        self, session_manager, narrative_analyzer, consistency_validator, genre_analyzer, performance_story_datasets
    ):
        """Test performance of concurrent multi-service analysis."""
        async def comprehensive_analysis(project_data):
            project_id = project_data["project_id"]
            story_data = project_data["story_data"]
            
            start_time = time.time()
            
            # Create session
            session_id = await session_manager.create_session(project_id)
            await session_manager.update_session(session_id, story_data)
            
            # Run multiple analyses concurrently
            analysis_tasks = [
                narrative_analyzer.analyze_story_structure(story_data),
                consistency_validator.validate_consistency(story_data),
                genre_analyzer.apply_genre_patterns(story_data, target_genre="thriller")
            ]
            
            analysis_results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            end_time = time.time()
            
            # Count successful analyses
            successful_analyses = [r for r in analysis_results if not isinstance(r, Exception)]
            
            return {
                "project_id": project_id,
                "total_time": end_time - start_time,
                "successful_analyses": len(successful_analyses),
                "total_analyses": len(analysis_tasks),
                "complexity": project_data["complexity"]
            }
        
        # Run comprehensive analysis on first 6 datasets
        test_datasets = performance_story_datasets[:6]
        
        tasks = [comprehensive_analysis(pd) for pd in test_datasets]
        
        overall_start = time.time()
        results = await asyncio.gather(*tasks)
        overall_end = time.time()
        
        total_time = overall_end - overall_start
        
        # All projects should complete
        assert len(results) == len(test_datasets)
        
        # Most analyses should succeed
        total_successful = sum(r["successful_analyses"] for r in results)
        total_attempted = sum(r["total_analyses"] for r in results)
        success_rate = total_successful / total_attempted
        
        assert success_rate >= 0.8  # At least 80% success rate
        
        # Performance should be reasonable
        assert total_time < 8.0  # All comprehensive analyses within 8 seconds
        
        # Individual project analysis times
        individual_times = [r["total_time"] for r in results]
        max_individual_time = max(individual_times)
        avg_individual_time = statistics.mean(individual_times)
        
        assert max_individual_time < 4.0  # No single project should take more than 4 seconds
        assert avg_individual_time < 2.5  # Average should be reasonable
    
    @pytest.mark.asyncio
    async def test_sustained_load_performance(
        self, session_manager, narrative_analyzer, performance_story_datasets
    ):
        """Test performance under sustained concurrent load."""
        # Run multiple waves of concurrent requests
        waves = 3
        requests_per_wave = 4
        wave_results = []
        
        for wave in range(waves):
            wave_start = time.time()
            
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
                    "confidence": analysis_result.confidence
                }
            
            # Select datasets for this wave
            wave_datasets = performance_story_datasets[:requests_per_wave]
            wave_tasks = [wave_analysis(pd, wave) for pd in wave_datasets]
            
            wave_analysis_results = await asyncio.gather(*wave_tasks)
            wave_end = time.time()
            
            wave_metrics = {
                "wave_number": wave,
                "total_time": wave_end - wave_start,
                "analysis_times": [r["analysis_time"] for r in wave_analysis_results],
                "confidences": [r["confidence"] for r in wave_analysis_results]
            }
            wave_results.append(wave_metrics)
            
            # Small delay between waves
            await asyncio.sleep(0.1)
        
        # Analyze performance across waves
        wave_times = [w["total_time"] for w in wave_results]
        wave_avg_analysis_times = [statistics.mean(w["analysis_times"]) for w in wave_results]
        wave_avg_confidences = [statistics.mean(w["confidences"]) for w in wave_results]
        
        # Performance should not degrade significantly across waves
        first_wave_time = wave_times[0]
        last_wave_time = wave_times[-1]
        
        # Last wave should not be significantly slower
        assert last_wave_time <= first_wave_time * 1.3  # At most 30% degradation
        
        # Analysis quality should remain consistent
        confidence_variance = max(wave_avg_confidences) - min(wave_avg_confidences)
        assert confidence_variance < 0.2  # Quality should remain stable
        
        # All waves should complete within reasonable time
        for wave_time in wave_times:
            assert wave_time < 3.0
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_concurrent_load(
        self, session_manager, narrative_analyzer, performance_story_datasets
    ):
        """Test memory usage patterns under concurrent load."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        async def memory_intensive_analysis(project_data):
            project_id = project_data["project_id"]
            story_data = project_data["story_data"]
            
            session_id = await session_manager.create_session(project_id)
            await session_manager.update_session(session_id, story_data)
            
            # Perform analysis
            analysis_result = await narrative_analyzer.analyze_story_structure(story_data)
            
            # Get current memory
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            return {
                "project_id": project_id,
                "memory_mb": current_memory,
                "success": True
            }
        
        # Run concurrent memory-intensive analyses
        tasks = [memory_intensive_analysis(pd) for pd in performance_story_datasets]
        
        results = await asyncio.gather(*tasks)
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Memory usage should be reasonable
        memory_increase = final_memory - initial_memory
        
        # Should not use excessive memory (allow up to 100MB increase for testing)
        assert memory_increase < 100  # MB
        
        # All analyses should complete successfully
        successful_results = [r for r in results if r["success"]]
        assert len(successful_results) == len(performance_story_datasets)
        
        # Memory usage should not grow linearly with concurrent requests
        max_memory = max(r["memory_mb"] for r in successful_results)
        memory_efficiency = max_memory / len(performance_story_datasets)
        
        # Should be more efficient than linear growth
        assert memory_efficiency < initial_memory + 10  # Should not add 10MB per request
    
    @pytest.mark.asyncio
    async def test_error_handling_performance_under_load(
        self, session_manager, narrative_analyzer, performance_story_datasets
    ):
        """Test error handling performance when some requests fail."""
        async def analysis_with_simulated_failures(project_data):
            project_id = project_data["project_id"]
            story_data = project_data["story_data"]
            
            # Simulate random failures for some requests
            if "simple-perf-002" in project_id or "medium-perf-001" in project_id:
                raise Exception(f"Simulated failure for {project_id}")
            
            session_id = await session_manager.create_session(project_id)
            await session_manager.update_session(session_id, story_data)
            
            analysis_result = await narrative_analyzer.analyze_story_structure(story_data)
            
            return {
                "project_id": project_id,
                "success": True,
                "confidence": analysis_result.confidence
            }
        
        # Run with simulated failures
        tasks = [analysis_with_simulated_failures(pd) for pd in performance_story_datasets]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # Separate successful and failed results
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed_results = [r for r in results if isinstance(r, Exception)]
        
        # Should have expected number of failures (2 simulated failures)
        assert len(failed_results) == 2
        assert len(successful_results) == len(performance_story_datasets) - 2
        
        # Failures should not significantly impact overall performance
        assert total_time < 4.0  # Should complete quickly despite failures
        
        # Successful requests should still maintain quality
        if successful_results:
            avg_confidence = statistics.mean(r["confidence"] for r in successful_results)
            assert avg_confidence >= 0.5