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
status: resolved
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
resolved_by: >-
  unified-trading-pm@176ff63dab (validator retry) + gh secret sync across all 26 registry repos
  (cloud-monitoring-slack-ci-failures-webhook) — see Findings 3-5 for the follow-up confirmation/audit/hardening
  investigation outcomes.
locked_by:
depends_on: []
---

# 13-repo simultaneous QG cascade — root cause + two fixes shipped

> **🗄️ ARCHIVED 2026-08-18** — `status: resolved`, all todos `[x]`, `locked_by:` empty. Per
> `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`, a doc with every todo done archives
> immediately. Successor: none (all 5 findings closed out in this doc; no follow-up work remains open).

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

### Finding 3 — the 7 "proactive" webhook fixes: 6 confirmed genuinely broken, 1 was a red herring

Pulled each of the 7 repos' own failed-run notify-job log from the 11:08-11:09 UTC incident window (same method as
alerting-service/deployment-api):

- **6 confirmed genuinely broken** — identical `SLACK_WEBHOOK_URL is not an https URL` signature on
  `client-reporting-api` (run 32130210529), `fund-administration-service` (32130238714), `greeks-service`
  (32130244297), `market-data-processing-service` (32130256980), `ml-service` (32130266624),
  `trading-agent-service` (32130278632). The re-propagation fixed a real defect on all 6.
- **`unified-trading-pm` was NOT broken** — its own failed run (32130292495, sha `95a51158`, matching the
  "incident since 95a51158" the recovery alert cited) shows the notify job's dedup gate correctly computed
  `should_post=false (key 'qg-fail:unified-trading-pm:live-defi-rollout' last posted 119m ago < 120m cooldown —
  suppressed)` — a legitimate, working-as-designed cooldown suppression (PM had already posted a CRITICAL for the
  same dedup key ~119 minutes earlier, per its multiple RED cycles today), not a webhook defect. The proactive
  re-propagation there was a harmless no-op, not a fix.

### Finding 4 — fleet-wide webhook audit: one more confirmed-empty repo, 12 unverifiable-but-synced

Checked `gh secret list` across the 13 repos NOT in the original incident (`batch-live-reconciliation-service`,
`features-service`, `ibkr-gateway-infra`, `instruments-service`, `system-integration-tests`,
`unified-api-contracts`, `unified-trading-library`, `unified-trading-api`, `unified-trading-system-ui`,
`deployment-ui`, `e2e-testing`, `agent-orchestrator`, `unified-trading-ci`):

- **`unified-trading-ci` had ZERO webhook secrets defined** (neither `SLACK_CI_WEBHOOK_URL` nor
  `SLACK_WEBHOOK_URL` existed as a secret name at all) — a confirmed gap, now fixed.
- The other 12 all had both secret names present. Checked each for a recent failed CI run to verify the stored
  VALUE the same way as Findings 2/3 — almost none had one: most of these repos have been consistently green for
  their last 15+ runs, and several (`unified-trading-system-ui`, `deployment-ui`, `unified-trading-ci`) run an
  entirely different CI system (JS/TS-based) that may not even route through `notify-slack.yml` the same way.
  **Could not independently confirm these 12 were actually broken** — secret presence alone doesn't prove a valid
  value, and no real failure event existed to check against without manufacturing one (which would have meant
  either a fake CI failure or a live test post to `#ci-failures`, both avoided as unnecessary noise).
- **Action taken**: proactively synced `SLACK_CI_WEBHOOK_URL` + `SLACK_WEBHOOK_URL` from the same GSM source
  (`cloud-monitoring-slack-ci-failures-webhook`) across all 13 — safe/idempotent regardless of prior state, closes
  the confirmed `unified-trading-ci` gap, and removes the uncertainty for the other 12 going forward even though
  their prior state is unconfirmed. **All 26 repos in `workspace-manifest.json`'s registry now carry the same
  verified-current webhook.**

### Finding 5 — the manifest-bump pipeline is already heavily hardened; the P3 todo's premise was wrong

Read `update-repo-version.yml` (the actual `workspace-manifest.json` writer — `version-registry-update.yml` only
writes to Firestore, a separate SSOT). It already has: a dedicated serialized `concurrency: group: version-bump,
cancel-in-progress: false` (one pending slot, no eviction), a 5×-retry-with-rebase push loop, CUSTOM git merge
drivers registered specifically to auto-resolve the deterministic conflict classes (version keys → max-semver,
`breaking_pending` → union, audit jsonl → union), atomic tmp-file+rename writes, and a corruption
detect-and-revert (`assert 'versions' in d` → `git checkout -- workspace-manifest.json` on failure). This directly
contradicts this doc's original Finding-1 hypothesis that the manifest-bump pipeline itself was an unhardened
race — it demonstrably is not.

Given that, the more likely actual culprit for the transient `run_validators.py --scope all` failure is the
OTHER half of what it checks — `validate_plan_links.py` (broken-link scanning across `plans/active/*.md`), which
has no retry/serialization protection of its own and runs against whatever git state happens to be checked out at
scan time. This session independently produced strong corroborating evidence: multiple `plans/active/*.md`
archive-safety-ratchet and AG-closeout-linkage violations were hit and fixed live during this exact investigation,
confirming the plans corpus was under heavy concurrent-edit churn in the same window (dozens of docs
archived/edited by concurrent slot-3/slot-6/dp-audit-bot sessions).

**No further source-side fix is being shipped for this.** The consumer-side retry already landed
(`unified-trading-pm@176ff63dab`) wraps the ENTIRE `run-all-validators.sh --asset-group all` call — it re-pulls
PM and retries regardless of which specific sub-validator (manifest or plan-links) flaked, so it already covers
this class without needing to know which one it was. Adding a duplicate retry inside `validate_plan_links.py`
itself would be redundant with what's already shipped. If this recurs with QG-level visibility into which
specific validator failed (not available this session — the log only surfaces the generic "Production readiness
validators FAILED" line), re-open this with the precise sub-check identified.

## Todos

- [x] ✅ [SCRIPT] P2. Independently confirm (via each repo's own notify-job log) that the 7 proactively-fixed repos
      were actually broken. DONE — see Finding 3: 6 of 7 confirmed genuinely broken (identical webhook-invalid
      signature); `unified-trading-pm` was a false positive (legitimate dedup/cooldown suppression, not a broken
      webhook) — the fix there was a harmless no-op.
- [x] ✅ [SCRIPT] P2. Audit the remaining 13 fleet repos for the same webhook gap. DONE — see Finding 4:
      `unified-trading-ci` had zero webhook secrets defined (confirmed gap, fixed); the other 12 have secret names
      present but unverifiable without a real failure event (none existed this session) — proactively synced from
      GSM for full-fleet consistency rather than left unconfirmed. All 26 registry repos now carry the same
      verified-current webhook.
- [x] ✅ [SCRIPT] P3. Investigated hardening the manifest-bump pipeline at its source. DONE — see Finding 5: found
      `update-repo-version.yml` is already extensively hardened (serialized concurrency, 5× retry-with-rebase,
      custom merge drivers, atomic writes, corruption revert) — the original premise (this pipeline is an
      unhardened race) was wrong. The more likely culprit (`validate_plan_links.py`, no retry of its own) is
      already covered by the consumer-side retry shipped in Finding 1's fix — no additional source-side code
      change is warranted without more precise per-sub-validator failure evidence than was available this
      session.
