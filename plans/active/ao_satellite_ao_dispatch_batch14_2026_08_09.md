---
doc_type: plan
title:
  AO satellite AO batch 14 — re-source ANTHROPIC_AUTH_TOKEN from the now-live GSM secret (orchestrator_master epic)
summary: >-
  FOURTEENTH AO-dispatch batch for the `ao` topic tranche — a single-item satellite extraction from
  `deepseek_claude_blended_provider_routing_2026_07_28.md`, produced by a round9 `/na-eligibility-audit ao` re-sweep
  (2026-08-09) specifically checking for items unblocked by two credential facts that landed THAT DAY: the GSM secret
  `deepseek-v4-pro-api-key` was created live (operator, interactive ruling recorded in the source doc itself), and 5
  Slack alerting webhooks were provisioned. The source doc's `[INFRA] P2` re-sourcing todo was explicitly
  `BLOCKED on the operator todo above (needs the secret's exact name; do not guess one)` — that block is now cleared:
  the secret exists, its exact resource name is known and recorded in the source doc. A prior same-day
  `/ag-closeout-audit ao` Phase 1 pass (`ao_satellite_ao_dispatch_batch12_2026_08_09.md`'s Deferred section) declined
  this entire source doc as "operator-gated (4/6 items need operator-held DeepSeek credentials/production
  `accounts.json` access)" — that declination pre-dates (or did not register) the secret-creation fact; this batch
  targets specifically the one item the new fact unblocks, not a re-litigation of the doc's other 4 genuinely-gated
  items (2 real-production pilots, 1 CLI-version design call, 1 gitignored-per-VM data check), which stay `assigned_vm:
  NA` per that same declination and this run's own re-confirmation.
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
monitoring time, 1 is a CLI-version design call (fix depends on what the production VM's pinned `claude` binary
actually supports), 1 is a `accounts.json`-is-gitignored-per-VM data check not doable from this checkout. None of the 4
are touched by the credential-creation fact this batch extracts on.

A 1-item batch is sanctioned by `task_template.md` §4 ("Fewer is fine; group RELATED items") with direct precedent
(`ao_satellite_ao_dispatch_batch9_2026_08_08.md`, `batch11_2026_08_09.md`, `batch13_2026_08_09.md`, all 1 todo).

## Rules for every worker on this plan

- Do not edit the source doc's remaining checkbox beyond appending your evidence when done — the paired finalize plan
  (`/plans/active/ao_satellite_ao_dispatch_batch14_finalize_2026_08_09.md`) reconciles evidence back into the source
  doc.
- **Never print or log the literal secret value.** Use secret-manager indirection end to end; verify success via a
  fresh spawn authenticating, not by echoing the token.
- This touches live credential-loading paths on two real hosts (this machine's equivalent + the planning VM) — dry-run
  the read path before removing the literal key from either file, and confirm a fresh spawn authenticates successfully
  BEFORE deleting the plaintext fallback.

## Todos

- [ ] [INFRA] P2. **Re-source `ANTHROPIC_AUTH_TOKEN` from the `deepseek-v4-pro-api-key` GSM secret on BOTH hosts** —
      this checkout's host and the planning VM (`i-0c9b283b31d6b5ca7`, EIP 13.113.200.22, via SSM). Read the token via
      `gcloud secrets versions access latest --secret=deepseek-v4-pro-api-key --project=central-element-323112`
      indirection (mirroring the pattern `agent-orchestrator/scripts/refresh_env_from_sm.sh` already uses for other
      secrets) instead of the literal `ANTHROPIC_AUTH_TOKEN=` line in `~/.claude-accounts/deepseek-v4-pro.env`. Verify a
      fresh DeepSeek-routed spawn authenticates successfully on each host BEFORE removing the literal key from that
      host's env file. **Done when**: both hosts read the token via secret-manager indirection, a fresh spawn
      authenticates on each, and the literal key is removed from both files (confirm via a direct file read on each
      host — the same standard the source doc's own "Verified still open 2026-08-06" measurement trap note warns
      against skipping). Source:
      `/plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md:440`. Repo: agent-orchestrator (+ host
      env-file changes on two hosts).

## Codex SSOTs (read before starting)

`/codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md`,
`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`,
`/codex/12-agent-workflow/commit-push-flip-rule.md`.

## Progress Log

- **2026-08-09** — Authored by a round9 `/na-eligibility-audit ao` re-sweep, specifically checking for docs unblocked
  by two credential facts that landed 2026-08-09 (GSM secret creation; 5 Slack webhooks provisioned — the latter does
  not touch this doc). Conflict-check: grepped all active `parent_epic: orchestrator_master` plans plus batch10-13 for
  `ANTHROPIC_AUTH_TOKEN`/`deepseek-v4-pro-api-key` — the only hit outside the source doc itself is
  `operator_action_items_consolidated_2026_08_08.md`, which records the secret as operator-created and explicitly
  points the re-sourcing work back at the source doc ("re-sourcing on both hosts is the next (non-operator) todo
  there") — a status pointer, not a competing dispatch claim. Clear to extract. Noted for the record: a same-day
  `/ag-closeout-audit ao` Phase 1 pass (batch12) had already classified this source doc's whole remainder as
  operator-gated before (or without registering) the secret-creation fact — this batch corrects that stale
  declination for the one item the new fact actually unblocks, leaving the other 4 genuinely-gated items alone.
