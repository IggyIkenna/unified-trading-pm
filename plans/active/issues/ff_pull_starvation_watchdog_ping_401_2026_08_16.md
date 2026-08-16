---
doc_type: issue
title: "FF-pull starvation watchdog operator-ping delivery was HTTP 401 on slot 5 — ROOT-CAUSED + FIXED (stale per-slot .orch_token); slots 3/4 likely need the same fix"
summary: >-
  `slot-git-status-report.sh`'s FF-pull starvation watchdog (`check_starvation_for_slot`,
  `ff-starvation-detect.sh`) was correctly detecting real starvation episodes (a dirty local edit colliding with
  incoming origin content, blocking `slot-cron-ff-pull.sh`'s auto-heal) — confirmed live for `.tabs/5/unified-
  trading-pm` (starved 20:13:27Z-21:10:21Z, 42 commits behind, well past both the 25-commit and 3-tick paging
  thresholds) — but every ping attempt to `${ORCH_URL}/api/slots/<N>/message` was returning HTTP 401, logged as
  `[starve-ping-fail]`. **ROOT-CAUSED for slot 5**: `resolve_token_for_slot()` checks the PER-SLOT
  `.tabs/<N>/.orch_token` file before the home-dir `~/.orch_token` fallback — slot 5's per-slot token had `exp:
  2026-05-27` (expired ~3 months ago, JWT `exp` claim decoded directly), silently shadowing the still-valid
  `~/.orch_token` (`exp: 2026-09-09`) that would otherwise have been used. **FIXED for slot 5** (2026-08-16):
  replaced the stale per-slot token with the valid home-dir one; verified live with a direct
  `POST /api/slots/5/message` call — now returns HTTP 200 (previously 401). Slots 3 and 4 showed the identical
  401 pattern in the shared log (`/tmp/slot-git-status-report.501.log`, since at least 19:28Z) and likely have
  the same stale-per-slot-token root cause, but their `.tabs/3/.orch_token` / `.tabs/4/.orch_token` files were
  NOT touched this session — those are different slots' checkouts, not mine to reach into without the operator
  present/confirming (per the multi-agent slot-boundary rule).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [ff-pull, starvation, watchdog, alerting, auth, 401, cron, per-tab-worktrees]
related:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-16"
author: claude-code (interactive session, slot-5)
priority: P1
parent_epic: infrastructure_master
source: >-
  Operator asked "isnt here a rule or cron for this... thought we fixed this" after I manually `git pull --ff-only`ed
  a starved PM repo. Investigation of /tmp/slot-cron-ff-pull.result.json (repo_dirty_ticks: 6 for this slot's PM
  clone) and /tmp/slot-git-status-report.501.log found the watchdog fired repeatedly and failed to deliver every time.
assigned_vm: planning
execution_scope: orchestrator-agent
effort: max
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.5
assigned_role: backend_engineer
drift_direction: none
depends_on: []
resolved_by:
locked_by:
context_scope:
  [
    scripts/dev/slot-git-status-report.sh,
    scripts/dev/ff-starvation-detect.sh,
    scripts/dev/slot-cron-ff-pull.sh,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /tmp/slot-git-status-report.501.log,
  ]
---

# FF-pull starvation watchdog detects correctly but ping delivery is 401 fleet-wide

## What I found

- `slot-cron-ff-pull.sh` (cron, every 5 min) reported `.tabs/5/unified-trading-pm` as `repo_dirty_ticks: 6` in
  `/tmp/slot-cron-ff-pull.result.json` — 6 consecutive ticks unable to fast-forward, despite the repo being only
  42 commits behind origin (confirmed via `git rev-list --count HEAD..origin/live-defi-rollout`), and despite the
  working-tree content of the dirty files being byte-identical to origin (confirmed via `git diff origin/...`).
- The starvation detector (`ff-starvation-detect.sh`, invoked by `slot-git-status-report.sh`'s
  `check_starvation_for_slot`) correctly identified this as a paging-worthy episode: 42 ≥ `FF_STARVE_COMMIT_THRESHOLD`
  (25, default) and 6 ticks ≥ `FF_DIRTY_STREAK_THRESHOLD` (3, `slot-cron-ff-pull.sh`).
- Every ping attempt (`post_starve_ping` → `POST ${ORCH_URL}/api/slots/${slot_id}/message`, bearer-token
  authenticated) returned HTTP 401, logged as `[starve-ping-fail] slot 5/unified-trading-pm — HTTP 401` — first
  observed 20:13:27Z, repeating every ~5 min through at least 21:10:21Z with zero successful `[starve-ping]`
  (200) entries anywhere in the visible log window.
- **Not isolated to this slot**: the same log shows `[starve-ping-fail] slot 3/unified-trading-pm — HTTP 401` and
  `[starve-ping-fail] slot 4/unified-trading-pm — HTTP 401` starting at least 19:28Z, and slot 3 also logged one
  `HTTP 502` (21:09:40Z) — consistent with a shared credential/endpoint problem, not a per-slot config issue.
- I manually resolved MY slot's starvation with `git pull --ff-only origin live-defi-rollout` (succeeded cleanly,
  `Applied autostash`, `ahead=0`/`behind=0` after) — this is a workaround for one instance, not a fix for the
  delivery pipeline.

## Why it matters

The whole point of the starvation watchdog (per `per-tab-worktrees.md`'s documented design) is that a stuck slot
self-reports instead of silently drifting hundreds of commits behind until someone notices by accident (the
exact `2026-06-10`/`2026-07-14` incidents that motivated building this). Right now the DETECTION half works but
the DELIVERY half is silently swallowing every alert — functionally equivalent to having no watchdog at all,
except it looks like one exists (misleading). This is exactly the kind of gap that lets a slot drift for hours
before an operator notices, same failure class as the incidents the mechanism was built to prevent.

## Root cause (found + fixed, slot 5 only)

`resolve_token_for_slot()` (`scripts/dev/slot-git-status-report.sh:444-465`) resolution order is: explicit
`TOKEN_FILE` → per-slot `${TABS_DIR}/<N>/.orch_token` → `~/.orch_token` → `/tmp/orch_token` → (loopback-only
anonymous). Slot 5's per-slot `.orch_token` (dated `Aug 16` mtime but actually minted long before — decoded JWT
`exp` claim: `2026-05-27T15:40:57Z`) was silently shadowing the healthy `~/.orch_token` (`exp:
2026-09-09T08:09:17Z`) sitting one fallback level down — the resolver never got far enough to try it. This is a
pure stale-local-credential bug, nothing wrong on the orchestrator/server side, and nothing wrong with the
watchdog's detection logic.

**Fix applied (slot 5, 2026-08-16)**: backed up the expired per-slot token to
`.tabs/5/.orch_token.expired-2026-05-27.bak`, copied the valid `~/.orch_token` content into
`.tabs/5/.orch_token` (mode 600 preserved). Verified live: `POST /api/slots/5/message` with the new token now
returns `200` (was `401`).

## What I did NOT do

- Did NOT touch slots 3 or 4's `.orch_token` files, even though the identical 401 pattern in the shared log
  strongly suggests the same stale-per-slot-token cause — those are different slots' checkouts (potentially
  live/in-use by another session right now), out of bounds for me to reach into without the operator present.
- Did NOT change `resolve_token_for_slot()`'s resolution order or add expiry-awareness (e.g. skip an expired
  per-slot token and fall through to the next candidate) — that's a real hardening opportunity (see todo below)
  but is a shared-script change affecting the whole fleet, not a same-turn fix for my own stale file.
- Did NOT investigate why slot 5's per-slot token was ~3 months stale in the first place (no rotation cron found
  for `.orch_token` files specifically) — worth checking if one is supposed to exist.

## Todos

- [x] ✅ [OPS] P1. **FIXED 2026-08-16 (interactive session, slot-5)** — stale per-slot `.orch_token` replaced with the
      valid `~/.orch_token`; verified via a live `200` response. See "Root cause" above.
- [ ] [OPERATOR] P2. Check `.tabs/3/.orch_token` and `.tabs/4/.orch_token` (and any other slot) for the same
      stale-per-slot-token pattern (decode the JWT `exp` claim, compare against `~/.orch_token`'s) and refresh
      any that are expired, mirroring the slot-5 fix above.
- [ ] [BACKEND] P3. Harden `resolve_token_for_slot()` to skip an expired candidate and fall through to the next
      one (it already has `decode_jwt_exp()` available — currently only used elsewhere for a different check;
      wire it into the resolution order itself) instead of using the first FILE it finds regardless of validity
      — this is the actual generalizable fix that prevents this class of silent shadowing recurring per-slot.
- [ ] [BACKEND] P3. Find or create whatever's supposed to keep `.orch_token` files fresh across slots (a
      rotation cron, a re-mint-on-expiry hook) — a 3-month-stale credential with no apparent alarm suggests
      nothing is currently minding token freshness at all.
- [ ] [DOC] P3. Consider whether the watchdog itself should escalate differently (e.g. fall back to a Slack
      webhook, or write a local marker file) when the orchestrator ping fails repeatedly, so a future credential
      lapse doesn't silently degrade to zero visibility again the same way this one did.

## Progress Log

- **2026-08-16 (interactive session, slot-5)**: filed after the operator asked why a starved PM repo wasn't
  auto-healed given the documented cron/watchdog — traced to detection working correctly but delivery 401'ing.
  Root-caused to a stale per-slot `.orch_token` (expired 2026-05-27) shadowing a valid `~/.orch_token`
  (2026-09-09) in the resolver's fallback order. Fixed for slot 5, verified live (401→200). Slots 3/4 likely
  affected too but not touched — flagged as an operator todo since those checkouts aren't mine to reach into.
