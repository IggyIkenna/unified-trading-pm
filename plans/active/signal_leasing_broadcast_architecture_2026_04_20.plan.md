---
title: "Signal Leasing — broadcast-capable external-counterparty architecture"
status: active
priority: P0
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-20
depends_on:
  - path_to_100m_finalization_2026_04_20
---

# Signal Leasing — broadcast-capable external-counterparty architecture

## Context

Path-to-$100M finalisation (2026-04-20) locked Signal Leasing as the **fourth commercial path** (alongside DART,
IM, Reg Umbrella). Two counterparties are already interested; targeted go-live **September 2026** at ~$5k/month
combined revenue to start.

Per user direction 2026-04-20: Signal Leasing requires a **heavy cross-repo refactor** so that `strategy-service`
can **externally broadcast strategy instructions to counterparties who execute on their own infrastructure**. This
is a net-new emission pathway distinct from DART signals-only (client→Odum-execution) and IM (Odum-managed
capital).

Unlike DART's `Instructions integration` (block 5) which is *inbound* (client sends instructions to Odum),
Signal Leasing is *outbound*: Odum emits strategy-level position/directional signals to authenticated counterparty
endpoints. No capital flows. No execution observation. Odum does not see counterparty fills.

This plan spans **strategy-service, execution-service, deployment-service, UAC, UTL, codex docs, CLAUDE.md files,
cursor rules, frontend, presentations, and registry data**. Multi-repo. Phased execution with QG gates between
phases.

## Decisions locked 2026-04-20

User confirmed D1-D10 per the recommendations below (session 2026-04-20). Phase 1 pre-audit unblocked.

Additional scope added by user: counterparty observability UI (light dashboard) — integrated as Phase 5 deliverable
alongside the public marketing page. Specifically:

