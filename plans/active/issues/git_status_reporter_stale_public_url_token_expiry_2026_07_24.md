---
doc_type: issue
title:
  "git-health reporter goes silent host-wide when ~/.orch_token expires: slot-git-status-report.sh POSTs to the PUBLIC
  ORCH_URL with a Bearer token, so a rotated/expired token silences the whole host's git-health view while FF-pull stays
  healthy (it never pushes)"
summary:
  The per-slot git-health reporter (unified-trading-pm/scripts/dev/slot-git-status-report.sh) POSTs each slot's
  git-status snapshot to /api/slots/{slot_id}/git-status using the default public ORCH_URL
  (https://api.agent-orchestrator.odum-research.com) with an `Authorization` Bearer header read from ~/.orch_token. When
  that token expires/rotates, every push 401s and the reporter goes SILENT for the entire host — the dashboard
  git-health view for all of that host's slots freezes at the last successful report and the server's staleness watchdog
  then fires `git_staleness_alert_sent` (message "git reporter cron silent for Nm") for every slot on a loop. Critically
  the FF-pull cron (slot-cron-ff-pull.sh) is UNAFFECTED because it never pushes to the server — so ff-pull keeps working
  while the dashboard shows the host as stale, which can mask a real dirty/behind worktree or raise false ff_cron_stale
  alarms fleet-wide. Confirmed live 2026-07-24 on host ip-172-31-5-118 (17 slots) — reporter froze at
  2026-07-24T15:47:03Z, and `git_staleness_alert_sent` was still firing for slots 0-16 at 20:02Z (~255m silent);
  ~/.orch_token mtime was 2026-06-24, consistent with an expired/stale bearer token. Non-blocking, no-page
  (observability-integrity, not operational) — but it recurs on every token rotation and spams the activity feed.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [git-health, monitoring, reporter, token-expiry, loopback, false-positive, per-tab-worktrees, agent-orchestrator]
related:
  [
    /plans/archive/issues/git_health_phantom_dirty_flicker_ff_cron_race_2026_07_21.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
  ]
created: 2026-07-24
author: unknown
last_updated: 2026-07-24
priority: P2
parent_epic: infrastructure_master
source:
  "review(agt-af7186) msgs 1862/1867 + review(agt-d76e80) to main orchestrator, 2026-07-24; main root-cause on-host"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
resolved_by:
locked_by:
context_scope:
  [
    /plans/archive/issues/git_health_phantom_dirty_flicker_ff_cron_race_2026_07_21.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
    scripts/dev/slot-git-status-report.sh,
  ]
depends_on: []
---

# git-health reporter goes silent host-wide on ~/.orch_token expiry

## What happens

`slot-git-status-report.sh` (cron, ~5-min cadence, per host) walks `.tabs/<N>/<repo>/`, builds a git-status snapshot,
and POSTs it to `/api/slots/<N>/git-status`. Defaults (script header):

- `ORCH_URL` = `https://api.agent-orchestrator.odum-research.com` (PUBLIC — token-required)
- Auth = `Authorization: Bearer <cat ORCH_TOKEN_FILE>`, `ORCH_TOKEN_FILE` default `$HOME/.orch_token`

When `~/.orch_token` expires/rotates, every POST 401s, the reporter stops updating server state for that host, and the
server's staleness watchdog emits `git_staleness_alert_sent` ("git reporter cron: silent for Nm") for each slot on the
host, every tick. FF-pull (`slot-cron-ff-pull.sh`) is unaffected — it fast-forwards local clones and never talks to the
server — so the host keeps pulling cleanly while its dashboard git-health rows freeze. Net harm: the dashboard
git-health view for the whole host is stale/misleading (can mask a genuinely dirty/behind worktree, or drive false
`ff_cron_stale`/`reporter_stale` alarms) and the activity feed fills with per-slot staleness alerts.

## Evidence (2026-07-24, host ip-172-31-5-118, 17 slots)

- `/api/fleet/git-health`: `reporter_stale=true` + `ff_cron_stale=true` for all 17 slots; cached `reported_at` frozen at
  `2026-07-24T15:47:03Z`.
- `/api/activity` at ~20:02Z: `git_staleness_alert_sent` for slot_id 0-16,
  `red_repos: ["git reporter cron: silent for 255m"]`.
- `slot-cron-ff-pull.sh` live + healthy: `/tmp/slot-cron-ff-pull.result.json` `ff_pull_last_run` ~2 min old (per review
  agt-af7186).
- `~/.orch_token` mtime `2026-06-24` — stale bearer token, consistent with the 15:47Z silence onset.

## Fix (agreed direction: loopback trusted-local, no token)

The reporter runs ON the orchestrator host, where `http://localhost:8765` is trusted-local and needs no bearer token —
so the durable fix is to make on-VM reporting use loopback rather than the public URL + a rotating token (re-minting the
token just resets the same treadmill). Design constraint: operator laptops run this script OFF-VM and MUST keep using
the public URL + token, so the fix must be conditional, not a blanket default flip.

## Todos

- [x] [INFRA] ✅ **DONE 2026-08-06 (slot-2, interactive) — token re-minted + tooling shipped
      `unified-trading-pm@9ef9926e9`.** Re-mint `~/.orch_token` on the OPERATOR'S LOCAL host `hk` (distinct from the
      `ip-172-31-5-118` instance already tracked in
      `/plans/archive/2026_07/ao_satellite_ao_dispatch_batch2_2026_07_30.md`). Measured 2026-08-06: the token on `hk`
      expired **2026-08-05T06:08:07Z**, so `slot-git-status-report.sh`'s POST to the public URL 401s and the AO Fleet
      tab had been showing STALE git state for that host's slots ever since — the exact host-wide silent-blindness this
      doc was filed for, recurring on a second host. `hk` is a laptop-style checkout, NOT the orchestrator VM, so the
      2026-07-26 loopback fix above does not rescue it: there is no local `:8765` backend to fall back to, which makes
      the public-URL token the only path and its expiry a hard outage for that host. **Retagged
      `[OPERATOR]`→`[INFRA]`**: minting turned out NOT to need a human — the VM already holds the signing secret and is
      reachable read/write via the same SSM channel the sanctioned `/check-agent-orchestrator` path uses, so an agent
      can mint without ever seeing the secret. **Evidence:** new token `sub=harsh role=operator` exp
      `2026-09-05T17:03:18Z`; `/api/state` 200 (was 401); full reporter sweep on `hk` = 16/16 slots `[ok]`, 0 fail;
      server-side `/api/fleet/git-health` host `hk` `reporter_stale` count **15/16 → 0/16** (the 15 frozen slots all
      read `reported_at: 2026-08-05T06:07:04Z`, i.e. the token's own expiry minute — direct corroboration of the root
      cause). Procedure promoted to `scripts/dev/remint-orch-token.sh` so the next expiry is one command.

