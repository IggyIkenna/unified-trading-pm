---
doc_type: codex-runbook
title: CI/CD daily health log
summary:
  "Dated, append-only log of the daily /ci-reconcile habit — persistent (non-auto-resolving) alerts, GH Actions spend +
  self-hosting migration candidates, and CI VM resource health, one entry per run with a delta-since-last-run line so
  the operator can scan for what changed without re-deriving state from scratch. Written by /ci-reconcile itself when
  run in daily-report mode (SKILL.md §7b) — never hand-edit past entries, append a new dated ## section instead."
status: current
nature: process
asset_group: [cross-cutting, ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [runbook, ci-reconcile, ci-cd, billing, self-hosted, vm-health, daily]
related:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /codex/04-architecture/ci-alerting.md,
    /codex/05-infrastructure/deployment-observability.md,
  ]
created: "2026-08-18"
authoritative_for: [
    daily CI/CD fleet health tracking — persistent alerts,
    GH Actions spend,
    self-hosting migration status,
    CI VM
    resource health,
  ]
referenced_by: []
owner: operator (daily, human-run)
cadence: daily
verifier:
  "a new dated ## section exists for today with all four subsections populated (persistent alerts / ci-reconcile ran /
  spend / VM health) and a delta line against the prior entry"
last_executed: "2026-08-18"
code_refs:
  [cursor-configs/skills/ci-reconcile/SKILL.md, scripts/generate-workflow-catalog.py, scripts/dev/slack-read-channel.py]
audience: operator / dev
last_updated: "2026-08-18"
execution:
  {
    owner: "operator (daily, human-run)",
    cadence: "daily",
    verifier:
      "a new dated ## section exists for today with all four subsections populated (persistent alerts / ci-reconcile
      ran / spend / VM health) and a delta line against the prior entry",
    last_executed: "2026-08-18",
  }
---

# CI/CD daily health log

Append-only. One `## <date>` section per day `/ci-reconcile` runs in daily-report mode. Read the PREVIOUS entry before
running, diff key figures into a **Delta since last run** line at the top of the new one. Never edit a past entry — if
something reported that day turns out wrong, correct it in the NEXT entry, not retroactively.

## 2026-08-18

**Delta since last run**: n/a — first entry.

- **Persistent alerts (non-auto-resolving)**: none. Two real incidents overnight (5 Dockerfile digest-pin conflicts
  across execution-service/features-service/instruments-service; a lag-monitor ETag staleness bug) — both root-caused
  and fixed same-session, confirmed landed.
