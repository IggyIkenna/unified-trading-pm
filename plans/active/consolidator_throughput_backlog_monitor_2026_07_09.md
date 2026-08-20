---
doc_type: plan
title: Consolidators tab — per-AG backlog + consolidation throughput monitor
summary:
  Make the Consolidators cockpit tab answer "is the consolidator keeping up?" — surface the per-asset_group backlog
  (per-VM shards written since the last consolidated-index run, i.e. not yet absorbed) and a live throughput view of
  shards absorbed per tick. v1 is cheap + no consolidator change (backend backlog field from a single shard-prefix list
  + a client-accumulated session sparkline that INFERS merged/tick from backlog deltas). v2 (the truthful
  merged-per-tick histogram) was DESCOPED 2026-07-13 — it rides WS-H's structured-progress spine (WS-H's current home is
  unsettled — see the 2026-07-13 Progress Log entry below), not a separate build here. WS-3 (2026-07-10) folds in the
  deployments-page split — this page owns the DATA-CORRECTNESS lens, the per-run "did the run PRODUCE its expected data"
  verdict (fired-but-empty + stale-output) + a job-identity-keyed lookup seam the deployments detail popover cross-links
  to (deployments owns liveness/fired-on-time). LOCAL plan — built interactively in this slot.
status: active
nature: design
asset_group:
  [ui] # corrected 2026-07-30 (ui-tranche launch) -- was [cross-cutting]; the Consolidators cockpit
  # tab itself (repos: deployment-ui, deployment-api, unified-trading-library)
stage: [meta]
repos: [deployment-ui, deployment-api, unified-trading-library]
scope: [engineer]
tags: [deployment-observability, cockpit, consolidator, manifest, backlog, throughput, deployment-ui]
related:
  [
    /plans/archive/2026_07/deployment_observability_expansion_2026_07_08.md,
    /plans/archive/2026_07/deployment_full_estate_cost_provenance_2026_07_09.md,
  ]
created: "2026-07-09"
last_updated: "2026-08-19" # (was: 2026-08-07 -- plan-reconcile 2026-08-18: bumped to match latest Progress Log entry, now through na-eligibility-audit 2026-08-17; corrects a 2026-08-15 bump that recorded 2026-08-07 instead of that pass's own date)
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
assigned_role: ui_developer
drift_direction: advance-code
context_scope:
  [
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/06-coding-standards/ui-testing-layers.md,
    deployment-api/deployment_api/routes/health_consolidator/,
    deployment-ui/src/pages/Cockpit.tsx,
  ]
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
- **v2 (DESCOPED 2026-07-13 — no longer a workstream here) = the truthful merged-per-tick histogram.** Instrument the
  consolidator job to record `{ts, asset_group, shards_merged, backlog_after, rows_added, duration_ms}` per run; the
  endpoint returns the last N runs → an exact histogram. This is now a downstream consumer of **WS-H's
  structured-progress event-facade spine** (see the Progress Log descope note — WS-H's home is unsettled, no longer
  `deployment_observability_expansion_2026_07_08.md`, see finding 183), NOT a separate build in this plan. The v1
  inferred sparkline stays as the shipped view.

## Codex SSOTs (READ before touching each area)

- Manifest consolidator runtime (Cloud Run Job + Scheduler `*/1`, per-(kind, AG), `unified_trading_sa` objectAdmin):
  `/codex/05-infrastructure/manifest-consolidator-ssot.md`.
- Availability manifest / per-VM shard layout + single-walk: `/codex/02-data/availability-manifest-and-data-status.md`.
- Consolidator health endpoint: `deployment-api/deployment_api/routes/health_consolidator.py` (`ConsolidatorAgHealth`,
  `_ag_health`); per-VM shard helpers `unified_trading_library.manifest_writer._state` (`_per_vm_shards_exist`,
  `_consolidated_blob_age_sec`). (Cross-ref: this endpoint was shipped by `unified_deployment_health_cockpit_2026_06_23`
  [complete], which is the same surface `monitoring_control_plane_master_2026_06_10.md`'s G3 item still lists as
  "homeless"/"IN PROGRESS — slot 3"; see that doc's G3 note for the reconciliation. [finding 182, synced 2026-07-14])
- UI testing gate (playwright L2): `/codex/06-coding-standards/ui-testing-layers.md`.

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
      `MANIFEST_CONSOLIDATED_STALENESS_SEC`), others keep 120s default. — `deployment-api@90ace9f` + unit test; live
      cefi now `age=120s status=ok`.
- [x] 6. ✅ [UI] P2. **Poll cadence 15s→30s** — consolidation changes every 1–5 min, so 15s over-polled. —
      `deployment-ui@b00454b` (O5 test waits the new 30s 2nd-poll).
- [ ] [REVIEW] P1. **Local verify now; Cloud Build deploy DEFERRED (operator 2026-07-10 — local-dev-only until all
      cockpit plans complete; operator is the sole viewer, local iteration is faster).** QG both repos green; run
      deployment-api locally against live GCS + the UI against it, and verify the endpoint returns `pending_shard_count`
      and cefi=`ok` live. Deploy (Cloud Build, `Evidence: cloudbuild=<id>` SUCCESS) happens at end-of-cockpit-plans, if
      the promote pipeline hasn't already carried it.

## WS-3 — data-correctness lens: per-run "did it PRODUCE its data" verdict + deployments cross-link seam (NEW 2026-07-10)

> **The other half of the deployments-page split** (`deployment_full_estate_cost_provenance_2026_07_09.md` principles
> 6+7 + its 2026-07-10 hand-off). Deployments = **liveness** ("does it exist, is it healthy, did it fire, did it fire ON
> TIME" — incl. a new Cloud Scheduler OVERDUE badge). This page = **data-correctness** ("did that run PRODUCE the data
> it was designed to"). Deployments LINKS to this verdict, never re-derives it (duplicating the manifest SSOT + breaking
> single-walk). A job can exit 0 and write nothing — "fired" ≠ "produced"; that fired-but-empty case is the gap only
> this lens catches.

