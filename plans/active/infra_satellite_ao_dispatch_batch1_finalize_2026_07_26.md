---
doc_type: plan
title:
  Infra satellite AO batch 1 — finalize (reconcile all 17 source docs + re-check the 10 conflict-gated deferrals +
  archive)
summary: >-
  Gated closeout for `infra_satellite_ao_dispatch_batch1_2026_07_26.md` — machine-held via `depends_on` +
  `gate_on_depends: true` until all 25 of that plan's todos are done, so this can never dispatch early. Batch 1 was
  extracted from 17 DIFFERENT infra satellite plans/issues (not from one parent), so this finalize reconciles each of
  those 17 docs' corresponding checkboxes independently, then re-checks batch 1's own `## Deferred` section — 10 of its
  14 held-back items are CONFLICT-GATED, which is the only category that clears without a human ruling, so each one's
  named competing claim is re-examined to see whether it has since shipped or been superseded and the item can move into
  a batch 2. Only then does the standard archival ritual run on batch 1. The goal is that after this plan, every infra
  satellite doc's real remaining work is either shipped, re-tracked as an explicit new todo, or confirmed still
  correctly gated on a human decision — with the count of genuinely-orphaned infra docs re-measured rather than assumed.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [infra, ao-dispatch, close-out, batch-1, satellite-docs, archival, plan-hygiene]
related:
  [
    /plans/active/infra_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/archive/issues/infra_plan_reconcile_parked_decisions_2026_07_26.md,
    /plans/active/ag_closeout_audit_rollout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-30"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/active/infra_satellite_ao_dispatch_batch1_2026_07_26.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/issue-doc-lifecycle.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /plans/PLAN_FORMAT.md,
    /plans/active/task_template.md,
  ]
supersedes:
superseded_by:
depends_on: [infra_satellite_ao_dispatch_batch1_2026_07_26]
gate_on_depends: true
sequential: true
source: >-
  `/ag-closeout-audit infra` run 2026-07-26 — mirrors the `sports_satellite_ao_dispatch_batch2_finalize_2026_07_24.md`
  gated-reconcile-then-archive pattern, per `plans/active/task_template.md` §4's finalize-plan-coverage rule (every AO
  batch plan needs a paired gated finalize).
---

# Infra satellite AO batch 1 — finalize

> **`status: draft` — NOT ingested, NOT dispatched.** Flips to `active` only together with its parent batch, on explicit
> operator approval.

