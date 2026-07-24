---
doc_type: plan
title: TradFi legacy-twin bucket deletes — Ikenna sign-off gate
summary:
  Small operator-gated follow-up forked out of tradfi_v9_stage1_finish_2026_07_06.md (now archived, all its other tasks
  closed) during the 2026-07-24 plan-hygiene line-cap remediation. Carries the single remaining
  BLOCKED-OPERATOR-DECISION todo — after the tradfi v9 apply + orphan-sweep E=0 + a byte-verify, the legacy-path twin
  objects (defi / tradfi / pred; cefi + sports already done) can be deleted in a quiet window, but Ikenna's migration
  sign-off gates it — bucket deletes are never-autonomous (hard-stop). This plan does NOT re-run or duplicate the
  dry-run evidence; it references it.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, instruments-service, deployment-service]
scope: [engineer, admin]
tags: [tradfi, legacy-twin, bucket-delete, operator-signoff, hard-stop, orphan-sweep]
related:
  [
    /plans/archive/2026_07/tradfi_v9_stage1_finish_2026_07_06.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/migration_verification_orphan_safety_2026_06_10.md,
    /plans/active/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
last_updated: 2026-06-27
parent_epic: instruments_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: data_engineering
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Forked from tradfi_v9_stage1_finish_2026_07_06.md's task 11 (this was the only remaining open todo besides the
  Folded-in-scope Layer-1 certify item, which moved to tradfi_consolidated_closeout_2026_07_18.md in the same
  remediation pass) per the operator-approved plan-hygiene line-cap remediation
  (plans/active/issues/plan_line_cap_remediation_2026_07_23.md, row 30). Content moved verbatim, not rewritten.
---

# TradFi legacy-twin bucket deletes — Ikenna sign-off gate

> **Do not run any delete without operator sign-off.** This is a hard-stop per `/codex/11-project-management/`
> governance HARD RULES (bucket deletes are human-only) and per `migration_verification_orphan_safety_2026_06_10.md`
> §"HARD-STOP respected: everything up to `--apply` only; G4 `--apply` + G4.5 verified-delete `--apply` stay
> operator-gated" — `cleanup_legacy_twins.py --apply` is listed there alongside the migration `--apply` itself as a
> HARD-STOP.

## Where the dry-run evidence already lives (referenced, not duplicated)

The prerequisite this todo needs (orphan-sweep `orphan_class_E=0` + a byte-verify) was met and evidenced in
`/plans/archive/2026_07/tradfi_v9_stage1_finish_2026_07_06.md`'s own task 2 (🎯 GATE MET 2026-07-10 17:17:22 UTC —
`A_canonical_manifested=2,594,017 · B_legacy_duplicate=995 · C_manifest_infra=38 · C2_non_data=7,884,651 · D_junk=105,207 · E_orphan_real=0`,
over 10,584,946 objects). The report itself lives at
`gs://market-data-tick-tradfi-prd-central-element-323112/_index/audit/orphan_sweep_tradfi.parquet` — 995 actionable rows
(0 orphan-E + 995 legacy-B), which is this plan's verified-delete candidate set. Read that task's full entry for the
complete diagnosis trail (taxonomy fixes, the 585-orphan backfill-and-close, the fresh full re-sweep) — it is not
restated here.

## Todo

- [ ] [DATA] P1. **BLOCKED-OPERATOR-DECISION — legacy-twin bucket DELETES (defi / tradfi / pred).** After the tradfi
      apply + orphan-sweep E=0 + a byte-verify, the legacy-path twin objects can be deleted in a quiet window (cefi +
      sports already done). **Ikenna's migration sign-off GATES this — bucket deletes are never-autonomous
      (hard-stop).** Do NOT run any delete until the operator signs off; the working agent posts the byte-verify
      evidence and RAISES for sign-off. _(Carries `BLOCKED-` so the orchestrator will not dispatch it — stays visible
      for the operator.)_ **STATUS 2026-07-10 (this session): still correctly BLOCKED, NOT run — two real reasons, not
      one.** (1) The task's own literal prerequisite — orphan-sweep E=0 + byte-verify — is not yet available; task 2's
      full sweep is genuinely still in progress this session (see task 2 above). (2) This session's dispatch briefing
      characterized tradfi/defi/pred legacy-bucket deletes as "pre-approved per this workspace's standing
      migration-mechanics decision — proceed," but the governing SSOT this task cites
      (`migration_verification_orphan_safety_2026_06_10.md` §"HARD-STOP respected: everything up to `--apply` only; G4
      `--apply` + G4.5 verified-delete `--apply` stay operator-gated") explicitly lists
      `cleanup_legacy_twins.py --apply` alongside the migration `--apply` itself as a HARD-STOP, and this task's own
      text requires "Ikenna's migration sign-off." A dispatch-briefing paraphrase of a "standing decision" does not
      override an explicit, irreversible-production-delete HARD-STOP written into the plan's own governing
      codex-adjacent doc — deliberately did NOT run `cleanup_legacy_twins.py --apply --i-understand` this session. Once
      task 2's sweep completes,
      `cleanup_legacy_twins.py --asset-group tradfi --report-uri _index/audit/orphan_sweep_tradfi.parquet --dry-run`
      (never `--apply`) is the safe next step — it produces the verified-delete candidate list + byte-verify evidence
      this task asks the working agent to post, for a REAL operator sign-off to review.

  **Note (2026-07-24, forked from `tradfi_v9_stage1_finish_2026_07_06.md`, now archived)**: the task's own literal
  prerequisite (task 2's orphan-sweep) IS now met — see "Where the dry-run evidence already lives" above. The
  `--dry-run` re-run against the fresh report (995 legacy-B candidate rows) is the safe next step for whoever picks this
  up; `--apply` stays gated on Ikenna's sign-off regardless.

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

- **2026-07-24** — Forked out of `tradfi_v9_stage1_finish_2026_07_06.md` (task 11) via the operator-approved
  plan-hygiene line-cap remediation (`plans/active/issues/plan_line_cap_remediation_2026_07_23.md` row 30). Content
  moved verbatim; no new work performed. The parent plan's remaining task (Folded-in-scope Layer-1 certify) moved to
  `tradfi_consolidated_closeout_2026_07_18.md` in the same pass, leaving the parent with 0 open todos — it was archived
  to `plans/archive/2026_07/tradfi_v9_stage1_finish_2026_07_06.md`.
