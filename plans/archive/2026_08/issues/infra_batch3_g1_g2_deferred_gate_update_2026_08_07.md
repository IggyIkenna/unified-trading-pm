---
doc_type: issue
title: Infra batch3 Deferred G1/G2 — gate update (partial clear, new blocker)
summary: >-
  Tracked follow-up from archiving `infra_satellite_ao_dispatch_batch3_2026_07_30.md`. G1 (4-item
  base-service.sh/base-library.sh serialized unit, ruling-register entry #36 option A) and G2 (move 0.10.8 constant into
  resolve-canonical-versions.py, same entry) are now PARTIALLY conflict-clear: the original blocking conditions (batch1b
  BACKEND P3 sub-item 3 + ci-batch2 todos 1/11) have ALL landed. However a NEW claim on base-service.sh has appeared:
  `infra_satellite_ao_dispatch_batch6_2026_08_02.md`'s open `[INFRA] P3` UV_LINK_MODE todo. Re-check after batch6 ships.
status: resolved
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
    /plans/active/infra_satellite_ao_dispatch_batch9_2026_08_09.md,
    /plans/active/codex_violations_ratchet_to_five_2026_06_10.md,
  ]
created: "2026-08-07"
last_updated: "2026-08-09"
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
resolved_by: "unified-trading-pm (ag_closeout_auditor, infra tranche, dispatch agt-3b6f6b, 2026-08-09)"
depends_on: []
source: >-
  Authored by slot-6 as step 1 of the 6-step archival ritual for
  `infra_satellite_ao_dispatch_batch3_finalize_2026_07_30.md` (2026-08-07). Migrates the G1/G2 deferred items from the
  batch3 parent's Deferred table so they are tracked as a `- [ ]` todo, not stranded prose.
---

> **🟢 ARCHIVED 2026-08-09 — RESOLVED** (status: resolved, 0 open todos, unlocked). G1 confirmed fully done (4/4 items,
> landed via other channels, never cross-referenced back here); G2 extracted into
> `infra_satellite_ao_dispatch_batch9_2026_08_09.md`. Archived by `/ag-closeout-audit infra` (dispatch agt-3b6f6b).

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

- [x] ✅ [DOC] P3. **DONE 2026-08-09 (`/ag-closeout-audit infra` daily run).** Re-ran
      `generate_ag_closeout_audit_candidates.py --tranche infra` and re-checked both gates against LIVE source (not just
      doc prose) now that batch6's UV_LINK_MODE todo shipped 2026-08-08: - **G1 (4-item base-service.sh/base-library.sh
      serialized unit) — ALL 4 CONFIRMED DONE, via other channels, never flipped anywhere:** (1) domain-client base-gate
      retarget — live in `base-service.sh:1416-1426`, "RETARGETED 2026-07-30"; stale checkbox in
      `codex_violations_ratchet_to_five_2026_06_10.md` flipped this same run. (2) pip floor bump
      (CVE-2026-3219/-6357/PYSEC-2026-196 ignore drops) — `QG_PIP_AUDIT_COMMON_IGNORES` confirmed empty in both files
      live; `cve_affected_pinned_deps_remediation_2026_06_18.md`'s own `[SCRIPT] P2` (DONE 2026-07-30,
      `unified-trading-pm@af08848b9`) dropped all 9 ignore entries including these 3, fleet-wide. (3) cryptography/idna/
      CVE-2026-4539 re-check — same doc: cryptography floor bumped 2026-07-13 (17/17 repos), idna/pygments fixed
      2026-07-30, ignore list empty, confirmed live. (4) uv drift-guard — live in `base-service.sh:476-477` +
      `base-library.sh:253-254`, a warn-only `uv version drift` check already present in both files. - **G2 (move the
      0.10.8 constant into a canonical source) — STILL OPEN, scope now WIDER than originally scoped (6 hardcoded sites
      confirmed live, not 3): `scripts/setup.sh` (×2), `scripts/workspace/workspace-bootstrap.sh`
      (`REQUIRED_UV="0.10.8"`), `scripts/self-hosted-runners/hosted-baseline/python-quality-gates-v2.yml`,
      `scripts/quality-gates-base/base-service.sh` (×3), `scripts/quality-gates-base/base-library.sh` (×3).
      `scripts/workspace/resolve-canonical-versions.py` currently has no UV-version constant at all (only handles
      `uv_sources` path-based deps) — the centralization genuinely doesn't exist yet. Conflict-check: no other active
      plan/issue references `REQUIRED_UV`/uv-version-centralization — conflict-clear. - **Extracted G2 into
      `infra_satellite_ao_dispatch_batch9_2026_08_09.md`** (status: draft, paired with a `status:       active` finalize
      plan per the no-double-gate rule) — bundled alongside 3 conflict-clear items from
      `codex_drift_followups_dual_cloud_image_builds_2026_08_08.md` (a same-day net-new candidate). **This doc's own
      todo is now fully answered — 0 open todos, unlocked, archiving per the 6-step ritual.**

## Progress Log

- **2026-08-09 — `/ag-closeout-audit infra` daily run (autonomous, dispatch agt-3b6f6b).** Re-checked the sole todo live
  against source code, not just doc prose (see todo above for full evidence). G1: all 4 items confirmed done — 3 landed
  silently via `cve_affected_pinned_deps_remediation_2026_06_18.md`'s 2026-07-30 fleet-wide ignore-drop + the 2026-07-30
  domain-client retarget + the pre-existing uv drift-guard; none were ever cross-referenced back to this gate or to
  `codex_violations_ratchet_to_five`'s own stale copy of item 1 until today. G2: still genuinely open, rescoped from 3
  to 6 hardcoded sites (a real, live count, not the original estimate), conflict-clear, extracted into
  `infra_satellite_ao_dispatch_batch9_2026_08_09.md` alongside 3 same-day net-new candidates from
  `codex_drift_followups_dual_cloud_image_builds_2026_08_08.md`. Archiving now per
  `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` (0 open todos, unlocked, no deferred item left
  behind — G2's only remaining content is now tracked in batch9).
- **na-eligibility-audit 2026-08-07 (infra tranche)**: KEEP-NA, valid — first verdict for this same-day doc. Read
  end-to-end; `grep -cE '^- \[ \]'` = 1, matching. The sole todo is explicitly gated on
  `infra_satellite_ao_dispatch_ batch6_2026_08_02.md`'s own `[INFRA] P3` UV_LINK_MODE todo shipping first (a still-open
  dependency on the shared, serialized `base-service.sh`/`base-library.sh` resource) — dependency-blocked, not
  worker-determinable today.
