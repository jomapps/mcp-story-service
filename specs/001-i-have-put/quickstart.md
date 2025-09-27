# Quickstart: MCP Story Service

**Purpose**: End-to-end validation of narrative intelligence capabilities  
**Duration**: ~20 minutes  
**Prerequisites**: MCP Story Service running on localhost:8010 with process isolation

## Quick Validation Scenarios

### Scenario 1: Story Structure Analysis (FR-001)

**Goal**: Verify three-act structure analysis with genre-specific recommendations and 75% confidence threshold

**Test Story**: 
```
"Detective Sarah Chen discovers her partner's involvement in a corporate conspiracy. 
As she investigates deeper, she realizes the conspiracy reaches the highest levels of city government. 
When her own life is threatened, she must choose between her career and exposing the truth. 
In a final confrontation, she brings down the corrupt officials but at great personal cost."
```

**Expected Analysis**:
- **Act 1** (0-25%): Discovery of partner's involvement
- **Act 2** (25-75%): Investigation and escalation of danger  
- **Act 3** (75-100%): Final confrontation and resolution
- **Genre**: Thriller conventions with >=75% confidence threshold
- **Pacing**: Rising tension with climactic resolution
- **Process Isolation**: Separate process spawned for project analysis

**MCP Tool Call**:
```python
# Agent calls via MCP protocol
result = await mcp_client.call_tool("analyze_story_structure", {
    "story_content": "[test story above]",
    "genre": "thriller", 
    "project_id": "quickstart-test-001"
})
```

**Validation Checks**:
- ✅ Returns valid act structure with position percentages
- ✅ Identifies thriller genre conventions with confidence scores
- ✅ meets_threshold: true when confidence >= 75%
- ✅ Provides pacing analysis with tension curve and confidence score
- ✅ Offers specific improvement recommendations
- ✅ Creates isolated process for project analysis
- ✅ Returns process isolation status in response

---

### Scenario 2: Malformed Content Handling (Clarification)

**Goal**: Verify partial analysis with confidence scores and missing data warnings

**Test Content**: 
```
"Detective finds... something important. Bad things happen. Good ending."
```

**Expected Behavior**:
- **Partial Analysis**: Proceed where possible
- **Content Warnings**: Specific missing elements identified
- **Confidence Impact**: Lower scores due to incomplete content
- **Missing Data Warnings**: Clear descriptions of gaps

**MCP Tool Call**:
```python
result = await mcp_client.call_tool("analyze_story_structure", {
    "story_content": "Detective finds... something important. Bad things happen. Good ending.",
    "project_id": "quickstart-malformed-001"
})
```

**Validation Checks**:
- ✅ Analysis proceeds despite incomplete content
- ✅ content_warnings array populated with specific issues
- ✅ confidence_score reflects content quality impact
- ✅ Partial results provided where possible
- ✅ Suggested remediation included in warnings
- ✅ Analysis limitations clearly documented

---

### Scenario 3: Plot Thread Tracking (FR-002)

**Goal**: Verify multi-episode plot thread lifecycle management with confidence scoring

**Test Threads**:
```python
threads = [
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
```

**MCP Tool Call**:
```python
result = await mcp_client.call_tool("track_plot_threads", {
    "project_id": "quickstart-test-002",
    "threads": threads,
    "episode_range": {"start": 1, "end": 5}
})
```

**Validation Checks**:
- ✅ Tracks each thread's lifecycle stage with confidence scores
- ✅ Identifies resolution opportunities with confidence assessment
- ✅ Maps thread dependencies and importance scores
- ✅ Provides actionable next steps for thread development
- ✅ Calculates overall narrative cohesion score with confidence
- ✅ Process isolation enforced for project threads

---

### Scenario 4: Consistency Validation (FR-003)

**Goal**: Verify plot hole detection and timeline consistency with severity ratings

**Test Story Elements**:
```python
story_elements = {
    "characters": [
        {"name": "Sarah Chen", "role": "detective", "introduced": "episode_1"},
        {"name": "Partner Mike", "role": "corrupt_cop", "introduced": "episode_1"}
    ],
    "events": [
        {"description": "Sarah discovers evidence", "episode": 1, "timestamp": "day_1"},
        {"description": "Mike warns conspirators", "episode": 2, "timestamp": "day_1"},  # ISSUE: How did he know?
        {"description": "Sarah confronts Mike", "episode": 3, "timestamp": "day_5"}
    ],
    "timeline": [
        {"event": "Discovery", "day": 1},
        {"event": "Warning", "day": 1}, 
        {"event": "Confrontation", "day": 5}
    ]
}
```

