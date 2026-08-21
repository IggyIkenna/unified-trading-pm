---
doc_type: issue
title: "CredsEnvPoller is disabled fleet-wide — a rotated Claude Code token never reaches the live VM without manual intervention"
summary: >-
  Investigating why `sub-h-igboestates` (`igboestates@gmail.com`) stayed `status: auth_failed` on the live
  orchestrator after a fresh `claude setup-token` value was minted and uploaded to both creds buckets, exactly
  following `/codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md`'s documented procedure. Root cause:
  `orchestrator.service`'s systemd unit sets neither `ORCHESTRATOR_CREDS_S3_BUCKET` nor
  `ORCHESTRATOR_CREDS_GCS_BUCKET`, so `CredsEnvPoller.start()` (`server/creds_env_poller.py`) logs "disabled" and
  never runs — the ONLY mechanism this codebase has for pulling a rotated `.env` file down from the creds buckets to
  `~/.claude-accounts/` at runtime. The original 7 accounts (`sub-a` through `sub-g`) got their env files from
  `bootstrap_vm.sh`'s STEP 5a, a ONE-TIME fetch that only runs at VM boot/re-provision — not a standing sync. This
  means every one of the 8 personal accounts has the SAME latent gap: a future token rotation (setup-tokens are
  valid ~1 year, so this will recur) will silently fail to reach the live VM the same way, with no error surfaced
  anywhere except the account sitting in `auth_failed`.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, credentials, oauth, multi-account, infrastructure, creds-poller]
related:
  [
    /codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md,
    /plans/active/ao_open_work_consolidated_tracker_2026_08_14.md,
  ]
context_scope:
  [
    agent-orchestrator/server/creds_env_poller.py,
    agent-orchestrator/scripts/bootstrap_vm.sh,
    agent-orchestrator/server/usage_poller.py,
    /codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md,
  ]
created: 2026-08-18
last_updated: 2026-08-19 # was 2026-08-18 -- stale vs the 2026-08-19 na-eligibility-audit + live SSM-applied-fix entries; corrected (plan_reconciler ao)
parent_epic: orchestrator_master
priority: P2
assigned_vm: NA
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: >-
  Surfaced completing the igboestates-account (sub-h-igboestates) onboarding's remaining gap (operator handed a
  freshly-minted `claude setup-token` value, reporting "missing the token"/`auth_failed`) — investigated live via
  read-only SSM against the orchestrator VM (i-0c9b283b31d6b5ca7).
execution_scope: local-only
drift_direction: advance-code
---

# CredsEnvPoller is disabled fleet-wide — a rotated Claude Code token never reaches the live VM without manual intervention

## What's wrong

`server/creds_env_poller.py::CredsEnvPoller.start()`:

```python
target = self._provider_and_uri()
if target is None:
    logger.info("CredsEnvPoller disabled — no ORCHESTRATOR_CREDS_S3_BUCKET / ORCHESTRATOR_CREDS_GCS_BUCKET set")
    return
```

Confirmed live (2026-08-18, read-only SSM against `orchestrator.service`'s systemd unit): `Environment=` carries
`ORCHESTRATOR_S3_BUCKET` (the STATE bucket, a different var) and several other real values, but neither
`ORCHESTRATOR_CREDS_S3_BUCKET` nor `ORCHESTRATOR_CREDS_GCS_BUCKET`. The poller therefore never starts its thread —
confirmed by the matching symptom: uploading a correctly-formatted `.env` to BOTH creds buckets (per the SSOT's own
documented procedure) never produced a local `~ubuntu/.claude-accounts/sub-h-igboestates.env` file, even after
waiting well past the poller's own 300s default interval.

This means the ONLY path that has EVER populated `~/.claude-accounts/` on this VM is `bootstrap_vm.sh`'s STEP 5a
(`aws s3 cp ... --recursive` / `gsutil -m cp ...`), which runs once at boot/re-provision. Every account currently
`healthy` (`sub-a` through `sub-g`, plus the now-fixed `sub-h`) got its `.env` that way, or via the manual
UTL-based one-time fetch this session used as a workaround (see Todos). None of them will pick up a ROTATED token
without either a VM reboot/re-run of `bootstrap_vm.sh`, or the same manual fetch repeated by hand.

## Real measured impact

`sub-h-igboestates` sat in `auth_failed` from account creation (earlier the same day, 2026-08-18) through at least
one full operator-provided fresh token upload, because the distribution half of the documented procedure silently
did nothing. The fix this session applied was a manual, one-off UTL `download_file()` call via SSM directly to the
VM's local path — real, but not the STANDING mechanism the codebase believes exists (the codex SSOT's own framing,
"have the running fleet pick it up within one poll interval, without a re-bootstrap", is currently false for this
VM). Every one of the other 7 personal accounts' setup-tokens is `~1 year` valid (per `setup_token_expires_at`) —
this will recur on each one's own expiry unless fixed.

