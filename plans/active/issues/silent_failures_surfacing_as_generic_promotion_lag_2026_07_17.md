---
doc_type: issue
title:
  Three unrelated hard failures all surfaced as the same vague "PROMOTION LAG > 60m" warning — the lag alert reports a
  symptom, never a cause
summary: |
  On 2026-07-16/17, three completely different faults — a 16h self-hosted runner-pool collapse (missing Secret Manager
  IAM grant, swallowed by `|| true`), a deliberate provenance-gate refusal, and an unsatisfiable SIT-leaf deadlock —
  ALL surfaced in Slack as the identical `PROMOTION LAG > 60m ... un-propagated` WARNING. Nothing named a cause, so
  each was mis-triaged: the provenance block was read as "the bot forgot to arm auto-merge" (the gate was then
  overridden, promoting 33 bypassed commits), and the runner collapse was read as "normal SIT latency" (it had been
  dead 16h). The lag monitor is a SYMPTOM detector being used as the fleet's only promotion alarm. Root fixes for all
  three are shipped; this doc tracks the systemic gap — a failure should page for its own cause, not leak out as lag.
status: open
resolved_by:
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, alerting, observability, promotion, self-hosted-runners, silent-failure, triage]
related:
  [
    /plans/archive/issues/provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md,
    /codex/04-architecture/ci-alerting.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-07-17
author: unknown
last_updated: 2026-07-17
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 0.8
assigned_role: devops_engineer
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /codex/04-architecture/ci-alerting.md,
    /codex/08-workflows/ci-cd-flow.md,
    /plans/archive/issues/provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md,
    scripts/self-hosted-runners/glue-runner-run.sh,
    scripts/quality_gates/check_no_swallowed_credential_fetch.py,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
  ]
supersedes:
superseded_by:
depends_on:
source:
  - operator 2026-07-17 — "file issue then fix to fail loudly and force full pipeline to unblock now so that next time
    we get zero alerts"
  - measured during the 2026-07-16/17 ci-failures triage session
---

# One alert, three causes: promotion lag is a symptom detector