**MCP Tool Call**:
```python
result = await mcp_client.call_tool("validate_consistency", {
    "project_id": "quickstart-test-003",
    "story_elements": story_elements,
    "validation_scope": ["timeline", "character", "plot"]
})
```

**Validation Checks**:
- ✅ Detects plot hole: How did Mike know to warn conspirators?
- ✅ Identifies character motivation inconsistencies
- ✅ Validates timeline chronology
- ✅ Provides severity ratings (critical/warning/suggestion) with confidence impact
- ✅ Suggests specific fixes for each issue
- ✅ confidence_score reflects analysis certainty

---

### Scenario 5: Genre Pattern Application (FR-004)

**Goal**: Verify 75% confidence threshold for genre recommendations

**Test Genre**: Noir Thriller  
**Test Elements**:
```python 
story_beats = [
    {"position": 0.1, "type": "inciting_incident", "description": "Discovery of corruption"},
    {"position": 0.5, "type": "midpoint", "description": "Personal threat emerges"},
    {"position": 0.9, "type": "climax", "description": "Final confrontation"}
]

character_types = [
    {"name": "Sarah", "role": "protagonist", "archetype": "noir_detective"},
    {"name": "Mike", "role": "antagonist", "archetype": "corrupt_authority"}
]
```

**MCP Tool Call**:
```python
result = await mcp_client.call_tool("apply_genre_patterns", {
    "project_id": "quickstart-test-004", 
    "genre": "thriller",
    "story_beats": story_beats,
    "character_types": character_types
})
```

**Validation Checks**:
- ✅ Evaluates adherence to thriller conventions with confidence scores
- ✅ meets_threshold: true/false based on 75% confidence
- ✅ Suggests missing genre-specific elements with confidence ratings
- ✅ Provides authenticity score and improvement areas
- ✅ Recommends genre-appropriate story beats and positioning
- ✅ All recommendations include confidence scores

---

### Scenario 6: Session Continuity with Process Isolation (FR-008, FR-010)

**Goal**: Verify story state persistence until project completion and process isolation

**Test Flow**:
1. Create initial story analysis session with process isolation
2. Perform story structure analysis 
3. Add plot thread tracking
4. Retrieve session to verify persistence and process separation
5. Continue with consistency validation
6. Verify all data maintained across requests with isolation

**MCP Tool Calls**:
```python
# Step 1: Get/create session with process isolation
session = await mcp_client.call_tool("get_story_session", {
    "project_id": "quickstart-session-test"
})

# Step 2: Analyze structure (adds to isolated session)
structure = await mcp_client.call_tool("analyze_story_structure", {
    "story_content": "[test story]",
    "project_id": "quickstart-session-test"
})

# Step 3: Add threads (updates isolated session)
threads = await mcp_client.call_tool("track_plot_threads", {
    "project_id": "quickstart-session-test",
    "threads": [...]
})

# Step 4: Verify session persistence and isolation
updated_session = await mcp_client.call_tool("get_story_session", {
    "project_id": "quickstart-session-test"  
})

# Step 5: Test different project isolation
other_project = await mcp_client.call_tool("get_story_session", {
    "project_id": "different-project-test"
})
```

**Validation Checks**:
- ✅ Session created with unique ID and process isolation active
- ✅ Story analysis results cached in isolated session
- ✅ Plot thread data persisted across calls within same process
- ✅ Session maintains active story arcs
- ✅ persistence_policy: "until_completion" or "manual_deletion"
- ✅ process_isolation_active: true for all project operations
- ✅ Different projects get separate processes and sessions
- ✅ No cross-contamination between project sessions

---

### Scenario 7: Integration Failure Handling (Clarification)

**Goal**: Verify fail-fast behavior when external services unavailable

**Test Setup**: 
- Simulate Brain service (brain.ft.tc:8002) unavailability
- Attempt story analysis that requires Brain service coordination
- Verify immediate failure with clear error message

