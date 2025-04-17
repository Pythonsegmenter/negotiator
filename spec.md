# Negotiator Travel Agent — Full Technical Specification

Everything your dev team needs to implement the first production‑ready version.

## 1. Purpose & Scope

Help a traveler obtain the best deal for a single activity by letting an LLM‑powered Agent negotiate with multiple Guides via WhatsApp (or a simulator).
Deliver a plain‑text report summarizing every offer plus the Agent's recommendation.

## 2. Top‑Level Architecture

| Layer | Responsibility | Key Tech |
|-------|----------------|----------|
| Orchestrator | Runs single‑threaded loop, polls managers, coordinates state, decides when session ends. | pure Python state‑machine |
| User Manager | Converses with the traveler, gathers all required input, pushes clarifications, returns User Info. | LLM wrapper + messaging |
| Guide Manager (N×) | One instance per guide; manages a Guide Chat, stores Guide Info, executes negotiation logic. | LLM wrapper + messaging |
| Messaging Adapter | Unified interface for WhatsApp (prod) or stub (test); simulates human delays. | external API / simulator |
| Data Persistence | JSON logging of every message; JSON profiles for each guide; atomic writes. | stdlib json, pathlib |
| Report Generator | Builds final plain‑text report & recommendation from structured data. | Jinja2 template |
| Config | Centralized settings via dynaconf. | dynaconf |
| Tests | pytest suites: unit (mock LLM), integration (real LLM), test‑mode simulated guides. | pytest, unittest.mock |
| Deps / Env | Managed with uv + Pipfile. | uv, pipenv |

Modules communicate only through thin, explicit contracts to enable parallel development.

## 3. Key Data Objects

### 3.1 User Info (user_info.json)

```json
{
  "activity": "Climb Mt Agung at sunrise",
  "location": "Mount Agung, Bali",
  "time": {
    "start": "2025-08-14T23:00+08:00",
    "end":   "2025-08-15T12:00+08:00"
  },
  "deadline":     "2025-05-10T18:00+02:00",
  "participants": 2,
  "budget":       300,
  "preferences": {
    "price_vs_value": "lowest_price"
  }
}
```

### 3.2 Guide Chat Log (chats/<guide_id>.jsonl)

Each line is a JSON object:

```json
{ "timestamp":"…", "sender":"agent"|"guide", "text":"…" }
```

Append‑only.

### 3.3 Guide Info (guides/<guide_id>.json)

Written only when negotiation for that guide is finalized:

```json
{
  "name":             "Bali Peak Tours",
  "final_price_total":280,
  "currency":         "USD",
  "features":         ["hotel pick‑up", "breakfast", "gear"],
  "optional_extras":  { "private jeep": 50 },
  "meeting_point":    "Lobby of XYZ Hotel",
  "meeting_time":     "23:30",
  "status":           "responsive",    // or "unresponsive", "incomplete"
  "negotiation_summary":"Started at 350, reduced to 280 after price match."
}
```

## 4. Module Contracts

### 4.1 BaseManager Interface

```python
class BaseManager(ABC):
    def needs_action(self, global_state: State) -> bool: ...
    def next_action(self, global_state: State) -> Optional[Action]: ...
    def execute(self, action: Action) -> None: ...
```

`global_state` provides read‑only access to User Info, aggregated Guide Infos, and deadlines.

`Action` encapsulates outgoing message details (text, delay).

### 4.2 Orchestrator Loop

```python
while not session.is_finished():
    for mgr in managers_round_robin():
        if mgr.needs_action(state):
            action = mgr.next_action(state)
            if action:
                mgr.execute(action)
    time.sleep(config.loop_min_delay_ms / 1000)
```

Single‑threaded: skip managers without changes.

Session ends when all managers' `needs_action == False` and either the deadline is reached or all negotiations are stable.

### 4.3 Messaging Adapter

```python
class Messenger:
    def send(self, to: str, text: str, delay_s: float = None) -> None: ...
    def poll(self) -> List[IncomingMessage]: ...
```

