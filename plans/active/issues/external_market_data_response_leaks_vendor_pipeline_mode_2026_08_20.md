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
- [ ] [BACKEND] P1. **Audit every other external response for the same leak** — this was found on one endpoint by
      inspecting one worked example; `GET /external/market-data/delivery/stream` and `/external/market-data/availability`
      should be checked for the same `pipeline_mode`/vendor-bearing path pattern before assuming this is the only one.
- [ ] [REVIEW] P2. **Confirm the fix against the corrected doc example** once shipped — the doc now says `file` is
      opaque; the fix should make that literally true, not just documented as an aspiration.

## Progress Log

**2026-08-20 — filed.** No code touched. `platform-api-reference.html` corrected in the same session to document the
target (opaque) contract rather than the current (vendor-leaking) behaviour — the two are now honestly divergent
pending this fix, not silently inconsistent.