### Join key — reconcile with the deployments agent BEFORE building the seam (blocking)

- [x] [DESIGN] P1. ✅ **AGREED (2026-07-10, with the deployments agent) — join key = the VERBATIM Cloud Run job
      short-name** (`job.name.rsplit("/", 1)[-1]` from `JobsClient.list_jobs`, real e.g.
      `uts-prod-manifest-consolidator-market-data-cefi`), NOT the `(kind, asset_group)` tuple. Rationale: it's the ONE
      string both sides read verbatim, so neither derives it — the tuple would need two independent fuzzy
      `{kind}-{asset_group}` parses (deployments' classifier is a suffix/substring match) → drift → silent missed joins;
      and env-prefix / `-backfill` / `-v2` variants collide on the tuple but never on the name. **This page OWNS the
      `short-name → (kind, asset_group) → partition/bucket` decode as SSOT**; deployments passes `kind` + `asset_group`
      alongside as hint/validation only. Bare short-name is unique today (all `asia-northeast1`); region-qualify if
      multi-region lands. (The agent's `prd-manifest-consolidator-cefi` example is illustrative — real names carry the
      `uts-prod-` prefix + a `-{kind}-` segment my decode handles.) Enumerator jobs = `expected-universe-v2-{ag}` (5);
      catalogue = `lifecycle-catalogue-regen-{ag}` / `-full-{ag}` / `instrument-catalogue-regen`. **WS-3 seam is
      UNBLOCKED.**

### The seam + the verdict (this page owns)

- [x] [BACKEND] P1. ✅ **STALE — already done piecemeal, closing 2026-08-07 (na-eligibility-audit).** Per-run
      output-production verdict endpoint (the seam deployments links to) — a lightweight lookup keyed by the agreed job
      identity → `{last_run_at, partitions_written, rows_written, expected_vs_actual, verdict}`,
      `verdict ∈ {produced, fired_but_empty, stale_output, ok}`. The 4 concrete sub-todos directly below this one
      (fired- but-empty detection, per-cadence stale-output budget, dynamic all-consolidator coverage-expansion, and the
      `VerdictBadge` UI surfacing) are ALL individually shipped and checked — `deployment-api@1a505c16`/`@14650f9`,
      `deployment-ui@15832cd`/`@368ea8e6` — and together they ARE this exact seam/verdict ask; the umbrella checkbox was
      simply never flipped alongside its parts.
- [x] [BACKEND] P1. ✅ **Fired-but-produced-nothing detection — SHIPPED 2026-07-11.** `_is_fired_but_empty()` joins the
      job's latest Cloud Run execution (`latest_execution_by_job()`, one batched list, keyed by job short-name) with the
      index freshness: a recent SUCCEEDED run (exit 0, within budget) against a STILL-STALE index → `fired_but_empty`
      (ran green, wrote nothing); if the last success is ALSO old, it's plain `stale_output`/down, not empty. Added a
      real `fired_but_empty` branch to `_verdict()` + `execution_status`/`execution_last_run_at`/`execution_exit_code`
      on `ConsolidatorHealth`. — `deployment-api@1a505c16` + 6 unit tests + `deployment-ui@368ea8e6` (amber "fired ·
      empty" badge + estate count) + `pw:L2 ✓` cockpit.spec.ts **O6**.
- [x] [BACKEND] P1. ✅ **Stale-output — per-(kind,AG) cadence budget SHIPPED 2026-07-11.** Verified the Cloud Scheduler
      cron is a UNIFORM `*/1` for every consolidator, so the real budget is the `MANIFEST_CONSOLIDATED_STALENESS_SEC`
      each producer VM sets — ALL producers set 86400s EXCEPT the live market-data ticks (defi/tradfi/sports/prediction,
      `*/1`, no override) = 120s. Encoded that rule in `gen_consolidator_catalog.py` (`_staleness_budget`) so each
      catalog entry carries `staleness_budget_seconds`; `_entry_budget()` reads it (falls back to the legacy per-AG
      override then the global default). Fixes the false-degrade on all the slow-cadence consolidators (instruments /
      features / execution / strategy / ml / gas-fees) that previously used the 120s default. —
      `deployment-api@1a505c16` + 2 unit tests. UI unchanged (renders `index-age / budget` from the backend); help doc
      documents it.
- [x] [BACKEND] P1. ✅ **Coverage-expansion — DYNAMIC enumeration of ALL consolidators (operator-DECIDED 2026-07-10: all
      25, NOT market-data-first).** Endpoint now returns one `ConsolidatorHealth` per (kind,AG) across the full estate,
      driven by `consolidator_catalog.generated.json` (a projection of the deployment-service terraform consolidator
      locals, regenerated by `scripts/gen_consolidator_catalog.py`) — a NEW consolidator auto-appears with ZERO code
      change once the catalog is regenerated (`_load_catalog`/`_build_consolidators`/`_consolidator_health`). Honest
      nuance vs the todo's "live job/bucket census": the source is the generated terraform-projection catalog, not a
      live `gcloud run jobs list` census — same zero-code-change-on-add contract, but the catalog must be regenerated
      when terraform changes (documented on `ConsolidatorHealth`). — `deployment-api@14650f9`.
- [x] [UI] P1. ✅ **Surface the production verdict on the consolidator page** — `VerdictBadge` renders per (kind,AG)
      (`produced` / `producing` / `stale_output` / `empty` / `unknown`) alongside freshness + backlog, hover = the
      derivation detail. — `deployment-ui@15832cd`; the `fired_but_empty` verdict + its amber badge landed 2026-07-11
      (`deployment-ui@368ea8e6`), so the badge now covers the full vocabulary incl. the precise execution-join verdict.

### Per-consolidator views, dynamic list + tooltips (operator-decided 2026-07-10)

- [x] [UI] P1. ✅ **One view per consolidator (25 today), driven by the DYNAMIC list — not just 5 per-AG cards.** One
      `ConsolidatorCard` per (kind,AG) from the backend's `consolidators[]`, GROUPED by the fixed pipeline sequence
      (`instruments → market-data → features → ml → strategy → execution`;
      `groupKey()`/`CATEGORY_ORDER`/`categoryRank()`, gas-fees folded into market-data, all feature kinds unified), 4
      cards/row wide · 2 small · 1 mobile. A new consolidator appears automatically with no UI change. —
      `deployment-ui@15832cd`.
- [x] [UI] P1. ✅ **Metric documentation — REDIRECTED by operator (2026-07-11) from per-metric tooltips to a single
      top-of-tab `?` help dialog rendering an updatable Markdown doc.** Operator: "move the tooltips … to topside under
      help/? … or even best create new document that is directly rendered so we can update the doc when we change
      something." Built `ConsolidatorsHelp` (HelpCircle → Dialog → no-dep `Markdown` renderer) sourcing
      `docs/consolidators-help.md` (`.md?raw`), documenting every metric (rows / size / fed-by / index-age / backlog /
      verdict). Per-metric hover titles kept on the verdict + job/bucket where cheap. — `deployment-ui@15832cd`
      (`Markdown.tsx`, `consolidators-help.md`). Supersedes the per-metric-tooltip approach.
- [x] [DOCS] P2. ✅ **Consolidator/manifest docs updated — DONE 2026-07-11.** The shipped `docs/consolidators-help.md`
      documents every metric (rows/size/fed-by/index-age/backlog/oldest-pending/verdict incl. fired-but-empty + the
      run-summary/not-reporting state). Mirrored to codex: `/codex/05-infrastructure/manifest-consolidator-ssot.md`
      gained a "Cockpit data-correctness signals + `_index/latest.json` run summary" section (verdict vocabulary,
      per-cadence budget, backlog+oldest-pending, absolute snapshot, the latest.json contract + dynamic-enumeration
      source), and `/codex/02-data/availability-manifest-and-data-status.md` gained the sibling-`latest.json` note
      pointing to it. — PM plan flip (this commit). Phantom/reprobe docs stay with that separate, still-open item.

### Fan-in — oldest-unmerged-shard age (operator-SCOPED-DOWN 2026-07-11)

> **Operator (2026-07-11): "fed by N VMs" is ALREADY LIVE + backlog is already shown; the ONLY remaining fan-in signal
> is the AGE OF THE OLDEST UNMERGED SHARD — how long has a written-but-not-yet-absorbed shard been waiting, so we can
> tell how long the consolidator has been failing to merge properly.** The per-VM contributor NAME drill + Fleet
> cross-link is NOT wanted (at backfill scale it's thousands of VMs; the aggregate + this age signal is the useful
> part). Cheap: the SAME `_index/per_vm/*.parquet` prefix list already walked for backlog also carries each pending
> shard's `last_modified` → oldest-pending age = `now - min(pending shard mtimes)`.

- [x] [BACKEND] P2. ✅ **Oldest-unmerged-shard age from the shard mtimes — SHIPPED 2026-07-11.** `per_vm_shard_backlog`
      now returns a `PerVmShardBacklog` NamedTuple `(pending, total, oldest_pending_at)` — the oldest pending shard's
      mtime (`min` over the pending set) from the SAME single prefix list (no new walk), `None` when nothing pends.
      `ConsolidatorHealth.oldest_pending_shard_age_seconds` = `now − oldest_pending_at`. —
      `unified-trading-library@101e8f10` (`PerVmShardBacklog` exported from the facade, 2 new unit tests incl. the
      min-over-multiple case) + `deployment-api@1a505c16`.
- [x] [UI] P2. ✅ **Show oldest-unmerged-shard age on the card — SHIPPED 2026-07-11.** Backlog cell renders a second
      line "oldest {age}" (live-ticking forward like index age), turning red once it exceeds the cadence budget (merge
      stuck that long). Help doc entry updated. — `deployment-ui@368ea8e6` + `pw:L2 ✓` cockpit.spec.ts **O6**
      (`cockpit-consolidator-oldest-pending-*`).

### Consolidator self-reported run summary (`latest.json`) — operator-REDIRECTED #4 (2026-07-11)

> **Operator clarified (2026-07-11): the phantom/reprobe visibility below is a SEPARATE concern (and the phantom
> estate-coverage issue is Ikenna's, different again). The real #4 is: not all ~25 consolidators are LIVE right now —
> only some run. Have each LIVE consolidator publish a `latest.json` run summary, and WIRE THE CODE so a currently-dead
> consolidator emits the same data the moment it is fired up.** Because all ~25 Cloud Run jobs run the ONE shared
> `unified_trading_library.manifest_consolidator` module, instrumenting it once satisfies both halves — zero per-job
> change.

- [x] [BACKEND] P1. ✅ **Consolidator writes `_index/latest.json` every run — SHIPPED 2026-07-11.** `main()` in
      `manifest_consolidator.py` publishes the authoritative run summary each cycle (incl. no-op / failure, so
      `last_run_at` always reflects liveness):
      `{last_run_at, verdict(produced|empty|failed), shards_changed, rows_in/out/added, duration_ms, ...}` from the
      `ConsolidationReport`. Best-effort (`_write_latest_run_summary` mirrors `_write_stall_state` — a write failure
      logs + never crashes the cycle). One shared module → a dead consolidator starts reporting the instant it's fired,
      no per-job change. — `unified-trading-library@111592eb` + 3 unit tests (`_run_verdict`, shape, swallow-error).
- [x] [BACKEND] P1. ✅ **Endpoint reads `latest.json` — SHIPPED 2026-07-11.** `_read_latest_run()` per consolidator;
      `run_reporting` + `run_verdict`/`run_last_run_at`/`run_shards_changed`/`run_rows_added`/`run_duration_ms` on
      `ConsolidatorHealth`. When present the self-reported verdict is AUTHORITATIVE (`_authoritative_verdict`:
      produced→produced/producing, empty→fired_but_empty, failed→stale_output), superseding the WS-3 Cloud-Run-execution
      inference; absent → `run_reporting=false` (dead / not-yet-fired), never a fabricated all-clear. —
      `deployment-api@022bfebc` + 3 unit tests.
- [x] [UI] P1. ✅ **Surface the run summary + not-reporting state — SHIPPED 2026-07-11.** `RunSummary` renders "last run
      {age} · merged N · +M rows · {duration}" for live consolidators; a dead one shows "not reporting — consolidator
      not live yet". Help doc updated. — `deployment-ui@c97a769e` + `pw:L2 ✓` cockpit.spec.ts **O7** (live +
      not-reporting states).
- [x] [INFRA] P1. ✅ **Estate redeploy DONE — latest.json emitting in prod (operator un-deferred 2026-07-13; GCP only,
      AWS mirror dormant → same-shape later).** Pipeline-driven, not a manual build: the UTL LDR-push trigger had
      already built the base image containing `unified-trading-library@111592eb` (`:latest` digest `dcb489…`); bumped
      the MTDS Dockerfile `BASE_IMAGE_DIGEST` `e353…→dcb489…` + baselined a fresh transitive click CVE (PYSEC-2026-2132,
      `--ignore-vuln`; `click.edit()` unused) → `market-tick-data-service@96ce4311`; the MTDS trigger rebuilt
      `Evidence: cloudbuild=de50eace-6538-442d-aa9e-abf5dce59585` SUCCESS (`:latest`=`ccbc8462…`). Scoped to the **24
      LIVE jobs only** (ENABLED `*/1` crons) per operator — the 9 PAUSED (`gas-fees` + 8 `-legacy`) left untouched.
      Canary `market-data-cefi` updated+executed → SUCCESS + `_index/latest.json` written (schema v1); fanned out to the
      other 23 (`gcloud run jobs update --image`, 23/23 OK); **verified 24/24 live buckets carry a fresh `latest.json`**
      (timestamps 08:43–08:45Z, self-written each cron cycle), no breakage. The cockpit now reads `run_reporting=true`
      for the live estate.

### Dark data-correctness actors — phantom/reprobe VISIBILITY (SEPARATE from #4 above; detection ALREADY EXISTS)

> **NOT what the operator redirected #4 to (2026-07-11) — kept as a distinct, still-open item.** This is the
> phantom-audit + reprobe VISIBILITY (Slack-only results → queryable), independent of the consolidator `latest.json`
> above and of the phantom estate-COVERAGE issue (`issues/phantom_audit_estate_coverage_gap_2026_07_10.md`, Ikenna's).

> **Operator GO (2026-07-11): build the visibility (persist `latest.json` → read endpoint → surface). Confirmed this is
> INDEPENDENT of the still-OPEN estate-coverage issue** (`issues/phantom_audit_estate_coverage_gap_2026_07_10.md`,
> `status: open`, `resolved_by:` empty as of 2026-07-11 — Ikenna has NOT addressed it). Whether the phantom audit walks
> 5 or all 47 buckets is a SEPARATE concern (the open issue); we wire the plumbing to surface whatever it CURRENTLY
> covers, and when coverage expands the same UI shows more. The one requirement: the card states honest coverage/cadence
> so partial-or-weekly never reads as a false "all clear".
>
> **Confirmed: the phantom-audit + reprobe DETECTION already exists and is mature — the ONLY gap is that results aren't
> queryable (Slack-only). So this is "wire a thin persist + read endpoint", NOT "build detection".** Phantom =
> `dp-manifest-hygiene-full` (weekly `0 8 * * 0`) → `e2e-testing/scripts/audit/manifest_hygiene_daily.py --mode full` →
> `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --dry-run` (~10 false-positive guards,
> codex-canonical; `--apply` exists but the cron never passes it). Reprobe = `dp-reprobe-empty` (daily `0 9 * * *`) →
> `e2e-testing/scripts/audit/reprobe_new_empty_confirmed.py --reclassify-apply` (proof-gated
> `empty_confirmed → attempted_failed` auto-heal — **LIVE in prod**, capped 200/run + backup-before-write). Both
> terminate at `log_event → PubSub → alerting-service → Slack`; NO Firestore/DB. The candidate-CSV + issue-doc outputs
> target the PM git clone, which doesn't exist on the Cloud Run image → discarded on job exit.

- [x] [BACKEND] P2. ✅ **Persist a per-AG summary + read endpoint (phantom) — SHIPPED 2026-07-13.**
      `_write_phantom_audit_latest()` writes a stable `_index/phantom_audit_latest.json` (schema v1: phantom*count +
      generated_at + triage-JSONL link) to the AG's manifest bucket on every canonical AG audit (incl. phantom_count=0,
      honest all-clear), re-published with the real triage link on the dry-run path; leans on the existing
      `gs://central-element-323112-phantom-triage/triage*{ag}\_{ts}.jsonl`(zero new detection logic). deployment-api
      `\_audit_fields()`reads it per market-data/instruments entry (gated; absent = None).
      —`instruments-service@5d06c2d1` +`deployment-api@92442b13` + unit tests.
- [x] [BACKEND] P2. ✅ **Persist a per-AG summary + read endpoint (reprobe) — SHIPPED 2026-07-13.**
      `_write_reprobe_audit_latest()` writes a per-AG `_index/reprobe_audit_latest.json` (new_empties / disagreements /
      ambiguous / proven / reclassified + day + generated_at) to the AG's market-data bucket every run (dry-run OR
      `--reclassify-apply`), same GCS-JSON pattern + same deployment-api read path as phantom. —
      `e2e-testing@85d8d4ac` + `deployment-api@92442b13` + unit tests.
- [x] [UI] P2. ✅ **Surface on the consolidator page — SHIPPED 2026-07-13.** `AuditSummary` renders "phantoms N · {age}"
      (amber when > 0; timestamp red when the ~weekly audit is overdue — loud staleness) + "reprobe N disagree · M
      reclassified · {age}" (amber on disagreements) on market-data/instruments cards; absent audit → NO row (honest
      absence, never a fabricated 0). Tooltips + help-doc section explain phantom / reprobe-disagreement. —
      `deployment-ui@b0c68249`. `pw:L2 ✓` cockpit.spec.ts O8.

