---
doc_type: issue
title:
  Parked BLOCKED-OPERATOR-DECISION items + confirmed P0/P1 contradictions from the 2026-08-02 /plan-reconcile
  whole-corpus run
summary: >-
  The autonomous (nobody-present) `/plan-reconcile` whole-corpus run of 2026-08-02 auto-fixed what was provable from
  code/git/filesystem and parked everything else here, per the skill's Phase-4 routing. Contains (1) the confirmed P0
  contradictions the corpus-wide contradiction sweep found — several are data-correctness class and two are live
  delete-safety hazards sitting in still-OPEN todos; (2) the operator rulings the run could not make autonomously
  (SSOT-ownership disputes, two-active-docs-opposing-directives, issue-doc archival routing for resolved incidents whose
  prevention todos are still open); (3) the four RED hygiene ratchets, two of which are genuine regressions against
  their baselines rather than pre-existing debt. Every item carries options + a worker recommendation. No DISPOSITION
  here was decided autonomously; the two P0 delete-safety hazards (§ 1a, § 1b) did get non-destructive STOP banners + an
  `[OPERATOR]` retag so a dispatched worker cannot execute the stale instruction while the ruling is pending — that is
  the skill's "superseded content with no banner -> add banner" auto-fix, and for § 1b it also executes an amendment
  already RULED on 2026-07-28 but never applied. Neither banner picks an option.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, market-data-processing-service, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [plan-reconcile, contradiction-audit, operator-decision, hygiene-ratchet, data-correctness, delete-safety]
related:
  [
    /plans/active/issues/zero_checkbox_sweep_all_tranches_2026_07_31.md,
    /codex/11-project-management/issue-doc-lifecycle.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/02-data/sports-2020-06-data-floor.md,
  ]
created: 2026-08-02
author: unknown
last_updated: 2026-08-02
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
assigned_role: review
drift_direction: correct-codex
depends_on: []
resolved_by:
  "All 11 todos RULED 2026-08-02 (operator) and applied; last remaining item ([DOC] P2, name the register in SKILL.md)
  closed 2026-08-04 (na-eligibility-audit) via unified-trading-pm@d872efb3a. Each individual ruling's substance is
  restated inline at its point of application (not solely dependent on this register)."
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "Autonomous /plan-reconcile whole-corpus (unscoped) run, 2026-08-02, slot-3. 714 docs inventoried (253 plans + 433
  issue docs + 28 epics); 13 read-only epic-cluster/topic hunters over 18.3 MB. Parked here because the run had no
  interactively-present operator."
context_scope:
  [
    /codex/11-project-management/issue-doc-lifecycle.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/issues/zero_checkbox_sweep_all_tranches_2026_07_31.md,
    /cursor-configs/skills/plan-reconcile/SKILL.md,
  ]
---

> **🔴 ARCHIVED 2026-08-06 — RESOLVED** (all todos `[x]`, unlocked). All 11 parked items RULED by the operator
> 2026-08-02 and applied; each ruling's substance is restated inline at its point of application across the corpus, not
> solely dependent on this register. Archived by /plan-reconcile ao.

# Parked operator decisions — `/plan-reconcile` whole-corpus run, 2026-08-02

> **Routing note.** Everything below reached Phase 4 and was classified NOT auto-fixable: it needs an SSOT-ownership
> call, a choice between two ACTIVE docs giving opposing directives, a delete-safety ruling, or a codex-SSOT edit (never
> autonomous). The run's auto-fixes shipped separately and are listed in § 5 for contrast.

## 1. P0 — data-correctness and delete-safety, all sitting in still-OPEN todos

These are the run's highest-severity confirmed findings. Each was found by a hunter, then survived independent
refutation (scope / date / supersession attacks) before landing here.

### 1a. Sports close-out's open Track C todo instructs conflating two live bookmakers and purging 1.1M–1.65M live rows

- `/plans/active/sports_consolidated_closeout_2026_07_19.md:518-523` — an UNCHECKED `- [ ]` todo instructing a worker to
  fold `UNIBET_UK`/`UNIBET_EU` → `UNIBET` and to purge `SMARKETS` as "an explicitly deleted venue."
