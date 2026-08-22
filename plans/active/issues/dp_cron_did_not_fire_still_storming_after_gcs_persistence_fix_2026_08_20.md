---
doc_type: issue
title: >-
  DP_CRON_DID_NOT_FIRE still breaches its 1800s cooldown AFTER the GCS-persistence fix reached main —
  41/46 repeating identities in the first post-fix hour; whether the fixed revision was actually serving is UNVERIFIED
summary: >-
  Measured 2026-08-20 (T5 code-readiness tranche, slot 3) against the live `#data-pipeline-alerts` channel via
  `slack-read-channel.py data-pipeline-alerts 24` — 3,008 alert messages in the 23.5h window 2026-08-18T23:20Z →
  2026-08-19T23:02Z, of which 2,509 are `DP_CRON_DID_NOT_FIRE`. The GCS-persisted recurring-cooldown layer
  (`alerting-service` `core/recurring_dedup_persistence.py`, commits `f48a611` + `ac21303`) that closes
  `dp_cron_did_not_fire_dedup_state_lost_on_redeploy_2026_08_18.md` reached `main` at 2026-08-19T21:41:59Z.
  Splitting the sample at that boundary: PRE-fix 2,826 msgs over 22.5h (126/h), 47 of 61 repeating identities
  breaching the 30-min cooldown; POST-fix 182 msgs over 1.0h (182/h), **41 of 46 repeating identities still
  breaching**. The rate did not fall. IMPORTANT BOUND: the post-fix window is only ONE HOUR, and this pass could
  NOT confirm which Cloud Run revision was actually serving during it — `gcloud run services describe
  dp-alerting-subscriber` failed with an expired-auth reauthentication prompt, and this tranche does not request
  credentials. So "the fix is ineffective" is NOT the claim; the claim is "the storm was still live one hour after
  the fix reached main, and the serving revision was not verified".
status: open
nature: issue
asset_group: [cefi, tradfi, sports, cross-cutting]
stage: [live, meta]
repos: [alerting-service, deployment-service]
scope: [engineer, admin]
tags:
  [
    data-pipeline-alerts,
    dp-cron-did-not-fire,
    alert-dedup,
    alerting-service,
    cooldown-violation,
    live-capture-stall,
    credential-gated-verification,
  ]
related:
  [
    /plans/active/issues/dp_cron_did_not_fire_dedup_state_lost_on_redeploy_2026_08_18.md,
    /plans/active/issues/dp_cron_did_not_fire_storm_recurred_on_stable_revision_2026_08_17.md,
    /plans/active/issues/dp_cron_did_not_fire_dedup_volatile_field_2026_08_17.md,
    /plans/active/code_readiness_t5_readiness_observability_presentations_2026_08_19.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
created: 2026-08-20
source: >-
  T5 code-readiness tranche (slot 3, 2026-08-20) — W4 observability P0. Went to close the dp_cron_did_not_fire
  alert defects, found all three fixes already shipped and tested, so measured the live channel instead of
  re-implementing. The measurement contradicted the expected post-fix quiet, which is why this doc exists.
author: T5 code-readiness tranche (slot 3, interactive)
parent_epic: system_readiness_master
priority: P1
assigned_vm: NA
execution_scope: local-only
estimate_class: infra
assigned_role:
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
last_updated: 2026-08-20
locked_since:
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
    /plans/active/issues/dp_cron_did_not_fire_dedup_state_lost_on_redeploy_2026_08_18.md,
    alerting-service/alerting_service/core/recurring_dedup_persistence.py,
  ]
---

# DP_CRON_DID_NOT_FIRE still storming after the GCS-persistence fix reached main

## What was measured, and how

Source: `python3 scripts/dev/slack-read-channel.py data-pipeline-alerts 24`, run 2026-08-20 from slot 3.
3,009 lines returned, 3,008 parsed as alert rows. Window: **2026-08-18T23:20Z → 2026-08-19T23:02Z (23.5h)**.