**Expected Behavior**:
- **Immediate Failure**: No graceful degradation
- **Clear Error Messages**: Service-specific failure indication
- **Retry Guidance**: Information about service dependency

**Validation Approach**:
```python
# Simulate Brain service unavailability
try:
    result = await mcp_client.call_tool("analyze_story_structure", {
        "story_content": "Test story requiring Brain service coordination",
        "project_id": "integration-failure-test"
    })
    # Should not reach here if Brain service is unavailable
    assert False, "Expected integration failure"
except McpError as e:
    # Verify error contains service-specific information
    assert "brain.ft.tc:8002" in str(e)
    assert "unavailable" in str(e).lower()
```

**Validation Checks**:
- ✅ Immediate failure when external service unavailable
- ✅ Error message identifies specific failing service
- ✅ No partial results provided when integration fails
- ✅ Retry guidance included in error response
- ✅ Process isolation maintained even during failures

---

## Performance Validation (PR-001, PR-002)

### Concurrent Request Test with Process Isolation

**Goal**: Verify 10 concurrent request handling with separate processes per project

**Test Setup**:
```python
import asyncio

async def concurrent_isolation_test():
    tasks = []
    for i in range(10):
        task = mcp_client.call_tool("analyze_story_structure", {
            "story_content": f"Test story {i} content for project isolation testing...",
            "project_id": f"concurrent-test-{i}"  # Different project per request
        })
        tasks.append(task)
    
    # All should complete successfully with separate processes
    results = await asyncio.gather(*tasks)
    return results
```

**Validation Checks**:
- ✅ All 10 requests complete successfully
- ✅ Each request gets separate process (process isolation verification)
- ✅ No request failures or timeouts
- ✅ Response quality maintained under concurrent load  
- ✅ Session isolation between concurrent projects verified
- ✅ Response times prioritize quality over speed
- ✅ Process cleanup occurs after analysis completion

---

## Integration Validation

### Service Communication Test

**Goal**: Verify integration with other platform services

**Mock Integration Points**:
- **Brain Service** (brain.ft.tc:8002): Knowledge coordination
- **Auto-Movie Dashboard** (auto-movie.ft.tc:3010): User guidance
- **Task Service** (tasks.ft.tc:8001): Content generation context

**Validation Approach**:
```python
# Test Brain service coordination (when available)
try:
    brain_sync = await story_service.coordinate_with_brain({
        "project_id": "integration-test",
        "knowledge_type": "narrative_analysis",
        "data": story_analysis_results
    })
    
    # Verify successful coordination
    assert brain_sync["status"] == "coordinated"
    assert "story_knowledge_id" in brain_sync
except IntegrationError:
    # Verify fail-fast behavior per clarification
    assert "brain.ft.tc:8002" in str(error)
    assert "unavailable" in str(error).lower()
```

**Validation Checks**:
- ✅ MCP protocol communication functions correctly
- ✅ Service coordination works when services available
- ✅ Fail-fast error handling for service unavailability per clarification
- ✅ Error messages include specific service identification
- ✅ Process isolation maintained during integration calls

---

## Success Criteria

**All scenarios must pass with these outcomes**:

1. **Functional Requirements Met**: All FR-001 through FR-010 validated with confidence scoring
2. **Performance Requirements Met**: Quality-focused analysis with 10 concurrent capacity and process isolation
3. **Integration Requirements Met**: MCP protocol and fail-fast service coordination working
4. **Clarification Requirements Met**: 75% confidence threshold, partial analysis for malformed content, process isolation, session persistence until completion, fail-fast integration
5. **Data Consistency**: All story entities properly validated and persistent within process boundaries
6. **Error Handling**: Graceful failure modes with clear error messages and confidence impact
7. **Process Isolation**: Each project runs in separate process with no cross-contamination
8. **Confidence Scoring**: All analysis outputs include confidence scores with 75% threshold enforcement

**Quickstart Complete**: MCP Story Service ready for AI agent integration and production story analysis workflows with constitutional compliance.

---

**Estimated Runtime**: 20 minutes for full validation  
**Next Steps**: Execute `/tasks` command to generate implementation tasks based on validated contracts and scenarios