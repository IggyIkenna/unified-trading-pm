---
doc_type: issue
title: "FF-pull starvation watchdog operator-ping delivery was HTTP 401 fleet-wide — ROOT-CAUSED + FIXED across all 11 slots (stale per-slot .orch_token, all minted same batch)"
summary: >-
  `slot-git-status-report.sh`'s FF-pull starvation watchdog (`check_starvation_for_slot`,
  `ff-starvation-detect.sh`) was correctly detecting real starvation episodes (a dirty local edit colliding with
  incoming origin content, blocking `slot-cron-ff-pull.sh`'s auto-heal) — confirmed live for `.tabs/5/unified-
  trading-pm` (starved 20:13:27Z-21:10:21Z, 42 commits behind, well past both the 25-commit and 3-tick paging
  thresholds) — but every ping attempt to `${ORCH_URL}/api/slots/<N>/message` was returning HTTP 401, logged as
  `[starve-ping-fail]`. **ROOT-CAUSED**: `resolve_token_for_slot()` checks the PER-SLOT `.tabs/<N>/.orch_token`
  file before the home-dir `~/.orch_token` fallback. Operator asked to check all 11 slots (2026-08-17): 8 of 11
  (`.tabs/{1,2,3,4,5,6,7,8}`) had a per-slot `.orch_token` with the IDENTICAL expired `exp: 2026-05-27T15:40:57Z`
  claim (a single provisioning batch, not independent staleness) silently shadowing the healthy
  `~/.orch_token` (`exp: 2026-09-09T08:09:17Z`). Slots 9, 10, 11 have NO per-slot token file at all and were
  already correctly falling through to the valid home-dir one — no fix needed there. **FIXED for all 8 affected
  slots** (2026-08-16/17): each stale token backed up to `.orch_token.expired-2026-05-27.bak` alongside it and
  replaced with the valid home-dir token; verified live via direct `POST /api/slots/<N>/message` calls for
  slots 1, 3, 5, 7 — all now return HTTP 200 (previously 401). Slots 2, 4, 6, 8 got the identical file swap but
  were not individually re-verified via a live call (same source/target content as the verified ones, so treated
  as equivalent — flagged in Progress Log, not blindly assumed silently).
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

## Root cause (found + fixed, all 8 affected slots)

`resolve_token_for_slot()` (`scripts/dev/slot-git-status-report.sh:444-465`) resolution order is: explicit
`TOKEN_FILE` → per-slot `${TABS_DIR}/<N>/.orch_token` → `~/.orch_token` → `/tmp/orch_token` → (loopback-only
anonymous). Every affected slot's per-slot `.orch_token` decoded to the SAME JWT `exp` claim
(`2026-05-27T15:40:57Z`) — a single provisioning batch that was never refreshed, not 8 independent staleness
events — silently shadowing the healthy `~/.orch_token` (`exp: 2026-09-09T08:09:17Z`) sitting one fallback
level down. The resolver never got far enough to try the home-dir fallback for any of them. This is a pure
stale-local-credential bug, nothing wrong on the orchestrator/server side, and nothing wrong with the watchdog's
detection logic.

**Fix applied (all 8 affected slots, 2026-08-16/17)**: for each of `.tabs/{1,2,3,4,5,6,7,8}`, backed up the
expired per-slot token to `.orch_token.expired-2026-05-27.bak` alongside it, then copied the valid
`~/.orch_token` content in (mode 600 preserved). Verified live via `POST /api/slots/<N>/message` for slots 1,
3, 5, 7 (spot-check, not all 8, to avoid spamming every slot inbox with a diagnostic message) — all returned
`200` (was `401`). Slots 2, 4, 6, 8 got the identical byte-for-byte token swap but weren't individually
re-curled. Slots 9, 10, 11 had no per-slot token file and needed no change — confirmed already falling through
correctly to the valid `~/.orch_token`.

## What I did NOT do

- Did NOT change `resolve_token_for_slot()`'s resolution order or add expiry-awareness (e.g. skip an expired
  per-slot token and fall through to the next candidate) — that's a real hardening opportunity (see todo below)
  but is a shared-script change affecting the whole fleet, not a same-turn file swap.
- Did NOT investigate why 8 slots' per-slot tokens were minted in the same stale batch and never refreshed in
  ~3 months with no apparent alarm — no rotation cron found for `.orch_token` files specifically; worth
  checking if one is supposed to exist (see todo below).
- Did NOT spot-check slots 2, 4, 6, 8 with a live call after the swap — same source (`~/.orch_token`) and same
  mechanism as the 4 verified slots, but noting the gap rather than silently claiming full verification.

## Todos

- [x] ✅ [OPS] P1. **FIXED 2026-08-16 (interactive session, slot-5)** — slot 5's stale per-slot `.orch_token`
      replaced with the valid `~/.orch_token`; verified via a live `200` response.
- [x] ✅ [OPERATOR] P2. **FIXED 2026-08-17 (interactive session) — superseded the original ask.** Checked all
      11 slots per operator request, not just 3/4: found the identical expired token on 7 more slots (1, 2, 3,
      4, 6, 7, 8), fixed all the same way as slot 5, confirmed slots 9-11 already correct. See "Root cause"
      above.
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

- **2026-08-17 (interactive session)**: operator asked to check all 11 slots. Found the same expired
  (`2026-05-27`) per-slot token on 7 more slots (1, 2, 3, 4, 6, 7, 8) beyond the already-fixed slot 5 — all one
  provisioning batch, not independent staleness. Fixed all 8 the same way (backup + replace with
  `~/.orch_token`), confirmed slots 9-11 already correct (no per-slot file), live-verified 4 of the 8 (1, 3, 5,
  7) via direct `200` responses. Fleet-wide token-shadowing bug now resolved; the generalizable code fix
  (expiry-aware fallback) and the "why did nothing rotate this" question remain open below.
- **2026-08-16 (interactive session, slot-5)**: filed after the operator asked why a starved PM repo wasn't
  auto-healed given the documented cron/watchdog — traced to detection working correctly but delivery 401'ing.
  Root-caused to a stale per-slot `.orch_token` (expired 2026-05-27) shadowing a valid `~/.orch_token`
  (2026-09-09) in the resolver's fallback order. Fixed for slot 5, verified live (401→200).
- **context-scout 2026-08-17**: refreshed context_scope (4 entries — dropped a `/tmp/` log path, not a durable reference).
