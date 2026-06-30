---
doc_type: audit-result
title: Verdict pack — CEFI (G4 pre-apply, R7/R3 2026-06-11)
summary:
status:
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created:
audited_scope:
date:
auditor:
parent_epic: cefi_master
severity:
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
