---
doc_type: issue
title: "13-repo simultaneous QG cascade — PM-manifest-race single point of failure + silent SLACK_CI_WEBHOOK_URL gap on 9 repos (2026_08_18)"
summary: >-
  Operator noticed the 2026-08-18 14:20 ldr-ci-monitor "13 repo(s) LDR RECOVERED" alert and asked why 13 repos went
  RED near-simultaneously and whether there was "a huge blockage somewhere." Root-caused via /ci-reconcile: every
  repo's quality-gates-v2 "checks" slice runs `unified-trading-pm/codex/scripts/run-all-validators.sh` against a
  cloned PM checkout (validating PM's OWN workspace-manifest.json + plans/active/*.md), making PM's corpus validity
  a single point of failure for the entire fleet's CI. A burst of concurrent automated version-registry-update
  manifest-bump commits (one per sibling repo publishing a new package version) landed on PM's live-defi-rollout
  trunk within the same ~2-minute window, transiently invalidating the manifest; every repo whose CI happened to
  clone PM during that window failed together (confirmed: alerting-service, deployment-api, execution-service,
  market-tick-data-service all failed within 11:07:54-11:09 UTC with the identical
  "Production readiness validators FAILED" signature). Separately, only 4 of 13 repos posted a visible CRITICAL to
  #ci-failures — the other 9 (confirmed on alerting-service, deployment-api) had a stale/invalid
  SLACK_CI_WEBHOOK_URL / SLACK_WEBHOOK_URL secret, so their notify job ran "successfully" (best-effort, never fails
  the build) but silently never posted.
status: open
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm, alerting-service, client-reporting-api, deployment-api, fund-administration-service, greeks-service, market-data-processing-service, ml-service, trading-agent-service]
scope: [engineer, admin]
tags: [ci-reconcile, quality-gates-v2, fleet-wide, single-point-of-failure, slack-webhook, workspace-manifest]
related:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /codex/04-architecture/ci-alerting.md,
  ]
created: "2026-08-18"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
assigned_role: infra
drift_direction: advance-code
source: >-
  /ci-reconcile interactive investigation, 2026-08-18 (this session) — operator asked "was there a huge blockage
  somewhere?" after seeing the 13-repo mass-recovery ldr-ci-monitor alert; root-caused via direct gh run/log
  inspection across 4 repos, confirmed via GSM + gh secret list, fixed both findings live.
resolved_by:
locked_by:
depends_on: []
---

# 13-repo simultaneous QG cascade — root cause + two fixes shipped

## What I found

### Finding 1 — PM corpus validity is a fleet-wide CI single point of failure

Every repo's `quality-gates-v2` "checks" slice runs (via `scripts/quality-gates-base/base-service.sh` /
`base-library.sh`, section `[6/6] PRODUCTION READINESS VALIDATORS`):

```
unified-trading-pm/codex/scripts/run-all-validators.sh --asset-group all --failed-only
```

against a cloned `unified-trading-pm` checkout, validating PM's OWN `workspace-manifest.json` (schema +
topological order) and `plans/active/*.md` (no broken links) — **not anything about the repo whose CI is running**.
Confirmed via direct log inspection on `execution-service` (run 32130228649) and `market-tick-data-service` (run
32130261947): both show the identical failure line

```
❌ Production readiness validators FAILED — fix unified-trading-pm/workspace-manifest.json and plans/active/*.md
```

`alerting-service` (run 32130200241) failed at the same moment (11:07:54Z, within 2 minutes of the other two).
`deployment-api` (run 32130215515) failed at 11:08:05Z. Re-running `python3 scripts/run_validators.py --scope all`
against the CURRENT PM tree passes clean (`workspace-manifest.json valid`, `No broken links`) — confirming this was
transient, not a real ongoing defect.

**Why it went invalid**: in the 11:00-11:10 UTC window, PM's `live-defi-rollout` absorbed a dense burst of automated
`chore(manifest): update <repo> to <version>, bump PM to <version> [skip ci]` commits (one per sibling repo
publishing a new package version — execution-service, market-tick-data-service, deployment-service,
strategy-service, trading-agent-service, instruments-service, client-reporting-api, greeks-service,
features-service, plus unified-api-contracts/unified-trading-library triggering cascading re-bumps), interleaved
with dozens of concurrent interactive-session commits. Consistent with a version-registry-update race transiently
breaking manifest validity (same shape as this skill's documented class (k) — a concurrent-writer race on a shared
JSON manifest) before the next bump commit self-corrected it.

**Why it "recovered together" at 14:20**: not independently fixed — every repo's *next* CI trigger after PM's tree
settled back to valid just happened to pass, which is why 4 repos posted CRITICALs around 11:16 UTC and the rest
cleared on their own next scheduled/triggered run, landing in the same `ldr-ci-monitor` batch.

### Finding 2 — silent Slack notification gap on (at least) 9 repos