> **✅ Coverage-gap FINDINGS — VERIFIED 2026-07-10 (operator asked to verify before filing; done by reading source +
> live `gcloud`). Outcome: ONE genuine gap FILED, two downgraded to by-design:**
>
> - **FILED → `issues/phantom_audit_estate_coverage_gap_2026_07_10.md`** (data-pipeline scope, for Ikenna): phantom
>   audit walks only 5 hardcoded buckets (`_BUCKET_KIND_MAP` — market-data-{cefi,defi,tradfi} + instruments-sports +
>   market-data-tick-prediction); the cron never passes `--manifest-bucket`, so the rest of the estate —
>   instruments-{cefi,defi,tradfi} (VERIFIED: the 86,977-row / 64,227-`captured` cefi index I downloaded), market-data-
>   sports, gas-fees, lending-indices, oracle-prices, features/execution/… — is NEVER phantom-checked. Real
>   data-correctness coverage gap.
> - **WITHDRAWN (verified by-design, NOT bugs)**: (a) tradfi/prediction reprobe hooks never auto-heal — TRUE
>   (`reprobe_tradfi.py:75` / `reprobe_prediction.py:71` always `reached_source=False`), but deliberate (batch sources)
>   AND the cells are still DETECTED via the oracle (`ORACLE_EXPECTS_DATA`, `reprobe_new_empty_confirmed.py:247-250`);
>   (b) weekly phantom cadence — a deliberate cost tradeoff (full GCS walks; daily index-only checks still run).
> - **UI implication (kept)**: the panel MUST show HONEST cadence + coverage so a narrow/weekly audit never reads as a
>   false "all clear".