- **Counterparty observability UI** (light dashboard at `/signals/counterparty-view` or under a tenant-scoped
  route):
  - Signal history (last N emissions scoped to the counterparty's entitled slots)
  - Backtest comparison (Odum-held backtest numbers vs live signal performance — read-only reference)
  - Delivery health (webhook success rate, retry counts, avg latency)
  - Optional P&L attribution if the counterparty reports back
- Target user: institutional quant shops (QRT-style) who integrate primarily via backend API + webhook; the UI is
  secondary observability only, NOT a full trading platform.
- Scope: light dashboard only; NO catalogue / NO execution surface / NO research surface / NO reporting surface
  beyond the counterparty's own signal-delivery audit trail.

## Decisions needed before execution (block Phase 1 start)

| # | Decision | Options | Recommendation |
|---|---|---|---|
| D1 | **Emission service ownership** | (a) New sub-package in `strategy-service` (`strategy_service/signal_broadcast/`); (b) dedicated new service repo (`signal-broadcast-service`); (c) extend `execution-service` with a "webhook adapter" that routes signals to counterparty endpoints instead of venues | (a) sub-package. Strategy-service already owns the signal-emission event path; dedicated repo adds 67th repo overhead without functional gain. |
| D2 | **Delivery transport** | (a) Webhook HTTP POST signed JWT; (b) mTLS-protected REST pull endpoint; (c) Pub/Sub subscription with per-counterparty topic; (d) Hybrid — webhook primary, REST pull fallback | (d) Hybrid: webhook for real-time, REST pull for counterparty-initiated reconciliation + backfill |
| D3 | **Authentication model** | (a) Per-counterparty API key in Secret Manager; (b) OAuth client credentials; (c) mTLS client cert | (a) + HMAC signing of payload. Simplest to roll out + standard in institutional signal feeds |
| D4 | **Which strategies are leasable** | (a) New lock state `SIGNAL_LEASABLE`; (b) Entitlement flag on counterparty-to-slot pair; (c) Per-counterparty allowlist of slot labels stored in UAC registry | (c) Per-counterparty allowlist — matches how entitlements already work for DART clients. No new enum value needed. |
| D5 | **Delivery guarantees** | (a) At-most-once (fire-and-forget); (b) At-least-once (retry with idempotency key); (c) Exactly-once (transactional outbox) | (b) At-least-once with idempotency key; (c) is over-engineered for signal delivery |
| D6 | **Metering + audit granularity** | (a) Per-signal emitted; (b) Per-signal-acknowledged; (c) Per-month usage summary only | (a) + (b): emit + ack events, both logged; billing reads from whichever the commercial contract specifies |
| D7 | **Rate limiting** | (a) Per-counterparty (total calls/sec); (b) Per-counterparty-per-strategy; (c) Global | (b) Per-counterparty-per-strategy. Flexibility for noisy-neighbour protection at strategy level |
| D8 | **Payload schema** | (a) Full strategy state dump; (b) Position/directional delta only; (c) Both via negotiated schema depth | (c) Negotiated depth (minimal / standard / rich), mirrors block 5 schema-depth dimension from rule 10 |
| D9 | **Counterparty persona model** | (a) Extend UI personas.ts with `signal-lease-counterparty-1` etc; (b) New domain entity "counterparty" distinct from "client"; (c) Treat as a restricted DART client variant | (b) New domain entity. Counterparty is semantically not a client (no capital allocation, no reporting surface access). |
| D10 | **Failure isolation** | (a) Failed counterparty delivery blocks strategy-service; (b) Failed delivery logged + retried, never blocks strategy-service | (b) per the shard-level-failure-isolation rule — counterparty endpoint failure must never impact strategy-service operation |

**All D1-D10 must be confirmed by user before Phase 1 executes.**

## Affected repos (8)

| Repo | Scope | Owner workstream |
|---|---|---|
| `unified-api-contracts` | New `signal_broadcast/` sub-package: counterparty entity, delivery event, emit event, schema-depth enum, ack event. Per-counterparty entitlement schema. | UAC Citadel |
| `unified-trading-library` | `STRATEGY_SIGNAL_EMITTED_EXTERNAL` + `STRATEGY_SIGNAL_ACKNOWLEDGED` events in `STANDARD_LIFECYCLE_EVENTS`. Delivery helpers if shared. | UTL events |
| `strategy-service` | New `strategy_service/signal_broadcast/` sub-package: emitter, per-counterparty router, signing, idempotency, retry, audit log | Services engineering |
| `execution-service` | Minor — ensure execution events for Odum-operated strategies don't leak if the strategy is also leased externally; emission happens BEFORE execution, not instead | Services engineering |
| `deployment-service` | Counterparty endpoint + secret provisioning; Cloud Run deployment for the signal-broadcast worker if separate | DevOps |
| `unified-trading-system-ui` | New `/signals` public marketing page; admin surface at `/services/signals/counterparties` for Odum ops to see emission state; personas.ts — no new persona (counterparties are domain entities, not user-logins) | Frontend |
| `unified-trading-pm` | Codex docs (architecture, security, playbooks, SSOT index); CLAUDE.md rule addition; cursor rules for emission-specific discipline | Docs |
| `.claude/memory/` | Project memory entry on the design decisions + D1-D10 resolutions | Memory |

## Cross-references

- [path_to_100m_finalization_2026_04_20.plan.md](path_to_100m_finalization_2026_04_20.plan.md) — parent context
- `codex/14-playbooks/commercial-model/signal-leasing.md` — commercial framing (already shipped)
- `codex/14-playbooks/_ssot-rules/04-dart-commercial-axes.md` — notes Signal Leasing as fourth path
- `codex/14-playbooks/shared-core/dart-pricing-axes.md` — pricing dimensions
- `codex/04-architecture/shard-level-failure-isolation.md` — D10 rule anchor
- `codex/04-architecture/interface-credential-convention.md` — authentication pattern reuse

## Out of scope (explicit)

- Building the counterparty discovery / sales CRM surface (sales-ops, not product)
- Legal contract templates for signal-lease agreements (legal workstream)
- Deep P&L-attribution-back-from-counterparty flow (that's a year-2 feature requiring counterparty reporting-back
  mechanics)
- Replacing existing inbound `Instructions integration` (block 5 per rule 10) — that's DART, unchanged
- Odum-strategy-level alpha decisions on which strategies to lease — commercial decision per-counterparty, not a
  code change

## Execution DAG

```
Phase 0 (decisions) ──▶ Phase 1 (pre-audit) ──▶ Phase 2 (UAC + UTL contracts)
                                                          ↓
                                                 Phase 3 (strategy-service emitter)
                                                          ↓
                                                 Phase 4 (deployment-service wiring)
                                                          ↓
                                                 Phase 5 (frontend marketing + admin)
                                                          ↓
                                                 Phase 6 (codex docs + CLAUDE.md + memory + rules)
                                                          ↓
                                                 Phase 7 (presentations + signal-leasing.md + revenue proj)
                                                          ↓
                                                 Phase 8 (quality gates + integration test + handoff)
```

Phases 2 + 5 + 6 + 7 are parallelisable after Phase 1. Phases 3 and 4 are sequential (emitter before deployment).

## Phases

### Phase 0 — Decisions gate

- [ ] [HUMAN] P0. User confirms D1-D10 resolutions. Agent does NOT proceed without written confirmation.
- [ ] [AGENT] P0. Capture D1-D10 resolutions inline in this plan as "Locked decisions".
- [ ] [AGENT] P0. **Phase 0 success gate**: all 10 decisions recorded.

### Phase 1 — Pre-audit

- [ ] [AGENT] P0. Grep every repo for existing `SIGNAL`, `broadcast`, `counterparty`, `signal_lease` tokens — establish
      what (if anything) already exists.
- [ ] [AGENT] P0. Audit existing event taxonomy in UTL `STANDARD_LIFECYCLE_EVENTS` to confirm no naming collision.
- [ ] [AGENT] P0. Audit secret-manager convention in existing code — reuse `ApiKeyReloader` pattern for counterparty
      credentials.
- [ ] [AGENT] P0. Audit `shard-level-failure-isolation.md` + existing adapter error-classification pattern — signal
      emission must classify errors through same `classify_venue_error()` pattern.
- [ ] [AGENT] P0. Build manifest of all UAC entity schemas that will need `signal_broadcast/` additions.
- [ ] [AGENT] P0. **Phase 1 success gate**: pre-audit manifest committed; no naming collisions; design patterns to
      reuse identified.

### Phase 2 — UAC + UTL contracts

- [ ] [AGENT] P0. Create `unified_api_contracts/signal_broadcast/` sub-package with:
      - `Counterparty` entity (id, name, endpoint, auth_method, hmac_secret_ref, allowed_slots, schema_depth, active)
      - `SignalEmission` event schema (strategy_id, slot_label, emission_timestamp, signal_payload, idempotency_key,
        delivery_attempt)
      - `SignalAcknowledgement` event schema (emission_id, counterparty_id, ack_timestamp, status)
      - `SchemaDepth` enum (`minimal` | `standard` | `rich`) — mirrors rule 10
      - `CounterpartyEntitlement` (counterparty_id, slot_label, active_from, active_to)
- [ ] [AGENT] P0. Add `STRATEGY_SIGNAL_EMITTED_EXTERNAL` + `STRATEGY_SIGNAL_ACKNOWLEDGED` to UTL
      `STANDARD_LIFECYCLE_EVENTS`.
- [ ] [AGENT] P0. Register new UAC external surface under `registry/capability_declarations/_signal_broadcast.py`
      per UAC Citadel architecture convention.
- [ ] [AGENT] P0. QG on UAC + UTL: `bash scripts/quality-gates.sh` in each repo; clean + committed.
- [ ] [AGENT] P0. **Phase 2 success gate**: UAC contracts shipped, UTL events registered, importable from consumer
      repos.

### Phase 3 — strategy-service signal-broadcast sub-package

- [ ] [AGENT] P0. Create `strategy_service/signal_broadcast/` sub-package:
      - `emitter.py`: consumes strategy-service's internal `STRATEGY_SIGNAL_GENERATED` events, builds the payload per
        counterparty's entitled slots, signs with HMAC, dispatches.
      - `router.py`: maps (slot_label, counterparty_id) → entitled emission + schema depth.
      - `transport.py`: webhook HTTP POST with at-least-once retry + idempotency; REST pull endpoint for
        counterparty-initiated reconciliation (D2 hybrid).
      - `audit.py`: emits `STRATEGY_SIGNAL_EMITTED_EXTERNAL` event + logs to BQ billing table.
      - `credentials.py`: uses `ApiKeyReloader` pattern to hot-reload counterparty HMAC secrets.
      - `failure_isolation.py`: wraps per-counterparty delivery in try/except that classifies errors through
        `classify_venue_error()` and emits `ADAPTER_FETCH_FAILED` pattern. Never raises to the generator.
- [ ] [AGENT] P0. Config reloader for signal-broadcast per service-infra rules (typed config).
- [ ] [AGENT] P0. ServiceBootstrap + Health API endpoints registered per rule.
- [ ] [AGENT] P0. Unit tests: 90%+ coverage of emitter.py + router.py + audit.py.
- [ ] [AGENT] P0. Integration tests with mocked counterparty endpoints + idempotency retry scenarios.
- [ ] [AGENT] P0. **Phase 3 success gate**: strategy-service QG clean; signal broadcast runs end-to-end against
      mock counterparty.

### Phase 4 — deployment-service wiring

- [ ] [AGENT] P0. Secret-manager entries for per-counterparty HMAC secrets + auth keys, per credential convention.
- [ ] [AGENT] P0. Cloud Run deployment of signal-broadcast worker if separate — or confirm strategy-service's
      existing Cloud Run service absorbs the emitter.
- [ ] [AGENT] P0. Per-counterparty Pub/Sub topic or direct webhook target configuration.
- [ ] [AGENT] P0. Rate-limiting + retry configuration per counterparty (D7 per-strategy).
- [ ] [AGENT] P0. **Phase 4 success gate**: deployment infra provisioned for both counterparties; smoke test delivery
      confirmed.

### Phase 5 — frontend (marketing + admin + counterparty observability UI)

- [x] [AGENT] P0. `public/signals.html` — marketing landing page for external-facing Signals service. **Shipped
      2026-04-20.**
- [x] [AGENT] P0. `app/(public)/signals/page.tsx` — Next.js route using `MarketingStaticFromFile`. **Shipped
      2026-04-20.**
- [x] [AGENT] P0. Add "Signals" to public nav. **Shipped 2026-04-20 across all 7 marketing HTML pages.**
- [x] [AGENT] P0. `public/platform.html` — fix "Built for different entry points" 3-card section with
      rule-04-faithful framing + cross-link to `/signals`. **Shipped 2026-04-20.**
- [ ] [AGENT] P0. **Counterparty observability UI** — light dashboard under a tenant-scoped route (e.g.
      `/signals/dashboard` or under a per-counterparty subdomain). Components:
      - `<SignalHistoryTable>` — last N emissions scoped to entitled slots; filter by slot / date / status
      - `<BacktestComparisonPanel>` — Odum-held backtest performance numbers vs live signal aggregate; read-only
      - `<DeliveryHealthPanel>` — webhook success rate, retry counts, avg latency, last-delivery timestamp per slot
      - `<PnlAttributionPanel>` — OPTIONAL, only renders if counterparty reports P&L back
      - No catalogue, no execution, no research, no reporting beyond signal-delivery audit
- [ ] [AGENT] P0. Admin surface at `app/(platform)/services/signals/counterparties/page.tsx` — list counterparties,
      show emission state, toggle entitlements, view per-counterparty delivery health.
- [ ] [AGENT] P0. Counterparty persona (new domain entity per D9) integration — tenant-scoped auth for the
      observability UI. Per rule-03 same-system principle, the UI components reuse existing dashboards; scoped by
      entitlement to the counterparty-observability slice only.
- [ ] [AGENT] P0. **Phase 5 success gate**: `/signals` public page live + nav updated + platform accurate
      (shipped); counterparty observability UI renders with mocked data on staging; admin counterparty surface
      operational; `npm test` + `tsc --noEmit` clean.

### Phase 6 — codex docs + CLAUDE.md + memory + cursor rules

- [ ] [AGENT] P0. New codex doc: `codex/14-playbooks/shared-core/signal-broadcast-architecture.md` — implementation
      map + failure isolation pattern + auth model.
- [ ] [AGENT] P0. Update `codex/14-playbooks/commercial-model/signal-leasing.md` with Sept 2026 go-live + 2-client
      anchor + reference to this plan.
- [ ] [AGENT] P0. Update `_ssot-rules/04-dart-commercial-axes.md` — brief note Signal Leasing fourth path references
      this plan.
- [ ] [AGENT] P0. Update root `CLAUDE.md` (workspace root) — add key rule: "Strategy-service signal emission to
      external counterparties MUST use shard-level failure isolation + classify_venue_error() pattern; counterparty
      credentials via ApiKeyReloader."
- [ ] [AGENT] P0. Update `codex/00-SSOT-INDEX.md` — register `signal-broadcast-architecture.md` and
      UAC `signal_broadcast/` sub-package.
- [ ] [AGENT] P0. Update memory under
      `/Users/ikennaigboaka/.claude/projects/-Users-ikennaigboaka-Code-unified-trading-system-repos/memory/`
      with a project entry.
- [ ] [AGENT] P1. Cursor rule in `.cursor/rules/` if signal-broadcast introduces a pattern other adapters should
      follow (likely not — emission reuses existing adapter-error-classification rule).
- [ ] [AGENT] P0. **Phase 6 success gate**: docs + CLAUDE.md + memory updated, cross-references all resolve.

### Phase 7 — presentations + revenue projection sync

- [ ] [AGENT] P0. Update `unified-trading-system-ui/app/(platform)/investor-relations/plan-presentation/data.ts`
      slide 9 or add a signal-leasing detail to reflect Sept 2026 go-live + $5k/mo.
- [ ] [AGENT] P0. Update `board-presentation-data.ts` slide 8 Signal Leasing entry to be more concrete ("2
      counterparties live Sept 2026, $5k/mo combined, target 4-6 counterparties by end-2027").
- [ ] [AGENT] P0. Update `codex/14-playbooks/commercial-model/revenue-projection-2026-monthly.md` monthly table —
      scale Sept-Dec signal-leasing revenue from £12k+ down to £4k/mo (≈$5k) combined.
- [ ] [AGENT] P0. Update `commercial-model/cash-deployment-plan.md` — minor revenue revision cascades year-end cash
      projection down from ~£464k to ~£429k. Still healthy; no funding implication.
- [ ] [AGENT] P0. **Phase 7 success gate**: decks + revenue projection consistent with the $5k/mo anchor.

### Phase 8 — quality gates + integration test + handoff

- [ ] [AGENT] P0. Full workspace QG: every affected repo `bash scripts/quality-gates.sh`.
- [ ] [AGENT] P0. End-to-end integration test: mock counterparty endpoint receives a signed signal within 5 seconds of
      strategy-service emission; idempotency retry behaves correctly; delivery log populated correctly.
- [ ] [AGENT] P0. Playwright spec for admin `/services/signals/counterparties` page if that landed.
- [ ] [AGENT] P0. Summary report to user with commit SHAs + open items.
- [ ] [AGENT] P0. Memory updated with final state.

## Verification

1. UAC `signal_broadcast/` schema importable from strategy-service + deployment-service.
2. `STRATEGY_SIGNAL_EMITTED_EXTERNAL` event fires on every signal delivery; BQ billing table reflects counts.
3. Counterparty endpoint failure does NOT block strategy-service (shard-level failure isolation).
4. Two counterparty fixtures (staging) receive signals end-to-end.
5. `/signals` page live; admin surface operational.
6. Codex docs + CLAUDE.md + memory updated; SSOT index registers new entities.
7. Board + plan deck slides reflect Sept 2026 go-live + $5k/mo.
8. Revenue projection 2026 reflects adjusted numbers; cash projection healthy.

## Risks + mitigations

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Counterparty endpoint downtime stalls strategy-service | Medium | High | Shard-level failure isolation (D10) + per-counterparty circuit breaker |
| Counterparty endpoint leaks data cross-client | Low | High | mTLS + per-counterparty credentials + allowlist check on every emission |
| Idempotency key conflicts in retry storm | Low | Medium | Per-signal UUID + counterparty-side dedup |
| Orchestrator commit drift on this repo (observed in Stage 2) | High | Low | Small per-phase commits + `--no-verify` authorised for path-to-100M adjacent work |
| Scope creep (e.g. P&L-attribution-back-from-counterparty) | Medium | Medium | Explicit out-of-scope list at top; park in follow-up plan if needed |
| Counterparty legal agreements not finalised by Sept 2026 go-live | Medium | High | Legal workstream runs parallel; plan ships tech infra regardless; actual emission flipped on per-counterparty after legal signoff |

## Success criteria

- All 8 phases executed
- Counterparty signal delivery live on staging with both counterparty fixtures
- 2 production counterparties onboardable by Sept 2026
- All 8 affected repos + memory + docs aligned
- Revenue projection + decks reflect the ~$5k/mo Sept 2026 anchor

## What this plan does NOT do

- Build the sales / commercial close pipeline for the two interested counterparties (sales workstream)
- Write counterparty-side integration code (they write their own webhook consumers; Odum provides API docs + test
  harness)
- Replace DART `Instructions integration` (block 5) — that's inbound, unchanged
- Migrate existing clients to signal leasing — that's a commercial-path-change decision per-client
- Affect the IM pricing mechanics or CME co-invest structure — those are IM, not signal leasing

## Follow-ups for post-Sept-2026 wave 2

- Counterparty P&L reporting-back flow (for revenue-share pricing model per signal-leasing.md Option 3)
- Self-serve counterparty onboarding portal
- Cross-counterparty rate-limiting + fair-queue scheduling
- Signal-quality attribution back to Odum research for strategy refinement
