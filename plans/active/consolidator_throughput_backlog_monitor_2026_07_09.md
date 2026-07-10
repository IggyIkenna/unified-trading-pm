---
doc_type: plan
title: Consolidators tab — per-AG backlog + consolidation throughput monitor
summary:
  Make the Consolidators cockpit tab answer "is the consolidator keeping up?" — surface the per-asset_group backlog
  (per-VM shards written since the last consolidated-index run, i.e. not yet absorbed) and a live throughput view of
  shards absorbed per tick. v1 is cheap + no consolidator change (backend backlog field from a single shard-prefix list
  + a client-accumulated session sparkline that INFERS merged/tick from backlog deltas). v2 (the truthful
  merged-per-tick histogram, sourced by instrumenting the consolidator job) is DEFERRED + still under discussion. WS-3
  (2026-07-10) folds in the deployments-page split — this page owns the DATA-CORRECTNESS lens, the per-run "did the run
  PRODUCE its expected data" verdict (fired-but-empty + stale-output) + a job-identity-keyed lookup seam the deployments
  detail popover cross-links to (deployments owns liveness/fired-on-time). LOCAL plan — built interactively in this
  slot.
status: active
nature: design
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui, deployment-api, unified-trading-library]
scope: [engineer]
tags: [deployment-observability, cockpit, consolidator, manifest, backlog, throughput, deployment-ui]
related: [deployment_observability_expansion_2026_07_08.md, deployment_full_estate_cost_provenance_2026_07_09.md]
created: "2026-07-09"
last_updated: "2026-07-10"
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: design
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.8
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
assigned_role: ui-developer
drift_direction: advance-code
---

# Consolidators tab — per-AG backlog + consolidation throughput monitor

> **LOCAL / human plan** (`assigned_vm: NA`, executed interactively in this slot — NOT AO-dispatched). Follows the
> Consolidators-tab live-monitor rewrite (`deployment-ui@9476927`). Operator feedback: the index-age/budget bar is a
> low-value "countdown to next consolidation"; the real questions are **is the consolidator keeping up (backlog)** and
> **how much is it absorbing per tick (throughput)**.
>
> **Scope grew 2026-07-10 (WS-3)**: agreed a clean split with the deployments page
> (`deployment_full_estate_cost_provenance_2026_07_09.md`, principles 6+7 + its hand-off). **Deployments = liveness**
> ("exists / healthy / fired / fired ON TIME" + a new Cloud Scheduler OVERDUE badge). **This page = data-correctness**
> ("did the run PRODUCE the data it was designed for") + the job-identity lookup seam deployments cross-links to. A job
> can exit 0 and write nothing — that "fired ≠ produced" gap is exactly what this lens owns; deployments LINKS to the
> verdict, never re-derives it (that would duplicate the manifest SSOT + break the single-walk HARD RULE).

## Design decisions (captured 2026-07-09)

- **Backlog = per-VM shards newer than the consolidated index.** Each VM writes ONE `_index/per_vm/{instance}.parquet`
  shard (rewritten on flush; `BlobMetadata.last_modified` per blob). The consolidator (per-AG Cloud Run Job + Cloud
  Scheduler, `*/1 * * * *`) merges them into the consolidated index every minute. Backlog for an AG = count of shards
  with `last_modified` > consolidated-index `last_modified` (written since the last run → not yet absorbed). Computable
  from ONE per-AG prefix list — **single-walk-safe** (the same list `_per_vm_shards_exist` already does).
- **The merged-per-tick throughput time-series is recorded NOWHERE today, and CANNOT be reconstructed after the fact**
  (each shard file carries only its latest mtime). A true time-series needs a source that logs each run as it happens.
