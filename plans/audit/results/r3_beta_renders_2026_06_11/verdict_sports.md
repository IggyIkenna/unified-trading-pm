---
doc_type: audit-result
title: Verdict pack — SPORTS (G4 pre-apply, R7/R3 2026-06-11)
summary:
  SPORTS G4 pre-apply verdict (06-11) — projected 786,508 odds rows; GATE GREEN (removed=0, captured_regressions=0),
  17,288 blank-status ODDS_API probe phantoms honestly excluded. Three open pre-apply P1s — 6,869 blank-status
  instruments-store rows, inert CF-5 oracle relabel, C3 2018-era footystats window decision.
status: partial
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [manifest, honest-coverage, data-status, sports, migration, odds, footystats, data-correctness]
related:
  - /plans/audit/results/r3_beta_renders_2026_06_11/verdict_tradfi.md
  - ../r3_verdict_packs_2026_06_17/verdict_sports.md
created: 2026-06-11
audited_scope:
  SPORTS odds bucket projected-v9 index vs live _index (G4 dry-run), gate diff + open pre-apply P1 characterization
  (instruments-store blanks, CF-5 relabel, coverage window)
date: 2026-06-11
auditor: ikennaigboaka
parent_epic: sports_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
---

# Verdict pack — SPORTS (G4 pre-apply, R7/R3 2026-06-11)

**Projection**: 786,508 rows (odds bucket; reference handled by the IS migrator — dry-run GREEN 2.67M rows).

**Adjudicated diff**: **GREEN — removed=0, captured_regressions=0.** 17,288 blank-status ODDS_API probe phantoms
honestly excluded; cell coverage identical.

**Open P1s (pre-apply)**: (1) 6,869 instruments-store rows with BLANK capture_status (characterize/re-stamp before
apply); (2) CF-5 oracle relabel fired zero relabels on MDPS (gates fall through — reason-relabel inert); (3)
C3_pre_launch_window 10,345 objects (2018-era footystats/api_football) need a UAC coverage-window decision. v1_archive:
integrity-clean + row-coverage 72,522/72,522 → drop-safe at G4.5.

**Evidence**: beta/live renders. Sweeps: odds E=0 + reference E=0 (19:09–19:10Z).

**G4 --apply for sports: AWAITING OPERATOR**
