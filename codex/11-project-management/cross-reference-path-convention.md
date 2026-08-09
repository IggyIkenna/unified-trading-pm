---
doc_type: codex-ssot
title: Cross-reference path convention — /plans/... and /codex/... leading-slash, PM-repo-root-relative
summary: >-
  Every free-text cross-doc reference (inline prose, the `related:` frontmatter field) must be written as a path rooted
  at the unified-trading-pm repo root with a leading slash — `/plans/active/<slug>.md`,
  `/plans/active/issues/<slug>.md`, `/codex/<NN-section>/<doc>.md` — never a bare filename, never a `../`-relative path.
  Machine-parsed identifier fields (`depends_on`, `parent_epic`, `supersedes`, `superseded_by`, `entry_point_for`) are
  OUT of scope — those stay bare slugs per `plans/PLAN_FORMAT.md`, changing their format changes backend parsing, not
  doc hygiene.
status: current
nature: ssot
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, codex, references, cross-doc-links, quality-gates]
related:
  [/plans/PLAN_FORMAT.md, /plans/active/task_template.md, /plans/active/issues/reference_path_convention_2026_07_23.md]
created: "2026-07-23"
authoritative_for: [cross-reference-path-format]
referenced_by: []
owner:
last_reviewed: 2026-10-26
code_refs: []
---

# Cross-reference path convention

## The rule

Any reference to another doc — in prose, or in the `related:` frontmatter field — is written as a path rooted at the
`unified-trading-pm` repo root, with a leading `/`:

- `/plans/active/<slug>.md`
- `/plans/active/issues/<slug>.md`
- `/plans/epics/<slug>.md`
- `/plans/archive/<year_month>/<slug>.md`
- `/codex/<NN-section>/<doc>.md`

**Never**: a bare filename with no path (`sports_foo_2026_07_19.md`), or a `../`-relative path written as two or more
dot-dot segments walking up to a numbered codex section (this doc's own body would get auto-fixed if it spelled that
shape out literally — see the Enforcement section for what the fixer does to exactly this pattern). Both of these are
ambiguous or fragile in ways the leading-slash form isn't:

- **Bare filename** — a human/agent has to search the whole corpus to find it; if two docs anywhere under `plans/` or
  `codex/` share that basename, it's genuinely ambiguous (this happens — see `README.md`, which exists in ~35 different
  directories in this corpus).
- **`../`-relative** — resolves against the CITING file's own directory, so it silently breaks the moment that file
  moves (e.g. gets archived to a different directory depth), even though the TARGET never moved. The leading-slash form
  is immune to this — it only breaks if the target itself moves, which is the actual event you want a reference check to
  catch.

## Why this exists

Found 2026-07-23 while auditing why references break: `check_codex_refs.sh` (the one pre-existing checker) only
recognized bare `codex/...` refs — the `/codex/...` and `../codex/...` forms already circulating in ~16% and ~7% of the
corpus respectively were invisible to it. Separately, no checker at all existed for whether a `related:` field's bare
filename resolved to a real file. Both gaps are closed by `scripts/plan-hygiene/check_reference_paths.py` (wired hard
into `run_hygiene_sweep.sh`, shrinking-ratchet baseline — see below).

## Out of scope: machine-parsed identifier fields

`depends_on`, `parent_epic`, `supersedes`, `superseded_by`, `entry_point_for` are **bare slugs**, not file paths —
`plans/PLAN_FORMAT.md` documents them as such (`depends_on: [epic-slug, plan-slug-YYYY_MM_DD]`, no `.md`, no path), and
`agent-orchestrator/server/regen_backlog_from_plan.py` parses `depends_on` as a slug (it explicitly strips a trailing
`.md` before matching). Writing a leading-slash path into one of these fields doesn't just violate a style rule — it
risks changing what the backend resolves. **Never apply this convention to those 5 fields.**

## Enforcement

`scripts/plan-hygiene/check_reference_paths.py`, wired hard into `run_hygiene_sweep.sh`:

1. **Format** — every codex-shaped ref anywhere in `plans/**.md` + `codex/**.md` must be `/codex/...`; every `related:`
   entry must carry a full leading-slash path.
2. **Existence** — every `/plans/...` / `/codex/...` ref must resolve to a real file.

Both are a **shrinking-ratchet baseline** (`scripts/plan-hygiene/reference_paths_baseline.yaml`), the same shape as the
fallback-import/DTZ ratchets elsewhere in this workspace's quality gates: the check hard-fails only if the live
violation count exceeds the baseline (a NEW violation landed), never on the corpus's pre-existing debt. Seeded
2026-07-23 immediately after the corpus-wide migration (`python3 scripts/plan-hygiene/fix_reference_paths.py`, 2,149
files normalized): 109 format violations (bare filenames the migration couldn't safely auto-resolve — ambiguous or
genuinely dangling) and 1,286 existence violations (pre-existing dangling refs — docs describing
planned-but-never-shipped codex content, refs to plans since renamed/archived under a different name). Full list +
cleanup tracking: `/plans/active/issues/reference_path_convention_2026_07_23.md`. Ratchet DOWN as entries get fixed
(`--update-baseline` after fixing a batch) — never hand-raise a count.

## What `/plan-reconcile` covers that this mechanical check can't

The hygiene check is deterministic: does this path exist, is it in the right format. It cannot decide:

- **Which of several ambiguous matches is the right target** for a bare filename this migration left untouched (e.g. a
  `related:` entry naming a file that exists in more than one place) — a judgment call, not a lookup.
- **What the correct reference is when a doc has genuinely moved/been renamed/archived** — this needs a live
  grep-then-decide pass, not a static existence check.
- **Whether a dangling reference should be fixed (the target should exist and was lost) or removed** (the reference
  itself is stale and the claim it made no longer applies).

`/plan-reconcile`'s AO-dispatch-readiness + contradiction-sweep phases are the right home for these — see
`cursor-configs/skills/plan-reconcile/SKILL.md`.

## Archival must update referrers — the gap this exposed

`CLAUDE.md`'s "5-step archival ritual" (migrate DEFERRED → banner → codex-alignment check → update CLAUDE.md/codex →
clear lock) does not name a "update every referrer's path" step — checked 2026-07-23, it was never there to break.
Empirically, `plans/archive/` holds 1,564 files, so plans DO get physically moved by some process — meaning a
leading-slash-rooted reference to a plan that later gets archived-by-move (`/plans/active/<slug>.md` →
`/plans/archive/<year_month>/<slug>.md`) still breaks; the leading-slash convention fixes reference fragility from the
CITING file moving, not from the TARGET moving. Archival must add a 6th step: grep the corpus for every referrer of the
doc being archived/moved/renamed, and update each one's reference to the new path — tracked as its own todo, see the
issue doc above.