- **v1 (this plan) = cheap, no consolidator change.** Backend returns the backlog COUNT (point-in-time, real). The UI
  already polls every 15s → the FRONTEND accumulates the polled backlog samples into a session-scoped rolling window and
  renders a live sparkline per AG; "shards absorbed this tick" is INFERRED from backlog drops between samples. Honest
  limits: window = your current watching session (resets on reload); "merged" is inferred (backlog delta), not the job's
  real count. Both are exactly what v2 fixes.
- **v2 (DEFERRED, under discussion) = the truthful merged-per-tick histogram.** Instrument the consolidator job to
  record `{ts, asset_group, shards_merged, backlog_after, rows_added, duration_ms}` per run to a durable store; the
  endpoint returns the last N runs → an exact histogram with real numbers + durable history. See the WS-2 section.

## Codex SSOTs (READ before touching each area)

- Manifest consolidator runtime (Cloud Run Job + Scheduler `*/1`, per-(kind, AG), `unified_trading_sa` objectAdmin):
  `codex/05-infrastructure/manifest-consolidator-ssot.md`.
- Availability manifest / per-VM shard layout + single-walk: `codex/02-data/availability-manifest-and-data-status.md`.
- Consolidator health endpoint: `deployment-api/deployment_api/routes/health_consolidator.py` (`ConsolidatorAgHealth`,
  `_ag_health`); per-VM shard helpers `unified_trading_library.manifest_writer._state` (`_per_vm_shards_exist`,
  `_consolidated_blob_age_sec`).
- UI testing gate (playwright L2): `codex/06-coding-standards/ui-testing-layers.md`.

---

## WS-1 — v1: backlog field + live session throughput (BUILD NOW)

- [x] 1. ✅ [BACKEND] P1. **UTL backlog helper** — `per_vm_shard_backlog(client, bucket, index_last_modified)` next to
     `_per_vm_shards_exist` (manifest_writer `_state.py`): ONE `_index/per_vm/*.parquet` list, returns
     `(pending, total)` where pending = non-legacy shards with `last_modified` STRICTLY AFTER the index's; missing/None
     mtime → not pending (honest under-count). Exported via facade + top-level `__init__`/`__all__`. —
     `unified-trading-library@da31ef2` + 5 unit tests (`test_per_vm_shard_backlog.py`), UTL QG green.
