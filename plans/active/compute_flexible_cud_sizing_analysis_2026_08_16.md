---
doc_type: plan
title: Compute Flexible CUD sizing analysis — findings and revisit date
summary: >
  Answers "should we buy a 1-year Compute Flexible CUD" from real billing data (bq against
  gcp_billing_export_v1_resource) rather than estimate. Verdict: not yet — the always-on footprint is too small and
  still growing to size a 1-year commitment against. Revisit once it's had time to stabilize.
status: active
nature: design
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [cost, billing, cud, compute-engine, gcp]
related:
  [
    /codex/05-infrastructure/billing-cost-observability.md,
    /plans/active/manifest_consolidator_and_lifecycle_cost_optimization_2026_08_16.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-19"
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: research
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.24
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: ["interactive session, 2026-08-16, operator question: sizing a 1-year Compute Flexible CUD"]
assigned_role: infra
effort: low
drift_direction: advance-code
context_scope: [/codex/05-infrastructure/billing-cost-observability.md]
---

# Compute Flexible CUD sizing analysis

> **LOCAL / human plan** — a findings record + a single future-dated revisit todo, not active work. Written up
> during a `/pre-compact` pass after discovering this analysis existed only in chat, at risk of being lost.

## The question

Operator asked whether a 1-year GCP Compute Flexible CUD makes sense, sized off backfill compute hours.

## Method

Queried `central-element-323112.billing_export.gcp_billing_export_v1_resource_016B25_109840_AF2ACB` via `bq`
(BigQuery aggregate queries — not GCS reads, not the heavy-I/O class the operator later restricted). Split
Compute Engine spend by SKU (spot/preemptible vs on-demand), then by `resource.name` to identify what's actually
running, over a 90-day and a 30-day trailing window.

## Findings

1. **Backfill hours are the wrong base — CUDs don't cover Spot/Preemptible usage, and backfill VMs default to
   Spot** per this workspace's own launcher convention. Sizing a commitment against spot-shaped usage means paying
   for capacity that spot spend can never draw down.
2. **The "on-demand" bucket itself is bursty, not a steady floor** — 90-day: 21 of 91 days at $0, mean $183/day but
   median only $69/day, p90 $317/day, one day at $2,905. Not CUD-safe as a whole either.
3. **Splitting it further**: a real, coherent steady population exists — persistent "live" service VMs
   (`mtds-dex-swaps`, `mtds-perp-funding`, `mtds-dex-pools`, `mtds-live-cefi-consolidated`,
   `mdps-features-live-{cefi,defi}`, `mtds-live-sports-odds-api-trades`) — median ~$51/day, p90 ~$116/day on the
   days they existed. The rest of the on-demand bucket is one-off historical backfill campaigns
   (`cefi-*-heavy-*`, dated-suffix VMs) that happened to run on-demand rather than spot — a separate finding, not
   chased further this session (worth someone checking why, separately from the CUD question — Spot's ~60-91%
   discount beats a CUD's ~28% with no lock-in, so moving these to spot is the bigger, lower-risk lever if the
   pattern holds).
4. **Trailing 30 days** (most relevant — the live-service population only started appearing in the last 2 weeks of
   the window): total $4,589, median $116/day, mean $153/day, only 2 zero-days, p10 $16/day. Still growing, not
   stable.

## Verdict

**Don't buy the CUD yet.** If forced to size one today, the defensible floor is the p10-p25 of the last-30-day
series (~$16-40/day, ~$500-1,200/month) — but the live-service population that IS the real steady floor only
started existing in the two weeks before this analysis, and kept growing during the window. Locking a 1-year
commitment against a still-climbing baseline means either re-buying more later (footprint keeps growing) or
sitting on idle committed spend (footprint growth stalls or reverses) — both are real risks a few more weeks of
data would resolve.

## Interim check (2026-08-18, 2 days after this doc was written)

Not the full re-analysis (still scheduled below) — an early look at whether the "still climbing" premise still
holds, since it's cheap to check and the premise is load-bearing for the whole "wait" recommendation. Re-ran the
same live-service resource-name query (corrected table name: `gcp_billing_export_resource_v1_016B25_109840_AF2ACB`,
this doc's own method line below had it backwards). **Result: the population is no longer "still climbing" — it
declined 4 days straight through 08-17** (38.71 → 35.77 → 32.92 → 16.93/day, after peaking ~$40-48/day around
08-10 to 08-13). Full trend table + the manifest-consolidator cost-gain interim check run alongside it:
`/plans/active/manifest_consolidator_and_lifecycle_cost_optimization_2026_08_16.md`'s 2026-08-18 Progress Log
entries. Cause of the decline not investigated. **This does not change the verdict (still don't buy) but does
change the reasoning** — waiting is no longer just about "let growth stabilize," it's now also "let a possible
reversal resolve" — and it shortens the sensible re-check cadence (see the updated todo below).

## Todos

- [ ] [REVIEW] P3. **Re-check the live-service trend in ~1-2 weeks (not the full 30-day wait)** — the interim
      check above found a new 4-day DECLINE, not just continued growth, which the original 2026-09-15 date didn't
      account for. A short re-check resolves whether this is a real plateau/reversal or a temporary dip before
      waiting the full window blind to it. Done-when: a fresh trend pull shows either the decline continuing/
      stabilizing/reversing, dated.
- [ ] [REVIEW] P3. **Full sizing re-analysis no earlier than ~2026-09-15** (30 days after this session, adjust later
      if the interim check above changes the picture) — same method (bq against
      `gcp_billing_export_resource_v1_016B25_109840_AF2ACB`, split spot/on-demand, isolate the live-service
      resource-name population from one-off campaigns). If the live-service floor has stabilized (stopped moving
      week-over-week) rather than still trending, size a CUD off its p10-p25 at that point. Done-when: a fresh
      30/90-day pull exists with a stable-or-not verdict, dated.

## Progress Log

- **na-eligibility-audit 2026-08-17** (infra tranche) [body-hash:f14bf5dee79894a1]: KEEP-NA, valid — doc is a
  findings record + a single future-dated revisit todo, explicitly gated "no earlier than ~2026-09-15" and
  requiring a stabilization judgment call on a still-growing cost baseline. Added this Progress Log section (doc
  had none) so future incremental runs can skip it via the dated marker.
- **context-scout 2026-08-17**: populated/refreshed context_scope (1 entry).
- **na-eligibility-audit 2026-08-18** (infra tranche) [body-hash:4b8ac46902aa5bca]: KEEP-NA, valid — unchanged since
  2026-08-17. The 2026-08-18 interim-check addition updates the REASONING (trend now declining 4 days straight, not
  still growing) but not the verdict — both todos remain dated future re-checks requiring a stabilization judgment
  call on a moving cost baseline, not worker-determinable today.
- **context-scout 2026-08-19**: re-verified context_scope, no change needed (1 entry), still accurate.