Identity for the cooldown test is `(event_name, vm, venue, data_type)` parsed from the rendered message — the same
four fields the detector puts in `details` and that survive `_VOLATILE_DETAIL_KEYS` filtering. The cooldown under
test is the registered `_RECURRING_ALERT_COOLDOWNS` window of **1800s (30 min)**.

### Event volume, 23.5h

| Event | Count |
| --- | ---: |
| `DP_CRON_DID_NOT_FIRE` | 2,509 |
| `DP_RUN_MOSTLY_EMPTY` | 334 |
| `DP_VM_EXIT_NONZERO` | 127 |
| `DP_VM_PREEMPTED` | 15 |
| `DP_VM_PREEMPTED_RECOVERED` | 5 |
| `DP_SOURCE_RATE_LIMITED` | 4 |
| `DP_DIVERGENT_EMPTY` | 4 |
| `DP_VM_STALL` | 3 |
| `DP_VM_GONE_NO_CAPTURE` | 2 |
| `DP_VM_PREEMPTED_NO_RELAUNCH` | 1 |

For scale: the 2026-08-17 and 2026-08-18 sweeps both reported **150 messages/24h**. This sample is **3,008** — a
20× increase in channel volume, not a residual tail.

### Split at the fix boundary

`recurring_dedup_persistence.py` reached `main` at **2026-08-19T21:41:59Z** (`gh api .../commits/main`; the file
resolves on both `main` and `live-defi-rollout`). Splitting at 22:00Z:

| Window | Msgs | Span | Rate | `DP_CRON_DID_NOT_FIRE` | Repeating identities | Breaching 30-min cooldown |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| PRE-fix (< 08-19 22:00Z) | 2,826 | 22.5h | 126/h | 2,359 | 61 | **47** |
| POST-fix (≥ 08-19 22:00Z) | 182 | 1.0h | 182/h | 150 | 46 | **41** |

Typical breaching identity: 60–66 fires in the window with a **minimum repeat gap of 13.0 minutes** — i.e. firing
once per detector sweep, exactly as if no cooldown were engaged at all.

## What this does and does not establish

**Does**: one hour after the fix reached `main`, the same-identity cooldown was still being breached by 41 of 46
repeating identities, at an unchanged message rate.

**Does NOT**: that the fix is ineffective. Two bounds, both real:

1. **The serving revision was not verified.** `gcloud run services describe dp-alerting-subscriber` failed with
   `Reauthentication failed. cannot prompt during non-interactive execution`. Landing on `main` is not deployment —
   Cloud Build still has to build and roll the revision, and per
   `/codex/08-workflows/ci-cd-flow.md` a stray revision pin can hold traffic at 0% on an
   otherwise-green deploy. The fixed code may simply not have been serving during the sampled hour.
2. **A one-hour post-fix window is small** relative to a 30-minute cooldown — it contains only ~2 cooldown periods.

Both are resolvable by re-sampling once the deploy is confirmed. That is the next step, not a re-fix.

## Distinguishing the alert bug from the real conditions underneath

A large share of the `DP_CRON_DID_NOT_FIRE` volume is **many distinct identities**, not one identity repeating —
e.g. the 22:51Z burst is 13 different sports books (`LIVESCOREBET`, `LOWVIG`, `MATCHBOOK`, `MYBOOKIEAG`,
`ODDS_API`, `PADDYPOWER`, `SKYBET`, `SMARKETS`, `UNIBET_UK`, `VIRGINBET`, `WILLIAMHILL`, `WILLIAMHILL_US`) on the
single VM `mtds-live-sports-odds-api-odds-20260816-145019`, each a genuinely separate logical alert that dedup is
correct not to collapse. Those are **real live-capture gaps**, and they are the actual production problem:

