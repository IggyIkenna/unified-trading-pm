---
doc_type: codex-ssot
title: Service emission policy (Architecture View)
summary:
  Architecture seam of the service emission policy — how UAC policy-declaration, UTL publish_with_policy, the UAC
  next_state resolver, and the 3 v8 manifest columns compose one-direction-per-arrow with no circular imports.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-api]
scope: [engineer, admin]
tags: [manifest, uac, data-status, honest-coverage, observability]
related:
  [
    /codex/02-data/service-output-emission-semantics.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-05-11
authoritative_for:
  [
    service emission policy four-piece architecture seam (UAC-declaration/UTL-publisher/UAC-resolver/v8-manifest-column
    composition),
  ]
referenced_by: [plans/audit/results/run_lifecycle_events_audit_2026_05_05.md]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Service emission policy (Architecture View)

> **What it is:** The architectural seam between a service's publish boundary and the v8 manifest column that records
> what was published. Companion to
> [`/codex/02-data/service-output-emission-semantics.md`](/codex/02-data/service-output-emission-semantics.md) (which
> covers the runtime/data-side perspective). This doc covers the _architectural_ seam — how the policy SSOT, the
> publish-boundary helper, the resolver, and the manifest column compose to give downstream consumers a single read
> surface for "what was published, and how complete was it."
>
> **Why this doc exists separately from `02-data/`.** The 02-data doc is the runtime/operator-facing SSOT: which kwargs
> to pass to `publish_with_policy()`, which lifecycle event the publisher emits, how to wire a new service. THIS doc is
> the architecture-facing SSOT: how the four moving pieces (UAC declaration / UTL publisher / UAC resolver / v8 manifest
> column) compose without circular imports, what the layer-discipline guarantees are, and where the seams sit for future
> extension. Read 02-data first for "how do I use it"; read THIS doc for "why is it shaped this way."

> **STATUS** (2026-05-11): The four pieces are SHIPPED:
>
> - **UAC declaration** of policy SSOT —
>   `unified_api_contracts.canonical.crosscutting.service_emission_policy.SERVICE_OUTPUT_POLICIES` (slice (a),
>   UAC@`58c3b61`).
> - **UTL publisher** — `unified_trading_library.emission_publisher.publish_with_policy()` (slice (a), UTL@`1a7e1d4b`)
>   - `publish_with_manifest_lookup()` (slice (b), UTL@`ac5ade59`).
> - **UAC resolver** — `service_emission_policy.next_state(*, policy, event)` (Phase 1.B, UAC@`174f401`).
> - **UAC manifest column declaration** — `service_emission_state.ServiceEmissionStateEnum` +
>   `manifest_schema.V8_NEW_COLUMNS` (Phase 1.A + 1.C, UAC@`174f401` + rename @UAC@`76f950a`).
>
> Slice (c) Phase 6.1-6.9 (per-service rollout) is multi-week + tracked by
> [`plans/active/writegate_honest_coverage_endtoend_2026_05_06.md`](../../plans/active/writegate_honest_coverage_endtoend_2026_05_06.md).
> v8 manifest column wiring (UTL `ManifestWriter` extension + Phase 4 workspace consumer sweep) is tracked by
> [`plans/active/manifest_schema_final_gate_2026_05_09.md`](../../plans/active/manifest_schema_final_gate_2026_05_09.md)
> Phase 2 + 4.

## The four pieces

```
                ┌───────────────────────────────────────────────────┐
1. POLICY SSOT  │ UAC SERVICE_OUTPUT_POLICIES dict                  │
   (declaration)│   keyed by (service, output_data_type)             │
                │   → ServiceEmissionPolicy ∈ { STRICT_FAIL /        │
                │     PARTIAL_OK / NAN_FILL / BLOCK_CRITICAL }       │
                └───────────────────────────────┬───────────────────┘
                                                │
                ┌───────────────────────────────▼───────────────────┐
2. PUBLISHER    │ UTL publish_with_policy(service, output_data_type,│
   (runtime)    │ completeness_fraction, ...) → EmissionDecision    │
                │   → emits EmissionLifecycleEvent ∈ {              │
                │     PUBLISHED_OK / PUBLISHED_DEGRADED /            │
                │     STALE_DATA / BLOCKED }                         │
                └───────────────────────────────┬───────────────────┘
                                                │
                ┌───────────────────────────────▼───────────────────┐
3. RESOLVER     │ UAC service_emission_policy.next_state(*, policy, │
   (pure fn)    │ event) → ServiceEmissionStateEnum ∈ {              │
                │   PUBLISHED_OK / PUBLISHED_DEGRADED /              │
                │   STALE_DATA_HEARTBEAT_ONLY / BLOCKED }            │
                └───────────────────────────────┬───────────────────┘
                                                │
                ┌───────────────────────────────▼───────────────────┐
4. MANIFEST     │ UAC manifest_schema declares 3 v8 columns:        │
   COLUMN       │   service_emission_state (str | None)             │
   (persistent) │   last_emission_decision_at (ISO-8601 str | None) │
                │   expected_window_completeness_fraction (float)   │
                │ Writer: UTL ManifestWriter.record_captured(...)    │
                │ Reader: deployment-api /leaf-stats endpoint;       │
                │   downstream consumers per consumer-class audit.   │
                └───────────────────────────────────────────────────┘
```

The seam discipline is **one direction per arrow** — no circular dependency. UAC has zero runtime imports of UTL. UTL
imports UAC. The runtime path is `publisher → resolver → ManifestWriter`; the read path is
`ManifestReader → ServiceEmissionStateEnum (interpret)`.

## Architectural invariants

1. **Closed-set states + closed-set events + closed-set policies.** All three enums are frozen 2026-05-09 → 2026-05-23
   per `manifest_schema_final_gate_2026_05_09.md` § "UAC enums frozen for the window". Any proposal to add a value
   during the window is rejected; defer to post-cutover.
2. **The publisher emits ONE event per publish cycle.** The publisher is the only place lifecycle events get emitted —
   bypass routes (services that hand-emit `PUBLISHED_OK`) are banned. Reviewers reject any non-publisher `log_event`
   call that names a lifecycle-event string.
3. **The resolver is a pure function.** `next_state(*, policy, event) → state` is keyword-only, no I/O, no side effects.
   The `policy` arg is currently advisory (state derives from `event` under slice (b) spec); kept in signature for
   forward-compat with future policy-specific state nuances.
4. **The manifest column is `str | None`, not `ServiceEmissionStateEnum`.** Parquet round-trip safety — the column
   stores the `.value` of the enum (e.g. `"PUBLISHED_OK"`). Readers coerce via `ServiceEmissionStateEnum(row_value)`;
   `None` means "pre-v8 row, fall through to `capture_status`-based reasoning." The closed-set guarantee fires at the
   writer boundary (`SERVICE_EMISSION_STATES` frozenset membership check).
5. **The manifest column rename is FROZEN at `_fraction`** (UAC@`76f950a`, 2026-05-11). The value range is `[0.0, 1.0]`
   per the UTL `completeness_fraction` argument. The original `_pct` suffix was an SSOT-drift; the rename window was
   free because zero on-disk writes had shipped. Reviewers reject any new code that uses the old `_pct` constant name.
6. **The manifest column counterpart is the in-band `completeness_fraction` parquet column.** The v8 manifest column
   records the operator-declared EXPECTED fraction (so downstream readers can detect rows degraded BELOW their expected
   floor — e.g. an `ohlcv_24h` row whose policy is `PARTIAL_OK` with `expected_window_completeness_fraction=0.95` but
   actual `completeness_fraction=0.80` → escalate). They are sibling columns, not duplicates.

## Anti-patterns

- **Don't write to the manifest column directly from a service.** Always go through `publish_with_policy()` → resolver →
  `ManifestWriter`. Services that bypass write inconsistent `(state, event)` pairs; downstream `next_state` semantics
  break.
- **Don't catch `ManifestRowBlockedError` and continue.** A `BLOCKED` row is data deliberately withheld by the
  publish-boundary policy + a P0 alert fired. Catching the exception silently swaps correctness for "I got a number" —
  the original failure mode the policy was designed to prevent. The right consumer response is skip + surface the
  publish-time `correlation_id` to operators.
- **Don't read the manifest column without reading `capture_status` too.** The v8 column is `None` for pre-v8 rows
  (≤30-day reader-fallback window per `READER_FALLBACK_WINDOW_DAYS = 30`). Consumers that branch only on the new column
  miss the legacy rows; consumers that branch only on `capture_status` miss the policy-withheld-but-captured-upstream
  case (PUBLISHED_DEGRADED with low `completeness_fraction`).
- **Don't add a fifth `ServiceEmissionPolicy` value during the freeze window.** Per § "UAC enums frozen for the window."
  If a new policy is needed, defer to post-cutover; the four shipped values cover every operator-msg-10 use case.

## Cross-references

- [`/codex/02-data/service-output-emission-semantics.md`](/codex/02-data/service-output-emission-semantics.md) —
  runtime/data perspective: kwargs, lifecycle events, helper API, per-service rollout playbook, worked examples.
- [`/codex/02-data/availability-manifest-and-data-status.md`](/codex/02-data/availability-manifest-and-data-status.md) —
  full manifest schema (v8 incl. the 3 new emission columns); `AvailabilityRecord` dataclass.
- [`/codex/02-data/honest-absence-downstream-handling.md`](/codex/02-data/honest-absence-downstream-handling.md) —
  downstream NaN-handling tolerances per consumer class (the layer below this doc).
- [`../../plans/active/manifest_schema_final_gate_2026_05_09.md`](../../plans/active/manifest_schema_final_gate_2026_05_09.md)
  — owns the v8 manifest schema columns + the `next_state` resolver.
- [`../../plans/active/writegate_honest_coverage_endtoend_2026_05_06.md`](../../plans/active/writegate_honest_coverage_endtoend_2026_05_06.md)
  slices (a) + (b) + (c) — the architecture plan + per-service rollout.
- `cursor-configs/CLAUDE.md` § "Service-output emission policy" — key-rule entry pointing here.
- `unified_api_contracts.canonical.crosscutting.service_emission_policy` — the policy SSOT module.
- `unified_api_contracts.canonical.crosscutting.service_emission_state` — the manifest-column enum module.
- `unified_api_contracts.canonical.crosscutting.manifest_schema` — the v8 column declarations.
- `unified_trading_library.emission_publisher` — the publish-boundary helper.
- `unified_trading_library.manifest_completeness` — the upstream-completeness calculator used by
  `publish_with_manifest_lookup()`.
