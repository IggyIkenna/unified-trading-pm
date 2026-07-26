---
doc_type: issue
title: Parked operator decisions from the 2026-07-26 /plan-reconcile run, topic-scoped to the infra tranche
summary: >-
  Six BLOCKED-OPERATOR-DECISION items parked by the autonomous `/plan-reconcile --autonomous` pass scoped to the infra
  tranche (`infra_consolidated_closeout_2026_07_25.md`'s Sources). Every mechanically-provable finding in that pass was
  auto-fixed and shipped instead of parked; these six are the residue the evidence genuinely cannot settle — authority
  calls (which fix shape to build, whether to deprecate a doc), preference calls (where a near-complete plan's remnant
  lives), and one standing question that has blocked a whole close-out track for seven weeks. Each entry follows the
  SUB_AGENT_MANDATORY_RULES.md escalation format: both sides quoted with path:line, why they conflict, options A/B/C
  with the recommendation marked [WORKER REC]. Operator: answer inline under each entry; unanswered entries stay open.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, deployment-service, e2e-testing, execution-service]
scope: [engineer, admin]
tags: [plan-reconcile, operator-decision, infra, plan-hygiene, autonomous]
related:
  [
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/active/issues/vm_startup_scripts_no_auto_rollout_to_gcs_2026_07_19.md,
    /plans/active/issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md,
    /plans/active/issues/plan_reconciler_doc_hygiene_findings_2026_06_17.md,
    /plans/active/stash_pile_workspace_cleanup_2026_06_03.md,
    /plans/active/org_migration_to_odumresearch_2026_06_07.md,
    /plans/active/issues/plan_quality_four_line_defense_architecture_2026_07_23.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  `/plan-reconcile` run 2026-07-26, autonomous mode (operator away, unreachable), topic-scoped to the `infra` tranche
  per the skill's "Topic-scoped (sharded) runs" section.
depends_on: []
---

# Infra `/plan-reconcile` 2026-07-26 — parked operator decisions

> **Why parked, not asked**: the operator was away and unreachable for the whole run. Per the skill's ASK > PARK rule,
> parking is strictly worse than asking — if you are reading this and the operator is reachable, ask these directly
> rather than waiting on the doc. Everything the evidence could settle was auto-fixed in the same pass and is listed in
> `/plans/active/infra_consolidated_closeout_2026_07_25.md`'s 2026-07-26 Progress Log entry.

---

## 1. Which durable fix for VM startup/helper scripts not auto-rolling out to GCS? (P1)

`/plans/active/issues/vm_startup_scripts_no_auto_rollout_to_gcs_2026_07_19.md:81-89` states three fix shapes under the
heading **"Fix options (for operator decision)"** and picks none. The doc is `priority: P1`, `status: open`, and had
**zero checkboxes** until this pass added an `[OPERATOR]`-gated capture todo — so for 7 days its only P1 work was
invisible to every hygiene and dispatch surface.

The gap is real and measured by the doc itself (`:65-70`): "The GCS copy of `setup-data-pipeline-vm.sh` had `0`
occurrences of the new `_FANOUT` code… `deployment_heartbeat.py` **68 diff lines behind git**". The counter-fact that
makes this a choice rather than an emergency is at `:93-95`: "All GCS-hosted `vm/` scripts were re-synced to git HEAD on
2026-07-19… So the fleet is currently in sync; the open work is the DURABLE fix so it stays in sync automatically."

A: **Option 1 — a CI job triggered on changes under `deployment-service/scripts/vm/` that `gsutil cp`s the changed
files.** The doc's own words: "Smallest blast radius". It closes the gap at the ship boundary where the drift is
created, needs no launcher changes, and cannot silently no-op the way a per-launcher check can. [WORKER REC] B: Option 2
— give each launcher a freshness check mirroring `lc_verify_tarball_freshness` (the doc: "More robust but more code");
correct-by-construction at launch, but every launcher must adopt it or the guarantee is partial. C: Option 3 only —
document the manual `create-code-tarballs.sh` step as a HARD post-change requirement in the ship checklist. The doc
calls this "the minimum until (1) or (2) lands", i.e. explicitly not a durable fix; choosing it means accepting process
discipline as the control. Other: operator can type a custom answer

**Status**: open

---

## 2. Fold the aiohttp doc's last open todo into the execution-service holdout doc and close it? (P2)

Two infra-tranche issue docs are each **near-complete with exactly 1 open todo**, and it is provably the _same_ work.

`/plans/active/issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md:216-222` (its sole remaining `- [ ]`): "**The
only remaining scope of this item is the execution-service holdout** (still pinned to 3.13.5 via
`[tool.uv] override-dependencies`, retaining both ignore-vulns) — tracked by
`execution_service_aioresponses_to_adapter_mock_migration_2026_06_23.md`. Left unchecked (not flipped) because that
holdout migration has not shipped yet."

`/plans/active/issues/execution_service_aioresponses_to_adapter_mock_migration_2026_06_23.md:72-79` (its sole remaining
`- [ ]`) already owns exactly that: "migrate the 8 `aioresponses` test files… Then **remove the
`aiohttp>=3.13.4,<3.14.0` line from execution-service's `[tool.uv] override-dependencies`**… and **drop the 11 aiohttp
`--ignore-vuln` entries**".

So the aiohttp doc is dual-tracking a todo whose implementation lives entirely in the sibling. Per the skill's
near-complete rule, **where live work lives is a planning decision** — never auto-folded. Note `aiohttp_cve_…` also
carries `locked_by: live-defi-rollout`, which independently blocks autonomous archival.

A: **Fold + close**: rewrite the aiohttp doc's residual todo as a pointer only (no `- [ ]`), flip it `[x]` as
"superseded — scope owned by `execution_service_aioresponses_…`", set `status: resolved` +
`resolved_by: execution_service_aioresponses_to_adapter_mock_migration_2026_06_23.md`, `[unlock-plan]`, and archive. The
execution-service doc becomes the single owner, and its todo already spells out dropping the ignore-vulns, so nothing is
lost. [WORKER REC] B: Leave both open — the aiohttp doc is the fleet-level record of the CVE cluster and its open
checkbox is a deliberate "the fleet is not clean yet" signal; closing it could read as "aiohttp CVEs resolved" when one
repo still carries 11 of them. C: Fold in the other direction — keep the aiohttp doc as the owner and reduce the
execution-service doc to a pointer (rejected by this worker: the actual work is 8 execution-service test files, so the
execution-service doc is the natural home). Other: operator can type a custom answer

**Status**: open

---

## 3. Deprecate `plans/active/INDEX.md`, or build it a regenerator? (P3)

`/plans/active/issues/plan_reconciler_doc_hygiene_findings_2026_06_17.md`'s Finding 2 has been open since 2026-06-17
with its own text saying "**Operator call**". This pass re-measured every number in it (all three were stale; corrected
in place) and the finding got **stronger**, not weaker:

- `plans/active/INDEX.md:1` still self-describes as "**Active Plans Index**" / "the canonical index of all active
  plans", still hand-maintained, still has no regenerator (only read-only checkers touch it).
- `bash scripts/plan-hygiene/build_health_digest.sh` → `INDEX drift 226` (measured 2026-07-26, against 224 active
  plans). It was **99** when the finding was filed — the drift has more than doubled.
- The competing index is auto-regenerated twice daily and its host has _moved_:
  `scripts/plans/regenerate_active_plan_inventory.py:38` →
  `MASTER_FILE = PLANS_DIR / "active_plan_inventory_dashboard_2026_07_24.md"`.

A: **Deprecate INDEX.md** — add a `> **SUPERSEDED by /plans/active/active_plan_inventory_dashboard_2026_07_24.md**`
banner, drop it from `build_health_digest.sh`'s drift check, and stop the recurring red. The auto-regenerated inventory
already occupies the canonical-index role, so INDEX.md's self-description is the thing that is wrong. [WORKER REC] B:
Build a regenerator for INDEX.md and reconcile the 226-entry drift — only worth it if INDEX.md carries a view the
auto-inventory does not (it is grouped/annotated by theme, which the generated table is not); otherwise this is a second
generator maintaining a second index. C: Leave as-is and mute the digest check — cheapest, but keeps a doc that actively
lies to readers about being canonical. Other: operator can type a custom answer

**Status**: open

---

## 4. Re-target or retire `stash_pile_workspace_cleanup`'s Phase-3 fan-out to retired per-epic VMs? (P3)

`/plans/active/stash_pile_workspace_cleanup_2026_06_03.md:145-156` still dispatches **10 of its 17 open todos** to named
per-epic VMs: "Run stash audit + conservative sweep on **vm-defi**… **vm-cefi**… **vm-tradfi**… **vm-sports**…
**vm-prediction**… **vm-ml**… **vm-trading-core**… **vm-operator-ops**… **vm-cross-cutting**… **vm-orchestrator**".

The same doc already carries the contradiction, annotated at `:134-143`: "`cursor-configs/CLAUDE.md` system map states
the per-epic-VM topology was retired — 'N slot workers, role-based dispatch (no per-epic VMs; single-VM architecture
2026-06-27)'… A dispatcher should instead run the sweep per SLOT on the current fleet… **Annotation only — the todo list
below is left as-is (no re-targeting performed in this pass; re-scoping the fan-out is a judgment call, not a mechanical
sync).**" Phase 4 (`:160-162`) has the same problem in a different shape: "inherit-and-commit (`chore(orphan-wip)` onto
its own `tab/<op>/<N>` branch)" — the `tab/<op>/N` branch model is likewise RETIRED.