- [x] 2. ✅ [BACKEND] P1. **Endpoint field** — `pending_shard_count` + `total_shard_count` on `ConsolidatorAgHealth`;
     `_ag_health(..., include_backlog=True)` computes them via ONE `per_vm_shard_backlog` list (also yields shard
     existence, so no double-list); gated opt-in so the `/freshness` reuse (`consolidator_posture`) pays no extra list.
     `_mock_response` carries reps (cefi 2/6, defi 47/48). — `deployment-api@575810d` + 2 unit tests. (3 pre-existing
     unrelated QG failures in `test_data_status_drilldown.py` — DeFi uniswap pool schema, another agent's code.)
- [x] 3. ✅ [UI] P1. **Backlog display** — `pending_shard_count`/`total_shard_count` on `ConsolidatorAssetGroup`
     (health.ts) + "backlog (pending shards) N / total" per AG card (prominent when > 0). — `deployment-ui@8eb4001`.
     `pw:L2 ✓` cockpit.spec.ts O5 (cefi 47/48).
- [x] 4. ✅ [UI] P1. **Live throughput sparkline** — session rolling window (~40 samples ≈ 10 min) accumulated from the
     polls; per-AG recharts Area sparkline (`chart-theme` tones); "−N absorbed" derived from backlog drops; honest
     caption ("this session · inferred from backlog deltas"). — `deployment-ui@8eb4001`. `dataviz` skill loaded
     (single-series, no legend, 2px line). `pw:L2 ✓` O5 (sparkline accumulates across polls).
- [x] 5. ✅ [BACKEND] P1. **FINDING — cefi false-degraded fix (per-AG staleness budget).** Root cause (verified vs live
     GCS + Cloud Run): cefi market-tick is a DAILY batch, its consolidator effectively runs ~every 5 min (executions 5
     min apart; index age climbed 174→228s), but the endpoint judged every AG against a uniform 120s budget → cefi
     `degraded` ~60% of the time. Fix: `_AG_STALENESS_BUDGET_SEC`/`_budget_for` — cefi = 86400s (its launchers'
     `MANIFEST_CONSOLIDATED_STALENESS_SEC`), others keep 120s default. — `deployment-api@90ace9f` + unit test; live cefi
     now `age=120s status=ok`.
- [x] 6. ✅ [UI] P2. **Poll cadence 15s→30s** — consolidation changes every 1–5 min, so 15s over-polled. —
     `deployment-ui@b00454b` (O5 test waits the new 30s 2nd-poll).
- [ ] [REVIEW] P1. QG both repos green; **deploy deployment-api** (Cloud Build) so the live tab shows the real backlog +
      the cefi fix, and cite `Evidence: cloudbuild=<id>` SUCCESS. Verify the live endpoint returns `pending_shard_count`
      and cefi=ok.

## WS-2 — v2: truthful merged-per-tick histogram (DEFERRED — 🟡 UNDER DISCUSSION / nice-to-have)

> **Not built. Design captured so we don't lose it.** The consolidator job KNOWS its exact merge count (its merge step
> lists + reads every shard). Recording that per run gives an exact, durable histogram — replacing v1's inferred,
> session-only view. Deferred because it edits the consolidator job code and **redeploys ~10-20 Cloud Run Jobs + the AWS
> Batch mirror** — a data-correctness-critical-path change whose real cost is blast radius + rollout care, not dollars.
>
> **⚠️ Overlap with the parent's WS-H (2026-07-10 review)**: `deployment_observability_expansion_2026_07_08.md` WS-H
> builds a general structured-progress spine — a `report_progress({...})` helper riding the UTL **event facade** + a
> typed per-workload progress contract + a "manifest cross-check per typed metric (`shards_saved` vs object count)".
> That is the SAME per-run-job-metrics sink WS-2 needs. **WS-2 must RIDE WS-H's spine, not build a parallel
> GCS/Firestore store** — if WS-H ships the event-facade spine, WS-2's `{ts, shards_merged, …}` record becomes one typed
> progress event on it; the bespoke store below is the FALLBACK only if WS-H stays deferred. So the store-decision todo
> is contingent on WS-H's outcome — coordinate before building either.

