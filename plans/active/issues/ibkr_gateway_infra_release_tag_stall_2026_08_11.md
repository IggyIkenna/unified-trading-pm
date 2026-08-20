---
doc_type: issue
title: >-
  ibkr-gateway-infra release-tag-stall — root-caused past the "false alarm" verdict: semver-agent's source_dir was
  misconfigured (never existed), fixed; reconciler's content-check heuristic remains a latent recurrence risk
summary: >-
  A `/ci-reconcile` bundle re-investigated the recurring `reconcile-release-tags` STALL alert for ibkr-gateway-infra
  (fired 00:08Z, 06:15Z — 6+ hours, never cleared) after
  `plans/active/issues/ci_reconcile_overnight_batch_2026_08_11.md` item 9 had already called it a "VERIFIED FALSE ALARM"
  (semver-agent's own log shows "No feat:/fix:/breaking commits... skipping version bump", corroborated by `git diff
  --stat v0.5.0..main -- ibkr_gateway_infra/` being empty). That verdict's OUTCOME was correct for this specific
  27-commit window but its METHODOLOGY was accidentally checking the WRONG directory: `ibkr_gateway_infra/` has never
  existed in this repo — the real published package is `ibkr-gateway-client` (`pyproject.toml` `[project].name`), source
  dir `ibkr_gateway_client/` (matches `workspace-manifest.json`'s `breaking_scan_dir` for this repo, which was already
  correct). `.github/workflows/semver-agent.yml`'s `source_dir: "ibkr_gateway_infra"` input was introduced 2026-08-07 by
  the fleet thin-caller-stub migration (`make_stub.py`, invoked with a repo-name-derived guess instead of the actual
  package dir) and has been silently wrong for 4 days — meaning semver-agent's diff scope was PERMANENTLY EMPTY
  regardless of what changed in the real source, so any future feat:/fix: to `ibkr_gateway_client/` would never have
  triggered a version bump. Fixed: `source_dir` corrected to `"ibkr_gateway_client"`. Confirmed no actual harm THIS
  window (0 commits touched `ibkr_gateway_client/` since v0.5.0), but the bug was live and would have caused a genuine
  silent-stall (the exact failure class `reconcile_release_tags.py` exists to catch) on the next real change. A second,
  separate, NOT-fixed-this-pass finding: `reconcile_release_tags.py`'s own `_source_touched()` content-check (which is
  supposed to distinguish a real stall from "commits accumulated, nothing releasable changed") uses a fixed repo-wide
  `_NON_FUNCTIONAL_PATH_RE` allowlist (`.github/`, `docs/`, lockfiles, etc.) rather than being source_dir-aware per repo
  — for ibkr-gateway-infra specifically, `cloudbuild.yaml` and `scripts/setup.sh` (both outside `ibkr_gateway_client/`,
  both genuinely non-package infra) are NOT in that allowlist, so the reconciler will keep classifying this repo as
  "touched" (and therefore alarm-eligible) on any future infra-only commit even though semver-agent (now correctly
  scoped) would never bump on the same diff — a residual STALL/no-bump split of the exact shape the script's own
  docstring already warns against ("must not silently diverge... or exactly the false-positive-STALL / silent-non-bump
  split... recurs in a new shape"). Filed as a follow-up todo, not fixed in this pass (shared script, needs a
  per-repo-source_dir design decision, and another live `/ci-reconcile` session had this exact repo's clone
  mid-merge-conflict at investigation time).
status: open
nature: issue
scope: [engineer, admin]
asset_group: [cross-cutting]
stage: [meta]
repos: [ibkr-gateway-infra, unified-trading-pm]
tags: [ci-reconcile, semver-agent, release-tags, source-dir, alert-accuracy]
related: [/plans/active/issues/ci_reconcile_overnight_batch_2026_08_11.md, /codex/08-workflows/ci-cd-flow.md]
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/issues/ci_reconcile_overnight_batch_2026_08_11.md,
    unified-trading-pm/scripts/cicd/reconcile_release_tags.py,
    ibkr-gateway-infra/.github/workflows/semver-agent.yml,
  ]
created: 2026-08-11
author: claude-agent
last_updated: 2026-08-20
parent_epic: ci_master
priority: P2
source: ci-reconcile skill, Slack #ci-failures 2026-08-10T21:44Z-2026-08-11T06:16Z (reconcile-release-tags STALL, recurred 00:08Z + 06:15Z)
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
drift_direction: advance-code
depends_on: []
---

# ibkr-gateway-infra release-tag stall — root cause past the "false alarm" verdict

## What was checked

- `gh api repos/IggyIkenna/ibkr-gateway-infra/actions/workflows` — `Semver Agent` is present and enabled.
- `gh run list --workflow=semver-agent.yml` — firing correctly on every `push:[main]`, latest runs `success`.
- `ls -d */` in the repo root — only `ibkr_gateway_client/` exists as a Python source dir. No `ibkr_gateway_infra/`
  directory has ever existed (`find . -iname '*ibkr_gateway_infra*'` → 0 hits).
- `pyproject.toml`: `name = "ibkr-gateway-client"`, dynamic (hatch-vcs) versioning.
- `git log --follow -p -- .github/workflows/semver-agent.yml`: `source_dir: "ibkr_gateway_infra"` was introduced at
  `80eb4f8` (2026-08-07T20:37:29+01:00), part of the "ci: fleet workflows -> thin caller stubs against
  unified-trading-ci" migration. Before that commit the file had no `source_dir` field at all (different, older workflow
  shape).
- `git diff --stat v0.5.0..origin/main -- ibkr_gateway_client/` (the REAL source dir) — empty, same result as the
  wrong-dir check. **No actual releasable work was lost this window** — the 27 unreleased commits are exclusively
  `.github/workflows/*.yml`, `.gitleaks.toml`, `cloudbuild.yaml`, `docs/ARCHITECTURE.md`, `pyproject.toml`,
  `scripts/setup.sh`, `uv.lock` (confirmed via `gh api .../compare/v0.5.0...main --jq '[.files[]?.filename]'`).

## Fix shipped

`ibkr-gateway-infra@24b03af0e0` (`fix(ci): correct semver-agent source_dir to actual package dir ibkr_gateway_client`) —
landed on `live-defi-rollout` via `quickmerge.sh --agent --files '.github/workflows/semver-agent.yml'`,
`quality-gates.sh --no-fix` green before shipping, post-push ancestry verified. Drains to `main` via
`ldr-to-main-promote-fleet.yml` (`*/15`); semver-agent will correctly scope future diffs to `ibkr_gateway_client/` on
the next push to `main` after promotion.

## Why the alert kept recurring 6+ hours (00:08Z, 06:15Z)

`reconcile_release_tags.py` runs every ~30min and is STILL correctly reporting a stall right now (and will keep doing so
until either a real change lands in `ibkr_gateway_client/` or `_STALL_DAYS` logic changes) — this is expected, not a bug
in the alert's firing cadence itself. The recurrence is not a dedup/cooldown bug; genuinely nothing has changed about
the underlying condition (27 commits, all non-package, tag unchanged) between 00:08Z and 06:15Z.

## Follow-up (not fixed this pass)

- [ ] [CODE] P2. **Make `reconcile_release_tags.py`'s `_source_touched()` per-repo-source_dir-aware** — **BLOCKED on the
      OPERATOR audit todo below landing first (2026-08-15 diagnosis, slot-20·infra); do not implement the naive
      version.** Concretely: for ibkr-gateway-infra, `cloudbuild.yaml` and `scripts/setup.sh` are outside the real
      source dir (`ibkr_gateway_client/`) but are NOT matched by `_NON_FUNCTIONAL_PATH_RE` (`.github/`, `docs/`,
      lockfiles, `pyproject.toml`, etc.), so the reconciler will keep classifying any future infra-only commit to this
      repo as "touched" (stall- alarm-eligible) even though semver-agent (now correctly scoped to
      `ibkr_gateway_client/`) would never bump on the same diff — the exact STALL/no-bump divergence the script's own
      docstring warns against. Fix needs a source of per-repo `source_dir` inside the reconciler (candidates:
      `workspace-manifest.json`'s existing `breaking_scan_dir` field, already correct for ibkr-gateway-infra; or fetch
      each repo's own `semver-agent.yml` caller stub via the GH contents API the same way `_main_pyproject` already
      does) — a real design choice, not a one-line change, so left for a dedicated pass. **2026-08-15 finding: the
      obvious candidate source (`workspace-manifest.json`'s `breaking_scan_dir`) is CONFIRMED INCOMPLETE for at least
      one repo today — e2e-testing's `breaking_scan_dir: "tests"` covers only 43 of its `.py` files; `scripts/` holds
      144 `.py` files including recent `fix(...)`-labeled commits (`f27cf30`, `bb2e231`, `601f8be` etc.), and its
      `.github/workflows/semver-agent.yml` `source_dir: "e2e_testing"` is separately wrong too (no such dir exists) —
      i.e. this is the SAME repo `detect_breaking_change.py`'s own docstring already cites as the reason full source-dir
      scoping was reverted 2026-08-09 (a real `scripts/*.py` change going invisible to a scoped check is a FALSE
      NEGATIVE — a stall that should have cleared stays silently masked, and per `_source_touched`'s own docstring the
      design bias must be "fail toward alerting, never toward silently clearing a real stall"). Scoping
      `reconcile_release_tags.py`'s check to `breaking_scan_dir` today would silently reintroduce that exact
      already-fixed bug class for e2e-testing (and any other repo whose manifest entry is similarly incomplete —
      unaudited). Per CLAUDE.md's "AO-eligible = outcome determinable by the worker alone" rule this is not safely
      mechanical: the correct sequencing is (1) the OPERATOR audit todo below FIRST (verify/complete `breaking_scan_dir`
      — or an equivalent curated source — for every fleet repo, e2e-testing included), THEN (2) implement the scoped
      `_source_touched()` using that now-trustworthy source, and (3) apply the SAME change to
      `detect_breaking_change.py`'s own `_source_touched()` too if scoping it — per this file's own "if you change one,
      change both" invariant, since that copy is the live semver-agent bump signal
      (`unified-trading-ci/.github/workflows/semver-agent.yml` L612-626 consumes its `source_touched` field directly).
      Not attempted this pass; do not implement without the audit landing first. (repo: unified-trading-pm)
- [ ] [OPERATOR] P2. **Audit/complete `workspace-manifest.json`'s `breaking_scan_dir` (or an equivalent curated per-repo
      source-dir list) for every fleet repo carrying `semver-agent.yml`, e2e-testing included.** Confirmed incomplete
      for at least e2e-testing (`breaking_scan_dir: "tests"` misses `scripts/`'s 144 `.py` files, several with landed
      `fix(...)` commits) — the rest of the fleet is unaudited. This is the "OPERATOR audit todo" the CODE P2 todo above
      is gated on: implementing per-repo-source_dir-awareness off an incomplete source would silently reintroduce the
      exact false-negative class `detect_breaking_change.py`'s 2026-08-09 revert was fixing. Once this audit lands, also
      apply the same scoped-check change to `detect_breaking_change.py`'s own `_source_touched()` per this file's own
      "if you change one, change both" invariant. (repo: unified-trading-pm)
- [x] ✅ [SCRIPT] P3. **Fleet-wide sweep completed 2026-08-15** — compared every repo's `semver-agent.yml` `source_dir:`
      against its repo-name-derived guess (`repo-name-with-hyphens-to-underscores`) across all 24 repos carrying the
      workflow. `ibkr-gateway-infra` (`source_dir="ibkr_gateway_client"`) is the ONLY mismatch — every other repo
      matches (docs/no-package repos `unified-trading-ci`/`unified-trading-pm` have no `source_dir:` at all, not a
      mismatch). Retagged `[OPERATOR]` → `[SCRIPT]` — this was a bounded, deterministic grep, not a judgment call.

## Disposition

**Root-caused and fixed.** The "false alarm" verdict in `ci_reconcile_overnight_batch_2026_08_11.md` item 9 was
outcome-correct but methodology-incomplete — it verified the wrong directory was empty without noticing the directory
itself was wrong. The alert will keep firing (correctly, per current content) until real `ibkr_gateway_client/` work
lands; that is not a bug. The residual reconciler content-check gap is filed above as a follow-up, not blocking.

## Progress Log

- **context-scout 2026-08-14**: populated context_scope (4 entries).
- **context-scout 2026-08-17**: re-verified context_scope (4 entries), unchanged.
- **slot-20·infra 2026-08-15**: Picked up the `_source_touched()` per-repo-source_dir-aware follow-up via
  `cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md`. Diagnosed rather than blindly implemented: empirically
  confirmed `workspace-manifest.json`'s `breaking_scan_dir` (the obvious candidate source) is incomplete for e2e-testing
  (`"tests"` misses `scripts/`'s 144 `.py` files, several with landed `fix(...)` commits) — the exact same repo
  `detect_breaking_change.py`'s own docstring cites as the reason repo-wide (unscoped) `_source_touched` was chosen over
  source-dir scoping after the 2026-08-09 false-negative incident. Also confirmed live (not just docstring claim) that
  `detect_breaking_change.py`'s `_source_touched` IS the actual semver-agent bump signal —
  `unified-trading-ci/.github/workflows/semver-agent.yml:612-626` reads its `source_touched` field to default-bump PATCH
  — so scoping `reconcile_release_tags.py`'s copy without also revisiting that one risks the exact cross-script
  divergence this file's own comments warn against. Re-sequenced the todo above: gate implementation on the OPERATOR
  `breaking_scan_dir`-completeness audit landing first. Not attempted; no code changed this pass.
- **na-eligibility-audit 2026-08-17** [body-hash:1c5d01a7cddc8180]: KEEP-NA, valid -- Grep-verified 2 open checkboxes (lines 97,126), matching inventory_open_todos=2. The CODE todo (97) carries an explicit, dated (2026-08-15), in-doc redirect/gate stating it is BLOCKED on the OPERATOR todo landing first and instructing 'do not implement the naive version' -- a standing redirect matching the spirit of rule (b)/(c). The OPERATOR todo (126) is explicitly [OPERATOR]-tagged and the same 2026-08-15 diagnosis pass explicitly found the obvious mechanical candidate source (workspace-manifest.json's breaking_scan_dir) is CONFIRMED INCOMPLETE for at least one repo, i.e. this was already investigated and found to be a genuine curation/judgment task, not a mechanical grep (contrast with the sibling item at line 134, already closed, which WAS a mechanical grep and was explicitly retagged SCRIPT for that reason -- showing this doc's author already applies that exact distinction carefully).
- **context-scout 2026-08-20**: refreshed context_scope (4 entries).
- **T4-execution-settlement (2026-08-20)**: re-verified live, both open todos unchanged since 2026-08-17 —
  `scripts/cicd/reconcile_release_tags.py` has had zero commits since 2026-08-17 (`git log --since=2026-08-17 --
  scripts/cicd/reconcile_release_tags.py` empty) and its `_source_touched()` still uses the flat, repo-agnostic
  `_NON_FUNCTIONAL_PATH_RE` allowlist — NOT made per-repo-source_dir-aware, so the `[CODE] P2` todo's own explicit gate
  ("BLOCKED on the OPERATOR audit todo below landing first... do not implement the naive version") is still correctly
  unmet. `workspace-manifest.json` carries `breaking_scan_dir` for only 5 repos fleet-wide (grep count), confirming the
  `[OPERATOR] P2` audit ("for every fleet repo carrying `semver-agent.yml`, e2e-testing included") remains genuinely
  incomplete — this is real, bounded operator-curation work across ~19+ still-unaudited repos, not a mechanical grep
  (the doc's own 2026-08-15 diagnosis already distinguished this from the sibling mechanical-grep todo at the line
  below, which was correctly closed `[x]` `[SCRIPT]`). Per CLAUDE.md's own instruction ("a genuinely open-ended design
  decision... tag it BLOCKED-OPERATOR-DECISION... rather than forcing it") and the doc's own explicit "do not
  implement the naive version" guard, neither todo was forced this pass — both remain correctly gated exactly as the
  2026-08-15/08-17 passes left them. No code changed, nothing shipped; this is a confirmation-only pass. Tagging both
  remaining open todos `BLOCKED-OPERATOR-DECISION` for T4 close-out purposes: the `[OPERATOR]` audit needs a human to
  curate per-repo source dirs across the fleet, and the `[CODE]` todo is structurally gated on that audit landing
  first.
