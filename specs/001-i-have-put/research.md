# Research: MCP Story Service Technical Decisions

**Generated**: 2025-09-26  
**Purpose**: Technical research for narrative intelligence MCP server implementation

## MCP Protocol Implementation

**Decision**: Use Python `mcp` library with asyncio-based server implementation  
**Rationale**: Official MCP SDK provides standardized protocol compliance, handles WebSocket communication, tool registration, and error handling. Asyncio enables concurrent request processing required for 10 simultaneous story analysis operations. Aligns with constitutional requirement for MCP protocol standards compliance.  
**Alternatives considered**: 
- Custom WebSocket implementation (rejected: reinventing protocol complexity, violates Library-First principle)
- Node.js MCP implementation (rejected: team Python expertise, ecosystem alignment)

**Key Implementation Points**:
- Server class inherits from `mcp.Server` 
- Tool registration via `@server.call_tool` decorators
- Async handlers for all story analysis operations
- Structured JSON responses for narrative intelligence data

## Project Isolation Architecture

**Decision**: Separate analysis processes per project with process-scoped state isolation  
**Rationale**: Clarification session determined separate analysis processes required to prevent cross-contamination between concurrent projects. Aligns with constitutional Simplicity principle by avoiding complex shared state management.  
**Alternatives considered**:
- Shared process with namespace isolation (rejected: complexity risk, memory leakage potential)
- Database-level isolation (rejected: performance overhead, architectural complexity)

**Key Implementation Points**:
- Process spawning per project analysis request
- Process-local story state and analysis context
- Inter-process communication via structured messages
- Process cleanup after analysis completion or timeout

## Narrative Analysis Architecture

**Decision**: Modular service architecture with specialized analysis engines  
**Rationale**: Story analysis involves distinct domains (structure, consistency, genre, pacing) that benefit from separation of concerns. Allows independent development, testing, and enhancement of each analysis type. Supports constitutional Library-First principle with clear component responsibilities.  
**Alternatives considered**:
- Monolithic analysis service (rejected: difficult to maintain, test complexity, violates Simplicity)
- External ML service calls (rejected: adds latency, dependency complexity)

**Key Components**:
- `NarrativeAnalyzer`: Three-act structure identification and validation
- `ConsistencyValidator`: Plot hole detection using rule-based logic with confidence scoring
- `GenreAnalyzer`: Pattern matching against 15+ genre convention libraries with 75% confidence threshold  
- `PacingCalculator`: Tension curve analysis using narrative beat scoring

## Confidence Scoring System

**Decision**: 75% confidence threshold for genre analysis recommendations with graduated response levels  
**Rationale**: Clarification session established 75% threshold for balanced precision and coverage. Constitutional Quality Standards require confidence scores and reasoning explanations for all analysis outputs.  
**Alternatives considered**:
- Fixed high threshold (90%) - rejected: too restrictive, reduces recommendation coverage
- Adaptive thresholds - rejected: complexity without clear benefit for initial implementation

**Key Implementation Points**:
- All analysis outputs include confidence scores (0.0-1.0)
- Recommendations triggered at 75% confidence threshold
- Warnings and suggestions provided for lower confidence scores
- Reasoning paths logged for observability compliance

## Story State Management

**Decision**: Redis for session state with project completion persistence policy  
**Rationale**: Clarification session specified session persistence until project completion or manual deletion. Redis provides fast access for active story sessions. Neo4j integration through Brain service maintains knowledge consistency per constitutional Integration Testing requirements.  
**Alternatives considered**:
- Direct Neo4j integration (rejected: couples to database, violates service boundaries)
- In-memory only (rejected: loses state across service restarts)
- PostgreSQL (rejected: overkill for session data, adds complexity)

**Key Implementation Points**:
- Story project sessions keyed by project_id
- Thread lifecycle tracking with status transitions (introduced, developing, ready for resolution, resolved)
- Analysis results cached during multi-step operations
- Coordination messages to Brain service for knowledge persistence
- Manual cleanup endpoints for project completion

## Malformed Content Handling

**Decision**: Partial analysis with confidence scores and missing data warnings  
**Rationale**: Clarification session established approach for incomplete/malformed content. Aligns with constitutional Observability principle by providing clear error context and reasoning.  
**Alternatives considered**:
- Reject with errors (rejected: reduces system utility, blocks AI agent workflows)
- Auto-fill missing elements (rejected: may introduce incorrect narrative assumptions)

**Key Implementation Points**:
- Content validation with detailed error reporting
- Partial analysis proceeds where possible
- Confidence scores reflect content completeness
- Missing data warnings include specific gaps identified
- Analysis limitations clearly documented in responses

