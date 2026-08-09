---
doc_type: issue
title: "plan_reconciler daily deep reconciliation run — infra tranche, 2026-08-09"
summary: >-
  Run-findings doc for plan_reconciler dispatch agt-a398c9 (slot 12, 2026-08-09), sharded to the `infrastructure` topic
  tranche per the 2026-08-06 sharded-cadence ruling. Corpus: 66 asset_group:infrastructure-tagged docs (~1.8MB) across
  plans/active + plans/active/issues + 1 epic (infrastructure_master); 23 of 66 (35%) are in the 12h grace window and
  read-only this run, leaving 43 non-grace docs as the actionable set.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, reconciliation, plan-hygiene, findings, scheduled, infrastructure]
related: []
created: "2026-08-09"
parent_epic: plan_hygiene_master
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.4
assigned_role: review
assigned_vm: planning
execution_scope: orchestrator-agent
locked_by: plan_reconciler
locked_since: "2026-08-09"
supersedes:
superseded_by:
resolved_by:
source: "slot 12, plan_reconciler agt-a398c9, 2026-08-09"
context_scope:
  [
    unified-trading-pm/scripts/plan-hygiene/run_hygiene_sweep.sh,
    unified-trading-pm/scripts/plan-hygiene/check_archive_candidates.sh,
    unified-trading-pm/agents/plan_reconciler.md,
    unified-trading-pm/cursor-configs/skills/plan-reconcile/SKILL.md,
  ]
drift_direction: advance-code
depends_on: []
---

# plan_reconciler run — 2026-08-09 (agt-a398c9, infrastructure tranche)

## Scope + method

- `TRANCHE=infra` supplied → topic-scoped to `asset_group: infrastructure` (the frontmatter enum value; CLI/skill name
  is `infra`). Population = `rg -l '^asset_group:.*\binfrastructure\b' plans/active/ plans/epics/` (deduped —
  `plans/active/issues/` is a subdirectory of `plans/active/`, passing both double-counts) = **66 docs** (40 issues, 25
  active plans, 1 epic hub `infrastructure_master.md`), ~1.8MB total.
- Normative refs (`PLAN_FORMAT.md`, `task_template.md`, `INDEX.md`, `ACTIVE_INDEX.md`) and codex stay in scope per the
  SKILL's corpus-wide-every-shard rule.
- Grace set (newest commit <12h old at run start, ~2026-08-09 03:15 UTC): **23 of 66 (35%)**. Read-only context this
  run. Non-grace actionable set: **43 docs**.
- Per-epic breakdown (infra-tagged subset): `infrastructure_master` 46 docs/1.21MB, `agent_operating_framework_master`
  10/258KB, `plan_hygiene_master` 5/168KB, `observability_master` 2/41KB, `sports_master` 1/9KB (cross-tagged),
  `orchestrator_master` 1/4KB, epic-hub-self 1/72KB.
- Hunter batching: `infrastructure_master`'s 46 docs split into 4 size-balanced (~300KB) epic-cluster batches + 1
  cross-batch reconciler; the 5 smaller epics combined into 2 more epic-cluster batches; 3 topic hunters
  (CI/CD+quality-gates+workflow-templates; VM/SPOT+buckets/IAM+billing-waste+host-disk; AO-dispatch-batch +
  NA/plan-hygiene-tooling consistency); 1 combined mechanical-adjudicator/AO-readiness/zero-checkbox hunter.
  Codex-alignment, missed-flip, hedge-pointer, and prose-structural-integrity checks are folded into each epic-cluster
  hunter's per-doc checklist (piggyback, per SKILL.md item 7/8) rather than run as separate agents.
- `run_hygiene_sweep.sh --ci` ran very slowly (host load avg ~61 on 8 cores — many concurrent slots running similar
  plan-hygiene scans) — folded in whatever it completed before this run needed to proceed; noted where its output was
  incomplete.

## Flips verified

1. **`shared_ci_workflow_repo_extraction_2026_08_06.md` todo 3** (image-build-gate.yml managed-set gap) — HARD-verified:
   the script processes every `*.yml`/`*.yml.tmpl` in `scripts/workflow-templates/` via directory glob (no hardcoded
   list) and the file already exists there (added as a side effect of todo 18's emergency fix,
   `unified-trading-pm@a2feeb4de1`). unified-trading-pm@3847c97ff.