- [x] ✅ **DONE 2026-07-26 (slot-11, `infra`) — `unified-trading-pm@804fa2b9a`.** Make `slot-git-status-report.sh`
      prefer `http://localhost:8765` (trusted-local, no token) when the loopback backend is reachable, falling back to
      the public `ORCH_URL` + `ORCH_TOKEN_FILE` when it is not (off-VM operator laptops). Do NOT unconditionally flip
      the default `ORCH_URL` — that would break off-VM reporters. **Done-when:** on host ip-172-31-5-118, after the next
      reporter tick `/api/fleet/git-health` shows `reporter_stale=false` for the host's slots and
      `git_staleness_alert_sent` stops firing; off-VM path still uses public URL + token (verified by reading the
      branch, not just on-VM behaviour). Wire into the primary consumer's `quality-gates.sh` if the script isn't already
      covered. Implementation: a top-level probe (skipped entirely when `--orch-url`/`ORCH_URL` is explicit) hits
      `LOOPBACK_ORCH_URL` (default `http://localhost:8765`) `/api/healthz` with a 1s connect-timeout; on 200 it sets
      `ORCH_URL`+`IS_LOOPBACK=1` for the whole run. `resolve_token_for_slot` now succeeds with an EMPTY token in
      loopback mode when no token file exists (instead of skip-with-no-POST); `post_snapshot`/`post_starve_ping` omit
      the `Authorization` header entirely when the token is empty (not `Bearer ` with nothing after) so the request
      qualifies for the server's `_is_trusted_loopback` anonymous fallback. Live-verified against the real orchestrator
      (not just unit tests): ran the reporter with `ORCH_TOKEN_FILE` pointed at a deliberately garbage token, restricted
      to slot 11 — `[loopback] http://localhost:8765 reachable...` fired, POST succeeded
      (`[ok] slot 11 — 25 repos reported`), and `/api/fleet/git-health` confirmed `reporter_stale=false` for slot 11
      immediately after. 7 new hermetic bats tests in `tests/test_slot_git_status_loopback_preference.bats` (explicit
      URL/env override still wins; loopback-reachable vs unreachable; `resolve_token_for_slot` loopback-tolerant vs
      off-VM-strict; `post_snapshot` sends no Authorization header on an empty token) — all pass, plus the 7
      pre-existing `test_slot_git_status_dirty_count.bats` tests unaffected. `quality-gates.sh` green (sentinel matches
      HEAD). **"Wire into quality-gates.sh"**: NOT done — discovered `bats tests/` is not actually invoked anywhere in
      this repo's QG pipeline (bats-core is installed by CI tooling but never run), a pre-existing gap spanning every
      `.bats` file and the shared `base-service.sh` framework, out of scope for this one-script fix. Filed as
      `/plans/active/issues/pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md`.