- **ci-reconcile ran**: yes (this session, ad-hoc — not yet on a standing daily timer).
- **GH Actions spend**: real numbers pulled from `deployment-api`'s `/api/costs/breakdown` (GitHub Enhanced Billing,
  Plan-scoped token via GSM — `gh api .../settings/billing/actions` 404's on an ordinary token, this is the correct
  source, see §8's updated recipe). Last 10 days, net USD/day after credit: 08-09 $6.56 · 08-10 $6.64 · 08-11 $2.76 ·
  08-12 $3.63 · 08-13 $3.80 · 08-14 $16.01 · 08-15 $40.88 · 08-16 $21.59 · 08-17 $10.09 (operator's "quiet day"
  reference point — matches exactly) · 08-18 $0.08 so far (partial, provisional). 10-day total $112.03, avg
  ~$11.20/day, but swings 15x (\$2.76–\$40.88) tracking commit/promote velocity directly — 08-15's spike lines up with
  the heaviest promote-PR churn window this session. Consistent gross→net discount of 70-90% (a prepaid/included
  allowance draining faster on busy days). Structural finding unchanged: the expensive per-push test/typecheck/lint
  work is ALREADY on the self-hosted glue-runner pool (`[self-hosted, glue]`) on every private repo checked
  (execution-service, features-service, instruments-service, market-tick-data-service, strategy-service,
  deployment-service). `unified-trading-pm` itself (source of most high-frequency `*/15`–`*/30` scheduled monitors)
  is PUBLIC — those cost nothing regardless of cadence. Remaining GH-hosted jobs per private repo
  (`notify-slack.yml`, `plan-alignment-agent.yml`, `version-registry-notify.yml`, `publish-package.yml`,
  `image-build-gate.yml`'s dispatch/poll legs, a few repo-specific ones) are individually lightweight — no single
  obviously-misplaced expensive workflow found. The day-by-day spend swing confirms the real driver is commit/promote
  _volume_, not runner placement — a quiet day already costs ~$3-7, a heavy one $20-40+ regardless of what's
  self-hosted.
- **CI VM resource health** (`i-042a6332509482556`, `m8i.2xlarge`, 8 vCPU/32GB, glue-runner pool): 24h sample (17,277
  points) — CPU avg 13.3%/max 99.9%, load-avg-1m avg 1.3/max 15.2 (real oversubscription at peak, ~1.9x core count),
  iowait avg 0.8%/max 44.1%, swap avg 0.5%/max 9.5%. Verdict: correctly sized, not over-provisioned — the low average
  masks genuine burst demand that would get worse on a smaller box. No watchdog alerts fired in 24h. Not a finding.

## 2026-08-18 (second pass, agt-d23e6a, scheduled hourly sweep)

**Delta since last run**: new persistent alert found (PM promote-PR corpus-ratchet block) and partially fixed;
2 transient CRITICAL alerts confirmed self-healed; spend/VM health not re-run this pass (unchanged from above).

- **Persistent alerts (non-auto-resolving)**: `unified-trading-pm`'s `checks` QG slice was blocking every LDR→main
  promote PR (#3457, #3459, #3460, #3461 — visible live in `GET /api/escalations/active` as a chain of
  `promote_qg_failure` escalations) on 3 unrelated hard-fail ratchets: (1) `check_reference_paths` existence 35 vs
  baseline 34 — root cause: `plans/active/issues/ag_closeout_audit_ci_parked_2026_08_16.md` cited a target doc that
  had since been archived (active→archive move, stale path never updated) — **fixed**, repointed to
  `/plans/archive/issues/...`; (2) `check_ag_closeout_linkage` 1 orphan — `defi_perp_daily_ctx_hl_forward_gap_since_
2026_06_02_2026_08_04_finalize_2026_08_08.md` had no body-mention in `defi_consolidated_closeout_2026_07_18.md` —
  **fixed**, citation added (had to trim the addition to stay under the 1000-line hard cap, doc was already at 997L);
  (3) `check_artefact_disclosure` 6 hard hits of the banned client name in `strategy-service-deep-dive.html` — **left
  alone**, already an open P0 todo in the actively-dispatched `plans/active/client_artefact_remediation_siblings_
2026_08_18.md` (line 68, `sequential: true`), fixing it here would risk colliding with that plan's in-flight work.
  Shipped `unified-trading-pm@8f916bd82f`, verified on origin; (1) and (2) confirmed clear locally post-fix. The
  promote PR will still show red until the sibling plan's ClearLoop redaction lands — expected, not a new gap.
- **Self-healed, confirmed via current green state**: `agent-orchestrator` QG-slice cancel/timeout (20:06Z);
  `trading-agent-service`/`market-tick-data-service`/`ml-service`/`unified-trading-library` QG-slice failures
  (21:07-21:15Z, all same-SHA retry-succeeded at 22:05Z — transient runner flake, no code fix needed, no open
  promote PRs on any of the 4); `deployment-service` main-branch FAILING→FEATURE_GREEN (ci-status-update, 22:09Z);
  Cloud Run traffic-pin on `signal-broadcast-smoke-receiver` (19:12Z) — live `gcloud run services describe` shows
  100% traffic on the latest revision, not pinned. No Slack RECOVERED post found for the traffic-pin specifically
  (asymmetric-alerting gap, § 0d) — worth a one-line note, not a new incident.
- **Coverage gap**: could not verify `glue-runner-crash-loop-watchdog`'s 20:01Z CRITICAL (`github-glue-runner-
unified-api-contracts@glue-1.service`, "10.2h active, current job's own start time not resolvable") via live SSM —
  `ikenna-worker` AWS identity lacks `ssm:SendCommand` on `i-042a6332509482556` and isn't one of the two ambient
  self-service identities this workspace's IAM self-grant rule covers, so no self-grant attempted. Indirect check:
  `unified-api-contracts`'s own GH Actions history shows zero in-progress runs and clean `success` completions both
  before and after 20:01Z — no evidence of an actually-hung job, consistent with the known `unit_active_seconds`
  false-positive class this skill already documents (the alert's own "current job's own start time not resolvable"
  phrase matches that failure mode exactly). Likely false alarm, not confirmed — flagging the SSM access gap itself
  as worth a fix (a read-only `ssm:SendCommand`/`ssm:GetCommandInvocation` grant scoped to this instance would let
  `/ci-reconcile` verify this class directly instead of inferring from GH Actions data).
- **ci-reconcile ran**: yes (second pass this UTC day, scheduled dispatch agt-d23e6a).
- **GH Actions spend**: not re-pulled this pass — see the first entry above, unchanged.
- **CI VM resource health**: not re-run this pass — see the first entry above, unchanged.
