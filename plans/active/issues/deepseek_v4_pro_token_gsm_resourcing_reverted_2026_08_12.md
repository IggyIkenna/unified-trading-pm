---
doc_type: issue
title: >-
  deepseek-v4-pro token GSM re-sourcing is NOT live — creds_env_poller re-syncs the literal from S3, and the native
  proxy would break under the indirection
summary: >-
  Fresh measurement (slot 16, 2026-08-12) proves the batch14/finalize "re-source ANTHROPIC_AUTH_TOKEN from GSM" fix is
  not live. ~/.claude-accounts/deepseek-v4-pro.env still carries the literal token (no `gcloud secrets` indirection,
  grep-count 0), and the S3 creds bucket s3://uts-orchestrator-creds-427895769566/accounts/deepseek-v4-pro.env is
  byte-identical to it (sha256 86f0758f... both). Root cause: `creds_env_poller.py` re-syncs the local env file from
  that bucket every `creds_env_poll_interval_seconds` (default 300s), so the finalize-plan todo-2 local-only edit
  (2026-08-10, slot 5) reverted within one tick. The prior "DONE" record (finalize todo 2) and the slot 18/20 skip
  verdicts were based on the doc, not a live file read. Second, latent gap (never exercised because the edit never
  persisted): the account's ANTHROPIC_BASE_URL points at the running native proxy
  (http://127.0.0.1:8767/accounts/deepseek-v4-pro), and `deepseek_native_proxy_server._handle_native` resolves the token
  via `read_env_var_from_file` (literal regex parse, no command substitution, `usage_tracker.py:174`) — so a `$(gcloud
  secrets versions access ...)` indirection in the file would make the proxy send the command string as the Bearer token
  (DeepSeek 401), breaking the account.
status: open
resolved_by:
nature: notes
asset_group: [ao]
repos: [agent-orchestrator]
tags: [credential-sourcing, gsm, secret-manager, deepseek, env-file, creds-env-poller, native-proxy, false-done]
created: 2026-08-12
author: claude-agent
parent_epic: orchestrator_master
priority: P0
source:
  - /plans/active/ao_satellite_ao_dispatch_batch14_2026_08_09.md
  - /plans/active/ao_satellite_ao_dispatch_batch14_finalize_2026_08_09.md
  - /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md
related:
  [/plans/active/ao_consolidated_closeout_2026_08_12.md, /plans/active/ao_satellite_ao_dispatch_batch14_2026_08_09.md]
assigned_vm: planning
drift_direction: advance-code
stage: [meta]
scope: [engineer, admin]
execution_scope: orchestrator-agent
depends_on: []
locked_by:
locked_since:
---

# deepseek-v4-pro token GSM re-sourcing reverted + native-proxy incompatibility

## What I found

Dispatched on `ao_satellite_ao_dispatch_batch14-791d3e7d35b7` (batch14 `[INFRA] P2` — re-source `ANTHROPIC_AUTH_TOKEN`
from GSM). Slots 18 and 20 already skipped this same task twice today (2026-08-12), trusting the finalize plan's flipped
todo 2 ("fix landed 2026-08-10 slot 5"). I re-measured the LIVE state instead of the doc record. Measured on the
planning VM (`i-0c9b283b31d6b5ca7` / `13.113.200.22`, user `ubuntu`):

1. **The literal token is STILL live.**
   `grep -c 'gcloud secrets versions access' ~/.claude-accounts/deepseek-v4-pro.env` returns `0`; the file is a 5-line
   plain `export` file with a literal `ANTHROPIC_AUTH_TOKEN`. Live file sha256 =
   `86f0758f719394c4817f608aca80514ead6dda0c3e283757a3dc118391cfd77b`.
2. **The reversion source is the S3 creds bucket.** The running orchestrator (pid 1175401) has
   `ORCHESTRATOR_CREDS_S3_BUCKET=uts-orchestrator-creds-427895769566` set. The bucket's `accounts/deepseek-v4-pro.env`
   (read via UTL `get_storage_client(provider="aws")`, values never printed) is **byte-identical to the live file**
   (`86f0758f...`), also literal, also no indirection. `creds_env_poller.py` re-syncs `~/.claude-accounts/<id>.env` from
   that bucket every 300s (default `creds_env_poll_interval_seconds`, `config.py:1001`), overwriting local edits
   whenever bytes differ. Slot 5's 2026-08-10 fix edited only the local file → reverted within one poll tick. The file
   mtime (2026-08-12 14:38) is a poller re-sync; a `bak-canary-1786540999` backup (13:23 same day) already held the
   literal token, i.e. the indirection was already gone before today's canary activity.
3. **No wrong-secret risk in the value itself:** no-newline sha256 of the literal token in live file + all four backups
   (`presm`/`realfix`/`canary`/current) = `715f0bb827e70e22dbf924ef7a79d1d7189964086e0c30093914161f3f80d8c9`, which
   equals the GSM secret `deepseek-v4-pro-api-key` (project `central-element-323112`) value's hash. The literal and the
   secret are the SAME token — re-sourcing just needs to be made durable + proxy-safe.
4. **Latent proxy incompatibility (the real design gap).** The account's `ANTHROPIC_BASE_URL` is
   `http://127.0.0.1:8767/accounts/deepseek-v4-pro` — a RUNNING service (`deepseek_native_proxy_server`, port 8767).
   `_handle_native` builds `Authorization: Bearer {token}` from `_resolve_account_token()` →
   `read_env_var_from_file(env_file, "ANTHROPIC_AUTH_TOKEN")` (`usage_tracker.py:174`), a **literal regex parse with no
   command substitution**. If the file carried `export ANTHROPIC_AUTH_TOKEN="$(gcloud secrets versions access ...)"`,
   the proxy would send the command string as the token → DeepSeek 401 → the account's conversations through the proxy
   fail. Worker spawns (`tmux_spawn.py` `bash -c 'source <env_file>; exec claude'`) DO source the file, so the
   indirection resolves for them — the fix is half-compatible. The poller's revert therefore accidentally avoided
   breaking the proxy; a durable fix must not re-introduce it.
5. **Prior "done" records were doc-truth, not file-truth.** finalize todo 2's `c154633...` post-fix sha256 is NOT the
   current file (now `86f0758f...`); it was reverted within minutes of that edit. Slots 15/18/20 did not re-read the
   live file. This is the same "verify against the live object, not the label" discipline gap flagged in the source
   doc's own measurement-trap note.

## Why it matters

- A live API credential (`deepseek-v4-pro` token) is in **plaintext on the host and in the S3 creds bucket**, which is
  exactly what the source doc's `[INFRA] P2` todo exists to remove. The operator created the GSM secret (2026-08-09) on
  the explicit understanding the re-sourcing would then land; it has not, and the "done" bookkeeping said otherwise for
  2 days.
- The fix is not a one-line re-edit: the durable change needs the **S3 bucket source updated** (else the poller reverts
  within 5 min) AND the **native proxy's token resolution changed** (else the indirection breaks it). Two components,
  one of them a running-service credential path — a design decision, not a bounded worker task.
- `regen_backlog_from_plan.py` has re-derived a task from batch14's intentionally-permanent `[ ]` checkbox 5×
  (2026-08-09, pre-2026-08-12, slot 18, slot 20, slot 16) — each a full re-diagnosis session. Landing the finalize
  plan's remaining todos (3: reconcile into source doc; 5: archive the batch plan) is the structural stop; this
  finding's fix todos unblock todo 3's evidence.

## Recommended decision

1. Operator/main picks the proxy-token-resolution approach so the implementation is bounded:
   - **(A — recommended)** `_resolve_account_token` reads the token directly from GSM via UTL `get_secret`
     (`deepseek-v4-pro-api-key`), mirroring the re-sourcing intent and `refresh_env_from_sm.sh`; the env file then
     exists only for worker-spawn sourcing.
   - (B) `read_env_var_from_file` (or `_resolve_account_token`) shells out to resolve the fixed `$(gcloud ...)`
     substitution (contradicts `usage_tracker.py`'s no-subprocess rationale).
   - (C) leave the file literal and re-scope the whole re-sourcing todo to the proxy/worker layer only.
2. Then a worker applies the durable re-sourcing: update BOTH the S3 bucket `accounts/deepseek-v4-pro.env` AND the local
   file to the indirection (so `creds_env_poller` distributes it and stops reverting), verify resolved-token hash == GSM
   secret + a `claude -p` probe returning 402-not-401/403 (balance is exhausted, `-0.21` — a clean 200 stays
   untestable), and confirm the proxy resolves correctly through the new path.
3. Landing the finalize plan's todo 3 (reconcile) + todo 5 (archive batch14) afterwards stops the re-derivation thrash.

- [ ] [BACKEND] P0. Make `deepseek_native_proxy_server._resolve_account_token` resolve the account token via GSM (UTL
      `get_secret("deepseek-v4-pro-api-key")`, or a shell `source` of the env file per option B) instead of a literal
      parse of `~/.claude-accounts/deepseek-v4-pro.env`, so the env file can carry the `$(gcloud secrets ...)`
      indirection without sending the command string as the Bearer token. (repo: agent-orchestrator)
- [ ] [INFRA] P0. Re-apply the deepseek-v4-pro GSM re-sourcing DURABLY: upload the indirection version of
      `deepseek-v4-pro.env` to the S3 creds bucket (`uts-orchestrator-creds-427895769566/accounts/`) AND rewrite the
      local `~/.claude-accounts/deepseek-v4-pro.env` to match (so `creds_env_poller` no longer reverts it), then verify
      resolved-token hash == GSM secret hash (`715f0bb8...`) + a `claude -p` probe returning 402-not-401/403, and record
      before/after evidence. (repo: agent-orchestrator — host-local config + creds bucket)
- [ ] [REVIEW] P2. Correct the stale "DONE 2026-08-10 (slot 5)" record on
      `ao_satellite_ao_dispatch_batch14_finalize_2026_08_09.md` todo 2 (the edit was real but was reverted by
      `creds_env_poller` within one tick and is not live today) — append the reversion evidence so the finalize plan's
      todo 3 reconcile carries truthful data. (repo: unified-trading-pm)

## Codex SSOTs

`/codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md`,
`/codex/05-infrastructure/gcs-object-operations.md`,
`/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`.