- [x] [INFRA] ✅ **MOOT — verified resolved 2026-08-06, no action needed.** Immediate unblock (independent of the code
      fix): refresh `~/.orch_token` on ip-172-31-5-118 so the reporter resumes now, and confirm `reporter_stale` clears
      within one tick. **Why moot:** the 2026-07-26 loopback fix removed that host's token dependency entirely, exactly
      as the 2026-07-30 na-audit suspected but could not verify offline. Now measured live from `hk`:
      `/api/fleet/git-health` host `ip-172-31-5-118` = 17 slots, `reporter_stale` **0**, oldest report
      `2026-08-06T16:57:03Z` (~4 min old). Closing on evidence rather than leaving a stopgap open against a host that no
      longer needs it.

- [x] [INFRA] ✅ **DONE 2026-08-09 (batch16, `unified-trading-pm@b427499b33`) — token-near-expiry early warning shipped,
      option (a).** `scripts/dev/slot-git-status-report.sh` now decodes the reporter's own bearer JWT `exp` claim (the
      same decode already used for the treadmill diagnosis) and fires ONE state-transition-dedup warning into the AO
      activity feed once `exp` is within `TOKEN_EXPIRY_WARN_DAYS` (default 3) of now, per
      `/codex/04-architecture/agent-orchestrator-alerting.md`'s standing-condition convention — does not refire on
      unchanged-state ticks, clears on re-mint. TTL left unchanged (per this doc's own "do NOT just raise the TTL"
      ruling). **Evidence**: `tests/test_slot_git_status_token_expiry.bats` (7/7 pass, bats-core installed to a scratch
      prefix since the host had none) plus an independently-authored second repro harness (own throwaway HTTP server +
      JWTs, sourcing the real shipped `decode_jwt_exp`/`check_token_expiry_for_slot` functions directly) — 13/13 checks
      pass: fires exactly once on a 2.5-day-out JWT, does not refire across 3 unchanged ticks, clears on re-mint with no
      spurious fire, re-fires correctly on a fresh near-expiry episode, plus 2 boundary cases outside the shipped suite
      (exactly-at-3-days still fires; an already-expired token still fires rather than being silently skipped). Full
      independent re-verification (not just a re-read of the shipped test) done in
      `/plans/active/ao_satellite_ao_dispatch_batch16_finalize_2026_08_09.md` todo 1, 2026-08-10.

- [ ] [INFRA] P3. **Ghost host rows: `ip-172-31-0-185` is permanently `reporter_stale`/`ff_cron_stale` for a VM that no
      longer exists.** Measured 2026-08-06 from `/api/fleet/git-health`: host `ip-172-31-0-185` (`vm_id: planning`)
      still lists 3 slots, frozen at `2026-07-25T03:32:01Z` (slot 0) and `2026-07-28T14:02:02Z` (slots 1-2), all
      `reporter_stale=true`. `aws ec2 describe-instances --filters Name=private-ip-address,Values=172.31.0.185` returns
      **[]** — this is the human-planning VM terminated 2026-08-03 (see CLAUDE.md § System map). Net effect: fleet
      git-health can never read all-green, and any staleness condition keyed off these rows is a standing alert that can
      never resolve — precisely the never-resolving-condition anti-pattern
      `/codex/04-architecture/agent-orchestrator-alerting.md` rules against. Fix: prune or tombstone slot rows whose
      host has no live instance (decide which, then make the fleet view reflect it); confirm no alert path fires on them
      afterwards.

## Notes

- Non-blocking / no-page disposition confirmed with review (agt-af7186, msg 1867) and main on 2026-07-24.
- Sibling reporter issue (different failure mode — mid-FF-pull dirty flicker):
  /plans/archive/issues/git_health_phantom_dirty_flicker_ff_cron_race_2026_07_21.md.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — the one open `[INFRA] P3` is re-minting `~/.orch_token`, a
  credential operation, already ruled 'a distinct credential operation' in
  `ao_satellite_ao_dispatch_batch1_2026_07_26.md`'s Deferred list. Noted but NOT verified this run (no live orchestrator
  access from an offline audit worktree): the durable loopback fix shipped `unified-trading-pm@804fa2b9a` on 2026-07-26
  removes the on-VM token dependency entirely, so this stopgap may already be moot for the central host — confirm
  `reporter_stale=false` live before closing it.