### Shipping gate (WS-3 — mirrors WS-1's closer)

- [ ] [REVIEW] P1. **QG both repos green + LOCAL verify the seam resolves live (Cloud Build deploy DEFERRED per operator
      — local-dev-only for now).** After the seam + fired-but-empty + stale-output + verdict badge land:
      `quality-gates.sh` green (deployment-api + deployment-ui + any UTL helper), run locally against live GCS, verify
      the endpoint returns the verdict for a known job **short-name** AND that the deployments detail popover's
      cross-link resolves 1:1 (end-to-end handshake with `deployment_full_estate_cost_provenance_2026_07_09.md`'s
      job→manifest bridge). Deploy at end-of-cockpit-plans. No `- [x]` on any WS-3 build todo until this closes.

### Cross-tab placement notes (NOT this plan — captured so we don't lose them)

- **Duplicate info across the two UIs is INTENTIONAL for now (operator, 2026-07-10)** — where the deployments page and
  this page (or the data-status tab) show the same underlying signal, they're almost always different AXES of it
  (liveness vs produced-vs-expected; coverage-trust vs rows-written-verdict). KEEP both while the UIs are being built;
  de-dupe only once they're properly built. Do NOT collapse a cross-tab overlap prematurely.
- **Denominator freshness has two facets, split by tab**: the _trust caveat on the coverage %_ ("denominator last
  computed Nh ago" / stale-warning) → **data-status tab** (owns coverage %); the _enumerator/catalogue JOB fired + on
  time_ → **deployments** (its Cloud Scheduler census). The _did-the-enumerator-actually-write-rows_ verdict IS in this
  page's seam above (enumerator/catalogue are data-producing jobs). **→ HANDED to Ikenna / data-status tab
  (2026-07-10)**: the trust-annotation (denominator-freshness caveat on the coverage %) is his to own on the data-status
  tab; hand-off message delivered via operator. NOT this plan to build.
- **Lambda run-time honesty (FYI from the hand-off)**: deployments is fixing `last_run_at = fn.last_modified` (deploy
  time, not invoke). The data-producing pipeline jobs are Cloud Run (GCP) + AWS Batch, NOT Lambda, so the seam likely
  never touches a Lambda run-time — but if it ever does, use CloudWatch `Invocations`, never deploy-time.

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- 2026-07-13 — **Phantom + re-probe visibility SHIPPED end-to-end (todos 313/319/324).** The two dark data-correctness
  actors now self-publish a stable per-AG summary the cockpit reads. **Writers**: the cross-AG phantom reconciler writes
  `_index/phantom_audit_latest.json` (phantom_count + triage link) to the AG's manifest bucket
  (`instruments-service@5d06c2d1`); the daily empty re-probe writes `_index/reprobe_audit_latest.json` (disagreements /
  reclassified / new_empties) to the AG's market-data bucket every run, dry-run included (`e2e-testing@85d8d4ac`) — both
  land in the SAME bucket the consolidator card reads, so no new plumbing. **Reader**: deployment-api `_audit_fields()`
  reads both per market-data/instruments entry (gated so features/execution/flat pay nothing; absent = None, honest), +7
  `ConsolidatorHealth` fields (`deployment-api@92442b13`). **UI**: `AuditSummary` renders "phantoms N · {age}" (amber
  when > 0, timestamp red when the ~weekly audit is overdue) + "reprobe N disagree · M reclassified · {age}"; absent
  audit → NO row, never a fabricated 0 (`deployment-ui@b0c68249`, `pw:L2 ✓` O8 + help-doc section). All 4 repos
  QG-green + strict-quickmerge. **Design note**: inline JSON writers with a documented blob-path convention (not a new
  UTL symbol) to avoid a UTL ship→propagate cycle across two consumer repos. The artifacts appear in prod the moment
  each audit job next runs — same "ship code now, artifact on next run" shape as the consolidator `latest.json`.
- 2026-07-13 — **WS-2 (merged-per-tick histogram) DESCOPED from this plan (operator 2026-07-13).** Its 3 P3 todos
  (store-decision / instrument-the-job / history-endpoint) kept surfacing as "remaining" on a workstream that was always
  🟡 nice-to-have AND contingent on another plan. Design is NOT lost: WS-2 must **ride WS-H's structured-progress
  event-facade spine** (a `report_progress({ts, shards_merged, rows_added, duration_ms})` typed event), NOT build a
  parallel GCS/Firestore store — so the histogram is a downstream consumer of WS-H. (Was: "tracked [in
  `deployment_observability_expansion_2026_07_08.md`] if/when WS-H ships" — that doc's WS-H section was **EXTRACTED OUT
  2026-07-13** [operator], "needs its own dedicated plan (operator will create when it's staffed)"; no plan currently
  tracks WS-H. [finding 183, synced 2026-07-14]) The v1 inferred session-only sparkline stays as-is.