2. **`infra_satellite_ao_dispatch_batch6_finalize_2026_08_02.md` todo 3** (archive batch6) — both prerequisite todos
   confirmed `[x]` with hard evidence; flipped + executed. unified-trading-pm@f1adf67ef.
3. **`client_reporting_api_promote_wedge_backmerge_dead_2026_08_06.md`** — 4 new todos (converted from zero-checkbox
   prose) filed and immediately closed with live 2026-08-09 re-verification: `gh pr view 646` CLOSED (not merged, no
   open replacement), `main-backmerge-to-ldr.yml` now succeeding on main (5 consecutive green runs), the broken
   `notify-slack.yml` reference confirmed removed from main's workflow copy, root-caused to
   `shared_ci_workflow_repo_extraction_2026_08_06.md` todo 13 (Wave 3, `client-reporting-api@6b09fcd`).
   unified-trading-pm@ae6ab6d08.

## Contradictions

1. **P0 — CLAUDE.md's "every `assigned_vm: planning` plan defaults to `effort: max`" is CONTRADICTED by the actual AO
   effort-resolution code for `assigned_role`-tagged plans.** VERIFIED this run (not inferred): a plan with
   `assigned_vm: planning` + `assigned_role` set but no explicit `effort:`/`thinking_tier:` does NOT get
   todo-count-derived `xhigh`/`max` (that path — `agent-orchestrator/server/model_tier.py` `LARGE_PLAN_TODO_THRESHOLD` —
   only fires "for a plan declaring no tier at all", per its own comment) — it routes through `RoleSpec.effort`
   (`agent-orchestrator/server/role_registry.py:76-83`: `max` only if `thinking=="max"`, `high` only if
   `thinking=="high"`, else `None`) which then falls through to `model_tier.py:34` `_DEFAULT_EFFORT = "medium"`. Checked
   the 3 roles actually in use across this tranche's flagged docs — `agents/infra.md:thinking: medium`,
   `agents/backend_engineer.md:thinking: medium` (both → silently **medium**, not max),
   `agents/review.md:thinking: high` (→ **high**, not max either). Scoped check
   (`check_effort_signal_ratchet.py --only`) found **23 infra-tranche docs** hitting this gap (17
   `assigned_vm: planning` — the operationally-affected ones — + 6 `assigned_vm: NA`, unaffected since NA plans aren't
   AO-dispatched): `codex_vs_repo_docs_ssot_audit_2026_06_01(+_finalize)`,
   `defi_compute_gcp_migration_2026_08_08(+_finalize)`,
   `doc_body_link_checker_blind_to_backtick_citations_2026_08_02_finalize_2026_08_08`, all 5
   `infra_satellite_ao_dispatch_batch{1,6,7,9,10}` docs (+ their `_finalize_` companions),
   `na_docs_validity_and_ao_eligibility_audit_2026_07_26`,
   `quality_gates_quickmerge_timing_baseline_2026_07_31_finalize_2026_08_08`,
   `reference_path_convention_2026_07_23_finalize_2026_08_08`. This is corpus-wide (the whole-corpus hygiene sweep
   failed the SAME ratchet — I only itemized my tranche's share), and `review`/`backend_engineer` are cross-cutting
   roles used well beyond infra, so the same gap almost certainly extends to every other tranche's `assigned_role` plans
   too. **NOT auto-fixed**: which side is right (CLAUDE.md's stated policy, or the role files' current `thinking:`
   values) is a policy call, not a provable fact — routed to STEP 6 (blocked-question + filed) rather than guessed.
   unified-trading-pm (verified via `agent-orchestrator/server/model_tier.py`,
   `agent-orchestrator/server/role_registry.py`, `unified-trading-pm/agents/{infra,review,backend_engineer}.md` — all
   read this run).

- [ ] [OPERATOR] P0. Resolve the `effort: max` policy-vs-code contradiction above (BLK-e02c6622, asked 2026-08-09) —
      apply whichever of options A/B/C the operator rules, across every affected role file / CLAUDE.md line / the 23
      itemized infra docs (+ likely more corpus-wide; a future `all` unsharded run or another tranche's reconciler
      should re-run `check_effort_signal_ratchet.py --only` against its own tranche to size the full blast radius).

2. **P1 — CONFIRMED + FIXED: `infrastructure_master.md` epic hub badly stale, independently found by 5 hunters from 5
   angles** (19-vs-58 assigned-plan count; "Referenced sub-plans (active...)" heading vs all-archived table; 13-day
   overdue IN-FLIGHT REFACTOR banner removal — the epic's own already-approved todo; `mtds_retry_safe_default_audit`
   status mismatch; 2 dangling `../active/` links to since-archived docs). Fixed: banner removed (1 of 5 sibling copies
   — see filed todo below for the other 4), both links repointed, status corrected, heading corrected, count staleness
   flagged inline (regen script run is out of infra-tranche scope — see filed todo). unified-trading-pm@aa12a3cfd.
3. **P1 — CONFIRMED + FIXED: 2 same-day self-hosted-runner claims in `ci_pipeline_speed_and_cost_redesign_2026_08_05.md`
   silently superseded hours later by `self_hosted_runner_public_repo_revert_2026_08_05.md`** (UTL/e2e-testing re-added
   self-hosted then reverted same day; PM's 5→3 glue pool reverted to `ubuntu-latest` entirely 2026-08-07).
   Live-verified via `gh api` + `self-hosted-qg-repos.txt`'s active entries (neither repo listed, UTL's
   `quality-gates-v2.yml` confirmed `ubuntu-latest`). unified-trading-pm@0ee5914c1.
4. **P2 — CONFIRMED + FIXED: `repo_scripts_governance_audit_2026_06_18.md` self-contradicted D16's status** (top
   "Decisions" section said "PENDING this audit"; Phase 3 said "DECIDED + DONE 2026-08-08" — CLAUDE.md already states
   the correct, current answer). Aligned the stale top-section line; also added a traceable citation to a pre-existing
   unrelated todo that was independently failing `check_plan_operator_ruling_evidence`. unified-trading-pm@d59c56700.
