---
doc_type: plan
title: Give ao/ci/infra real asset_group enum values — retag the corpus, stop the cross-cutting ambiguity bug
summary: >-
  ao/ci/infra content has been tagged bare `asset_group=cross-cutting` since 2026-07-25 (avoiding a schema migration) --
  but `/ag-closeout-audit`'s own docs admit this needs real per-doc content judgment, not a mechanical rule, because
  `parent_epic=infrastructure_master` is shared by BOTH genuine cross-cutting data-pipeline docs and pure ci/infra
  content. Confirmed live 2026-07-27: a fresh 9-tranche audit found 37 of 40 cross-cutting candidates were genuinely
  ao/ci/infra -- a 92.5% false-positive rate on the current tag. This plan adds `ao`/`ci` as real enum values (infra
  already exists), retags the ~220-doc affected population, and updates every schema-definition site. The
  epic/consolidated-plan/batch scaffolding for ao/ci/infra already exists (`ao_consolidated_closeout_2026_07_25.md` etc)
  -- this is a tag-correctness fix, not new infrastructure.
status: active
nature: design
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [asset-group, schema, taxonomy, ao, ci, infra, cross-cutting, retag, ag-closeout-audit]
related:
  [
    /plans/active/task_template.md,
    /plans/PLAN_FORMAT.md,
    /plans/active/na_docs_validity_and_ao_eligibility_audit_2026_07_26.md,
    /codex/11-project-management/doc-frontmatter-schema.md,
  ]
created: "2026-07-27"
last_updated: "2026-07-27"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.2
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  "operator directive 2026-07-27, following a fresh /ag-closeout-audit all run whose cross-cutting tranche measured a
  37/40 (92.5%) false-positive rate on the current bare-cross-cutting tag for ao/ci/infra content"
assigned_role: infra
drift_direction: advance-docs
---

# Give ao/ci/infra real asset_group enum values

> **Why LOCAL, not AO-dispatched**: "should ao/ci/infra become real asset_group values" is a taxonomy judgment call, not
> a worker-executable todo (operator confirmed 2026-07-27: "definitely to be done locally to avoid getting to that
> backlog of already 700 backlog AO queue" — the very ambiguity this plan fixes would make a naive AO-dispatched version
> of this retag pass hard to trust). The retag EXECUTION (Phase 2) is mechanical once the schema decision is made, and
> could in principle run on the fleet — but it touches the same corpus `/ag-closeout-audit`'s own classification depends
> on, so a first pass stays local/supervised; a future batch could dispatch remaining docs once this plan proves the
> pattern.

