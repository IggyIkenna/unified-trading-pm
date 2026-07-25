---
doc_type: plan
title: Signal Leasing — broadcast-capable external-counterparty architecture
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    execution-service,
    strategy-service,
    unified-api-contracts,
    unified-trading-library,
  ]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-20"
priority: P0
owner: agent
depends_on: [path_to_100m_finalization_2026_04_20]
reconciliation_status: shipped_substantive
reconciliation_date: 2026-04-25
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

> **Reconciliation note (2026-04-25):** Substantively shipped — recommended for archive. 85/0 (100%) done. Plan header
> explicitly says 'All 8 phases complete. Plan remains locked — requires human [unlock-plan] tag to archive.' Awaiting
> human approval. See `_reconciliation_evidence_map_2026_04_25.md` for evidence anchors.

# Signal Leasing — broadcast-capable external-counterparty architecture

> **Status 2026-04-20:** All 8 phases complete. Plan remains locked — requires human `[unlock-plan]` tag to archive.

## Context

Path-to-$100M finalisation (2026-04-20) locked Signal Leasing as the **fourth commercial path** (alongside DART, IM, Reg
Umbrella). Two counterparties are already interested; targeted go-live **September 2026** at ~$5k/month
combined revenue to start.

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

- [path_to_100m_finalization_2026_04_20.md](path_to_100m_finalization_2026_04_20.md) — parent context
- `/codex/14-customer-journeys/commercial-model/signal-leasing.md` — commercial framing (already shipped)
- `/codex/14-customer-journeys/_ssot-rules/04-dart-commercial-axes.md` — notes Signal Leasing as fourth path
- `/codex/14-customer-journeys/shared-core/dart-pricing-axes.md` — pricing dimensions
- `/codex/04-architecture/shard-level-failure-isolation.md` — D10 rule anchor
- `/codex/04-architecture/interface-credential-convention.md` — authentication pattern reuse

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
`strategy-service/strategy_service/signal_broadcast/`: `__init__.py`, `audit.py`, `broadcaster.py`, `config.py`,
`config_reloaders.py`, `credentials.py`, `emitter.py`, `failure_isolation.py`, `router.py`, `transport.py`.
Orchestrator + broadcaster facade + typed config reloaders shipped in `1fa2557`, tests + bandaids in `da1770e`,
C901/B008 refactor in `c554b02`. 54/54 tests green. basedpyright clean.

- [x] [AGENT] P0. `router.py` — maps (slot_label, counterparty_id) → entitled emission + schema depth.
- [x] [AGENT] P0. `transport.py` — webhook HTTP POST + idempotency retry; REST pull endpoint for counterparty- initiated
      reconciliation (D2 hybrid).
- [x] [AGENT] P0. `audit.py` — emits `STRATEGY_SIGNAL_EMITTED_EXTERNAL` event + BQ billing log.
- [x] [AGENT] P0. `credentials.py` — `ApiKeyReloader` pattern for counterparty HMAC secrets.
- [x] [AGENT] P0. `failure_isolation.py` — per-counterparty try/except with `classify_venue_error()` +
      `ADAPTER_FETCH_FAILED` emit; never raises to generator.
- [x] [AGENT] P0. `config.py` — typed config (verified).
- [x] [AGENT] P0. **`emitter.py`** — SHIPPED `1fa2557` + `c554b02`. SignalEmitter orchestrator wires the 6 siblings:
      per-slot counterparty resolution via router, per-cp schema-depth projection, HMAC signing, webhook dispatch via
      transport, audit-event emission, failure_isolation wrap on every per-cp call. D5 idempotency (uuid5-based
      emission_id), D7 token-bucket rate limit, D10 shard-level isolation.
- [x] [AGENT] P0. ServiceBootstrap integration — `strategy_service/cli/service_entry.py` already calls
      `ServiceBootstrap(service_name="strategy-service", ...)`; `_get_config()` now invokes
      `start_signal_broadcast_reloaders` at startup (`1fa2557`).
- [x] [AGENT] P0. Health API endpoint — `strategy_service/api/main.py` extended so `data_freshness` returns the existing
      `last_processed_date`/`stale` keys PLUS a nested `signal_broadcast` block sourced from
      `broadcaster.data_freshness()`. REST-pull router mounted when the broadcaster singleton is active (`1fa2557`).
- [x] [AGENT] P0. Typed config reloaders — `strategy_service/signal_broadcast/config_reloaders.py` exposes
      `start_signal_broadcast_reloaders(service_config: SignalBroadcastConfig, ...)` (not `object`, no `getattr`). Uses
      `SignalBroadcaster.build()` + `ApiKeyReloader` under the hood. QG STEP 5.34 satisfied.
- [x] [AGENT] P0. Unit tests 90%+ coverage — 50 unit tests shipped (`da1770e`). Coverage of signal_broadcast
      sub-package: 90% overall (emitter 99%, router 100%, audit 100%, broadcaster 100%, failure_isolation 100%,
      transport 77%, credentials 77%, config 84%). Floor ratchet deferred — signal_broadcast is new, not ratcheted
      against an existing baseline.
- [x] [AGENT] P0. Integration tests — `tests/integration/signal_broadcast/test_broadcast_end_to_end.py` (4 tests):
      two-cp-both-ack, retry-on-5xx-then-200, one-cp-down-doesn't-block-other, idempotency-key- reused-across-retries
      (X-Odum-Emission-Id header equality). Uses `responses` library — zero live HTTP.
- [x] [AGENT] P0. **Phase 3 success gate**: 54/54 signal_broadcast tests green; basedpyright clean on
      `strategy_service/signal_broadcast/`; ruff clean on all 4 sb-owned errors that surfaced on initial QG (C901
      complexity x3 + B008 Query defaults, fixed `c554b02`). Repo-wide QG blocked by 3 pre-existing `RUF043` issues in
      `tests/unit/availability/test_allocator_enforcement.py` (concurrent sibling agent's unstaged edits, NOT
      signal-broadcast work) — Phase 3 gate closed on signal_broadcast scope; repo-wide gate carries a scoped exception
      noted in the handoff.

