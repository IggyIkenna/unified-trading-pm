---
doc_type: issue
title:
  "/docs-reconcile autonomous sweep 2026-07-30 — a dated codex-freshness gate cliff 16 days out, an authoritative_for
  collision that is also a live SSOT contradiction, and 4 dead doctrine refs with no successor"
summary: >-
  Parking + findings doc for the 2026-07-30 `/docs-reconcile` run (full corpus, autonomous mode, standing in for the
  `docs-reconciler.timer` worker). All five Phase-0 deterministic checks were GREEN at entry and stayed green at exit.
  The run auto-fixed the two mechanical classes it is authorized to: 33 archived-`unified-trading-codex/` path
  references across 25 cursor-rule files repointed to PM's folded `codex/`, and 62 no-longer-reproducing entries dropped
  from the two shrinking link ratchets (body-link 118 to 59, doc-ref 18 to 15) — both verified still-green after
  tightening. What it could NOT resolve autonomously is recorded here. The headline is a DATED time bomb the existing
  gate cannot see: 144 gated codex docs were bulk-stamped `last_reviewed: 2026-05-17` on one day, so they all cross the
  90-day staleness limit together on 2026-08-15, taking `check_codex_doc_freshness.py` (a hard PM QG gate, ratcheted at
  24) from 24 to roughly 168 violations and turning the PM quality gate RED for every commit until someone re-stamps or
  re-scopes. Second, `slot-label grammar` is claimed in `authoritative_for:` by two `status: current` codex-ssot docs
  whose grammars genuinely disagree (one says the archetype enum has 18 members, the other 57; the code has 60) — an
  authority call the skill forbids auto-resolving in any mode.
status: open
nature: issue
asset_group: [infrastructure] # retagged 2026-07-31 (corpus-sweep meta fold-in) -- was [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [docs-reconcile, retrieval-layer, codex-freshness, authoritative-for, operator-decision, doc-integrity]
related:
  [
    /cursor-configs/skills/docs-reconcile/SKILL.md,
    /codex/11-project-management/doc-frontmatter-schema.md,
    /codex/06-coding-standards/strategy-identity-versioning.md,
    /plans/archive/2026_07/issues/plan_reconcile_autonomous_sweep_2026_07_30.md,
    /plans/archive/2026_07/docs_retrieval_layer_reconcile_2026_07_23.md,
  ]
created: 2026-07-30
author: unknown
parent_epic: agent_operating_framework_master
priority: P1
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.16
assigned_role: NA
drift_direction: none
source:
  "/docs-reconcile autonomous full-corpus run, 2026-07-30, slot-3 — Phase 3 routing produced 2 operator-gated items and
  3 non-authority findings the run deliberately did not guess at"
depends_on: []
resolved_by:
locked_by:
context_scope:
  [
    /cursor-configs/skills/docs-reconcile/SKILL.md,
    /codex/11-project-management/doc-frontmatter-schema.md,
    /codex/06-coding-standards/strategy-identity-versioning.md,
    /plans/archive/2026_07/issues/plan_reconcile_autonomous_sweep_2026_07_30.md,
  ]
supersedes:
superseded_by:
---

# /docs-reconcile autonomous sweep — 2026-07-30 parked decisions + findings

## Run context (read this before acting on anything below)

- **Scope**: full corpus, autonomous mode, no operator reachable. Per the skill's ASK > PARK rule, everything under
  "Parked" would have been a batched interactive question if anyone had been in the session — parking is the fallback,
  not the preference. **Answer these in a normal interactive session and the next run applies them.**
- **Sub-agent caveat (affects confidence, stated honestly)**: the skill's Phase 1 is specified as a fan-out of up to 10
  parallel read-only hunters. No `Task`/`Agent` tool was available in this harness, so all six hunter passes were run
  sequentially by the single run agent, and Phase 2's adversarial refuter/confirmer split was self-performed rather than
  independently staffed. Findings below were still refuted before being reported (9 `authoritative_for` near-duplicate
  pairs were raised and 8 refuted; see below), but a genuinely independent refuter was not available.
- **Counts are measurements at the moment taken**, not durable numbers.

## Parked — operator ruling required

### P0-A. `check_codex_doc_freshness.py` goes RED on 2026-08-15 — a 144-doc bulk-stamp cohort tips at once

