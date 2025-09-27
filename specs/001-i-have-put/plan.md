# Implementation Plan: MCP Story Service - Standalone Narrative Intelligence Server

**Branch**: `001-i-have-put` | **Date**: 2025-09-26 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `D:\Projects\mcp-story-service\specs\001-i-have-put\spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Standalone MCP server providing specialized narrative intelligence for AI movie production platform. Primary requirement: AI agents need story analysis, plot validation, and narrative consistency checking capabilities to create well-structured, genre-appropriate content. Technical approach: Python-based MCP protocol server with narrative analysis algorithms, genre pattern matching, and story state management using separate analysis processes per project.

## Technical Context
**Language/Version**: Python 3.11+  
**Primary Dependencies**: MCP protocol implementation, asyncio for concurrent handling, narrative analysis libraries  
**Storage**: Redis for story state management, coordination with Neo4j via Brain service for knowledge persistence  
**Testing**: pytest for unit/integration testing, MCP protocol testing framework  
**Target Platform**: Linux server deployment at story.ft.tc:8010
**Project Type**: single - standalone MCP server service  
**LLM Requirements**: N/A - narrative analysis uses rule-based algorithms, no LLM integration required  
**Performance Goals**: Quality-prioritized story analysis, 10 concurrent requests, 75% confidence threshold  
**Constraints**: Integration with existing service architecture (brain.ft.tc, auto-movie.ft.tc, tasks.ft.tc), separate analysis processes per project  
**Scale/Scope**: Support for 15+ movie genres, multi-episode story tracking, real-time validation, project isolation

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**I. Library-First**: ✅ PASS - MCP server will be self-contained with clear narrative intelligence purpose, each service component has single responsibility  
**II. Test-First**: ✅ PASS - TDD approach with contract tests before implementation, integration tests for story analysis scenarios  
**III. Simplicity**: ✅ PASS - Single responsibility service focused exclusively on story analysis, quality over speed aligned with performance requirements  
**IV. Integration Testing**: ✅ PASS - MCP protocol contract validation, cross-service communication, session state persistence testing planned  
**V. Observability**: ✅ PASS - MCP protocol provides structured communication for debugging, confidence scores and reasoning paths required  
**VI. LLM Declaration**: ✅ PASS - No LLM requirements identified, narrative analysis uses rule-based algorithms

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
src/
├── models/              # Story entities: Arc, Thread, Beat, Journey, Genre, Rules
├── services/            # Narrative analysis engines and validators
│   ├── narrative/       # Story structure analysis
│   ├── consistency/     # Plot hole detection and validation  
│   ├── genre/          # Genre-specific pattern matching
│   └── pacing/         # Tension curve and rhythm analysis
├── mcp/                # MCP protocol server implementation
│   ├── server.py       # Main MCP server
│   ├── tools/          # MCP tool definitions for story analysis
│   └── handlers/       # Request handlers for each story operation
└── lib/                # Shared utilities and algorithms

tests/
├── contract/           # MCP protocol contract tests
├── integration/        # End-to-end story analysis tests
└── unit/              # Individual component tests

config/
├── genres/            # Genre template definitions (15+ genre YAML files)
└── patterns/          # Narrative pattern libraries (three-act, hero journey)
```

**Structure Decision**: Single project structure selected. MCP server will be self-contained with clear separation between narrative logic (src/services), protocol handling (src/mcp), and data models (src/models). Configuration-driven approach for genres and patterns allows extensibility while supporting the 15+ genre requirement with 75% confidence threshold.

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/powershell/update-agent-context.ps1 -AgentType claude`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each contract → contract test task [P]
- Each entity → model creation task [P] 
- Each user story → integration test task
- Implementation tasks to make tests pass

**Ordering Strategy**:
- TDD order: Tests before implementation 
- Dependency order: Models before services before UI
- Mark [P] for parallel execution (independent files)

**Estimated Output**: 50+ numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [x] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (none required)

---
*Based on Constitution v1.1.0 - See `.specify/memory/constitution.md`*