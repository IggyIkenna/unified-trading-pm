---
doc_type: plan
title: prediction satellite AO dispatch batch 12 — 2026-08-17
summary: >-
  Extraction batch from the prediction tranche's 2026-08-17 /na-eligibility-audit sweep — 3 conflict-cleared,
  bounded/deterministic items pulled directly from 2 source docs via the per-todo RECLASSIFY_SPLIT path (closing the
  loop on 3 MISCLASSIFIED_LIKELY_AO_ELIGIBLE flags an earlier pass today explicitly deferred to "a future pass"). Each
  todo cites its exact source doc; the source docs themselves keep `assigned_vm: NA` for their remaining
  genuinely-operator-gated/judgment items — checkbox reconciliation back into each source doc happens in the paired
  finalize plan. Conflict-checked against every active planning doc under `parent_epic: predictions_master`, the
  tranche's consolidated closeout, and every existing prediction satellite batch (1-11) before drafting — no item here
  duplicates ground an existing dispatched Todos entry already claims.
status: active
nature: process
asset_group: [prediction]
stage: [data]
repos: [unified-trading-pm, market-tick-data-service, unified-api-contracts, instruments-service]
scope: [engineer]
tags: [prediction, ao-dispatch, satellite-batch, na-eligibility-audit, reclassify-split]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/prediction_phase_ab_residuals_2026_07_24.md,
    /plans/active/issues/prediction_batch4_deferred_residuals_2026_08_16.md,
  ]
created: "2026-08-17"
last_updated: "2026-08-20"
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1.2
estimate_calibrated_ai_days: 1.4
assigned_role: data_engineering
effort: high
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/prediction_phase_ab_residuals_2026_07_24.md,
    /plans/active/issues/prediction_batch4_deferred_residuals_2026_08_16.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    market-tick-data-service/scripts/canonicalize_prediction_manifest_2026_07_18.py,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/manifest_finalize.py,
  ]
source: >-
  Drafted by the 2026-08-17 /na-eligibility-audit prediction-tranche run (autonomous, dispatch agt-becf6c) — per-todo
  RECLASSIFY_SPLIT path. All 3 items were tagged MISCLASSIFIED_LIKELY_AO_ELIGIBLE by an earlier na-eligibility-audit
  pass today and explicitly deferred to "a future pass"; this run re-assessed each independently against the primary
  bounded-outcome bar and promoted all 3.
---

# prediction satellite AO dispatch batch 12 — 2026-08-17

> **Drafted 2026-08-17 by /na-eligibility-audit (autonomous) — `status: active`, dispatchable.** Every todo below was
> classified bounded/deterministic (worker-determinable outcome, no open design/judgment call) and conflict-checked
> against every active batch/finalize plan + the consolidated closeout for this tranche before being drafted here.

## Todos

- [x] ✅ [DATA] P1. **Apply the standing canonicalization precedent by default to the A0-ambiguous prediction
      `instrument_type`/`data_type` value set; escalate only a genuine tied residual.** Ruled 2026-07-28 (general
      theme — canonicalization should be done properly, not left as an open-ended gate): (1) enumerate the FULL
      A0-ambiguous set live via the existing `enumerate_prediction_dimensions.py` script; (2) resolve each value by
      applying the SAME precedent already established for prediction (operator, 2026-07-18: canonical = UPPERCASE
      enum, the catalogue is SSOT) — default to whichever candidate reading matches the catalogue's clean canonical
      form, recording the specific per-value mapping decisions with evidence cited; (3) do not block the unambiguous
      majority on this. Only if a specific value survives (2) still genuinely tied between two readings with no
      catalogue precedent to break the tie — escalate that SPECIFIC residual value (not the whole todo) as a narrow
      options+recommendation operator question (mirror `sports_satellite_ao_dispatch_batch5_2026_07_26.md`'s per-item
      operator-decision-gate format). Done when: the full ambiguous set is enumerated with a disposition
      (resolved-by-precedent or escalated-as-residual) recorded per value in this doc's Progress Log. Repo:
      market-tick-data-service, instruments-service. Source:
      `plans/active/prediction_phase_ab_residuals_2026_07_24.md` Phase B, item "RULED 2026-07-28 — apply the standing
      canonicalization precedent by default" (line 432). **DONE 2026-08-17 (slot-19) — full live enumeration + disposition
      recorded, ZERO genuinely-tied residuals found (nothing to escalate). See Progress Log.**

