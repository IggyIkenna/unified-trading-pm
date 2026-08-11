---
doc_type: audit-result
title: Verdict pack — TRADFI (G4 pre-apply, R7/R3 2026-06-11)
summary:
  TRADFI G4 pre-apply verdict (06-11) — projected v9 946,360 rows (902,878 captured / 37,477 empty / 6,005 failed),
  unparseable residue 106/902,984 (0.012%); grain-aware diff removed=4,374 + changed=2,916 (273 captured→failed, 2,629
  captured→empty, 14 empty→captured upgrades), ~79% removed are garbage-venue v9 drops; awaiting operator.
status: partial
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [manifest, honest-coverage, data-status, tradfi, migration, canonicalisation, data-correctness, verification]
related:
  - /plans/audit/results/r3_beta_renders_2026_06_11/verdict_cefi.md
  - ../r3_verdict_packs_2026_06_17/verdict_tradfi.md
created: 2026-06-11
audited_scope:
  TRADFI projected-v9 index vs live _index (G4 dry-run), grain-aware manifest diff adjudication (garbage-venue drops,
  phantom closed-market over-claims, legacy respelling, CME weekend cells)
date: 2026-06-11
auditor: ikennaigboaka
parent_epic: tradfi_master
severity: P2
resulting_plan:
lib_version:
doc_versions_checked:
---

# Verdict pack — TRADFI (G4 pre-apply, R7/R3 2026-06-11)

**Projection**: 946,360 rows (`_index/audit/projected_index_tradfi.parquet`) — 902,878 captured · 37,477 empty_confirmed
· 6,005 attempted_failed. Unparseable residue: 106 objects of 902,984 (0.012%).

**Adjudicated diff** (projected vs live, `manifest_diff` grain-aware): unchanged=57,841 · added=2 · removed=4,374 ·
changed=2,916 (273 captured→failed, 2,629 captured→empty, **14 empty→captured UPGRADES**).

| Delta class                                  | Share                            | Justification                                                                                                    |
| -------------------------------------------- | -------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Garbage-venue rows (UNKNOWN/blank)           | ~79% of removed                  | Correct v9 drops — rows have no venue identity; 0 objects                                                        |
| Phantom closed-market over-claims            | ~10% removed, ~91% of downgrades | Spot-verified (2020-01-01 BARCHART/CBOE/CME: captured rows, 0 GCS objects) — projection is the HONEST correction |
| Legacy instrument_type respelling            | ~11% of removed                  | combo/future rows superseded by canonical futures_chain vocabulary; data present under canonical key             |
| Weekend-boundary cells (CME Sunday sessions) | ~9% of downgrades                | Calendar-aware CF-11 governs post-apply — NOTE, not a blocker                                                    |

**Evidence**: `market_tick_data_{beta,live}_datastatus.png` · `instruments_{beta,live}_datastatus.png`. Sweep:
E=0/unknown=0 (19:07Z snapshot). Open notes: 106 unparseable objects (shape histogram in `/tmp/r7_tradfi_final.log`).

**G4 --apply for tradfi: AWAITING OPERATOR**
