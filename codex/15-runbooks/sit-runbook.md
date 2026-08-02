---
doc_type: codex-runbook
title: SIT (System Integration Tests) Runbook
summary:
  SIT (System Integration Tests) operational runbook — staging force-unlock via the sit-unlock dispatch, manual SIT
  trigger, the (NOT-IMPLEMENTED) starvation detector spec, the common-failure-mode table, and the SIT staging-lock
  lifecycle. Re-verified 2026-07-31 — several named workflows do not exist and staging is dormant; see the banner.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [system-integration-tests, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: [sit, runbook, ci, staging, quality-gates, escalation]
related: [/codex/08-workflows/ci-cd-flow.md, /codex/06-coding-standards/integration-testing-layers.md]
created: 2026-03-27
authoritative_for: [SIT staging force-unlock procedure, SIT staging-lock lifecycle + starvation detector]
referenced_by:
owner: workspace-platform (CI maintainers)
last_reviewed: 2026-09-25
code_refs:
execution:
  {
    owner: workspace-platform (CI maintainers),
    cadence: ad-hoc — when SIT is stuck or staging is locked,
    verifier:
      gh workflow run sit-unlock.yml --repo IggyIkenna/unified-trading-pm + verify staging-lock GCS blob removed,
    last_executed: 2026-07-31 (static re-verification of named workflows; force-unlock not exercised),
  }
cadence: ad-hoc — when SIT is stuck or staging is locked
verifier: gh workflow run sit-unlock.yml --repo IggyIkenna/unified-trading-pm + verify staging-lock GCS blob removed
last_executed: 2026-07-31 (static re-verification of named workflows; force-unlock not exercised)
---

# SIT (System Integration Tests) Runbook

> **⚠️ Re-review 2026-07-31 — read this before following any procedure below.** Three of this runbook's named artifacts
> do not exist, and its default promotion assumption is obsolete:
>
> | This runbook says                         | Verified reality (2026-07-31)                                                     |
> | ----------------------------------------- | --------------------------------------------------------------------------------- |
> | `sit-starvation-detector.yml`             | **Does not exist.** No such workflow in `unified-trading-pm/.github/workflows/`.   |
> | `system-integration-tests.yml` (SIT repo) | **Does not exist.** The SIT workflow is `full-workspace-sit.yml`.                  |
> | "Telegram alert"                          | Alerts route to **Slack** via `notify-slack.yml`. `telegram_*` names survive only  |
> |                                           | as output-variable names "kept for compat" (see `cold-storage-cleanup.yml:236`).   |
> | Staging is the promotion path             | **Staging is DORMANT.** Default promote is LDR→`main` direct (`promotion_model:    |
> |                                           | ldr_main`). Staging is reversible-on-demand, not the steady state.                 |
>
> The closest live equivalent to the described starvation detector is `glue-pool-starvation-monitor.yml`, but it is a
> **different check** — it pages on glue-job queue depth while the runner pool is idle, not on a stale
> `staging_status.locked_since`. Nothing currently watches staging-lock age. The live SIT signal that actually gates
> LDR→main is the `sit-gate/fleet-green` required check emitted by `sit-gate.yml`.
>
> Sections below are kept because the force-unlock mechanics and the failure-mode table are still useful when staging is
> deliberately re-enabled, but treat every workflow filename as suspect until re-verified.

## Force-Unlock Staging

If staging is locked and SIT is stuck or failed, force-unlock via repository dispatch:

```bash
gh api repos/IggyIkenna/unified-trading-pm/dispatches \
  -X POST \
  -f event_type="sit-unlock"
```

Or manually edit `workspace-manifest.json` in unified-trading-pm:

```json
"staging_status": {
  "locked": false,
  "locked_since": null,
  "locked_reason": null,
  "lock_version": null
}
```

Then commit **without** any CI-skip marker.

> **HARD RULE — do NOT use the literal CI-skip marker here.** Writing it (even in a commit *body*, even when only
> describing it) makes the required `quality-gates-v2` check go MISSING, which permanently BLOCKS the promotion PR.
> Always spell it `skip-ci` in prose. Recovery if it happens:
> `gh workflow run quality-gates-v2.yml --ref <branch>`. SSOT: `/codex/08-workflows/ci-cd-flow.md`.

## Manual SIT Trigger

```bash
gh workflow run full-workspace-sit.yml \
  --repo IggyIkenna/system-integration-tests \
  --ref main
```

Or via dispatch:

```bash
gh api repos/IggyIkenna/system-integration-tests/dispatches \
  -X POST \
  -f event_type="staging-changed" \
  -f client_payload='{"reason": "manual-trigger"}'
```

## Starvation Detector

> **This workflow does not exist (verified 2026-07-31).** Kept as the specification of a check we no longer have —
> nothing currently watches staging-lock age. `glue-pool-starvation-monitor.yml` is a different check (glue-job queue
> depth vs idle pool). If staging is re-enabled, this detector has to be rebuilt.

The starvation detector was specified as a scheduled workflow that checks if staging has been locked longer than a
configured threshold (default: 2 hours), running every 30 minutes and:

1. Reads `staging_status.locked_since` from `workspace-manifest.json`
2. Computes elapsed time since lock acquisition
3. If elapsed > threshold: sends a Slack alert (via `notify-slack.yml`) and optionally dispatches `sit-unlock`

When it fires, it means SIT either failed silently, hung, or was never triggered after a staging lock. Check the
system-integration-tests workflow logs first.

## Common Failure Modes

| Failure Mode              | Symptoms                                        | Fix                                                                                                                  |
| ------------------------- | ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **OOM**                   | SIT runner killed, exit code 137                | Increase runner memory or split test suite into shards                                                               |
| **Quota exceeded**        | GH API 403 / rate limit errors                  | Wait for quota reset (1h); reduce parallel dispatches                                                                |
| **Network timeout**       | Emulator connection refused / curl timeouts     | Check emulator health; restart docker-compose stack                                                                  |
| **Staging lock stuck**    | `staging_status.locked = true` for >2h          | Force-unlock (see above); check SIT logs for root cause                                                              |
| **SHA pinning violation** | staging-to-main aborts with "untested commits"  | New commits landed in staging after SIT ran; SIT auto-re-triggers                                                    |
| **Merge conflict**        | staging-to-main reports "dirty" mergeable state | Resolve conflict on the repo's staging branch; re-run promotion                                                      |
| **Manifest corruption**   | JSON parse errors on workspace-manifest.json    | `git log -1 workspace-manifest.json` to find last good state; `git checkout <sha> -- workspace-manifest.json`        |
| **Emulator port clash**   | Address already in use on 8085/4443/9050        | Kill orphan emulator processes; check for zombie docker containers                                                   |
| **Cassette drift**        | Schema parity tests fail in UAC                 | Re-record via the repo gate, never bare pytest: `cd unified-api-contracts && bash scripts/quality-gates.sh`          |

## Recovery Workflow

```
1. Check GHA run logs → identify failure category from table above
2. If staging lock stuck → force-unlock (dispatch sit-unlock)
3. If emulator failure → restart docker-compose; re-trigger SIT
4. If schema drift → re-record cassettes in UAC; commit; re-trigger SIT
5. If OOM/quota → wait + retry, or increase resources
```

## Escalation Path

1. **Automated**: Slack alert fires (`overnight-dead-man-switch.yml`; the starvation detector no longer exists)
2. **L1 -- Self-service**: Check this runbook; try force-unlock + manual SIT trigger
3. **L2 -- Investigation**: Check GHA run logs at `github.com/IggyIkenna/system-integration-tests/actions`; check
   emulator logs
4. **L3 -- Owner escalation**: If the problem is in cascade logic (update-repo-version, staging-to-main), escalate to PM
   repo owner
5. **Emergency**: If staging is blocking a hotfix, use `staging-to-main` workflow_dispatch with `start_from_repo` to
   resume partial promotion, or manually merge the hotfix repo's staging->main PR

## SIT Lock Lifecycle

```
Version bump committed to staging
  → sit-debounce-trigger.yml fires
  → staging_status.locked = true (with timestamp)
  → system-integration-tests.yml runs
  → On PASS: staging-to-main promotes; lock released
  → On FAIL: Slack alert; lock stays (NOTE: no detector currently watches it)
  → On timeout (>2h): would be force-unlocked by the starvation detector — NOT IMPLEMENTED today
```