> **🟡 Coordination note (2026-07-27) — a concurrent agent is live-building overlapping infrastructure.** Mid-session,
> another AO worker was found actively shipping: a new `na-eligibility-audit` skill
> (`cursor-configs/skills/na-eligibility-audit/SKILL.md`), a shared conflict-check SSOT
> (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`), a `check_na_corpus_ratchet.py`
> shrinking-ratchet gate wired into `run_hygiene_sweep.sh`, an `agents/na_eligibility_auditor.md` worker role, and edits
> to `cursor-configs/skills/ag-closeout-audit/SKILL.md` + `plan-reconcile/SKILL.md` + `task_template.md` + `CLAUDE.md`.
> **This plan deliberately does NOT touch any of those files** — Phase 3 (originally "update ag-closeout-audit SKILL.md
> to reflect the new schema") is dropped entirely; that skill's classification-mechanism section will need a follow-up
> once the new enum values exist AND the concurrent agent's rewrite has landed and stabilized. The scheduling/sharding
> work from an earlier plan-mode session (`federated-wishing-lovelace.md` — retime nightly crons + shard
> `/ag-closeout-audit all` dispatch via a new `tranche` field on `plan_health.py`'s `PlanHealthDispatchRequest`) is also
> NOT started here — the concurrent agent's own todo list includes "wire dispatch mode server-side (plan_health.py)", a
> same-file collision risk. Re-check both before resuming either piece.

## Phase 1 — Schema definition (3 files, mechanical, additive-only)

- [x] [SCRIPT] P1. Add `ao` and `ci` to `ASSET_GROUP` in `scripts/docs/docspec.py` — unified-trading-pm@a97bc7bed.
      `frozenset({"cefi", "defi", "tradfi", "sports", "prediction", "cross-cutting", "ao", "ci", "infrastructure",     "meta"})`.
- [x] [DOC] P1. Update `plans/PLAN_FORMAT.md`'s `asset_group` enum documentation to match —
      unified-trading-pm@a97bc7bed.
- [x] [DOC] P1. Update `/codex/11-project-management/doc-frontmatter-schema.md`'s `asset_group` enum documentation to
      match — unified-trading-pm@a97bc7bed (§5:
      `asset_group (10): cefi · defi · tradfi · sports · prediction ·     cross-cutting · ao · ci · infrastructure · meta`).
- [x] [REVIEW] P2. Grepped every consumer of the string `ASSET_GROUP` (`--include=*.py`, 13 hits workspace-wide
      2026-07-27, down from the 444+264 scoping estimate which double-counted vendored/build artifacts). All 13
      inspected by content, not just name: only `scripts/docs/docspec.py` (the enum itself) and
      `scripts/plan-hygiene/check_ag_closeout_linkage.py` (a dynamic consumer of it) touch the DOC-TAXONOMY enum this
      plan changed. Every other hit is a same-named but semantically DIFFERENT trading-domain concept —
      `EXPECTED_COVERAGE_BY_ASSET_GROUP`/`VENUES_BY_ASSET_GROUP`/`DATA_TYPES_BY_ASSET_GROUP` (data-pipeline reference
      data), `VALID_ASSET_GROUPS` (UI reference-data export), `ASSET_GROUP_COLORS` (strategy UI display),
      `ASSET_GROUP_DOMAINS` (bucket-naming domains), `ASSET_GROUP_KEYWORDS` (an unrelated doc-hygiene keyword matcher in
      `fix_frontmatter.py`), and
      `VALID_STRATEGY_ASSET_GROUPS = {"CEFI", "TRADFI", "DEFI", "SPORTS", "QUANT",     "OPTIONS"}` (strategy-service's
      own closed vocabulary — genuinely 5(+QUANT/OPTIONS) trading asset-groups, not doc-topic tranches). **Zero UI/API
      impact confirmed** — no hardcoded "5 AGs + cross-cutting" doc-taxonomy list exists outside docspec.py itself.

## Phase 2 — Corpus-wide retag pass

- [x] [SCRIPT] P2. Enumerated the full bare-`[cross-cutting]` population directly via `docspec.parse_frontmatter` (227
      non-terminal-status docs across `plans/active/*.md` + `plans/active/issues/*.md` at run time — the corpus had
      shrunk from the original 241 scoping estimate via other concurrent hygiene work). Cross-referenced against the
      2026-07-25 `ao_consolidated_closeout`/`ci_consolidated_closeout`/`infra_consolidated_closeout`/
      `cross_cutting_consolidated_closeout` docs' own citation sets (`CITE_RE` basename extraction) — that sweep had
      ALREADY done real per-doc judgment for most of the corpus, so 180 of 227 resolved mechanically from existing
      ground truth (78 confirmed-stays + 92 confirmed-retags + 4 self-referential hub docs + 3 self-evident scaffolding
      docs + 3 finalize-twins inheriting their source's verdict). The genuine residual — 47 docs cited in NONE of the
      four closeout docs — got real fresh per-doc reads via a 4-agent Workflow run (each agent read every doc in full,
      not just frontmatter, against the four tranches' verbatim scope definitions): 20 confirmed genuinely
      cross-cutting, 27 confirmed really-ao/ci/infra. Total: 119 retags, 108 confirmed stays.
- [x] [DOC] P2. Retagged all 119 confirmed docs in 5 batches (32 ao, 26 ci, 34 infrastructure, 14 ao, 13 ci/infra) —
      unified-trading-pm@b5800679b (32 ao, rebase-adjusted after a concurrent archival), @cb7392e77 (26 ci), @d5698952a
      (34 infrastructure), @a180fe9d0 (14 more ao), @3ba9aec2e (13 more ci/infrastructure).
      `check_ag_closeout_linkage.py` re-run after the full batch (not per-batch — the shared branch was under heavy
      concurrent write load all session, each quickmerge needed 1-5 pull-rebase retries; batching the linkage check
      after all 5 landed avoided wasting the check on a still-drifting intermediate state): 0 orphans.
- [x] [REVIEW] P2. **Done**: re-ran the fresh-audit citation-pre-filter methodology against `cross-cutting` —
      `generate_ag_closeout_audit_candidates.py --tranche cross-cutting` now reports 3/100 (3%) never-cited, down from
      37/40 (92.5%). The 3 residual never-cited docs are legitimate-content gaps (not mistags) — recent (2026-07-24/27)
      genuinely-cross-cutting docs simply not yet added to `cross_cutting_consolidated_closeout`'s own Sources/Tracks
      list; tracked as a Phase 3 follow-up below rather than fixed inline (adding them to that doc's Tracks is an
      editorial call about WHICH track each belongs under, not a mechanical retag). `check_ag_closeout_linkage.py`: 0
      orphans (676 docs scanned).

## Phase 3 — Follow-ups intentionally NOT in this plan (tracked, not silently dropped)

- [ ] [DOC] P3. Add the 3 residual never-cited-but-genuinely-cross-cutting docs found by Phase 2's verification pass to
      `cross_cutting_consolidated_closeout_2026_07_25.md`'s own Sources/Tracks lists (an editorial call about which
      Track each belongs under, not a mechanical retag — that's why it's not folded into Phase 2 itself):
      `instruments_service_e2e_live_mock_observability_2026_07_27.md`,
      `issues/mdps_features_live_launcher_exec_dispatch_never_wired_2026_07_27.md`,
      `issues/prod_terraform_drift_backlog_reconcile_2026_07_24.md`.
- [ ] [REVIEW] P3. Once the concurrent `na-eligibility-audit`/`ag-closeout-audit` skill work (see coordination note
      above) has landed and stabilized, revisit whether `ag-closeout-audit` SKILL.md's classification-mechanism section
      needs a follow-up edit now that ao/ci have real enum values (its current "no dedicated asset_group value — read
      the closeout doc's Sources list instead" workaround section becomes obsolete once Phase 1+2 land).
- [x] [REVIEW] P3. `plan_health.py` confirmed free (clean, no uncommitted changes, mtime ~4.5h old at check time) — and
      the `federated-wishing-lovelace` scheduling design turned out to be ALREADY SHIPPED by a concurrent session before
      this check, not merely unblocked: `agent-orchestrator@afe2635` (2026-07-26, "shard ag-closeout-audit dispatch by
      tranche; retime nightly gaps to 2h") added the `tranche` field to `PlanHealthDispatchRequest` + sharded
      per-tranche dispatch + widened `plan-reconciler`(01:00)/`docs-reconciler`(03:00) to a 2h gap;
      `agent-orchestrator@f4a116e` (2026-07-27) added the same tranche-sharded dispatch mode for `/na-eligibility-audit`
      plus its own `na-eligibility-auditor.timer` (07:00, 2h after `ag-closeout-auditor.timer`'s 05:00). Full chain
      verified live in the timer install scripts: 01:00 -> 03:00 -> 05:00 -> 07:00, all 2h apart, all tranche-sharded.
      Nothing left to resume.

## Codex SSOTs

- `/plans/active/task_template.md` §1-2 (LOCAL vs AO track, frontmatter)
- `/codex/11-project-management/doc-frontmatter-schema.md` (asset_group enum SSOT)
- `cursor-configs/skills/ag-closeout-audit/SKILL.md` (classification-mechanism section this plan's schema change
  eventually simplifies — do not edit until the concurrent rewrite lands, see coordination note)

## Progress Log

- **2026-07-27** — Scoped by operator directive following a fresh `/ag-closeout-audit all` run
  (`na_docs_validity_and_ao_eligibility_audit_2026_07_26.md`'s Progress Log) that measured a 37/40 false-positive rate
  on the bare-`cross-cutting` tag for ao/ci/infra content. Blast radius checked before drafting: 241 docs currently
  bare-tagged `[cross-cutting]`, 444+264 code references to the enum (mostly consumers, not hardcoded lists). Not yet
  started — Phase 1 is next.
- **2026-07-27 (later same day)** — Phases 1 and 2 both completed and shipped. Ran on a host with MULTIPLE concurrent
  Claude Code sessions sharing this exact working directory (not separate slot clones — confirmed via `ps aux` showing 5
  distinct `claude` processes with different `--resume` ids, all mounting the same repo paths), on top of the usual
  multi-slot shared-branch write load — every quickmerge in this run needed 1-5 pull-rebase-autostash retries, one
  genuine modify/delete conflict (a concurrent session archived `agent_orchestrator_alert_channel_cleanup_2026_07_13.md`
  while this run's ao-batch commit was mid-flight retagging it; resolved by accepting the archival and dropping the
  now-moot retag on that one file), and one caught-and-averted mistake: this run briefly authored a
  finalize-plan-coverage fix (`instruments_satellite_ao_dispatch_batch1_finalize_2026_07_27.md`) for a doc that turned
  out to be 4 SECONDS old and actively being authored by a different concurrent session in the SAME working tree —
  caught via the mtime<120s liveness check, the draft was moved out of the repo (not committed), and the other session
  completed its own pairing independently within the same minute, confirming the tree-wide gate was self-resolving and
  did not need an external fix. Also hit the SAME `test_gen_doc_index.py::test_build_index_is_deterministic` transient
  flake twice (build_index() called twice in one test process, racing a concurrent session's write to the exact file
  being retagged) — both times confirmed transient via a standalone re-run before retrying, per the workspace's own
  "re-run the specific failing check standalone" discipline; do not treat this specific test as flaky-by-default, it
  passed cleanly every time nothing else was concurrently touching the same file. Final numbers: 227 docs enumerated,
  119 retagged (32+14 ao, 26+11 ci, 34+2 infrastructure), 108 confirmed genuinely cross-cutting (stay as-is), 3 residual
  content gaps tracked as a Phase 3 follow-up. `check_ag_closeout_linkage.py`: 0 orphans. Cross-cutting citation
  false-positive rate: 92.5% -> 3%. Remaining work is Phase 3 only (both items explicitly deferred, see their own
  entries for why).
- **2026-07-27 (operator check-in)** — Operator asked whether `plan_health.py` was free yet, and separately whether
  `status: draft -> active` is "the orphan-detection skill's" mechanism and whether any draft `ao` plans were lying
  around. Answered: `plan_health.py` was not just free — the whole `federated-wishing-lovelace` scheduling design it was
  blocking had ALREADY shipped (`agent-orchestrator@afe2635`/`@f4a116e`, see the now-flipped item above; not a "resume",
  nothing left). On draft->active: clarified it's not exclusive to `/ag-closeout-audit` — it's `task_template.md`'s
  general draft-gated-finalize-twin convention, used by BOTH `/ag-closeout-audit` (Phase 3 carve- out) and
  `/na-eligibility-audit` (Phase 2 reclassify) whenever either creates a new gated companion doc. Checked the corpus for
  stuck/forgotten `ao`-topic drafts (`asset_group` containing `ao` OR `parent_epic` in
  `{orchestrator_master, agent_operating_framework_master}`, `status: draft`): exactly ONE match,
  `ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md`, and it is correctly still-draft (its source batch has 3/11
  todos done, not yet complete) — not stuck, working as designed. No action needed.
