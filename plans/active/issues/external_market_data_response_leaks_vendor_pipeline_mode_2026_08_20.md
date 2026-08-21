---
doc_type: issue
title: MTDS external market-data delivery response leaks the internal vendor tag (pipeline_mode) to counterparties — should be opaque or relabeled
summary: >-
  `GET /external/market-data/delivery/batch` returns an object `file` path that embeds
  `pipeline_mode=batch_tardis` (or the equivalent per-source segment) directly in a counterparty-facing response.
  Operator ruling 2026-08-20: external callers should never see which upstream data vendor (Tardis, Databento, etc.) a
  dataset came from — that is supply-chain detail, not schema. The client artefacts were corrected to document `file`
  as an opaque pass-through token rather than show the real vendor-tagged path, but the underlying API still returns
  the literal tag today. The doc and the code now disagree on purpose (doc states the target contract); this issue
  tracks closing that gap in code.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [external-api, vendor-disclosure, mtds, client-disclosure, api-contract]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /codex/14-customer-journeys/commercial-model/platform-api-reference.html,
    /plans/active/issues/mtds_availability_data_type_without_venue_silently_ignored_2026_08_19.md,
  ]
context_scope:
  [
    market-tick-data-service/market_tick_data_service/api/routers/external.py,
    /codex/14-customer-journeys/commercial-model/platform-api-reference.html,
    /codex/02-data/pipeline-mode-partition.md,
  ]
created: 2026-08-20
last_updated: "2026-08-20"
parent_epic: system_readiness_master
assigned_vm: NA
locked_by:
locked_since:
resolved_by:
execution_scope: local-only
priority: P1
severity: P1
source: >-
  Operator ruling 2026-08-20 while auditing client artefacts for vendor-name disclosure: counterparties should never
  see where our data comes from, only the schema available to them. Found while relabeling the docs' worked example
  and confirming the literal current API response would still show it.
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
---

# The vendor tag reaches the external response today

## The gap

`GET /external/market-data/delivery/batch` returns an object listing where each `file` value is a real internal GCS
path of the shape `raw_tick_data/by_date/day=.../pipeline_mode=batch_tardis/asset_group=.../venue=.../data_type=.../part-NNNN.parquet`.
`pipeline_mode` is source-aware (`{mode}_{source}[_{transport}]` per
[/codex/02-data/pipeline-mode-partition.md](/codex/02-data/pipeline-mode-partition.md)), so the vendor name is
literally embedded in a counterparty-facing response today.

## Why it matters

Operator ruling 2026-08-20: an external caller should never learn which upstream vendor a dataset came from — that is
our supply-chain detail, not part of the schema we're offering. `platform-api-reference.html` §04 was corrected to
document `file` as an **opaque token** the caller must round-trip verbatim rather than parse — which is also better
API design regardless of the vendor question, since it means the internal path structure was never really part of the
external contract. But the live endpoint still returns the literal vendor-tagged string, so the doc's corrected
example and the real response now disagree on purpose: the doc states the target contract, the code has not caught up.

## Todos

- [ ] [BACKEND] P1. **Decide the mechanism**: either (a) return a genuinely opaque token (a signed reference / short
      id) that the download step resolves server-side, or (b) keep a real path but strip/alias the `pipeline_mode`
      segment specifically for the external response serializer, leaving the internal storage layout untouched.
      Option (a) is stronger — it also removes any future coupling between the external contract and internal
      GCS layout changes, not just this one vendor-tag issue.
- [x] ✅ [BACKEND] P1. **EXTRACTED 2026-08-21** — audit `GET /external/market-data/delivery/stream` and
      `/external/market-data/availability` for the same `pipeline_mode`/vendor-bearing path leak. Extracted to
      `cross_cutting_satellite_ao_dispatch_batch21_2026_08_21.md` for AO dispatch (na-eligibility-audit,
      cross-cutting tranche, batch 2 of 3).
- [ ] [REVIEW] P2. **Confirm the fix against the corrected doc example** once shipped — the doc now says `file` is
      opaque; the fix should make that literally true, not just documented as an aspiration.