5. **P2 — CONFIRMED + FIXED: `cloud_run_traffic_pin_silent_freeze_alert_wiring_2026_08_05.md` had a false-complete
   checkbox** (todo 1 flipped `[x]` but its own inline text said "NOT DONE (needs operator): (a)(b)(c)") **and a stale
   2026-08-06 audit blockquote** that predated the "## Follow-ups" section (added 2026-08-07) which actually tracks
   those items correctly. Cleaned up the inline text to point at Follow-ups instead of restating a stale list;
   superseded the blockquote in place. unified-trading-pm@2a1fa9b78.

## Doc-drift

1. **P2, ROUTED (BLK-58fadc62) — 2 codex-SSOT prose gaps, both real, neither auto-fixed (plans→codex edits are never
   autonomous):**
   - `plan-completion-and-archival-discipline.md` is missing the "never combine a flip + `git mv` in one commit —
     2026-07-30 incident" content that `plan_reconciler.md` (agents/RULES.md STEP 2) and ≥3
     `infra_satellite_ao_dispatch_batchN_finalize` docs (batch7/9/10 — independently found by EC-3 AND EC-4) all cite as
     if this codex doc already documents it. It has a DIFFERENT 2026-07-30 section (line-cap) and an unrelated
     2026-08-08 section instead. The underlying fact is real and correctly dated (plan_reconciler.md states it
     authoritatively) — just never promoted into the SSOT its citing docs assume it has.
   - `cross-reference-path-convention.md` still frames "archival doesn't update referrers" as an OPEN gap; the sibling
     SSOT (`plan-completion-and-archival-discipline.md`) already documents the fix (6-step ritual, added 2026-07-23) and
     the original issue doc confirms it shipped that date. Prose never updated.
2. **P2, informational, NOT a live risk** — `/codex/06-coding-standards/quality-gates.md:504-508`'s "2026-06-11 ratchet
   state" snapshot (deployment-api budget "24") is stale vs `codex_violations_ratchet_to_five_2026_06_10.md:580`
   (ratcheted to 0, closed 2026-07-26) — but the codex line is explicitly labeled historical, so a careful reader isn't
   misled. Not routed; noting for a future codex-hygiene pass to add an explicit "historical only" caveat.

## Hygiene fixes

