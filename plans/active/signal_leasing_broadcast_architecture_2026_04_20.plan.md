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

Path-to-$100M finalisation (2026-04-20) locked Signal Leasing as the **fourth commercial path** (alongside DART, IM, Reg
Umbrella). Two counterparties are already interested; targeted go-live **September 2026** at ~$5k/month combined revenue
to start.

Per user direction 2026-04-20: Signal Leasing requires a **heavy cross-repo refactor** so that `strategy-service` can
**externally broadcast strategy instructions to counterparties who execute on their own infrastructure**. This is a
net-new emission pathway distinct from DART signals-only (client→Odum-execution) and IM (Odum-managed capital).

Unlike DART's `Instructions integration` (block 5) which is _inbound_ (client sends instructions to Odum), Signal
Leasing is _outbound_: Odum emits strategy-level position/directional signals to authenticated counterparty endpoints.
No capital flows. No execution observation. Odum does not see counterparty fills.

This plan spans **strategy-service, execution-service, deployment-service, UAC, UTL, codex docs, CLAUDE.md files, cursor
rules, frontend, presentations, and registry data**. Multi-repo. Phased execution with QG gates between phases.

## Decisions locked 2026-04-20

User confirmed D1-D10 per the recommendations below (session 2026-04-20). Phase 1 pre-audit unblocked.

Additional scope added by user: counterparty observability UI (light dashboard) — integrated as Phase 5 deliverable
alongside the public marketing page. Specifically:

