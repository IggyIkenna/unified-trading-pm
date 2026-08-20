---
doc_type: plan
title: AO-dispatch plan corpus sweep — separate operator-gated items from worker-dispatchable todos
summary: >-
  Retroactive corpus-wide sweep enforcing `task_template.md` §3 finding Y (2026-08-16): no `assigned_vm: planning`
  plan should carry an `[OPERATOR]`/`BLOCKED-<TOKEN>`-tagged item (credentials, live-trading validation, data-
  completeness sign-off, account/vendor signups, design/investigation judgment calls, post-audit human
  conflict-resolution rulings) interleaved with plain worker-dispatchable todos in the same file. Builds a soft-flag
  mechanical check, runs it corpus-wide (~183 `assigned_vm: planning` active plans), then per-epic-group classifies and
  forks each genuine hit into a companion NA doc — freeing the AO plan to reach zero-open-todos and archive
  independently of the human-gated item's resolution. **The `orchestrator_master` (ao-topic) group is handled directly
  by `ao_open_work_consolidated_tracker_2026_08_14.md`'s own new Track 7, not here** (2026-08-16 merge — see that
  doc's Notes) — this sweep covers the other 9 non-ao epic groups.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    ao,
    ao-dispatch,
    plan-hygiene,
    operator-purity,
    na-eligibility,
    corpus-sweep,
    task_template,
  ]
related:
  [
    /plans/active/task_template.md,
    /plans/active/ao_satellite_ao_dispatch_batch21_2026_08_16.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-19"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
assigned_role: infra
effort: high
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/task_template.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    scripts/plan-hygiene/check_delete_vm_launch_gating.sh,
    scripts/plan-hygiene/check_na_corpus_ratchet.py,
  ]
source: >-
  Operator directive 2026-08-16 — go through the PM repo's plan corpus and force AO-dispatched plans to separate
  operator-blocking items (credentials, live-trading validation, data-completeness validation, account signups,
  design/investigation, human conflict-resolution after audits) into their own docs, so a plan's only remaining reason
  to stay open is a real inter-task dependency, never a human-gated item sitting in the same file. Operator confirmed
  this sweep itself is a LOCAL plan (per-doc classification is a judgment call, same bar as `/na-eligibility-audit`'s
  own KEEP-NA-vs-RECLASSIFY split), not AO-dispatched.
---

# AO-dispatch plan corpus sweep — separate operator-gated items from worker-dispatchable todos

> **LOCAL / human plan** (`assigned_vm: NA`) — never auto-dispatched. Per-doc classification here is the same kind of
> judgment call `/na-eligibility-audit` already runs, not bounded AO-dispatch work. Run incrementally by
> tranche/topic, mirroring `/na-eligibility-audit`'s and `/ag-closeout-audit`'s tranche pattern — do not attempt all
> ~183 candidate docs in one pass.

## Why this plan exists

Companion durable rule: `task_template.md` §3 finding Y (2026-08-16) — going forward, an AO-dispatched plan must not
mix an operator-gated item into the same file as its dispatchable todos. That rule only governs NEW authoring. This
plan remediates the EXISTING corpus: a scoped sample of ~30 `assigned_vm: planning`, `status: active` plans (out of
~183 candidates) found ~12 with a genuine open `[OPERATOR]`/`BLOCKED-OPERATOR` checkbox sitting alongside plain,
already-or-still-dispatchable todos — e.g. `sports_predictions_live_mode_activation_readiness_2026_07_21.md` (a
`[REVIEW]` todo immediately followed by an `[OPERATOR]` real-money live-trading go-ahead),
`defi_operator_ruling_ao_dispatch_2026_08_15.md` (an `[OPERATOR]` reconcile-before-delete ruling sandwiched between
two plain `[DATA]` todos), `cross_ag_live_capture_parity_2026_08_14.md` (three separate `[OPERATOR]` rulings
interleaved among build/fix todos), `deployment_api_unauthenticated_prod_p0_2026_08_10.md` (an `[OPERATOR]` live-fire
prod test following plain verification todos). Extrapolated hit rate: **roughly 30-60+ plans** likely need this
treatment corpus-wide.

**What "separate" means per plan** (task_template.md §3 finding Y): fork the operator-gated item out into a companion
`assigned_vm: NA` doc (a sibling `<slug>_operator_items_<date>.md`, or fold into an existing NA tracker for the same
topic), cross-link both directions via `related:`. This is NOT a delete/downgrade of the operator item — it stays
tracked, just no longer blocking the AO plan's own archival or reading as "why is this blocked" to a corpus skim.

## Phase 0 — build the mechanical soft-flag tool

- [ ] [SCRIPT] P1. Write `scripts/plan-hygiene/check_ao_plan_operator_purity.sh` (or `.py`, match the sibling
      `check_delete_vm_launch_gating.sh` shape/output format): for every `plans/active/*.md` with
      `assigned_vm: planning` + `status: active`, flag the file if it contains BOTH (a) an open `- [ ]` line carrying
      `[OPERATOR]`, `BLOCKED-CREDENTIALS`, `BLOCKED-OPERATOR-DECISION`, `BLOCKED-UPSTREAM-OUTAGE`,
      `BLOCKED-OPERATOR`, or `BLOCKED-INFRA`, AND (b) at least one other open `- [ ]` line WITHOUT any of those
      markers. **Soft flag only** (WARN, not FAIL) — per finding U, an `[OPERATOR]` tag can be a correct, standing
      ruling-citation rather than a live ask; a human/skill pass judges each hit for real, same division of labor as
      `check_delete_vm_launch_gating.sh` vs. `/plan-reconcile`'s AO-dispatch-readiness hunter. Wire into
      `run_hygiene_sweep.sh` alongside the other soft-flag checks. Done-when: the script runs clean against the
      current corpus and produces a file-list + per-file hit-count, cited in this plan's Progress Log.

