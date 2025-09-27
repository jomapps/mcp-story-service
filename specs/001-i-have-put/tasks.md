# Tasks: MCP Story Service - Standalone Narrative Intelligence Server

**Input**: Design documents from `D:\Projects\mcp-story-service\specs\001-i-have-put\`
**Prerequisites**: plan.md (✓), research.md (✓), data-model.md (✓), contracts/ (✓), quickstart.md (✓)

## Execution Flow (main)
```
1. Load plan.md from feature directory → ✓ Tech stack: Python 3.11+, MCP protocol, asyncio
2. Load optional design documents → ✓ All design docs available
3. Generate tasks by category → ✓ Setup, Tests, Core, Integration, Polish
4. Apply task rules → ✓ [P] for parallel, TDD ordering, process isolation
5. Number tasks sequentially → ✓ T001-T052
6. Generate dependency graph → ✓ Listed below
7. Create parallel execution examples → ✓ Grouped examples provided
8. Validate task completeness → ✓ All contracts, entities, scenarios covered
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `src/`, `tests/` at repository root per plan.md structure

## Phase 3.1: Setup

- [x] T001 Create project structure per implementation plan (src/, tests/, config/ directories with narrative analysis structure)
- [x] T002 Initialize Python 3.11+ project with MCP protocol dependencies (pyproject.toml with mcp, asyncio, redis, pytest dependencies)
- [x] T003 [P] Configure linting and formatting tools (ruff, black, mypy configuration files)
- [x] T004 [P] Create 15+ genre template files in config/genres/ (thriller.yaml, drama.yaml, comedy.yaml, action.yaml, horror.yaml, romance.yaml, sci-fi.yaml, fantasy.yaml, mystery.yaml, western.yaml, war.yaml, historical.yaml, biographical.yaml, documentary.yaml, animation.yaml)
- [x] T005 [P] Create narrative pattern libraries in config/patterns/ (three-act.yaml, hero-journey.yaml, pacing-templates.yaml)

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### MCP Protocol Contract Tests
- [x] T006 [P] Contract test analyze_story_structure tool in tests/contract/test_story_structure_tool.py
- [x] T007 [P] Contract test track_plot_threads tool in tests/contract/test_plot_threads_tool.py 
- [x] T008 [P] Contract test validate_consistency tool in tests/contract/test_consistency_tool.py
- [x] T009 [P] Contract test apply_genre_patterns tool in tests/contract/test_genre_patterns_tool.py
- [x] T010 [P] Contract test get_story_session tool in tests/contract/test_session_tool.py
- [x] T011 [P] Contract test calculate_pacing tool in tests/contract/test_pacing_tool.py

### Integration Tests (Quickstart Scenarios)
- [x] T012 [P] Integration test story structure analysis scenario in tests/integration/test_story_structure_scenario.py
- [x] T013 [P] Integration test malformed content handling scenario in tests/integration/test_malformed_content_scenario.py
- [x] T017 [P] Integration test session continuity with process isolation scenario in tests/integration/test_session_isolation_scenario.py
- [x] T014 [P] Integration test plot thread tracking scenario in tests/integration/test_plot_thread_scenario.py
- [x] T015 [P] Integration test consistency validation scenario in tests/integration/test_consistency_scenario.py
- [x] T016 [P] Integration test genre pattern application scenario in tests/integration/test_genre_scenario.py
- [x] T018 [P] Integration test integration failure handling scenario in tests/integration/test_integration_failure_scenario.py
- [x] T019 [P] Integration test concurrent request handling with process isolation in tests/integration/test_concurrent_requests.py

## Phase 3.3: Core Models (ONLY after tests are failing)

### Data Models
- [x] T020 [P] StoryArc model with confidence scoring and project isolation in src/models/story_arc.py
- [x] T021 [P] PlotThread model with lifecycle stages and confidence tracking in src/models/plot_thread.py
- [x] T022 [P] NarrativeBeat model with emotional impact and tension scoring in src/models/narrative_beat.py
- [x] T023 [P] CharacterJourney model with arc types and state progression in src/models/character_journey.py
- [x] T024 [P] GenreTemplate model with conventions and authenticity rules in src/models/genre_template.py
- [x] T025 [P] ConsistencyRule model with validation logic and severity levels in src/models/consistency_rule.py
- [x] T026 [P] StorySession model with process isolation context in src/models/story_session.py
- [x] T027 [P] ContentAnalysisResult model for malformed content handling in src/models/content_analysis.py