## Genre Pattern System

**Decision**: Configuration-driven genre templates with extensible pattern matching supporting 15+ genres  
**Rationale**: Genre conventions are data-driven rules that change over time. Configuration files enable easy updates without code changes. Supports 15+ genre requirement (FR-004) with 75% confidence threshold.  
**Alternatives considered**:
- Hard-coded genre rules (rejected: inflexible, maintenance burden, violates Simplicity)
- Machine learning classification (rejected: training data complexity, black box decisions)

**Key Implementation Points**:
- YAML genre definition files in `config/genres/` (thriller, drama, comedy, action, horror, romance, sci-fi, fantasy, mystery, western, war, historical, biographical, documentary, animation)
- Pattern matching engine using rule-based validation
- Authenticity scoring based on convention adherence with 75% threshold
- Hybrid genre support through pattern composition
- Extensible template system for new genres

## Integration Failure Handling

**Decision**: Fail immediately with integration error messages when external services unavailable  
**Rationale**: Clarification session established fail-fast approach for Brain, Auto-Movie, and Task service integrations. Provides clear feedback to AI agents about service dependencies.  
**Alternatives considered**:
- Graceful degradation (rejected: may provide incomplete analysis without clear indication)
- Request queuing (rejected: adds complexity, delays feedback)

**Key Implementation Points**:
- Health check endpoints for external service availability
- Immediate failure responses with specific service identification
- Error messages include retry guidance and timeframes
- Service dependency validation before analysis operations
- Circuit breaker patterns for external service protection

## Testing Strategy

**Decision**: Pytest with MCP protocol contract testing and narrative scenario validation  
**Rationale**: Constitutional Test-First principle requires comprehensive testing strategy. pytest ecosystem maturity for Python services. MCP contract tests ensure protocol compliance. Narrative scenarios validate story analysis quality using known story examples.  
**Alternatives considered**:
- unittest (rejected: less flexible fixtures and parameterization)
- Integration testing only (rejected: debugging complexity, slow feedback)

**Key Testing Layers**:
- **Contract tests**: MCP tool registration, request/response schemas
- **Unit tests**: Individual analysis engine validation with known inputs
- **Integration tests**: End-to-end story analysis flows with sample narratives
- **Scenario tests**: Genre-specific validation using classic story examples
- **Performance tests**: 10 concurrent request handling validation

## Performance Considerations

**Decision**: Quality-prioritized design with thorough analysis over speed constraints  
**Rationale**: Constitutional Performance and Reliability standards explicitly prioritize quality over speed. Clarification confirmed thorough analysis preferred over rapid response.  
**Alternatives considered**:
- Aggressive caching (may implement later if needed)
- Simplified analysis (rejected: contradicts quality priority)

**Key Performance Points**:
- Async/await throughout for concurrent handling
- Process isolation for analysis operations (per clarification)
- Stateful analysis to avoid recomputation within sessions  
- Configurable analysis depth based on request complexity
- Memory-conscious design for concurrent requests (10 max)
- Response time flexibility to ensure analysis thoroughness

## Deployment Configuration

**Decision**: Docker containerization with configurable service URLs and process management  
**Rationale**: Matches existing service architecture pattern. Environment-specific URLs (localhost:8010, story.ft.tc:8010) support development to production progression. Container orchestration supports process isolation requirement.  
**Alternatives considered**:
- Direct Python deployment (rejected: environment consistency issues, process isolation challenges)
- Serverless functions (rejected: story sessions require state persistence)

**Key Deployment Points**:
- Dockerfile with Python 3.11+ runtime
- Process management for project isolation
- Environment variables for service URL configuration
- Health check endpoint for monitoring
- Redis connection configuration for story state
- Integration endpoints for external services (Brain, Auto-Movie, Task)
- Logging integration for observability compliance

## Observability Implementation

**Decision**: Structured logging with confidence scores, reasoning paths, and performance metrics  
**Rationale**: Constitutional Observability principle requires comprehensive debugging support. MCP protocol provides structured communication baseline.  
**Alternatives considered**:
- Basic logging only (rejected: insufficient for narrative intelligence debugging)
- External monitoring only (rejected: lacks analysis-specific context)

**Key Observability Features**:
- Analysis decision logging with confidence scores
- Reasoning path capture for all recommendations
- Session state change tracking
- Performance metrics for analysis quality assessment
- Error context with narrative intelligence debugging information
- MCP protocol communication logging for integration debugging

---

**Research Complete**: All technical decisions resolved with constitutional compliance, clarification requirements addressed, and implementation guidance provided.