- [ ] [DESIGN] P3. **Store decision — OPEN.** GCS/S3 rolling history object (recommended: zero new IAM, each job writes
      its own cloud's bucket it already has objectAdmin on, reuses the endpoint read path; ~$2-4.50/mo GCS Class-A) vs
      Firestore (native TTL + query, cheaper writes ~$1/mo, `ci_status` precedent, BUT +IAM +client dep, and the AWS
      mirror would need GCP creds — cross-cloud). **Cost is negligible either way (< ~$5/mo); the decision is
      architecture-fit + blast radius.** OPEN sub-question: does the AWS Batch mirror actually consolidate any of the 5
      AGs (cefi/defi/tradfi/sports/prediction), or is it GCP-only? All 5 index buckets are GCP → if GCP-only, Firestore
      is clean same-cloud and the cross-cloud concern is moot.
- [ ] [INFRA] P3. **Instrument the job** — after each merge, append
      `{ts, asset_group, shards_merged, backlog_after,     rows_added, duration_ms}` (~15 lines; the merge already knows
      `len(shards)`). Rolling window cap (last 24-48h). Staged rollout (one AG first, verify, then fan out); rollback
      story documented.
- [ ] [BACKEND] P3. **Endpoint history** — `/api/health/consolidator` (or a `/consolidator/{ag}/history`) returns the
      last N runs; the UI swaps the inferred sparkline for the real merged/tick histogram (drop the "inferred" caption).

## WS-3 — data-correctness lens: per-run "did it PRODUCE its data" verdict + deployments cross-link seam (NEW 2026-07-10)

> **The other half of the deployments-page split** (`deployment_full_estate_cost_provenance_2026_07_09.md` principles
> 6+7 + its 2026-07-10 hand-off). Deployments = **liveness** ("does it exist, is it healthy, did it fire, did it fire ON
> TIME" — incl. a new Cloud Scheduler OVERDUE badge). This page = **data-correctness** ("did that run PRODUCE the data
> it was designed to"). Deployments LINKS to this verdict, never re-derives it (duplicating the manifest SSOT + breaking
> single-walk). A job can exit 0 and write nothing — "fired" ≠ "produced"; that fired-but-empty case is the gap only
> this lens catches.

### Join key — reconcile with the deployments agent BEFORE building the seam (blocking)

- [ ] [DESIGN] P1. **Agree the join key = the FULL Cloud Run job short-name (which encodes `{kind}-{asset_group}`), NOT
      `asset_group` alone.** LIVE-VERIFIED
      (`gcloud run jobs list --region asia-northeast1 --project central-element-323112`, 2026-07-10): the hand-off's
      assumed example `prd-manifest-consolidator-cefi` does NOT exist. Real names are
      `uts-prod-manifest-consolidator-{kind}-{asset_group}` and there are **~25 non-legacy consolidator jobs, MULTIPLE
      per asset_group across kinds** (`market-data-cefi` AND `instruments-cefi` AND `features-delta-one-cefi` AND
      `execution-cefi` …). So `asset_group` alone is ambiguous — the seam MUST key on `(kind, asset_group)` / the full
      short-name. Enumerator jobs = `expected-universe-v2-{ag}` (5); catalogue = `lifecycle-catalogue-regen-{ag}` /
      `-full-{ag}` / `instrument-catalogue-regen`. Reconcile 1:1, then both sides freeze the key.

### The seam + the verdict (this page owns)

- [ ] [BACKEND] P1. **Per-run output-production verdict endpoint (the seam deployments links to)** — a lightweight
      lookup keyed by the agreed job identity →
      `{last_run_at, partitions_written, rows_written, expected_vs_actual,     verdict}`,
      `verdict ∈ {produced, fired_but_empty, stale_output, ok}`. Scope = the **data-producing** scheduled jobs only
      (consolidator per (kind,AG), enumerator per AG, catalogue per AG) — NOT the watchers/audits (they write no
      pipeline data → liveness is their whole story). SINGLE-WALK-SAFE: reuse the consolidated-index blob metadata + the
      per-VM prefix list already fetched (`per_vm_shard_backlog`); NEVER a whole-corpus walk.
- [ ] [BACKEND] P1. **Fired-but-produced-nothing detection** — a run whose Scheduler/execution says it fired (exit 0)
      but `rows_written ≈ 0` while backlog > 0 → `fired_but_empty`. Reuse the index row-count delta
      (`object_delta_for_asset_group`, already built) across the run window. This is the silent failure a liveness-only
      view shows as "succeeded".
- [ ] [BACKEND] P1. **Stale-output detection** — newest output partition older than the job's OWN cadence →
      `stale_output`. Generalize the per-AG staleness budget already added for the cefi false-degraded fix
      (`_AG_STALENESS_BUDGET_SEC` / `_budget_for`) into a per-(kind,AG) cadence budget, so each job is judged against
      its schedule, not a uniform 120 s.
- [ ] [BACKEND] P2. **Coverage-expansion — verdict across ALL consolidator kinds, not just market-data.** Today
      `/api/health/consolidator` covers ONLY the market-data bucket per AG (5 AGs). The full consolidator estate is ~25
      jobs across kinds (instruments / features-delta-one / features-onchain / features-volatility / features-calendar /
      features-sports / execution / strategy / gas-fees / ml-training-artifacts). For the deployments cross-link to
      resolve for EVERY job it lists, the seam must cover every data-producing job. Decide scope (market-data-first,
      then fan out) — flag to operator. **SEQUENCING (2026-07-10 review)**: until this lands, the deployments
      job→manifest bridge resolves ONLY for the 5 market-data jobs — the other ~20 consolidator / enumerator / catalogue
      jobs it lists get a DANGLING cross-link. Agree the interim contract with the deployments agent (bridge =
      market-data-first; a job the seam doesn't yet cover renders "not-yet-covered", NOT an error).
- [ ] [UI] P1. **Surface the production verdict on the consolidator page** — per (kind,AG), a `produced` /
      `fired-but-empty` / `stale-output` badge alongside the existing freshness + backlog. A red fired-but-empty /
      stale-output is the data-correctness signal deployments links here to confirm. `pw:L2` regression on the badge
      states.

### Fan-in — which VMs feed the index (recommendation #4; contributor↔live-VM correlation)

- [ ] [BACKEND] P2. **Contributor-VM fan-in from the shard filenames (EXACT, single-walk-cheap).** Each per-VM shard is
      `_index/per_vm/{instance}.parquet` → the filename IS the VM instance name; the SAME prefix list we already do for
      backlog yields, per (kind,AG), EXACT: N contributor VMs, WHICH VMs, and each VM's last-flush age (shard
      `last_modified`). Return `contributor_count` + `stale_contributor_count` (last flush > cadence). DEFER per-VM
      `rows_written` (needs a shard content-read → breaks single-walk; blob-size proxy is too rough).
- [ ] [UI] P2. **Fan-in headline + drill.** Card headline "fed by N VMs · M stale (>{cadence})"; drill lists contributor
      VM names + last-flush age, each **cross-linked to the Fleet/Deployments row**. The correlation that matters at
      scale: shard stale + VM stopped = data frozen (expected); shard stale + VM still RUNNING = the VM is stalled and
      silently not flushing (a bug). `pw:L2` on the fan-in cell.

### Dark data-correctness actors — decide whether they surface here (operator to prune)

- [ ] [DESIGN] P2. **Phantom-audit + reprobe-empty visibility — decide surface + build a read endpoint if in-scope.**
      These are the "is the index HONEST" checks, Slack-only today (no endpoint): `dp-manifest-hygiene-full` (weekly
      `0 8 * * 0`) finds **phantom rows** (index says `captured`, NO parquet on disk — the index lying about coverage;
      `DP-MANIFEST-003/005`); `dp-reprobe-empty` (daily `0 9 * * *`) re-fetches wrongly-`empty_confirmed` cells and
      flips proven-wrong ones back to `attempted_failed` (`DP-FETCH-006`). Surfacing needs a small endpoint reading
      their last result (GCS sentinel / event log). Data-correctness signal → belongs on THIS page if surfaced at all.

### Shipping gate (WS-3 — mirrors WS-1's closer)

- [ ] [REVIEW] P1. **QG both repos green + deploy deployment-api + verify the seam resolves live.** After the seam +
      fired-but-empty + stale-output + verdict badge land: `quality-gates.sh` green (deployment-api + deployment-ui +
      any UTL helper), deploy deployment-api via Cloud Build citing `Evidence: cloudbuild=<id>` SUCCESS, and verify the
      LIVE endpoint returns the verdict for a known job identity AND that the deployments detail popover's cross-link
      resolves 1:1 (end-to-end handshake with `deployment_full_estate_cost_provenance_2026_07_09.md`'s job→manifest
      bridge). No `- [x]` on any WS-3 build todo until this closes.

### Cross-tab placement notes (NOT this plan — captured so we don't lose them)

- **Duplicate info across the two UIs is INTENTIONAL for now (operator, 2026-07-10)** — where the deployments page and
  this page (or the data-status tab) show the same underlying signal, they're almost always different AXES of it
  (liveness vs produced-vs-expected; coverage-trust vs rows-written-verdict). KEEP both while the UIs are being built;
  de-dupe only once they're properly built. Do NOT collapse a cross-tab overlap prematurely.
- **Denominator freshness has two facets, split by tab**: the _trust caveat on the coverage %_ ("denominator last
  computed Nh ago" / stale-warning) → **data-status tab** (owns coverage %); the _enumerator/catalogue JOB fired + on
  time_ → **deployments** (its Cloud Scheduler census). The _did-the-enumerator-actually-write-rows_ verdict IS in this
  page's seam above (enumerator/catalogue are data-producing jobs). **⚠️ UNOWNED (2026-07-10 review)**: the data-status
  trust-annotation has NO todo in any plan today — it needs a `- [ ]` in a data-status plan
  (`data_status_tab_and_downloads_remediation_2026_06_16.md` or a new one), else it's lost on hand-off. NOT this plan to
  build — flag it when passing notes to the data-status/deployments agents.
- **Lambda run-time honesty (FYI from the hand-off)**: deployments is fixing `last_run_at = fn.last_modified` (deploy
  time, not invoke). The data-producing pipeline jobs are Cloud Run (GCP) + AWS Batch, NOT Lambda, so the seam likely
  never touches a Lambda run-time — but if it ever does, use CloudWatch `Invocations`, never deploy-time.

## Progress Log

- 2026-07-09 — Plan created (LOCAL). Verified: `BlobMetadata.last_modified` is available per blob → true backlog is a
  single-list computation (single-walk-safe). Consolidator runs every 1 min per-AG (Cloud Run Job + Scheduler). v1 needs
  ZERO consolidator change. v2 store/cost analysis captured; v2 deferred as nice-to-have pending the GCS-vs-Firestore +
  AWS-mirror-scope decision.
- 2026-07-10 — WS-3 added from the deployments-page split hand-off
  (`deployment_full_estate_cost_provenance_2026_07_09.md` principles 6+7 + its 2026-07-10 hand-off). Agreed lens split:
  deployments = liveness / fired-on-time (+ a new Cloud Scheduler OVERDUE census); this page = data-correctness /
  produced-vs-expected + the job-identity lookup seam deployments cross-links to. **LIVE-VERIFIED the join key**
  (`gcloud run jobs list --region asia-northeast1`, 2026-07-10): the hand-off's example `prd-manifest-consolidator-cefi`
  does not exist — real = `uts-prod-manifest-consolidator-{kind}-{asset_group}`, ~25 non-legacy consolidator jobs,
  MULTIPLE per AG across kinds → the join key must be the full short-name / (kind,AG), NOT asset_group alone. Flag back
  to the deployments agent. Also captured: fan-in from shard filenames (#4, exact + single-walk), phantom/reprobe
  visibility decision (#5, needs an endpoint), coverage-expansion beyond market-data (current endpoint covers only 5
  market-data buckets vs ~25 jobs), and the denominator-freshness cross-tab split. Awaiting operator review to prune
  scope.
- 2026-07-10 — Cross-plan review gap-fixes (operator asked to close gaps in THIS plan; notes for other plans passed
  separately). Fixed the 4 gaps found reviewing the 8-plan UI-enhancement cluster: (5) added a **WS-3 shipping gate**
  `[REVIEW]` closer (QG + deploy + live seam/cross-link verify) — WS-3 had none vs WS-1's; (6) flagged **WS-2 duplicates
  the parent's WS-H** structured-progress spine → WS-2 must RIDE the event-facade spine, bespoke store is fallback-only;
  (7) noted the **denominator-freshness data-status annotation is UNOWNED** (needs a todo in a data-status plan); (8)
  documented the **coverage-expansion sequencing** contract (bridge = market-data-first, ~20 dangling links interim →
  "not-yet-covered", not error). Also codified the operator principle: **cross-tab duplicate info is intentional for now
  (different axes) — keep both until the UIs are properly built, de-dupe later**.
