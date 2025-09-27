<!--
Sync Impact Report:
Version change: v1.0.0 → v1.1.0 (Added LLM Declaration Principle)
Modified principles: None (existing principles unchanged)
Added sections: VI. LLM Declaration and Management
Removed sections: None
Templates requiring updates:
  ✅ plan-template.md - Updated Technical Context with LLM Requirements field
  ✅ spec-template.md - No constitutional requirements identified  
  ✅ tasks-template.md - TDD workflow matches Test-First principle
  ✅ Command templates - No command templates directory found
Follow-up TODOs: None - all templates updated for LLM Declaration principle
-->

# MCP Story Service Constitution

## Core Principles

### I. Library-First
Every feature starts as a standalone library with clear narrative intelligence purpose. Libraries MUST be self-contained, independently testable, and documented. Each service component MUST have a single, well-defined responsibility within the story analysis domain. No organizational-only libraries - each component must provide concrete value to story intelligence or MCP protocol functionality.

### II. Test-First (NON-NEGOTIABLE)
TDD is mandatory: Tests written → User approved → Tests MUST fail → Then implement. Red-Green-Refactor cycle strictly enforced. Contract tests MUST validate MCP protocol compliance before any tool implementation. Integration tests MUST validate story analysis scenarios before service development. All narrative analysis algorithms MUST be validated against known story examples.

### III. Simplicity
Start simple, follow YAGNI principles. Single responsibility service focused exclusively on story analysis. Avoid premature optimization - quality over speed as explicitly stated in performance requirements. Each analysis engine (narrative, consistency, genre, pacing) MUST address one concern. Complex multi-service integrations MUST be justified in Complexity Tracking section.

### IV. Integration Testing
Focus areas requiring integration tests: MCP protocol contract validation, story analysis cross-service communication, narrative consistency across analysis engines, session state persistence, concurrent request handling. All external service integrations (Brain, Auto-Movie, Task services) MUST have integration test coverage. Service boundaries MUST be validated through contract testing.

### V. Observability  
MCP protocol provides structured communication ensuring debuggability. All story analysis operations MUST log analysis decisions, confidence scores, and reasoning paths. Error states MUST include sufficient context for narrative intelligence debugging. Session state changes MUST be trackable. Performance metrics MUST be captured for story analysis quality assessment.

### VI. LLM Declaration and Management
All LLMs required or used by the service MUST be declared in environment variables. LLM integrations MUST use BAML (Boundary ML) for structured LLM interactions and prompt management. Environment variables MUST specify model names, endpoints, API keys, and configuration parameters. No hardcoded LLM references or API calls outside of BAML framework. All prompt templates and LLM workflows MUST be version-controlled through BAML configuration files.

## Quality Standards

### Story Analysis Quality
Narrative intelligence outputs MUST be deterministic given identical inputs. Analysis algorithms MUST provide confidence scores and reasoning explanations. Genre compliance scoring MUST reference specific conventions. Plot hole detection MUST specify severity levels and suggested remediation. All story recommendations MUST be actionable and contextually relevant.

### MCP Protocol Compliance  
All tools MUST validate input parameters according to contract specifications. Response schemas MUST match contracted formats exactly. Error responses MUST follow MCP protocol standards. Tool registration MUST be complete and discoverable. Concurrent request handling MUST maintain protocol integrity.

### Performance and Reliability
Quality prioritized over speed - thorough analysis preferred over rapid response. 10 concurrent requests MUST be supported without degradation. Story session state MUST persist across service restarts. Memory usage MUST remain bounded under concurrent load. Response times MAY be longer to ensure analysis depth and accuracy.

## Development Workflow

### Implementation Process
1. Specification requirements → Contract definitions → Integration test scenarios
2. Contract tests written and failing → Model implementation → Service implementation  
3. MCP tool handlers → Protocol integration → Performance validation
4. All tests passing → Documentation complete → Deployment ready

### Code Review Requirements
Constitution compliance MUST be verified in all reviews. TDD workflow MUST be evidenced (failing tests before implementation). Integration boundaries MUST be validated. Performance characteristics MUST be documented. Complexity deviations MUST be justified and tracked.

### Quality Gates
Tests MUST pass before merge. Contract compliance MUST be validated. Integration tests MUST cover cross-service boundaries. Performance requirements MUST be satisfied. Documentation MUST be complete and accurate.

## Governance

This constitution supersedes all other development practices. Amendments require explicit documentation, approval, and migration plan. All implementation decisions MUST verify constitutional compliance before proceeding.

Complexity deviations MUST be documented in Complexity Tracking with explicit justification. Multiple service integrations require architectural review. Performance trade-offs MUST align with quality-over-speed principle.

Use CLAUDE.md for agent-specific runtime development guidance. Constitutional violations block implementation progress until resolved.

**Version**: 1.1.0 | **Ratified**: 2025-09-26 | **Last Amended**: 2025-09-26