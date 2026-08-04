---
doc_type: issue
title:
  "Orphaned live CVE fix: slot-5 (dead) has an unpushed aiohttp>=3.14.3 bump in unified-trading-library closing 3 real
  CVEs (2026-59881/69243/69244) — wip-preserved (zero loss) but NOT on origin/live-defi-rollout; needs a mechanical
  worker rescue"
summary: >-
  Review git-health flagged (msg #3601, 2026-08-03 ~22:02Z) that AO slot 5 died (worker_alive=false, tmux_alive=false,
  last_ping 21:52:33Z) holding one unpushed commit in unified-trading-library: d42fe0191bbe "fix(deps): bump aiohttp to
  >=3.14.3 to close 3 new CVEs". The three CVEs are real and currently UNPATCHED on origin/live-defi-rollout
  (CVE-2026-59881 RSV1 decompress bomb; CVE-2026-69243 WebSocket-upgrade request smuggling; CVE-2026-69244 OOB heap read
  in the C response parser). Zero loss risk — already safety-net-preserved at
  origin/wip-preserve/orchestrator-slot-5-d42fe019 — but main agt-1756f6 independently verified d42fe019 is NOT an
  ancestor of origin/live-defi-rollout (origin still carries the pre-fix aiohttp pin). It is a deps+lockfile-only change
  (pyproject.toml + uv.lock, no code), so a clean mechanical rescue: format-patch/reapply or pick up the wip-preserve
  ref, then ship via quickmerge. Main CANNOT do this (main never pushes code; deps go through the quickmerge dep gates)
  — hence a worker-rescue issue. NOTE the commit's own "blocking promotion PR #729" framing is stale: review confirmed
  PR #729 already MERGED at 21:17:40Z, ~19min BEFORE this fix committed locally at 21:36:06Z — so lint-codex/pip-audit
  is either advisory-only in the LDR→main gate set or something else let it through; that stale claim does not diminish
  the fix (3 real CVEs still unpatched on origin).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-library]
scope: [admin]
tags: [orphan-rescue, cve, security, deps, aiohttp, per-tab-worktrees, wip-preserve, git-health]
related: [/codex/05-infrastructure/per-tab-worktrees.md, /codex/08-workflows/ci-cd-flow.md]
created: 2026-08-03
author: unknown
parent_epic: agent_operating_framework_master
priority: P1
assigned_vm: NA
execution_scope: local-only
resolved_by:
locked_by:
source:
  "review git-health finding msg #3601 (2026-08-03 ~22:02Z); orphan-commit + not-on-LDR independently verified by main
  agt-1756f6 via git merge-base --is-ancestor"
drift_direction: advance-process
estimate_class: refactor
depends_on: []
---

# Orphaned live CVE fix on dead slot 5 — mechanical worker rescue needed

## The finding (verified)

- **Dead slot**: AO slot 5 — `worker_alive=false`, `tmux_alive=false`, `last_ping 21:52:33Z` (>120s stale at flag time →
  a genuinely DEAD slot under the per-tab-worktrees LIVENESS gate, not a live-WIP protect case).
- **Orphan commit**: `d42fe0191bbe` in `unified-trading-library` —
  `fix(deps): bump aiohttp to >=3.14.3 to close 3 new CVEs`. Deps+lockfile only (`pyproject.toml` + `uv.lock`), **no
  code**.
- **CVEs closed** (real, currently unpatched on origin/live-defi-rollout):
  - CVE-2026-59881 — RSV1 decompress bomb
  - CVE-2026-69243 — WebSocket-upgrade request smuggling
  - CVE-2026-69244 — OOB heap read in the C response parser
- **Zero loss risk**: safety-net preserved at `origin/wip-preserve/orchestrator-slot-5-d42fe019`.
- **Main-verified**: `git merge-base --is-ancestor d42fe0191bbe origin/live-defi-rollout` → **NOT** an ancestor
  (confirmed orphan); origin/live-defi-rollout still carries the pre-fix aiohttp pin.
- **Stale self-framing (corrected by review, does not affect the fix)**: the commit says it blocked promotion PR #729,
  but #729 already **MERGED 21:17:40Z**, ~19min before this fix committed locally at 21:36:06Z — so lint-codex/pip-audit
  is advisory-only in the LDR→main gate set (or something else let it through). The 3 CVEs are still real and unpatched
  regardless.

## Why main can't do it (and it's a worker task)

Main agt-1756f6 is constrained to **never push code**; the docs carve-out covers plan/issue docs only. A deps+lockfile
bump reaches LDR via **quickmerge** (which runs the dep gates) — that is a worker action, not a docs-carveout push.
Hence this durable issue so a worker picks it up cleanly.

## Todos

- [ ] [BACKEND] P1. Rescue the orphaned CVE fix onto `origin/live-defi-rollout`. Clean mechanical path (deps+lockfile
      only): (a) `cd unified-trading-library`,
      `git fetch origin 'refs/wip-preserve/*:refs/remotes/origin/wip-preserve/*'`, confirm
      `origin/wip-preserve/orchestrator-slot-5-d42fe019` resolves to `d42fe0191bbe`; (b) either
      `git cherry-pick d42fe0191bbe` (or `format-patch` + `git am`) onto a fresh LDR-tip branch, OR re-derive the
      pyproject.toml `aiohttp>=3.14.3` bump + `uv lock` if the patch conflicts; (c) run repo QG green
      (`bash scripts/quality-gates.sh`); (d) ship via
      `bash scripts/quickmerge.sh "fix(deps): bump aiohttp to >=3.14.3 (rescue orphaned slot-5 CVE fix; closes CVE-2026-59881/69243/69244)" --agent --files 'pyproject.toml uv.lock'`.
      Verify d42fe019's intent lands (origin pin ≥3.14.3, uv.lock resolves aiohttp 3.14.3+). Done-when:
      `aiohttp>=3.14.3` is an ancestor of origin/live-defi-rollout and the 3 CVEs are closed on origin. (repo:
      unified-trading-library)

## Progress Log

- **2026-08-03 ~22:05Z (main agt-1756f6)**: Filed from review git-health finding #3601. Independently verified the
  orphan (not-on-LDR via `merge-base --is-ancestor`). Zero-loss (wip-preserved), so no emergency, but it's a live
  security fix sitting unshipped — flagged P1 for the next available worker cycle over routine cleanup, per review's
  recommendation. Main did NOT push it (main never pushes code; deps go via quickmerge dep gates).
