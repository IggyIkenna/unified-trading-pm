---
doc_type: issue
title: >-
  quality-gates-v2's metadata-only fast-path didn't cover the bot's digest-only refresh commit — every UTL base-image
  republish ran full QG on all ~24 fleet repos simultaneously for a single-line Dockerfile bump
summary: >-
  Surfaced while investigating a fleet-wide self-hosted-runner capacity question (operator: "why 24 distinct repos — is
  that because we run full QG on every UTL/UAC/PM change to check compatibility?"). Traced the actual driver:
  `update-dependency-version.yml`'s digest-only path (non-breaking bump, no dep-pin needed, only the Dockerfile's `ARG
  BASE_IMAGE_DIGEST` changed) commits with the exact message `chore(deps): refresh base-image digest pin (ARG
  BASE_IMAGE_DIGEST)` to EVERY downstream repo's `live-defi-rollout`, dispatched near-simultaneously fleet-wide
  (confirmed: 4 repos dispatched within 4 seconds of each other). `python-quality-gates-v2.yml`'s existing
  `metadata_only` fast-path (built for `chore(release): bump version to X` and `chore(deps): pin X to Y`) only
  allow-lists changed files `{pyproject.toml, uv.lock}` — a Dockerfile-only diff always fell through `EXTRA` non-empty,
  forcing the FULL gate (ruff, basedpyright, the whole pytest matrix) for a commit that cannot have changed any
  Python/TS behaviour. On agent-orchestrator, 3 of the last 10 LDR commits were this exact bot commit — and it's the
  same commit shape that caused PR #783's Dockerfile merge conflict (a separate, already-fixed incident this session,
  `sit_gate_fleet_green_auto_retrigger_stuck_2026_07_27.md`).
status: resolved
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ci-cd, quality-gates-v2, metadata-only-fastpath, capacity, update-dependency-version]
related:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /plans/archive/2026_08/issues/sit_gate_fleet_green_auto_retrigger_stuck_2026_07_27.md,
    /plans/archive/issues/ldr_to_main_promote_churn_fix_verification_2026_07_27.md,
    /plans/archive/2026_08/ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md,
  ]
created: 2026-08-05
author: unknown
priority: P1
parent_epic: infrastructure_master
source:
  [
    "Operator question during a live fleet-CI-capacity investigation, 2026-08-05 — 'do they all need to run
    sequentially, or be dropped for latest... why run CI for all 5 if the 5th has all the previous 4 anyway'",
  ]
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by: 2026-08-05, same session — fix shipped
---

# quality-gates-v2 metadata-only fast-path missing the digest-refresh commit shape

## What I found

1. `update-dependency-version.yml`'s "Commit" step produces three distinct commit shapes on a non-breaking bump:
   - `chore(deps): pin <dep> to <version>` — pyproject.toml + uv.lock only (already fast-pathed).
   - `chore(deps): pin <dep> to <version> + base-image digest refresh` — pyproject.toml + uv.lock + Dockerfile
     (previously NOT fast-pathed — the `EXTRA` check found `Dockerfile` outside the allowed set).
   - `chore(deps): refresh base-image digest pin (ARG BASE_IMAGE_DIGEST)` — Dockerfile ONLY, when the dep bump itself
     was skipped (constraint already satisfied / capped) but the shared UTL base image republished (previously NOT
     fast-pathed at all — no case arm matched this message, so `META` stayed `false` unconditionally).
2. `python-quality-gates-v2.yml`'s `vcheck` step (both the per-slice copy and the push/main-record mirror copy) only
   recognized `chore(release): bump version to `/`chore(deps): pin ` prefixes, allow-listing changed files to
   `{pyproject.toml, uv.lock}` — a Dockerfile-only or Dockerfile-plus diff always fell through to the full gate.
3. Fleet-wide impact, quantified: `unified-trading-library` republishes roughly every 2-7 hours (5 dispatch events over
   the prior ~30h at time of writing). Each republish fans out `repository_dispatch` to all ~24 downstream repos
   essentially simultaneously (`instruments-service`, `execution-service`, `strategy-service`, `ml-service` all
   dispatched within 4 seconds of each other in one observed burst). Every one of those repos then ran a FULL
   quality-gates-v2 (multi-slice: tests + checks matrix) for a commit whose only functional content is a 64-hex-char
   digest string — real compute burned on the already-oversubscribed shared 16-vCPU CI runner box
   (`fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`,
   `ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`) for a check that could not possibly catch anything.
4. This is also the exact commit shape (agent-orchestrator commits `7446a16`/`a0f36c2`, message
   `chore(deps): refresh base-image digest pin (ARG BASE_IMAGE_DIGEST)`) whose independently-bumped Dockerfile digest
   caused PR #783's merge conflict — a separate incident resolved earlier this session
   (`sit_gate_fleet_green_auto_retrigger_stuck_2026_07_27.md` 2026-08-05 addendum). Not the same bug, but the same root
   commit shape surfacing cost in two different ways (wasted CI compute here; a spurious merge conflict there).

## Fix shipped

`unified-trading-pm/.github/workflows/python-quality-gates-v2.yml`, both `vcheck` copies (per-slice + push/main mirror —
comment `MUST stay logic-identical`): the allowed changed-file set is now computed PER matched message shape instead of
one fixed set for every `metadata_only` case:

- `chore(release): bump version to `\* → unchanged, `{pyproject.toml, uv.lock}` only.
- `chore(deps): pin `\* → widened to `{pyproject.toml, uv.lock, Dockerfile, Dockerfile.*}` (covers the combined
  pin+digest-refresh shape).
- `chore(deps): refresh base-image digest pin (ARG BASE_IMAGE_DIGEST)` (exact match, new case) →
  `{Dockerfile, Dockerfile.*}` only.

Trust model is unchanged from the existing cases: message + changed-file-set only, no commit-author check — the same
level of trust `pyproject.toml`/`uv.lock` metadata-only commits already got. A single-line `ARG BASE_IMAGE_DIGEST` bump
cannot change Python/TS behaviour, so skipping the Python test/lint/typecheck slices for it loses no real coverage; the
FROM-digest change itself still flows through the normal image-build/deploy path untouched by this fast-path (this only
skips `quality-gates-v2`'s Python-side slices, not image building or deployment).

**Verified before shipping** (8 cases, isolated bash harness mirroring the exact case/EXTRA logic): the 3 pre-existing
shapes (version bump, dep pin, a non-matching normal commit) are unchanged; the new digest-only and combined pin+digest
shapes correctly fast-path; two adversarial cases (a matching message with an EXTRA unexpected file change, e.g. a `.py`
file riding alongside) correctly still force the full gate — the allow-list check is not weakened for anything outside
the three known-safe shapes.

## Todos

- [x] ✅ [SCRIPT] P1. Extend `python-quality-gates-v2.yml`'s metadata-only detection (both `vcheck` copies) to fast-path
      the `chore(deps): refresh base-image digest pin (ARG BASE_IMAGE_DIGEST)` commit shape and the combined
      pin+digest-refresh shape, each with a message-specific changed-file allow-list. Shipped this session —
      unified-trading-pm@(see commit landing this doc).
- [ ] [VERIFY] P2. After the next `unified-trading-library` base-image republish fans out fleet-wide, confirm a sampled
      downstream repo's `chore(deps): refresh base-image digest pin` commit actually reports `metadata_only=true` and
      the qg-slices report GREEN in seconds (not the full multi-minute run) — a genuine live confirmation beyond the
      isolated bash-harness test above.

## Codex SSOTs

- `/codex/08-workflows/ci-cd-flow.md` — gate set / quality-gates-v2 contract.
