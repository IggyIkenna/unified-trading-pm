---
doc_type: codex-ssot
title: Agent Slack read-access — scripts/dev/slack-read-channel.py
summary:
  An agent session can read any Slack channel's recent history directly, right now, with zero setup — no MCP server, no
  OAuth flow, no pasted screenshots. `scripts/dev/slack-read-channel.py` resolves a read-scoped bot token from GCP
  Secret Manager via gcloud ADC (the token never touches disk or argv) and dumps rendered + raw-JSON channel history.
  This doc exists because that capability was previously hard to find — an agent asked "do I have Slack access?"
  reflexively checked for an MCP tool (found none) and concluded no access, instead of checking for an existing
  capability script.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [slack, read-access, agent-capability, observability, monitoring, tooling, discoverability]
related:
  [
    /codex/04-architecture/ci-alerting.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
    /codex/05-infrastructure/agent-orchestrator-slack-notifications.md,
  ]
created: 2026-08-10
authoritative_for: [agent read-access to Slack channels, SLACK_ALERTS_READER_BOT_TOKEN auth pattern]
referenced_by: []
owner:
last_reviewed: 2026-08-10
code_refs: [scripts/dev/slack-read-channel.py]
---

# Agent Slack read-access

**Before concluding "I don't have Slack access" or trying to stand up a Slack MCP server, run
`scripts/dev/slack-read-channel.py` — it already works, on every host.**

## What it does

Downloads a Slack channel's recent history (rendered to stdout + raw JSON dumped to `slack-<channel>-<hours>h.json` in
the CWD) so alert triage ("is something broken?") can be done from a terminal, without the operator pasting anything.

```bash
python3 scripts/dev/slack-read-channel.py [channel=ci-failures] [hours=24] [--json-only]
```

## Auth — why it needs zero setup

The bot token is `SLACK_ALERTS_READER_BOT_TOKEN` in GCP Secret Manager, resolved in-process via
`gcloud secrets versions access latest --secret=SLACK_ALERTS_READER_BOT_TOKEN` — **the token never touches disk or
argv.** Every host this runs on (operator laptop slots, the AO orchestrator VM, any dispatched worker) already has a
gcloud identity configured for the prod project, so this is genuinely fleet-wide with no per-host credential
provisioning step. Degraded-path fallback (every gcloud identity hits `PERMISSION_DENIED` or a stale-token reauth prompt
that can't run non-interactively): supply the token directly via a `SLACK_ALERTS_READER_BOT_TOKEN` env var for that one
invocation — never as a default, never silently.

The bot must be a member of the target channel to read it; `channel not visible to the reader bot` names the channels it
CAN see, which is the fastest way to tell "bot not invited" from "channel name typo."

## Why not a Slack MCP server instead

Was asked for directly (2026-08-09/10). Weighed and deferred, not rejected — revisit if the CLI-script ergonomics
genuinely become the bottleneck:

- This script already satisfies the actual need (read channel history without the operator pasting) with an auth pattern
  that deliberately never persists the token to disk. A generic third-party Slack MCP server would need the token as a
  literal env var in `claude mcp add -e SLACK_BOT_TOKEN=...`, which either breaks that invariant or needs a wrapper
  script reinventing this same gcloud-ADC resolution anyway.
- It requires trusting and installing a third-party MCP package fleet-wide (every slot + the AO VM) for marginal benefit
  over `Bash(python3 scripts/dev/slack-read-channel.py ...)`, which already works today.
- "Every slot + the AO" is exactly what this script already covers via gcloud ADC — no separate rollout needed.

## Why this doc exists (the discoverability gap it closes)

`DOC_INDEX.generated.md` had 20+ docs tagged `slack` before this one — alerting routing, dedup/cooldown contracts,
outbound webhook payload formats, on-call escalation — but none of them said "you can read Slack directly right now."
The script itself was well-documented at the file level (see its own header for the TRAPS learned building it), just not
indexed as a discoverable _capability_. `rg -l '^tags:.*read-access' codex/` (or `^authoritative_for:.*Slack read`) now
lands here directly.

## Related capability scripts in the same family

- `scripts/dev/slack-read-channel.py` — this doc's subject; ad-hoc channel history read.
- Outbound (write) side is a different codepath entirely — see
  `/codex/05-infrastructure/agent-orchestrator-slack-notifications.md` (AO's webhook push) and
  `/codex/04-architecture/ci-alerting.md` (the `notify-slack.yml` CI carrier) — do not confuse the two; this doc is
  read-only.