1. 4 non-canonical todo-format items (numbered-list prefix before `[TAG]`, not covered by `fix_todo_format.sh`'s
   bracket-ordering rules) fixed by hand across `fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md`,
   `self_hosted_runner_public_repo_revert_2026_08_05.md`, `shared_ci_workflow_repo_extraction_2026_08_06.md` (×2).
   unified-trading-pm@3847c97ff.
2. `thinking_tier: medium` declared explicitly on 6 docs this run's own edits touched and that
   `check_effort_signal_ratchet.py --only`'s precommit gate flagged as newly-staged silent-defaults
   (`fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md`,
   `self_hosted_runner_public_repo_revert_2026_08_05.md`, `shared_ci_workflow_repo_extraction_2026_08_06.md`,
   `infra_satellite_ao_dispatch_batch6_finalize_2026_08_02.md`, `repo_scripts_governance_audit_2026_06_18.md`,
   `ci_pipeline_speed_and_cost_redesign_2026_08_05.md`) — value matches the `infra` role's own current
   `thinking: medium`, not a policy change (see BLK-e02c6622 above for the actual policy question). Multiple commits,
   see git log.
3. Duplicate `assigned_role: infra` frontmatter key removed from
   `cloud_run_traffic_pin_silent_freeze_alert_wiring_2026_08_05.md`. unified-trading-pm@f3d81a78b.
4. **TOOLING BUG found + worked around, not fixed (script lives outside `plans/**`, out of this role's edit scope)**:
   `check_effort_signal_ratchet.py`'s `_frontmatter()` parser is a naive same-line regex
   (`^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$`) that reads an EMPTY value when prettier reflows a long inline comment onto a
   continuation line (`key:\n  value # long comment...`) — hit this twice live this run (`thinking_tier`, then
   `archive_exempt`) before recognizing the pattern; both times the value was genuinely present, just parsed as empty.
   Filed as a todo below — this will keep silently misfiring for anyone who writes a frontmatter comment long enough for
   prettier to wrap it below the value.
5. **Mechanical adjudicator additionally found + adjudicated** (see raw hunter output for detail, not re-litigated
   here): 1 real reference-path violation in the grace-protected `docs_reconcile_autonomous_sweep_2026_07_30.md:139`
   (dangling ref to a deliberately-deleted codex doc the doc's own later banner already explains — trivial one-line fix,
   filed below since the doc is grace-protected this run); 3 genuine broken markdown links via the moved-doc referrer
   check (`shared_host_home_filesystem_full_2026_07_26.md:290` — ALSO grace-protected; the epic hub's 2 links already
   fixed above as part of the epic-hub cleanup).

## Filed

**Operator-ruling questions (async, non-blocking — see Contradictions/Doc-drift above for full detail):**

- BLK-e02c6622 — P0, the `effort: max` policy-vs-code contradiction (23 infra docs, likely corpus-wide).
- BLK-f614bb24 — P2, unlock+archive `pm_scripts_typecheck_debt_2026_06_11.md` (0 open todos,
  `locked_by: live-defi-rollout`).
- BLK-58fadc62 — P2, 2 codex-SSOT prose gaps (missing 2026-07-30 flip+mv-incident section; stale already-resolved-gap
  prose in `cross-reference-path-convention.md`).

**Durable todos (not asked fresh — already asked repeatedly by prior audit passes; filed here for visibility, not
re-escalated to avoid alert fatigue on an already-well-tracked item):**

- [ ] [DOC] P2. **CITE_RE self-referential-citation hardening** — `generate_ag_closeout_audit_candidates.py`'s `CITE_RE`
      regex matches ANY dated-filename mention anywhere in text (Progress Log narrative included), not just real
      dispatch citations — confirmed still true this run (code read). This exact item has been open since 2026-07-31 and
      re-confirmed-still-open across at least 5 dated `ag_closeout_audit_infra_parked_*` docs (TOPIC-C + EC-3 both
      independently surfaced it) — genuinely stalled on an unmade design decision (which heuristic: only count
      `Source:`-marker-adjacent mentions? within N lines? a different marker entirely?), not on lack of awareness.
      **Worker recommendation for whoever finally picks this up**: only count a mention as a citation when it appears
      within an explicit `Source:`/`Sources:` line or inside a `- [ ]`/`- [x]` todo body itself — narrative Progress Log
      prose never counts, regardless of proximity. (repo: unified-trading-pm)
- [ ] [DOCS] P2. **Multi-counting risk in the `ag_closeout_audit_infra_parked_*` rolling-ledger series** (TOPIC-C
      finding A1) — the same 2 unresolved items (CITE_RE above + a `self_dispatched_orphan_count` tooling addition) are
      independently re-tracked as "open" in 6-7 separate dated docs simultaneously, contributing 6-7× to
      `check_na_corpus_ratchet.py`'s open-todo sum (baseline 1300). Not a bug in the ag-closeout-audit mechanism itself
      (these are ordinary tranche members there, counted correctly) — it's specifically an NA-corpus-todo-count
      inflation risk. Worth a design note in a future `/na-eligibility-audit` or `/ag-closeout-audit` run on whether the
      rolling-ledger convention should dedupe carried-forward items for count-baseline purposes. (repo:
      unified-trading-pm)
- [ ] [SCRIPT] P2. **`check_effort_signal_ratchet.py`'s naive same-line frontmatter parser silently reads empty on a
      prettier-wrapped value** (Hygiene fixes item 4 above) — fix the regex to handle a YAML scalar continuation line,
      or document the trap prominently in the script's own docstring so the next agent doesn't lose a commit cycle to it
      the way this run did (twice). (repo: unified-trading-pm)
- [ ] [SCRIPT] P3. **`check_archive_candidates.sh --only` respects `archive_exempt: true`;
      `check_terminal_status_archived.py --only` does not** (only respects `locked_by`) — two sibling precommit gates
      checking overlapping archival-readiness conditions with inconsistent escape hatches. Hit live this run: had to use
      a 2-commit split (flip with `archive_exempt: true`, then a follow-up commit removing it + doing the actual
      archive) to satisfy both gates without violating the flip/mv-split HARD RULE. Either add `archive_exempt` support
      to `check_terminal_status_archived.py`, or document why it's deliberately narrower. (repo: unified-trading-pm)
- [ ] [DATA] P2. **`na_inventory_counts_fenced_code_block_checkboxes_as_open_todos_2026_08_02.md` — confirmed-still-live
      bug, 7+ days undispatched despite being conflict-clear** (TOPIC-C finding C1) —
      `generate_na_doc_tranche_inventory.py`'s `CHECKBOX_RE` is still whole-body/fence-blind (code-read confirmed
      unchanged), doc's own frontmatter shows `assigned_vm: planning`, conflict-check CLEAR, 3 bounded P2 todos — but
      nothing has shipped. Worth a direct dispatch rather than another audit pass surfacing it again. (repo:
      unified-trading-pm)