- **Counterparty observability UI** (light dashboard at `/signals/counterparty-view` or under a tenant-scoped route):
  - Signal history (last N emissions scoped to the counterparty's entitled slots)
  - Backtest comparison (Odum-held backtest numbers vs live signal performance — read-only reference)
  - Delivery health (webhook success rate, retry counts, avg latency)
  - Optional P&L attribution if the counterparty reports back
- Target user: institutional quant shops (QRT-style) who integrate primarily via backend API + webhook; the UI is
  secondary observability only, NOT a full trading platform.
- Scope: light dashboard only; NO catalogue / NO execution surface / NO research surface / NO reporting surface beyond
  the counterparty's own signal-delivery audit trail.

## Decisions needed before execution (block Phase 1 start)

| #   | Decision                          | Options                                                                                                                                                                                                                                                                | Recommendation                                                                                                                                 |
| --- | --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| D1  | **Emission service ownership**    | (a) New sub-package in `strategy-service` (`strategy_service/signal_broadcast/`); (b) dedicated new service repo (`signal-broadcast-service`); (c) extend `execution-service` with a "webhook adapter" that routes signals to counterparty endpoints instead of venues | (a) sub-package. Strategy-service already owns the signal-emission event path; dedicated repo adds 67th repo overhead without functional gain. |
| D2  | **Delivery transport**            | (a) Webhook HTTP POST signed JWT; (b) mTLS-protected REST pull endpoint; (c) Pub/Sub subscription with per-counterparty topic; (d) Hybrid — webhook primary, REST pull fallback                                                                                        | (d) Hybrid: webhook for real-time, REST pull for counterparty-initiated reconciliation + backfill                                              |
| D3  | **Authentication model**          | (a) Per-counterparty API key in Secret Manager; (b) OAuth client credentials; (c) mTLS client cert                                                                                                                                                                     | (a) + HMAC signing of payload. Simplest to roll out + standard in institutional signal feeds                                                   |
| D4  | **Which strategies are leasable** | (a) New lock state `SIGNAL_LEASABLE`; (b) Entitlement flag on counterparty-to-slot pair; (c) Per-counterparty allowlist of slot labels stored in UAC registry                                                                                                          | (c) Per-counterparty allowlist — matches how entitlements already work for DART clients. No new enum value needed.                             |
| D5  | **Delivery guarantees**           | (a) At-most-once (fire-and-forget); (b) At-least-once (retry with idempotency key); (c) Exactly-once (transactional outbox)                                                                                                                                            | (b) At-least-once with idempotency key; (c) is over-engineered for signal delivery                                                             |
| D6  | **Metering + audit granularity**  | (a) Per-signal emitted; (b) Per-signal-acknowledged; (c) Per-month usage summary only                                                                                                                                                                                  | (a) + (b): emit + ack events, both logged; billing reads from whichever the commercial contract specifies                                      |
| D7  | **Rate limiting**                 | (a) Per-counterparty (total calls/sec); (b) Per-counterparty-per-strategy; (c) Global                                                                                                                                                                                  | (b) Per-counterparty-per-strategy. Flexibility for noisy-neighbour protection at strategy level                                                |
| D8  | **Payload schema**                | (a) Full strategy state dump; (b) Position/directional delta only; (c) Both via negotiated schema depth                                                                                                                                                                | (c) Negotiated depth (minimal / standard / rich), mirrors block 5 schema-depth dimension from rule 10                                          |
| D9  | **Counterparty persona model**    | (a) Extend UI personas.ts with `signal-lease-counterparty-1` etc; (b) New domain entity "counterparty" distinct from "client"; (c) Treat as a restricted DART client variant                                                                                           | (b) New domain entity. Counterparty is semantically not a client (no capital allocation, no reporting surface access).                         |
| D10 | **Failure isolation**             | (a) Failed counterparty delivery blocks strategy-service; (b) Failed delivery logged + retried, never blocks strategy-service                                                                                                                                          | (b) per the shard-level-failure-isolation rule — counterparty endpoint failure must never impact strategy-service operation                    |

**All D1-D10 must be confirmed by user before Phase 1 executes.**

## Affected repos (8)

| Repo                        | Scope                                                                                                                                                                                                            | Owner workstream     |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------- |
| `unified-api-contracts`     | New `signal_broadcast/` sub-package: counterparty entity, delivery event, emit event, schema-depth enum, ack event. Per-counterparty entitlement schema.                                                         | UAC Citadel          |
| `unified-trading-library`   | `STRATEGY_SIGNAL_EMITTED_EXTERNAL` + `STRATEGY_SIGNAL_ACKNOWLEDGED` events in `STANDARD_LIFECYCLE_EVENTS`. Delivery helpers if shared.                                                                           | UTL events           |
| `strategy-service`          | New `strategy_service/signal_broadcast/` sub-package: emitter, per-counterparty router, signing, idempotency, retry, audit log                                                                                   | Services engineering |
| `execution-service`         | Minor — ensure execution events for Odum-operated strategies don't leak if the strategy is also leased externally; emission happens BEFORE execution, not instead                                                | Services engineering |
| `deployment-service`        | Counterparty endpoint + secret provisioning; Cloud Run deployment for the signal-broadcast worker if separate                                                                                                    | DevOps               |
| `unified-trading-system-ui` | New `/signals` public marketing page; admin surface at `/services/signals/counterparties` for Odum ops to see emission state; personas.ts — no new persona (counterparties are domain entities, not user-logins) | Frontend             |
| `unified-trading-pm`        | Codex docs (architecture, security, playbooks, SSOT index); CLAUDE.md rule addition; cursor rules for emission-specific discipline                                                                               | Docs                 |
| `.claude/memory/`           | Project memory entry on the design decisions + D1-D10 resolutions                                                                                                                                                | Memory               |

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
- Odum-strategy-level alpha decisions on which strategies to lease — commercial decision per-counterparty, not a code
  change

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

- [x] [HUMAN] P0. User confirmed D1-D10 resolutions 2026-04-20 ("confirm all recommendations"). Agent proceeds.
- [x] [AGENT] P0. D1-D10 resolutions captured inline in this plan as "Decisions locked 2026-04-20" section above.
- [x] [AGENT] P0. **Phase 0 success gate passed**: all 10 decisions recorded.

### Phase 1 — Pre-audit

- [x] [AGENT] P0. Grep every repo for existing `SIGNAL`, `broadcast`, `counterparty`, `signal_lease` tokens — establish
      what (if anything) already exists.
- [x] [AGENT] P0. Audit existing event taxonomy in UTL `STANDARD_LIFECYCLE_EVENTS` to confirm no naming collision.
- [x] [AGENT] P0. Audit secret-manager convention in existing code — reuse `ApiKeyReloader` pattern for counterparty
      credentials.
- [x] [AGENT] P0. Audit `shard-level-failure-isolation.md` + existing adapter error-classification pattern — signal
      emission must classify errors through same `classify_venue_error()` pattern.
- [x] [AGENT] P0. Build manifest of all UAC entity schemas that will need `signal_broadcast/` additions.
- [x] [AGENT] P0. **Phase 1 success gate**: pre-audit manifest committed; no naming collisions; design patterns to reuse
      identified. Manifest: `plans/signal_leasing_preaudit_manifest_2026_04_20.md`.

### Phase 2 — UAC + UTL contracts

- [x] [AGENT] P0. Create `unified_api_contracts/signal_broadcast/` sub-package with: - `Counterparty` entity (id, name,
      endpoint, auth_method, hmac_secret_ref, allowed_slots, schema_depth, active) - `SignalEmission` event schema
      (strategy_id, slot_label, emission_timestamp, signal_payload, idempotency_key, delivery_attempt) -
      `SignalAcknowledgement` event schema (emission_id, counterparty_id, ack_timestamp, status) - `SchemaDepth` enum
      (`minimal` | `standard` | `rich`) — mirrors rule 10 - `CounterpartyEntitlement` (counterparty_id, slot_label,
      active_from, active_to)
- [x] [AGENT] P0. Add `STRATEGY_SIGNAL_EMITTED_EXTERNAL` + `STRATEGY_SIGNAL_ACKNOWLEDGED` to UTL
      `STANDARD_LIFECYCLE_EVENTS`.
- [x] [AGENT] P0. Register new UAC external surface under `registry/capability_declarations/_signal_broadcast.py` per
      UAC Citadel architecture convention.
- [x] [AGENT] P0. QG on UAC + UTL: `bash scripts/quality-gates.sh` in each repo; clean + committed.
- [x] [AGENT] P0. **Phase 2 success gate**: UAC contracts shipped, UTL events registered, importable from consumer
      repos.

### Phase 3 — strategy-service signal-broadcast sub-package [SHIPPED 2026-04-20]

**Status audit 2026-04-20 (evening update)**: sub-package complete at 10 files in
`strategy-service/strategy_service/signal_broadcast/`: `__init__.py`, `audit.py`, `broadcaster.py`,
`config.py`, `config_reloaders.py`, `credentials.py`, `emitter.py`, `failure_isolation.py`, `router.py`,
`transport.py`. Orchestrator + broadcaster facade + typed config reloaders shipped in `1fa2557`, tests +
bandaids in `da1770e`, C901/B008 refactor in `c554b02`. 54/54 tests green. basedpyright clean.

- [x] [AGENT] P0. `router.py` — maps (slot_label, counterparty_id) → entitled emission + schema depth.
- [x] [AGENT] P0. `transport.py` — webhook HTTP POST + idempotency retry; REST pull endpoint for counterparty-
      initiated reconciliation (D2 hybrid).
- [x] [AGENT] P0. `audit.py` — emits `STRATEGY_SIGNAL_EMITTED_EXTERNAL` event + BQ billing log.
- [x] [AGENT] P0. `credentials.py` — `ApiKeyReloader` pattern for counterparty HMAC secrets.
- [x] [AGENT] P0. `failure_isolation.py` — per-counterparty try/except with `classify_venue_error()` +
      `ADAPTER_FETCH_FAILED` emit; never raises to generator.
- [x] [AGENT] P0. `config.py` — typed config (verified).
- [x] [AGENT] P0. **`emitter.py`** — SHIPPED `1fa2557` + `c554b02`. SignalEmitter orchestrator wires the 6
      siblings: per-slot counterparty resolution via router, per-cp schema-depth projection, HMAC signing,
      webhook dispatch via transport, audit-event emission, failure_isolation wrap on every per-cp call.
      D5 idempotency (uuid5-based emission_id), D7 token-bucket rate limit, D10 shard-level isolation.
- [x] [AGENT] P0. ServiceBootstrap integration — `strategy_service/cli/service_entry.py` already calls
      `ServiceBootstrap(service_name="strategy-service", ...)`; `_get_config()` now invokes
      `start_signal_broadcast_reloaders` at startup (`1fa2557`).
- [x] [AGENT] P0. Health API endpoint — `strategy_service/api/main.py` extended so `data_freshness`
      returns the existing `last_processed_date`/`stale` keys PLUS a nested `signal_broadcast` block sourced
      from `broadcaster.data_freshness()`. REST-pull router mounted when the broadcaster singleton is active
      (`1fa2557`).
- [x] [AGENT] P0. Typed config reloaders — `strategy_service/signal_broadcast/config_reloaders.py` exposes
      `start_signal_broadcast_reloaders(service_config: SignalBroadcastConfig, ...)` (not `object`, no
      `getattr`). Uses `SignalBroadcaster.build()` + `ApiKeyReloader` under the hood. QG STEP 5.34 satisfied.
- [x] [AGENT] P0. Unit tests 90%+ coverage — 50 unit tests shipped (`da1770e`). Coverage of signal_broadcast
      sub-package: 90% overall (emitter 99%, router 100%, audit 100%, broadcaster 100%, failure_isolation
      100%, transport 77%, credentials 77%, config 84%). Floor ratchet deferred — signal_broadcast is new,
      not ratcheted against an existing baseline.
- [x] [AGENT] P0. Integration tests — `tests/integration/signal_broadcast/test_broadcast_end_to_end.py` (4
      tests): two-cp-both-ack, retry-on-5xx-then-200, one-cp-down-doesn't-block-other, idempotency-key-
      reused-across-retries (X-Odum-Emission-Id header equality). Uses `responses` library — zero live HTTP.
- [ ] [AGENT] P0. **Phase 3 success gate**: 54/54 signal_broadcast tests green; basedpyright clean on
      `strategy_service/signal_broadcast/`; ruff clean on all 4 sb-owned errors that surfaced on initial QG
      (C901 complexity x3 + B008 Query defaults, fixed `c554b02`). Repo QG still blocked by 3 pre-existing
      `RUF043` issues in `tests/unit/availability/test_allocator_enforcement.py` (concurrent sibling agent's
      unstaged edits, not signal-broadcast work). Signal-broadcast Phase 3 itself is complete; full-repo QG
      gate will flip to green once the sibling agent commits their fix.

### Phase 4 — deployment-service wiring [REMAINING]

**Clarification 2026-04-20**: this phase wires **deployment-service directly** (the Python service that owns
Cloud Run manifests + Secret Manager scripts + VM tarballs). `deployment-api` is the thin observability facade
over deployment-service — NOT the direct wiring target. Touch `deployment-api` only if we want ops to see
counterparty-endpoint state via its API (that's Phase 5 admin-surface territory, not infra).

- [ ] [AGENT] P0. Secret Manager entries for per-counterparty HMAC secrets + auth keys in
      `deployment-service/scripts/` (per `interface-credential-convention.md`).
- [ ] [AGENT] P0. Cloud Run deployment — decide: (a) extend strategy-service's existing Cloud Run service to host
      the signal-broadcast sub-package, OR (b) separate Cloud Run worker. Default to (a) — strategy-service
      already owns signal emission; no need for a 67th service. Update `deployment-service/cloud-run/` manifest
      accordingly.
- [ ] [AGENT] P0. Per-counterparty webhook target config in `deployment-service/config/` (env var allowlist)
      and/or Pub/Sub topic provisioning. Per D4 — entitlements source from UAC `CounterpartyEntitlement`.
- [ ] [AGENT] P0. Rate-limiting + retry configuration per D7 (per-counterparty-per-strategy). Config lives in
      strategy-service signal_broadcast `config.py` + deployment-service env injection.
- [ ] [AGENT] P0. VM tarball refresh per `deployment-service/scripts/vm/create-code-tarballs.sh` if VMs consume
      strategy-service — `bash ... --include strategy-service` if signal_broadcast sub-package affects tarball.
- [ ] [AGENT] P0. **Phase 4 success gate**: deployment infra provisioned for both counterparties (staging secrets
      + Cloud Run manifest + webhook config); smoke test delivery confirmed end-to-end on staging.

### Phase 5 — frontend (admin + counterparty observability UI)

**Scope boundary (clarified 2026-04-20):** the **public marketing surface** for the Signals Service (`/signals`
page, nav entry, `/briefings/signals-out` pillar, direction-arrow wording, cross-links to `/platform/signals-in`)
is owned by the sister [marketing_site_restructure_2026_04_20](marketing_site_restructure_2026_04_20.plan.md) plan
and is substantially **already shipped**. This plan now owns only the backend-adjacent Phase 5 components:
counterparty observability UI + admin surface + counterparty-persona integration. Previously-listed marketing
stubs are consolidated into a single "shipped under sister plan" entry below.

- [x] [AGENT] P0. Public marketing surface (signals.html / signals/page.tsx / nav entry / platform 3-card fix /
      `/briefings/signals-out` pillar) — **shipped under marketing_site_restructure**. No further work here.
- [ ] [AGENT] P0. **Counterparty observability UI** — light dashboard at
      `app/(platform)/services/signals/dashboard/page.tsx`. Components:
      - `<SignalHistoryTable>` — last N emissions scoped to entitled slots; filter by slot / date / status
      - `<BacktestComparisonPanel>` — Odum-held backtest numbers vs live signal aggregate (read-only)
      - `<DeliveryHealthPanel>` — webhook success rate, retry counts, avg latency, last-delivery timestamp
      - `<PnlAttributionPanel>` — OPTIONAL, renders only if counterparty reports P&L back
      - NO catalogue / NO execution / NO research / NO reporting beyond signal-delivery audit.
      - **No-orphan-page discipline**: wire inbound link from public `/signals` page CTA ("Existing
        counterparty? View your dashboard →", gated by login) AND from counterparty-login post-auth redirect.
- [ ] [AGENT] P0. **Admin surface** at `app/(platform)/services/signals/counterparties/page.tsx` — list
      counterparties, show emission state, toggle entitlements, view per-counterparty delivery health.
      **No-orphan discipline**: inbound link from admin platform-shell nav + admin landing page service-tile.
- [ ] [AGENT] P0. **Counterparty persona** (new domain entity per D9) — NOT a UI persona in `personas.ts`,
      NOT a DART client variant. Distinct domain entity with its own auth provider integration (tenant-scoped).
      Define in UAC under `signal_broadcast/Counterparty` (already shipped) — wire UI auth gate to recognise
      counterparty-type users and route them to `/services/signals/dashboard` on login.
- [ ] [AGENT] P0. **Route-audit gate**: before Phase 5 marks done, `rg "href=\"/services/signals" --type ts`
      must show inbound-link paths for both `/dashboard` and `/counterparties` routes. No-orphan rule enforced.
- [ ] [AGENT] P0. **Phase 5 success gate**: `/signals` public page live + nav updated + platform accurate (shipped);
      counterparty observability UI renders with mocked data on staging; admin counterparty surface operational;
      `npm test` + `tsc --noEmit` clean.

### Phase 6 — codex docs + CLAUDE.md + memory + cursor rules

- [ ] [AGENT] P0. New codex doc: `codex/14-playbooks/shared-core/signal-broadcast-architecture.md` — implementation
      map + failure isolation pattern + auth model.
- [ ] [AGENT] P0. Update `codex/14-playbooks/commercial-model/signal-leasing.md` with Sept 2026 go-live + 2-client
      anchor + reference to this plan.
- [ ] [AGENT] P0. Update `_ssot-rules/04-dart-commercial-axes.md` — brief note Signal Leasing fourth path references
      this plan.
- [ ] [AGENT] P0. Update root `CLAUDE.md` (workspace root) — add key rule: "Strategy-service signal emission to external
      counterparties MUST use shard-level failure isolation + classify_venue_error() pattern; counterparty credentials
      via ApiKeyReloader."
- [ ] [AGENT] P0. Update `codex/00-SSOT-INDEX.md` — register `signal-broadcast-architecture.md` and UAC
      `signal_broadcast/` sub-package.
- [ ] [AGENT] P0. Update memory under
      `/Users/ikennaigboaka/.claude/projects/-Users-ikennaigboaka-Code-unified-trading-system-repos/memory/` with a
      project entry.
- [ ] [AGENT] P1. Cursor rule in `.cursor/rules/` if signal-broadcast introduces a pattern other adapters should follow
      (likely not — emission reuses existing adapter-error-classification rule).
- [ ] [AGENT] P0. **Phase 6 success gate**: docs + CLAUDE.md + memory updated, cross-references all resolve.

### Phase 7 — presentations + revenue projection sync

- [ ] [AGENT] P0. Update `unified-trading-system-ui/app/(platform)/investor-relations/plan-presentation/data.ts` slide 9
      or add a signal-leasing detail to reflect Sept 2026 go-live + $5k/mo.
- [ ] [AGENT] P0. Update `board-presentation-data.ts` slide 8 Signal Leasing entry to be more concrete ("2
      counterparties live Sept 2026, $5k/mo combined, target 4-6 counterparties by end-2027").
- [ ] [AGENT] P0. Update `codex/14-playbooks/commercial-model/revenue-projection-2026-monthly.md` monthly table — scale
      Sept-Dec signal-leasing revenue from £12k+ down to £4k/mo (≈$5k) combined.
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

| Risk                                                             | Probability | Impact | Mitigation                                                                                                                        |
| ---------------------------------------------------------------- | ----------- | ------ | --------------------------------------------------------------------------------------------------------------------------------- |
| Counterparty endpoint downtime stalls strategy-service           | Medium      | High   | Shard-level failure isolation (D10) + per-counterparty circuit breaker                                                            |
| Counterparty endpoint leaks data cross-client                    | Low         | High   | mTLS + per-counterparty credentials + allowlist check on every emission                                                           |
| Idempotency key conflicts in retry storm                         | Low         | Medium | Per-signal UUID + counterparty-side dedup                                                                                         |
| Orchestrator commit drift on this repo (observed in Stage 2)     | High        | Low    | Small per-phase commits + `--no-verify` authorised for path-to-100M adjacent work                                                 |
| Scope creep (e.g. P&L-attribution-back-from-counterparty)        | Medium      | Medium | Explicit out-of-scope list at top; park in follow-up plan if needed                                                               |
| Counterparty legal agreements not finalised by Sept 2026 go-live | Medium      | High   | Legal workstream runs parallel; plan ships tech infra regardless; actual emission flipped on per-counterparty after legal signoff |

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