A prior reconcile pass explicitly declined to fix this mechanically, so it is re-surfaced rather than re-decided: as
written, 10 of this plan's todos can never complete, which permanently pins it at 1/18.

A: **Re-target to the current topology** — replace the 10 `vm-*` rows with one per real host in the current fleet (the
central orchestrator VM, the human-planning VM, and the two operator laptops), and rewrite Phase 4's inherit-and-commit
step to "commit onto the slot's own `live-defi-rollout` checkout, liveness-gated per the HARD RULE" per
`/codex/05-infrastructure/per-tab-worktrees.md`. [WORKER REC] B: Retire Phase 3 entirely — mark the 10 rows VOID ("the
hosts they name no longer exist") and keep only the still-real laptop/VM sweeps, accepting that historical epic-VM
stashes are gone with their instances anyway. C: Leave as-is — the sweep is P3 and the pile may be a non-issue on the
current fleet; a fresh `git stash list` census across live hosts should come first and decide whether the plan is worth
re-scoping at all. Other: operator can type a custom answer

**Status**: open

---

## 5. `org_migration_to_odumresearch` — still wanted, or formally abandon? (P2, standing since 2026-06-07)

This is the single item blocking half of this tranche's Track 2 close-out criterion
(`/plans/active/infra_consolidated_closeout_2026_07_25.md:106-108`: "org migration fully verified fleet-wide (no stale
`IggyIkenna` refs)"). `/plans/active/org_migration_to_odumresearch_2026_06_07.md` is `status: paused` with **0 of 27
todos done** and no Progress Log entry since 2026-06-07 — seven weeks.

Its own banner (`:45-53`) already asked and never got an answer: "**⚠️ 2026-06-07 MAJOR UPDATE — the rulesets
justification is GONE; migration is now OPTIONAL/low-priority.** … **Decision pending operator:** still want the org for
those, or keep everything under `IggyIkenna`/Pro (which now fully supports fleet rulesets)?" The 2026-07-12 sync note
(`:55-58`) only recorded the stall: "frontmatter `status: active` → `paused`… 0/27 todos executed since the 2026-06-07
pending-operator-decision note above… Un-pause when the operator rules on org-vs-stay-on-Pro."

This is not a new finding — it is a standing condition being re-surfaced because a close-out track cannot close while it
sits unanswered, and nothing has re-asked it in seven weeks.

A: **Formally abandon + archive** — the plan's own analysis says the only hard driver (AO branch-protection rulesets) is
gone and everything remaining is "nice-to-have, not unblock". Archive it with a
`> **ABANDONED — org migration not pursued (operator ruling <date>)**` banner and rewrite Track 2's close-out criterion
to drop the org-migration clause, unblocking the track. [WORKER REC] B: Keep paused, but set an explicit review date in
the frontmatter so it stops silently blocking Track 2 — and amend Track 2's criterion to "org migration is either
executed or formally abandoned" so the track can close either way. C: Un-pause and schedule the cut — still wanted for
org secrets / team access / bus-factor; if so it needs a cutover window and Phase 0's CI/CD-drain precondition
re-verified against `/plans/active/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md` first (per the plan's own 2026-07-14
finding-92 note). Other: operator can type a custom answer

**Status**: open

---

## 6. Does the prek hard-gate satisfy "line 2", or must the full sweep be wired into `quality-gates.sh`? (P1)

This is the authority half of a contradiction this pass auto-corrected the factual half of.

`/plans/active/issues/plan_quality_four_line_defense_architecture_2026_07_23.md` § "The four lines of defense" item 2
defines line 2 as: "wire the FULL sweep (**not just `--precommit`'s 3 local checks**) into `quality-gates.sh` for the
`unified-trading-pm` repo specifically… so a plan/codex-touching change cannot land without the full hygiene sweep
passing — not just the fast pre-commit subset."

Its final `- [ ]` todo asserts the opposite in its own UPDATE: "**line 2 IS NOW LIVE** — a concurrent session shipped
`pm@0bba96586` ('flip check_line_caps.sh from advisory to a real hard gate')… **All 4 lines are now confirmed live**".

Measured 2026-07-26: `grep -n run_hygiene_sweep scripts/quality-gates.sh` → **no hits** — the same command and the same
empty result the todo itself cites earlier as proof line 2 is NOT wired. What actually shipped is one more check inside
the prek `--precommit` path, which is precisely the subset item 2 calls insufficient. The factual correction is applied;
what evidence cannot settle is which definition of line 2 the workspace actually wants.

A: **Keep the original definition — wire the full `run_hygiene_sweep.sh --ci` into PM's `quality-gates.sh`**, and leave
the acceptance-test todo open until it is. Line 2's whole purpose is catching what a staged-files gate structurally
cannot see (corpus-wide drift a commit did not touch). [WORKER REC] B: **Ratify the narrower definition** — declare the
prek hard-gate sufficient for line 2, rewrite item 2 to describe what actually shipped, and let the acceptance-test todo
close. Cheaper and already live, but it permanently gives up corpus-wide commit-time enforcement. C: Split — wire the
full sweep in `--ci` (advisory) now and hard-fail only once its prerequisite (over-cap plans) is at zero, keeping the
staged gate hard in the meantime. Other: operator can type a custom answer

**Status**: open