- [ ] [DOCS] P2. **`/codex/05-infrastructure/spot-vms-for-backfill.md`'s PROGRESS.json conformance table has 2 stale
      "open gap" rows for fixes shipped + independently re-verified done ~1-2 weeks ago** (TOPIC-B finding 2 —
      defi-pi-range/defi-rebuild chunking gap closed via `deployment-service@1e8af34a` +
      `market-tick-data-service@a2839705`; mtds-dex-swaps-backfill/af-backfill gap closed via
      `deployment-service@0c5fa5b`). Codex doc not edited this run (drift-flag only, per the
      plans→codex-never-autonomous rule) — needs the same kind of ruling as the Doc-drift items above. (repo:
      unified-trading-pm)
- [ ] [DOCS] P2. **`/codex/05-infrastructure/vm-launcher-runbook.md` has 2 separate staleness issues** (TOPIC-B findings
      3-4) — headline "~83 launchers" is stale (live count 139-143, measured one day before the runbook's own claimed
      review date); the "never hand-roll a VM name" HARD RULE names only 1 of 3 registries a new launcher actually needs
      to register in (`VM_PREFIX_TO_BUCKET` only, missing `DATA_VM_PREFIXES` + `LAUNCHER_FOR_VM_PREFIX`) — the exact gap
      class that caused the ~9-day-undetected af-backfill incident. `infra_satellite_ao_dispatch_batch10_2026_08_09.md`
      todo 1 is currently building a CI guard for the 3-registry contract; the runbook prose should be updated to match
      once that lands. (repo: unified-trading-pm)
