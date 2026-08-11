---
doc_type: audit-result
title: Verdict pack — DEFI (G4 pre-apply, R7/R3 2026-06-11)
summary:
  DEFI G4 pre-apply verdict (06-11) — projected v9 1,580,037 rows; first-ever CF-11 honest-absence re-emit for defi
  (object-scan was silently dropping the 1.23M-row absence corpus, fixed mtds@77f1a61); removed=5,320 all
  respelling-supersession (AAVEV3/UNISWAPV2/3/4 + EIGENLAYER), regressions=0; awaiting operator.
status: partial
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [manifest, honest-coverage, data-status, defi, migration, canonicalisation, data-correctness, pipeline-mode]

  - /plans/audit/results/r3_beta_renders_2026_06_11/verdict_cefi.md
  - ../r3_verdict_packs_2026_06_17/verdict_defi.md
created: 2026-06-11
audited_scope:
  DEFI projected-v9 index vs live _index (G4 dry-run), CF-11 honest-absence re-emit + respelling-supersession
  adjudication + orphan sweep
date: 2026-06-11
auditor: ikennaigboaka
parent_epic: defi_master
severity: P2
resulting_plan:
lib_version:
doc_versions_checked:
---

# Verdict pack — DEFI (G4 pre-apply, R7/R3 2026-06-11)

**Projection**: 1,580,037 rows. First-ever CF-11 honest-absence re-emit for defi (the pure object-scan was silently
dropping the 1.23M-row absence corpus — fixed mtds@77f1a61).

**Adjudicated diff**: removed=5,320, captured_regressions=0 (was 810 pre-adjudication). All removals are
respelling-supersession: AAVEV3/UNISWAPV2/3/4 venue-spelling duplicates (canonical twins verified 0-missing) + 104
EIGENLAYER data_type/instrument_type respells.

**Evidence**: beta/live renders as above. Sweep: E=0/unknown=0 (18:52Z). Also fixed in this wave: processed-candle
corpus pass-through (prior code falsely phantom-demoted captured processed rows — a REAL-RUN bug, not just projection).

**G4 --apply for defi: AWAITING OPERATOR**