## Todos

- [ ] [REVIEW] P2. **Operator decision RESOLVED 2026-08-19** (see Progress Log) and config APPLIED live —
      remaining work is verification only (capture a "CredsEnvPoller started" log line / observe a real rotation
      land), not a pending operator decision. Decide whether to enable `CredsEnvPoller` by setting `ORCHESTRATOR_CREDS_S3_BUCKET` (or
      `ORCHESTRATOR_CREDS_GCS_BUCKET`) on `orchestrator.service`'s systemd unit and restarting — this is a live
      service config change + restart, the same category of action
      `claude-cli-multi-account-headless-auth.md` already flags as needing operator confirmation before doing
      unilaterally (in-flight dispatches risk), so it's parked here rather than done automatically. Recommended
      value: `uts-orchestrator-creds-427895769566` (S3) or `central-element-323112-orchestrator-creds` (GCS),
      matching the two buckets the onboarding SSOT already documents. Done when: the env var is set, the service
      restarted at an operator-confirmed time, and a real token rotation (or a no-op env-file re-upload) is observed
      landing in `~/.claude-accounts/` within one poll interval without any manual SSM intervention.
- [ ] [REVIEW] P3. Once the poller is confirmed working end-to-end, update
      `/codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md`'s own framing (it currently states the
      poller "exists so an operator can rotate a long-lived setup-token... and have the running fleet pick it up
      within one poll interval" as if this were already true) to either confirm it's now real, or keep flagging it
      as aspirational until verified — don't leave the doc's claim ahead of the actual verified state.

## Progress Log

- **2026-08-18 (created)**: root-caused and worked around live during `sub-h-igboestates` onboarding completion —
  see the `agent-orchestrator` repo's own session for the manual fix (UTL `download_file()` via SSM, not
  `CredsEnvPoller`, which is confirmed disabled). The account itself is now `status: healthy`
  (`weekly_pct=12`, `five_hour_pct=8`, real `last_used_at`) — this issue tracks the STANDING poller gap, not the
  one-off symptom, which is already resolved.

- **na-eligibility-audit 2026-08-19 (ao tranche)** [body-hash:a31fbbeb17037f53]: KEEP-NA, valid — primary/blocking todo is an [OPERATOR]-tagged live orchestrator.service systemd env-var change + restart (fleet-critical service, in-flight dispatch risk); todo 2 is gated on todo 1's outcome and can't execute meaningfully first.
- **2026-08-19 (interactive session, operator-authorized: "ao is quiet, do it yourself, you have adc")**: applied the
  config half live via SSM against `i-0c9b283b31d6b5ca7`. Appended `ORCHESTRATOR_CREDS_S3_BUCKET=uts-orchestrator-creds-427895769566`
  to `/home/ubuntu/unified-trading-system-repos/agent-orchestrator/.env.local` (the recommended S3 value, matching
  the existing `ORCHESTRATOR_S3_BUCKET` state-bucket pattern on the same AWS account — chose S3 over GCS for
  consistency, no other reason to prefer either) and restarted `orchestrator.service`. **Confirmed**: service came
  back `ActiveState=active`/`SubState=running`, `/api/healthz` returned `200` post-restart (verified across 2
  separate checks, ~30s apart — the FIRST check raced an unrelated, ordinary `ao-self-pull.sh` restart cycle that
  landed ~20s after mine, both cleanly resolved). **NOT independently confirmed**: this doc's own done-when
  ("a real token rotation... observed landing in `~/.claude-accounts/` within one poll interval") — I verified the
  config is live and the service restarted with it present, which per `creds_env_poller.py`'s own code (the
  `disabled` branch only fires when `_provider_and_uri()` returns `None`, i.e. neither bucket var is set) should
  mean the poller now starts its thread, but I did not independently capture a "CredsEnvPoller started" log line or
  observe an actual rotation land — leaving the checkbox open until that stronger bar is met. **Webhook half NOT
  applied**: the same pass attempted to set `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` per the prepared recipe in
  `ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md` — both documented secret names
  (`AGENT_ORCHESTRATOR_SLACK_WEBHOOK`, `alerting-uts-live-alerts-slack-webhook`) under project `central-element-323112`
  returned empty via `gcloud secrets versions access latest`, and a follow-up `gcloud secrets list ... | grep -iE
  "slack|webhook|alert"` also returned nothing (command exited non-zero with no stdout) — genuinely could not locate
  the secret under either documented name or a name-pattern search, not a transient failure. This is orthogonal to
  the creds-poller fix (unrelated env var, tracked in the sibling doc) — not chased further this pass; flagging so
  the next attempt doesn't repeat the same 2 dead-end secret names.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