- 2026-07-13 — **UI polish: content-sized consolidator metric columns.** The card's metric row was a fixed
  `grid-cols-5`, forcing every metric to a rigid 1/5 share → the widest one (`index age`, e.g. `41s / 24.0h`) truncated
  to `24.…` while `rows`/`fed by` wasted their column. Replaced with a content-sized `flex flex-wrap` row (`Stat` + the
  index-age/backlog cells swap `min-w-0`→`shrink-0`) so each metric takes exactly the width it needs and the row wraps
  as a whole rather than ellipsizing mid-value. Verified in mock-mode (full text renders, 0 console errors) + smoke
  specs green. — `deployment-ui@e40f8015`.
- 2026-07-13 — **LOCAL VERIFY of the live stack → found + fixed 2 real bugs in the shipped #4 endpoint.** Ran
  deployment-api on :8010 (live GCS) + deployment-ui on :5196 (proxy). The Consolidators tab renders the real estate
  correctly (25 cards, pipeline groups, per-card run-summaries, gas-fees "not reporting", 0 console errors — screenshot
  captured). Two bugs surfaced (both in prod's `deployment-api@022bfebc`): (1) `_read_latest_run` **500'd on a missing
  `latest.json`** — the provider `NotFound` (404) isn't an `OSError` so it escaped the catch → fixed with a
  `get_blob_metadata` existence check first; (2) `_authoritative_verdict` trusted the **per-CYCLE**
  `run_verdict='empty'` (a no-op cycle reports empty even on a fully-populated index) → 5M-row consolidators showed
  "empty" and idle buckets showed "fired_but_empty" → fixed by reconciling against the real `index_row_count`.
  Verified-live distribution after the fix: **14 produced / 10 empty / 1 stale_output** (market-data-defi, 8 shards
  waiting), 24 reporting + gas-fees not-reporting. — `deployment-api@ce9f5fba` + updated unit tests. (NOTE: the deployed
  prod deployment-api SERVICE carries these 2 bugs until its own service redeploy — a separate deferred deploy; the
  local stack the operator views has the fix.)

- 2026-07-13 — **ESTATE REDEPLOY DONE — `latest.json` live in prod across the 24 running consolidators (operator
  un-deferred).** Corrected the operator's mental model first (a green LDR→main does NOT auto-run in the jobs: MTDS pins
  the UTL base image by digest, and Cloud Run JOBS pin the image digest at deploy time — codex `ci-cd-flow.md` "Image
  deploy-hygiene"). Then executed the pipeline-aligned path: the UTL LDR-trigger had already built the base image with
  `@111592eb` (`:latest`=`dcb489…`); bumped MTDS `BASE_IMAGE_DIGEST`→`dcb489` (`market-tick-data-service@96ce4311`),
  MTDS trigger rebuilt (build de50eace (full id at line 263) SUCCESS, `:latest`=`ccbc8462…`). Scoped strictly to the
  **24 LIVE jobs** (ENABLED `*/1` crons) per operator "only the ones running now"; the 9 PAUSED (`gas-fees` + 8
  `-legacy`) untouched. Canary `market-data-cefi` → SUCCESS + `latest.json` written; fanned out `gcloud run jobs update`
  to the other 23 (23/23 OK); verified **24/24 live buckets carry a fresh `latest.json`** (08:43–08:45Z), no breakage.
  One incidental finding handled with operator approval: a fresh transitive **click CVE PYSEC-2026-2132**
  (command-injection in `click.edit()`, which MTDS never calls) was blocking the MTDS gate → baselined via
  `--ignore-vuln` (the repo's existing "awaiting upstream fix" pattern). AWS Batch mirror stays dormant → same-shape
  when it comes alive.

- 2026-07-11 — **#4 REDIRECTED + SHIPPED: consolidator self-reported `latest.json` run summary.** Operator clarified #4
  is NOT phantom/reprobe (separate) but consolidator liveness: not all ~25 are live now; have the live ones publish a
  `latest.json` run summary + wire the code so dead ones do too when fired. Since all 25 jobs run the one shared
  `manifest_consolidator` module, instrumented `main()` once. Shipped: **UTL `111592eb`** (writes `_index/latest.json`
  each run — verdict/shards/rows/duration; best-effort), **deployment-api `022bfebc`** (`_read_latest_run` +
  `run_reporting`/`run_verdict`/… fields; self-reported verdict is authoritative, degrades to not-reporting for dead
  ones), **deployment-ui `c97a769e`** (per-card run summary + "not reporting — consolidator not live yet"; help doc;
  pw:L2 **O7**). All QG-green + strict-quickmerge. Operator decisions: content = run-summary/production verdict;
  **estate redeploy DEFERRED** to the end-of-cockpit-plans window (until then prod shows "not reporting" everywhere —
  honest). The phantom/reprobe visibility item is kept SEPARATE + still open.

- 2026-07-11 — **WS-3 signals SHIPPED (fired-but-empty, per-cadence budget, oldest-pending shard age).** Three repos in
  dep order: **UTL `101e8f10`** (`per_vm_shard_backlog` → `PerVmShardBacklog` NamedTuple with `oldest_pending_at`,
  facade-exported), **deployment-api `1a505c16`** (`_is_fired_but_empty` execution-join verdict, catalog-sourced
  per-(kind,AG) `_staleness_budget`, `oldest_pending_shard_age_seconds`), **deployment-ui `368ea8e6`** (amber "fired ·
  empty" badge + estate count, oldest-pending age on the backlog cell, help doc for all three signals; fixed the stale
  O1/O5/each-tab consolidator playwright specs that the 15832cd redesign had broken with pre-redesign per-AG testids +
  added **O6** as the fired-but-empty/oldest-pending regression). All three QG-green + strict-quickmerge verified; UI
  playwright cockpit suite green for consolidators. **FINDING fixed in passing** (was blocking UTL QG): the UTL test
  fixture `tests/fixtures/cloud-providers.yaml` still carried the `gas-fees` storage kind that the real/packaged yaml
  removed 2026-07-12 — the estate-cleanup commit `3936f74` claimed to sync test files but missed this fixture, reddening
  `test_bucket_naming_cell_sweep` (collection read the fixture-with-gas-fees, runtime resolved against
  packaged-without). Synced the fixture (verified `test_domain_client_readers` uses hardcoded bucket names, not
  `resolve_bucket_name(kind="gas-fees")`, so no dependency broke). **Still OPEN in WS-3**: fan-in contributor-VM drill
  is DROPPED (operator scoped to oldest-shard age only); phantom/reprobe visibility (API+UI scaffold, independent of the
  still-open coverage issue); the [DOCS] codex mirror (help doc shipped; codex mirror pending). Two PRE-EXISTING
  deployment-inventory playwright failures (`cockpit.spec.ts:222` batch-137-OOM row, `:267` composite-health) are
  unrelated to consolidators (another agent's deployments-tab mock) — flagged to operator, not fixed here.

- 2026-07-11 — **WS-3 partial SHIP + card redesign (interactive, this slot).** Shipped to live-defi-rollout in dep
  order: **UTL `fd219fe`** (the backlog native-mtime fix above), **deployment-api `14650f9`** (catalog-driven
  per-consolidator estate ~25 jobs + absolute `index_row_count`/`index_size_bytes` via a cheap parquet-FOOTER read —
  `_RangedIndexReader` reads only the footer via ranged GETs, e.g. 14M rows from a 219 MB index over ~490 KB),
  **deployment-ui `15832cd`** (per-consolidator cards on one metrics row, hero backlog chart w/ Y-axis + legend,
  pipeline-order grouping, 1/2/4 grid, `?` help dialog + `Markdown` renderer + `consolidators-help.md`), **ml-service
  `4ad7208`** (unrelated empty-string ratchet fix that was blocking its QG). All four QG-green + strict-quickmerge
  verified. FLIPPED: coverage-expansion (dynamic catalog), verdict badge, per-consolidator dynamic views, metric-doc
  (redirected tooltips→help-doc). NEW operator ask this session, now shipped: **absolute index row-count + file-size**
  per fetch (wasn't an original todo). STILL OPEN in WS-3 (honest): precise `fired_but_empty` (needs per-run execution
  seam), per-(kind,AG) cadence stale-output budget, fan-in contributor-VM drill + cross-link, phantom/reprobe
  persist+read+surface, the [DOCS] codex update, and both [REVIEW] deploy gates (deploy DEFERRED per operator —
  local-dev-only until all cockpit plans land).

- 2026-07-10 — **BUG FOUND + FIXED (surfaced by operator's "what does 0/9 mean?" question during the live UI review).**
  WS-1's `per_vm_shard_backlog` (UTL `_state.py`) computed `pending` off the WRAPPER `list_blobs`, whose returned
  `BlobMetadata.last_modified` is **always `None`** (the list op doesn't map mtimes) — so `pending` was **structurally
  always 0** against real GCS (e.g. market-data-defi showed `0/9` when 9 shards were genuinely newer than the index).
  The WS-1 unit tests passed only because they mocked string mtimes. Fixed: read mtimes from the NATIVE client's list
  (`client._client.list_blobs` → `blob.updated` populated per object in ONE call, mirroring
  `consolidated_blob_age_sec`); wrapper path kept as the non-GCP fallback. Verified live: defi now `9/9`, tradfi
  `3/3 → producing` (the `producing` verdict was previously unreachable). **TODO before commit**: a regression test
  using the real `BlobMetadata` shape (mtime-absent) so this can't silently regress; note the deeper gap that the
  wrapper `list_blobs` never populates `last_modified` (a UTL improvement candidate). **SHIPPED
  `unified-trading-library@fd219fe`** (2026-07-11, live-defi-rollout; the pre-commit `# pyright: ignore[reportAny]` on
  `_state.py:477` + UTL QG green).

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
- 2026-07-10 — Operator decisions folded in. (1) **Local-dev-only for now** — deployment-api + UI run locally against
  live GCS; Cloud Build deploy DEFERRED to end-of-cockpit-plans (operator is the sole viewer, local iteration is
  faster). Both REVIEW gates (WS-1, WS-3) reframed to local verify. (2) **Join key AGREED** with the deployments agent =
  the VERBATIM Cloud Run short-name (`job.name.rsplit("/",1)[-1]`), NOT the (kind,AG) tuple — one string read verbatim
  both sides, no fuzzy-parse drift; this page owns the `short-name → (kind,AG) → partition` decode as SSOT, deployments
  passes kind+AG as hint only. **WS-3 seam UNBLOCKED.** (3) WS-2 (v2 histogram) still operator-undecided → stays
  deferred. (4) Denominator-freshness trust-annotation HANDED to Ikenna (data-status tab). (5) WS-3 prune (phantom/
  reprobe visibility, coverage-expansion scope, fan-in) still awaiting operator's keep/drop calls.
- 2026-07-10 — More operator decisions. **Fan-in AGREED — wire it.** **Coverage = ALL 25 consolidators + the list must
  be DYNAMIC** (live job/bucket census, never hardcoded; a new consolidator auto-appears) → coverage-expansion bumped
  P2→P1 + reframed; added **[UI] 25 per-consolidator views** (grouped, dynamic) + **[UI] tooltips on every metric**
  (hard requirement — don't let the user assume) + a **[DOCS] deferred** todo (update manifest-consolidator +
  availability- manifest codex AFTER the UI lands). Downloaded a live index for operator inspection —
  `instruments-store-cefi-prd/_index/availability_index.parquet` (2.8 MB, 86,977 rows × 41 cols; capture_status captured
  64,227 / empty_confirmed 22,630 / attempted_failed 81 / expected_unattempted 39). Phantom-audit + reprobe-empty "do
  the scripts already exist" investigation running (background) — findings + gap-scoping to follow.
- 2026-07-10 — Phantom/reprobe deep-audit DONE. **Detection ALREADY EXISTS + is mature** (phantom =
  `reconcile_phantom_manifest_rows_all.py` via `dp-manifest-hygiene-full`; reprobe = `reprobe_new_empty_confirmed.py`
  via `dp-reprobe-empty`, whose proof-gated auto-heal is LIVE in prod) — the gap is VISIBILITY only (both
  Slack-terminal; phantom has ONE unwired GCS triage artifact, reprobe has none). Dark-actors section reframed "decide
  whether to build" → 3 todos (persist per-AG `latest.json` + read endpoint + UI surfacing; ZERO new detection).
  **Escalated 4 coverage-gap FINDINGS** (data-correctness, not this UI plan): tradfi/prediction reprobe hooks are STUBS
  (can't self-heal wrong empties), DeFi per-data-type buckets unaudited, phantom covers 5 of ~20+ consolidator buckets,
  weekly cadence → up-to-7d stale. Candidate issue doc pending operator decision.
- 2026-07-10 — VERIFIED the phantom/reprobe gap-findings MYSELF (operator: verify before filing, don't delegate) — read
  the source + live `gcloud`. Outcome: tradfi/prediction reprobe-stub finding **WITHDRAWN** (mechanically true but
  deliberate design — oracle still detects via `ORACLE_EXPECTS_DATA`, `reprobe_new_empty_confirmed.py:247-250`);
  weekly-cadence **WITHDRAWN** (deliberate cost tradeoff); phantom **ESTATE-COVERAGE gap CONFIRMED + FILED** →
  `issues/phantom_audit_estate_coverage_gap_2026_07_10.md` (`_BUCKET_KIND_MAP` walks only 5 buckets, cron never passes
  `--manifest-bucket` → instruments-{cefi,defi,tradfi} incl. the verified 86,977-row cefi index, gas-fees /
  lending-indices / oracle-prices, features/execution/… never phantom-checked). For Ikenna (data pipeline).

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — LOCAL plan built interactively; both [REVIEW] gates are
  explicitly deferred by a dated operator decision (2026-07-10, local-dev-only until all cockpit plans complete).
- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) -- swapped the archived cost-provenance plan for the
  deployment-ui Cockpit page (the Consolidators tab's real frontend home), pairing it with the existing deployment-api
  backend source path.
- **na-eligibility-audit 2026-08-06 (ui tranche, dispatch agt-a6d668)**: KEEP-NA, valid — same as 2026-07-30; LOCAL plan
  with both REVIEW gates explicitly deferred by a dated operator decision (2026-07-10, local-dev-only until all cockpit
  plans complete).
- **context-scout 2026-08-07**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **na-eligibility-audit 2026-08-07 (ui tranche)**: KEEP-NA, stale item closed — the WS-3 "seam" umbrella todo was stale
  (its 4 concrete sub-parts are all already individually shipped, see the closed todo above). Doc otherwise stays NA —
  the 2 remaining open items (WS-1 + WS-3 shipping gates) are both explicitly deferred by the same dated 2026-07-10
  operator decision (local-dev-only until all cockpit plans complete).
- **na-eligibility-audit 2026-08-17 (ui tranche)** [body-hash:65529ba73a1af7cc]: KEEP-NA, valid — both open [REVIEW]
  gates cite the same explicit dated 2026-07-10 operator ruling (Cloud Build deploy deferred until all cockpit plans
  complete); neither is fully done (deploy step + one cross-link check unverified in the Progress Log), so RECLASSIFY
  does not apply. 5th consecutive audit pass reaching this same verdict.
- **context-scout 2026-08-19**: re-verified context_scope, no change needed (5 entries) — the 2026-08-18 `last_updated` bump was a plan-reconcile metadata-date correction only, no body content changed; all 5 paths still resolve.