This is the finding of the run, and it is invisible to every check that exists today, because today everything passes.

Measured on 2026-07-30 against the 4 cutover-critical dirs the gate covers:

- Gate state today: 308 docs scanned, **24 violations, strict == baseline == 24, gap = 0.** All 24 are
  `no-last_reviewed-field` (a missing stamp). **Zero docs are date-stale** — max age among stamped docs is 84 days,
  under the 90-day limit.
- **144 of the 284 stamped gated docs carry the identical `last_reviewed: 2026-05-17`** — a single bulk-stamp pass.
  `2026-05-17 + 90d = 2026-08-15`.
- Projected gated violations if nothing changes: `+7d` → 25 · `+14d` → 36 · **`+30d` → 224** · `+45d` → 231 · `+60d`
  → 250.

So the gate holds at 24 for another two weeks and then jumps by roughly an order of magnitude in a single day. Because
this is a **hard PM QG gate**, that is a repo-wide commit blocker arriving on a known date, and the ratchet cannot
absorb it (a shrinking ratchet only ever goes down).

The remediation is an authority call — re-stamping 144+ docs is either a real review or a rubber stamp, and which one it
is, is exactly the operator's decision, not a worker's.

- **A: schedule a real staged re-review before 2026-08-15, cohort-split so this never re-synchronises [WORKER REC]** —
  re-stamp in batches with deliberately staggered dates (not one bulk date), so the cliff becomes a trickle. Keeps the
  gate meaningful. Costs the most review time, and needs starting now, not on 2026-08-14.
- **B: bulk re-stamp all 144 to today's date.** Cheap, unblocks CI, but re-arms the identical cliff for 2026-11-13 and
  converts `last_reviewed` into a meaningless field — the gate would then be measuring "when did someone last run sed",
  which is the failure mode the gate exists to prevent.
- **C: raise `DEFAULT_STALENESS_DAYS` (e.g. 90 → 180).** One-line, buys ~3 months, but only moves the same cliff and
  weakens the gate for every doc.
- **D: change the gate's shape** — make staleness advisory/report-only and keep only `no-last_reviewed-field` hard.
  Removes the cliff permanently, at the cost of no longer enforcing freshness at all.
- Other: operator free-text.

Note the interaction with the standing widen-question: the gate covers 308 of 871 codex docs. Widening it to all of
codex would add 563 docs and **~513 further violations** (513 of the 563 ungated docs have no `last_reviewed` at all).
Widening before resolving this cliff would be strictly worse. Distribution by ungated dir was measured this run — worst:
`09-strategy` 185/203, `14-customer-journeys` 123/126, `15-runbooks` 61/72, `06-coding-standards` 54/63.

### P0-B. `slot-label grammar` has two `status: current` SSOT claimants, and they contradict each other

> **✅ RESOLVED 2026-07-31 — OPTION C (merge) was taken, by another session, in `unified-trading-pm@257ee3a13`**
> (_"docs(codex): merge naming-convention.md into strategy-identity-versioning.md (P0-B SSOT collision)"_ — note the
> commit subject cites this very finding id). The old `architecture-v2/naming-convention.md` under `codex/09-strategy/`
> was DELETED (deliberately named here WITHOUT its full former path — a leading-slash ref to a deleted file would
> register as a dangling reference) and its content folded into
> `/codex/06-coding-standards/strategy-identity-versioning.md` (+207 lines), which is now the single
> `authoritative_for:` claimant for slot-label grammar; `codex/00-SSOT-INDEX.md`, `/codex/09-strategy/README.md`, the
> strategy-description template and two `.cursor/rules` files were repointed in the same commit. **Found + recorded
> during the 2026-07-31 corpus-sweep** because this doc's `related:` list still named the deleted path, which failed
> `check_frontmatter_schema` ("referenced doc … does not exist (NEW — not in doc_reference_baseline.yaml)") and blocked
> commits repo-wide; that dangling entry has been dropped (the merge target was already listed alongside it). **The
> archetype-count item at the end of this section is ALSO closed** — re-measured this sweep by AST rather than trusted
> from the old note: `StrategyArchetype` in
> `unified-api-contracts/unified_api_contracts/internal/architecture_v2/enums.py` has **60** members today, and the
> surviving SSOT now states exactly that in both places it counts (`| Archetype | 60 enum |` and "Archetype axis (60
> values — VERIFIED, code ground truth)"). Both the stale `18-enum` and the stale `57` claims are gone with the deleted
> doc. So this whole P0-B finding is closed, with nothing left to carry forward. The analysis below is retained verbatim
> as the record of why the collision existed and how the options were framed.