## Phase 1 — corpus-wide triage report

- [ ] [SCRIPT] P1. Run the Phase-0 script against the full `plans/active/*.md` corpus (excluding `issues/`) and
      publish the complete candidate list with hit-counts (superset of the ~183-plan `assigned_vm: planning`
      population). Group by `parent_epic` (per
      `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §2 — the clean grouping axis, not
      `asset_group`). Cite the full list + counts in this plan's Progress Log; this becomes the incremental work
      queue for Phases 2+.

## Phase 2+ — per-epic-group classification and split (incremental, one group per pass)

> Run one `parent_epic` group at a time (mirrors `/na-eligibility-audit`'s tranche-by-tranche incremental mode — do
> not attempt the whole corpus in one sitting). For each flagged doc in the group:
>
> 1. Read the whole doc (not just the flagged lines) — confirm the operator item is genuine (finding U's 3-part test:
>    business/spend judgment, credential-only access, or a failed-reversibility delete) and not itself
>    mis-tagged (if mis-tagged, that's a separate `/plan-reconcile`-style fix — untag it instead of forking it out).
> 2. If genuine: fork it into a companion `assigned_vm: NA` doc (new sibling file, or fold into an existing NA
>    tracker for the same topic if one already exists — grep first, don't create a duplicate tracker). Cross-link
>    `related:` both directions. Remove the operator item's checkbox line from the AO plan, replacing it with a
>    one-line pointer to the companion doc (mirrors the "digest line" bold-no-brackets convention, `task_template.md`
>    §3 finding H).
> 3. If the AO plan now has zero remaining open todos as a result, run the standard 6-step archival ritual on it
>    immediately (don't leave a fully-done AO plan open just because this sweep hasn't finished every group).
> 4. Update the Phase-0 script's baseline/ratchet (once wired, Phase 4) only after the group's forks are committed.

- [ ] [PM] P2. **Group: cefi-related epics** — same treatment.
- [ ] [PM] P2. **Group: defi-related epics** — same treatment (start with the 3 named examples above:
      `defi_operator_ruling_ao_dispatch_2026_08_15.md`, `cross_ag_live_capture_parity_2026_08_14.md`).
- [ ] [PM] P2. **Group: tradfi-related epics** — same treatment.
- [ ] [PM] P2. **Group: sports-related epics** — same treatment (start with
      `sports_predictions_live_mode_activation_readiness_2026_07_21.md`).
- [ ] [PM] P2. **Group: prediction-related epics** — same treatment.
- [ ] [PM] P2. **Group: cross-cutting / infra / ci / ui epics** — same treatment (start with
      `deployment_api_unauthenticated_prod_p0_2026_08_10.md`).
- [ ] [PM] P2. **Remaining epics not covered above** — re-run Phase 1's grouped report to confirm nothing was missed
      before closing this phase; classify + fork any stragglers.

## Phase 3 — verify and wire the ratchet

- [ ] [SCRIPT] P1. Re-run the Phase-0 script corpus-wide. **Done when**: either zero hits remain, or every remaining
      hit is explicitly justified inline (a standing operator-ruling citation per finding U, not a live ask) — write
      the disposition for each remaining hit into this plan's Progress Log.
- [ ] [INFRA] P1. Promote the Phase-0 script from soft-flag-only to a HARD, shrinking-ratchet gate (mirror
      `check_na_corpus_ratchet.py`'s baseline pattern) once the corpus is clean — a NEW plan authored with a mixed
      operator item going forward should fail `run_hygiene_sweep.sh`, not just warn. Write
      `scripts/plan-hygiene/ao_plan_operator_purity_baseline.yaml` at the post-sweep hit count (0, ideally) and wire
      it into the sweep script's `--ci` mode.
- [ ] [DOC] P0. **Archive this plan** once every group above is done and the ratchet is wired — 6-step ritual, corpus
      referrer fixups, inventory regen.

## Codex SSOTs (read before starting)

`/plans/active/task_template.md` §3 finding Y, `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`,
`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`,
`/codex/12-agent-workflow/commit-push-flip-rule.md`.

## Progress Log

- **context-scout 2026-08-19**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **2026-08-16 (interactive session, operator directive)**: Authored per the operator's request to force AO plans to
  separate operator-blocking items (credentials, live-trading validation, data-completeness validation, account
  signups, design/investigation, post-audit human conflict-resolution) from worker-dispatchable todos, so dispatching
  the AO backlog runs into blocks only from real inter-task dependencies, never a mixed-in human-gated item. Companion
  durable rule shipped in the same session: `task_template.md` §3 finding Y. Scoping numbers (183 candidates, ~12/30
  sampled hits, 4 concrete examples) come from a same-session Explore-agent research pass, not a full corpus run —
  Phase 1 replaces this estimate with the real complete list.
- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:1a4a951d09a2ddd0]: KEEP-NA, valid — explicit operator ruling on record that per-doc classification in this sweep is itself the judgment-call deliverable, not AO-dispatchable, even though individual Phase-0/1/3 tooling todos are mechanical in isolation.

- **na-eligibility-audit 2026-08-19 (ao tranche)** [body-hash:5e353e515fd43619]: KEEP-NA, valid — frontmatter source: cites an explicit dated operator ruling that this sweep itself is a LOCAL plan (per-doc classification is a judgment call); converges with the 2026-08-17 na-eligibility-audit verdict on the same citation. 4 Phase-0/1/3 tooling todos look mechanical in isolation, tagged MISCLASSIFIED_LIKELY_AO_ELIGIBLE for next-run reassessment, but the doc-level ruling covers the whole doc regardless.
