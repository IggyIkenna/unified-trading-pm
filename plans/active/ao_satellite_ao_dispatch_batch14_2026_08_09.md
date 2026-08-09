---
doc_type: plan
title: AO satellite AO batch 14 — re-source ANTHROPIC_AUTH_TOKEN from the now-live GSM secret (orchestrator_master epic)
summary: >-
  FOURTEENTH AO-dispatch batch for the `ao` topic tranche — a single-item satellite extraction from
  `deepseek_claude_blended_provider_routing_2026_07_28.md`, produced by a round9 `/na-eligibility-audit ao` re-sweep
  (2026-08-09) specifically checking for items unblocked by two credential facts that landed THAT DAY: the GSM secret
  `deepseek-v4-pro-api-key` was created live (operator, interactive ruling recorded in the source doc itself), and 5
  Slack alerting webhooks were provisioned. The source doc's `[INFRA] P2` re-sourcing todo was explicitly `BLOCKED on
  the operator todo above (needs the secret's exact name; do not guess one)` — that block is now cleared: the secret
  exists, its exact resource name is known and recorded in the source doc. A prior same-day `/ag-closeout-audit ao`
  Phase 1 pass (`ao_satellite_ao_dispatch_batch12_2026_08_09.md`'s Deferred section) declined this entire source doc as
  "operator-gated (4/6 items need operator-held DeepSeek credentials/production `accounts.json` access)" — that
  declination pre-dates (or did not register) the secret-creation fact; this batch targets specifically the one item the
  new fact unblocks, not a re-litigation of the doc's other 4 genuinely-gated items (2 real-production pilots, 1
  CLI-version design call, 1 gitignored-per-VM data check), which stay `assigned_vm: NA` per that same declination and
  this run's own re-confirmation.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-14, satellite-docs, satellite-extraction, credentials]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch14_finalize_2026_08_09.md,
    /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md,
    /plans/active/ao_satellite_ao_dispatch_batch12_2026_08_09.md,
    /plans/active/issues/operator_action_items_consolidated_2026_08_08.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md,
    /codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md,
  ]
source: >-
  `/na-eligibility-audit ao` round9 re-sweep, 2026-08-09 — specifically checking every `ao`-tranche NA doc for items
  unblocked by the 2026-08-09 GSM secret-creation fact (`deepseek-v4-pro-api-key`, project `central-element-323112`).
  Conflict-checked against all active `parent_epic: orchestrator_master` plans, batch10-13, and
  `operator_action_items_consolidated_2026_08_08.md` (which only records the secret as created, explicitly deferring the
  re-sourcing work to this exact source doc — not a competing dispatch claim).
---

# AO satellite AO batch 14

> **`status: draft`** — pending operator approval, same convention as batch5-13: flip to `active` to dispatch.
> **`assigned_vm: planning` / `execution_scope: orchestrator-agent`** once approved, same as the rest of this series.

## Why this plan exists

`deepseek_claude_blended_provider_routing_2026_07_28.md`'s `[INFRA] P2` todo ("Re-source `ANTHROPIC_AUTH_TOKEN` from the
GSM secret on BOTH hosts") was explicitly blocked pending the operator creating a GSM secret and naming it — "do not
guess one." The operator did exactly that on 2026-08-09 (interactive ruling recorded in the source doc's own Progress
Log): `deepseek-v4-pro-api-key` (project `central-element-323112`), version 1, confirmed via `gcloud secrets create`.
The naming half of the split-of-duties this todo was waiting on is done; the re-sourcing half — reading the token via
secret-manager indirection on both hosts instead of the literal key in `~/.claude-accounts/deepseek-v4-pro.env` — is a
bounded, worker-determinable infra task with no remaining judgment call.

The source doc's other 4 open items stay genuinely NA (re-affirmed by this run, consistent with
`ao_satellite_ao_dispatch_batch12_2026_08_09.md`'s Deferred-section declination and the source doc's own
2026-08-06/2026-08-07 na-eligibility-audit markers): 2 are operator-review production pilots gated on real elapsed
monitoring time, 1 is a CLI-version design call (fix depends on what the production VM's pinned `claude` binary actually
supports), 1 is a `accounts.json`-is-gitignored-per-VM data check not doable from this checkout. None of the 4 are
touched by the credential-creation fact this batch extracts on.

A 1-item batch is sanctioned by `task_template.md` §4 ("Fewer is fine; group RELATED items") with direct precedent
(`ao_satellite_ao_dispatch_batch9_2026_08_08.md`, `batch11_2026_08_09.md`, `batch13_2026_08_09.md`, all 1 todo).

## Rules for every worker on this plan

- Do not edit the source doc's remaining checkbox beyond appending your evidence when done — the paired finalize plan
  (`/plans/active/ao_satellite_ao_dispatch_batch14_finalize_2026_08_09.md`) reconciles evidence back into the source
  doc.
- **Never print or log the literal secret value.** Use secret-manager indirection end to end; verify success via a fresh
  spawn authenticating, not by echoing the token.
