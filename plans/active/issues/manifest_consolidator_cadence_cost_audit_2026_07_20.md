---
doc_type: issue
title:
  "Manifest-consolidator cost audit — ~$180/day GCP spend driven by a uniform */1 cadence; cadence reduction is real but
  requires two coupled fixes (reader staleness budget + liveness watchdog), not a schedule-only edit"
summary: >-
  Audited why the manifest-consolidator's GCP Cloud Run spend is as high as it is (~$180/day / ~$5.4k/mo across 18 jobs,
  all on `*/1 * * * *`). Root cause: cost is dominated by fixed per-invocation overhead (cold start + GCS round-trips,
  ~35-46s regardless of bucket size or whether there's anything to merge), not data volume, so every minute-tick costs
  roughly the same whether or not it does real work. A follow-up "properly checked" pass found the codex SSOT's claim
  that "every consolidator except live market-data gets an 86400s staleness budget" does NOT match the actual
  enforcement code — only the `cefi` asset_group gets that relief; every other bucket defaults to 120s unless a specific
  reader happens to override it. A live per-bucket write-activity check narrowed the genuinely low-risk
  cadence-reduction set to 12 of the 18 jobs (~$109/day); `instruments-sports` + `features-sports` have live writers
  right now and are NOT safe to slow without a companion staleness-budget fix. A second, independent coupling (the
  liveness watchdog's hardcoded 60s/5-cycle DOWN threshold, shared across all 18 buckets in one Cloud Run Job
  invocation) would false-page `CONSOLIDATOR_DOWN` for any bucket slowed without updating it in lockstep. No changes
  made — this is a findings/audit doc only.
status: open
nature: issue
asset_group: [cross-cutting] # corrected 2026-07-31 (ag-closeout-audit cross-cutting Phase 0 meta-tag sweep) -- was [meta], a genuine mistag: manifest-consolidator cadence/cost content is core cross-cutting scope (manifest/GCS-path), not process-level/spans-nothing meta
stage: [data]
repos: [deployment-service, unified-trading-library, deployment-api]
scope: [engineer, admin]
tags:
  [
    manifest-consolidator,
    cost,
    billing,
    cloud-run,
    cadence,
    staleness-budget,
    liveness-watchdog,
    infrastructure,
    ssot-drift,
  ]
related: []
created: 2026-07-20
priority: P2
parent_epic: infrastructure_master
source:
  "Operator-requested audit of the deployment-ui cost page (2026-07-20), following a separate snapshot-staleness
  investigation ($532.97 UI figure vs $640.61 live BigQuery for the same manifest-consolidator label/window). Cadence
  finding then independently re-verified against the actual read-path/watchdog code and live GCS state per operator
  instruction to 'check properly' before any change is proposed."
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
assigned_vm: NA
resolved_by:
---

# Manifest-consolidator cost audit — cadence reduction is real, but coupled to two other systems

No changes have been made to any schedule, config, or code as part of this audit. Everything below is read-only
findings, gathered from live `gcloud`/`bq`/`aws` queries + source reads on 2026-07-20.

## 1. What it costs today (measured)

Direct BigQuery query against
`central-element-323112.billing_export.gcp_billing_export_resource_v1_016B25_109840_AF2ACB`, filtered to GCP label
`purpose=manifest-consolidator`, for a fully-settled day (2026-07-19, Pacific billing calendar):

- **Total: ~$180.51/day** across the 18 current GCP Cloud Run Jobs (~$5,415/mo, ~$65.9k/yr). AWS-side Batch Fargate
  manifest-consolidator (~26 EventBridge rules, `rate(1 minute)`) is currently confirmed **all DISABLED** — zero AWS
  spend to address here (note: this contradicts the codex SSOT's "26 ACTIVE, all ENABLED" claim, which is stale
  documentation, not a cost problem).
- All 18 GCP jobs run on Cloud Scheduler `*/1 * * * *` (every minute, UTC), 17 of them at 4 vCPU / 16Gi, one
  (`market-data-defi`) at 8 vCPU / 32Gi.
- Measured CPU usage on a typical job is ~345,600 vCPU-sec/day ÷ 4 vCPU ≈ 86,400s — i.e. billed as if running nearly
  continuously across the day's 1,440 invocations (~60s billed per tick on average).
- Sampled 14 live executions across large (`market-data-cefi`), small (`features-calendar`), and mid-size
  (`instruments-sports`) buckets: all clocked **~28-46s regardless of bucket size** (cold start: ~8.5s image pull +
  ~13.7s provisioning, then lock/freshness checks + a GCS shard-listing call even on a genuine no-op). **A no-op cycle
  costs essentially the same as a real merge** — cost tracks invocation count, not data volume.

## 2. Finding A — cadence reduction is real, but two things are coupled to it

### 2a. Codex SSOT vs actual code — the "every non-live consolidator gets 86400s" claim is wrong

`/codex/05-infrastructure/manifest-consolidator-ssot.md` states: _"live market-data ticks
(defi/tradfi/sports/prediction) = 120s; every other consolidator = 86400s."_ The actual enforcement
(`unified_trading_library/manifest_writer/_staleness_budget.py` → `_state.py::_resolve_consolidated_staleness_sec`) does
not match this:

```python
AG_STALENESS_BUDGET_SEC: dict[str, int] = {"cefi": 86400}   # ONLY cefi gets a code-level override
```

Every other asset_group (defi/tradfi/sports/prediction) — and every asset-group-less flat bucket (`strategy-store`,
`execution-store`, `ml-store`, `features-calendar`) — falls through to the Pydantic field default of **120s**, unless
the _specific process reading that bucket_ happens to export `MANIFEST_CONSOLIDATED_STALENESS_SEC` itself. A repo-wide
grep shows this override is set ad hoc by individual one-off backfill-VM launchers
(`deployment-service/scripts/vm/launch-*-backfill-vm.sh`, ~25 call sites, all `=86400`) for their own reads — it is
**not** a durable per-bucket guarantee for every reader (e.g. a dashboard, a health check, or any script that doesn't
happen to set it). This is a real SSOT/code drift worth correcting in the codex doc independent of any cadence decision.

### 2b. Live write-activity check — sports is the exception, not the rule

`ManifestConsolidatorStaleError` (a loud, paging failure) only fires when the index is stale past budget **and**
other-VM shards currently exist to merge. Listed `_index/per_vm/` live for every non-`cefi` bucket on 2026-07-20:

| Bucket                                                                              | Live writer activity                                                                                            | Verdict                                         |
| ----------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| `instruments-sports`                                                                | **Actively written** — shards timestamped within minutes of the check (`is-daily-enum-sports`, `af-backfill-*`) | **Not safe to slow as-is**                      |
| `features-sports`                                                                   | **Actively written** — shards timestamped during the check itself                                               | **Not safe to slow as-is**                      |
| `instruments-{defi,tradfi,prediction}`                                              | Only a stale `_legacy_seed.parquet` (May/June) — no live writer                                                 | Safe (nothing to race)                          |
| `features-{defi,tradfi,calendar}`, `strategy`, `execution`, `ml-training-artifacts` | Zero per-VM shards                                                                                              | Safe (genuinely-empty-bucket exemption applies) |

Combined with the 3 `cefi`-labeled jobs (which get the code-level 86400s override regardless of write activity —
`market-data-cefi`, `instruments-cefi`, `features-cefi`), this gives **12 of 18 jobs genuinely low-risk to slow today**
(~~$109.10/day of the $180.51/day total, ≈60%). `instruments-sports` + `features-sports` (~~$23.85/day) need the
staleness-budget widened for their asset_group _before_ their cadence is touched, or a real reader will start seeing
spurious loud failures. The 4 live market-data jobs (`market-data-{defi,tradfi,sports,prediction}`) are correctly
excluded from any cadence change — they exist specifically for near-real-time freshness.

### 2c. Liveness watchdog — a second, independent coupling

`uts-prod-consolidator-liveness-watchdog` (Cloud Scheduler `*/2 * * * *`) checks all 18 buckets in **one Cloud Run Job
invocation** against a hardcoded assumption:

```python
# Consolidator runs at */1 (60s); 5 missed cycles = 300s before we page
_DEFAULT_CYCLES_GRACE = 5
_DEFAULT_CYCLE_SEC = 60
```

Confirmed via `gcloud run jobs describe` that the deployed job passes only `--buckets <18 names>` — no per-bucket
override, so every bucket shares this 300s DOWN threshold. The CLI does support `--cycles-grace`/`--cycle-sec`, but only
as one shared value per invocation, not per-bucket. **Slowing any bucket's cron without also widening this watchdog
threshold (or splitting it into per-tier invocations) will produce false `CONSOLIDATOR_DOWN` pages** for that bucket
roughly 5 minutes into every gap, regardless of whether anything is actually wrong.

## 3. Options considered and their disposition (operator decision, 2026-07-20)

- **A — cadence reduction**: confirmed real and the largest lever (~$109/day / ~$3,270/mo addressable at low risk);
  requires the three coupled pieces above (cron schedule + reader staleness budget + watchdog threshold) shipped
  together, not a schedule-only edit. **Not yet implemented — audit only.**
- **B — resource right-sizing** (4vCPU/16Gi is oversized for steady-state no-op cycles on most buckets): **declined by
  operator.** Not pursued further; noted here only for completeness of the original audit.
- **C — Group-B ("extended" tier: features-\*, execution, strategy, ml-training-artifacts) has no per-bucket cpu/memory
  override mechanism in Terraform** (unlike the Phase-A module, which supports one): **operator decision is to keep the
  current default as-is.** No action.

## 4. Suggested path forward (not executed — for a future plan if the operator wants to proceed)

1. Extend `AG_STALENESS_BUDGET_SEC` (or the sports asset_group's read path generally) before touching
   `instruments-sports` / `features-sports` cadence at all.
2. For the 12 low-risk jobs: widen the Cloud Scheduler cron (e.g. hourly — still ~3,600x tighter than each bucket's
   effective 24h(-ish) tolerance for `cefi`, and simply safe for the currently-idle buckets since no other-VM shards
   exist to race) **together with** a matching liveness-watchdog `--cycle-sec`/`--cycles-grace` update (likely requires
   splitting the watchdog invocation into a fast-tier and slow-tier group).
3. Re-verify via the existing verification recipe in `/codex/05-infrastructure/manifest-consolidator-ssot.md` + a
   follow-up cost check after one full billing cycle.
4. Separately: correct the codex SSOT doc's "every other consolidator = 86400s" claim to reflect the actual `cefi`-only
   code-level override (Finding 2a) — a docs-only fix, independent of whether the cadence change ships.

## 5. Verification commands used (reproducible)

```bash
# Current job/cron inventory
gcloud run jobs list --region asia-northeast1 --project central-element-323112 --format="value(metadata.name)" | grep manifest-consolidator
gcloud scheduler jobs list --location asia-northeast1 --project central-element-323112 --filter="name~manifest-consolidator" --format="table(name,schedule,state)"

# Per-job/per-SKU cost for a settled day
bq query --project_id=central-element-323112 --use_legacy_sql=false --format=csv <<'SQL'
SELECT resource.name AS resource_id, sku.description AS sku,
  ROUND(SUM(cost / IFNULL(NULLIF(currency_conversion_rate, 0), 1)), 4) AS cost_usd
FROM `central-element-323112.billing_export.gcp_billing_export_resource_v1_016B25_109840_AF2ACB`
WHERE _PARTITIONTIME >= TIMESTAMP('2026-07-18')
  AND DATE(usage_start_time, 'America/Los_Angeles') = DATE('2026-07-19')
  AND cost <> 0
  AND (SELECT value FROM UNNEST(labels) WHERE key = 'purpose' LIMIT 1) = 'manifest-consolidator'
GROUP BY resource_id, sku ORDER BY resource_id, cost_usd DESC
SQL

# Live per-VM shard activity for a bucket
gcloud storage ls -l "gs://<bucket>/_index/per_vm/**"

# Watchdog's actual deployed args (confirms no per-bucket override)
gcloud run jobs describe uts-prod-consolidator-liveness-watchdog --region asia-northeast1 \
  --project central-element-323112 --format="value(spec.template.spec.template.spec.containers[0].args)"
```

## 6. Resolution criteria

This issue closes when either: (a) the operator explicitly declines to pursue cadence reduction and this is archived as
a documented-but-not-actioned finding, or (b) a plan is authored covering the three coupled pieces in §4 and shipped,
with a post-change cost verification showing the expected reduction and zero new `CONSOLIDATOR_DOWN` /
`ManifestConsolidatorStaleError` events attributable to the change.

## Todos

- [x] ✅ [INFRA] P2. **RULED 2026-07-29 (operator direct answer) — proceed.** Ship the coupled cadence-reduction fix per
      "Suggested path forward":

      **(1) extend `AG_STALENESS_BUDGET_SEC` for sports' read path first** — ALREADY DONE by separate, earlier work,
                  confirmed live 2026-07-30 before touching anything else:
                  `unified_trading_library/manifest_writer/_staleness_budget.py`'s `AG_STALENESS_BUDGET_SEC` is
                  `{"cefi": 86400, "sports": 1800, "defi": 3600}` — sports added `fix(manifest): add sports:1800s override`
                  (`unified-trading-library@fd87daa1`, 2026-07-24) and defi added as a bonus 2026-07-29
                  (`unified-trading-library@13d3daef`) by `sports_manifest_read_staleness_budget_missing_2026_07_15.md` /
                  `defi_manifest_consolidator_staleness_budget_missing_2026_07_29.md`, both predating this dispatch.
                  `deployment-api`'s cockpit-only `_AG_STALENESS_BUDGET_SEC` mirrors the same 3 entries. No new code needed here.

                  **(2) widen the cron schedule for the 12 low-risk jobs + matching liveness-watchdog fast/slow-tier split** —
                  SHIPPED + APPLIED LIVE 2026-07-30, `deployment-service@7b832cb0`:
                  `manifest_consolidator_scheduler.tf` gained a `manifest_consolidator_schedule` local (the exact 12 categories
                  from this audit's §2b: `instruments-{cefi,tradfi,defi,prediction}`, `market-data-cefi`,
                  `features-{cefi,defi,tradfi,calendar}`, `strategy`, `execution`, `ml-training-artifacts`) mapped to `0 * * * *`
                  (hourly), consumed via `lookup(..., "*/1 * * * *")` in both `manifest_consolidator_cron` resources so every
                  other category keeps its original per-minute cadence. `consolidator_liveness_scheduler.tf`'s single watchdog
                  job/cron was split into a `for_each` fast/slow tier pair (fast: unchanged 60s/5-cycle=300s threshold for the 6
                  still-`*/1` buckets; slow: 3600s/2-cycle=7200s threshold, checked at `:15,:45` past the hour, for the 12 widened
                  buckets) — the watchdog CLI applies one shared `--cycle-sec`/`--cycles-grace` per invocation, so this split was
                  required, not optional, once the cron cadences diverged. The alert policy's `dynamic "conditions"` per-tier
                  approach was REJECTED live by GCP ("Alert policies with a log matching condition can only have a single
                  condition") — used a single condition with an OR'd `job_name` filter across both tiers instead (same
                  page-on-either-tier semantics). **Applied via `ENV=prod ./tofu.sh apply` (scoped `-target=`, confirmed a
                  subsequent untargeted-but-scoped re-plan shows "No changes")**: live `gcloud scheduler jobs list` confirms
                  exactly 12 jobs on `0 * * * *` / 6 on `*/1 * * * *`; both new watchdog Cloud Run Jobs
                  (`uts-prod-consolidator-liveness-watchdog-{fast,slow}`) manually executed to completion (`gcloud run jobs
                  execute --wait`) with every bucket reporting `-> ok` (zero false `CONSOLIDATOR_DOWN`). Two IAM self-grants were
                  needed mid-apply (`roles/monitoring.alertPolicyEditor`, `roles/logging.configWriter` on `unified-trading-sa`,
                  per the cloud-identity self-service rule) — granted + verified live, not paused on.

                  **(3) re-verify via the existing recipe** — done above (live scheduler list + watchdog dry-executions + log
                  read, zero false pages). **The "follow-up cost check after one full billing cycle" cannot be done
                  synchronously** (GCP billing export settles ~1 day later) — tracked as its own new P3 todo below rather than
                  left as unchecked prose.

                  **(4) correct the codex SSOT's stale claim** — DONE:
                  `/codex/05-infrastructure/manifest-consolidator-ssot.md`'s "Per-(kind, AG) cadence staleness budget" section
                  corrected to the real `{"cefi": 86400, "sports": 1800, "defi": 3600}` dict + the new non-uniform cron cadence;
                  the older 2026-07-12 "Feed-SLA registry" finding kept historically intact with a dated stale-as-of note
                  appended (this doc's own dated-finding convention).

                  Repos: unified-trading-library (already-landed, no new commit this session), deployment-service (terraform),
                  unified-trading-pm (codex).

- [ ] [OPS] P3. Query the BigQuery billing export for `purpose=manifest-consolidator` for a fully-settled day AFTER
      2026-07-30 (the cadence-reduction ship date) — same recipe as this doc's own §5 — and confirm the
      ~$109/day
      (~$3,270/mo) addressable savings materialised, with zero
      `CONSOLIDATOR_DOWN`/`ManifestConsolidatorStaleError` events attributable to the change (check
      `#data-pipeline-alerts` history + the watchdog's own Cloud Run execution log for the 24h+ following the ship).
      This is the doc's own §6 "Resolution criteria" (b) — closes the doc once confirmed. (repo: unified-trading-pm,
      read-only verification)

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (infra tranche, dispatch agt-30721a) — Sole todo carries an
  explicit dated operator citation ('RULED 2026-07-29 — proceed') on a live prod cost/paging system change.
- **rulings-closeout sweep 2026-07-30**: Implemented + applied all 4 sub-items of the ruling live (see the todo's own
  detail above). Verified item (1) was already satisfied by separate prior work before touching anything, so no
  duplicate/conflicting code was written. Left the "one full billing cycle" cost re-check as an explicit new P3 todo
  (genuinely can't run synchronously) rather than a prose promise.