Prod: real WhatsApp API.

Test: stub injecting scripted or LLM‑generated replies.

Handles typing delays as per config.

### 4.4 Guide Manager Negotiation Rules

Budget provided?

- Yes → start negotiation immediately toward that hidden anchor.
- No → wait for first guide's offer as anchor.

Always attempt to lower price until:
- Guide refuses to go lower or
- Floor reached.

Follow‑ups:
- Max 3 attempts.
- Delay = max(follow_up_min_hours, remaining_time/10).

Practical details:
- Press until meeting time/place and required extras are confirmed.
- Cannot finalize without them.

No identity leaks:
- May reference "another provider offered X," but never names.

## 5. Chronological Flow

1. **Collect Input**
   - User Manager: prompt until required fields complete → write user_info.json → notify Orchestrator.

2. **Instantiate Guides**
   - Orchestrator: for each guide contact, create Guide Manager and log file.

3. **Initial Outreach**
   - Guide Managers: compose opener from User Info → send.

4. **Main Loop**
   - Orchestrator iterates managers:
     - Guide Mgr: on new inbound msg → update Guide Info → maybe reply.
     - User Mgr: if any guide question needs user input → ask.
   - Skip managers with no state change.

5. **Progress Updates**
   - User Manager: at 1/3 and 2/3 of timeframe, send summary of replies & needs.

6. **Negotiation Close**
   - Orchestrator ends loop when deadline hit or all negotiations stable.

7. **Report Generation**
   - Report Generator: read all Guide Info + User Info → produce plain‑text report.

8. **Notify Guides**
   - User Manager/helper: inform winner and unselected guides (using user's explanation or default).

9. **Cleanup**
   - Data Persistence: flush logs, mark session completed.

## 6. Configuration (dynaconf)

```toml
[default]
loop_min_delay_ms      = 250
typing_delay_range     = [0.4, 1.2]     # seconds
follow_up_max          = 3
follow_up_min_hours    = 2
whatsapp_api_token     = ""
simulation_mode        = true
```

All numeric values and modes are configurable via dynaconf.

## 7. Error Handling & Logging

| Area | Strategy |
|------|----------|
| JSON writes | Atomic temp‑file → rename; retry once on failure. |
| Messaging send | Catch API errors; back‑off + retry (configurable). |
| LLM calls | 2 retries with exponential back‑off; mark pending on failure. |
| Manager exceptions | Orchestrator catches, logs stack trace, continues loop. |
| Guide unresponsive | After 3 follow‑ups, mark status: "unresponsive" in Guide Info. |

Central logging via Python's logging; optional integration with external logger script.

## 8. Testing Plan

### 8.1 Unit Tests (pytest)
- Messaging Adapter (stub)
- Guide Manager Logic (scripted replies & price paths)
- User Manager Prompts (required‑field gathering)
- Orchestrator Loop (mock needs_action flips)

### 8.2 Integration Tests
Full system with real LLM API calls modeling guide behavior.

Verify end‑to‑end flow, JSON outputs, and final report.

### 8.3 CI/CD
- GitHub Actions runs unit tests on each PR.
- Nightly integration test job (tagged slow).

## 9. Developer Work Breakdown
- Messaging Adapter (prod & stub)
- Data Persistence (atomic JSON logger & profile writer)
- User Manager (input flows, updates)
- Guide Manager (negotiation FSM)
- Orchestrator & State Classes
- Report Generator (Jinja2 + tests)
- Config & Env (dynaconf, uv, Pipfile)
- Testing Framework (mocks, CI pipeline)

Independent modules; clear interfaces ensure parallel progress.

## 10. Glossary
- **Agent** – entire LLM‑powered system
- **User** – traveler
- **Guide** – service provider contacted via WhatsApp
- **User Info / Guide Info** – structured, condensed state
- **User Chat / Guide Chat** – raw conversation logs
- **Manager** – encapsulates chat state & logic (User or Guide)
- **Orchestrator** – polls managers, drives session lifecycle