- This touches live credential-loading paths on two real hosts (this machine's equivalent + the planning VM) — dry-run
  the read path before removing the literal key from either file, and confirm a fresh spawn authenticates successfully
  BEFORE deleting the plaintext fallback.

## Todos

- [x] ✅ [INFRA] P2. **DONE 2026-08-09 (slot 30).** **Correction found while executing: "BOTH hosts" was stale — exactly
      the "either VM"/"both VMs" framing `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md` warns
      against carrying forward for the human-planning VM, terminated 2026-08-03 (CLAUDE.md: "`planning` is the ONLY
      VM"). Verified live via IMDSv2
      (`curl -H "X-aws-ec2-metadata-token: $TOKEN"     http://169.254.169.254/latest/meta-data/instance-id` →
      `i-0c9b283b31d6b5ca7`, `.../public-ipv4` → `13.113.200.22`) that THIS slot's own host **IS** the planning VM named
      in this todo — there was only ever ONE file to fix (`~/.claude-accounts/deepseek-v4-pro.env`, confirmed the sole
      `oauth_token_env_file` for this account in the live `accounts.json`, same `ubuntu` user the orchestrator process
      itself runs as). No SSM dispatch needed (operator's Option-B answer to the filed blocked question, `BLK-a07f8261`,
      is moot once this fact is known — not wrong, just resolved by a fact the blocked-question itself hadn't yet
      surfaced).

      Re-sourced via `export ANTHROPIC_AUTH_TOKEN="$(gcloud secrets versions access latest
          --secret=deepseek-v4-pro-api-key --project=central-element-323112)"` (mirrors
          `agent-orchestrator/scripts/refresh_env_from_sm.sh`'s pattern). Verification (the literal "successful spawn"
          bar in this todo's original text is currently unreachable for EITHER the old or new config — the account has
          $0 balance, tracked as its own fresh finding in the source doc below, not a re-sourcing defect): (1) SHA-256 hash
          of the GSM secret value == hash of the prior literal token, byte-identical; (2) a live `claude -p` auth probe
          under this account returns the IDENTICAL `API Error: 402 Insufficient Balance` on both the pre-change backup file
          and the post-change indirection file — proving the token reaches the API identically either way (a real auth
          failure would read 401/403, not 402). Literal key removed from the live file; a `chmod 600` backup
          (`deepseek-v4-pro.env.bak-presm-1786317618`) kept in `~/.claude-accounts/` as the reversible fallback until a
          genuine post-topup successful spawn is confirmed (operator's own security call whether/when to shred it).
          `unified-trading-pm@<pending>` (this doc + source doc updates). Source:
          `/plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md:440`. Repo: agent-orchestrator (env-file
          change is host-local config, not a repo commit — no agent-orchestrator sha for this todo itself).

## Codex SSOTs (read before starting)

`/codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md`,
`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`,
`/codex/12-agent-workflow/commit-push-flip-rule.md`.

## Progress Log

- **2026-08-09** — Authored by a round9 `/na-eligibility-audit ao` re-sweep, specifically checking for docs unblocked by
  two credential facts that landed 2026-08-09 (GSM secret creation; 5 Slack webhooks provisioned — the latter does not
  touch this doc). Conflict-check: grepped all active `parent_epic: orchestrator_master` plans plus batch10-13 for
  `ANTHROPIC_AUTH_TOKEN`/`deepseek-v4-pro-api-key` — the only hit outside the source doc itself is
  `operator_action_items_consolidated_2026_08_08.md`, which records the secret as operator-created and explicitly points
  the re-sourcing work back at the source doc ("re-sourcing on both hosts is the next (non-operator) todo there") — a
  status pointer, not a competing dispatch claim. Clear to extract. Noted for the record: a same-day
  `/ag-closeout-audit ao` Phase 1 pass (batch12) had already classified this source doc's whole remainder as
  operator-gated before (or without registering) the secret-creation fact — this batch corrects that stale declination
  for the one item the new fact actually unblocks, leaving the other 4 genuinely-gated items alone.

- **2026-08-09 (slot 30, infra craft) — todo 1 DONE**: initially blocked on what looked like a missing-SSM-access gap to
  reach "the planning VM" as a second host (`BLK-a07f8261`, operator answered "B — dispatch as a task on the planning VM
  itself" before I'd finished checking my own instance identity). Discovered mid-flight: this slot's own host IS the
  planning VM (verified via IMDSv2 instance-metadata, `i-0c9b283b31d6b5ca7`/`13.113.200.22` match exactly) — so "both
  hosts" collapsed to one, already fixed. See the flipped todo above for the full evidence (hash-match +
  identical-402-both-configs verification method, since the account's own $0 balance — filed as a fresh recurrence in
  the source doc — blocks a literal clean-200 spawn test right now). No SSM dispatch was actually needed in the end; the
  operator's B ruling was still the RIGHT call given what was known at blocked-question time, it just turned out to be
  moot once the host-identity fact surfaced.