## Findings — sibling endpoint audit (2026-08-21)

Batch21 item (`cross_cutting_satellite_ao_dispatch_batch21_2026_08_21.md`), source: this doc's todo 2. Direct read of
`market-tick-data-service/market_tick_data_service/api/routers/external.py` (both endpoints, full bodies) plus the
schemas each response is built from. Pure investigation — no fix applied.

- **`GET /external/market-data/availability` — NO LEAK.** `get_availability()` (lines 120-216) reads
  `{gcp_project_id}-honest-coverage/{date}/coverage.json` and returns only the `by_asset_group` /
  `by_venue` / `by_venue_data_type` rollup cells verbatim (`summary`, `venue_summary`,
  `venue_data_type_summary`, `data_type_summary_by_venue`). Confirmed by reading
  `instruments-service/scripts/measure_honest_coverage.py::_compute_coverage()` (the writer of those cells): every
  cell is count/percentage/diagnostic aggregates (`captured`/`empty_confirmed`/`attempted_failed` counts,
  `*_pct` fields, `hollow_instrument_type_fraction`, etc.) — no raw GCS object path, no `pipeline_mode`/vendor
  field anywhere in the writer's output shape. `grep`'d the writer for `pipeline_mode`/`source`/`path`: zero hits
  in the emitted-cell construction.
- **`GET /external/market-data/delivery/stream` — LEAKS, and more directly than `/delivery/batch`.**
  `get_stream_delivery()` (lines 410-448) streams NDJSON via `envelope.model_dump_json()` on each
  `CanonicalPersistEnvelope` read off the `EventTransport` facade. `CanonicalPersistEnvelope`
  (`unified-api-contracts/unified_api_contracts/events/persist.py:53-117`) declares
  `pipeline_mode: PipelineMode | None = None` as a **named top-level field** — `model_dump_json()` serializes it
  verbatim into every emitted line, so the vendor tag reaches the external caller as an explicit, labeled field
  rather than embedded inside a path string the caller would have to parse (arguably a *worse* disclosure than
  `/delivery/batch`'s `file` path leak — no parsing needed to read it off). Additionally, when `payload_pointer`
  is set (non-hot-path shards) it carries a raw GCS blob path per the same canonical partition convention as
  `/delivery/batch`'s `file` field, so that field would independently re-leak the same tag via the path-embedding
  mechanism too.

**Verdict for the record**: `/availability` = no leak (aggregate-only payload, no path/vendor field in the writer's
schema). `/delivery/stream` = leak, both via the explicit `pipeline_mode` field and via `payload_pointer` when set.
Mechanism decision (todo 1 above) still applies to `/delivery/stream` too — whichever fix lands there should also
strip/opacify `pipeline_mode` on the envelope (or the external serializer) and any `payload_pointer` path, not just
`/delivery/batch`'s `file` field.

## Progress Log

**2026-08-20 — filed.** No code touched. `platform-api-reference.html` corrected in the same session to document the
target (opaque) contract rather than the current (vendor-leaking) behaviour — the two are now honestly divergent
pending this fix, not silently inconsistent.

- **na-eligibility-audit 2026-08-21**: RECLASSIFY (per-todo split) — todo 2 (audit sibling endpoints for the same
  leak) is a bounded, pure investigation task; extracted to
  `cross_cutting_satellite_ao_dispatch_batch21_2026_08_21.md`. Todo 1 ("Decide the mechanism") stays `assigned_vm:
  NA` — explicit design decision. Doc's own `assigned_vm: NA` unchanged. Cross-cutting tranche, batch 2 of 3.
- **2026-08-21 (batch21 item, slot 4)**: sibling-endpoint audit done. `/availability` = no leak (verified against
  the coverage-rollup writer's own output shape). `/delivery/stream` = leak — `CanonicalPersistEnvelope.pipeline_mode`
  is a named field serialized verbatim by `model_dump_json()`, plus `payload_pointer` re-leaks via path-embedding
  when set. Findings section added above. Todo 1's mechanism fix should cover both `/delivery/batch` and
  `/delivery/stream`.