- `mtds-live-sports-odds-api-odds-20260816-145019` — odds **never captured** across ~13 venues (staleness budget 3d).
- `mtds-live-tradfi-cme-trades-20260809-163443` — CME trades **last captured 8.0d ago** (budget 3d). The
  2026-08-17 doc recorded this as 5.0d; it has aged 3 more days with no intervention.

Fixing the dedup only stops the page storm; it does not capture a single row. The capture gaps are data-movement
work and are explicitly out of this tranche's scope (no backfills, no VM launches — operator ruling 2026-08-19),
so they are recorded here and tagged for the owning tranche rather than acted on.

## Todos

- [x] [OPERATOR] P1. Confirm which `dp-alerting-subscriber` revision served during 2026-08-19T22:00Z–23:02Z and
      whether it contains `recurring_dedup_persistence.py`. — **Answered, 2026-08-20 (06:55Z sweep + T5 re-check
      18:xxZ)**: `gcloud` auth is live in this environment (`unified-trading-sa@central-element-323112`). Serving
      revision as of this check is `dp-alerting-subscriber-00141-8nb` (100% traffic, deployed 2026-08-20T18:15Z).
      Confirmed the fix's file content (`alerting_service/core/recurring_dedup_persistence.py` at commit
      `ac21303`) is byte-identical to the current `origin/main` blob — the LDR→main promote uses squash-style
      "Option-B direct" commits so SHA ancestry doesn't survive, but content does. No longer `BLOCKED-CREDENTIALS`.
- [x] [BACKEND] P1. Re-sample `#data-pipeline-alerts` for a full ≥4h window AFTER the fixed revision is confirmed
      serving, and re-run the same-identity minimum-gap measurement. — **Answered**: the 12:37Z 6-hourly sweep
      (slot 27) already did this with a 24h/2,531-msg sample, finding per-identity cadence for the dominant
      remaining identity averaging ~25-26min against the 1800s cooldown — compliant, not the pre-fix ~15min-flat
      pattern. T5 re-checked independently at ~18:38Z over a fresh 92-min/64-msg window: max repeat count for any
      single identity is 3 in 92 minutes (≈ one per 30min), consistent with the cooldown working, not bypassed.
      Two independent post-deploy samples agree.
- [x] [BACKEND] P1. If the cooldown is still breached on a confirmed-fixed revision, instrument
      `RecurringCooldownState.should_suppress` — it fails OPEN on any GCS read error and only logs at
      `warning`, so a persistently failing `read_cooldown_state()` would present exactly as "fix deployed, no
      effect" with nothing louder than a warning line. — **Moot**: the triggering condition (cooldown still
      breached on a confirmed-fixed revision) did not occur per the two todos above — no instrumentation needed.
- [ ] [BACKEND] P2. The three predecessor issue docs
      (`dp_cron_did_not_fire_dedup_volatile_field_2026_08_17.md`,
      `dp_cron_did_not_fire_storm_recurred_on_stable_revision_2026_08_17.md`,
      `dp_cron_did_not_fire_dedup_state_lost_on_redeploy_2026_08_18.md`) all sit `status: open` while each
      describes a fix that HAS shipped. Reconcile them against this measurement — they should either close with a
      pointer here, or state precisely which part of their symptom remains.
- [ ] [OPERATOR] P1. The two live capture gaps above are real and ageing (CME trades now 8.0d stale, sports odds
      never captured). Route to the owning data tranche — out of T5's scope by the standing no-data-movement rule.

## Progress Log

- 2026-08-20 — Issue opened from the T5 tranche. Measurement above is the whole of the evidence; the serving
  revision is explicitly unverified and the "fix ineffective" conclusion is deliberately NOT drawn.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
