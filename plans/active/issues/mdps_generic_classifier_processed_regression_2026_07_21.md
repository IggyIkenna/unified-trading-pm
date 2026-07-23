---
doc_type: issue
title: >-
  `_classify_data_type_for_venue`'s processed-vs-raw 4-state classification silently broke for MDPS rows the day the
  manifest `data_type` axis switched to source-keyed (`752eaff`) -- every MDPS venue/category outside the new
  honest-coverage path now always reports "missing", never "blocked_on_raw"
summary: >-
  Surfaced as an incidental finding (fact #7 / Open Question 4) while designing a SEPARATE, unimplemented feature
  (extending MTDS honest-coverage to MDPS with a timeframe axis -- see
  `mdps_honest_coverage_timeframe_extension_design_2026_07_21.md`), then independently re-confirmed by all 3 adversarial
  reviewers of that design. This finding is a REAL, ALREADY-LIVE regression, not a design gap -- filed separately per
  the workspace's "big finding (data-correctness) -> NOTIFY OPERATOR + issue doc" rule, since it is dated,
  in-production, and unrelated to whether the honest-coverage design ever ships.
  `deployment-api/deployment_api/services/data_status/breakdowns_core.py`'s generic (non-honest-coverage) classifier
  `_classify_data_type_for_venue` (lines ~680-756) decides "missing" vs "blocked_on_raw" by checking
  `is_processed_data_type(dt)` / `get_raw_source_data_types(dt)` against UAC's `PROCESSED_REQUIRES_RAW` registry
  (`unified_api_contracts/registry/processed_data_dependencies.py:24-89`), which is keyed on the LEGACY aggregated
  data_type token shape (`ohlcv_1m`, `deriv_ohlcv_5m`, ...). MDPS's writer (`market-data-processing-service` commit
  `752eaff`, landed 2026-07-21 -- the same day this was found) changed the manifest `manifest_row_key`'s `data_type` to
  the SOURCE-keyed value instead (`canonical_writer.py:513`, comment: "Manifest data_type AXIS = SOURCE data_type
  (operator ruling 2026-07-21)") -- so post-cutover MDPS rows now carry `data_type="trades"` / `"derivative_ticker"`,
  which are RAW-source keys, not `PROCESSED_REQUIRES_RAW` keys. `is_processed_data_type("trades")` is therefore `False`
  for every post-cutover MDPS row, and the generic classifier can never again emit "blocked_on_raw" for MDPS -- it
  silently degrades to always reporting "missing" instead, for any MDPS venue/category that isn't (yet) covered by the
  honest-coverage path (i.e. everything, since that path doesn't exist yet -- see the sibling design doc).
status: resolved
nature: issue
asset_group: [cefi, defi, tradfi]
stage: [data]
repos: [deployment-api, unified-api-contracts, market-data-processing-service]
scope: [engineer]
tags:
  [
    mdps,
    data-status,
    honest-coverage,
    classifier-regression,
    data-correctness,
    manifest,
    processed-vs-raw,
    operator-ruling-2026-07-21,
    duplicate-finding,
  ]
related:
  - mdps_honest_coverage_timeframe_extension_design_2026_07_21.md
  - plans/active/data_pipeline_check_mdps_features_2026_07_20.md
  - ../../archive/issues/mdps_datatype_axis_switch_breaks_generic_classifier_2026_07_21.md
created: "2026-07-21"
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.2
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
resolved_by: >-
  DUPLICATE of `plans/archive/issues/mdps_datatype_axis_switch_breaks_generic_classifier_2026_07_21.md` (same root
  cause, found independently by a different agent the same day, already fixed+shipped there:
  unified-api-contracts@0900a4d98b1e5136ba28d343cbf6df7c58bfbd47 +
  deployment-api@ac2e61e606e41ba87515d54eb531648bafa304a3, both verified landed on origin/live-defi-rollout).
locked_by:
source: [self-investigation-2026-07-21, promoted-from-scratchpad-2026-07-23]
---

# Why this is filed separately from the honest-coverage design doc

The design doc it was found inside proposes brand-new, unimplemented functionality (MDPS timeframe-aware honest
coverage) that is explicitly NOT ready to ship (a corroborated critical bug + 3 open questions block it, see the sibling
doc). This finding is different in kind: it is a REAL regression in code that is ALREADY LIVE in production today,
introduced by a real, already-landed commit, affecting a currently-served UI surface (the generic processed-vs-raw
classification), independent of whether the honest-coverage feature is ever built. Bundling it into the design doc would
bury a live data-correctness bug inside a large "not ready yet" design write-up. Per this workspace's findings-triage
rule ("big finding — data-correctness / cross-repo / SSOT contradiction — NOTIFY OPERATOR + issue doc"), it gets its own
filing.

**Provenance note**: this finding and its sibling design doc were produced in a prior pass of this same session
(2026-07-21, before a context-compaction boundary) but were never committed -- they existed only as scratchpad text
files with no repo footprint. Promoted here 2026-07-23 during a `/pre-compact` audit that caught them (Step 1:
"chat-only findings... exist nowhere on disk"). All content below is the original finding, reproduced faithfully;
nothing has been re-verified against the CURRENT working tree as part of this promotion pass -- the file:line citations
reflect the state as of 2026-07-21 and should be spot-checked before acting, since ~2 days of concurrent work have
landed on `deployment-api`/`unified-api-contracts` since then.

# What was found

`_classify_data_type_for_venue` (`deployment-api/deployment_api/services/data_status/breakdowns_core.py:680-756`) is the
GENERIC (non-honest-coverage) 4-state classifier -- the "baseline, less-precise path," distinct from and run in parallel
with the honest-coverage path this session's design work concerns. At lines ~742/746 it calls
`is_processed_data_type(dt)` / `get_raw_source_data_types(dt)` (both from
`unified_api_contracts/registry/processed_data_dependencies.py`) to decide whether a missing shard should report as
`"blocked_on_raw"` (the raw MTDS data it depends on hasn't landed yet -- an honest, non-alarming state) versus plain
`"missing"` (nothing is blocking it, something is actually wrong).

`PROCESSED_REQUIRES_RAW` (`processed_data_dependencies.py:24-89`) is keyed on the LEGACY aggregated token shape:
`ohlcv_1m`, `deriv_ohlcv_5m`, etc. -- the data_type string MDPS used to write into manifest rows BEFORE today's commit.

MDPS's writer (`market-data-processing-service/.../canonical_writer.py:513`, comment "Manifest data_type AXIS = SOURCE
data_type (operator ruling 2026-07-21)") changed `manifest_row_key`'s `data_type` value from the legacy aggregated shape
to the SOURCE-keyed shape (`"trades"`, `"derivative_ticker"`) as of commit `752eaff`, landed 2026-07-21 (the same day as
this finding). This was confirmed to be an intentional operator ruling, not a bug in itself -- the regression is a
SECOND-ORDER effect nobody updated for.

**Consequence**: `is_processed_data_type("trades")` — checking a RAW-source key against a registry keyed on
PROCESSED/aggregated keys — is `False`. Every post-cutover MDPS manifest row is now invisible to this classifier's "is
this actually a processed shard blocked on raw data" check. The generic classifier can never emit `"blocked_on_raw"` for
MDPS again; every MDPS gap reports as plain `"missing"` instead, for any venue/category that isn't (or isn't yet)
covered by a more precise path.

# Corroboration

Independently re-confirmed by 2 of 3 adversarial reviewers of the sibling honest-coverage design (which cited this same
fact as "fact #7" and correctly declined to fix it in scope, flagging it for separate filing instead — this doc is that
separate filing). Reviewer 1 explicitly re-verified `breakdowns_core.py:742,746` + the registry file and confirmed the
citation is accurate. No reviewer disputed this finding — all three treated it as a real, independent, pre-existing (as
of 2026-07-21) regression.

# What was NOT done

- Not fixed. Not implemented. This is a finding-only doc.
- Not re-verified against the CURRENT (2026-07-23) working tree -- ~2 days of unrelated concurrent work have landed on
  `deployment-api`, `unified-api-contracts`, and `market-data-processing-service` since this was found; the exact line
  numbers cited may have drifted. The underlying mechanism (source-keyed vs aggregated-keyed lookup mismatch) is very
  unlikely to have self-resolved, since nothing in this session's other work touched `processed_data_dependencies.py` or
  `breakdowns_core.py`, but re-grepping the exact lines before fixing is recommended rather than trusting these
  citations verbatim.
- Blast radius not fully mapped: this affects the GENERIC classifier's surface specifically (whichever UI/API consumers
  read `_classify_data_type_for_venue`'s output directly, as opposed to the honest-coverage path's output) -- which
  specific UI panels/API responses this reaches was not traced in the original finding.

# Suggested next step

1. Re-verify the citations against the current tree (2 days have passed).
2. Decide the fix shape: either (a) widen `PROCESSED_REQUIRES_RAW` to ALSO accept source-keyed data_type strings as keys
   (additive, lowest-risk), or (b) reconcile via a shared "source data_type -> processed data_type" mapping function
   used by both the legacy-token lookup and the new source-keyed writes, so there is one translation layer instead of
   two divergent vocabularies. Option (a) is the smaller, faster fix; option (b) is more correct long-term and would
   also help close the "three divergent timeframe vocabularies" finding in the sibling design doc.
3. Confirm the actual production impact: is `_classify_data_type_for_venue`'s output currently visible anywhere an
   operator/user would see a misleading "missing" (vs "blocked_on_raw") status for MDPS data today? If so, this is a
   live, user-visible correctness issue and should be prioritized accordingly, not treated as cosmetic.

# Resolution (2026-07-23) — DUPLICATE of an already-fixed issue, not new work

While re-verifying citations against the current tree per the "suggested next step" above, found that
`_classify_data_type_for_venue` (`deployment-api/deployment_api/services/data_status/breakdowns_core.py:680-756`)
**already has the fix**: `service: str = ""` is a real parameter (line 688), threaded into
`is_processed_data_type`/`get_raw_source_data_types` exactly as this doc's own "suggested next step" option (b)
described, with a docstring (lines 730-744) citing `mdps_datatype_axis_switch_breaks_generic_classifier_2026_07_21.md`
by name.

That doc — `plans/archive/issues/mdps_datatype_axis_switch_breaks_generic_classifier_2026_07_21.md` — describes the
IDENTICAL root cause (same commit `752eaff`, same file:line citations, same "missing vs blocked_on_raw" mechanism),
found independently the same day (2026-07-21) by a different agent working
`mtds_data_status_page_parity_2026_07_21.md`'s MDPS-parity todo, and already fixed + shipped + archived:
`unified-api-contracts@0900a4d98b1e5136ba28d343cbf6df7c58bfbd47` (option (b), NOT (a) — a service-scoped dual-key, since
a global re-key would have misclassified genuine raw MTDS rows carrying the same token) +
`deployment-api@ac2e61e606e41ba87515d54eb531648bafa304a3` (threads `service=service` through), both verified landed on
`origin/live-defi-rollout` by SHA, both repos' full `quality-gates.sh` green, with dedicated regression tests
(`test_processed_data_dependencies.py`, `TestMdpsSourceAxisClassification` in `test_data_status_service.py`).

**This doc's own promotion (2026-07-23, "rescued" from a scratchpad file with zero prior repo footprint) was itself the
duplicate** — the finding was real and correctly triaged at the time it was originally made (2026-07-21), but by the
time it was promoted out of scratchpad two days later, a parallel session had already found, fixed, and archived the
same root cause under a different filename. Nothing further to do here. Also fixed in the same shipped commit (per the
archived doc's own todos): the closely-related `_TIMEFRAMES` vocabulary gap (missing `"15s"`) this doc's "suggested next
step" #2 also flagged.