Checked the actual `Slack CRITICAL — QG Slice Failed / send-notification` job logs for `alerting-service` and
`deployment-api`. Both show the dedup gate correctly decided `should_post=true` (first transition in-window), but
the final line in both is:

```
SLACK_WEBHOOK_URL is not an https URL (unset/masked/misconfigured) — skipping (notify is best-effort)
```

Both repos already had `SLACK_CI_WEBHOOK_URL` and `SLACK_WEBHOOK_URL` defined as secret NAMES (confirmed via
`gh secret list`) — the fallback chain (`secrets.SLACK_CI_WEBHOOK_URL || secrets.SLACK_WEBHOOK_URL`, per
`unified-trading-ci/.github/workflows/notify-slack.yml`) still resolved to something failing the `https://*` check,
meaning the stored VALUE was stale/invalid on these repos specifically (secret values are never readable via the
API, only existence). `gh secret list` showed all 13 repos have both secret names defined, so this can't be
diagnosed by presence alone — only by each repo's own notify-job log output.

## Fixes shipped

1. **Validator retry hardening** (`unified-trading-pm@176ff63dab`, `scripts/quality-gates-base/base-service.sh` +
   `base-library.sh`): on a `run-all-validators.sh --asset-group all --failed-only` failure, re-pull PM
   (`git -C unified-trading-pm pull --ff-only origin live-defi-rollout`), wait 5s, retry once before failing the
   repo's own gate. Absorbs a transient PM-manifest race without weakening detection of a genuinely, persistently
   broken PM corpus (a real break still fails after the re-pull + retry). Fixed in the shared base script both
   service- and library-type repos source, so this is a one-shot fleet-wide fix — verified via `bash -n` syntax
   check on both files plus a full local `quality-gates.sh --no-fix` PASS on PM itself.
2. **Slack webhook secret repropagation** (`gh secret set`, not a code change): pulled the known-good webhook from
   GSM (`cloud-monitoring-slack-ci-failures-webhook`, a genuine `https://hooks.slack.com/services/...` URL, created
   2026-08-07) and re-set both `SLACK_CI_WEBHOOK_URL` and `SLACK_WEBHOOK_URL` on the 9 repos that recovered silently
   in the 14:20 batch without ever posting a visible CRITICAL: `alerting-service`, `client-reporting-api`,
   `deployment-api`, `fund-administration-service`, `greeks-service`, `market-data-processing-service`,
   `ml-service`, `trading-agent-service`, `unified-trading-pm`. Directly confirmed-broken via log inspection:
   `alerting-service`, `deployment-api`; the other 7 were fixed proactively (same idempotent re-propagation, not
   individually log-confirmed this session — **not yet independently verified as having actually been broken**, see
   Todos).

## Why it matters

PM's corpus validity gating the ENTIRE fleet's CI, combined with the concurrency this workspace already runs at
(many parallel human sessions + automated version-bump jobs landing on the same trunk), means this exact cascade
will recur on any future manifest-write race unless retried — the fix directly addresses that. The silent-webhook
gap is separately serious: any repo missing a valid webhook can go RED for an arbitrary duration with ZERO visible
signal in `#ci-failures`, discoverable only by directly reading `gh run list` — exactly the failure mode `/ci-reconcile`
exists to catch, but only when someone thinks to run it.

## Todos

- [ ] [SCRIPT] P2. Independently confirm (via each repo's own notify-job log, same method used for alerting-service/
      deployment-api) that the other 7 repos whose webhook secret was proactively re-set this session
      (client-reporting-api, fund-administration-service, greeks-service, market-data-processing-service,
      ml-service, trading-agent-service, unified-trading-pm) were actually broken before the fix — or confirm the
      re-propagation was a no-op/idempotent correction on an already-working secret. (repo: unified-trading-pm)
- [ ] [SCRIPT] P2. Audit the remaining ~12 repos in the fleet NOT covered by this incident's 13-repo list (e.g.
      instruments-service, features-service, ibkr-gateway-infra, unified-api-contracts, unified-trading-library,
      unified-trading-api, system-integration-tests, e2e-testing, agent-orchestrator,
      unified-trading-system-ui, deployment-ui, batch-live-reconciliation-service) for the same
      SLACK_CI_WEBHOOK_URL/SLACK_WEBHOOK_URL validity gap — this session only checked/fixed the 13 that happened to
      be visible in this specific incident. (repo: unified-trading-pm)
- [ ] [SCRIPT] P3. Consider whether `run-all-validators.sh --asset-group all --failed-only`'s underlying
      `validate_workspace_manifest.py` topological check should also get retry/backoff at ITS OWN invocation site
      (PM's own CI, and the `version-registry-update.yml` bump-commit workflow itself) rather than only downstream
      at the consumer side — the retry shipped here treats the symptom in every consumer; hardening the
      version-registry-update race at its source (atomic manifest writes, or a lock) would prevent the transient
      invalidity from ever existing on PM's trunk in the first place. Scope this as its own investigation, not a
      quick follow-on — touches the automated version-bump pipeline every repo publish goes through.