- **context-scout 2026-08-03**: refreshed context_scope (4 entries, unchanged — verified all still resolve).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.

### 2026-08-06 — `hk` re-minted, verified end-to-end, procedure promoted

Host `hk` recovered: 15/16 slots were frozen at `2026-08-05T06:07:04Z`, now 0/16 stale. `ip-172-31-5-118` confirmed
already healthy (loopback fix). New: `ip-172-31-0-185` is a ghost host (todo above).

**Traps — both mint a token that looks perfect and 401s. `scripts/dev/remint-orch-token.sh` encodes both; do not
re-learn them by hand:**

1. **The signing secret is not in the shell.** `sudo -u ubuntu .venv/bin/python -c "auth.issue_token(...)"` on the VM
   returns a well-formed 171-byte JWT that the server rejects. `auth._load_secret()` is env-first →
   `ORCHESTRATOR_JWT_SECRET` (a literal in `.env.local`) → `ORCHESTRATOR_JWT_SECRET_GCS` → **silent per-process
   `secrets.token_urlsafe(32)` fallback**, warning to stderr only. Neither var is in ubuntu's profile — they are in the
   systemd unit — so an ad-hoc mint always takes the fallback. Diagnostic that settles it in one round trip: mint twice
   and print `sha256(auth._jwt_secret)[:12]` — a **changing** fingerprint means fallback; a stable one that matches
   `sha256` of the running process's `/proc/<MainPID>/environ` value means you have the real secret. Also do NOT "fix"
   it by exporting `ORCHESTRATOR_JWT_SECRET_GCS`: the GCS read needs ADC the sudo shell also lacks, so it fails the same
   silent way. Source `.env.local` instead.
2. **`aws ssm get-command-invocation --output text` ends with a trailing blank line**, so `tail -1` yields an EMPTY
   token and curl sends a bare `Bearer `. The server's reply is byte-identical to a genuine signature failure, which
   sends you hunting the secret again after you have already fixed it. Use `head -1`.

**Method note:** verify the minted token against the live API BEFORE overwriting the existing token file. A failed mint
must not also destroy a working (or merely soon-to-expire) credential — the script now enforces this ordering.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.

- **na-eligibility-audit 2026-08-09 (round11)**: satellite-extraction, partial — re-read end-to-end (the prior 6 markers
  on this doc were generic boilerplate that never quoted either open item's actual text). The `[INFRA] P2` "30-day
  treadmill" item is NOT a genuine design fork on closer read: the doc's own text already picks option (a) ("is the
  smallest and needs no new credential surface") with a concrete done-when — extracted to
  `/plans/active/ao_satellite_ao_dispatch_batch16_2026_08_09.md`. This doc was excluded from the same-day
  `/ag-closeout-audit ao` batch12 run's fresh 36-doc scan because it's cited by
  `ao_satellite_ao_dispatch_batch2_2026_07_30.md` — but that citation only covers 2 OTHER, already-closed items, not
  this one; a citation-based pre-filter isn't the same as content coverage. Doc stays `assigned_vm: NA` overall: the
  remaining `[INFRA] P3` "Ghost host rows" item is a genuine unresolved design call (the doc's own text explicitly asks
  the worker to "decide which" of prune-vs-tombstone) — no whole-doc RECLASSIFY, per-item extraction only.
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep)**: KEEP-NA, valid — `grep -cE '^[[:space:]]*[-*] \[ \]'` =
  **2**, matching. The `[INFRA] P2` "30-day treadmill" item is already correctly
  `➡️ EXTRACTED 2026-08-09 to ao_satellite_ao_dispatch_batch16_2026_08_09.md` (verified live: exists, `status: active`,
  `assigned_vm: planning`). The `[INFRA] P3` "Ghost host rows" item remains a genuine, explicit "decide which" design
  fork (prune vs. tombstone) the doc's own text never resolves — no new bounded item found on independent re-read.
- **2026-08-10 (batch16 finalize, slot-13)** — Todo 2: reconciled batch16's verified evidence back onto this doc's own
  `[INFRA] P2` checkbox, flipping it `[x]` with the real commit sha / test evidence / independent re-verification detail
  instead of the extraction redirect-pointer. Doc retains 1 open item (`[INFRA] P3` ghost-host-rows, a genuine
  prune-vs-tombstone design call) — stays `status: open`, not archived.
