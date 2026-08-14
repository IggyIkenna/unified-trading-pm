---
doc_type: issue
title: >-
  market-tick-data-service main is 1384 commits behind LDR (promote PR #953 closed-not-merged, no successor opened
  across 3 fleet-bot ticks); separately, the QG-slice-failed Slack notification re-fires on an unchanged stale PR/sha
  with no dedup
summary: >-
  Live, unresolved as of this doc's creation (2026-08-11 09:18Z), found mid-`/ci-reconcile` session. Two distinct
  findings on `market-tick-data-service`. (1) Promotion stall: promote PR #953 (head `143fceffcb80`, testing-merge sha
  `9afe4693`) was blocked on QG STEP 5.94 (blanket pyright-suppression ratchet) until a fix landed at
  `market-tick-data-service@ccb84c57` (peer-session-shipped, verified GREEN on LDR's own branch-push
  `quality-gates-v2`). PR #953 then CLOSED at 08:53:05Z — but `git merge-base --is-ancestor ccb84c57 origin/main`
  returns NO, i.e. the fix never actually merged; the close was the bot's own stale-PR housekeeping (superseded-ref
  cleanup), not a successful promotion. `gh api compare/main...live-defi-rollout --jq .ahead_by` = **1384** at last
  check (09:15Z) — a large, real gap. `ldr-to-main-promote-fleet.yml` reported `success` on 3 consecutive ticks after
  the close (08:52, 09:00, 09:15) with NO new open promote PR appearing for this repo in any of them. Root cause of why
  no successor PR opened is NOT YET DIAGNOSED — needs a fresh session to re-check current state (`gh pr list --repo
  IggyIkenna/market-tick-data-service --search promote --state open`) and, if still stuck, read the fleet bot's own run
  logs for this repo specifically to see what decision it's making each tick. (2) Alert redispatch: the operator
  observed the IDENTICAL Slack alert (PR #953, sha `9afe4693`, "QG slice(s) FAILED") fire twice 15 minutes apart (9:34
  and 9:49 local) with no content change in between — meaning something re-triggered a fresh `quality-gates-v2` run
  against the SAME stale PR head on a ~15-min cadence (matching the fleet-bot's own tick interval) without the
  underlying content ever changing, and the "Slack CRITICAL — QG Slice Failed" job (a step inside `quality-gates-v2.yml`
  itself, confirmed present via `grep` in `market-tick-data-service/.github/workflows/quality-gates-v2.yml`) fires
  unconditionally per-run with no dedup_key/cooldown against a repeat identical failure — unlike the dedup'd
  `notify-slack.yml` carrier CLAUDE.md documents for other CI alert paths. NOT YET ROOT-CAUSED: what specifically
  re-triggers the run each tick (the workflow's actual `on:` triggers weren't found via grep on the per-repo file,
  meaning it's likely a reusable-workflow call into `unified-trading-ci` — check there next) and whether this Slack step
  should route through the shared dedup'd carrier instead of firing raw.
status: open
nature: issue
scope: [engineer]
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service, unified-trading-ci, unified-trading-pm]
tags: [ci-reconcile, promotion-lag, quality-gates, slack-alerting, dedup, market-tick-data-service]
related:
  [
    /plans/active/issues/ci_reconcile_overnight_batch_2026_08_11.md,
    /codex/04-architecture/ci-alerting.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
context_scope:
  [
    /codex/04-architecture/ci-alerting.md,
    /codex/08-workflows/ci-cd-flow.md,
    unified-trading-pm/scripts/cicd/ldr_to_main_fleet_promote.sh,
    unified-trading-ci/.github/workflows/python-quality-gates-v2.yml,
  ]
created: 2026-08-11
author: claude-agent
last_updated: 2026-08-11
parent_epic: infrastructure_master
priority: P1
source: /ci-reconcile session, operator-observed duplicate Slack alerts 2026-08-11 09:34/09:49
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
drift_direction: advance-code
depends_on: []
archive_exempt: true
---

> **Progress Log 2026-08-14 (slot-29, review, `cross_cutting_satellite_ao_dispatch_batch13b_2026_08_13_finalize.md`
> todo 1)**: reached 0 open todos this session via checkbox reconciliation from
> `cross_cutting_satellite_ao_dispatch_batch13b_2026_08_13.md`. `archive_exempt: true` set deliberately — full 6-step
> archival (incl. corpus-wide referrer fixup) is that finalize plan's separate todo 2, not this reconciliation pass's
> scope. Drop this field and archive when todo 2 runs.

# market-tick-data-service main promotion stall + QG-slice-failed Slack redispatch

## Finding 1 — main is 1384 commits behind LDR, promote PR closed without merging

**Timeline**:

- Promote PR #953 opened, blocked on STEP 5.94 (net-new blanket pyright-suppression headers on 2 new files — already
  root-caused and fixed this session, see `check_adapter_contract_regression.py`-adjacent work in the overnight-batch
  doc's sibling history).
- Fix landed at `market-tick-data-service@ccb84c57` (a peer session, not this one — this session independently verified
  it via `grep -c "^# pyright: report"` returning 0 on both previously-flagged files, and via a manual
  `gh workflow run quality-gates-v2.yml --ref live-defi-rollout` dispatch that reported `success`).
- PR #953 **CLOSED** at `2026-08-11T08:53:05Z`. `mergedAt` is `null`. This is the bot's documented
  superseded-ref-cleanup behavior (closes a stale `promote/<repo>/<old-sha>` PR when LDR's tip moves past it), NOT a
  successful merge.
- No new open promote PR exists for this repo as of the last check
  (`gh pr list --repo IggyIkenna/market-tick-data-service --search promote --state open` → `[]`).
- `ldr-to-main-promote-fleet.yml` (the repo's promotion mechanism — this repo does NOT have a per-repo standalone
  Option-B bot like `unified-trading-pm` does) ran successfully 3 times after the close (08:52, 09:00, 09:15 UTC)
  without opening a replacement PR for this repo.
- `ahead_by` (main behind LDR) = **1384** at 09:15Z — this is dramatically larger than the promotion-lag numbers seen on
  other repos this session (PM was ~445, UAC ~941) and is NOT something this session caused; it may be a long-standing
  gap that predates tonight, or the fleet bot may be structurally stuck on this repo specifically.

**Not yet done**: determine WHY no successor promote PR opened. Candidates to check first: (a) does the fleet bot skip a
repo if `ahead_by` exceeds some internal threshold or times out on a huge diff, (b) is there a genuine content conflict
between LDR and main for this repo (check `git merge-base main...live-defi-rollout` + attempt a local test merge, same
technique used earlier this session for `unified-trading-pm`'s `published_packages` conflict — that fix
(`reconcile_manifest_backmerge.py`, `unified-trading-pm@14ec1f1ab1`) does NOT apply here since MTDS has no per-repo
Option-B bot; the failure mode would be different), (c) read `scripts/cicd/ldr_to_main_fleet_promote.sh`'s own per-repo
decision logic / logs for `market-tick-data-service` specifically on the 08:52/09:00/09:15 runs.

## Finding 2 — QG-slice-failed Slack alert re-fired on the identical stale PR/sha, no dedup

Operator directly observed (pasted into chat, not independently re-derived by this session before compacting):

```
[9:34 AM] CRITICAL — python-quality-gates-v2 — QG slice(s) FAILED | market-tick-data-service | PR #953
  promote/market-tick-data-service/143fceffcb80 → main | sha 9afe4693ea3f7cdc529d7a1b440fed864bbbbabc
[9:49 AM] CRITICAL — python-quality-gates-v2 — QG slice(s) FAILED | market-tick-data-service | PR #953
  promote/market-tick-data-service/143fceffcb80 → main | sha 9afe4693ea3f7cdc529d7a1b440fed864bbbbabc
```

Identical PR, identical sha, 15 minutes apart, no recovery post in between. `sha 9afe4693` is GitHub's own synthetic
test-merge commit for PR #953 (confirmed via `gh api commits/9afe4693...` → commit message
`Merge 143fceffcb80... into 66ae3c80...`) — meaning something re-ran `quality-gates-v2` against that PR's (unchanged)
mergeability check TWICE, 15 minutes apart, and each run independently fired the "Slack CRITICAL — QG Slice Failed /
send-notification" step with no awareness of the prior identical page.

**Confirmed so far**: the Slack-notify step lives inside
`market-tick-data-service/.github/workflows/quality-gates-v2.yml` itself (found via the check-runs API:
`Quality Gates (market-tick-data-service) / Slack CRITICAL — QG Slice Failed / send-notification`), and a `grep` for
`dedup_key`/`cooldown_min` in that per-repo file returned nothing.

**Not yet done**: (a) the per-repo `quality-gates-v2.yml` `on:` trigger block wasn't located via a direct grep this
session (likely because the real trigger logic lives in the reusable workflow it calls,
`unified-trading-ci/.github/workflows/python-quality-gates-v2.yml`, per the pattern already confirmed for the separate
UAC "Install uv" incident earlier this session) — read that file next to find what re-dispatches this per-PR check every
~15 min. (b) confirm whether this Slack step should be migrated to the dedup'd `notify-slack.yml` carrier (`dedup_key` +
`cooldown_min`, per `/codex/04-architecture/ci-alerting.md`) the same way other CI alert paths already are, or whether a
fleet-bot-side fix (don't re-trigger `quality-gates-v2` on an unchanged PR head) is the more correct root fix — these
are two different fixes for two different possible root causes and this session did not get far enough to tell which
applies.

## Follow-ups

- [x] ✅ [SCRIPT] P1. Diagnose why no successor promote PR opened for `market-tick-data-service` across 3+ fleet-bot
      ticks after PR #953 closed — read `scripts/cicd/ldr_to_main_fleet_promote.sh`'s per-repo logic + the 08:52/
      09:00/09:15 run logs, and re-check current `ahead_by` (was 1384 at 09:15Z — confirm whether it's grown, shrunk, or
      stable). (repo: unified-trading-pm / market-tick-data-service) **RESOLVED 2026-08-13
      (cross_cutting_satellite_ao_dispatch_batch13b, unified-trading-pm@0f26818135) — correct behavior, not a stall.**
      Fleet bot evaluated MTDS each tick; verbatim run 31477434767 (09:22:47Z):
      `SKIP market-tick-data-service:     main tree == LDR tree (content-identical; any ahead_by is squash-accounting noise)`.
      `ahead_by` grew 1384→1436 but is squash-skew SHA-count noise: LDR carries the 1436 original commit SHAs a squash
      promote never replays onto main, while `git rev-parse main^{tree} == LDR^{tree}` (byte-identical content). No
      successor PR = nothing to promote. A successor (#963) DID open once real content landed 08-12 (merged stream
      #963-#980); #981 (tip cbc6531b) is open now. Code fix added: the content-gate SKIP line now prints compare
      ahead_by to self-document the squash-skew. Note: the QG-redispatch half of this issue (Finding 2) is a SEPARATE
      todo in cross_cutting_satellite_ao_dispatch_batch13b, not covered here.
- [x] ✅ [SCRIPT] P2. **ALREADY FIXED, no new code needed** — reconciled from
      `cross_cutting_satellite_ao_dispatch_batch13b_2026_08_13.md`: the redispatch was root-caused to the promote-PR
      head being a per-SHA frozen ref (`promote/<repo>/<sha12>`) that PM's drain bot supersedes roughly every ~15min,
      minting a fresh dedup key each time — matching the observed cadence. The Slack step was already routed through the
      dedup'd `notify-slack.yml` carrier before this todo was drafted; 3 peer `unified-trading-ci` commits (`45eabc2`
      15-min debounce, `e499f9d` tier-3 escalation at 30min, `ec6d421` redesign to track the underlying condition across
      PR supersessions) fully closed the gap. Confirmed live on `unified-trading-ci@67698d8`. Original text: Read
      `unified-trading-ci/.github/workflows/python-quality-gates-v2.yml`'s `on:` trigger config to find what
      re-dispatches a promote-PR's `quality-gates-v2` check on an unchanged head every ~15 min, and fix the redispatch
      (or, if redispatch is intentional/correct, migrate the "QG Slice Failed" Slack step to the dedup'd
      `notify-slack.yml` carrier so an unchanged repeat failure doesn't repage). (repo: unified-trading-ci)
- [x] [OPERATOR] P2. ~~Slack read access... needs an interactive `gcloud auth login`~~ — **SUPERSEDED 2026-08-11,
      corrected finding**: this todo's premise was wrong on two counts. (1) AO itself was never actually blocked —
      re-diagnosed live via SSM on the orchestrator VM: AO workers run as the `ubuntu` OS user, whose active gcloud
      identity is already `unified-trading-sa@central-element-323112.iam.gserviceaccount.com`, which already holds
      `secretmanager.secretAccessor` (granted 2026-07-31) and successfully read `SLACK_ALERTS_READER_BOT_TOKEN` live in
      this check. The earlier "no GCP identity on that VM" claim (`/codex/05-infrastructure/agent-slack-read-access.md`,
      now corrected) was checked as `root` via SSM's default shell, not `ubuntu` — a wrong-OS-user false negative, not a
      real gap. (2) There is no `github-token-sa` account in this project's IAM at all (`gcloud auth list` on the VM
      shows `github-actions-deploy`, `github-deploy`, `uac-weekly-validation-ci`, `unified-trading-sa`, and the
      operator's own account — never a `github-token-sa`); that name from the prior session's summary does not
      correspond to a real identity here and should not be reused. **What remains genuinely open**: the operator's own
      LAPTOP gcloud session (`ikenna@odum-research.com`) hits an org-enforced reauth window that fails non-interactively
      (`Reauthentication failed. cannot prompt during     non-interactive execution`, reproduced 2026-08-11) — this
      affects only interactive/laptop sessions running the script as the operator's personal identity, not AO.
      `slack-read-channel.py` already has a documented fallback (`SLACK_ALERTS_READER_BOT_TOKEN` env var) for exactly
      this case. A durable fix (SA impersonation or a dedicated key for local use) is a real security decision — flagged
      to the operator rather than self-served outright, since the self-service HARD RULE covers AO's own two cloud
      identities, not a human's personal laptop auth setup. **RESOLVED 2026-08-11, same session, operator go-ahead
      obtained**: impersonation was tried first and confirmed insufficient (still requires the human's own base session
      to mint the impersonated token — hits the identical reauth wall). Operator explicitly chose keying
      `unified-trading-sa` directly over a new minimal-scope SA, after being shown the blast-radius tradeoff (this SA
      holds project-admin roles). Key generated on the AO VM (as `unified-trading-sa`, after also granting it
      `roles/iam.serviceAccountKeyAdmin` on itself — it had `serviceAccountAdmin` but not key-creation rights),
      transported to the laptop via one-time hybrid RSA/AES encryption over the SSM channel (plaintext never left the VM
      in the SSM log; VM-side plaintext auto-shredded via a `trap ... EXIT`), installed at
      `~/.config/gcloud/keys/unified-trading-sa.json` (mode 600), activated as an additional (non-default) local gcloud
      account. `scripts/dev/slack-read-channel.py` was hardened in the same session to explicitly pin
      `--account=unified-trading-sa@...` first rather than trust ambient ADC — see
      `/codex/05-infrastructure/agent-slack-read-access.md` for the full mechanics and rotation instructions.
      **Correction note**: while live-testing the `ubuntu`-user secret access above, the real Slack bot token was
      briefly exposed (truncated via `head -c 80`, likely near-complete) into SSM command-invocation output and this
      session's transcript — flagged to the operator directly; recommend rotating `SLACK_ALERTS_READER_BOT_TOKEN` in
      Slack + GSM as a precaution.

## Progress Log

- **context-scout 2026-08-14**: populated context_scope (4 entries).
