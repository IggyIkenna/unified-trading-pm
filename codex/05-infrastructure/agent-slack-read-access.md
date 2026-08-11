---
doc_type: codex-ssot
title: Agent Slack read-access — scripts/dev/slack-read-channel.py
summary:
  An agent session on a GCP-hosted host (operator laptop slot, dispatched worker) can read any Slack channel's recent
  history directly, right now, with zero setup — no MCP server, no OAuth flow, no pasted screenshots.
  `scripts/dev/slack-read-channel.py` resolves a read-scoped bot token from GCP Secret Manager, pinned to the
  `unified-trading-sa` service-account identity rather than ambient ADC (the token never touches disk or argv) and dumps
  rendered + raw-JSON channel history. **This now includes the AO orchestrator VM** — AO workers run as the `ubuntu`
  user, whose active gcloud identity (`unified-trading-sa`) already holds `secretmanager.secretAccessor` and was
  live-verified working 2026-08-11 — **and the operator's laptop**, via a dedicated SA key activated 2026-08-11
  specifically to bypass the org's human-reauth policy (see the Auth section for both; a 2026-08-10 claim that AO was
  closed off was a wrong-OS-user false negative, corrected in place).
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
last_reviewed: 2026-08-11
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

## Auth — pinned to `unified-trading-sa`, not ambient ADC (hardened 2026-08-11)

The bot token is `SLACK_ALERTS_READER_BOT_TOKEN` in GCP Secret Manager. The script resolves it in-process — **the token
never touches disk or argv** — by trying, in order: (1)
`gcloud secrets versions access latest --secret=SLACK_ALERTS_READER_BOT_TOKEN --account=unified-trading-sa@<active-gcloud-project>.iam.gserviceaccount.com`,
(2) the same call with no `--account` (whatever's ambient), (3) a `SLACK_ALERTS_READER_BOT_TOKEN` env var. **This was
originally "just resolve via ambient gcloud ADC, whichever account happens to be active" — deliberately changed** after
the finding below: relying on "whichever account is active" is a real footgun on a multi-account host (the AO VM's
`ubuntu` user carries 5+ configured accounts across per-slot gcloud configs; any interactive session on that same OS
user running `gcloud config set account`/`gcloud auth login` would silently change what a _different_, unrelated
scheduled job authenticates as). Pinning to the specific SA removes that class of failure entirely.

`unified-trading-sa@central-element-323112.iam.gserviceaccount.com` already holds
`secretmanager.secretAccessor`/`.viewer` (see `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`)
and is a **real, directly-authenticated local credential** (not merely impersonated) on:

- **The AO orchestrator VM** — `ubuntu`'s own ADC already resolves to this SA (how AO always worked; a 2026-08-10 claim
  that AO had zero GCP credential was a wrong-OS-user false negative — that check ran as `root` via SSM's default shell,
  and root's own gcloud config on that box genuinely has no active account, but that answers the wrong question.
  Confirmed live 2026-08-11: `ps -eo user,cmd | grep tmux` shows every `orch-slot-N` tmux session runs as `ubuntu`;
  `sudo -u ubuntu gcloud auth list` shows `unified-trading-sa@central-element-323112.iam.gserviceaccount.com` marked `*`
  active, ADC file is `service_account` type, not a user OAuth token;
  `sudo -u ubuntu gcloud secrets versions access latest --secret=SLACK_ALERTS_READER_BOT_TOKEN` succeeded and returned a
  real token. Lesson: on a multi-user host, "I checked gcloud state" must name which OS user it checked, or it silently
  answers for whichever user the shell happened to default to. `/data-pipeline-alerts-reconcile` and any other skill
  previously marked "interactive-session-only for this reason" can be re-scoped to AO — re-verify the specific skill's
  own gate before flipping it, this correction only covers the underlying credential, not every consumer).
- **The operator's laptop** — a dedicated key was generated 2026-08-11 specifically to close the gap where the
  operator's personal `ikenna@odum-research.com` session hits an org-enforced reauth wall
  (`Reauthentication failed: cannot prompt during non-interactive execution`) that blocks any non-interactive
  `gcloud secrets` call even right after a fresh interactive login — a service-account credential has no such human
  reauth requirement (service-account impersonation was tried first and confirmed insufficient: it still needs the
  human's own base session to mint the impersonated token, so it hits the identical reauth wall). The key lives at
  `~/.config/gcloud/keys/unified-trading-sa.json` (mode 600), activated via
  `gcloud auth activate-service-account --key-file=...` (this ADDS the account, it does not change the laptop's default
  — `ikenna@odum-research.com` stays the active/default identity for everything else; only this script's explicit
  `--account=` pin uses the SA). **Key was hand-carried off the AO VM via one-time hybrid RSA/AES encryption over the
  SSM command channel** (a local ephemeral RSA keypair encrypts the AES key, which encrypts the SA-key JSON; only the
  base64 ciphertext ever appears in SSM's command-invocation log — never the plaintext key), then the VM-side plaintext
  was shredded via a `trap ... EXIT` in the generating script so a mid-run failure can't leave a leftover (a first
  attempt DID leave one, cleaned up manually — lesson: always wrap a remote secret-generation script in a cleanup trap,
  not a linear success-path-only cleanup step at the end). Generating the key also needed granting `unified-trading-sa`
  itself `roles/iam.serviceAccountKeyAdmin` on its own resource first — it already held `serviceAccountAdmin` (per the
  self-service doc) but that role does not include key-creation rights. Provisioning a NEW key for a different host is a
  real security decision (this SA holds broad project-admin roles — see the self-service doc) — don't self-serve another
  one without the same explicit tradeoff conversation; ask the operator first, same as this one was asked. Rotate/revoke
  via `gcloud iam service-accounts keys list/delete --iam-account=unified-trading-sa@...` if the laptop is ever
  compromised.

Degraded-path fallback (every gcloud path fails — no gcloud binary, `PERMISSION_DENIED`, or the pinned account isn't
locally activated on this host yet): supply the token directly via a `SLACK_ALERTS_READER_BOT_TOKEN` env var for that
one invocation — never as a default, never silently.

<details><summary>Superseded 2026-08-10 entry (kept for provenance, do not trust — see above)</summary>

Correction (2026-08-10, direct verification via AWS SSM on `i-0c9b283b31d6b5ca7`): the AO orchestrator VM does **NOT**
have this today — it's an AWS EC2 instance, not GCP-hosted, and cross-cloud GCP access was never provisioned on it.
Verified live: `gcloud auth list` → "No credentialed accounts", `GOOGLE_APPLICATION_CREDENTIALS` unset, no
service-account key file present. This isn't a missing IAM binding (which would be a quick grant) — there is currently
NO GCP identity on that VM to grant a binding to. Setting this up properly means standing up real cross-cloud auth
(Workload Identity Federation is the right pattern here, not deploying a static SA key JSON to a production orchestrator
VM) — tracked as its own scoped follow-up, not a quick fix. Until that lands, AO cannot run this script or any
skill/task that depends on it. **This was wrong** — see the correction above.

</details>

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
