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
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [docs-reconcile, retrieval-layer, codex-freshness, authoritative-for, operator-decision, doc-integrity]
related:
  [
    /cursor-configs/skills/docs-reconcile/SKILL.md,
    /codex/11-project-management/doc-frontmatter-schema.md,
    /codex/09-strategy/architecture-v2/naming-convention.md,
    /codex/06-coding-standards/strategy-identity-versioning.md,
    /plans/active/issues/plan_reconcile_autonomous_sweep_2026_07_30.md,
    /plans/archive/2026_07/docs_retrieval_layer_reconcile_2026_07_23.md,
  ]
created: 2026-07-30
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

Both are `doc_type: codex-ssot`, both `status: current`, both name the same topic in `authoritative_for:`:

- `codex/09-strategy/architecture-v2/naming-convention.md` —
  `authoritative_for: [canonical strategy-id naming grammar (slot-label / fully-qualified / bare-slot)]`
- `codex/06-coding-standards/strategy-identity-versioning.md` —
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

The run repointed 33 such refs where the target provably exists under PM's `codex/`. These 4 have **no counterpart**, so
repointing them would have manufactured a knowingly-wrong path, and they were deliberately left alone:

| Location                                                  | Dead target                                            | Successor hunt result                                                                                                                                                                   |
| --------------------------------------------------------- | ------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `cursor-rules/architecture/strategy-data-access.mdc:11`   | `09-strategy/cross-cutting/config-architecture.md`     | only match is `codex/09-strategy/_archived_pre_v2/cross-cutting/config-architecture.md` — pointing a live rule at an `_archived_pre_v2` doc is worse than a dead link                   |
| `.cursor/rules/core/provider-api-version-manifest.mdc:16` | `02-data/provider-api-version-manifest.md`             | none anywhere                                                                                                                                                                           |
| `.cursor/rules/misc/sync-system.mdc:14`                   | `unified-trading-codex/scripts/sync-rules-and-docs.py` | script does not exist in any repo — the whole rule may be obsolete                                                                                                                      |
| `.cursor/rules/ui/ui-quality-gates-typescript.mdc:18`     | `06-coding-standards/quality-gates-ui-typescript.md`   | nearest is `quality-gates-ui-template.sh` (a shell template, not the doc); current UI SSOT is likely `codex/06-coding-standards/ui-testing-layers.md` but that is not a provable rename |

Each needs a human to either repoint the prose at the real current doc or delete the dead reference. **Do not
blanket-fix the second row with a path rewrite**: it is a markdown body link currently held in
`scripts/quality_gates/doc_body_link_baseline.yaml`, so rewriting the string without fixing the target converts a
baselined broken link into a NEW one and fails `check_doc_body_links.py`.

### P1-D. Unterminated bold span renders a whole block bold in a live issue doc

`plans/active/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md:429` opens
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
