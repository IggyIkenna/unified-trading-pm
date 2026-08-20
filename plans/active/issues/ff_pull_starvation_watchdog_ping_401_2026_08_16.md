---
doc_type: issue
title: "orch_token 401 silenced BOTH the FF-pull starvation ping AND the server-side git-staleness Slack page — ROOT-CAUSED, credentials fixed fleet-wide (11 laptop slots; VM's 33 confirmed unaffected), resolve_token_for_slot() hardened (unified-trading-pm@8f59e8a32d)"
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
parent_epic: security_and_cross_cutting_master
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

## Scope clarification: laptop vs. the `planning` VM (2026-08-17)

The 11 slots checked/fixed above are all on the OPERATOR'S LAPTOP (`/Users/.../unified-trading-system-repos/.tabs/{1..11}`)
— that machine only has 11 slots, confirmed via directory listing. Separately checked the AO `planning` VM
(`i-0c9b283b31d6b5ca7`, read-only via SSM) since it runs the same cron/watchdog per `per-tab-worktrees.md`
("operator laptops + every VM") and the operator asked about slots up to 33:

- The VM has its OWN, separate slot pool: **33 numbered slot directories**,
  `/home/ubuntu/unified-trading-system-repos/.tabs/{1..33}` — a different host, different slot numbering, not
  an extension of the laptop's 1-11.
- **None of the 33 VM slots have a per-slot `.orch_token` file** (`find .tabs/ -mindepth 2 -maxdepth 2 -iname
  .orch_token` returned nothing) — so the VM never had the shadowing bug the laptop had; every VM slot
  correctly falls through to `~/.orch_token`.
- The VM's `~/.orch_token` (home-dir) is currently **valid**: `exp: 2026-08-23T20:33:48Z` (~6 days out from
  today) — shorter-lived than the laptop's freshly-copied one (`2026-09-09`), worth a re-check before it lapses,
  but not an active problem now.
- Found one orphaned `.tabs/.orch_token` (sitting directly in `.tabs/`, NOT inside a numbered subdirectory,
  mtime May 20 — same stale batch) — this path doesn't match `resolve_token_for_slot()`'s lookup order at all
  (per-slot means `.tabs/<N>/.orch_token`, not `.tabs/.orch_token`), so it's dead/unconsulted, not a live bug.
  Left untouched (not verified as safe to delete this session).
- **Conclusion: the VM's 33 slots do not need the laptop's fix — they were never affected.**

## Correction: this also silenced the SERVER-SIDE git-staleness Slack page, not just the starvation ping (2026-08-17)

Operator asked whether this pages Slack (for either operator) and whether a proactive check across slots is
cheap enough to add. Both already exist — but were both silently defeated by this same bug:

- **A real Slack page already exists**: `notify_git_staleness_red` / `notify_git_staleness_resolved`
  (`agent-orchestrator-alerts` channel, PAGE severity, 30-min-red threshold, 4h re-remind, clean close) — this
  is orchestrator-server-side, driven by the git-status snapshots `post_snapshot()` uploads every tick, and is
  entirely separate from the client-side starvation ping investigated above.
- **It never fired for the affected slots because `post_snapshot()` was ALSO 401-ing on the same stale token**
  — confirmed in `/tmp/slot-git-status-report.501.log`: `[fail] slot 5 — HTTP 401; body: {"detail":"invalid or
  expired token"}` starting **19:43:50Z**, earlier than the starvation-specific pings (20:13Z), because
  snapshots upload every tick regardless of dirty state. The server had zero live data for the 8 affected
  slots during the whole stale-token window — it structurally could not have paged on data it never received.