- [ ] [DIAG] P2. **Root-cause the actively-growing blank/null prediction `instrument_type` manifest rows (~10 rows/day,
      NOT static residue) and ship+verify a fix, or record an accepted-gap reason.** Live counts across 3 dated reads:
      30 (2026-07-20) → 70 (2026-07-24) → 100 (2026-07-27), a consistent ~10 rows/day linear rate — distinct from the
      co-located, static 76-row `prediction` (singular) malformed residual on the same axis, which is dead historical
      residue. Done when: the writer/cron path responsible for the blank stamps is identified by name (file:line) with
      a live-vs-historical verdict — candidates include the per-CID writer path near
      `engine/orchestrator/manifest_finalize._finalize_prediction_bundles` (already known to mis-stamp
      `instrument_type` on bundle rows, though that finding was lowercase `"prediction"`, not blank) or a different
      live/per-CID path — and either a fix ships and is verified against the next day's count, or the ~10/day gap is
      recorded as accepted with a stated reason. Repo: market-tick-data-service. Source:
      `plans/active/prediction_phase_ab_residuals_2026_07_24.md` Phase B, item "prediction manifest blank/null
      `instrument_type` rows are ACTIVELY GROWING" (line 463).

- [ ] [DATA] P3. **Investigate whether the 49 canonical-only POLYMARKET `trades` days (2025-04-19..2025-06-05 +
      2025-06-13, outside the 348-date legacy-bundle range) can recover `title`/`slug`/`event_slug` from the IS
      POLYMARKET reference universe** (`prediction_canonical_question_group`/`market_lifecycle`, which the manifest
      census confirms covers these dates) rather than from the legacy `prediction_trades` bundle (which does not exist
      for these days). Evidence at
      `gs://market-data-tick-pred-prd-central-element-323112/_ops/4bi_scratchpad_2026_08_06/` (46-141 shards/day
      sampled, all `enrichment_fields_present=False`). Done when: a dated verdict is recorded (recoverable — with the
      recovery mechanism identified — or genuinely not recoverable from any live source), committed to this doc's
      Progress Log. Repo: unified-api-contracts + instruments-service (read path) + market-tick-data-service
      (enrichment script, if recoverable). Source:
      `plans/active/issues/prediction_batch4_deferred_residuals_2026_08_16.md` todo 2 (line 92).

- [ ] [SCRIPT] P2. **Execute the already-implemented, already-held null-`instrument_type` stamp for the 11,540
      re-accumulated prediction manifest rows (9,260 per-CID + 2,280 CQG-bundle) found by todo 1's 2026-08-17
      enumeration.** Run `market-tick-data-service/scripts/canonicalize_prediction_manifest_2026_07_18.py
      --bundle-mode normalize --apply --confirm-prod-write` (additive per-VM-shard write, race-free vs the
      consolidator, safe-idempotent — a re-run against an already-corrected row is a no-op; this exact target was
      already applied once, 2026-07-19 tick 18, and the script's own docstring anticipates periodic re-runs as the
      sanctioned maintenance pattern for this durability gap). Verify post-run: a fresh dry-run of the same script
      shows 0 rows in TARGET #2's in-scope count. Do NOT pass `--remove-stragglers` (a separate, higher-risk in-place
      CAS action) unless explicitly re-scoped. Repo: market-tick-data-service.
      **[OPERATOR] GATE RESOLVED 2026-08-19 (operator ruling, `BLK-2062d75e`, answered 2026-08-19T15:44:13Z) — RULED
      option A: normalize the CQG-bundle to `PREDICTION_MARKET` too.** The 2026-08-19 gate this line carried (this
      todo's "RESOLVED BY PRECEDENT" framing only actually covering the per-CID half, not the CQG-bundle half of the
      SAME contradiction `prediction_phase_ab_residuals_2026_07_24.md` finding (i) flagged as unresolved) is now
      closed — the operator explicitly chose "normalize the bundle to `PREDICTION_MARKET` too... matching the per-CID
      precedent" over "enforce SSOT bundle-null" (would have un-stamped 77,788 rows) or "leave inconsistent."
      **`[OPERATOR]` tag REMOVED below — this todo is dispatchable as originally written** (`--bundle-mode normalize
      --apply --confirm-prod-write`, both halves: 9,260 per-CID + 2,280 CQG-bundle).

## Deferred