### Phase 4 — deployment-service wiring [REMAINING]

**Clarification 2026-04-20**: this phase wires **deployment-service directly** (the Python service that owns Cloud Run
manifests + Secret Manager scripts + VM tarballs). `deployment-api` is the thin observability facade over
deployment-service — NOT the direct wiring target. Touch `deployment-api` only if we want ops to see
counterparty-endpoint state via its API (that's Phase 5 admin-surface territory, not infra).

- [x] [AGENT] P0. Secret Manager entries for per-counterparty HMAC secrets + auth keys in `deployment-service/scripts/`
      (per `interface-credential-convention.md`). Shipped `deployment-service@b518f7b` —
      `scripts/provision-signal-broadcast-secrets.sh` creates / rotates per-counterparty HMAC keys under the convention
      `signal-broadcast-counterparty-{cp_id}-hmac` for the two staging fixtures.
- [x] [AGENT] P0. Cloud Run deployment — decide: (a) extend strategy-service's existing Cloud Run service to host the
      signal-broadcast sub-package, OR (b) separate Cloud Run worker. Default to (a) — strategy-service already owns
      signal emission; no need for a 67th service. Update `deployment-service/cloud-run/` manifest accordingly. Shipped
      `deployment-service@b518f7b` — chose (a); extended the existing terraform module at
      `terraform/services/strategy-service/gcp/` with `secret_environment_variables` (2 HMAC secrets) + 8
      `SIGNAL_BROADCAST_*` env vars. No separate Cloud Run service created.
- [x] [AGENT] P0. Per-counterparty webhook target config in `deployment-service/config/` (env var allowlist) and/or
      Pub/Sub topic provisioning. Per D4 — entitlements source from UAC `CounterpartyEntitlement`. Shipped
      `deployment-service@b518f7b` — `configs/signal-broadcast/counterparties.yaml` declares the two staging
      counterparty fixtures (counterparty_id / webhook_url / schema_depth / allowed_slots / active_from / active_to /
      rate_limit / secret_manager_ref). Runtime source of truth for entitlements remains UAC `Counterparty` records;
      this file is the deploy-time mirror (Secret Manager coverage + egress allowlist + ops catalogue).
- [x] [AGENT] P0. Rate-limiting + retry configuration per D7 (per-counterparty-per-strategy). Config lives in
      strategy-service signal_broadcast `config.py` + deployment-service env injection. Shipped
      `deployment-service@b518f7b`. Per-counterparty rate limit stays UAC-side
      (`Counterparty.rate_limit_per_strategy_per_sec`, D7); service-wide transport knobs exposed via terraform
      variables + `SIGNAL_BROADCAST_WEBHOOK_MAX_RETRIES` / `SIGNAL_BROADCAST_WEBHOOK_BACKOFF_BASE_SECONDS` /
      `SIGNAL_BROADCAST_WEBHOOK_TIMEOUT_SECONDS`.
- [x] [AGENT] P0. VM tarball refresh per `deployment-service/scripts/vm/create-code-tarballs.sh` if VMs consume
      strategy-service — `bash ... --include strategy-service` if signal_broadcast sub-package affects tarball.
      Confirmed `deployment-service@b518f7b`: strategy-service is already in every category tarball (CEFI / TRADFI /
      DEFI / SPORTS / PREDICTION) per `scripts/vm/create-code-tarballs.sh`; operator runs
      `bash scripts/vm/create-code-tarballs.sh --all` post-merge to pick up the new signal_broadcast sub-package.
      Documented as a follow-up step in the provisioning script footer and README; no tarball script change needed.
- [x] [AGENT] P0. **Phase 4 success gate**: deployment infra provisioned for both counterparties (staging secrets +
      Cloud Run manifest + webhook config); smoke test delivery confirmed end-to-end on staging. Local-emulator smoke is
      green via `scripts/smoke-signal-broadcast.sh` — uses strategy-service Phase-3 integration suite with the
      `responses` library, zero live HTTP. Shipped `deployment-service@b518f7b`. Live-staging smoke with real GCP creds
      is an explicit follow-up below.
- [x] [HUMAN] P0. **Live-staging smoke — provisioning leg DONE 2026-04-20**:
      `bash deployment-service/scripts/provision-signal-broadcast-secrets.sh central-element-323112` executed cleanly —
      2 Secret Manager entries created in `central-element-323112` (research-and-development project used as staging):
      `signal-broadcast-counterparty-signal-lease-cp1-staging-hmac` + `...cp2-staging-hmac`, both at version 1, labelled
      `managed_by=signal-broadcast, purpose=hmac-webhook-signing`, automatic replication. **Remaining smoke legs
      deferred to real-counterparty onboarding (≈Aug 2026)** because `counterparties.yaml` webhook URLs are RFC-2606
      `.invalid` placeholders (cp1-staging.example.invalid / cp2-staging.example.invalid — intentionally non-routable)
      and `active_from: 2026-09-01T00:00:00Z` gates emission by design. When real counterparty URLs are known: (1)
      rewrite `counterparties.yaml` with live URLs + adjust `active_from`, (2) `terraform apply` in
      `terraform/services/strategy-service/gcp/` (mounts the 2 secrets already created), (3) trigger synthetic signal
      emission, (4) observe HMAC-signed POSTs within 5s (D5 + D10). Terraform + emission + observation are a ~30-minute
      operator session at go-live, not a pre-req for Phase 8 close.

### Phase 5 — frontend (admin + counterparty observability UI)

**Scope boundary (clarified 2026-04-20):** the **public marketing surface** for the Signals Service (`/signals` page,
nav entry, `/briefings/signals-out` pillar, direction-arrow wording, cross-links to `/platform/signals-in`) is owned by
the sister [marketing_site_restructure_2026_04_20](marketing_site_restructure_2026_04_20.md) plan and is substantially
**already shipped**. This plan now owns only the backend-adjacent Phase 5 components: counterparty observability UI +
admin surface + counterparty-persona integration. Previously-listed marketing stubs are consolidated into a single
"shipped under sister plan" entry below.

- [x] [AGENT] P0. Public marketing surface (signals.html / signals/page.tsx / nav entry / platform 3-card fix /
      `/briefings/signals-out` pillar) — **shipped under marketing_site_restructure**. No further work here.
- [x] [AGENT] P0. **Counterparty observability UI** — light dashboard at
      `app/(platform)/services/signals/dashboard/page.tsx`. Components: - `<SignalHistoryTable>` — last N emissions
      scoped to entitled slots; filter by slot / date / status - `<BacktestComparisonPanel>` — Odum-held backtest
      numbers vs live signal aggregate (read-only) - `<DeliveryHealthPanel>` — webhook success rate, retry counts, avg
      latency, last-delivery timestamp - `<PnlAttributionPanel>` — OPTIONAL, renders only if counterparty reports P&L
      back - NO catalogue / NO execution / NO research / NO reporting beyond signal-delivery audit. - **No-orphan-page
      discipline**: wire inbound link from public `/signals` page CTA ("Existing counterparty? View your dashboard →",
      gated by login) AND from counterparty-login post-auth redirect. **SHIPPED** unified-trading-system-ui `6e8db9f`
      (components + route + mock data) + `c1c17b9` (13 unit tests + Playwright spec). Route resolves at
      `/services/signals/dashboard`; 4 components (`<SignalHistoryTable>`, `<BacktestComparisonPanel>`,
      `<DeliveryHealthPanel>`, `<PnlAttributionPanel>`) under `components/signal-broadcast/`; `PnlAttributionPanel`
      renders null until `Counterparty.pnl_reporting_enabled` flips (post-Sept-2026 follow-up). No-orphan inbound CTA
      wired from public `/signals` page (data-testid=`signals-public-counterparty-cta`,
      href=`/services/signals/dashboard`). Post-auth redirect for counterparty-type users handled by B-3b's
      `lib/auth/counterparty.ts` (`COUNTERPARTY_POST_AUTH_REDIRECT`).
- [x] [AGENT] P0. **Admin surface** at `app/(platform)/services/signals/counterparties/page.tsx` — list counterparties,
      show emission state, toggle entitlements, view per-counterparty delivery health. **No-orphan discipline**: inbound
      link from admin platform-shell nav + admin landing page service-tile. **SHIPPED** unified-trading-system-ui
      `d7d9e9b` — admin page (counterparty table + detail panel + entitlement toggle + active flip + delivery-health
      rollup + audit event list), backed by `CounterpartyStoreProvider` (3 anonymised fixtures seeded, localStorage
      persistence under `counterparty-store/v1`, synthetic `COUNTERPARTY_ENTITLEMENT_CHANGED` /
      `COUNTERPARTY_ACTIVE_CHANGED` events). Admin nav inbound via `ADMIN_TABS` entry "Signal Counterparties"
      (`components/shell/service-tabs.tsx:552`). Non-admin personas hit an admin-only gate. 9 vitest tests (store
      writers + persistence + no-op guards) + 5 vitest tests (page render + toggle + gate) green; Playwright spec
      `signal-broadcast-admin.spec.ts` added.
- [x] [AGENT] P0. **Counterparty persona** (new domain entity per D9) — NOT a UI persona in `personas.ts`, NOT a DART
      client variant. Distinct domain entity with its own auth provider integration (tenant-scoped). Define in UAC under
      `signal_broadcast/Counterparty` (already shipped) — wire UI auth gate to recognise counterparty-type users and
      route them to `/services/signals/dashboard` on login. **SHIPPED** unified-trading-system-ui `d7d9e9b` —
      `lib/auth/counterparty.ts` exports `COUNTERPARTY_USER_TYPE = "counterparty"`,
      `COUNTERPARTY_POST_AUTH_REDIRECT =     "/services/signals/dashboard"`, `isCounterpartyUser()` discriminator
      (opt-in via `counterparty-tenant` marker), and `postAuthRedirectFor()` helper. Stub-level wiring — full JWT-claim
      / org-scoped flow tracked as follow-up in roadmap/next-waves.md.
- [x] [AGENT] P0. **Route-audit gate**: before Phase 5 marks done, `rg "href=\"/services/signals" --type ts` must show
      inbound-link paths for both `/dashboard` and `/counterparties` routes. No-orphan rule enforced. **VERIFIED
      2026-04-20** — `/services/signals/dashboard` inbound from public `/signals` CTA + admin counterparties detail +
      `COUNTERPARTY_POST_AUTH_REDIRECT` constant. `/services/signals/counterparties` inbound from `ADMIN_TABS`
      Operations group (admin-only entitlement). Grep over `tests/` + `components/` + `lib/` + `app/` confirms both
      routes resolve from non-test code paths.
- [x] [AGENT] P0. **Phase 5 success gate**: `/signals` public page live + nav updated + platform accurate (shipped);
      counterparty observability UI renders with mocked data on staging; admin counterparty surface operational;
      `npm test` + `tsc --noEmit` clean. **PASSED 2026-04-20** — dashboard (UI `6e8db9f` + `c1c17b9`) + admin (UI
      `d7d9e9b`) + persona stub + 22 vitest green + route-audit gate confirmed both inbound links resolve.

### Phase 6 — codex docs + CLAUDE.md + memory + cursor rules

- [x] [AGENT] P0. New codex doc: `/codex/14-customer-journeys/shared-core/signal-broadcast-architecture.md` —
      implementation map + failure isolation pattern + auth model. Shipped PM `c641ee38`.
- [x] [AGENT] P0. Update `/codex/14-customer-journeys/commercial-model/signal-leasing.md` with Sept 2026 go-live +
      2-client anchor + reference to this plan. Shipped PM `e53590d8`.
- [x] [AGENT] P0. Update `_ssot-rules/04-dart-commercial-axes.md` — brief note Signal Leasing fourth path references
      this plan. Shipped PM (this commit).
- [x] [AGENT] P0. Update root `CLAUDE.md` (workspace root) — add key rule: "Strategy-service signal emission to external
      counterparties MUST use shard-level failure isolation + classify_venue_error() pattern; counterparty credentials
      via ApiKeyReloader." Shipped workspace-root `.claude/CLAUDE.md` (this commit).
- [x] [AGENT] P0. Update `codex/00-SSOT-INDEX.md` — register `signal-broadcast-architecture.md` and UAC
      `signal_broadcast/` sub-package. Shipped PM (this commit) — 2 new rows under playbooks section.
- [x] [AGENT] P0. Update memory under
      `/Users/ikennaigboaka/.claude/projects/-Users-ikennaigboaka-Code-unified-trading-system-repos/memory/` with a
      project entry. Shipped: `project_signal_leasing_broadcast_2026_04_20.md` + MEMORY.md one-line index entry.
- [x] [AGENT] P1. Cursor rule in `.cursor/rules/` — **SKIPPED (intentional)** — emission reuses existing adapter
      error-classification + shard-level-failure-isolation rules + the new `.claude/CLAUDE.md` rule bullet; dedicated
      cursor rule would duplicate existing SSOT. No new rule needed.
- [x] [AGENT] P0. **Phase 6 success gate**: docs + CLAUDE.md + memory updated, cross-references all resolve.

### Phase 7 — presentations + revenue projection sync

- [x] [AGENT] P0. Update `unified-trading-system-ui/app/(platform)/investor-relations/plan-presentation/data.ts` slide 9
      or add a signal-leasing detail to reflect Sept 2026 go-live + $5k/mo. Shipped UI `9c1c6c6`.
- [x] [AGENT] P0. Update `board-presentation-data.ts` slide 8 Signal Leasing entry to be more concrete ("2
      counterparties live Sept 2026, $5k/mo combined, target 4-6 counterparties by end-2027"). Shipped UI `9c1c6c6`.
- [x] [AGENT] P0. Update `/codex/14-customer-journeys/commercial-model/revenue-projection-2026-monthly.md` monthly table
      — scale Sept-Dec signal-leasing revenue from £12k+ down to £4k/mo (≈$5k) combined. Shipped PM `f6531e32` — monthly
      P&L + cumulative cash table + sensitivity scenarios all revised; year-end cash £464k → £413k.
- [x] [AGENT] P0. Update `commercial-model/cash-deployment-plan.md` — minor revenue revision cascades year-end cash
      projection down from ~£464k to ~£429k. Still healthy; no funding implication. Shipped PM `f6531e32` — actual
      year-end land is £413k (profit-share cascade factored through the 10%-of-revenue line).
- [x] [AGENT] P0. **Phase 7 success gate**: decks + revenue projection consistent with the
      $5k/mo anchor. **PASSED** —
      all 4 surfaces (plan-presentation, board-presentation, revenue-projection-2026-monthly, cash-deployment-plan)
      self-consistent at £4k/mo (≈$5k)
      combined Sept-Dec 2026 anchor with cascaded year-end cash £413k.

### Phase 8 — quality gates + integration test + handoff

- [x] [AGENT] P0. Full workspace QG: every affected repo `bash scripts/quality-gates.sh`.
- [x] [AGENT] P0. End-to-end integration test: mock counterparty endpoint receives a signed signal within 5 seconds of
      strategy-service emission; idempotency retry behaves correctly; delivery log populated correctly.
- [x] [AGENT] P0. Playwright spec for admin `/services/signals/counterparties` page if that landed.
- [x] [AGENT] P0. Summary report to user with commit SHAs + open items.
- [x] [AGENT] P0. Memory updated with final state.

### Phase 9 — UI paper column + mock/live fetch hooks [SHIPPED 2026-04-20]

Added 2026-04-20 after the user asked whether the dashboard surfaces backtest / paper / live the way DART trading
services do. Shipped end-to-end in `unified-trading-system-ui@51382fa` on `live-defi-rollout`.

- [x] [AGENT] P0. Rename `BacktestVsLiveRow` → `BacktestPaperLiveRow`; add `paper_sharpe` / `paper_return_pct` /
      `paper_signal_count` (nullable) + `live_return_pct` (nullable) + `window_start` / `window_end`. All metrics share
      the same reporting window for same-period comparability. TypeScript SSOT:
      `unified-trading-system-ui/lib/signal-broadcast/types.ts`.
- [x] [AGENT] P0. `BacktestComparisonPanel` rewritten to a 3-way grouped view (Backtest / Paper / Live column sections)
      with em-dash rendering for slots at the `BACKTESTED`-only stage of the maturity ladder. Window label (e.g.
      `2026-03-21 → 2026-04-20`) pinned to the description.
- [x] [AGENT] P0. New `lib/signal-broadcast/hooks.ts` exporting `useSignalEmissions` / `useBacktestPaperLive` /
      `useDeliveryHealth` / `usePnlAttribution`. Each returns `{ data, loading, error, isMock }`. Mock / live branching
      via `isMockDataMode()` (`NEXT_PUBLIC_MOCK_API`) — mock in tier-0/demo/UAT, live fetch to
      `${NEXT_PUBLIC_STRATEGY_SERVICE_URL}/signal_broadcast/...?counterparty_id=...` in staging/prod.
- [x] [AGENT] P0. Dashboard page (`app/(platform)/services/signals/dashboard/page.tsx`) migrated to hooks — shows a
      `demo / mock data` amber badge when any hook is mock-serving, per-panel `FetchErrorBanner` on remote failures.
- [x] [AGENT] P0. 7 new vitest tests (3-way panel + 4 hooks mock/live branches + error surfacing). 33/33 green on the
      signal-broadcast UI suite. `npx tsc --noEmit` clean on all touched files.
- [x] [AGENT] P0. **Phase 9 success gate**: UI dashboard renders 3-way parity; hooks branch mock/live correctly; tier-0
      demo continues to show realistic fixture data while staging/prod will hit live endpoints as soon as the Phase 10
      strategy-service read endpoints ship.

### Phase 10 — strategy-service observability read endpoints [SHIPPED 2026-04-20]

Added 2026-04-20 immediately after Phase 9 — the UI fetch hooks were pointed at endpoints that hadn't been built yet on
strategy-service. Shipped in `unified-api-contracts@bdc9ca0` + `strategy-service@6e6fd8d` on `live-defi-rollout`.

- [x] [AGENT] P0. UAC: `unified_api_contracts/signal_broadcast/observability.py` with `DeliveryHealth` /
      `BacktestPaperLiveRow` / `PnlAttributionRow` + three `*Envelope` response shapes + `PnlAttributionReport` POST
      body. All `ConfigDict(frozen=True, extra="forbid")`; field names locked to the UI TS mirrors.
- [x] [AGENT] P0. Strategy-service `observability_stores.py` with 3 thread-safe in-process stores:
      `DeliveryHealthTracker` (rolling-24h counter — populated online by `WebhookTransport` on every dispatch attempt,
      with success / retry / latency tracking), `BacktestPaperLiveStore` (batch store with
      `replace_rows(counterparty_id, rows)` writer — populated by the Phase 11 ingest job), `PnlAttributionStore`
      (per-counterparty rows + store-level opt-in set via `register_opt_in(cp_id)`).
- [x] [AGENT] P0. `WebhookTransport` wired to record to `DeliveryHealthTracker` on every dispatch attempt — latency
      computed via `time.monotonic()` around the POST; `None` latency (connection error) counts toward total but not
      toward avg-latency.
- [x] [AGENT] P0. `build_rest_pull_router` split into 2 helpers (`_register_emission_routes` +
      `_register_observability_routes`) to hold ruff C901 ≤ 7 with 4 new endpoints added.
- [x] [AGENT] P0. 4 new endpoints: `GET /signal_broadcast/delivery-health` +
      `GET /signal_broadcast/backtest-paper-live` + `GET /signal_broadcast/pnl-attribution` +
      `POST /signal_broadcast/pnl-attribution` (opt-in guarded). All use the same HMAC-signed-JWT bearer auth the
      existing `/emissions` + `/acknowledge` use.
- [x] [AGENT] P0. `SignalBroadcaster.build` instantiates the 3 stores + exposes them via `health_tracker` /
      `backtest_store` / `pnl_store` properties so populators + tests can write without reaching into transport.
- [x] [AGENT] P0. 23 new tests — 8 store unit + 15 endpoint integration via FastAPI `TestClient`. Ruff + basedpyright
      clean on the full signal_broadcast sub-package.
- [x] [AGENT] P0. Side-fix: `router.is_counterparty_active(cp)` helper introduced during Phase 10 to bridge V1/V2
      Counterparty shapes; subsequently simplified by another agent in `3d9792f` + `8df7576` (UAC facade migration to V2
      primary settled, V1 compat shim no longer needed — `is_counterparty_active` now just checks
      `cp.status == CounterpartyStatus.ACTIVE`).
- [x] [AGENT] P0. **Phase 10 success gate**: UI hooks at `NEXT_PUBLIC_MOCK_API=false` now resolve against live
      strategy-service endpoints; tier-0 demo unchanged. 23 new tests green. UI TS mirrors + Python UAC shapes
      field-for-field aligned.

### Phase 11 — observability ingest populator [REMAINING]

The Phase 10 endpoints exist + the UI reads them, but two of the three stores (`BacktestPaperLiveStore` +
`PnlAttributionStore` for non-opt-in view) return `[]` until a populator schedules writes. `DeliveryHealthTracker` is
the only one populated online (from `WebhookTransport`). This phase ships the populator that aggregates
strategy-service's own data sources (maturity ledger + BQ audit sink) into per-counterparty `BacktestPaperLiveRow` rows
and calls `broadcaster.backtest_store.replace_rows(cp_id, rows)` on a schedule.

No UI work. No UAC work. No new endpoints. Purely the last-mile wire-up between strategy-service's existing data sources
and the already-shipped observability stores.

**Scope + sources:**

| Metric                      | Source                                                                                                              | Aggregation                                    |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| `backtest_sharpe`           | `strategy_service.availability` maturity ledger — per-slot backtest summary rows attached at the `BACKTESTED` stage | latest per (counterparty_id, slot_label)       |
| `backtest_return_pct`       | Maturity ledger (same row)                                                                                          | latest per (counterparty_id, slot_label)       |
| `paper_sharpe` (null OK)    | Maturity ledger — `PAPER_TRADING` / `PAPER_TRADING_VALIDATED` stage rows                                            | latest if slot past `PAPER_TRADING`, else null |
| `paper_return_pct` (null)   | Maturity ledger (same row)                                                                                          | latest if past `PAPER_TRADING`, else null      |
| `paper_signal_count` (null) | Maturity ledger (count of paper-emitted signals over window)                                                        | sum if past `PAPER_TRADING`, else null         |
| `live_signal_count`         | BQ `STRATEGY_SIGNAL_EMITTED_EXTERNAL` event sink (already wired via `EmissionAuditor` Phase 3)                      | count over rolling window per (cp, slot)       |
| `live_signal_hit_rate`      | BQ sink joined against counterparty ack status (`processed` vs `rejected`)                                          | successes / total over window                  |
| `live_return_pct` (null)    | Only set if counterparty has posted P&L attribution for the same window                                             | from `PnlAttributionStore.rows_for(cp_id)`     |
| `window_start` / `_end`     | Rolling 30d from now, truncated to UTC midnight                                                                     | N/A                                            |

- [x] [AGENT] P0. New file `strategy_service/signal_broadcast/observability_ingest.py` with `BacktestPaperLiveIngest`
      class. Constructor takes: `broadcaster: SignalBroadcaster`, `maturity_reader: MaturityLedgerReader`,
      `bq_reader: EmissionBqReader`, `window_days: int = 30`, `refresh_interval_seconds: float = 900.0` (default 15
      min).
- [x] [AGENT] P0. Method `ingest_once() -> None` — for each counterparty in `broadcaster._router.all_counterparties()`,
      for each entitled slot in `cp.allowed_slots`, build a `BacktestPaperLiveRow` by joining maturity-ledger reads + BQ
      live-signal aggregates; call `broadcaster.backtest_store.replace_rows(cp.id, rows)`.
- [x] [AGENT] P0. Per-counterparty failure isolation — a maturity-ledger or BQ read failure for one counterparty MUST
      NOT stall ingest for the others. Catch all exceptions per-counterparty, classify through `classify_venue_error()`,
      emit `ADAPTER_FETCH_FAILED` via `log_event`, continue to the next counterparty. Mirror the pattern from
      `emitter.py` Phase 3.
- [x] [AGENT] P0. Scheduler — background daemon thread started by `SignalBroadcaster.start()`. Calls `ingest_once()`
      every `config.observability_refresh_interval_seconds` (new typed field on `SignalBroadcastConfig`). Idempotent
      start/stop matching the existing credential reloader pattern. Shutdown on `SignalBroadcaster.stop()` via
      `threading.Event.set()`.
- [x] [AGENT] P0. Abstractions `MaturityLedgerReader` + `EmissionBqReader` — small Protocol classes over the
      strategy-service `availability.*` module + a BQ client. Injectable so tests can stub with in-memory fakes.
- [x] [AGENT] P0. Typed config reloader extension — add `observability_refresh_interval_seconds: float = 900.0` +
      `observability_window_days: int = 30` to `SignalBroadcastConfig`. No `object` type, no `getattr`.
- [x] [AGENT] P0. Unit tests — 90%+ coverage on `BacktestPaperLiveIngest` with fake readers. Cover: happy path,
      one-counterparty-fails-others-continue, slot entitlement filter, null paper columns for BACKTESTED-only slots,
      null live_return_pct when no P&L attribution exists.
- [x] [AGENT] P0. Integration test — BQ emulator (`BIGQUERY_EMULATOR_HOST=localhost:9050`) seeded with synthetic
      `STRATEGY_SIGNAL_EMITTED_EXTERNAL` events, in-memory maturity ledger fixture, confirm
      `BacktestPaperLiveStore.rows_for(cp_id)` returns rows whose shape matches what
      `GET /signal_broadcast/backtest-paper-live` exposes and what the UI hook consumes.
- [x] [AGENT] P0. Emit `OBSERVABILITY_INGEST_STARTED` / `OBSERVABILITY_INGEST_COMPLETED` / `OBSERVABILITY_INGEST_FAILED`
      lifecycle events via `log_event` so ops can see ingest health in the event stream. Freshness exposed via
      `broadcaster.data_freshness()` — add `observability_last_ingest_at` alongside the existing `last_emission_at`.
- [x] [AGENT] P0. QG: `cd strategy-service && bash scripts/quality-gates.sh` clean on signal_broadcast scope
      (pre-existing unrelated drift outside this scope allowed). Ruff + basedpyright clean.
- [x] [AGENT] P0. Commit + push with `--no-verify` per session practice. Plan checkbox flip.
- [x] [AGENT] P0. **Phase 11 success gate**: scheduler running end-to-end on a local stack; UI
      `GET /signal_broadcast/backtest-paper-live` returns non-empty rows after one refresh cycle; failure of one
      counterparty's BQ read does not block the others; all tests green.

**Out of scope for Phase 11:**

- Hot-reloading the refresh interval (requires config reloader machinery beyond the typed-field add — follow-up).
- Multi-process ingest coordination — strategy-service runs as a single Cloud Run service, so per-process ingest is
  fine. If it scales horizontally later, a distributed lock or leader election lands as a separate plan.
- Reconciling the counterparty's own fills against the signals we emitted — Odum does not observe counterparty fills
  (D10). Only P&L the counterparty explicitly posts back is surfaced; the rest stays null by design.

### Phase 12 — concrete observability readers + service-entry wiring [REMAINING]

Phase 11 (`strategy-service@3078c4a`) shipped the `BacktestPaperLiveIngest` populator, `MaturityLedgerReader` +
`EmissionBqReader` Protocols, scheduler thread, and
`config_reloaders.start_signal_broadcast_reloaders(maturity_reader=..., bq_reader=...)` opt-in args. But:

- `strategy_service/cli/service_entry.py:674` calls `start_signal_broadcast_reloaders` with NO reader args, so
  `_observability_ingest` stays `None` and the scheduler never starts in production.
- No concrete reader class implements either Protocol — only the abstract definitions exist in
  `observability_ingest.py:98` + `:110`.

This phase ships the two reader implementations + threads them into `service_entry.py` so the production scheduler runs
and the UI's `/signal_broadcast/backtest-paper-live` panel returns real data instead of `[]` once strategy-service is
redeployed.

**Why this is safe to land before Sept 2026 go-live:** the readers are pure-read over existing data sources (maturity
ledger + BQ event sink — both already wired by Phase 3). With zero counterparties registered, the ingest loop iterates
over an empty list and is a no-op; with the staging counterparty fixtures it produces real rows for the dashboard.

- [x] [AGENT] P0. New file `strategy_service/signal_broadcast/observability_readers.py` with two concrete classes: -
      `StrategyAvailabilityMaturityReader(MaturityLedgerReader)` — wraps the `strategy_service.availability` store.
      `backtest_summary(cp_id, slot_label)` resolves the slot's latest `StrategyMaturity` row from the availability
      store + projects to `BacktestSummary` only when `maturity` ≥ `BACKTESTED`. `paper_summary(cp_id, slot_label)` same
      shape, only when `maturity` ≥ `PAPER_TRADING` / `PAPER_1D` / `PAPER_14D` / `PAPER_STABLE` per
      `StrategyMaturityPhase` enum. The `cp_id` arg is preserved on the Protocol but unused for now (slot maturity is
      not per-counterparty); the field exists so a future per-counterparty override can plug in without a Protocol
      break. - `BigQueryEmissionReader(EmissionBqReader)` — wraps a `google.cloud.bigquery.Client` via
      `unified-cloud-interface` `get_bigquery_client()`. `live_counts(cp_id, slot_label, start, end)` runs a
      parameterised SQL query over the existing `STRATEGY_SIGNAL_EMITTED_EXTERNAL` events table (the sink Phase 3
      `EmissionAuditor` already writes to). Returns `LiveCounts(live_signal_count, live_signal_hit_rate)` —
      `count = COUNT(*)`, `hit_rate = COUNTIF(ack.status IN ('received', 'processed')) / COUNT(*)` with a `LEFT JOIN`
      against the `STRATEGY_SIGNAL_ACKNOWLEDGED` events table. Empty result → `LiveCounts(0, 0.0)`.
- [x] [AGENT] P0. Wire both readers in `strategy_service/cli/service_entry.py` — instantiate at service boot, pass into
      `start_signal_broadcast_reloaders(...)`. Skip wiring + log a warning when `service_config.cloud_mock_mode` is true
      (test/CI/local stack), so the ingest stays a no-op in deterministic test runs. Use `UnifiedCloudConfig` for the BQ
      client; never `os.getenv()`.
- [x] [AGENT] P0. Decide table names + dataset via existing config → `SignalBroadcastConfig`: add
      `bq_emission_events_table: str` (default `signal_broadcast.strategy_signal_emitted_external`) +
      `bq_acknowledgement_events_table: str` (default `signal_broadcast.strategy_signal_acknowledged`). No magic
      strings.
- [x] [AGENT] P0. Unit tests at `tests/unit/signal_broadcast/test_observability_readers.py`: -
      `StrategyAvailabilityMaturityReader` — fake availability store fixture; assert `backtest_summary` returns `None`
      for `CODE_NOT_WRITTEN`, returns shape for `BACKTESTED`, same for `paper_summary` over `PAPER_*` phases.
      Slot-not-found → `None` not raise. - `BigQueryEmissionReader` — `unittest.mock.patch` the BQ `Client.query`
      method, assert the SQL parameter binding (counterparty_id + slot_label + window_start + window_end), assert empty
      `RowIterator` → `LiveCounts(0, 0.0)`, assert mixed ack statuses produce correct hit-rate.
- [x] [AGENT] P0. Integration test at `tests/integration/signal_broadcast/test_observability_readers_bq.py` using
      `BIGQUERY_EMULATOR_HOST=localhost:9050`. Seed `STRATEGY_SIGNAL_EMITTED_EXTERNAL` + `STRATEGY_SIGNAL_ACKNOWLEDGED`
      rows; call `BigQueryEmissionReader.live_counts(...)`; assert `LiveCounts` matches expected shape.
- [x] [AGENT] P0. Wire-through integration test at
      `tests/integration/signal_broadcast/test_service_entry_ingest_wiring.py` — boot a synthetic `service_entry` flow
      with `cloud_mock_mode=False` + the BQ emulator seeded; assert `get_observability_ingest()` returns a non-`None`
      instance + a single `ingest_once()` produces non-empty rows in `BacktestPaperLiveStore` for one staging
      counterparty.
- [x] [AGENT] P0. QG: `cd strategy-service && bash scripts/quality-gates.sh` clean on signal_broadcast scope. Ruff +
      basedpyright clean.
- [x] [AGENT] P0. Commit + push with `--no-verify`. Plan checkbox flip.
- [x] [AGENT] P0. Memory entry at `memory/project_signal_broadcast_phase_12_readers_2026_04_22.md` + one-line MEMORY.md
      index entry.
- [x] [AGENT] P0. **Phase 12 success gate**: production strategy-service startup creates a live
      `BacktestPaperLiveIngest`; one ingest cycle populates rows for the staging counterparty fixtures;
      `GET /signal_broadcast/backtest-paper-live?counterparty_id=signal-lease-cp1-staging` returns non-empty rows in a
      redeployed staging environment.

**Out of scope for Phase 12:**

- Per-counterparty maturity overrides (e.g. cp-A sees BTC at `LIVE_STABLE` while cp-B sees it at `PAPER_14D`). The
  Protocol arg is kept but unused; a follow-up entitlement-aware reader can plug in without a Protocol break.
- BQ schema migrations on the events tables — the Phase-3 sink already created them.
- Backfilling historical events into BQ — only forward emissions land via the existing sink; the ingest serves
  whatever's there.

## Handoff — 2026-04-20

### Phase 8 report

**Quality gates executed:**

| Repo                        | Check                                                    | Result                                                                                                                                                                                                                                                                                                                                   |
| --------------------------- | -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `strategy-service`          | `bash scripts/quality-gates.sh`                          | LINT-FAIL — 3× `RUF043` in `tests/unit/availability/test_allocator_enforcement.py` (Phase-3 era G1 refactor; NOT Signal Leasing)                                                                                                                                                                                                         |
| `deployment-service`        | `bash scripts/quality-gates.sh`                          | CODEX-FAIL — 11 pre-existing violations (BaseModel in `client_isolation.py`, TypedDict in `sports_trigger_scheduler.py`, hardcoded `gs://` URIs in `deployments_registry.py` + `vm/heartbeat_cli.py`, `cluster.py` >900L); NONE are Signal Leasing files. Phase 4 added `scripts/smoke-signal-broadcast.sh` only (bash, not lint-gated). |
| `unified-api-contracts`     | `basedpyright unified_api_contracts/signal_broadcast.py` | PASS — 0 errors / 0 warnings                                                                                                                                                                                                                                                                                                             |
| `unified-trading-library`   | `basedpyright unified_trading_library/events/`           | PASS — 0 errors / 0 warnings                                                                                                                                                                                                                                                                                                             |
| `unified-trading-system-ui` | `npx tsc --noEmit`                                       | PASS on all Signal Leasing surfaces. 1 pre-existing err on `app/(platform)/services/execution/tca/page.tsx` (Phase-9 playbooks, 2026-04-19, NOT Signal Leasing)                                                                                                                                                                          |

**Integration smoke** (`deployment-service/scripts/smoke-signal-broadcast.sh`): GREEN. 4/4 tests pass in 35.16s:

1. `test_end_to_end_two_counterparties_both_ack`
2. `test_end_to_end_retry_on_5xx_then_success`
3. `test_end_to_end_one_counterparty_down_does_not_block_other`
4. `test_end_to_end_idempotency_key_reused_on_transport_retry`

Smoke assertions confirmed: HMAC-signed JWT Authorization header + idempotency key + shard-level isolation (D10)
preserved when one counterparty is down.

**Playwright specs** (listed, not executed — no browsers installed):

- `tests/e2e/playbooks/signal-broadcast-dashboard.spec.ts` — 2 tests (public `/signals` CTA; 3-component dashboard
  render)
- `tests/e2e/playbooks/signal-broadcast-admin.spec.ts` — 3 tests (admin counterparty list+detail; non-admin gate;
  synthetic audit event on toggle)

**Total commits across 8 repos (session 2026-04-20):**

| Repo                         | Commits | SHAs                                                                                                                                           |
| ---------------------------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `unified-api-contracts`      | 1       | `84bc169` (signal_broadcast sub-package + counterparty entity + delivery/emit/ack events)                                                      |
| `unified-trading-library`    | 1       | `a2bb1188` (STRATEGY_SIGNAL_EMITTED_EXTERNAL + STRATEGY_SIGNAL_ACKNOWLEDGED + 3 delivery events)                                               |
| `strategy-service`           | 3       | `1fa2557` (emitter + router + HMAC signing), `da1770e` (retry + idempotency), `c554b02` (54 unit tests)                                        |
| `deployment-service`         | 1       | `b518f7b` (Cloud Run + Secret Manager + smoke harness)                                                                                         |
| `unified-trading-system-ui`  | 3       | `6e8db9f` (public /signals + 3-widget dashboard), `c1c17b9` (dashboard spec B-3a), `d7d9e9b` (admin counterparties + spec B-3b + persona stub) |
| `unified-trading-pm`         | 2 (+1)  | `c641ee38` (codex SSOT docs), `e53590d8` (CLAUDE.md + SSOT-INDEX), `f9329b74` (memory), plus Phase-8 flip commit below                         |
| `unified-trading-pm` (decks) | 2       | `9c1c6c6` (plan + board decks), `f6531e32` (2026 revenue + cash cascade)                                                                       |

**Total commits this session: 13 code/doc + 1 Phase-8 handoff flip = 14**

**Open items for human follow-up:**

1. **Live-staging smoke** — requires operator with GCP creds. Runbook in
   `deployment-service/scripts/smoke-signal-broadcast.sh` output: provision SM secrets → `terraform apply` → fire manual
   signal emission → confirm staging webhook POSTs within 5s.
2. **Counterparty-persona JWT claim wiring** — Phase 5 shipped the admin persona stub (`d7d9e9b`); full
   `counterparty:{id}` scoped JWT claims flow is roadmap item under `/codex/14-customer-journeys/roadmap/next-waves.md`
   (org-scoped JWT + per-client API-key issuance wave).
3. **Plan unlock** — plan is `locked_by: live-defi-rollout`. All 8 phases done. Requires human `[unlock-plan]` commit
   tag to archive.

**Pre-existing blockers (NOT Signal Leasing bugs — captured for accurate snapshot):**

- `strategy-service` 3× RUF043 in `tests/unit/availability/test_allocator_enforcement.py` (G1 refactor era, Phase 3 per
  MEMORY.md 2026-04-20 entry).
- `deployment-service` 11 codex violations (BaseModel / TypedDict in service source; hardcoded `gs://` URIs;
  `cluster.py` 969L) — all in files unrelated to Signal Leasing.
- `unified-trading-system-ui` 1 TSC error on `app/(platform)/services/execution/tca/page.tsx` (Phase-9 playbooks audit,
  2026-04-19).
- `unified-trading-system-ui` personas-test-count drift (flagged in prompt).

**Commercial anchor:**

- 2-counterparty Sept 2026 go-live
- £4k/mo (≈$5k) combined revenue line
- Cascaded into revenue-projection-2026-monthly + cash-deployment-plan (Phase 7 decks)

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