- **A proactive near-expiry warning ALSO already exists** (`check_token_expiry_for_slot`, enabled by default,
  warns 3 days before a token's `exp`) — built specifically after a prior, near-identical incident
  (`git_status_reporter_stale_public_url_token_expiry_2026_07_24.md`). It delivers its warning via the SAME
  `post_starve_ping` mechanism authenticated with the SAME (possibly-already-expired) token — so once a token
  is fully expired rather than merely near-expiry, this warning's own delivery 401s too. Confirmed on the
  laptop: `.tabs/.token-expiry-state/` exists but is empty (mtime `Aug 10` — this feature was deployed ~2.5
  months AFTER the token's `2026-05-27` expiry, so it never got the chance to warn in time, and has been
  silently re-failing its own warning every 5 minutes since).
- **No new cron/check needed** — decoding a JWT's `exp` claim is a local base64 operation, zero network calls,
  zero rate-limit exposure; the existing 3-day warning is already cheap and already runs every tick. The real
  gap was `resolve_token_for_slot()` trusting the first readable file regardless of validity — see the FIXED
  code todo below.

## Todos

- [x] ✅ [OPS] P1. **FIXED 2026-08-16 (interactive session, slot-5)** — slot 5's stale per-slot `.orch_token`
      replaced with the valid `~/.orch_token`; verified via a live `200` response.
- [x] ✅ [OPERATOR] P2. **FIXED 2026-08-17 (interactive session) — superseded the original ask.** Checked all
      11 laptop slots per operator request, not just 3/4: found the identical expired token on 7 more slots (1,
      2, 3, 4, 6, 7, 8), fixed all the same way as slot 5, confirmed slots 9-11 already correct. Separately
      checked the `planning` VM's 33 slots (operator asked about slots up to 33) — confirmed unaffected, see
      "Scope clarification" above. See "Root cause" above for the laptop mechanism.
- [x] ✅ [BACKEND] P3. **FIXED 2026-08-17 (interactive session) — `unified-trading-pm@8f59e8a32d`, quickmerge,
      QG-green, landed on live-defi-rollout.** Hardened `resolve_token_for_slot()`
      (`scripts/dev/slot-git-status-report.sh`) with a new `_token_is_expired()` helper (reuses
      `decode_jwt_exp()`, "can't decode = can't tell = don't skip" contract preserved) — a positively-confirmed-
      expired candidate is now skipped in favor of the next fallback instead of being returned blindly, with a
      `[token-expired-skip]` log line (correctly routed to stderr, not stdout, since the function's stdout is
      its return channel via command substitution — caught and fixed via a 4-scenario isolated unit test before
      shipping: expired-per-slot-falls-through, no-per-slot-unaffected, valid-per-slot-used-directly, and a
      JWT-shape integrity check on the fallthrough result). This is the generalizable fix — a stale per-slot
      file can no longer silently shadow a healthy fallback for the life of that file.
- [ ] [OPERATOR] P3. Re-check the `planning` VM's `~/.orch_token` before `2026-08-23T20:33:48Z` (~6 days from
      filing) — it's currently valid but shorter-lived than the laptop's; confirm whatever's supposed to refresh
      it actually fires, or refresh it manually if not.
- [ ] [BACKEND] P3. Find or create whatever's supposed to keep `.orch_token` files fresh across slots (a
      rotation cron, a re-mint-on-expiry hook) — a 3-month-stale credential with no apparent alarm suggests
      nothing is currently minding token freshness at all.
- [ ] [BACKEND] P3. `check_token_expiry_for_slot`'s own warning delivery is still vulnerable to the same class
      of failure (it authenticates via the same token it's warning about) — once the hardening above is live
      fleet-wide, re-evaluate whether this is still a real gap (a near-expiry warning now naturally resolves
      via a healthy fallback token before full expiry) or already closed as a side effect.

## Progress Log

- **2026-08-17 (interactive session, cont. — code fix)**: operator asked whether this alerts Slack and whether
  a proactive check is cheap enough to add fleet-wide. Found BOTH already exist (server-side
  `notify_git_staleness_red` Slack page; client-side `check_token_expiry_for_slot` 3-day warning) and were both
  silently defeated by the same stale-token bug (confirmed `post_snapshot()` was also 401-ing since 19:43Z, so
  the server had no data to page on). Implemented + unit-tested (4 scenarios, isolated harness, caught a real
  stdout/stderr bug in my own first draft before shipping) the generalizable fix: `resolve_token_for_slot()` now
  skips a positively-confirmed-expired candidate and falls through, instead of trusting the first readable
  file. Shipped via quickmerge, QG-green, `unified-trading-pm@8f59e8a32d` on live-defi-rollout.
- **2026-08-17 (interactive session, cont.)**: operator asked whether slots 9-33 were checked and whether this
  was laptop or AO scope. Confirmed the laptop has exactly 11 slots (nothing higher). Checked the AO `planning`
  VM read-only via SSM — it has its own separate 33-slot pool, none of which carry a per-slot `.orch_token`
  (so none were shadowing their home-dir fallback); VM's `~/.orch_token` is valid until `2026-08-23`. VM
  confirmed unaffected by this bug — see "Scope clarification" section above.
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
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