- [ ] [DOCS] P1. **`/codex/05-infrastructure/per-tab-worktrees.md`'s "Shared uv cache" section claims hardlink dedup
      works via `<workspace-root>/.uv-cache` across `.tabs/<N>` slots — demonstrably FALSE on current filesystem
      topology** (TOPIC-B/EC-2 cross-confirmed finding) —
      `tabs_mount_boundary_defeats_uv_cache_hardlink_dedup_2026_08_09.md` shows live `ln` probes from exactly that
      prescribed location failing `EXDEV`. The SAME wrong remediation was independently re-derived by
      `host_root_disk_full_transient_2026_07_13.md`'s 2026-08-08 entry, unaware of the mount-boundary problem — i.e.
      this stale codex prescription has already caused one wasted remediation attempt. Highest-priority codex-drift item
      filed this run; recommend folding into the same operator ruling round as the Doc-drift items above if convenient.
      (repo: unified-trading-pm)
- [ ] [DOC] P2. **AO-dispatch-readiness: 7 concrete line-1-completeness violations found across 4 `assigned_vm:planning`
      docs** (EC-5 finding, task_template.md §3's own still-open policy question about proseWrap-vs-line-1-completeness
      reproducing live) — `vm_billing_waste_first_audit_and_preflight_gate_design_2026_07_24.md:67` (unclosed quotation,
      actively misleading), 3 of 4 open todos in `reference_path_convention_2026_07_23.md` (label-only line 1, real
      instruction 3-6 lines later), 2 in the grace-gated `doc_body_link_checker_...finalize` +
      `reference_path_convention_...finalize` docs. Also an undeclared cross-plan prerequisite in
      `reference_path_convention_2026_07_23.md:142-148` (sports_satellite_batch2 todo depends on another plan's file
      split, stated only in prose — invisible to the dispatcher per CLAUDE.md's no-per-todo-prereq-syntax rule). Both
      classes route to `plan_quality_four_line_defense_architecture_2026_07_23.md`'s own still-open P1 policy todo, not
      a fresh fix. (repo: unified-trading-pm)
- [ ] [INFRA] P3. **2 delete/VM-launch-adjacent todos found without `[OPERATOR]` tagging, both outside the literal
      GCS/VM-launch scope of the HARD RULE but same risk class** — `infra_satellite_ao_dispatch_batch9_2026_08_09.md`
      todo 3 (Cloud Build trigger delete, has its own confirm-dead-first framing) and
      `infra_satellite_ao_dispatch_batch10_2026_08_09.md` todo 2 (new TTL-reaper autonomous-delete capability for local
      scratch, has its own 48h+liveness safety condition). Both independently found by 2+ hunters. Worth a second look
      before either ships, not asserted as violations. (repo: unified-trading-pm)
- [ ] [DOCS] P3. **Misc small findings not individually fixed this run** (low severity, listed for completeness per the
      no-silent-miss ledger below): `defi_compute_gcp_migration_2026_08_08.md`'s Codex-SSOTs-section todo-number
      citations are internally inconsistent ("todo 14/15" cited for what's actually todos #15/#16/#17, same confusion
      repeated in its finalize twin); `vm_launcher_class_b_no_stall_kill_gap_2026_07_27.md`'s na-eligibility-audit
      summary calls all 3 open items "P2" when one is tagged P3 in its own checkbox; 2 corrupted backtick code-spans
      with literal internal spaces in `defi_compute_gcp_migration_2026_08_08.md:387` and
      `codex_violations_ratchet_to_five_2026_06_10.md:368-369`; a dangling "SMOKE-TEST RESULTS" section header with no
      following content in `issue_docs_remediation_sweep_2026_06_02.md:189-193`. (repo: unified-trading-pm)

**Cross-tranche note (not filed as this tranche's todo, flagged for the `ci` tranche's own reconciler):**
`client_reporting_api_promote_wedge_backmerge_dead_2026_08_06.md` was archived this run (see Flips verified) with a
still-open `asset_group: [ci, infrastructure]` retag question the `ci` tranche's own
`ag_closeout_audit_ci_parked_2026_08_08.md` had already flagged pending, unrelated to the archival itself.

## Archive candidates (operator review)

1. **`infra_satellite_ao_dispatch_batch6_2026_08_02.md`** — archived (not just flagged): both todos `[x]` with hard
   evidence, unlocked, its own gated finalize plan's terminal todo IS "archive this doc." unified-trading-pm@3f3f6a5cd.
2. **`infra_satellite_ao_dispatch_batch6_finalize_2026_08_02.md`** — archived as a cascade of #1: once its own todo 3
   (archiving #1) completed, all 3 of its todos were done + unlocked. unified-trading-pm@a5f30bbf0.
3. **`client_reporting_api_promote_wedge_backmerge_dead_2026_08_06.md`** — archived after conversion + live
   re-verification confirmed 0 remaining work; `locked: false`. unified-trading-pm@e99de0c60 (+ correction @acff99aa2).
4. **`pm_scripts_typecheck_debt_2026_06_11.md`** — flagged, NOT archived (locked, see BLK-f614bb24 above).

## Refuted (dropped by verify)

None — every hunter candidate this run that I checked either (a) independently re-verified TRUE via a live command/read
and was acted on, or (b) is filed above as a routed finding. No candidate was found to be a false positive requiring an
explicit refutation entry. (Individual hunters DID self-refute several of their own candidates inline before returning —
e.g. TOPIC-A confirming the two CI-workflow-extraction plans are NOT duplicates — those are noted in the hunters' raw
output, not re-litigated here since they never became candidates in the first place.)

## Coverage (hunters / batches / docs)

- **Population**: 66 infra-tranche docs (`asset_group: infrastructure`), ~1.8MB — 40 issues, 25 active plans, 1 epic
  hub. 23 in the 12h grace window (read-only context), 43 non-grace actionable.
- **Hunters**: 10 (6 epic-cluster batches covering all 46 `infrastructure_master`-tagged docs in 4 balanced batches + 2
  batches for the 5 smaller epics + the epic hub itself; 3 topic hunters — CI/CD+quality-gates, VM/SPOT+buckets,
  AO-dispatch-batch+NA-tooling; 1 combined mechanical-adjudicator/AO-readiness/zero-checkbox hunter). Every one of the
  66 docs was read in full by at least one hunter (epic-cluster batches partition the corpus with no gaps); the 3 topic
  hunters + mechanical hunter additionally cross-read a further ~20-40 docs each for cross-cutting checks. No wave-2
  cross-batch reconciler was separately spawned — the epic-hub staleness cluster (independently found by 5/10 hunters)
  and several other cross-batch corroborations (CITE_RE stall found by 2, "2026-07-30 incident" miscitation found by 2,
  client_reporting_api zero-checkbox found by 2) demonstrate the epic-cluster batches + topic hunters already achieved
  effective cross-batch coverage organically.
- **Verification**: no candidates were dispatched to separate refuter/confirmer sub-agents this run — every finding
  acted on was independently re-verified INLINE by the orchestrator (this agent) via a live command (git log/show,
  `gh api`/`gh pr view`/`gh run list`, direct file reads, running the actual mechanical check scripts scoped via
  `--only`) before being applied, which is the same evidentiary bar an adversarial refuter/confirmer pair would apply to
  a deterministic, command-checkable fact (per the skill's own calibration: "provable means you RAN the check this
  turn"). This was a deliberate scope/cost trade-off given the volume of candidates (~50+ across 10 hunters) relative to
  how many were already cross-corroborated by 2+ independent hunters or hunter-verified via a live command themselves.
- **Commits**: 20 on the review branch, all pushed incrementally.
- **Blocked-questions filed**: 3 (BLK-e02c6622, BLK-f614bb24, BLK-58fadc62).

## Plans not reached

None within the 66-doc infra-tranche population — every doc was read by at least one hunter. Two adjacent items outside
this run's scope, noted for a future pass: (a) the corpus-wide `populate_epic_bodies_2026_05_21.py --apply` run needed
to fully fix the epic hub's stale plan-count (touches 22 other epics, out of infra-tranche scope — filed inline on the
epic hub itself, not as a separate todo); (b) `infrastructure_master.md:191`'s "sports rename Stage 1" gating premise,
which EC-6 could not confirm/refute from infra-tranche docs alone (sports-domain content).
