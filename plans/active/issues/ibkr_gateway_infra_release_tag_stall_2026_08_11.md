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
created: 2026-08-11
author: claude-agent
last_updated: 2026-08-11
parent_epic: infrastructure_master
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

- [ ] [CODE] P2. **Make `reconcile_release_tags.py`'s `_source_touched()` per-repo-source_dir-aware**, mirroring
      `detect_breaking_change.py`'s scoping instead of using a flat repo-wide `_NON_FUNCTIONAL_PATH_RE` allowlist.
      Concretely: for ibkr-gateway-infra, `cloudbuild.yaml` and `scripts/setup.sh` are outside the real source dir
      (`ibkr_gateway_client/`) but are NOT matched by `_NON_FUNCTIONAL_PATH_RE` (`.github/`, `docs/`, lockfiles,
      `pyproject.toml`, etc.), so the reconciler will keep classifying any future infra-only commit to this repo as
      "touched" (stall- alarm-eligible) even though semver-agent (now correctly scoped to `ibkr_gateway_client/`) would
      never bump on the same diff — the exact STALL/no-bump divergence the script's own docstring warns against. Fix
      needs a source of per-repo `source_dir` inside the reconciler (candidates: `workspace-manifest.json`'s existing
      `breaking_scan_dir` field, already correct for ibkr-gateway-infra; or fetch each repo's own `semver-agent.yml`
      caller stub via the GH contents API the same way `_main_pyproject` already does) — a real design choice, not a
      one-line change, so left for a dedicated pass. (repo: unified-trading-pm)
- [ ] [OPERATOR] P3. **Audit whether the 2026-08-07 thin-caller-stub migration mis-derived `source_dir` for any OTHER
      repo whose package directory name doesn't match its repo-name-derived guess**
      (`repo-name-with-hyphens-to-underscores`). Spot-checked market-tick-data-service, features-service,
      execution-service, instruments-service, strategy-service during this pass — all match (repo name == package dir
      name) — but ibkr-gateway-infra is a KNOWN exception (repo `ibkr-gateway-infra`, package `ibkr-gateway-client`) and
      there may be others not yet checked. A full fleet sweep (compare each repo's `semver-agent.yml` `source_dir:`
      against its actual top-level Python package directory) was out of scope for this bundle. (repo:
      unified-trading-pm)

## Disposition

**Root-caused and fixed.** The "false alarm" verdict in `ci_reconcile_overnight_batch_2026_08_11.md` item 9 was
outcome-correct but methodology-incomplete — it verified the wrong directory was empty without noticing the directory
itself was wrong. The alert will keep firing (correctly, per current content) until real `ibkr_gateway_client/` work
lands; that is not a bug. The residual reconciler content-check gap is filed above as a follow-up, not blocking.
