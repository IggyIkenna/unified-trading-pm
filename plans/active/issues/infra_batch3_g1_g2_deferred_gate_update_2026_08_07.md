---
doc_type: issue
title: Infra batch3 Deferred G1/G2 — gate update (partial clear, new blocker)
summary: >-
  Tracked follow-up from archiving `infra_satellite_ao_dispatch_batch3_2026_07_30.md`. G1 (4-item
  base-service.sh/base-library.sh serialized unit, ruling-register entry #36 option A) and G2 (move 0.10.8 constant into
  resolve-canonical-versions.py, same entry) are now PARTIALLY conflict-clear: the original blocking conditions (batch1b
  BACKEND P3 sub-item 3 + ci-batch2 todos 1/11) have ALL landed. However a NEW claim on base-service.sh has appeared:
  `infra_satellite_ao_dispatch_batch6_2026_08_02.md`'s open `[INFRA] P3` UV_LINK_MODE todo. Re-check after batch6 ships.
status: open
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [infra, ao-dispatch, deferred, batch3-followup, base-service]
related:
  [
    /plans/archive/2026_07/infra_satellite_ao_dispatch_batch3_2026_07_30.md,
    /plans/active/infra_satellite_ao_dispatch_batch6_2026_08_02.md,
    /plans/active/infra_satellite_ao_dispatch_batch1_2026_07_26.md,
  ]
created: "2026-08-07"
last_updated: "2026-08-07"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.08
assigned_role: infra
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
source: >-
  Authored by slot-6 as step 1 of the 6-step archival ritual for
  `infra_satellite_ao_dispatch_batch3_finalize_2026_07_30.md` (2026-08-07). Migrates the G1/G2 deferred items from the
  batch3 parent's Deferred table so they are tracked as a `- [ ]` todo, not stranded prose.
---

# Infra batch3 Deferred G1/G2 — gate update

## Context

When `infra_satellite_ao_dispatch_batch3_2026_07_30.md` was archived (2026-08-07), its Deferred table recorded G1 and G2
as still gated by multiple competing base-service.sh/base-library.sh claims. As of the archival date:

**Original blocking conditions — now ALL MET:**

- `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md`'s `[BACKEND] P3` MTDS retry_safe todo: **`[x]` DONE**.
  Sub-item 3 ("generalize lint into base-service.sh") shipped as STEP 5.104 in base-service.sh (`PM@4d3713ade`).
- `ci_satellite_ao_dispatch_batch2_2026_07_29.md` todos 1 and 11 (base-service.sh + base-library.sh): **ARCHIVED** — the
  whole plan is at `plans/archive/2026_07/ci_satellite_ao_dispatch_batch2_2026_07_29.md`, all todos `[x]`.

**New blocking condition:**

- `infra_satellite_ao_dispatch_batch6_2026_08_02.md`'s `[INFRA] P3` `UV_LINK_MODE=hardlink` investigation/fix: still
  `[ ]` open. This plan claims `scripts/quality-gates-base/base-service.sh` under the serialized-resource ruling (batch1
  ruling-register entry #36: "one owning plan at a time"). Infra cannot own G1/G2 while batch6's claim is live.

**G3 (DataStatusTab.tsx sequencing):** Already extracted and shipped in
`infra_satellite_ao_dispatch_batch5_2026_08_01.md` (archived). Not tracked here.

## Todos

- [ ] [DOC] P3. **After `infra_satellite_ao_dispatch_batch6_2026_08_02.md`'s `[INFRA] P3` base-service.sh UV_LINK_MODE
      todo ships (the claim on base-service.sh ends), re-run `generate_ag_closeout_audit_candidates.py --tranche infra`
      and check whether G1 (4-item base-service.sh/base-library.sh serialized unit, batch1 ruling-register entry #36
      option A) and G2 (move the 0.10.8 constant into `scripts/workspace/resolve-canonical-versions.py`, same entry) are
      now fully conflict-clear and extractable.** If clear: file a thin extraction plan (or add to an existing active
      infra batch). If still blocked by another claim, update the gate record here. (repo: unified-trading-pm)

## Progress Log

- **na-eligibility-audit 2026-08-07 (infra tranche)**: KEEP-NA, valid — first verdict for this same-day doc. Read
  end-to-end; `grep -cE '^- \[ \]'` = 1, matching. The sole todo is explicitly gated on
  `infra_satellite_ao_dispatch_ batch6_2026_08_02.md`'s own `[INFRA] P3` UV_LINK_MODE todo shipping first (a still-open
  dependency on the shared, serialized `base-service.sh`/`base-library.sh` resource) — dependency-blocked, not
  worker-determinable today.