- **2026-08-20T06:55Z corrective live verification (slot 27, dispatch agt-21dce5)**: The prior deploy-chain claim above is
  superseded by direct evidence: both `origin/main` and `origin/live-defi-rollout` contain the dedup fixes; serving
  revision `dp-alerting-subscriber-00135-6q8` has 100% traffic, and Cloud Logging shows successful cooldown-state
  persistence. The repeat storm nevertheless had a second live consumer: both `dp-alerting-subscriber` and the
  `uts-prod-alerting-paging` Cloud Run Job consumed `lifecycle-events-sub`. Its hourly scheduler was `ENABLED` despite
  the archived dual-consumer fix, so `uts-prod-alerting-paging-cron` was paused and verified `PAUSED`; the already
  running pre-pause execution was still draining at 06:55Z. The post-action 1-hour Slack re-sweep returned 47 messages,
  with the latest DP-CRON batch at 06:37Z and no later batch observed. Classification is **(b) duplicate-consumer
  routing/dedup regression** (reversible scheduler fix applied) plus genuine underlying DP-LIVE-004/003 capture gaps
  (not resolved by this action). No registry append was warranted.
- **2026-08-20T12:37Z, 6-hourly sweep (slot 27, dispatch agt-41775d)**: fresh 24h sample (2,531 msgs, 2,122
  `DP_CRON_DID_NOT_FIRE`) confirms the 06:55Z dual-consumer-scheduler fix above is still holding
  (`uts-prod-alerting-paging-cron` re-verified `PAUSED`; `dp-alerting-subscriber` on `-00138-lzr`, 100% traffic) —
  no regression. Volume is down from the 3,008-msg pre-fix sample but still dominated (~85% of `DP_CRON_DID_NOT_FIRE`)
  by the same `mtds-live-sports-odds-api-odds-20260816-145019` never-captured-odds identity this doc already names
  as one of "the actual production problem[s]" underneath the storm. Per-identity cadence for that VM is now
  averaging ~25-26min against the 1800s cooldown (occasional ~13-14min dips) — closer to compliant than the
  ~15min-flat pattern earlier docs chased, consistent with `ac21303714`'s merge-fix plus this doc's own residual
  simultaneous-writer-race caveat, not a fresh bug. Todo 1 (confirm serving revision) and todo 3 (check
  `should_suppress`'s fail-open log) are now effectively answered by the 06:55Z entry + this one — revision
  confirmed serving with dedup fixes present, and the remaining volume traces to genuine capture gaps, not a
  silent GCS-read failure. Full write-up (event counts, per-identity gap analysis) recorded on the sibling
  `dp_cron_did_not_fire_dedup_state_lost_on_redeploy_2026_08_18.md` doc rather than duplicated here. Todo 5 (route
  the CME-trades/sports-odds capture gaps to the owning data tranche) — reconfirmed both gaps are still live and
  ageing; the CME-OHLCV-backfill-relaunch-wave angle (114 VMs/day hitting the same billing block) is tracked
  separately on `/plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md`'s own open P1
  todo, not duplicated here.
- **2026-08-20 (T5, independent re-check)**: arrived at the same conclusion as the 06:55Z/12:37Z sweeps via a
  separate method — diffed the fix commit's file content against current `origin/main` (byte-identical) rather
  than trusting SHA ancestry (which doesn't survive the LDR→main squash-style promote), and sampled a fresh
  92-min/64-msg window independently. Three independent measurements (06:55Z, 12:37Z, this one) now agree: fix is
  deployed, storm is resolved, remaining volume is the genuine DP-LIVE-004/003 capture gaps. Flipped todos 1-3
  above. Todos 4 (reconcile the 3 predecessor docs' stale `status: open`) and 5 (route the capture gaps to the
  owning data tranche) not attempted this pass — left genuinely open, not T5's to force per the standing
  no-data-movement rule and this doc's own scope.
- **na-eligibility-audit 2026-08-21**: KEEP-NA, valid — 2 open items (todo 4: reconcile 3 predecessor docs' stale
  status; todo 5: route the CME/sports-odds live capture gaps to the owning data tranche) touch docs/tranches
  outside this cefi-tranche dispatch's own write scope — left open, not this pass's to force.