None — every item drafted here already cleared the conflict-check (verified against every `parent_epic:
predictions_master` active planning doc, the consolidated closeout, and prediction satellite batches 1-11; no
overlapping claim found — see the 2026-08-17 na-eligibility-audit run's Phase 2 notes).

## Progress Log

### 2026-08-17 (slot-19, data_engineering) — todo 1: full live A0-ambiguous enumeration + disposition

**Stale-doc finding, fixed here rather than left to re-trap the next reader**: the todo's own source text and this
plan's `context_scope` both cite `enumerate_prediction_dimensions.py` as an existing, reusable script — it does not
exist in any repo. The 2026-07-18 A0 entry (`prediction_phase_ab_residuals_2026_07_24.md` line 116) itself says
"Reusable reads: **scratchpad** `enumerate_prediction_dimensions.py`" — a scratchpad artifact from that session,
never committed. Used the already-committed, equivalent tool instead:
`market-tick-data-service/scripts/canonicalize_prediction_manifest_2026_07_18.py` (default `--dry-run`, read-only,
single-object read of the live consolidated `_index`) — its `print_split_report` IS the live A0-style enumeration
(exact-value cross-tab of `data_type` x categorized `instrument_type`, covering the full known dupe/leakage set from
the original A0 read: `_LOWERCASE_DUPE_ITYPES={"prediction","prediction_market"}`,
`_UNDERLYING_LEAKAGE_ITYPES` = the 13 tokens A0 found). Ran live 2026-08-17 08:31 UTC.

**Live corpus**: 2,805,608 rows (grew from A0's 756,817-row 2026-07-18 baseline — genuine ongoing capture, not a
read anomaly). Full cross-tab (every `data_type` x `instrument_type`-category combination present; no
`lowercase-dupe:*` / `underlying-leakage` / `other:*` column appeared in the live output, meaning literally none of
those categories have ANY surviving rows):

| data_type | `<null/empty>` | `PREDICTION_MARKET` (canonical) |
| --- | ---: | ---: |
| `MARKET_LIFECYCLE` | 2,280 | 0 |
| `book_snapshot_5` | 2,280 | 1,167,348 |
| `market_lifecycle` | 2,280 | 2,280 |
| `prediction_canonical_question_group` | 2,280 | 104,627 |
| `trades` | 2,420 | 1,519,813 |

**Per-value disposition (the todo's own done-when)**:

1. **`instrument_type` null/empty — 11,540 rows (9,260 per-CID + 2,280 CQG-bundle) — RESOLVED BY PRECEDENT.** Stamp
   `PREDICTION_MARKET` (2026-07-18 operator ruling: canonical = UPPERCASE enum, catalogue is SSOT). Per-CID rows are
   "always stamped" by contract (the script's own docstring) — a per-CID null is pure defect residue, not a design
   question. The fix is already implemented and held in `canonicalize_prediction_manifest_2026_07_18.py
   --bundle-mode normalize --apply --confirm-prod-write` (this exact target — was already applied once, 2026-07-19
   tick 18; this is the re-accumulated residual the doc's own line 424-425 anticipates via periodic re-runs).
   **Not run this session** — executing the write is a separate action from this todo's enumeration/disposition
   scope; not flagged `[OPERATOR]` in the source plan and the script itself documents periodic `--apply` re-runs as
   the sanctioned maintenance pattern, so this is a clean pickup for the next `[SCRIPT]`-tagged execution todo, not
   an escalation.
2. **`instrument_type` lowercase-dupe (`prediction`/`prediction_market`) and underlying-asset-leakage
   (`BTC`/`ETH`/`SPX`/... ) — 0 rows live, CONFIRMED FULLY RESOLVED.** These were the bulk of A0's original 2026-07-18
   finding (18 distinct non-canonical values); the 2026-07-19 apply + the write-guard/writer-root fixes
   (`unified-api-contracts@08d48757`, `instruments-service@517baeb9`, `market-tick-data-service@b7272103`, all
   already landed per this doc's siblings) have durably closed this axis. Nothing to canonicalize, nothing to
   escalate.
3. **`data_type` `MARKET_LIFECYCLE` (uppercase, 2,280 rows, ALL null-`instrument_type`) vs `market_lifecycle`
   (lowercase, 4,560 rows) — NOT A DEFECT, no action.** Initially looked like a new casing dupe outside the script's
   3 known targets, but UAC's own registries explicitly ratify BOTH forms as intentional, service-attributed
   spellings, not a canonical/non-canonical pair: `market_data_categories.py:376-377` — `"market_lifecycle"` = "MTDS/
   YAML canonical name (lowercase)", `"MARKET_LIFECYCLE"` = "instruments-service GCS data_type (uppercase legacy)";
   mirrored in `_mvp_scope_rules.py:872-873`, `_source_priority_table.py:557`, `required_window_registry.py:317`, and
   `availability_semantics.py:288` ("MARKET_LIFECYCLE rows are written by instruments-service"). Two different
   writers (MTDS vs instruments-service) legitimately emit two different spellings for the same logical concept, and
   UAC already keys both — applying "one canonical spelling" here would be WRONG, not a fix. Recorded as
   resolved-not-ambiguous rather than silently matched to the sibling data_types' lowercase convention (the
   assumption I initially reached for, before checking UAC).
4. **`data_type` `prediction_trades`→`trades` and empty `source` — 0 residual rows, CONFIRMED FULLY DURABLE** from
   the 2026-07-19 apply + the items-2/3 writer-root fixes (this doc's cited source, tick 21).

**Verdict: zero genuinely-tied residuals survive step (2) — nothing meets the bar for step (3)'s operator escalation**
(no per-item options+recommendation question needed this round). The only concrete remaining action is executing the
already-implemented, already-held null-`instrument_type` stamp (disposition 1) — a `[SCRIPT]`-tagged execution todo,
not a canonicalization-decision todo, so it is out of THIS todo's own scope rather than a loose end.

- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries).
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries).
