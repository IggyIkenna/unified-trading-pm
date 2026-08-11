---
doc_type: audit-result
title: Verdict pack — CEFI (G4 pre-apply, R7/R3 2026-06-11)
summary:
  CEFI G4 pre-apply verdict (06-11) — projected v9 index 3,886,859 rows, CF-11 staleness bug fixed; adjudicated diff
  removed=733 garbage venues (0 GCS objects), captured_regressions=943 spot-verified phantoms (honest downgrade), 3,853
  empty→failed by-design CF-11 reclassify; G4 --apply awaiting operator.
status: partial
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [manifest, honest-coverage, data-status, cefi, migration, verification, data-correctness, canonicalisation]

  - /plans/audit/results/r3_beta_renders_2026_06_11/verdict_defi.md
  - /plans/audit/results/r3_beta_renders_2026_06_11/verdict_tradfi.md
  - ../r3_verdict_packs_2026_06_17/verdict_cefi.md
created: 2026-06-11
audited_scope:
  CEFI projected-v9 index vs live _index (G4 dry-run), manifest diff adjudication
  (removed/regressions/status-transitions) + orphan sweep
date: 2026-06-11
auditor: ikennaigboaka
parent_epic: cefi_master
severity: P2
resulting_plan:
lib_version:
doc_versions_checked:
---

# Verdict pack — CEFI (G4 pre-apply, R7/R3 2026-06-11)

**Projection**: 3,886,859 rows. CF-11 staleness bug fixed (consolidated read primary).

**Adjudicated diff**: removed=733 (garbage venues UNKNOWN/BTCF0/ETHF0 — 0 GCS objects) · captured_regressions=943 (was
1,562; genuine phantoms, spot-verified — honest downgrade) · 3,853 empty→failed = by-design CF-11 reclassification.
spot→spot_pair itype synonym fixed (5,239 false demotes eliminated); double-hive-key parse fixed (unparseable → 0).

**Evidence**: beta/live renders. Sweep: E=0/unknown=0 (19:00Z).

**G4 --apply for cefi: AWAITING OPERATOR**
