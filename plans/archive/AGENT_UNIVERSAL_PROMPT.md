# Universal Agent Prompt Template

Replace `{AGENT_N}` with: agent1, agent2, agent3, agent4, agent5, agent6, agent7

---

```
You are executing one workstream of a 7-agent parallel refactor of the Unified Trading System.

Complete the plan. After you've completed the plan, ask yourself, "Did you complete the plan?" If you didn't complete the plan, then complete the plan. If you then complete the plan, ask yourself a second time, "Did you really complete the plan?" Is it finished? Is it production grade? Did you leave anything, any detail whatsoever? If you did, then complete the plan. If you're waiting for dependency blockers, unblock them. If you're agent 1, block them if they are dependencies that are not specified to be unblocked in plans which are a level above you. If your agent 5 is waiting for an agent 4 block, then wait. If your agent 1 is waiting for a block, there should be no block, so fix the block. If your agent 5 is waiting for a block that's not relevant to agent 4, 3, 2, 1, 6, 7, 8, 9, or 10, then again unblock yourself. The one to eight agent tasks are all the tasks we're going to do. If something falls outside that that still needs to be done to complete something in your particular agent block, then do that thing so that you don't only partly complete your plan.

BEFORE ANY CODE, read these files IN ORDER — they are your ground truth:

1. .cursor/plans/CITADEL_VISION_2026_03_22.md — the complete system vision, service architecture,
   live/batch pattern, separation of concerns, interface contracts, collection names
2. .cursor/plans/{AGENT_N}_*_2026_03_22.md — YOUR specific plan with phased todos
3. .cursor/plans/AGENT_PROMPTS.md — shared preamble (read the SHARED PREAMBLE section)
4. .cursor/plans/PLAN_AMENDMENTS_2026_03_22.md — corrections and additions to original plans
5. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md — mandatory coding rules
6. .cursorrules — workspace standards

WORKSPACE: /Users/ikennaigboaka/Code/unified-trading-system-repos/
Each subdirectory is an INDEPENDENT git repo. Only commit to repos you modify.

═══════════════════════════════════════════════════════════════════
CODING RULES (violating these fails the plan)
═══════════════════════════════════════════════════════════════════

- `uv pip install` not `pip install`
- `bash scripts/quality-gates.sh` for tests (never pytest directly)
- `basedpyright` not `pyright`
- No `os.getenv()` — use `UnifiedCloudConfig`
- Flat deps only in pyproject.toml (no optional-dependencies)
- Do NOT run `bash scripts/quickmerge.sh` unless explicitly told to
- Do NOT run `git reset --hard` under any circumstances

═══════════════════════════════════════════════════════════════════
SEPARATION OF CONCERNS (the most important section — read twice)
═══════════════════════════════════════════════════════════════════

The system has 3 layers. Every feature lives in EXACTLY ONE layer.
Getting this wrong is the #1 way to create technical debt.

LAYER 1 — SERVICE ENGINE / MOCK STATE (unified-trading-api services/)
  What belongs here:
  - PnL calculation (from tick prices × position quantities)
  - Org-scoped data filtering (client sees only their org's data)
  - Batch/live collection routing (mode param → collection suffix)
  - Alert state transitions (acknowledge, escalate, resolve)
  - Circuit breaker state (trip, reset)
  - Risk exposure aggregation (sum positions by strategy/venue)
  - Seed data generation (from UAC registry, not hardcoded lists)
  What does NOT belong here:
  - UI components, HTML, CSS, React
  - Chart rendering, indicator math (SMA/EMA — that's presentation)

LAYER 2 — API ROUTES (unified-trading-api routes/)
  What belongs here:
  - HTTP endpoints (GET/POST) with OpenAPI docs
  - WebSocket channels (market-data, positions, analytics, alerts)
  - Auth token extraction and org_id injection
  - Request validation, pagination, query param parsing
  - Proxy to client-reporting-api for /reporting/* in real mode
  What does NOT belong here:
  - Business logic (delegate to service layer)
  - UI rendering

LAYER 3 — UI (unified-trading-system-ui)
  What belongs here:
  - Visual rendering of data received from the API
  - Chart overlays and indicator computation (SMA/EMA/BB — presentation math)
  - Skeleton loading, error boundaries, empty states
  - Export formatting (CSV/XLSX — client-side serialization of API data)
  - Responsive layout, dark mode, animations
  - WebSocket subscription management (subscribe/unsubscribe)
  What does NOT belong here:
  - Data generation (no `const mockData = [...]`, no `lib/trading-data.ts`)
  - PnL calculation (comes from WebSocket analytics channel)
  - Org filtering (API does this based on auth token)
  - Mock fixtures or MSW handlers (API handles mock/real internally)

THE CURL TEST: If you can't demonstrate a feature with `curl` (or `wscat` for
WebSocket), the logic is in the wrong layer. Move it.

Examples:
  curl /positions/active       → must return positions with PnL already calculated
  curl /alerts/active          → must return alerts with correct count
  curl -X POST /alerts/1/ack   → must change state; next GET shows acknowledged
  curl /analytics/strategies   → must return all 50+ strategies (not 18)
  wscat -c ws://localhost:8030/ws → subscribe → see PnL updating from ticks

═══════════════════════════════════════════════════════════════════
LIVE / BATCH COEXISTENCE (applies to ALL domain data)
═══════════════════════════════════════════════════════════════════

Every time-varying domain has TWO collections:
  {domain}_live  — mutable, updated by WebSocket ticks / user actions
  {domain}_batch — immutable T+1 reconciled snapshot, seeded once

Same API endpoint serves both. The ONLY branching is the collection name:
  GET /positions/active?mode=live   → reads positions_live
  GET /positions/active?mode=batch  → reads positions_batch
  GET /alerts/active?mode=live      → reads alerts_live (can acknowledge)
  GET /alerts/active?mode=batch     → reads alerts_batch (actions DISABLED)
  GET /risk/exposure?mode=live      → reads risk_live (updates from ticks)
  GET /risk/exposure?mode=batch     → reads risk_batch (end-of-day snapshot)

The service layer code (filtering, pagination, org-scoping) is >90% identical.
No mode-specific business logic. The data shape is the same — only values differ
slightly to reflect T+1 reconciliation.

In batch mode: action buttons (acknowledge, escalate, circuit breaker) are DISABLED.
You cannot mutate historical data. Show tooltip: "Switch to live mode to take action."

Real-time PnL recalculation (ticks → positions → strategy PnL) ONLY affects _live
collections. Batch data is never touched by ticks.

═══════════════════════════════════════════════════════════════════
REGISTRY-DRIVEN DATA (no hardcoded lists)
═══════════════════════════════════════════════════════════════════

Instruments: UAC `representative_sample.py` is the SSOT (50+ specs across CeFi,
TradFi, DeFi, Sports). Seed generators import the registry. If UAC expands,
`POST /admin/reset` picks up new instruments automatically.

Strategies: 50+ strategy configs generated from codex archetypes × asset classes.
Config, not code. The EventDrivenStrategyEngine is parameterised — expanding
strategies means adding config entries, not new code paths.

The UI reads instrument lists from `ui-reference-data.json` (synced from UAC) and
strategy lists from `GET /analytics/strategy-configs`. The UI NEVER hardcodes
instrument or strategy lists.

═══════════════════════════════════════════════════════════════════
OPERATIONAL ACTIONS (real backend mutations, not empty UI signs)
═══════════════════════════════════════════════════════════════════

Every action button in the UI calls a real API POST that mutates MockStateStore:
  POST /alerts/{id}/acknowledge → sets acknowledged:true in alerts_live
  POST /alerts/{id}/escalate    → bumps severity
  POST /risk/circuit-breaker    → trips/resets per strategy
  POST /risk/kill-switch        → emergency stop
  POST /execution/orders        → places a manual order
  POST /admin/reset             → restores all state to seed

After each POST, subsequent GETs reflect the new state.
POST /admin/reset undoes everything back to initial seed.
This is NOT cosmetic — it demonstrates real operational workflows.

═══════════════════════════════════════════════════════════════════
CURRENT STATE (verified 2026-03-22 — do NOT redo what's done)
═══════════════════════════════════════════════════════════════════

- API service layer EXISTS: services/ with DomainService Protocol, MockDomainService,
  LiveDomainService, factory.py. All 19 routes use get_service(request) DI.
- WebSocket EXISTS: routes/websocket.py (4,859L) with channel multiplexing + tick gen.
- personas.py EXISTS: 121L, 4 orgs, 5 personas. Matches auth-api.
- auth-api EXISTS: port 8200, JWT, 5 mock users. NOT in dev stack yet.
- Dark mode EXISTS: theme: "dark" is the only mode. next-themes + CSS variables.
- seed.py EXISTS: 4,188L covering basic domains. NEEDS enrichment + registry import.
- Execution pages ALL EXIST: 7 tabs, 298-405L each.
- 49/60 service pages are REAL. 11 are stubs (24L).
- MSW still exists (lib/mocks/) — needs removal AFTER API serves all data.

═══════════════════════════════════════════════════════════════════
COMPLETION PROTOCOL (after EVERY todo)
═══════════════════════════════════════════════════════════════════

1. TICK THE PLAN — change `- [ ]` to `- [x]` in your plan file
2. RUN TESTS — `bash scripts/quality-gates.sh` in every repo you modified
3. HARDEN RULES — add architectural comments, update next.config.mjs redirects
4. UPDATE MANIFEST — UI_STRUCTURE_MANIFEST.json page states, hook lists
5. UPDATE DOCS — CODEBASE_STRUCTURE.md, ROUTES.md if architecture changed
6. COMMIT WITH CONTEXT — explain WHY + reference plan todo ID

═══════════════════════════════════════════════════════════════════
YOUR MISSION
═══════════════════════════════════════════════════════════════════

Read your plan file: .cursor/plans/{AGENT_N}_*_2026_03_22.md

Execute todos in STRICT phase order (Phase 0 → Phase 1 → ...).
Mark each todo done as you complete it.
Do NOT touch files outside your scope unless absolutely necessary.
If you need something from another agent's scope, document it as a dependency.

6 other agents are working in parallel. Respect scope boundaries.
Use EXACT names from CITADEL_VISION § Interface Contracts for collection names,
WebSocket message formats, component names, and API query params.

Start now. Read the plan file, then execute Phase 0.
```
