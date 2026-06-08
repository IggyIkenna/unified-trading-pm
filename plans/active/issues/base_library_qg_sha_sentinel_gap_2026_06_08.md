---
title: "base-library.sh does not write .qg_last_passed_sha → quickmerge --agent Stage-3 fails on every library"
created: 2026-06-08
source:
  - plans/active/utl_full_quality_gates_green_2026_06_01.md
  - scripts/quality-gates-base/base-library.sh
  - scripts/quality-gates-base/base-service.sh
  - scripts/quickmerge.sh
locked_by: live-defi-rollout
priority: P2
status: active
---

## What I found

`quickmerge.sh` Stage 3 (`AGENT FAST-PATH`, ~line 1039) verifies the Pass-1 sentinel by reading
**`.qg_last_passed_sha`** and comparing it to `git rev-parse HEAD`:

```bash
_SENTINEL=".qg_last_passed_sha"
... [ "$_SENTINEL_SHA" != "$_CURRENT_SHA" ] && { echo "❌ Pass 1 quality-gates.sh not run on current HEAD (SHA mismatch)"; exit 1; }
```

But the two base scripts disagree on which sentinel they write:

- **`base-service.sh`** (line ~2697): `git rev-parse HEAD > "${PROJECT_ROOT}/.qg_last_passed_sha"` on a green run. ✅
- **`base-library.sh`** (line ~1000): writes only `.qg_content_sentinel` (a content hash) — it **never writes
  `.qg_last_passed_sha`**. ❌

Net effect: a green `bash scripts/quality-gates.sh` on a **library** repo (UTL, UAC, unified-cloud-interface, …) leaves
`.qg_last_passed_sha` stale (or absent), so `quickmerge --agent` **always** fails Stage 3 with "SHA mismatch" and
refuses to ship — even though the gate is genuinely green. Confirmed on `unified-trading-library` 2026-06-08 (sentinel
stuck at an ancient `a5d63e7b` across 3 green runs; HEAD was `167f8c18`/`9e97e01b`).

## Why it matters

Every library promotion via the sanctioned `quickmerge --agent` two-pass path is broken until a human/agent manually
writes the sentinel — exactly the toil the two-pass model was meant to remove. It silently pushes agents toward
re-running QG in quickmerge (slow) or raw pushes (banned). It is fleet-wide for all `base-library.sh` repos.

## Recommended decision

Make `base-library.sh` write `.qg_last_passed_sha` on a green run, mirroring `base-service.sh` (one line, parity with
the existing content-sentinel write). Then re-run `rollout-quality-gates-unified.py` so every library repo picks it up.
Verify the **blast radius (Rule 11)**: run a green QG + `quickmerge --agent` on ≥2 representative library repos (UTL +
one other) and confirm Stage 3 passes; check `base-codex.sh`/`base-ui.sh` for the same gap. Workaround in the interim:
`git rev-parse HEAD > .qg_last_passed_sha` after a green QG (used for UTL@9e97e01b / PR #253).