> **The pattern**: every promotion-side failure, whatever its cause, exits through the SAME door — a `branch-health`
> WARNING saying N branch-pairs are "un-propagated". The alert states the symptom (content hasn't moved) and never the
> cause. All three causes below produced a byte-identical alert shape, and two of the three were mis-triaged BECAUSE of
> it — one of those mis-triages caused real damage.

## The three faults that looked identical

| #   | Real cause                                                                                                      | What Slack said                 | How it was mis-read                                                        |
| --- | --------------------------------------------------------------------------------------------------------------- | ------------------------------- | -------------------------------------------------------------------------- |
| 1   | **Runner pool dead 16h** — `GH_TOKEN_SECRET` migration shipped without the IAM grant; `\|\| true` ate the error | `PROMOTION LAG > 60m` (WARNING) | "normal SIT latency, working as designed" — it was a total pool collapse   |
| 2   | **Provenance gate refusing** — 33 non-quickmerge commits, auto-merge deliberately NOT armed                     | `PROMOTION LAG > 60m` (WARNING) | "the bot forgot to arm auto-merge" → gate overridden, 33 commits laundered |
| 3   | **SIT-leaf deadlock** — `system-integration-tests` had `promotion_model` unset; never dispatched at all         | `PROMOTION LAG > 60m` (WARNING) | "+1 more" noise for ~4 days                                                |

Fault 1 is the sharpest: **4,159 crash-loops in a 2h window, 0 runners listening, ~37 workflows stranded — and not one
alert fired.** The only signal was a lag WARNING that reads exactly like a slow-but-healthy pipeline. A CRITICAL
infrastructure outage was invisible for 16 hours because its symptom shares a channel with routine latency.

## Root cause of the invisibility

**Silent-failure idiom.** `scripts/self-hosted-runners/glue-runner-run.sh` did:

```bash
GH_TOKEN="$(gcloud secrets versions access latest --secret="${GH_TOKEN_SECRET}" \
  ${GCP_PROJECT:+--project="${GCP_PROJECT}"} 2>/dev/null || true)"
: "${GH_TOKEN:?GH_TOKEN ... must be set via EnvironmentFile or GH_TOKEN_SECRET}"
```

`2>/dev/null || true` discards the exit code AND the reason. The real error
(`PERMISSION_DENIED: secretmanager.versions.access`) never reached the journal; operators saw only the generic "must be
set via EnvironmentFile" — which describes a _config_ problem and points away from the actual _IAM_ problem.

**Structural gap.** No detector owns "a self-hosted pool stopped accepting jobs". `promotion_lag_monitor.py` is
explicitly scoped as the SSOT for branch-pair PROPAGATION lag only — it is not, and should not be, an infra monitor. But
it is currently the only thing that fires, so it absorbs every cause by accident.

## Fixed already (do not re-file)

- **Fault 1 root** — IAM grant added (operator) + `GCP_PROJECT` pinned in `/etc/github-glue-runner.env`; pool restored,
  5/5 runners `Listening for Jobs`, 0 token crashes (was 4,159/2h), queue drained 14 → 4.
- **Fault 1 silence** — ⚠️ **ATTEMPTED AND REVERTED — still open, see the P0 below.**
- **Fault 2** — provenance block now carries a stable marker and the lag monitor reports
  `⛔ BLOCKED by the provenance gate — re-ship via quickmerge. Do NOT hand-arm auto-merge`.
- **Fault 3** — `system-integration-tests` opted into `ldr_main` (fail-OPEN SIT-leaf path, same as `e2e-testing`).

## Still open — the systemic gap

- [ ] [DEVOPS] P0. **Re-do the `|| true` fix — the first attempt BROKE PROD and was rolled back (2026-07-17).** The
      replacement block (loud gcloud error + redaction + empty-secret case) passed `bash -n` and passed three
      simulated-failure unit tests, but on the live runner it died with
      `glue-runner-run.sh: line 200: GH_TOKEN: unbound variable` — the JIT `generate-jitconfig` curl at ~L195, under the
      script's `set -euo pipefail`. All 5 runners crash-looped again (~34 restarts) until rollback; service was restored
      from `${DST}.bak-2026-07-17` within minutes and the repo copy reverted so the SSOT matches the VM. The broken
      candidate is kept at `/tmp/glue-runner-run.sh.broken-keepme` on the VM for post-mortem.

      **ROOT CAUSE FOUND (post-mortem, same day) — it was an APOSTROPHE, and the fix is one character.** The block's
              error text contained `${GCP_PROJECT:-<unset — no --project passed; relying on gcloud's ambient default>}`.
              Inside a `${VAR:-word}` expansion bash **re-parses quotes in the default word**, so the `'` in `gcloud's` opened
              a single-quoted region. In a ~200-line script full of apostrophes it silently **re-paired with a later one** —
              quotes balanced overall, so `bash -n` saw VALID syntax — while everything between them became a quoted STRING
              instead of code, swallowing the `GH_TOKEN="${_sm_out}"` assignment. Hence `line 200: GH_TOKEN: unbound variable`
              at the `generate-jitconfig` curl ~120 lines below the edited block. Verified in isolation: the same construct
              alone fails `bash -n` with ``unexpected EOF while looking for matching `'``.
              **Rule to carry forward: never put an apostrophe (or any unbalanced quote) inside a `${VAR:-...}` default word.**
              Write "gcloud" not "gcloud's", or build the message outside the expansion.

              **Why my tests missed it**: they exercised ONLY the changed block, in a SHORT file with no later apostrophe to
              re-pair against — so the toy either errored honestly or passed, and could never reproduce the swallow. `bash -n`
              validates syntax, not binding, and the syntax was genuinely valid. **Still do not retry without whole-script
              validation**: add a `--selfcheck` mode that runs everything short of exec'ing `Runner.Listener`, exercise it on a
              scratch slot, then roll ONE unit and confirm `Listening for Jobs` before the other four. (The canary was
              worthless last time because the same bad script had already been rolled to all five.)

- [x] ✅ [DEVOPS] P1. **A self-hosted pool with 0 runners listening must page on its OWN cause.** Nothing watches runner
      liveness. Cheapest honest signal: alert when a `glue`-labelled job has been `queued` > N minutes while
      `in_progress == 0` — that is unambiguous and needs no VM access. (The `glue-writer` pool stayed healthy
      throughout, so a naive "is the host up" check would have said GREEN.) **DONE (na-eligibility-audit 2026-08-03)** —
      closed via `plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md:213`: `unified-trading-pm@80f397278`, new
      `.github/workflows/glue-pool-starvation-monitor.yml` (cron `*/15`) +
      `scripts/cicd/glue_pool_starvation_monitor.py` routed through `notify-slack.yml`, 16/16 tests proving the
      synthetic starved-queue case fires and a healthy pool does not.
- [x] ✅ [DEVOPS] P1. **Ban the `|| true` credential idiom.** — unified-trading-pm. Delivered
      `scripts/quality_gates/check_no_swallowed_credential_fetch.py` (standalone, deliberately NOT wired into
      `scripts/quality-gates.sh` — that wiring is the gated finalize-plan todo) + a shrinking-ratchet baseline
      (`no_swallowed_credential_fetch_baseline.yaml`) + `tests/unit/test_check_no_swallowed_credential_fetch.py` (22
      cases: positive/negative/baseline-ratchet/synthetic-new-hit). `glue-runner-run.sh` was NOT edited — it is already
      fixed on the live idiom (see the comment at its L64-66) and is operator-gated per the P0 above; the checker only
      greps, it never mutates.

      **Today's hits (2026-07-26, seeded baseline, 18 total across 3 repos)**:
              - `agent-orchestrator` (2): `scripts/fleet-git-health-guard.sh:101`, `scripts/fleet-git-health-guard.sh:105`
              - `deployment-service` (5): `scripts/signal-broadcast-live-smoke.sh:69`,
              `scripts/aws/replicate-secrets-to-aws.sh:158`, `scripts/vm/launch-api-football-backfill-vm.sh:325`,
              `scripts/vm/relaunch_staged_2026_05_29.sh:70`, `scripts/vm/launch-cefi-sharded-backfill.sh:188`
              - `unified-trading-pm` (11): `scripts/verify-slot-host-symmetry.sh:337`, `scripts/verify-slot-host-symmetry.sh:490`,
              `scripts/repo-management/run-audit-reflog-with-alert.sh:125`, `scripts/self-hosted-runners/setup-glue-runners.sh:86`,
              `scripts/self-hosted-runners/setup-glue-runners.sh:89`, `scripts/workspace/load-gh-token.sh:68`,
              `scripts/workspace/load-gh-token.sh:72`, `scripts/workspace/generate-act-secrets.sh:32`,
              `scripts/workspace/generate-act-secrets.sh:35`, `scripts/orchestrator/enable_slack_alerts.sh:59`,
              `scripts/orchestrator/enable_slack_alerts.sh:60`

              Fixing these 18 sites (surface the real error instead of `|| true`) is separate follow-up work, out of this
              todo's scope (delivering the checker + baseline); ratchet the baseline down as each is fixed.

- [x] ✅ [DEVOPS] P2. **Make the lag alert state a cause per line, or say it cannot.** It now distinguishes
      provenance-blocked; it should also distinguish (a) SIT-gated in-flight, (b) no promote PR exists, (c) promote PR
      BLOCKED/CONFLICTING, (d) cause unknown. A line that cannot name a cause should say so explicitly rather than imply
      "just slow". **DONE 2026-08-08, `unified-trading-pm@66ba7feda`** (via
      `ci_satellite_ao_dispatch_batch6_2026_08_08.md` todo 7, verified ancestor of `origin/live-defi-rollout`):
      `_ldr_main_finding()` in `scripts/cicd/promotion_lag_monitor.py` now names provenance-blocked (pre-existing),
      SIT-gated-in-flight (`sit-gate/fleet-green` status pending), no-promote-PR-open, and PR-BLOCKED/CONFLICTING
      (`mergeable_state` dirty/blocked); a match-less case says "cause unknown" explicitly. 12 new regression tests
      (`test_promotion_lag_monitor_promote_pr_cause.py`), `quality-gates.sh` green.
- [ ] [DEVOPS] P2. **`detect_breaking_change.py` is Python-only** (`endswith(".py")` + `ast.parse`), so every TS repo
      (`deployment-ui`, `unified-trading-system-ui`) is permanently "unknown-delta" and needs a full SIT round-trip on
      EVERY promote. That is a structural promotion tax, not a fault — but it is why those two repos are always the last
      to promote and always in the lag list.
- [ ] [DEVOPS] P3. Runner units have no `StartLimitBurst`/`StartLimitIntervalSec`, so a crash-looping unit restarts
      forever at ~6s (3,014+ counted) instead of entering `failed` where `systemctl --failed` would surface it. Entering
      `failed` would have made this visible to any host check on day one.

## Lesson

Two of the three mis-triages were mine, in this session. The alert did not lie — it just answered a question nobody
asked ("has content moved?") while the real questions ("is the pool alive?", "did a gate refuse?", "is this repo even
dispatched?") had no alarm at all. **When an alert's remedy is "go investigate", it is a symptom detector.** The fix is
not a better lag threshold; it is making each cause page for itself.

## na-eligibility-audit verdict

**na-eligibility-audit 2026-07-30** (tranche `ci`, autonomous): KEEP-NA, valid — the head P0 (re-do the `|| true`
credential-fetch fix in `glue-runner-run.sh`) is operator-gated on prod-risk grounds recorded in this doc: the first
attempt BROKE PROD, crash-looping all 5 glue runners (~34 restarts) until rollback, and the doc's own text forbids a
retry without first adding a `--selfcheck` mode and rolling ONE unit at a time. The sibling `- [x]` item in this same
doc re-states it as "operator-gated per the P0 above". The three smaller items (runner-liveness paging, per-line lag
causes, systemd `StartLimitBurst`) are bounded and are reasonable future carve-out candidates.

## Progress Log

- **context-scout 2026-08-03**: refreshed context_scope (6 entries — added
  `plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md` (as of 2026-08-09, archived to
  `/plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_2026_07_26.md`), where the runner-liveness-paging todo
  actually shipped).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.

**na-eligibility-audit 2026-08-06**: KEEP-NA, valid — operator-gated P0, first attempt broke prod, bounded residuals
exist

**round-9 combined RECLASSIFY + satellite-extraction sweep, 2026-08-09** (ci tranche): KEEP-NA, valid — re-read all 3
open items end-to-end. (1) The `|| true` re-fix P0 stays operator-gated: the doc's own root-cause section names the
exact bug (an apostrophe inside a `${VAR:-...}` default word) and a specific required safety protocol (whole-script
`--selfcheck` validation + one-unit-at-a-time canary rollout) before any retry — this is a live edit to the same
production self-hosted-runner systemd script that already crash-looped all 5 runners once; two prior audits (2026-07-30,
2026-08-06) independently reached the same verdict, unchanged here. (2) The `detect_breaking_change.py` Python-only
limitation is framed by the doc itself as an accepted structural tax, not a scoped fix with a done-when — extending it
to TypeScript is a design call, not a deterministic todo. (3) The systemd `StartLimitBurst`/ `StartLimitIntervalSec` gap
is comparatively low-risk (purely additive rate-limiting, does not touch the credential- fetch logic that broke prod)
but sits in the exact same live runner-fleet unit-file territory as item 1 and has not been separately operator-cleared
for extraction — left grouped with the doc's established conservative posture rather than unilaterally split off. No new
facts from today's round-9 cheat sheet (GSM secrets, Slack webhooks) apply to this doc's content. No `assigned_vm`
change.

**na-eligibility-audit 2026-08-10** (ci tranche, autonomous, dispatch agt-74eff9) [body-hash:c74b4b6fce6eb5a1]: KEEP-NA,
valid — Full read confirms 3 open items, all independently KEEP-NA'd across 3 prior audit passes (2026-07-30,
2026-08-06, round-9 combined sweep 2026-08-09) with detailed per-item re-derivation each time. Item 1 (P0, redo the
`|| true` credential-fetch fix): this is a live-dispatch-critical-path self-hosted-runner systemd script
(`glue-runner-run.sh`) whose FIRST fix attempt already crash-looped all 5 glue runners (~34 restarts) until rollback;
the doc's own root-cause section (an apostrophe inside a `${VAR:-...}` default word silently swallowing a credential
assignment) mandates a `--selfcheck` whole-script validation mode plus a one-unit-at-a-time canary rollout before any
retry -- exactly the 'multi-file/multi-day rewrite of live-dispatch-critical-path machinery' caution class, not a
small/low-risk change despite being bundled into one todo.