### Service Layer
- [x] T028 NarrativeAnalyzer service with three-act structure identification in src/services/narrative/analyzer.py
- [x] T029 ConsistencyValidator service with plot hole detection and confidence scoring in src/services/consistency/validator.py 
- [x] T030 GenreAnalyzer service with 75% confidence threshold pattern matching in src/services/genre/analyzer.py
- [x] T031 PacingCalculator service with tension curve analysis in src/services/pacing/calculator.py
- [x] T032 StorySessionManager service with process isolation and persistence policies in src/services/session_manager.py
- [x] T033 ProcessIsolationManager service for separate analysis processes per project in src/services/process_isolation.py

## Phase 3.4: MCP Protocol Implementation

### MCP Server Core
- [x] T034 MCP server setup with asyncio and process isolation in src/mcp/server.py
- [x] T035 Story structure analysis tool handler with confidence scoring in src/mcp/handlers/story_structure_handler.py
- [x] T036 Plot threads tracking tool handler with lifecycle management in src/mcp/handlers/plot_threads_handler.py
- [x] T037 Consistency validation tool handler with severity ratings in src/mcp/handlers/consistency_handler.py
- [x] T038 Genre patterns tool handler with 75% confidence threshold in src/mcp/handlers/genre_patterns_handler.py
- [x] T039 Session management tool handler with persistence until completion in src/mcp/handlers/session_handler.py
- [x] T040 Pacing calculation tool handler with quality prioritization in src/mcp/handlers/pacing_handler.py

### MCP Tool Definitions
- [x] T041 Register all MCP tools with protocol compliance in src/mcp/tools/tool_registry.py

## Phase 3.5: Integration & Configuration

- [x] T042 Redis connection and session state management with project isolation in src/lib/redis_client.py
- [x] T043 Load 15+ genre templates from config files with validation in src/lib/genre_loader.py
- [x] T044 Error handling and logging configuration with confidence impact tracking in src/lib/error_handler.py
- [x] T045 Integration service coordinators for Brain, Auto-Movie, and Task services with fail-fast behavior in src/lib/integration_manager.py
- [x] T046 Process isolation utilities with cleanup policies in src/lib/process_utils.py

## Phase 3.6: Polish

### Unit Tests
- [x] T047 [P] Unit tests for StoryArc model with confidence validation in tests/unit/test_story_arc_model.py
- [x] T048 [P] Unit tests for narrative analysis algorithms with 75% threshold testing in tests/unit/test_narrative_analyzer.py
- [x] T049 [P] Unit tests for consistency validation logic with malformed content handling in tests/unit/test_consistency_validator.py
- [x] T050 [P] Unit tests for genre pattern matching with confidence scoring in tests/unit/test_genre_analyzer.py

### Performance & Validation
- [x] T051 Performance tests for concurrent request handling (10 simultaneous with process isolation) in tests/performance/test_concurrent_performance.py
- [x] T052 Run quickstart.md validation scenarios and verify all clarification requirements in tests/validation/test_quickstart_scenarios.py

## Dependencies

### Critical Path Dependencies
- Setup (T001-T005) before everything else
- Tests (T006-T019) before implementation (T020+)
- Models (T020-T027) before services (T028-T033)
- Services (T028-T033) before MCP handlers (T035-T040)
- MCP server (T034) before tool handlers (T035-T040)
- Tool registry (T041) after all handlers (T035-T040)
- Integration (T042-T046) after services and before polish
- Unit tests (T047-T050) after corresponding implementation
- Performance tests (T051-T052) after all core implementation

### File Dependencies
- T020 (StoryArc) blocks T028 (NarrativeAnalyzer), T035 (story structure handler)
- T021 (PlotThread) blocks T036 (plot threads handler)
- T022 (NarrativeBeat) blocks T031 (PacingCalculator), T040 (pacing handler)
- T023 (CharacterJourney) blocks T029 (ConsistencyValidator), T037 (consistency handler)
- T024 (GenreTemplate) blocks T030 (GenreAnalyzer), T038 (genre patterns handler)
- T026 (StorySession) blocks T032 (SessionManager), T039 (session handler)
- T027 (ContentAnalysisResult) blocks T013 (malformed content scenario)
- T033 (ProcessIsolationManager) blocks T017 (session isolation scenario), T019 (concurrent requests)
- T034 (MCP server) blocks all handlers T035-T040
- T041 (tool registry) requires all handlers T035-T040

## Parallel Execution Groups

### Group 1: Setup Phase (after T001-T002 complete)
```bash
# Launch T003-T005 together:
Task: "Configure linting and formatting tools (ruff, black, mypy configuration files)"
Task: "Create 15+ genre template files in config/genres/ (thriller.yaml, drama.yaml, comedy.yaml, action.yaml, horror.yaml, romance.yaml, sci-fi.yaml, fantasy.yaml, mystery.yaml, western.yaml, war.yaml, historical.yaml, biographical.yaml, documentary.yaml, animation.yaml)"
Task: "Create narrative pattern libraries in config/patterns/ (three-act.yaml, hero-journey.yaml, pacing-templates.yaml)"
```