> **Machine-gated on `infra_satellite_ao_dispatch_batch1_2026_07_26.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue any todo below until all 25 tasks in that plan are `done`. `sequential: true` because todo 2
> needs todo 1's reconciliation finished (to know which source docs still have real open work vs are now fully closed),
> and todo 4 (archival) must run last.

## Todos

- [x] ✅ **DONE 2026-08-09 (slot-3, review-craft-per-task).** For each of batch 1's 25 now-done todos: find the
      corresponding checkbox in the source doc its text names (every todo ends with `Source: `<doc>.md``) and flip it
      `[x]`, citing the batch-1 commit(s) that shipped it. **Verify each cited sha actually exists and is an ancestor of
      `origin/live-defi-rollout` (`git merge-base --is-ancestor <sha> origin/live-defi-rollout`) before citing it — do
      not copy batch 1's own evidence line blind.** Several batch-1 todos COMBINED multiple source-doc checkboxes into
      one (the setuptools 3-step chain, the uv `setup.sh` fix + rollout pair, the e2e-login 3-step chain, the
      PROGRESS.json rollout folding three families, the fleet-monitor pair, the launcher-write pair) — flip ALL the
      constituent boxes, not just one per todo, and say in each flip which combined todo covered it. The 17 source docs
      are: `/plans/archive/issues/setuptools_fleet_pysec_2026_3447_bump_2026_07_14.md` (ARCHIVED 2026-07-30 — already
      reconciled + archived independently, skip for this one), `/plans/archive/issues/uv_pin_fleet_drift_2026_06_22.md`,
      `issues/e2e_login_persona_handoff_helper_stale_2026_07_22.md`,
      `issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md`,
      `issues/vm_billing_waste_first_audit_and_preflight_gate_design_2026_07_24.md`,
      `issues/session_bound_vm_monitoring_reliability_gap_2026_07_26.md`,
      `utl_uac_reuse_consolidation_remediation_2026_06_10.md`, `issues/issue_docs_remediation_sweep_2026_06_02.md`,
      `codex_violations_ratchet_to_five_2026_06_10.md`, `repo_scripts_governance_audit_2026_06_18.md`,
      `issues/service_dockerfile_pattern_normalization_2026_06_17.md`, `codex_vs_repo_docs_ssot_audit_2026_06_01.md`,
      `issues/prod_terraform_drift_backlog_reconcile_2026_07_24.md`,
      `/plans/archive/issues/plan_hygiene_precommit_and_agentic_resolution_2026_06_10.md`,
      `l0_doc_index_generator_2026_06_24.md`, `issues/cve_affected_pinned_deps_remediation_2026_06_18.md`,
      `stash_pile_workspace_cleanup_2026_06_03.md`, `issues/reference_path_convention_2026_07_23.md`. (That list is 18
      entries because `session_bound_vm_monitoring_reliability_gap` co-sourced one combined todo with the billing-waste
      doc — reconcile both.) **Several of these carry `locked_by: live-defi-rollout`** — flipping a checkbox is fine on
      a locked doc; ARCHIVING one is not (that needs `[unlock-plan]`). **Done when**: every source-doc box corresponding
      to a done batch-1 todo is flipped with a verified sha, and any box that could NOT be flipped is listed with the
      reason. Repo: unified-trading-pm. **RESULT**: walked all 17 source docs (setuptools doc correctly skipped, already
      archived+reconciled). All shas re-verified via `git merge-base --is-ancestor` against `origin/live-defi-rollout`
      (2 shas — `execution-service@8479a77f`, `deployment-service@1e8af34a`'s sibling in an unrelated doc — turned out
      to be pre-quickmerge-rebase shas no longer resolving directly; confirmed via content-diff, per
      `agents/review.md`'s squash/rebase-ancestry gotcha, that the identical diff landed under a different current sha,
      so nothing was actually missing). **13 of 17 docs were ALREADY fully reconciled** by earlier passes (mostly the
      2026-08-08 na-eligibility-audit round7 sweep, which ran before this finalize todo was dispatched) —
      `uv_pin_fleet_drift`, `deployment_ui_smoke_failures`, `vm_billing_waste`, `utl_uac_reuse_consolidation` (now fully
      archived with operator `[unlock-plan]` sign-off), `issue_docs_remediation_sweep`, `repo_scripts_governance_audit`,
      `service_dockerfile_pattern_normalization`, `codex_vs_repo_docs_ssot_audit`, `prod_terraform_drift_backlog`,
      `plan_hygiene_precommit_and_agentic_resolution`, `cve_affected_pinned_deps_remediation`, and
      `stash_pile_workspace_cleanup` needed no edits. **4 docs got real fixes this pass**: `e2e_login_persona_handoff`
      (2 boxes flipped, `unified-trading-system-ui@15e4b4bc`), `codex_violations_ratchet_to_five` (added the missing
      `unified-trading-pm@a674e1ff3` ruff-ratchet-baseline citation to the deployment-api item),
      `l0_doc_index_generator` (2 boxes were genuinely still `[ ]` despite batch1 claiming them done — flipped, citing
      `agent-orchestrator@517a0bc` + `unified-trading-pm@54d7779a4`), `reference_path_convention` (replaced a literal
      `pm@<commit-pending>` placeholder with the real verified sha
      `unified-trading-pm@b555f4b86b76b2f6dfeb02c3bf3549d63b88fd19`). **One discrepancy found in this todo's own
      premise**: `session_bound_vm_monitoring_reliability_gap_2026_07_26.md` does NOT actually carry any content related
      to the "fleet-monitor pair" todo (checkpoint-reading blind spot / preemption-alert severity) — grepped the whole
      doc for `checkpoint|alert|read_progress|cdlap|DP_VM_PREEMPTED`, zero hits; its actual subject is a session-bound
      `ScheduleWakeup` monitoring-loop reliability question, unrelated. The "18 entries because session_bound
      co-sourced" framing above is incorrect — `vm_billing_waste_first_audit_and_preflight_gate_design_2026_07_24.md`
      alone fully self-sources that todo (already correctly `[x]` there, both halves, citing
      `deployment-service@b501a5e`). No box was flipped in `session_bound_vm_monitoring_reliability_gap` (none exists to
      flip); its own open items are unrelated pre-existing work, left untouched. **No box in any of the 17 docs could
      not be flipped for lack of a match** — every batch-1 todo's target checkbox was found in its named doc except the
      (nonexistent) one this discrepancy concerns.

- [x] ✅ **DONE 2026-08-09 (slot-24, review-craft-per-task).** Re-checked batch 1's 10 CONFLICT-GATED deferrals — the
      only category that clears without a ruling. For each, read the specific competing claim named in batch 1's
      `##     Deferred` and determined whether it has since shipped, been superseded, or otherwise resolved. **Verdicts
      (all dated 2026-08-09, evidence-cited, key shas re-verified via `git merge-base --is-ancestor` against
      `origin/live-defi-rollout`):**

      **(1) `PYTEST_UNIT_DIR` vs `mtds_ungated_test_families_2026_07_17.md` — ALREADY RESOLVED** (per this todo's own
          prior text, na-eligibility-audit ci tranche 2026-07-31): fixed, cefi's narrower approach won; doc archived, all 5
          todos done. No batch-2 candidate needed.

          **(2)+(3) the 4 `base-service.sh`/`base-library.sh` PM items (domain-client retarget, pip floor bump,
          cryptography/idna re-check, uv drift-guard) + the `0.10.8` constant move — CLEARED.** Both competing edits have
          landed: `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md`'s MP3 lint-generalization item is `[x]` ✅ DONE
          (STEP 5.104 added to `base-service.sh`, `unified-trading-pm@4d3713ade`, ancestor-verified);
          `tradfi_satellite_ao_dispatch_batch4_2026_07_26.md` is fully archived (its `base-library.sh` sentinel-contract
          touch shipped). Matches the independent 2026-08-08 na-eligibility-audit finding on `codex_violations_ratchet_to_five_2026_06_10.md`
          verbatim ("appears CLEARED"). **Batch-2 candidate**: bundle all 5 as ONE `sequential: true` unit (both files are a
          shared hotspot) per operator ruling `autonomous_session_operator_decisions_2026_07_25.md` entry #36 option A —
          source docs unnamed in the deferred text but findable via the 4 named fix categories.

          **(4) `DATA_PIPELINE_SERVICES` vs cross-cutting batch1 item (B) — RESOLVED BY LOGIC, already shipped (not merely
          cleared).** Fixed independently by `infra_satellite_ao_dispatch_batch5_2026_08_01.md`'s own G-UI gap item —
          `deployment-ui@fecd67c` (2026-08-06, ancestor-verified) replaced the stale `features-cefi/defi/tradfi/prediction-service`
          names with the current FOLD A family names and added the missing `strategy-service`/`ml-service` entries; live
          `DATA_PIPELINE_SERVICES` set confirmed current. No batch-2 candidate needed.

          **(5) `managed-by` launcher label standardization vs the wave-launcher terraform item in cross-cutting batch1b —
          CLEARED.** The competing item is `[x]` ✅ DONE, re-verified live 2026-08-01 (slot 11): the runtime-pin-vs-terraform-default
          split this item warned about no longer exists (`uts-prod-tradfi-wave-launcher`'s Cloud Run job resolves directly
          to `deployment-service:latest`), so a `tofu apply` is harmless — no contention remains on the Cloud-Run terraform
          side. **Batch-2 candidate**: `managed-by` launcher label standardization (`deployment-service/scripts/vm/launch-*.sh`),
          low value per the source doc (`launched_by` already answers "who launched this").

          **(6) repo_scripts DEPRECATE remediation vs cross-cutting batch1 item (k)'s ~60-script cloud-agnostic sweep —
          STILL-CONFLICTING.** Item (k)'s outer checkbox reads `[x]` in the archived doc, but a live grep
          (`grep -rl 'from google\.cloud import\|import boto3' --include='*.py' */scripts/`) still finds 113 files with
          direct cloud-SDK imports fleet-wide, and the most recent independent audit
          (`repo_scripts_governance_audit_2026_06_18.md`'s na-eligibility-audit round7 sweep, 2026-08-08) explicitly
          re-confirmed this item is "CONFLICT-GATED — re-confirmed still claimed by
          `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` item (k)". **Restated live competing claim for batch
          2**: item (k)'s checkbox is prematurely flipped relative to actual sweep completion; do not draft a competing
          todo — either wait for item (k)'s claim to be honestly closed out or file a stale-checkbox finding against the
          archived doc first.

          **(7) fastapi/starlette + pyarrow/twisted/mako/ujson dep work vs `workspace-constraints.toml` /
          `canonical-dependency-manifest.json` churn — PARTIALLY CLEARED.** The fastapi/starlette cap-lift half is DONE and
          shipped (`fleet_fastapi_upper_bound_stale_vs_utl_floor_bump_2026_07_28.md` archived `status: resolved`,
          "RATIFIED 2026-07-28 — direction A confirmed complete"; live `workspace-constraints.toml` shows
          `fastapi>=0.137.0`/`starlette>=1.3.1` with the `_IncludedRouter` fix noted). The ujson/twisted/msgpack pip-audit
          follow-ups are covered by `cve_affected_pinned_deps_remediation_2026_06_18.md` (active, `assigned_vm: planning`).
          **STILL-CONFLICTING residual**: pyarrow/mako are covered by NEITHER doc — confirmed via today's (2026-08-09)
          `codex_violations_ratchet_to_five_2026_06_10.md` Progress Log entry, which independently reached the same
          "genuinely blocked, pyarrow/mako uncovered" verdict same-day. **Restated live competing claim for batch 2**: the
          pyarrow 23.0.0→24.0.0 fix needs a coordinated PM canonical-cap widen (`workspace-constraints.toml:80` currently
          caps `<24.0.0`) plus the twisted 25.5.0→26.4.0 major-bump (via binance-futures-connector) and mako 1.3.12 in-range
          bump — genuinely unowned, no fresh todo drafted here per the "too large for a batch todo" finding already on
          record.

          **(8) MTDS >900-line tail (12 modules) vs cefi batch1 + defi batches 2/3/4's `market_interface/` edits —
          CLEARED.** All 4 named competing batches have shipped their `market_interface/` edits:
          `cefi_satellite_ao_dispatch_batch1_2026_07_25.md` archived; `defi_satellite_ao_dispatch_batch3_2026_07_26.md` and
          `defi_satellite_ao_dispatch_batch4_2026_07_26.md` both archived; `defi_satellite_ao_dispatch_batch2_2026_07_26.md`
          down to its 1 remaining open item (a KALSHI_PERP scope-audit gate, unrelated to `market_interface/`). Corpus-wide
          grep of `plans/active/*.md` found no other open checkbox touching `market_interface/` splitting work. **Batch-2
          candidate**: split the 12 named MTDS `market_interface/` modules currently over the 900-line soft tail, now with
          low collision risk.

          **(9) the corpus-wide sweeps (zero-checkbox sweep + reference-path `format_count`/`existence_count` baseline
          drains) vs the concurrent per-tranche reconcile/audit runs — STILL-CONFLICTING.** Both source docs remain open:
          `issues/zero_checkbox_sweep_all_tranches_2026_07_31.md` (`status: open`, 1 checkbox unresolved) and
          `reference_path_convention_2026_07_23_finalize_2026_08_08.md`/`issues/reference_path_convention_2026_07_23.md`
          (`status: active`/`open`, 3+4 open checkboxes). Per-tranche `/plan-reconcile` + `/ag-closeout-audit` +
          na-eligibility-audit runs are demonstrably still concurrently active as of TODAY (2026-08-09) — e.g. this same
          finalize session found a fresh 2026-08-09 na-eligibility-audit entry on `codex_violations_ratchet_to_five_2026_06_10.md`.
          **Restated live competing claim for batch 2**: do not draft a new whole-corpus multi-hundred-file sweep todo
          while daily per-tranche audits are still running; re-check once that cadence quiets.

          **(10) the two sports-doc line-cap splits vs sports batches 3 and 5 — PARTIALLY CLEARED, both sub-items resolved
          differently than anticipated.** (a) `sports_shard_enumeration_cartesian_blowup_2026_07_20.md` — CLOSED via a
          workaround, not a split: the blocked reference was repointed to the archive path without needing the split
          (`unified-trading-pm@ca9551fbc`, 2026-07-29, ancestor-verified; confirmed live by `reference_path_convention_2026_07_23.md`'s
          own 2026-08-03 na-eligibility-audit close). No batch-2 candidate needed. (b) `sports_satellite_ao_dispatch_batch2_2026_07_24.md`
          — the blocking condition changed: the doc is now itself ARCHIVED (`plans/archive/2026_07/`, 999 lines, no longer
          an active-plan touched-file), so `check_line_caps.sh`'s no-exceptions rule no longer applies the same way it did
          when the doc sat active at exactly 1000 lines. The reference-repoint fix itself (in
          `reference_path_convention_2026_07_23.md`) is still `[ ]` open — no evidence either sports batch 3 or 5 explicitly
          performed a split (grepped both for "split"/"1000"/"line-cap" against this doc, no hits). **Batch-2 candidate**:
          small, now-unblocked fix — repoint the stale `fss_bookmaker_dispersion_dead_code_overwrites_best_odds_2026_07_25.md`
          reference inside the archived `sports_satellite_ao_dispatch_batch2_2026_07_24.md` to its archive path (1 line of
          slack remains at 999/1000, so verify post-edit length before shipping).

          **Batch-2 candidate summary (7 items, in priority order)**: (2)+(3) base-service.sh/base-library.sh bundled unit
          [P2]; (8) MTDS >900-line market_interface/ split, 12 modules [P2]; (5) managed-by launcher label standardization,
          low value [P3]; (10b) sports batch2 doc reference repoint, 1-line-slack [P3]. **Still-conflicting, no todo
          drafted**: (6) repo_scripts DEPRECATE remediation (stale item-(k) checkbox); (7) pyarrow/mako dep-manifest
          residual; (9) corpus-wide sweeps (daily per-tranche audits still active). **Already resolved, no action**: (1)
          PYTEST_UNIT_DIR; (4) DATA_PIPELINE_SERVICES; (10a) sports blowup-doc reference.

- [ ] [REVIEW] P1. **Re-measure the infra tranche's orphan count and close the coverage-gap that made batch 1
      necessary.** Two parts. (a) Re-run the `/ag-closeout-audit infra` classification over the tranche's now-updated
      docs and report the new orphan count against the 2026-07-26 baseline of **29 orphaned of 34 tranche-primary docs**
      — the number should have dropped by roughly the number of source docs batch 1 fully closed, and any doc that did
      NOT move should be named with why (operator-gated / human-only / too-large is a legitimate answer; "still orphaned
      for no stated reason" is not). (b) Fix the structural cause: `infra_consolidated_closeout_2026_07_25.md` carries
      ZERO `- [ ]` todos and has no aggregated-sources sibling, so nothing in the infra covering set dispatches anything
      and every satellite doc is orphaned by construction. Either give the hub real todos for the work only it can own
      (its 4 Track close-out criteria), or add the `<ag>_consolidated_closeout_aggregated_sources_*` sibling the 5 AGs
      have so the digest role is explicit and separate — and state which model was chosen and why. Also register the two
      tranche members that were NOT in the hub's Sources list when this audit ran
      (`issues/session_bound_vm_monitoring_reliability_gap_2026_07_26.md` and
      `issues/infra_plan_reconcile_parked_decisions_2026_07_26.md`) using proper `[text](path)` markdown links, not bare
      backticked filenames — prettier can wrap a long bare filename across a line break and silently break the substring
      match `scripts/plan-hygiene/check_ag_closeout_linkage.py` relies on. Then run that linkage check. **Done when**:
      the new orphan count is reported with per-doc reasons for anything that did not move,
      `check_ag_closeout_linkage.py` reports 0 orphans, and the hub's dispatch-vs-digest model is explicitly stated in
      the hub itself. Repo: unified-trading-pm.

- [ ] [DOCS] P2. **Archive batch 1 per the 6-step ritual, and only then.** In order: (1) migrate every still-open
      Deferred item out of batch 1 into a real home — a batch-2 plan for the cleared conflicts, the reconcile register
      `issues/infra_plan_reconcile_parked_decisions_2026_07_26.md` for the operator-gated ones (append them in the same
      structured question+options+recommendation format the existing 6 use), and a named standalone-plan todo for the
      too-large ones (`artifact_pipeline_observability`, the 20-repo codex-vs-repo-docs sweep, the schema-provenance
      migration) — **nothing may be lost to archival**; (2) add the archival banner + set `status: superseded` with
      `superseded_by:` pointing at the batch-2 plan if one was created; (3) run the codex-alignment check against the
      SSOTs batch 1 cites; (4) update CLAUDE.md / codex if any batch-1 todo established a NEW durable contract (the
      PROGRESS.json launcher-conformance list and the plan-hygiene runtime retirement both plausibly do); (5) **update
      every referrer's path corpus-wide** — grep for `infra_satellite_ao_dispatch_batch1_2026_07_26` and repoint each
      hit to the archived path, using leading-slash repo-root-relative form (this is the step the pre-2026-07-23 5-step
      ritual never named, and the exact gap that produced three separate dangling-reference regressions on 2026-07-25);
      (6) clear the lock (batch 1 has none, so this is a no-op — confirm rather than assume). Then physically move it
      under `plans/archive/2026_07/`. **Done when**: `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci --no-regen` is
      0 hard, `python3 scripts/plan-hygiene/check_reference_paths.py` shows no NEW dangling reference above its
      baseline, and `.venv/bin/python scripts/plans/regenerate_active_plan_inventory.py` reports 0 orphans. Repo:
      unified-trading-pm.

## Why this finalize plan looks different from the AG ones

The 5 asset groups' finalize plans reconcile satellite docs against a closeout hub that itself carries real dispatchable
todos. Infra's hub carries none, which is why todo 3(b) above exists at all: without fixing the hub's dispatch-vs-digest
ambiguity, the next `/ag-closeout-audit infra` run would re-derive the same "everything is orphaned by construction"
verdict no matter how much batch 1 shipped. Reconciling the checkboxes without closing that structural gap would make
the orphan count look better while leaving the mechanism that produced it untouched.

## Codex SSOTs

`/codex/11-project-management/` (findings triage, archival ritual, issue-doc lifecycle) ·
`/codex/11-project-management/cross-reference-path-convention.md` · `plans/PLAN_FORMAT.md` (`status: draft` semantics) ·
`plans/active/task_template.md` §4 (finalize-plan-coverage rule)

## Progress Log

- **2026-07-26** — Drafted alongside `infra_satellite_ao_dispatch_batch1_2026_07_26.md` by `/ag-closeout-audit infra`
  (Autonomous mode). Left `status: draft` — flips to `active` only with its parent, on explicit operator approval.
- **2026-08-09 (slot-3)** — Worked todo 1 (reconcile all 17 source docs). Fanned out 17 parallel sub-agents (one per
  doc, read+edit only, no git writes, to avoid a shared-index race in one slot clone). 13/17 docs were already fully
  reconciled by earlier passes (mostly the 2026-08-08 na-eligibility-audit round7 sweep); 4 got real fixes
  (`e2e_login_persona_handoff_helper_stale`, `codex_violations_ratchet_to_five`, `l0_doc_index_generator` — 2 boxes that
  were genuinely still open despite batch1 claiming them done, `reference_path_convention` — a stale
  `pm@<commit-pending>` placeholder replaced with the real verified sha). Found and recorded one discrepancy in this
  todo's own premise: `session_bound_vm_monitoring_reliability_gap_2026_07_26.md` does not actually co-source the
  fleet-monitor-pair todo as claimed (zero related content) —
  `vm_billing_waste_first_audit_and_preflight_gate_design_2026_07_24.md` alone fully sources it. Full detail in the
  todo's own RESULT note above. Todo 1 done; todos 2-4 remain (this plan is `sequential: true`, so todo 2 unblocks
  next).
- **2026-08-09 (slot-24, review-craft-per-task)** — Worked todo 2 (re-check the 10 CONFLICT-GATED deferrals). 4 CLEARED
  outright (2+3, 5, 8) + 1 already resolved-by-logic/shipped (4) + 1 partially cleared with a small residual (10) + 3
  STILL-CONFLICTING with the live claim restated for batch 2 (6, 7-residual, 9). Wrote up a 4-item batch-2 candidate
  list in priority order. Todo 2 done; todos 3-4 remain (`sequential: true`, so todo 3 unblocks next).
- **context-scout 2026-08-03**: re-scouted; context_scope refreshed (6 entries) — finalize gate, code-free by design.