- `/plans/active/sports_consolidated_native_ao_extract_2026_07_25.md:151-166` — dated two days LATER, `[x]` DONE, and
  proves both premises false: UNIBET_UK and UNIBET_EU are genuinely distinct live bookmakers (folding "would silently
  conflate two distinct bookmakers' live data"), and SMARKETS carries 1.1M–1.65M live rows and was "NEVER removed from
  all repos."
- The correction was never back-ported. The stale instruction is the one a dispatched worker would read.

**A [WORKER REC]**: strike the Track C todo and replace it in-place with a pointer to the `native_ao_extract`
correction, so the destructive instruction cannot be picked up. **B**: leave both and add a warning banner. **C**:
re-verify the SMARKETS row counts first, then decide. **Other**: operator text.

### 1b. Two open GCS-delete todos gated on a proof already shown insufficient

- `/plans/active/sports_consolidated_closeout_2026_07_19.md:552-553` and
  `/plans/active/sports_consolidated_native_ao_extract_2026_07_25.md:204-210` — both open, both self-justified rather
  than `[OPERATOR]`-gated, both gate a `sports_reference_v2/by_date/` cull on a reader-check alone.
- `/plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md:184-217` already proved 1,492 of those rows are the
  SOLE surviving copy of real pre-floor data with no canonical twin — which a reader-check does not detect. Its own
  finalize doc (`..._finalize.md:141-145`, 2026-07-28) confirms the fix is "STILL UNDONE"; batches 6/7/8 never pick it
  up.

**A [WORKER REC]**: retag both todos `[OPERATOR]` and add the delete-safety §3a citation, blocking autonomous execution
until the 1,492-row carve-out is resolved. **B**: resolve the 1,492 rows first (copy to canonical), then leave the todos
self-justified. **C**: both. **Other**: operator text.

### 1c. TradFi E7 reads "orphan_class_E=0, complete" over a confirmed data-loss finding in the same doc

- `/plans/active/data_completion_tradfi_2026_07_15.md:210-218` — E7 Verify `[x]`: "DONE — apply 2026-07-06...
  orphan_class_E=0 corpus-wide... schema_version=9=100%".
- Same doc, `:392-404` — R1 RUNBOOK, still open: "AUDITED 2026-07-26, VIOLATION CONFIRMED, DATA-LOSS FINDING FILED...
  the 2026-07-06 completing apply's launcher NEVER passes `--also-legacy`... legacy bucket... confirmed permanently
  deleted." ~2,008 legacy-only tradfi days destroyed without migration.
- The completion marker and the data-loss finding describe the SAME delete event and cannot both stand.

**A [WORKER REC]**: un-check E7 and restate it as "complete for the migrated corpus; ~2,008 legacy-only days
irrecoverable — see R1", so no downstream reader treats tradfi as 100%. **B**: leave E7 and rely on R1. **C**: escalate
the data-loss finding to its own issue doc first. **Other**: operator text.

### 1d. cefi Track 1 declared DONE the same day a sibling says the same artifact is still in progress

- `/plans/active/cefi_consolidated_closeout_2026_07_18.md:183-190` — Track 1 "DONE 2026-07-27... every shard
  EXIT_STATUS=0... 0 further planned changes."
- `/plans/archive/2026_07/cefi_consolidated_native_ao_extract_2026_07_25.md:332-335`, SAME day — the identical artifact
  "turned out ~2 orders of magnitude larger than planned (~4.5M objects, not ~12,662)... **still in progress**."
  Corroborated by `cefi_content_migration_fleet_half_incomplete_2026_07_26.md` and children showing 17/44 shards still
  incomplete on 2026-07-31, four days after the claimed completion.

**A [WORKER REC]**: un-check Track 1 — the fleet docs are the measured ground truth and the closeout is the roll-up.
**B**: keep it checked and add a "roll-up only, see fleet docs" qualifier. **Other**: operator text.

### 1e. cefi legacy-bucket deletion status contradicted across three docs

- `/plans/active/issues/cross_cutting_manifest_canonicalisation_findings_2026_07_11.md:223-230` — re-confirmed by its
  OWN 2026-07-30 na-eligibility pass that cefi's legacy bucket "remains genuinely undeleted."
- `/plans/active/issues/cefi_legacy_bucket_deleted_before_l3_gate_2026_07_28.md:78-80` and
  `/plans/active/cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md:218-220` — deleted 2026-07-14, i.e.
  before the cross-cutting doc's own adjudication section was written.

**A [WORKER REC]**: correct the cross-cutting doc to "deleted 2026-07-14" and cite the L3-gate issue doc. **Other**:
operator text.

## 2. SSOT-ownership disputes — cannot be settled autonomously

### 2a. Is Massive (Polygon.io) actually removed as a TradFi source?

`/plans/epics/tradfi_master.md:178-180` plus two active plans assert, present tense, "REMOVED as a TradFi source
2026-07-19" / "PURGED 2026-07-21" — and CLAUDE.md's own domain index repeats it. But
`/plans/active/issues/tradfi_adapter_dead_code_fallback_audit_2026_07_25.md:74-75,131` (created 2026-07-31, still open)
found `instruments-service`'s `massive.py` is live, tested and wired end-to-end; the two cited commits only stripped
Massive from the read-time `SOURCE_PRIORITY` dict and never touched instruments-service.

**This one implicates a codex SSOT** (`/codex/02-data/tradfi-databento-sourcing-ssot.md`) and CLAUDE.md, so the run did
not touch it. **A [WORKER REC]**: finish the removal in instruments-service, then the docs become true as written.
**B**: narrow every doc's claim to "removed from `SOURCE_PRIORITY`; instruments-service adapter still present". **C**:
declare Massive intentionally retained as a non-priority fallback and correct the "removed" language everywhere.
**Other**: operator text.

### 2b. Who may hand-edit the live `backlog.yaml` to park a task?

`/plans/active/issues/ao_park_disposition_blocked_answer_no_follow_through_2026_07_31.md:8-12` frames the park hand-edit
as barred for agents and reachable only via an explicit operator step. Two live worker sessions did it themselves anyway
and documented it as sanctioned: `/plans/archive/issues/ao_db_lock_storm_and_stuck_shutdown_outage_2026_07_26.md:304` and
`/plans/active/issues/backlog_park_lost_across_sibling_todo_insertion_2026_07_30.md:119,122` ("the documented sanctioned
mechanism, not a code change"). Note CLAUDE.md's standing rule is "**Never hand-edit `backlog.yaml`** — author plans,
the backend derives it", which reads as barring both.

**A [WORKER REC]**: reaffirm the CLAUDE.md rule (no agent hand-edits; parks go through the API/an operator step) and
correct the two worker docs. **B**: carve out an explicit park-only exception and write it into the AO codex SSOT.
**Other**: operator text.

### 2c. `PLAN_FORMAT.md` ↔ `task_template.md` disagree on the canonical todo-tag vocabulary

`/plans/PLAN_FORMAT.md:306-312` declares a "closed set of canonical tags" that OMITS `[INFRA]`, `[DATA]`, `[BACKEND]`,
`[REVIEW]`, `[CODE]`, `[DOCS]`, `[PM]`, `[DIAG]` — while `/plans/active/task_template.md:133` documents exactly those as
the live per-task role-routing tags, and essentially every todo in the corpus uses them (this very doc's siblings
included). One of the two normative refs is stale.

**A [WORKER REC]**: update `PLAN_FORMAT.md`'s tag list to match `task_template.md`, which matches live practice and the
shipped role-router. **B**: the reverse. **Other**: operator text.

### 2d. `PLAN_FORMAT.md`'s archive-criteria rule is unsatisfiable under the current schema

Its "Archive Criteria by Plan Type" table (`:67-69`) gates archival on `repo_gates` / `completion_gates` — fields the
same doc later labels "Legacy schema (pre-2026-05-21)" (`:211-219`) and which the current canonical schema (`:78-131`)
does not contain. No current plan can satisfy it; every real archival instead uses zero-open-todos + evidence.

**A [WORKER REC]**: rewrite the table to the zero-open-todos + evidence bar actually in use (matches
`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`). **B**: reinstate the gate fields. **Other**:
operator text.

### 2e. The AOF epic violates the `assigned_vm` rule it established

`/plans/epics/agent_operating_framework_master.md:25` sets `assigned_vm: planning` and `:70` frames it as a reassignable
dispatch target — but the SAME epic's decision D2 at `:130` drops epic→VM delegation, and
`/plans/PLAN_FORMAT.md:204-206` cites this epic as the SSOT for "`NA` is the expected value on every current epic."

**A [WORKER REC]**: set the epic to `assigned_vm: NA` and drop the reassignment sentence. **Other**: operator text.

## 3. Issue-doc archival routing — 3 resolved incidents whose prevention todos are still open

`check_terminal_status_archived` is RED. The run archived the 10 unambiguous cases (§ 5). These 3 carry
`status: resolved` (the incident genuinely cleared) but still hold 7 open prevention/follow-up todos between them:

| Doc                                                                     | Open todos | Tags                        |
| ----------------------------------------------------------------------- | ---------- | --------------------------- |
| `github_actions_billing_wall_recurrence_2026_07_29.md`                  | 3          | `[BACKEND]` ×3              |
| `github_actions_total_fleet_outage_startup_failure_2026_07_30.md`       | 2          | `[BACKEND]` P1, `[DATA]` P2 |
| `ldr_to_main_promote_workflows_sustained_startup_failure_2026_07_30.md` | 2          | `[SCRIPT]` P2, `[CI]` P1    |

`/codex/11-project-management/issue-doc-lifecycle.md` is unambiguous that the answer is ACKED-INTO-PLAN — migrate the
todos into a named active plan, then archive ("If a banner says 'stays in `active/issues/` until parent closes', the
banner is wrong"). What it does NOT determine is WHICH plan absorbs them, and that is an ownership call. The
fold-by-default carve-out does not apply (these are `[BACKEND]`/`[DATA]`/`[SCRIPT]`/`[CI]`, not `[REVIEW]`/`[DOC]`).

Note the corpus currently contains the opposite precedent, applied without a ruling:
`/plans/archive/issues/orphaned_commit_recovery_has_no_dispatch_path_2026_07_30.md` carries an inline "stays OPEN for
the 3 prevention todos the sweep filed" — which is exactly the anti-pattern the codex names. Whichever way this is ruled
should also settle that doc.

**A [WORKER REC]**: migrate all 7 into `/plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md` (the live CI
tranche plan), then archive all 3 — this follows the codex verbatim and clears the ratchet. **B**: flip the 3 back to
`status: open` and codify "terminal status requires zero open todos" as an explicit exception in the lifecycle SSOT
(this legitimises the existing `orphaned_commit_recovery` precedent, but contradicts the current SSOT text). **C**:
per-doc split. **Other**: operator text.

## 4. Hygiene ratchets RED — two are real regressions, not inherited debt

Measured by `run_hygiene_sweep.sh --ci --no-regen` at the start of the run:

| Gate                             | Live | Baseline | Delta                                     |
| -------------------------------- | ---- | -------- | ----------------------------------------- |
| `check_reference_paths` format   | 208  | 161      | **+47 REGRESSION**                        |
| `check_reference_paths` exist    | 915  | 901      | **+14 REGRESSION**                        |
| `check_terminal_status_archived` | 13   | 1        | **+12 REGRESSION** — 10 fixed by this run |
| `check_na_corpus_ratchet` docs   | 356  | 350      | **+6 REGRESSION**                         |
| `check_na_corpus_ratchet` todos  | 1302 | 1292     | **+10 REGRESSION**                        |
| `check_archive_candidates`       | 32   | 4        | **+28 REGRESSION** — 10 fixed by this run |

The reference-path format violations are concentrated in `plans/archive/` (out of this skill's audit scope but inside
the ratchet's), so they cannot be cleared by an active-corpus pass. **A [WORKER REC]**: run a scoped
`fix_reference_paths.py` pass over `plans/archive/` as its own tracked plan — mechanical, and it is the only thing that
will move that number. **B**: exclude `plans/archive/` from the ratchet's population and re-baseline. **Other**:
operator text.

**NA-ratchet interaction, disclosed**: this run ADDED 6 open todos to the NA corpus by converting
`mdps_sports_honest_absence_writes_fail_fetchevidence_gate_2026_08_01.md` from prose (§ 5). That makes the NA number
worse while making previously-invisible work visible — the run judged visibility strictly better than a passing count,
but it is a deliberate, disclosed contribution to a RED ratchet, not an accident.

## 5. What the run DID auto-fix (for contrast — no ruling needed, already shipped)

- **10 resolved issue docs archived** to `plans/archive/issues/` with banners, all 22 path referrers repointed
  corpus-wide — `unified-trading-pm@a04f74e` + `@ff619d4`. Resolution evidence spot-verified reachable on
  `origin/live-defi-rollout` for `instruments-service@fa931784` (repointed 2026-08-06 — original sha orphaned by the
  2026-08-05 history rewrite; content verified identical), `features-service@f57d11ae`,
  `unified-trading-library@e1da2c7f`, `deployment-service@b1f0a22`.
- **Two P0 delete-safety STOP banners + `[OPERATOR]` retags** — `unified-trading-pm@b710bbd`. § 1a's Track C todo in
  `sports_consolidated_closeout_2026_07_19.md` now carries the disproof of its UNIBET-fold and SMARKETS-purge premises
  inline; § 1b's two `sports_reference_v2/by_date/` cull todos (in that same doc and in
  `sports_consolidated_native_ao_extract_2026_07_25.md`) now carry the 1,492-sole-copy carve-out and lost their
  "self-justified, not `[OPERATOR]`-gated" claim. **These make the todos safe to READ; they do NOT decide them** — the
  dispositions remain parked above. § 1b additionally is the execution of an amendment batch5 already ruled on
  2026-07-28 and whose finalize doc recorded as STILL UNDONE, so it is applying a ratified decision, not making one.
- **1 done-but-unchecked checkbox flipped** in `data_pipeline_e2e_milestones_gate_2026_07_24.md` (the first live 30-day
  VM billing-waste audit) — `unified-trading-pm@a5d0702de`, verified an ancestor of `origin/live-defi-rollout`, with the
  target-side `[x]` and its dated Progress Log evidence read directly. The AWS-side IAM block is recorded on the flip as
  a stated residual rather than silently absorbed.
- **Zero-checkbox sweep re-run** against its standing register: 8 hits, 6 already classified, 1 converted to 6 canonical
  todos, 1 recorded as informational.

## Todos

- [x] ✅ [OPERATOR] P0. **Rule § 1a** — RULED 2026-08-02, option A (strike + replace with pointer). The UNIBET-fold and
      SMARKETS-purge clauses are struck from `sports_consolidated_closeout_2026_07_19.md`'s Track C todo; the STOP
      banner now records the historical disproof rather than gating a still-live instruction. (repo:
      `unified-trading-pm`)
- [x] ✅ [OPERATOR] P0. **Rule § 1b — CONFLICT RESOLVED 2026-08-03, option B stands.** A different session on this same
      host (`slot-3`, commit `df384e4cc`) had applied option A first; operator confirmed B overrides it — resolve the
      1,492 rows (copy to canonical) first, then the two todos revert to self-justified (not permanently
      `[OPERATOR]`-gated). The existing `[OPERATOR]` + delete-safety §3a retag stays in place in the interim — correct
      either way, since the carve-out isn't resolved yet. Actual migration filed as its own tracked todo,
      `sports_reference_v2_1492_row_canonical_copy_2026_08_03.md` (real data-pipeline work, not inline here). (repo:
      `unified-trading-pm`, `market-tick-data-service`)

- [x] ✅ [OPERATOR] P1. **Rule § 1c** — RULED 2026-08-02, option A (un-check, restate as partial). E7's checkbox now
      reads "complete for the migrated corpus only", cross-references R1's data-loss finding directly. (repo:
      `unified-trading-pm`)
- [x] ✅ [OPERATOR] P1. **Rule § 1d and § 1e** — RULED 2026-08-02, option A for both. Track 1 un-checked (Script 1's
      ~4.5M-file backfill confirmed still in progress via the fleet doc, `status: open`); legacy-bucket cross-cutting
      doc corrected to "deleted 2026-07-14" citing both corroborating docs. (repo: `unified-trading-pm`)
- [x] ✅ [CODE] P1. **Rule § 2a** — Massive/Polygon.io removal status. RULED 2026-08-02: option A (finish the removal in
      instruments-service) — **EXECUTED 2026-08-03**. `instruments-service@4b594a6d` deletes
      `reference_data/adapters/tradfi/massive.py` + `tests/unit/test_massive_adapter.py` and unwires every call site
      (factory `_ADAPTERS`/`ADAPTER_DATA_SOURCES`, `_resolve_source_aware_adapter_key`,
      `_DATE_AWARE_TRADFI_ADAPTER_KEYS`, the `--source` CLI flag + its whole `source=` plumbing through
      `instruments_handler`→`process`→`process_fetch`/`process_completeness`→`urdi_reference_provider`→`factory`, the
      `MASSIVE` pseudo-venue key-reloader branch, and the `sessions.py` `EXCHANGE_HOURS`/`get_session_metadata` aliases
      whose only consumer was `massive.py`) — 19 files, −1,109/+36, `quality-gates.sh` green (exit 0, 5,113 tests pass,
      coverage 88.76% ≥ 88.0% floor). Docs corrected in `unified-trading-pm@3fe932104` (codex
      `/codex/02-data/tradfi-databento-sourcing-ssot.md` dated-2026-08-03 paragraph + CLAUDE.md domain index, both now
      citing the completing sha alongside `uac@a2beed46`/`mtds@362a487e`). QG STEP 5.83's stale per-file baseline entry
      for the deleted adapter cleared in `unified-trading-pm@77be36524` (single-entry removal, NOT
      `--regenerate-baseline`, so no sibling repo's ratchet was silently re-based). Deliberately RETAINED, not a
      residual gap: UAC's `external/massive/` normalisers + schemas, `PipelineMode.BATCH_MASSIVE` + `possible_manifest`
      recognition, and the `source="massive"` mentions in instruments-service `scripts/` + `tests/scripts/` — all
      historical data provenance, not adapter wiring. (repo: `instruments-service`, `unified-trading-pm`)
- [x] ✅ [OPERATOR] P2. **Rule § 2b** — RULED 2026-08-02, option B (carve out a park-only exception). Documented in
      `/codex/04-architecture/agent-orchestrator-backlog-state-alignment.md`: an agent may hand-edit an existing row's
      `priority`/`prereqs` to park it, provided the task content is untouched AND the same park intent is also authored
      into the source plan (matching the already-shipped `defi_morpho_lending_indices_never_wired` precedent). A
      hand-edit with no matching plan-side authoring is still banned. (repo: `agent-orchestrator`)
- [x] ✅ [OPERATOR] P2. **Rule § 2c and § 2d** — RULED 2026-08-02, "sync all 3 to live practice." `PLAN_FORMAT.md`'s
      canonical tag list now includes `INFRA`/`DATA`/`BACKEND`/`REVIEW`/`CODE`/`DOCS`/`PM`/`DIAG`; the archive-criteria
      table (unsatisfiable `repo_gates`/`completion_gates` fields, legacy pre-2026-05-21 schema) is rewritten to the
      zero-open-todos + hard-evidence bar actually in use. (repo: `unified-trading-pm`)
- [x] ✅ [OPERATOR] P3. **Rule § 2e** — RULED 2026-08-02, same "sync to live practice" batch. AOF epic's `assigned_vm`
      flipped `planning` → `NA`, matching its own cited role as the SSOT for "NA is expected on every epic"; the body's
      stale "reassign per-workstream" sentence corrected to match. (repo: `unified-trading-pm`)
- [x] ✅ [OPERATOR] P1. **Rule § 3** — RULED 2026-08-02, option A (migrate all 7 into `ci_satellite_ao_dispatch_batch1`,
      per-item source citations). All 7 migrated + the 3 source docs (already archived, found with the todos still
      stranded there) updated to point at the new location. The `orphaned_commit_recovery` opposite-precedent doc's
      stale "stays OPEN" framing corrected to note its 3 prevention todos are already closed and its archival is routed
      through a different plan's todo, not a legitimate open-ended exception. This one gates the
      `check_terminal_status_archived` ratchet reaching its baseline. (repo: `unified-trading-pm`)
- [x] ✅ [OPERATOR] P2. **Rule § 4** — RULED 2026-08-02, option B (exclude `plans/archive/` from the ratchet).
      `check_reference_paths.py`'s `target_files()` now skips `plans/archive/`; re-baselined from
      format=158/existence=407 down to format=81/existence=90 (both green, well under the reduced baseline). A separate
      tracked mechanical-cleanup plan, `plans/active/plans_archive_reference_path_hygiene_2026_08_02.md`, was also filed
      independently (option A) to actually fix the underlying `plans/archive/` reference-path defects rather than only
      exclude them from the ratchet — not urgent now that the ratchet itself is green, but still useful hygiene. (repo:
      `unified-trading-pm`)
- [x] ✅ [DOC] P2. **DONE (na-eligibility-audit 2026-08-04)** — Name this register in the skill file. Landed the same
      day this todo was filed: `unified-trading-pm@d872efb3a` ("close 3 mechanical findings from the 2026-08-02 audit
      parked-decision docs") added the "Standing register" line to `cursor-configs/skills/plan-reconcile/SKILL.md:371`,
      citing `/plans/active/issues/zero_checkbox_sweep_all_tranches_2026_07_31.md` by name. Done-when verified live:
      `grep -rn "zero_checkbox_sweep_all_tranches" cursor-configs/skills/` returns a hit. (repo: `unified-trading-pm`)

## Progress Log

- **na-eligibility-audit 2026-08-02**: KEEP-NA, valid -- this IS the operator-decision park register (filed today by the
  sibling `/plan-reconcile` whole-corpus run): 10 of its 11 open todos are `[OPERATOR]` rulings (delete-safety hazards,
  SSOT-ownership disputes, issue-doc archival routing). NOTE the 11th, `[DOC] P2` "Name this register in the skill
  file", IS a bounded one-line SKILL.md edit with a grep-checkable done-when -- but it is a near-duplicate of
  `zero_checkbox_sweep_all_tranches_2026_07_31.md` todo 1's residual (that doc's own 2026-08-02 log says so), so it is
  reported, not flipped; a doc-level `assigned_vm` flip would dispatch the 10 operator rulings alongside it.

- **2026-08-02** — filed by the autonomous `/plan-reconcile` whole-corpus run (slot-3). 13 read-only hunters over 714
  docs / 18.3 MB, partitioned by `parent_epic`. Every item above carries two line-cited verbatim quotes from its source
  docs and survived independent refutation before being parked. Items the run could prove from code/git/filesystem were
  auto-resolved instead and are listed in § 5, not here.

- **context-scout 2026-08-03**: populated context_scope (4 entries).
- **na-eligibility-audit 2026-08-04**: sole remaining open todo ([DOC] P2, "name this register") closed above with
  evidence — the fix had already landed same-day as a sibling doc's Progress Log entry (`unified-trading-pm@d872efb3a`)
  but was never back-flipped here. All todos now `[x]`, no `locked_by` — archival-eligible, routing through the standard
  6-step ritual.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.
