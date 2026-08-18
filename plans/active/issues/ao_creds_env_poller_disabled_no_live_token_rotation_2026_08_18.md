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
  ]
created: 2026-08-18
last_updated: 2026-08-18
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

- [ ] [OPERATOR] P2. Decide whether to enable `CredsEnvPoller` by setting `ORCHESTRATOR_CREDS_S3_BUCKET` (or
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