### Group 2: MCP Contract Tests (after setup complete)
```bash
# Launch T006-T011 together:
Task: "Contract test analyze_story_structure tool in tests/contract/test_story_structure_tool.py"
Task: "Contract test track_plot_threads tool in tests/contract/test_plot_threads_tool.py"
Task: "Contract test validate_consistency tool in tests/contract/test_consistency_tool.py"
Task: "Contract test apply_genre_patterns tool in tests/contract/test_genre_patterns_tool.py" 
Task: "Contract test get_story_session tool in tests/contract/test_session_tool.py"
Task: "Contract test calculate_pacing tool in tests/contract/test_pacing_tool.py"
```

### Group 3: Integration Tests (after contract tests complete)
```bash
# Launch T012-T019 together:
Task: "Integration test story structure analysis scenario in tests/integration/test_story_structure_scenario.py"
Task: "Integration test malformed content handling scenario in tests/integration/test_malformed_content_scenario.py"
Task: "Integration test plot thread tracking scenario in tests/integration/test_plot_thread_scenario.py"
Task: "Integration test consistency validation scenario in tests/integration/test_consistency_scenario.py"
Task: "Integration test genre pattern application scenario in tests/integration/test_genre_scenario.py"
Task: "Integration test session continuity with process isolation scenario in tests/integration/test_session_isolation_scenario.py"
Task: "Integration test integration failure handling scenario in tests/integration/test_integration_failure_scenario.py"
Task: "Integration test concurrent request handling with process isolation in tests/integration/test_concurrent_requests.py"
```

### Group 4: Data Models (after integration tests fail)
```bash
# Launch T020-T027 together:
Task: "StoryArc model with confidence scoring and project isolation in src/models/story_arc.py"
Task: "PlotThread model with lifecycle stages and confidence tracking in src/models/plot_thread.py"
Task: "NarrativeBeat model with emotional impact and tension scoring in src/models/narrative_beat.py"
Task: "CharacterJourney model with arc types and state progression in src/models/character_journey.py"
Task: "GenreTemplate model with conventions and authenticity rules in src/models/genre_template.py"
Task: "ConsistencyRule model with validation logic and severity levels in src/models/consistency_rule.py"
Task: "StorySession model with process isolation context in src/models/story_session.py"
Task: "ContentAnalysisResult model for malformed content handling in src/models/content_analysis.py"
```

### Group 5: Unit Tests (after corresponding implementation)
```bash
# Launch T047-T050 together:
Task: "Unit tests for StoryArc model with confidence validation in tests/unit/test_story_arc_model.py"
Task: "Unit tests for narrative analysis algorithms with 75% threshold testing in tests/unit/test_narrative_analyzer.py"
Task: "Unit tests for consistency validation logic with malformed content handling in tests/unit/test_consistency_validator.py"
Task: "Unit tests for genre pattern matching with confidence scoring in tests/unit/test_genre_analyzer.py"
```

## Validation Checklist
*GATE: Checked by main() before returning*

- [x] All contracts have corresponding tests (T006-T011 cover all 6 MCP tools)
- [x] All entities have model tasks (T020-T027 cover all data model entities)
- [x] All tests come before implementation (Phase 3.2 before 3.3+)
- [x] Parallel tasks truly independent (different files, no shared dependencies)
- [x] Each task specifies exact file path (all tasks include specific file paths)
- [x] No task modifies same file as another [P] task (verified no conflicts)
- [x] All quickstart scenarios have integration tests (T012-T019)
- [x] MCP protocol properly tested (contract tests for all tools)
- [x] TDD workflow enforced (tests must fail before implementation)
- [x] Process isolation requirements covered (T017, T019, T033, T046)
- [x] Confidence scoring implemented throughout (75% threshold in multiple tasks)
- [x] Malformed content handling covered (T013, T027, T049)
- [x] Session persistence until completion addressed (T026, T032, T039)
- [x] Integration failure handling implemented (T018, T045)
- [x] 15+ genre support validated (T004, T024, T030, T043)

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing
- Commit after each task
- Follow TDD: Red-Green-Refactor cycle
- Quality over speed (per performance requirements)
- MCP protocol compliance critical for agent integration
- Process isolation enforced for all project-scoped operations
- 75% confidence threshold validated in all analysis operations
- All clarification requirements integrated throughout task structure

---

**Task Generation Complete**: 52 tasks generated covering setup, testing, implementation, and validation phases with full clarification requirements integration. Ready for implementation execution following TDD principles with process isolation and constitutional compliance.