Both are `doc_type: codex-ssot`, both `status: current`, both name the same topic in `authoritative_for:`:

- `architecture-v2/naming-convention.md` under `codex/09-strategy/` (deleted — see resolution note above; named here
  WITHOUT its full former path so it doesn't register as a dangling reference) —
  `authoritative_for: [canonical strategy-id naming grammar (slot-label / fully-qualified / bare-slot)]`
- `/codex/06-coding-standards/strategy-identity-versioning.md` —
  `authoritative_for: [strategy identity + versioning (5-layer identity, archetype-ID rules, slot-label grammar)]`

`rg -l '^authoritative_for:.*slot-label grammar' codex/` therefore returns two docs — a coin flip, which is precisely
what the field exists to prevent. **Neither doc references the other**, so there is no parent/child deference to read it
as a legitimate split (this was the refuter's first hypothesis and it failed).

It is not only a retrieval collision — the two grammars genuinely disagree:

| Claim                | `naming-convention.md`                              | `strategy-identity-versioning.md`                                                          |
| -------------------- | --------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Slot-label grammar   | `ARCHETYPE@venue-asset-instrument-period-quote-env` | `{archetype_id}@{venue_scope}-{instrument_scope}[-{timeframe}]-{share_class}[-v{N}]-{env}` |
| Slot version `-v{N}` | absent from the grammar                             | present and optional                                                                       |
| Archetype enum size  | "Archetype axis (57 values)"                        | "`archetype_id` from the 18-enum" (repeated at 3 places)                                   |

**Code ground truth measured this run: `StrategyArchetype` in
`unified-api-contracts/unified_api_contracts/internal/architecture_v2/enums.py` has 60 members** (AST count). So the
`18-enum` claim is badly stale and the `57` claim is also now behind code. `naming-convention.md` itself dates its
count: "Phase 9 expansion (2026-04-25) and the 2026-05-18 taxonomy decision brought it to 57."

Which doc keeps the topic is an authority call the skill forbids auto-resolving in any mode, and this run was
additionally barred from editing `codex/**`.

- **A: `naming-convention.md` keeps `slot-label grammar`; `strategy-identity-versioning.md` narrows its
  `authoritative_for` to identity + versioning only and links out for the grammar [WORKER REC]** — the naming doc is the
  more specific, more current one (it carries the dated taxonomy history and the three-form table), and the
  coding-standards doc's own subject is versioning. Also fixes the 18-vs-60 staleness by deleting the duplicated grammar
  rather than maintaining two copies.
- **B: the reverse** — `strategy-identity-versioning.md` keeps the grammar as part of the identity contract, and
  `naming-convention.md` narrows to the fully-qualified/bare-slot forms. Defensible if slot labels are considered a
  coding standard first.
- **C: merge the two docs.** Cleanest long-term, largest blast radius (both are widely `referenced_by:`).
- Other: operator free-text.

**Regardless of A/B/C, the archetype count needs correcting to 60 in whichever doc survives** — that part is a
correctness fact, not an authority call, but it lives in `codex/**` so this run could not apply it.

## Findings that need no ruling (not parked — just not this run's to fix)

### P1-C. Four doctrine references point into the archived `unified-trading-codex` with no successor

**Re-verified 2026-08-08 (docs-reconcile, dispatch agt-bb1c67): 3 of 4 rows are now resolved/moot, independently of this
doc — only row 3 remains genuinely open.** The run repointed 33 such refs where the target provably exists under PM's
`codex/`. These 4 had **no counterpart** at the time, so repointing them would have manufactured a knowingly-wrong path,
and they were deliberately left alone:

| Location                                                  | Dead target                                            | Successor hunt result                                                                                                                                                                    | Status                                                                                                                                                                                                                                                                                                                                                         |
| --------------------------------------------------------- | ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `cursor-rules/architecture/strategy-data-access.mdc:11`   | `09-strategy/cross-cutting/config-architecture.md`     | only match is `/codex/09-strategy/_archived_pre_v2/cross-cutting/config-architecture.md` — pointing a live rule at an `_archived_pre_v2` doc is worse than a dead link                   | ✅ **MOOT** — the whole top-level `cursor-rules/` tree (this file included) was archived 2026-08-02 to `plans/archive/cursor-rules_2026_08_02/architecture/strategy-data-access.mdc`; the citing rule is no longer live, same disposition already applied to 2 sibling `cursor-rules/*.mdc` findings in `docs_reconcile_remaining_broken_links_2026_08_02.md`. |
| `.cursor/rules/core/provider-api-version-manifest.mdc:16` | `02-data/provider-api-version-manifest.md`             | none anywhere                                                                                                                                                                            | ✅ **FIXED 2026-08-05** (`unified-trading-pm@72b0f5724`, per `docs_reconcile_remaining_broken_links_2026_08_02.md`) — dropped the dead `CODEX:` pointer line; live-verified 2026-08-08, the file no longer contains it and the rule body is self-sufficient.                                                                                                   |
| `.cursor/rules/misc/sync-system.mdc:14`                   | `unified-trading-codex/scripts/sync-rules-and-docs.py` | script does not exist in any repo — the whole rule may be obsolete                                                                                                                       | ⬜ **STILL OPEN** — live-verified 2026-08-08: the file already carries a 2026-07-30 NOTE explaining the script is gone, but the `DO:` line directly below still instructs running it. Needs a human to decide: strip the `DO:` line (keep RULE/WHY as aspirational pending a successor script) vs. delete the whole rule.                                      |
| `.cursor/rules/ui/ui-quality-gates-typescript.mdc:18`     | `06-coding-standards/quality-gates-ui-typescript.md`   | nearest is `quality-gates-ui-template.sh` (a shell template, not the doc); current UI SSOT is likely `/codex/06-coding-standards/ui-testing-layers.md` but that is not a provable rename | ✅ **RESOLVED** (date untracked, found already-fixed 2026-08-08) — the file's "Source of truth" section now explicitly states "dead reference, no live successor (2026-07-30)" with the same successor-hunt reasoning, in prose rather than a markdown-link, so it no longer trips the body-link checker and no longer silently asserts a working link.        |

Only row 3 (`sync-system.mdc`) needs a human decision now. **Do not blanket-fix it with a path rewrite** if that
decision ever touches the `provider-api-version-manifest.mdc` row's history: that one was (correctly) a markdown body
link held in `scripts/quality_gates/doc_body_link_baseline.yaml`, so any similar future rewrite of a baselined broken
link must repoint to a real target, not just delete the string, or it converts a baselined entry into a NEW one and
fails `check_doc_body_links.py`.

### P1-D. Unterminated bold span renders a whole block bold in a live issue doc

`plans/archive/2026_08/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md:429` opens
`**Original investigation (2026-07-28) — from-scratch raw-column derivation, investigated and STOPPED:` and never closes
the span before the paragraph ends at :434. The following line then repeats "and STOPPED (not built) because…", so this
looks like a botched edit rather than a pure formatting slip — deciding whether the duplicated clause should be deleted
or the bold simply closed is a content question, which is why this run did not guess. This sits in the **plans** corpus,
so it routes to `/plan-reconcile` rather than being fixed here.

Scope note: the same structural check over the **codex** corpus (the skill's stated Phase-1.6 population — docs
body-edited in the last 24h, 24 codex/cursor-configs docs) found **zero** structural breaks.

### P2-E. Five bare-name mentions of the archived repo remain in the rules trees

Prose that names `unified-trading-codex` without a path, so it was out of the mechanical path-repoint's scope:
`cursor-rules/architecture/pipeline-mode-partition-structure.mdc:79` (already correct — says "folded into
`unified-trading-pm/codex/`"), `.cursor/rules/ci-cd/act-secrets-setup.mdc:14`,
`.cursor/rules/testing/test-coverage-targets.mdc:80`, plus the two the run did fix in-place because it was already
editing those files (`codex-maintenance.mdc:13`, `codex-no-absolute-paths.mdc:16`). The remaining ones are stale
terminology, not broken links.

## Todos

> **Converted from prose to tracked checkboxes 2026-07-31** (zero-checkbox sweep, all-9-tranches re-run — register:
> `/plans/active/issues/zero_checkbox_sweep_all_tranches_2026_07_31.md`). This doc is a **parking register**: every
> finding above was recorded as prose only, so a repo-wide commit blocker with a KNOWN arrival date (P0-A, 2026-08-15)
> scored `open_todos: 0` and was invisible to every backlog and open-todo count. That is precisely the failure mode this
> sweep exists to catch, and this doc's own Progress Log named itself as an instance. Findings are unchanged below —
> these checkboxes only make them countable. `assigned_vm: NA` is unchanged, so nothing here auto-dispatches; the two
> `[OPERATOR]` items are decisions, not worker tasks.

- [x] ✅ [OPERATOR] P0. **Rule on P0-A before 2026-08-15 — the `check_codex_doc_freshness.py` cliff.** — **RESOLVED
      2026-08-02, option A applied** (the worker recommendation: staged, deliberately cohort-split re-review, not a bulk
      re-stamp). All 144 docs sharing `last_reviewed: 2026-05-17` were re-reviewed for real content accuracy (not
      rubber-stamped) across 4 shards and re-dated onto a genuinely staggered spread (2026-08-29 through 2026-09-08+,
      ~11 distinct dates). Verified: `grep -rl "last_reviewed: 2026-05-17" codex/` now returns **zero** matches — the
      bulk-stamp cohort no longer exists, so the single-day cliff this todo was filed against cannot recur on
      2026-08-15. Simulated against the real gate (`check_codex_doc_freshness.py`, 90-day window) at 2026-08-16 (the day
      after the old cliff): 111 violations total but **zero in the re-reviewed shards**; the figure is unrelated
      pre-existing corpus drift, not this cohort. Shipped: shard offset-0 (38 docs — the SHA originally recorded here
      does not resolve in any local clone, most likely a transcription typo when this entry was written 2026-08-02;
      flagged 2026-08-03 by `check_plan_commit_sha_evidence.py`, not re-derived further), `@ff8b38f70` (shard offset-2,
      37 docs, confirmed ancestor of `origin/live-defi-rollout`), `@ab5bbcbf2` (shard-2 recovery, 38 docs, confirmed
      ancestor), plus a 4th shard folded into the same freshness-cliff pass. (repo: `unified-trading-pm`)
- [x] ✅ [DOC] P0. **P0-B `slot-label grammar` dual-SSOT collision — RESOLVED 2026-07-31** by another session via OPTION
      C (merge), `unified-trading-pm@257ee3a13`; see the resolved banner in §P0-B for the full evidence. Flipped here so
      the register reflects it.
- [ ] [DOC] P1. **Resolve the last dead `unified-trading-codex` doctrine ref with no successor (P1-C, narrowed
      2026-08-08)** — 3 of the original 4 rows are independently resolved/moot (see §P1-C table for evidence:
      `strategy-data-access.mdc` MOOT via the 2026-08-02 `cursor-rules/` archival, `provider-api-version-manifest.mdc`
      FIXED 2026-08-05, `ui-quality-gates-typescript.mdc` already rewritten to explanatory prose). Only
      `.cursor/rules/misc/sync-system.mdc:14-17` remains: needs a human to decide whether to strip the `DO:` line (keep
      the rule aspirational pending a successor sync script) or delete the rule outright, since the script it names does
      not exist anywhere. (repo: `unified-trading-pm`)
- [x] ✅ [DOC] P1. **Fix the unterminated bold span (P1-D)** at
      `/plans/archive/2026_08/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md:429` — the span never closes
      before the paragraph ends at :434 and the next line repeats the "and STOPPED (not built) because…" clause, so this
      is a botched edit, not a formatting slip. Decide whether the duplicated clause is deleted or the bold merely
      closed (a content call — do not guess). (repo: `unified-trading-pm`) **RESOLVED — `unified-trading-pm@7509ec538`
      (2026-07-31, slot-3), "fix unterminated bold span + duplicated clause in perp_funding_data_semantics_and_cadence".
      Verified 2026-08-03 (na-eligibility-audit): target doc now shows one correctly-closed bold span at line 466-467
      with no duplicate clause (grep confirms only one "and STOPPED" occurrence in the 883-line file). This item was
      already fixed 2 days before the 2026-08-02 na-eligibility-audit pass, which re-verified it as still open without
      checking the target file's actual content — flagged here so a future incremental-diff run doesn't re-surface it.
- [x] ✅ [DOC] P2. **Retire the 5 bare-name `unified-trading-codex` mentions (P2-E)** in the rules trees — stale
      terminology, not broken links, so this is a wording pass: `.cursor/rules/ci-cd/act-secrets-setup.mdc:14` and
      `.cursor/rules/testing/test-coverage-targets.mdc:80` were the two remaining genuinely stale ones (the
      `pipeline-mode-partition-structure.mdc:79` mention was already correct, and two more were fixed in-place in the
      2026-07-30 run). **RESOLVED 2026-08-03** by the docs_reconciler autonomous sweep: `act-secrets-setup.mdc`'s
      example sibling-repo now reads `unified-api-contracts` (a real, live sibling); `test-coverage-targets.mdc`'s "four
      permanently exempt repos" table dropped the `unified-trading-codex` row and now correctly says "three". All 5
      original P2-E mentions are now accounted for. (repo: `unified-trading-pm`)

## Applied this run (no ruling needed — recorded for the audit trail)

1. **33 archived-codex path refs repointed** across 25 files in `cursor-rules/**` + `.cursor/rules/**`, from
   `unified-trading-codex/…` to `unified-trading-pm/codex/…`, matching the convention those files already used
   elsewhere. Includes 6 Cursor `globs:` frontmatter patterns that had been matching **nothing** since the repo was
   archived — i.e. 4 rules (`codex-maintenance`, `codex-no-absolute-paths`, `coding-standards-alignment`,
   `plan-placement`) had silently stopped firing and now fire again on PM's `codex/`.
2. **Both link ratchets tightened by dropping non-reproducing entries** via each checker's own `--update-baseline`:
   body-link `118 → 59` (59 dropped), doc-ref `18 → 15` (3 dropped). Both regenerations were **pure deletions, zero
   additions** — no new breakage was laundered into a baseline. Both checkers re-verified green against the tightened
   baselines.

## Verification at exit

All five Phase-0 checks re-run after every edit: retrieval-layer parity PASS · `check_frontmatter_schema` 1851 docs /
zero violations · `check_doc_body_links` 1897 docs / zero new broken links (against the tightened baseline) ·
`gen_doc_index.py` builds (1673 docs, ~1.3s) · codex freshness 24/24 strict-vs-baseline, gap 0.

**Concurrency note (the run was not alone in the repo).** Corpus counts drifted downward mid-run (1898→1897→1896)
despite `git status` showing zero deletions, which was chased rather than hand-waved: the cause is peer agents moving
issue docs between `plans/active/` and `plans/archive/` while this run was in progress (`plans/archive/**` is excluded
from both scanners' corpora), with the slot ff-pull cron bringing those commits into the working tree. Local HEAD moved
`a2c264df4 → aacf460f2` during the run. Confirmed by the final fast-forward, which restored
`deployment_ui_vitest_coverage_gate_broadly_red_2026_07_29.md` to `active/` and took the counts straight back up to
1897/1851. Nothing was lost. The practical consequence for future runs: **any corpus count in a `/docs-reconcile` report
is a sample, not a stable measurement**, and the tightened link ratchets were deliberately re-verified against the
post-merge state (still green) rather than only against the pre-merge state they were generated from.

## Incidental blocker found while shipping — PM `quality-gates.sh` is RED for everyone right now

Not a `/docs-reconcile` finding (recorded here because it was found by this run and it currently blocks the normal
`quickmerge` ship path for **every** agent in this repo, so the next worker will hit it immediately).
`bash scripts/quality-gates.sh --no-fix` exits 1 with **7 failures, none in any file this run touched**, in two
unrelated clusters:

1. **6 × `tests/unit/test_capability_param_schema.py` + `test_capability_verdict_matrix.py`** — root cause is a broken
   sibling venv, not PM code:
   `param schema GAP: ImportError: cannot import name 'iter_route_contexts' from 'fastapi.routing'` in
   `strategy-service/.venv`. The exporter probes strategy-service's own venv by design, so a fastapi version skew there
   fails PM's gate. Fix belongs in strategy-service's dependency set.

> **Owner for the stale-venv / `iter_route_contexts` ImportError**:
> /plans/archive/2026_08/issues/stale_service_venvs_below_declared_fastapi_floor_2026_08_11.md

2. **1 × `scripts/quality_gates/test_check_repo_docs_ssot.py::test_live_corpus_has_zero_new_drift`** — all 6 flagged
   files live in `instruments-service-agentwork-sports-2026-07-13/`, a **stale agent scratch clone** sitting in the
   workspace root since 2026-07-13, untracked by PM. This looks like the same bug class `check_frontmatter_schema.py`
   already guards against with its explicit `.claude/` worktree exclusion ("would otherwise sweep up a live agent's
   worktree copy and false-flag it"): `check_repo_docs_ssot.py` has no equivalent scratch-clone exclusion, so a leftover
   `*-agentwork-*` directory turns the PM gate red. **Do not "fix" this with `--update-baseline`** — that would
   permanently bake a transient scratch directory's debt into the shared baseline. The right fix is either deleting the
   stale clone or teaching the checker to skip `*-agentwork-*`/scratch clones.

Because of (1)+(2) this run shipped under the CLAUDE.md closed carve-out (dirty-deps + PM `docs(plans):`); every path in
the commit is a strict-quickmerge carve-out file and no source file was involved. Worth noting for the skill itself:
`quickmerge --agent` has **no doc-only bypass** of the Pass-1 QG sentinel, so a docs-only skill like this one is fully
blocked from its documented ship path whenever any unrelated repo in the workspace is red.

## Progress Log

- **na-eligibility-audit 2026-07-30** (infra tranche, incremental run): **KEEP-NA, valid.** In scope because the doc was
  created hours earlier the same day and carried no verdict marker. Read end-to-end; `grep -cE '^- \[ \]'` = **0**,
  matching this verdict's item count (zero todo-level verdicts — the doc-level verdict is the whole verdict). NA is
  correct on the merits, not by default: both headline items are authority calls no worker may settle — **P0-A** is a
  re-stamp-vs-re-review policy choice on 144 bulk-stamped codex docs, and **P0-B** picks which of two `status: current`
  SSOTs keeps `authoritative_for: slot-label grammar`. Both additionally require editing `codex/**`, which is
  operator-ruling-gated in every mode, so neither could be applied here even if the call were obvious. Nothing in the
  doc is resolved or moot → not ARCHIVE; no bounded, worker-determinable content → not RECLASSIFY.
- **Zero-checkbox note (reported, deliberately not "fixed" here).** This doc holds real dated work — P0-A projects
  `check_codex_doc_freshness.py` from 24 to ~168 violations on **2026-08-15**, a hard PM QG gate, i.e. a repo-wide
  commit blocker on a known date — but expresses all of it as prose, so it is invisible to every backlog and open-todo
  count (this audit's own inventory scores it `open_todos: 0`). Converting parked A/B/C decisions into todos is
  authoring, not reconciliation, and is outside this skill's autonomous apply set, so it was not done. The class is
  already owned corpus-wide by `issue_docs_zero_checkbox_sweep_2026_07_24.md`, which does not yet name this doc —
  annotated there rather than fixed here, per the findings-triage "fits another plan → annotate, don't fix" rule.
- **Integrator correction 2026-07-30 (na-eligibility-audit tranche integration).** The owning doc named above was
  **ARCHIVED** to `/plans/archive/issues/issue_docs_zero_checkbox_sweep_2026_07_24.md` by `unified-trading-pm@17ba71f10`
  while this tranche was running, so the "`status: open`, `assigned_vm: planning`" citation above is stale and the infra
  tranche's annotation could not be landed there (a modify/delete conflict — the archival was accepted rather than
  resurrecting an archived doc). **The annotation's substance is preserved here instead**, because the owning doc's
  closure did not resolve it: that sweep's population was the docs referenced by the **5 asset-group** closeouts, which
  structurally excludes the non-AG tranches (`meta`/`infrastructure`/`cross-cutting`/`ao`/`ci`). Two live zero-checkbox
  instances sit in exactly that blind spot, both `asset_group: meta`, both created 2026-07-30: **this doc** (0
  checkboxes, carrying the dated 2026-08-15 `check_codex_doc_freshness.py` 24→~168 hard-gate cliff above) and
  `/plans/archive/2026_07/issues/plan_reconcile_autonomous_sweep_2026_07_30.md` (1 todo, but its 4 parked decisions are
  prose-only). Autonomous-mode parking registers are a recurring source of this class. **Open follow-up for the
  operator/next-toucher**: re-run the zero-checkbox sweep with the population widened to all 9 tranches — it currently
  has no owning active doc.
- **na-eligibility-audit 2026-08-02** (infra tranche, incremental run): **KEEP-NA, valid — unchanged from the 2026-07-30
  verdict, and the reason is now stronger, not weaker.** In scope this run because the 2026-07-31 zero-checkbox sweep
  converted this doc's prose findings into real checkboxes and P0-B was resolved. Read end-to-end; `grep -cE '^- \[ \]'`
  = **4** (was 0 at the last marker — that conversion is exactly why), matching this verdict's item count. All 4 remain
  authority calls: the `[OPERATOR] P0` codex-freshness cliff, two `[DOC] P1`s each needing a human to choose between
  repointing and deleting (the 4 successor-less doctrine refs; the botched-edit-vs-formatting-slip bold span, which the
  doc itself routes to `/plan-reconcile`), and a `[DOC] P2` wording pass. **The `[OPERATOR] P0` is now 13 days from
  becoming an outage** — `check_codex_doc_freshness.py` goes 24 → ~168 violations on **2026-08-15**, when 144 docs
  bulk-stamped `last_reviewed: 2026-05-17` cross the 90-day limit together; it is a HARD PM QG gate and a shrinking
  ratchet cannot absorb it. Re-verified still `- [ ]` this run and re-surfaced in this run's report rather than left to
  live only inside a parking register. Options A-D with a worker recommendation are already in §P0-A.
- **na-eligibility-audit 2026-08-03** (ao tranche): **KEEP-NA, stale item closed.** In scope because the doc was edited
  since the 2026-08-02 marker (`context_scope` backfill, commit 9cfc2d4d5-adjacent). Read end-to-end;
  `grep -cE '^- \[ \]'` = **2** now (was 4 at the last marker). Found the P1-D bold-span item (line 248) was already
  fixed by `unified-trading-pm@7509ec538` (2026-07-31) — 2 days before the 2026-08-02 pass re-verified it as open
  without checking the target file's content — closed it above with evidence. The 2 survivors (P0-A codex-freshness
  cliff, P1-C dead-doctrine-refs) remain genuine authority calls, matching every prior pass; doc stays NA.
- **context-scout 2026-08-03**: re-verified context_scope (4 entries) — all four still directly cited by the doc's own
  body; no change needed.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **docs-reconcile 2026-08-08** (dispatch agt-bb1c67): re-verified P0-A live
  (`grep -rl "last_reviewed: 2026-05-17" codex/` → **zero** matches, confirming the resolved-2026-08-02 fix holds — the
  cliff cannot recur). Re-verified all 4 P1-C rows individually against the live filesystem (not trusting the table's
  prior text): 3 are independently resolved/moot since this doc was last touched (evidence + dates added to the §P1-C
  table and the todo narrowed accordingly); only `sync-system.mdc` remains a genuine open human decision.
  `check_codex_doc_freshness.py --strict` re-run against the correct `--workspace-root` (parent of
  `unified-trading-pm/`, not the PM root itself — the script has no fallback for the latter, unlike
  `check_doc_retrieval_layer_parity.py`, which does): 309 docs scanned, 26 violations, matches the 26-baseline exactly
  (gap 0).
- **na-eligibility-audit 2026-08-08** (ao tranche): KEEP-NA, valid — in scope only because today's docs-reconcile pass
  narrowed the P1-C table (3 of 4 rows resolved/moot). `grep -cE '^[[:space:]]*[-*] \[ \]'` = **1**, matching. The sole
  survivor (`sync-system.mdc` — strip the `DO:` line vs. delete the rule outright) is still an explicit human decision
  per its own text; no bounded worker-determinable content added or removed by today's edit. Not re-litigated.

- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep)**: KEEP-NA, valid — `grep -cE '^[[:space:]]*[-*] \[ \]'` =
  **1**, matching. Sole surviving item (`.cursor/rules/misc/sync-system.mdc:14` — strip the `DO:` line vs. delete the
  rule outright) remains an explicit human decision on a rule whose backing script no longer exists; the other 3 of the
  original 4 P1-C rows were independently resolved/moot by 2026-08-08, correctly narrowing this item without a whole-doc
  flip. No new bounded content on independent re-read.
