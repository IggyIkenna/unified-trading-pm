---
doc_type: plan
title: Manifest consolidator + GCS lifecycle cost optimization
summary:
  Tracks the cost-optimization thread from an interactive cost-analysis session (2026-08-16) — a Compute-Flexible-CUD
  sizing question that widened into GCS bucket lifecycle policy correctness, manifest-consolidator resource sizing, and
  cost-gain tracking. Read Progress Log for the full evidence trail before acting on any todo.
status: active
nature: design
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, unified-trading-library, deployment-api, deployment-ui]
scope: [engineer, admin]
tags: [cost, gcs-lifecycle, manifest-consolidator, terraform, billing, coldline]
related:
  [
    /codex/05-infrastructure/gcs-lifecycle-policies.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/05-infrastructure/billing-cost-observability.md,
    /plans/active/issues/deployment_service_prod_terraform_drift_2026_08_07.md,
    /plans/active/issues/prod_terraform_drift_backlog_reconcile_2026_07_24.md,
    /plans/active/consolidator_throughput_backlog_monitor_2026_07_09.md,
    /plans/active/issues/manifest_consolidator_job_name_registry_mismatch_2026_08_15.md,
    /plans/archive/2026_08/honest_coverage_and_data_status_rollup_health_2026_08_16.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-20"
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [deployment_service_prod_terraform_drift_2026_08_07]
source: [interactive cost-analysis session, 2026-08-16]
assigned_role: infra
effort: medium
drift_direction: advance-code
context_scope:
  [
    /codex/05-infrastructure/gcs-lifecycle-policies.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf,
    deployment-service/deployment_service/cloud_run_job_registry.py,
    /codex/05-infrastructure/billing-cost-observability.md,
  ]
---

# Manifest consolidator + GCS lifecycle cost optimization

> **LOCAL / human plan** — built interactively, NOT AO-dispatched (this is judgment-call-heavy investigative/infra work
> touching prod, not a bounded worker todo). Originated from a Compute Flexible CUD sizing question that widened into
> three real findings. **Read the Progress Log before doing anything below** — several apparent action items are
> BLOCKED on a pre-existing, larger issue this session discovered.

## Background (why each thread exists)

1. **GCS lifecycle policy correctness**: all 105 buckets in `central-element-323112` were audited (background agent,
   read-only). 52 working-data buckets (tick/instruments/features/ml-store/execution-store/strategy-store/
   portfolio-state/config-store/deployment-state) carry an identical whole-bucket `SetStorageClass→COLDLINE age=60`
   rule that contradicts `gcs-lifecycle-policies.md`'s stated intent (raw pipeline data should be exempt, governed by
   manifest retention only). Operator wants these stripped — MDPS/tick-data reads are about to scale up and Coldline
   retrieval fees would bite once data crosses 60 days (currently mostly fresh — see Progress Log for full economics).
2. **Manifest-consolidator cost**: ~$5,020/30d (Cloud Run CPU+memory across ~20-25 jobs). A 2026-07-30 cadence fix
   (`*/1`→hourly for 12/18 jobs) already banked ~35% (~$2,190/mo) — confirmed via billing before/after. Two further
   candidate levers identified: resource right-sizing (4vCPU/16Gi default looks oversized vs a "~5-30s typical" code
   comment) and an unshipped 10-jobs→5-per-asset-group consolidation the SSOT doc itself proposes.
3. **Operator correction (2026-08-16, mid-session)**: no heavy I/O (GCS reads across many objects/buckets) from the
   laptop session — must run on a VM if genuinely needed. This changed how todo 2 below gets resolved — NOT via a new
   data pull.

## Todos

- [x] ✅ [REVIEW] P1. **Open the Consolidators cockpit tab (deployment-ui, already shipped) and read each of the 18
      jobs' `run_duration_ms` against its `timeout_seconds` override**, AND cross-reference against the Cloud Run
      execution's own wall-clock (start-to-finish, not just the in-process `duration_ms` stamp — see hypothesis below).
      Done-when: a table of (job, p50/p95 duration_ms, Cloud-Run-execution wall time, timeout_seconds, cpu, memory)
      for all 18 jobs, flagging any job whose duration is a poor match for its allocation.
      - **Already resolved without any GCS read** (terraform-comment archaeology, 2026-08-16): 3-4 buckets
        (`market-data-{defi,cefi,tradfi}`, `instruments-sports`) are NOT oversized — dated incident comments in
        `manifest_consolidator_scheduler.tf` show real measured merges of 7-57 minutes, justifying their existing
        8vCPU/32Gi overrides. Don't touch these. The open question is only the ~14 buckets still on the 4vCPU/16Gi
        default with no override and no incident commentary (features-*, strategy, execution, ml-training-artifacts,
        tradfi/prediction instruments) — genuinely unmeasured, could be fast or could be silently slow.
      - **New hypothesis to test on the VM, not assumed**: fleet-wide sanity check (268K executions/30d ÷ 192.99M
        vCPU-sec ≈ 720 vCPU-sec/execution ≈ ~180s wall-time on a 4vCPU job) is already far past "~5-30s typical" as an
        AVERAGE — but `duration_ms` is stamped in-process by `manifest_consolidator.py` and excludes Cloud Run
        cold-start/image-pull time. If cold-start is a meaningful share of the billed time, the fix is fewer-but-longer
        invocations (cadence/cold-start amortization), NOT cutting CPU/memory — cutting memory blind on this codebase
        has caused real OOM incidents before (see manifest-consolidator-ssot.md's 44GB-RSS incident) for zero benefit
        if cold-start turns out to be the real driver. Confirm which it is before proposing any resource cut.
      - **RESOLVED 2026-08-16 (interactive session, direct measurement)** — see full Progress Log entry below for the
        complete per-bucket table, the "only 1 of 18 jobs actually has a cpu/memory override" correction (the plan's
        own "3-4 buckets already justified" framing above was wrong — ground-truthed against the live `.tf` maps), the
        confirmed cold-start-dominated verdict for all genuinely-light buckets (no resource change), and a live P1
        incident found + fixed (`market-data-cefi` failing every hourly cycle on a 1800s timeout against a 161K-shard
        backlog) — resolved via a live `gcloud run jobs update` stopgap + `.tf` codification, verified green.
- [x] ✅ [INFRA] P2. BLOCKED-ON:deployment_service_prod_terraform_drift_2026_08_07 — **RESOLVED 2026-08-16 (separate
      interactive session from the one that produced most of this doc's other entries — see the new Progress Log
      entry at the bottom).** Re-ran the drift review fresh (not trusting the stale 36/17/4 framing per that doc's own
      warning); it had shrunk to 8-add/12-change/0-destroy on its own, plus 2 NEW live-vs-committed capacity/cadence
      gaps beyond the already-known meta-watchers one — found + fixed both, applied everything safe, full detail in
      `deployment_service_prod_terraform_drift_2026_08_07.md`. The block is genuinely lifted.
- [x] ✅ **EXTRACTED 2026-08-17 (na-eligibility-audit, infra tranche) → `infra_satellite_ao_dispatch_batch18_2026_08_17.md`
      item 6 (combined with the near-duplicate instance of this same todo below and the Cost-gain tracking todo
      further down — all one dispatched item).** Not yet executed — tracked there. [INFRA] P2. **Author the Terraform diff for the 52-bucket lifecycle strip** — **PARTIALLY DONE 2026-08-16**
      (same session as the drift resolution above): only `portfolio-state-*` → STRIP shipped + applied — the one call
      with unambiguous operator-decision evidence already in this doc's text. Did **NOT** attempt the other ~50
      working-data buckets this todo's own "once the above unblocks" framing implied were ready to go: the "full
      bucket classification (105/105, STRIP/KEEP/UNCLEAR)" the Progress Log entry below flags as "not yet copied into
      this doc's body" is STILL not in writing anywhere in this repo (checked fresh) — beyond `portfolio-state`→STRIP
      and `recon`→KEEP (already the no-op default) and the named UNCLEAR set, there's no written record to extend the
      strip against, so the rest stays unguessed. Mechanism is shipped and ready either way —
      `canonical_buckets.tf`'s blanket `lifecycle_rule` is now a `dynamic` block keyed by a `canonical_strip_lifecycle_kinds`
      local; adding a kind strips it, zero other code changes needed once the missing table exists. See the new
      Progress Log entry for the full account + a new `[OPERATOR]` follow-up asking for that table.
      - **RESOLVED 2026-08-16 (interactive session, direct measurement)** — see full Progress Log entry below for the
        complete per-bucket table, the "only 1 of 18 jobs actually has a cpu/memory override" correction (the plan's
        own "3-4 buckets already justified" framing above was wrong — ground-truthed against the live `.tf` maps), the
        confirmed cold-start-dominated verdict for all genuinely-light buckets (no resource change), and a live P1
        incident found + fixed (`market-data-cefi` failing every hourly cycle on a 1800s timeout against a 161K-shard
        backlog) — resolved via a live `gcloud run jobs update` stopgap + `.tf` codification, verified green.
- [x] ✅ **CLOSED 2026-08-17 (na-eligibility-audit, infra tranche) — gate condition satisfied.** This todo's own
      done-when ("the drift issue is resolved... OR...") is now true: `deployment_service_prod_terraform_drift_2026_08_07.md`'s
      todo 1 is `[x] ✅ RESOLVED 2026-08-16` (full apply landed, live-verified 0-diff), and this SAME doc's own todo
      above (BLOCKED-ON:deployment_service_prod_terraform_drift_2026_08_07, the duration-vs-allocation review) already
      recorded the block as genuinely lifted the same day. ~~BLOCKED-ON:deployment_service_prod_terraform_drift_2026_08_07
      — Do not edit `manifest_consolidator_scheduler.tf`... until the existing pending drift is resolved.~~
- [x] ✅ **EXTRACTED 2026-08-17 (na-eligibility-audit, infra tranche) → `infra_satellite_ao_dispatch_batch18_2026_08_17.md`
      item 6 (near-duplicate of the earlier instance of this same todo above — same underlying task, combined into one
      dispatched item, not extracted twice).** Not yet executed — tracked there. [INFRA] P2. **Author the Terraform diff for the 52-bucket lifecycle strip** once the above unblocks. Bucket list +
      per-bucket disposition (STRIP/KEEP/UNCLEAR) is in the Progress Log below — do not re-derive, the classification
      is done. Two operator-facing calls already made and documented (not to be silently reversed): `portfolio-state-*`
      → STRIP (live risk state, not a report); `recon-*` → KEEP (report-shaped despite being on the operator's
      original strip list — see Progress Log reasoning). 5 buckets (`backtest-results`, `alerting-service`,
      `commodity-signals-batch`, `pnl-attribution-output`) remain genuinely UNCLEAR — get an explicit operator call
      before including/excluding them, do not guess. Done-when: `.tf` diff drafted, `quality-gates.sh`-green,
      shipped via quickmerge (code only — `tofu apply` stays operator-executed, matching this repo's existing
      pattern of "authored, pending operator apply").
- [x] ✅ [INFRA] P2. BLOCKED-ON:deployment_service_prod_terraform_drift_2026_08_07 — **RESOLVED 2026-08-16** (the
      blocker doc itself, full detail there). This diff shipped as a `-target`-safe, QG-green, dirty-deps-carve-out
      commit — see the next todo's evidence.
- [x] ✅ [INFRA] P2. **Author the Terraform diff for the canonical-bucket lifecycle exemption set** — `deployment-service@2995d0cf`
      (2026-08-17, direct-push dirty-deps carve-out, `unified-api-contracts` still blocked at ship time). Discovered
      while authoring this that the WHOLE dynamic per-kind exemption mechanism (`canonical_strip_lifecycle_kinds`,
      the kind-resolver locals, the `dynamic "lifecycle_rule"` block) was already live in production for
      `portfolio-state` via an earlier targeted `tofu apply`, but its `.tf` source was never committed — same drift
      class as the market-data-cefi incident, caught before it could silently revert on a future blanket apply.
      **Corrected the terminology confusion this plan's own comment created**: `canonical_strip_lifecycle_kinds` is
      an EXEMPTION list (membership = rule stripped OFF = stays hot), not a "gets cooled" list — the classification
      table's "STRIP → COLDLINE@60" Rule column described the pre-existing blanket default these buckets would fall
      to if left unclassified, not the target state. **Operator resolved 2026-08-17**: the full 47-bucket raw
      pipeline/working-data estate stays EXEMPT (always-hot, governed by manifest retention only) — added the
      remaining 12 yaml-derived kinds (market-data, market-data-tick-prediction, instruments-store,
      instruments-store-prediction, features, features-sports, features-calendar, ml-store, execution-store,
      strategy-store, strategy-store-prediction, config-store) plus `alerting-service`/`features-commodity`
      (commodity-signals-batch) to `canonical_strip_lifecycle_kinds`, and removed `uts-{env}-deployment-state`'s
      separate hand-written `lifecycle_rule` block in `main.tf` directly (not part of the yaml-derived for_each).
      `backtest-results` (not in `cloud-providers.yaml`, TF-unmanaged, no `.tf` representation exists) fixed live
      via a direct bucket-level lifecycle-clear instead — confirmed empty rule set after. `pnl-attribution-output`
      resolved SEPARATELY (see entry below) — NOT a lifecycle-rule question. QG green (full run, exit 0, sentinel
      `78dfe2ef` == HEAD at push time).
- **[INFRA] P3. CANCELLED — SUPERSEDED 2026-08-17 (operator rejected, see the 2026-08-17 Progress Log entry
  below).** The 10(IS+MTDS)+8(Group B)=18-jobs→5-per-asset-group consolidation was verified NOT shipped and NOT a
  pure Terraform regroup, then explicitly rejected by the operator on architectural grounds (combining buckets into
  one container invocation means sizing RAM for the worst-case bucket and running sequentially — directly
  contradicts the already-confirmed finding that per-bucket resource sizing is what's actually working, and would
  make the market-data-cefi class of incident easier to reproduce, not harder). Do not resurrect without new
  evidence changing the RAM/time tradeoff.
- [x] ✅ **EXTRACTED 2026-08-17 (na-eligibility-audit, infra tranche) → `infra_satellite_ao_dispatch_batch18_2026_08_17.md`
      item 6 (folded into the same dispatched item as the Terraform-diff todos above — sequential follow-on, not
      independent).** Not yet executed — tracked there. [REVIEW] P3. **Cost-gain tracking** — after any change above ships, re-run the same `bq query` shape used to
- **[INFRA] P3. CANCELLED — SUPERSEDED 2026-08-17 (operator rejected, see the 2026-08-17 Progress Log entry
  below).** The 10(IS+MTDS)+8(Group B)=18-jobs→5-per-asset-group consolidation was verified NOT shipped and NOT a
  pure Terraform regroup, then explicitly rejected by the operator on architectural grounds (combining buckets into
  one container invocation means sizing RAM for the worst-case bucket and running sequentially — directly
  contradicts the already-confirmed finding that per-bucket resource sizing is what's actually working, and would
  make the market-data-cefi class of incident easier to reproduce, not harder). Do not resurrect without new
  evidence changing the RAM/time tradeoff.
- [ ] [REVIEW] P3. **Cost-gain tracking** — after any change above ships, re-run the same `bq query` shape used to
      measure the 2026-07-30 cadence fix (before/after daily cost split on `resource.name LIKE '%manifest-consolidator%'`
      / the relevant bucket set in `billing_export.gcp_billing_export_resource_v1_016B25_109840_AF2ACB` — table name
      corrected 2026-08-18, was previously mis-transcribed as `..._v1_resource_...`) to confirm the actual $ delta
      matches the estimate. BigQuery aggregate queries are NOT the I/O this plan avoids — only raw per-object GCS reads
      are. **Interim check run 2026-08-18** (an early look, not the full done-when — see Progress Log for the raw
      table and why 1 day is not enough yet): the previously-EXTRACTED `infra_satellite_ao_dispatch_batch18_2026_08_17.md`
      item 6 dispatch for this todo is now redundant for that first pass — re-un-extracted here so this plan's own
      todo tracks the real remaining work (re-check once ~1 week of post-2026-08-17 data exists). Done-when: a clean
      multi-day before/after $/day table exists with the fix's effect separable from normal day-to-day variance.
- [x] ✅ [OPERATOR] P1. **Resolve the pre-existing `deployment_service_prod_terraform_drift_2026_08_07` blocker itself**
      — **RESOLVED 2026-08-16**, full detail in that doc (not duplicated here); the client-reporting-batch destroy,
      both Secret IAM destroys, and the meta-watchers memory question all confirmed moot/resolved, plus 2 new
      instances of the same live-vs-committed capacity gap found + fixed.
- [x] ✅ [INFRA] P1. **Ensure VMs exit if their AG's manifest consolidator is down mid-run, not just at boot** (operator
      finding, 2026-08-16 session: "ensure VMs exit if their consolidator is down for the AG relevant to them, to avoid
      VMs not knowing what their completion status should be — should be a hard rule in the code if not already").
      Ground-truth investigation confirmed the gap was real: `assert_consolidator_healthy` (UTL
      `manifest_writer/_state.py`) is only reached (a) as a side effect of callers that repeatedly call
      `read_availability_index()` (e.g. MDPS's per-date `dependency_checker`), never as a designed periodic mechanism,
      and (b) via `setup-data-pipeline-vm.sh`'s §5b "OOM preflight", which is a ONE-TIME check at VM boot (hand-rolled
      `gcloud storage objects describe`, not a call to `assert_consolidator_healthy` — confirmed the SSOT doc's
      "should wrap this" aspiration never shipped; corrected there, see below). A write-only backfill VM that never
      re-reads the manifest during its run had ZERO ongoing consolidator-health signal for the rest of a multi-hour
      backfill. **Fix shipped**: `deployment-service@583091c593` (`live-defi-rollout`) — added an opt-in periodic
      watchdog to the shared VM-side wrapper `vm-exec-with-gcs-tee.sh` (used by `_launch_with_tee`, the seam nearly
      every launcher routes through), gated on a new `CONSOLIDATOR_WATCHDOG_BUCKET` env var (empty = fully disabled,
      zero behavior change for launchers that don't opt in). It re-checks the same bucket's manifest staleness every
      `CONSOLIDATOR_WATCHDOG_INTERVAL_SEC` (default 900s) for the wrapped command's WHOLE lifetime and, on breach past
      `CONSOLIDATOR_WATCHDOG_BUDGET_SEC` (default 86400s, mirrors `MANIFEST_CONSOLIDATED_STALENESS_SEC`), SIGTERMs
      (SIGKILL after a 5s grace) the task and forces the terminal exit code to 78 (EX_CONFIG) — the SAME code the
      one-time boot preflight already used for this exact condition. This is a loud-fail HARD exit (no
      warn-and-continue), matching the SSOT's own "Liveness + health contract" default; deliberately does NOT consult
      `MANIFEST_ALLOW_STALE_FALLBACK` (that flag only gates the READER's per-VM-shard fallback merge, a different
      concern). `setup-data-pipeline-vm.sh` wires the opt-in automatically for the exact launcher population its
      existing §5b preflight already covers (`VM_SERVICE=market_tick_data_service && VM_OPERATION=download`,
      non-test — the ~20 MTDS download backfill launchers). Tests: new
      `deployment-service/tests/unit/test_consolidator_watchdog_vm_wiring.py` (bash -n syntax + text-invariant +
      operator-extraction functional checks, mirroring the proven `test_spot_preemption_signal_coverage.py` pattern
      for this same class of un-sourceable VM bootstrap script). Also corrected
      `/codex/05-infrastructure/manifest-consolidator-ssot.md`'s stale "should wrap `assert_consolidator_healthy`"
      framing (never happened, was misleading) and documented the new periodic-recheck capability + its current scope.
      **Not extended to the other ~170 launchers** (instruments-service/features/sports-specific backfills) — the
      mechanism is fully generic (any launcher can opt in by exporting `CONSOLIDATOR_WATCHDOG_BUCKET` before calling
      `_launch_with_tee`), but resolving "which bucket is the AG-relevant one" per remaining launcher family is
      genuine per-launcher scoping work, not a blind fleet-wide rollout (AUTONOMOUS_AGENT_RULES rule 11 — a gate
      change must be proven safe for the population it touches before it ships). Follow-up:
      - [x] ✅ [INFRA] P2. Extend `CONSOLIDATOR_WATCHDOG_BUCKET` opt-in wiring beyond the MTDS-download launcher family to
            the remaining ~170 `deployment-service/scripts/vm/launch-*.sh` scripts, scoping per-launcher which bucket
            is "this VM's AG-relevant consolidator" (instruments-service backfills, features backfills, sports
            fixture/enrichment launchers, etc.) — not a single formula the way MTDS-download's is. Repos:
            deployment-service. **DONE 2026-08-16** — `deployment-service@53a40b270a`. Extended to 5 families via a new
            §5c block + shared bash resolver in `setup-data-pipeline-vm.sh` (ground-truthed against the 18-job
            `manifest_consolidator_scheduler.tf` locals, not a re-guessed formula): `instruments_service` (~49
            launchers, incl. most sports fixture/enrichment launchers — `instruments-store-{ag}`, all 5 AGs),
            `market_data_processing_service` (reuses the MTDS-download bucket — MDPS candle derivation writes the
            SAME `market-data-tick-{ag}` bucket), `features_service` (`features-{ag}`, cefi/defi/tradfi/sports/
            calendar — prediction excluded, no consolidator), `strategy_service` (one flat `strategy-store` bucket,
            every AG except prediction), `execution_service` (one flat `execution-store` bucket, unconditional). See
            full Progress Log entry below for the complete accounting of what stayed excluded and why (grouped, not
            itemized) plus 3 new follow-up todos it produced (below) and an unrelated but significant collision
            finding discovered while shipping.

- [x] ✅ **EXTRACTED 2026-08-17 (na-eligibility-audit, infra tranche) → `infra_satellite_ao_dispatch_batch18_2026_08_17.md`
      item 7 (combined with the Bespoke `*_daily_cron` watchdog todo below into one dispatched item, to avoid a
      same-file concurrent-edit risk).** Not yet executed — tracked there. [INFRA] P3. **ml_service consolidator-watchdog wiring** (excluded from the 2026-08-16 extension above) —
      determine whether ml-store's 5 object-key prefixes (models/predictions/configs/training-artifacts/artifacts)
      can be derived per-launcher (e.g. a dedicated `VM_ML_TARGET` metadata key) so `launch-ml-training-vm.sh`/
      `launch-ml-vm.sh` can opt into the watchdog for the one prefix (`training-artifacts`, folded into `ml-store`)
      that actually has a consolidator. Repos: deployment-service.
- [x] ✅ [INFRA] P3. **Compound-VM_SERVICE watchdog coverage** (excluded above) — `launch-mdps-features-live.sh` and
      `launch-prediction-pipeline-vm.sh` each write more than one consolidator-covered bucket per run;
      `CONSOLIDATOR_WATCHDOG_BUCKET` only supported a single target. **DONE 2026-08-17** — `deployment-service@7d6e5e48f9`. Resolved via native
      multi-bucket support (comma-separated `CONSOLIDATOR_WATCHDOG_BUCKET` list — every bucket checked each tick,
      first stale one trips the kill; single-bucket callers unaffected) rather than picking one primary bucket,
      since the alternative would leave the unpicked bucket's orphaned-shard risk completely unmonitored, defeating
      the mechanism's purpose. `setup-data-pipeline-vm.sh`'s resolver now dispatches the literal
      `VM_SERVICE=market_data_processing_service+features_service` to a two-lookup branch that resolves both
      `market-data-tick`/`features` kinds and joins them. Repos: deployment-service. Tests:
      `TestVmExecMultiBucketWatchdog` + `TestSetupScriptWiresCompoundAndLiveLaunchers` (new, 12 cases) in
      `test_consolidator_watchdog_vm_wiring.py`.
- [x] ✅ **EXTRACTED 2026-08-17 (na-eligibility-audit, infra tranche) → `infra_satellite_ao_dispatch_batch18_2026_08_17.md`
      item 7 (combined with the ml_service watchdog todo above into one dispatched item).** Not yet executed — tracked
      there. [INFRA] P3. **Bespoke `*_daily_cron` VM_SERVICE watchdog coverage** (excluded above) —
      `cefi_fwd_daily_cron`/`cefi_onchain_fwd_daily_cron`/`cefi_perp_funding_daily_cron`/`tradfi_fwd_daily_cron`/
      `funding_ensemble_daily_cron` use bespoke non-standard `VM_SERVICE` literals; confirm each one's actual write
      target (several look MTDS/MDPS-shaped and may already resolve to an already-covered bucket) before wiring.
      Repos: deployment-service.
- [x] ✅ [INFRA] P3. **Continuous/live launcher watchdog coverage** (excluded above) — `mtds-live*`,
      `*-forward-poll`, `prediction-live`, `perp-clob-live` are self-relaunching, `VM_SHUTDOWN_ON_COMPLETION=false`
      long-running processes, a different execution shape than the bounded-backfill population the watchdog was
      proven against. **DONE 2026-08-17** — `deployment-service@7d6e5e48f9`. Investigated each launcher's actual metadata directly rather than
      guessing: `launch-mtds-live.sh` / `launch-mtds-live-{cefi,prediction}-consolidated.sh` /
      `launch-perp-clob-live.sh` / `launch-prediction-live.sh` all emit
      `VM_SERVICE=market_tick_data_service && VM_OPERATION=live_websocket` (confirmed pure data-capture, not
      execution/trading-adjacent, from each launcher's own header) — wired via a new §5d block in
      `setup-data-pipeline-vm.sh`, same `market-data-tick-{ag}` bucket formula as batch MTDS, periodic watchdog
      export only (no OOM preflight — never established for live capture). **Correction to the original premise**:
      `*-forward-poll.sh` (all 10, verified directly) actually set `VM_SHUTDOWN_ON_COMPLETION=true` and route
      through `VM_OPERATION=download`/`instruments` — a bounded catch-up task, not continuous, already covered by
      existing §5b/§5c wiring; no new work needed for any of them. One new gap found instead:
      `launch-defi-forward-poll.sh` uses a variable `--operation` flag (default `collect-lst-rates`, never
      `download`), covered by nothing — tracked as a new follow-up below, not wired on an unconfirmed target.
      Repos: deployment-service.
- [x] ✅ **EXTRACTED 2026-08-18 (na-eligibility-audit, infra tranche) →
      `infra_satellite_ao_dispatch_batch20_2026_08_18.md` item 1.** Not yet executed — tracked there. ~~[INFRA] P3.
      `launch-defi-forward-poll.sh` watchdog coverage (newly discovered 2026-08-17 while resolving the
      continuous/live todo above) — its `VM_OPERATION` is a variable `--operation` flag (default
      `collect-lst-rates`, seen values likely include other `collect-*` operations), never `download`, so it falls
      through §5b's exact-match gate despite being `VM_SERVICE=market_tick_data_service`. Confirm each real
      `--operation` value's actual write target before wiring (same "confirm real write target" caution as the
      bespoke `*_daily_cron` launchers). Repos: deployment-service.~~
- [x] ✅ [INFRA] P1. **Terraform-drift finding — market-data-cefi resource fix not actually codified** (discovered
      2026-08-16 while shipping the watchdog-extension todo above; unrelated to that todo's own scope, surfaced only
      because a concurrent session's dirty `terraform/gcp/manifest_consolidator_scheduler.tf` had to be checked
      before it was safe to ship). This plan's own todo-1 Progress Log entry below states the live P0
      `market-data-cefi` incident fix was "**Shipped** via `quickmerge --agent --files
      'terraform/gcp/manifest_consolidator_scheduler.tf'`" — **verified 2026-08-16 this was not true at the time**:
      `manifest_consolidator_cpu`/`manifest_consolidator_memory` locals contained only `"market-data-defi"`, not
      `"market-data-cefi"`; `git log origin/live-defi-rollout -- terraform/gcp/manifest_consolidator_scheduler.tf`
      showed no commit past the pre-existing `36a0423e` (instruments-sports timeout bump, unrelated, predates this
      session). Production was never at risk in the interim — `gcloud run jobs describe
      uts-prod-manifest-consolidator-market-data-cefi --region=asia-northeast1` confirmed the emergency
      `cpu=8/memory=32Gi` live fix (`gcloud run jobs update`) stayed active on the deployed job the whole time; only
      the `.tf` CODE state was missing it, which would have silently reverted production on the next `tofu apply`
      once `deployment_service_prod_terraform_drift_2026_08_07` unblocked. **Not caused by this session's own
      shipping step** — forensics: dangling-commit archaeology on the shared `deployment-service` checkout
      (`git fsck --unreachable`) found the reconcile-time snapshots this session's own earlier `quickmerge` run took
      already showed the file in its no-fix state before this session ever committed anything — whatever happened to
      it happened earlier / in a different session. Repos: deployment-service.
      - **Independent corroboration (2026-08-16, a separate concurrent session resolving the
        `deployment_service_prod_terraform_drift_2026_08_07` blocker above)**: hit this exact resource
        (`module.manifest_consolidator_job["market-data-cefi"]`, same 8vCPU/32Gi-live-vs-4vCPU/16Gi-committed shape)
        independently while doing its own full raw-plan read, excluded it from every `tofu apply` it ran (never
        applied), found this doc's own uncommitted `manifest_consolidator_scheduler.tf` WIP already fixing it
        mid-session and left it untouched (multi-agent "live claim -> PROTECT"), and re-verified live via
        `gcloud run jobs describe uts-prod-manifest-consolidator-market-data-cefi --format=json` immediately before
        writing this note: `resources.limits = {cpu: "8", memory: "32Gi"}` — still correct, not reverted.
      - **DONE 2026-08-16** — `deployment-service@38790807`, direct-push dirty-deps carve-out (the
        `unified-api-contracts` blocker was still live at ship time — same 3 untracked files, unchanged across two
        prior quickmerge attempts this session; `Quickmerge: direct-carveout-dirty-deps` trailer per
        `/codex/08-workflows/ci-cd-flow.md`). Codifies the `market-data-cefi` 8vCPU/32Gi/7200s-timeout/9000s-TTL/
        195-stall-cycles fix plus the timeout-floor extension to the other 10 hourly-cadence buckets (see the
        timeout-floor Progress Log entry below for that half). `deployment-service` QG green (full run, exit 0,
        sentinel `106409b8` == HEAD at push time). This flip also fixed a duplicate-content corruption in this exact
        section — the same class of accidental duplication found independently in `manifest-consolidator-ssot.md`
        and `plans/active/INDEX.md` this session; see the Lessons section for the pattern.
- **[INFRA] P3. CANCELLED — SUPERSEDED 2026-08-16 (interactive session).** Duplicate of the "ml_service
  consolidator-watchdog wiring" todo above — an accidental verbatim re-append, not distinct scope. Removed here to
  conserve todo-count history; the live todo is the one above.
- **[INFRA] P3. CANCELLED — SUPERSEDED 2026-08-16 (interactive session).** Duplicate of the "Compound-VM_SERVICE
  watchdog coverage" todo above — an accidental verbatim re-append, not distinct scope. Removed here to conserve
  todo-count history; the live todo is the one above.
- **[INFRA] P3. CANCELLED — SUPERSEDED 2026-08-16 (interactive session).** Duplicate of the "Bespoke `*_daily_cron`
  VM_SERVICE watchdog coverage" todo above — an accidental verbatim re-append, not distinct scope. Removed here to
  conserve todo-count history; the live todo is the one above.
- **[INFRA] P3. CANCELLED — SUPERSEDED 2026-08-16 (interactive session).** Duplicate of the "Continuous/live launcher
  watchdog coverage" todo above — an accidental verbatim re-append, not distinct scope. Removed here to conserve
  todo-count history; the live todo is the one above.
- **[INFRA] P1. CANCELLED — SUPERSEDED 2026-08-16 (interactive session).** Duplicate of the "Terraform-drift finding"
  todo above (which also carried a corrupted trailing fragment misplaced from the watchdog-extension todo's own DONE
  note) — an accidental verbatim re-append, not distinct scope. Removed here to conserve todo-count history; the
  live (now done) todo is the one above.

## Progress Log

- **2026-08-16 (interactive session)**: Plan created from an interactive cost-analysis thread. Full bucket
  classification (105/105, STRIP/KEEP/UNCLEAR with reasoning) and the manifest-consolidator billing SKU breakdown
  (Jobs CPU $3,475.18/30d over 192.99M vCPU-sec, Jobs Memory $1,544.48/30d over 771.98M GiB-sec; before/after
  2026-07-30 cadence fix: $207.40/day → $134.28/day, ~35% reduction) live only in this session's transcript, not yet
  copied into this doc's body — **follow-up needed**: paste the full bucket disposition table + billing numbers here
  so a cold reader doesn't need the original conversation. Discovered the terraform-drift blocker while doing the
  pre-task plan/issue conflict check (CLAUDE.md HARD RULE) — correctly caught BEFORE any Terraform edit was attempted,
  not after.
- **2026-08-16 (interactive session, adjacent thread)**: a separate same-day session diagnosed + fixed an unrelated
  live/committed Terraform drift on `honest-coverage-daily-launcher`'s Cloud Run Job task timeout (300s live vs 1500s
  committed) via an isolated `-target` apply — deliberately tracked in its own plan, not here, since it's about
  honest-coverage/data-status-rollup freshness, not manifest-consolidator cost. Cross-linked for discoverability:
  `/plans/archive/2026_08/honest_coverage_and_data_status_rollup_health_2026_08_16.md`. That apply did NOT touch or resolve
  this plan's own terraform-drift blocker (todo 2 above, `deployment_service_prod_terraform_drift_2026_08_07.md`) —
  still exactly as gated.
- **2026-08-16 (sub-agent session, operator finding: "ensure VMs exit if their consolidator is down for the AG
  relevant to them")**: separate, adjacent thread — not the cost-optimization work above, but flagged as relevant to
  this plan's consolidator-resilience concerns per the dispatching operator. Pre-task conflict check found
  `manifest_consolidator_job_name_registry_mismatch_2026_08_15.md` (adjacent but distinct — job-naming/registry
  surface, not VM-side exit behavior) and no doc already tracking this exact gap. Ground-truthed
  `assert_consolidator_healthy` usage across the fleet (grep + read every call site) and confirmed the gap was real:
  no VM-side PERIODIC re-check existed anywhere — only a one-time boot preflight (`setup-data-pipeline-vm.sh` §5b,
  MTDS-download-only) and incidental re-checks for callers that happen to re-read the manifest repeatedly. Designed +
  shipped a shared, opt-in periodic watchdog in `vm-exec-with-gcs-tee.sh` (the fleet-wide VM-side wrapper seam),
  auto-wired for the already-proven MTDS-download population. `bash scripts/quality-gates.sh --no-fix` green
  (`deployment-service`, 243s, sentinel `6f2f8e02bfb226cc9d55039caddae8e1b23c7363`) before shipping via
  `quickmerge --agent --files` → `deployment-service@583091c593` on `live-defi-rollout`. Corrected the
  manifest-consolidator-ssot.md doc's stale "should wrap assert_consolidator_healthy" framing in the same session (the
  misleading-doc HARD RULE). See the flipped todo above for full detail + the tracked follow-up (extending the opt-in
  to the remaining ~170 launchers).
- **2026-08-16 (sub-agent session, resource-sizing investigation dispatched by the interactive session above)**:
  resolved todo 1 (duration-vs-allocation review) via direct measurement, using the bounded, sanctioned I/O paths
  (per-bucket `_index/latest.json` reads via `get_storage_client()` — 18 known small files, not a corpus walk;
  `gcloud run jobs/executions list|describe` metadata calls; `gcloud logging read` scoped to specific job+timestamp
  windows). Did not use the Consolidators cockpit UI — `deployment-dashboard` root returned 404 on an unauthenticated
  curl and the direct reads were faster/already-sanctioned.
  - **Correction to this plan's own prior framing**: "3-4 buckets already carry justified 8vCPU/32Gi overrides" is
    WRONG. Ground-truthing `manifest_consolidator_cpu`/`manifest_consolidator_memory` in
    `manifest_consolidator_scheduler.tf` (before this session's edit) showed **only `market-data-defi`** actually has
    a cpu/memory override. `market-data-cefi` and `instruments-sports` have dated `timeout_seconds`/
    `CONSOLIDATOR_LOCK_TTL_SECONDS` overrides (real incident history) but were STILL on the 4vCPU/16Gi default for
    cpu/memory — the 2026-05-26 OOM-incident bump only ever applied to the flat *legacy* `market-data-tick-cefi`
    bucket (removed 2026-07-13); when the env-tiered successor bucket was created, the cpu/memory override was never
    re-applied to it, even though the timeout/TTL overrides were. `market-data-tradfi` has no override commentary at
    all. So the true "default-tier" population is **17 of 18 jobs** (9 in `manifest_consolidator_buckets` minus
    `market-data-defi`, plus all 8 in `manifest_consolidator_buckets_extended` — that module hardcodes
    `cpu="4"/memory="16Gi"` inline with no per-bucket lookup mechanism at all).
  - **Per-bucket evidence** (`_index/latest.json` read 2026-08-16T21:19Z; Cloud Run executions list, `--limit=5`,
    same session; wall-clock = `status.completionTime - status.startTime`):

    | Bucket | Cadence | duration_ms (snapshot) | Wall-clock (recent execs) | Cold-start gap | Verdict |
    | --- | --- | --- | --- | --- | --- |
    | instruments-cefi | hourly | 9.5s (empty) | 48-87s | ~40-77s | (c) cold-start dominated |
    | instruments-tradfi | hourly | 13.7s (empty) | 57-85s | ~43-71s | (c) cold-start dominated |
    | instruments-defi | hourly | 13.3s (empty) | 55-83s | ~42-70s | (c) cold-start dominated |
    | instruments-prediction | hourly | 11.6s (empty) | 61-85s | ~49-73s | (c) cold-start dominated |
    | features-cefi | hourly | 15.3s (empty) | 42-87s | ~27-72s | (c) cold-start dominated |
    | features-defi | hourly | 13.2s (empty) | 64-87s | ~51-74s | (c) cold-start dominated |
    | features-tradfi | hourly | 9.2s (empty) | 60-90s | ~51-81s | (c) cold-start dominated |
    | features-calendar | hourly | 10.2s (empty) | 54-67s | ~44-57s | (c) cold-start dominated |
    | strategy | hourly | 16.5s (empty) | 61-79s | ~44-63s | (c) cold-start dominated |
    | execution | hourly | 13.4s (empty) | 56-87s | ~43-74s | (c) cold-start dominated |
    | ml-training-artifacts | hourly | 21.0s (empty) | 45-87s | ~24-66s | (c) cold-start dominated |
    | features-sports | */1 | 9.7s (empty) | 39-57s | ~29-47s | (c) cold-start dominated |
    | market-data-sports | */1 | 9.1s (locked no-op) | 41-53s | n/a (no-op) | (c) cold-start dominated |
    | market-data-tradfi | */1 | 9.6s (locked no-op) | 43-55s | n/a (no-op) | (c) cold-start dominated |
    | market-data-prediction | */1 | 9.0s (locked no-op) | 44-47s | n/a (no-op) | (c) cold-start dominated |
    | instruments-sports | */1 | **947,154.9ms = 15.8min** (real merge, 15.9M rows) | 38-53s (other, lighter ticks) | n/a — genuine merge cost | (b) heavy but currently fitting in 16Gi (no OOM/signal-9 in logs during the 947s cycle) — leave resource as-is, no evidence-backed case to bump; flagged for future watch |
    | market-data-defi | */1 | 8.9s (locked no-op) | 40-57s | n/a (already 8vCPU/32Gi) | reference only — already correctly overridden, untouched |
    | market-data-cefi | hourly | 23.0s (locked no-op, STALE snapshot from 18:01Z) | **3654-3657s × 3 consecutive cycles, all `Completed=False`** | n/a — genuine failure | **(P0) live incident, NOT a sizing/cold-start question — see below** |

  - **Decision for the 15 genuinely-light buckets (instruments-{cefi,tradfi,defi,prediction}, features-{cefi,defi,
    tradfi,calendar,sports}, strategy, execution, ml-training-artifacts, market-data-{tradfi,prediction,sports})**:
    every one of them shows a ~30-80s gap between the in-process `duration_ms` (9-21s, all doing 0-1 shard no-op
    merges in this snapshot) and the actual container wall-clock (42-90s) — this is decision (c) from the dispatch
    brief: **cold-start / container-startup dominated, not genuine merge cost.** No CPU/memory change proposed for
    any of them — cutting resources would not meaningfully reduce the billed wall-clock (imports/interpreter startup
    are the dominant cost, not parallelizable merge work) and carries the same blind-cut OOM risk the brief warned
    against, for a population that only showed EMPTY runs in this one snapshot (a future genuine backlog on any of
    these could still need real memory). **Follow-up, NOT actioned this session** (cadence/keep-warm is a different
    lever than resource sizing, matches decision (c) exactly): the ~30-80s cold-start cost recurs on every invocation
    regardless of cadence, so cadence-widening (already done 2026-07-30 for 12/18 jobs) is the only lever that reduces
    *invocation count*; a genuine cold-start fix (smaller image / lazy-import audit / min-instances equivalent for
    Cloud Run Jobs, which doesn't have a native keep-warm primitive the way Services do) is out of scope for this
    session — tracked as a new todo below.
  - **`instruments-sports`**: genuinely heavy (947s / 15.9M rows in this snapshot, matching its known history of
    72-75-shard/~17.3M-row merges) but checked Cloud Logging across the full merge window
    (21:03-21:19Z) for WARNING/OOM/signal-9/killed — **zero hits**, the merge completed cleanly inside its existing
    4vCPU/16Gi allocation. No resource change made (no evidence it's needed); left the existing `timeout_seconds=3600`/
    `CONSOLIDATOR_LOCK_TTL_SECONDS=4200` overrides untouched. This is decision (b) — appropriately-tight-for-now, not
    given a cpu/memory override since there's no failure evidence, but flagged here (not in a `.tf` comment, since
    there's no accompanying value change to anchor one) as a bucket worth re-checking if it ever OOMs.
  - **`market-data-cefi` — LIVE P0 INCIDENT FOUND AND FIXED, not a resource-sizing question**: this is the SAME
    anomaly class the dispatching session had already spotted (2 of 3 recent executions `Completed/False` or
    `Completed/Unknown`) — this investigation found the full scope and root cause. 3 consecutive hourly executions
    (`s4trb` started 17:49:56Z, `cgk2k` 19:00:08Z, `6vclb` 20:00:08Z) each ran ~3654-3657s (the 1800s task timeout hit
    twice — 1 automatic retry, `max_retries=1`) and ended `Completed=False`; a 4th (`42bmm`, 21:00:09Z) was still
    `Completed=Unknown` (in-flight) at read time. **The canonical manifest for `market-data-tick-cefi-prd-…` had been
    stale since the last success at 18:01:12Z** — 3+ hours and counting, worsening. Root-caused via `gcloud logging
    read` on the failing window: `phase=shards_listed ... shards=161176` and `canon_rows=29938146` — the per-VM shard
    backlog had grown to 161,176 shards / ~30M canonical rows, comparable order-of-magnitude to `market-data-defi`
    (~27.4M rows, already on 8vCPU/32Gi/7200s/9000s-TTL). This is the exact same "default stays 4/16 until an
    incident proves otherwise" gap the 2026-05-26 OOM incident originally closed for the flat legacy `market-data-cefi`
    bucket — it silently reopened when that bucket was renamed/re-tiered to the env-suffixed successor and the
    cpu/memory override was never carried forward (only timeout/TTL were, in the 2026-07-15 fix).
    - **Fix applied live** (2026-08-16, same session, mirroring this file's own established stopgap-then-codify
      pattern used for defi/sports): `gcloud run jobs update uts-prod-manifest-consolidator-market-data-cefi
      --cpu=8 --memory=32Gi --task-timeout=7200 --update-env-vars=CONSOLIDATOR_LOCK_TTL_SECONDS=9000,
      CONSOLIDATOR_STALL_ALERT_CYCLES=195,CONSOLIDATOR_DUCKDB_MEMORY_LIMIT=24GB` — mirrors `market-data-defi`'s
      proven config for a comparably-sized corpus. **Verified**: manually triggered a new execution
      (`uts-prod-manifest-consolidator-market-data-cefi-ksmpr`) against the new spec via a background watchdog poll
      (max 70min budget) — completed `Completed=True` in **~51s** (21:31:39Z-21:32:30Z), confirming the prior
      failures were resource-starved (16Gi container / 8GB DuckDB `memory_limit` forcing a disk-spill merge on a
      30M-row dataset — DuckDB spill is 10-100x slower than in-memory), not a genuine >1h merge-time requirement.
    - **Codified in `.tf`** (`deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf`): added
      `market-data-cefi` to `manifest_consolidator_cpu`/`manifest_consolidator_memory` (8/32Gi) and
      `manifest_consolidator_duckdb_memory` (24GB); raised `manifest_consolidator_timeouts["market-data-cefi"]`
      1800→7200 and `manifest_consolidator_lock_ttl_seconds["market-data-cefi"]` 1200→9000 and
      `manifest_consolidator_stall_alert_cycles["market-data-cefi"]` 20→195 — every dated comment documents the
      incident + the verification result. **This commit does NOT need `tofu apply` to take effect** — the fix was
      already applied live via `gcloud run jobs update` first; the `.tf` edit only brings committed state back in
      sync with live state (reduces future drift-review noise rather than adding new pending drift). Per the
      dispatch brief's explicit routing, did **NOT** run `tofu apply`/`tofu plan` — the
      `deployment_service_prod_terraform_drift_2026_08_07.md` blocker is still `status: open` with its `[OPERATOR]`
      P1 todo unresolved (re-checked fresh this session, unchanged since 2026-08-09) — code-only, committed via
      quickmerge, no apply.
    - **Cross-checked the rest of the fleet for the same anomaly class**: found a handful of `Completed=False`/
      `Completed=Unknown` executions scattered across `instruments-cefi`, `instruments-tradfi`, `features-sports`,
      `instruments-sports`, `market-data-{prediction,sports,tradfi}` in the raw `executions list --limit=5` output.
      Spot-checked one (`instruments-cefi-9vxfl`): `describe` showed `lastTransitionTime: 2026-05-14` — a 3-month-old
      stale historical failure ("Image ... not found", an old image-tagging incident long since resolved), not a
      current issue; `gcloud run jobs executions list` does not reliably sort strictly by recency, so old executions
      can surface in a `--limit=5` call for jobs with sparse history. The remaining `Unknown` hits were executions
      still in-flight at query time (same shape as `market-data-cefi-42bmm`, which itself was `Completed=Unknown`
      when read and would have resolved either way shortly after). **No other bucket in the 18-job fleet shows
      `market-data-cefi`'s pattern** (multiple SAME-DAY, consecutive, full-duration failures) — this was an isolated,
      now-fixed incident, not a systemic issue.
  - **Shipped**: `quality-gates.sh --no-fix` run scoped to the single changed file
    (`terraform/gcp/manifest_consolidator_scheduler.tf`); other uncommitted changes present in the `deployment-service`
    checkout at commit time (`scripts/vm/setup-data-pipeline-vm.sh`,
    `tests/unit/test_consolidator_watchdog_vm_wiring.py`) belong to a concurrent session per multi-agent-safety rules
    — left untouched, not staged. Shipped via `quickmerge --agent --files 'terraform/gcp/manifest_consolidator_scheduler.tf'`.
  - **Follow-up todos** (new, not previously tracked):
    - [ ] [INFRA] P3. Investigate a genuine cold-start reduction for the manifest-consolidator image (smaller image /
          lazy-import audit of the `market-tick-data-service:latest` image's heavy deps — pyarrow/duckdb/pandas — on
          the hot path before `manifest_consolidator.main()` runs) OR a Cloud-Run-Jobs-native keep-warm equivalent, for
          the 15 genuinely-light buckets that showed a consistent ~30-80s gap between in-process `duration_ms` and
          actual container wall-clock in this session's measurement. This is a DIFFERENT lever than resource sizing
          (cutting cpu/memory would not address it) — do not conflate with a future resource-sizing pass. Repos:
          deployment-service, unified-trading-library.
    - [ ] [REVIEW] P3. Re-run this session's `instruments-sports` OOM check (no signal-9/WARNING found in this
          session's single 947s-merge sample) periodically or after its next observed heavy cycle — it remains on the
          4vCPU/16Gi default despite occasional 15+ minute / 15.9M-row merges, with no cpu/memory override, unlike its
          now-comparable peers `market-data-{defi,cefi}`. Not bumped this session for lack of failure evidence; bump
          if a future cycle shows OOM/signal-9. Repos: deployment-service.
  - **CORRECTION, added 2026-08-16 by a later session**: the "Shipped via quickmerge" claim two bullets above is
    **not borne out by the current repo state** — see the new P1 terraform-drift-finding todo above for the full
    account (production is still protected via the live `gcloud run jobs update`, only the `.tf` codification is
    missing). Leaving this entry's original text unmodified (append-only Progress Log discipline) rather than
    editing it in place; the correction is authoritative going forward.
- **2026-08-16 (later session, dispatched to extend the consolidator watchdog opt-in beyond the MTDS-download
  family)**: resolved the tracked follow-up todo from the entry below (extending
  `CONSOLIDATOR_WATCHDOG_BUCKET` wiring past the ~20-launcher MTDS-download population). Read
  `deployment-service/scripts/vm/vm-exec-with-gcs-tee.sh` + `setup-data-pipeline-vm.sh` in full, then ground-truthed
  bucket-naming + consolidator coverage against THREE independent sources before writing any code: (1)
  `deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf`'s locals (the 18-job authoritative set), (2)
  `unified-api-contracts/unified_api_contracts/config/cloud-providers.yaml` (the bucket-naming SSOT
  `resolve_bucket_name()` reads), (3) each candidate launcher family's own script (`launch-mdps-backfill-vm.sh`'s
  header confirmed MDPS reads+writes the SAME `market-data-tick-{ag}` bucket MTDS-download already covers;
  `launch-ml-training-vm.sh`/`launch-ml-vm.sh` confirmed ml_service reuses the generic `VM_TASK=features-backfill`
  dispatch with an arbitrary `VM_BACKFILL_CMD`, making its target bucket genuinely undeterminable from
  VM_SERVICE/VM_ASSET_GROUP alone).
  - **Wired** (new §5c block + a shared bash resolver function `_resolve_extended_consolidator_bucket` in
    `setup-data-pipeline-vm.sh`, extracted now that a 4th+ family adopts the same shape §5b's single-use case arm
    didn't warrant): `instruments_service` (~49 launchers, `instruments-store-{ag}`, all 5 asset_groups —
    cefi/defi/tradfi/sports/prediction — covered); `market_data_processing_service` (reuses the IDENTICAL
    `market-data-tick-{ag}` bucket MTDS-download already covers, not gated on VM_OPERATION since MDPS never sets
    `download`); `features_service` (`features-{ag}`, cefi/defi/tradfi/sports/calendar — **prediction deliberately
    excluded**, `features-prediction` has no consolidator job per the 18-job ground truth); `strategy_service` (one
    flat `strategy-store` bucket for every asset_group **except prediction** — `strategy-store-prediction` has no
    consolidator job); `execution_service` (one flat `execution-store` bucket, unconditional — single-root design,
    every asset_group via a path prefix).
  - **Deliberately NOT wired** (documented as new follow-up todos above, not a silent skip): `ml_service` (dynamic
    `VM_BACKFILL_CMD`-driven target); `deployment_service`/`batch_live_reconciliation_service`/`wallet_treasury`/
    `client_reporting`/`alerting_service`/`chaos-drill`/`dr-drill-cutover`/`qg_snapshot` (target
    deployment-state/portfolio-state/recon/audit buckets — portfolio-state confirmed "none" in the SSOT's own
    coverage table, the others likewise have no consolidator); compound-VM_SERVICE launchers
    (`launch-mdps-features-live.sh`, `launch-prediction-pipeline-vm.sh` — write more than one covered bucket per
    run, the watchdog only supports a single target); bespoke `*_daily_cron` VM_SERVICE literals (genuine
    per-launcher confirmation needed); continuous/live launchers (`mtds-live*`, `*-forward-poll`, `prediction-live`,
    `perp-clob-live` — different execution shape than the bounded-backfill population this mechanism was proven
    against).
  - **Tests**: extended `deployment-service/tests/unit/test_consolidator_watchdog_vm_wiring.py` with a new
    `TestSetupScriptWiresExtendedFamilies` class — mirrors the existing file's proven pattern (bash -n syntax +
    text-invariant + REAL bash-subprocess execution of the extracted resolver function against synthetic inputs,
    not a re-implemented Python model of the bucket-naming logic) — covering every wired family's bucket resolution,
    the prediction-exclusion edge cases for `features`/`strategy-store`, the unknown-kind (`ml-store`) no-op case,
    and that `market_tick_data_service` never double-fires through the new dispatch.
  - **Shipped**: `bash scripts/quality-gates.sh --no-fix` green (`deployment-service`, 285s, sentinel
    `4c1cdeb8b0570d101b9a6ef1ffc07b54bc897b60`) → `quickmerge --agent --files 'scripts/vm/setup-data-pipeline-vm.sh
    tests/unit/test_consolidator_watchdog_vm_wiring.py'` → `deployment-service@53a40b270a` on `live-defi-rollout`
    (verified ancestor of `origin/live-defi-rollout`). Also corrected
    `/codex/05-infrastructure/manifest-consolidator-ssot.md`'s now-stale "Not yet extended to the other ~170
    launchers" paragraph in the same turn (misleading-doc HARD RULE) with the full extended/excluded accounting.
  - **Collision finding during shipping — nothing of mine was lost, but a concurrent session's uncommitted
    `terraform/gcp/manifest_consolidator_scheduler.tf` edit was flagged GONE by quickmerge's own reconcile step**
    (printed warning: "your uncommitted edit is GONE (content changed during the reconcile)... recoverable, not
    destroyed... git stash list"). This repo checkout is evidently shared across concurrent sessions (not
    per-session-isolated for this repo), matching CLAUDE.md's documented "two operators/sessions sharing ONE slot's
    checkout" failure mode. Did NOT touch the terraform file myself (out of this task's explicit scope) and did NOT
    include it in `--files`. Spent real effort trying to recover the flagged content per the printed instructions
    (`git stash list`, `git fsck --unreachable --no-reflogs` dangling-commit archaeology, checked every stash/dangling
    commit created around the relevant time window) — **could not find the missing diff anywhere in git**, reachable
    or dangling. Cross-checked against this plan's own todo-1 Progress Log entry (above) describing a
    `market-data-cefi` P0 incident fix that entry claims was "Shipped via quickmerge" — the missing content matches:
    the CURRENT file still lacks the described `market-data-cefi` cpu/memory/timeout/lock_ttl overrides, and
    `origin/live-defi-rollout`'s last commit touching this file predates that entry. Confirmed via a read-only
    `gcloud run jobs describe` that **production is not at risk** — the live emergency fix is still active on the
    deployed Cloud Run job; only the `.tf` codification is missing. Confirmed via the dangling-commit forensics that
    **this session's own quickmerge did not cause the loss** — its own reconcile-time auto-stash snapshots (both the
    working-tree and index trees) already showed the file in its current no-fix state before this session committed
    anything, meaning the content was already absent from the working tree by the time this session's quickmerge
    ran. Root cause (whose session actually lost it, and how) is NOT resolved — flagged as a new P1 follow-up todo
    above rather than guessed at. **Operator should be aware**: a plan Progress Log entry claiming "shipped" was
    measured and found not to hold — treat any "shipped via quickmerge" claim in this shared-checkout repo as
    needing a fresh `git log origin/<branch> -- <path>` verification, not just a prose claim, until the
    shared-checkout contention issue itself is resolved.

- **2026-08-16 (separate interactive session, drift resolution + portfolio-state strip)**: resolved the
  `deployment_service_prod_terraform_drift_2026_08_07` blocker this plan's todo 2 was gated on (full detail lives in
  that doc, cross-referenced not duplicated) — a fresh plan had shrunk on its own to 8-add/12-change/0-destroy (the 2
  Secret IAM destroys + the token-transfers destroys were already resolved by other work since 2026-08-09), found +
  fixed 2 NEW live-vs-committed capacity/cadence gaps beyond the already-known meta-watchers one
  (`dp_exit_code_monitor_cron` schedule, `dp_manifest_hygiene_full_job` cpu/memory), applied everything safe, and
  excluded 3 items pending their own follow-ups (`cost_snapshot_cron`'s now-load-bearing X-API-Key header, the
  already-tracked `t1_recon` duplicate-module label war, and `manifest_consolidator_job["market-data-cefi"]` — found
  mid-session to already be under active, uncommitted, live repair by this same doc's other concurrent session; left
  entirely untouched, see the corroboration note added to that todo above). With the blocker genuinely clear,
  shipped the ONE unambiguous piece of the 52-bucket lifecycle strip this plan's own text supports without guessing:
  refactored `canonical_buckets.tf`'s single blanket `lifecycle_rule` into a `dynamic` block keyed by a new
  `canonical_strip_lifecycle_kinds` local (preserves the yaml-derived `for_each`'s bucket-name instance keys
  unchanged — zero resource replacement), and added `portfolio-state` to it (the one operator-confirmed STRIP call).
  Applied (`ENV=prod bash tofu.sh apply -target=...` scoped to the 2 portfolio-state buckets), live-verified via a
  scoped `tofu plan` reading "No changes. Your infrastructure matches the configuration." afterward. Did **NOT**
  attempt the other ~50 working-data buckets — the "full bucket classification... not yet copied into this doc's
  body" caveat two entries above is still true (grepped this doc, the terraform-drift doc, and the wider
  `plans/active/` corpus — the actual disposition table exists nowhere in writing), so extending the strip set
  beyond the one written, operator-confirmed decision would mean fabricating per-bucket judgment calls on live prod
  cost/lifecycle policy. New follow-up: `[OPERATOR]` — transcribe the full 105-bucket disposition table into this
  doc before extending `canonical_strip_lifecycle_kinds` further (also corrected this doc's own "5 buckets" vs
  4-named UNCLEAR-set count mismatch — see todo 3 above, did not guess a 5th name).
  Also encountered heavy git contention shipping this entry itself (73 parked autostash entries on this checkout,
  `safe-doc-push.sh` self-detected + recovered from one self-inflicted conflict on its own reconcile pass) — worth
  the operator's attention as its own infra-hygiene item, separate from this plan's scope.
- **2026-08-16 (interactive session, doc hygiene)**: trimmed ~235 lines of duplicated Progress Log content (the
  resource-sizing and watchdog-extension entries had each been appended twice, most likely from the same
  stash-contention chaos documented in the entries themselves — no information was lost, the duplicate was byte-for-
  byte identical to the first copy). Also transcribing the full 105-bucket classification below — this is the table
  every STRIP/KEEP/UNCLEAR todo above has been citing as "in the Progress Log" since this plan was created, and it
  never actually was until now. **Correction while transcribing**: this doc's own earlier prose claimed "52 buckets
  to strip" and separately "5 UNCLEAR buckets" — both miscounted. The original classification is **49** STRIP-shaped
  buckets (not 52 — `deployment-state` was already counted inside that 49, not additional to it), and **4 named**
  UNCLEAR groups covering **5 physical** buckets (`commodity-signals-batch` has a `-prd`/`-test` pair, the other 3
  names are singletons). Net STRIP after the operator's `recon`→KEEP override: **47** (49 − 2 for `recon`).
  `portfolio-state` (already shipped/applied) stays counted in the 47.

  | Disposition | Buckets | Count | Rule (as classified 2026-08-16) |
  | --- | --- | --- | --- |
  | STRIP | `market-data-tick-{cefi,defi,pred,sports,tradfi}-{prd,test}` | 10 | COLDLINE@60 |
  | STRIP | `instruments-store-{cefi,defi,tradfi,sports,prediction}-{prd,test}` | 10 | COLDLINE@60 |
  | STRIP | `features-{cefi,defi,pred,sports,tradfi,calendar}-{prd,test}` | 12 | COLDLINE@60 |
  | STRIP | `ml-store-{prd,test}` | 2 | COLDLINE@60 |
  | STRIP | `execution-store-{prd,test}` | 2 | COLDLINE@60 |
  | STRIP | `strategy-store-{prd,pred-prd,test,pred-test}` | 4 | COLDLINE@60 |
  | STRIP | `portfolio-state-{prd,test}` | 2 | COLDLINE@60 — **applied 2026-08-16**, see entry above |
  | STRIP | `config-store-{prd,test}` | 2 | COLDLINE@60 |
  | STRIP | `uts-{dev,prod,staging}-deployment-state` | 3 | NEARLINE@30 |
  | **STRIP subtotal** | | **47** | |
  | KEEP (operator override) | `recon-{prd,test}` | 2 | COLDLINE@60 — report-shaped per `reconciliation-resolution.md`, not raw pipeline data; currently empty |
  | UNCLEAR — needs an explicit operator call, do not guess | `backtest-results-central-element-323112` | 1 | COLDLINE@14 — short window right as heavy backtesting starts |
  | UNCLEAR | `alerting-service-central-element-323112` | 1 | COLDLINE@60 — contents undocumented anywhere in codex |
  | UNCLEAR | `commodity-signals-batch-{prd(no suffix),test}` | 2 | prd: COLDLINE@60, test: none — owner marked UNKNOWN in `non-canonical-path-inventory.md` |
  | UNCLEAR | `pnl-attribution-output` (standalone) | 1 | none — looks like a dead orphan duplicate of the prefix already inside `portfolio-state-prd`; may just need deleting, not a lifecycle call |
  | **UNCLEAR subtotal** | | **5** | |
  | KEEP — audit/log-shaped, has a live rule | `central-element-323112-events`, `-deployment-events`, `-kill-switch-audit-log`, `-client-reports`, `-client-statements`, `-datapoint-validation`, `-defi-validation`, `manual-audit-prd`, `unified-trading-cicd-events`, `cf-manifest-audit-central-element-323112`, `-data-status-rollups`, `onchain-research-central-element-323112` | 12 | mostly COLDLINE@60 age-based (safe — never touches recent objects); 2 are permanent-delete rules (`cf-manifest-audit` Delete@90, `data-status-rollups` Delete@7), a different risk class, not lifecycle-cooling |
  | KEEP — audit/log-shaped, no live rule today | `manual-audit-test`, `trading-audit-records-{prd,test}`, `orats-smv-strikes-backup`, `phantom-triage`, `rescan-triage`, `pre-migration-snapshot`, `honest-coverage`, `benchmark-reports`, `benchmark-synthetic-input`, `build-metadata`, `databento-batch-registry-asia` | 12 | none — `trading-audit-records-*` carries a 7-year GCP Object Retention Lock, care needed if a rule is ever proposed |
  | Not trading-system data — GCP-managed, leave alone | `*.appspot.com`, `*_cloudbuild`, `gcf-sources-*`, `gcf-v2-sources-*`, `gcf-v2-uploads-*`, `firebaseapphosting-sources-*`, `run-sources-*` (4 regions), `central-element-323112-function-source` | 20 | n/a |
  | Infra/ops state — no lifecycle concern either way | `deployment-scripts`, `deployment-orchestration`, `client-reporting-data`, `terraform-state`, `uts-terraform-state`, `unified-deployment-state`, `orchestrator-creds` | 7 | version-count cleanup or none; `orchestrator-creds` must never cool if a rule is ever proposed |

  **Total: 47 + 2 + 5 + 12 + 12 + 20 + 7 = 105.** Updated the `[OPERATOR]` follow-up above to reference this table
  directly instead of asking for it to be produced — the remaining ask is narrower now: a call on the 4 named/5
  physical UNCLEAR buckets, then `canonical_strip_lifecycle_kinds` can be extended from 1 kind (`portfolio-state`) to
  the full 47 in one pass.

- **2026-08-17 (interactive session)**: three follow-up threads from the resource-sizing todo above, resolved with
  real evidence rather than left as speculation.
  - **10-jobs(IS+MTDS)/18-jobs-total→5-per-asset-group consolidation — OPERATOR REJECTED, not just unstarted.**
    Reasoning: combining multiple buckets into one container invocation means sizing RAM for the worst-case bucket
    in the group and running each bucket sequentially within one wall-clock window — directly contradicts the
    already-confirmed finding that per-bucket resource sizing (heavy buckets get their own large allocation) is
    what's actually working, and would make the market-data-cefi class of incident easier to reproduce, not harder.
    Do not resurrect this idea without new evidence changing the RAM/time tradeoff.
  - **Cadence-thinning for `market-data-defi`/`market-data-cefi`/`instruments-sports` (raised as a candidate, then
    tested against real data, then WITHDRAWN)** — initial reasoning from lock-TTL config (9000s/9000s/4200s)
    suggested these were mostly idle-polling gated by a long TTL, making a thinner cron "free." Live execution
    timestamps (`gcloud run jobs executions list`, corrected field path `status.startTime`/`status.completionTime`
    — the bare `startTime`/`completionTime` fields are empty, a gotcha worth remembering) contradicted this:
    `market-data-defi` and `instruments-sports` were both running real, fast (30-56s) merges on essentially every
    ~60-75s tick in the sampled window, not lock-gated no-ops. Cross-checked against Cloud Logging
    (`gcloud logging read`) — a 45-minute window showed EVERY `defi` cycle logging `shards=0` (zero real merges),
    confirming the frequent small merges are what keeps backlog from accumulating, not wasted polling. Thinning the
    cron would increase backlog between checks — the same condition that caused the `market-data-cefi` incident —
    not reduce risk. **Verdict: leave all three at their current cadence.** `market-data-cefi` already runs hourly
    as configured (confirmed via timestamps: real cadence-aligned executions at 22:00, 23:00, plus several
    off-hour manual verification triggers from this session's own agents, easy to mistake for organic traffic if
    not cross-checked against who was actively triggering things).
  - **"Is the consolidator re-pulling GB of canonical data on every cycle?" — checked against source, not logs
    alone.** `unified_trading_library/manifest_consolidator.py`'s `consolidate()` does a cheap GCS *list* on
    `_index/per_vm/` first (mtimes only, not shard content) to compute `shards_changed`; if that's zero it returns
    `no_op_unchanged=True` (line ~907) *before* reaching `_duckdb_consolidate_and_write`, where the canonical
    anti-join stream actually happens (gated `if ... shard_paths`, line ~3048). So a zero-shard cycle — confirmed
    the common case for `defi` in the sampled window — never touches the canonical at all; the 9-56s durations seen
    are list-overhead/cold-start, not a multi-GB re-read. When there GENUINELY are changed shards, the anti-join
    does stream the full canonical (memory-bounded, not I/O-bounded) — necessary work when it happens, not waste.
    **Verdict: the architecture already has the optimization this question was worried about; no fix needed.**
  - **Timeout-floor bump — extended the existing, still-uncommitted `market-data-cefi` diff rather than opening a
    second competing one on the same file** (re-verified the `unified-api-contracts` blocker is still live —
    identical 3 untracked files, unchanged mtime pattern — before touching anything). Bumped
    `manifest_consolidator_timeouts` for the 11 hourly-cadence buckets that were below a `>2x cadence` (7200s)
    floor: `instruments-{cefi,tradfi,defi,prediction}` 1800→7200, plus NEW entries for `features-{cefi,defi,tradfi,
    calendar}`/`strategy`/`execution`/`ml-training-artifacts` (previously falling through to the 300s default — an
    hour between triggers, 5 minutes to finish) at 7200. **Deliberately excluded** the per-minute buckets
    (`market-data-{sports,tradfi,prediction}`, `features-sports`) — real cadence there per the same evidence above,
    and `market-data-sports` has an explicit 1800s staleness SLA a longer *timeout* has nothing to do with anyway.
    Cost framing: a Cloud Run task timeout ceiling is free unless a run actually uses it, so this is pure insurance
    against the same failure class that just took `market-data-cefi` down, applied fleet-wide instead of waiting for
    each bucket to fail individually. `terraform fmt` run on the file after editing (real formatting delta, not a
    mistake — don't revert). `quality-gates.sh --no-fix` green (`deployment-service`, 236s — flagged by the resource-
    drift check as >2x the 106s baseline, consistent with the same host contention documented elsewhere in this
    plan, not a new problem). Quickmerge attempted and confirmed blocked on the identical, unchanged
    `unified-api-contracts` dependency — **not forced through**. Current state: both fixes (market-data-cefi
    resource sizing + the 11-bucket timeout floor) sit together in ONE ready-to-ship diff at
    `.tabs/4/deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf`, QG-green, waiting only on that
    other session's own commit.

- **na-eligibility-audit 2026-08-17** (infra tranche) [body-hash:5d942a38ce4c3053]: RECLASSIFY_SPLIT — extracted 3
  items to `infra_satellite_ao_dispatch_batch18_2026_08_17.md` (item 6: the 45-bucket lifecycle-strip Terraform diff
  + cost-gain tracking, combining the near-duplicate instance of the terraform-diff todo found in this doc — flagged
  as a real duplication, not re-extracted twice; item 7: ml_service + bespoke-cron watchdog wiring, merged into one
  todo to avoid a same-file concurrent-edit risk). Also closed one stale gate as moot (its own precondition doc
  resolved same-day, checkbox never flipped). Remaining open items (18-jobs consolidation re-scope, cold-start
  investigation, periodic OOM re-check, continuous-launcher design decision) are genuine judgment/investigation
  work — doc stays `assigned_vm: NA`. This doc is large and has documented its own concurrent-edit duplication
  history (see Progress Log above) — edits here were made conservatively, touching only the specific todo anchors
  needed for this run's extraction, not restructuring the doc.
- **context-scout 2026-08-17**: re-scouted; context_scope re-verified (4 entries), unchanged.

- **2026-08-17 (interactive session, UNCLEAR-bucket resolution + pnl-attribution-output correction)**: operator
  resolved all 4 UNCLEAR buckets. `backtest-results`/`alerting-service`/`commodity-signals-batch`/the full 47-bucket
  exemption ruling shipped as `deployment-service@2995d0cf` (see todo above for full detail).
  **`pnl-attribution-output` — the classification table's "dead orphan, may just need deleting" call was WRONG,
  caught by the delete-safety re-check this very todo's own remedy specified.** A dispatched Explore agent first
  corroborated "genuinely dead orphan, safe to delete" (zero live code references to the bucket NAME anywhere;
  strategy-service's real PnL-attribution writes resolve to `portfolio-state-prd` via `resolve_bucket_name`/UAC
  `PATH_REGISTRY`, confirmed via a 2026-07-19 migration doc's own parity check reading the bucket as empty at fold
  time). Both were consistent with an initial guess at the bucket's full name
  (`pnl-attribution-output-central-element-323112`) — which 404s, doesn't exist. The REAL bucket is the bare name
  `pnl-attribution-output` (matches strategy-service's own code comment: "the PnL-attribution output store was a
  BARE default bucket... never in cloud-providers.yaml"). Listing IT directly, immediately before the planned
  delete, found **7 real parquet files**, not zero: `by_strategy/ARBITRAGE_PRICE_DISPERSION/config_variant=
  funding-rate-dispersion/year=2024/month=01/2024-01-0{1..7}.parquet`. Operator recognized the shape and asked to
  check `e2e-testing` — confirmed: `e2e-testing/scripts/defi/test_apd_paper_e2e_smoke.py` +
  `scripts/strategy/scenarios/apd_price_dispersion_btc.json` +
  `reports/defi_paper_runs/arbitrage_price_dispersion_template.md` (which literally states
  `dispersion_type: funding-rate-dispersion`, `Archetype: ARBITRAGE_PRICE_DISPERSION (funding-rate-dispersion
  variant)`) is a dedicated paper-trading smoke-test suite for exactly this strategy/variant — the 7 files are its
  historical paper-run output (Jan 2024 is the smoke test's fixed simulated backtest window, not when the test
  itself ran). **Operator decision: keep the bucket and its 7 files permanently — it's a useful historical
  paper-run record, not touched further.** Lesson: a "confirmed empty" classification from 2 independent sources
  (a written migration doc AND a fresh dispatched-agent investigation) was still wrong, because both silently
  assumed a bucket-name pattern that doesn't hold for this one bucket — the delete-safety protocol's own
  "re-verify immediately before touching" step is what caught it, not the prior research. Neither source was
  lazy; both were victims of a plausible-but-wrong naming assumption neither had reason to question. See
  `/codex/12-agent-workflow/measurement-claims-discipline.md` for the general pattern this fits (an absence claim is
  a statement about the probe, not the target, until the probe is proven to have looked in the right place).

- **2026-08-17 (interactive session, remaining watchdog-coverage todos)**: resolved the two genuinely-open
  watchdog-coverage todos without needing an operator decision — both resolved cleanly from investigating the
  actual launcher code rather than being a real judgment call. **Compound-VM_SERVICE**: added native
  comma-separated multi-bucket support to `vm-exec-with-gcs-tee.sh`'s watchdog (rejected the "pick one primary
  bucket" alternative — it would leave the unpicked bucket's orphaned-shard risk unmonitored, defeating the
  mechanism). **Continuous/live**: wired `market_tick_data_service`+`live_websocket` launchers via a new §5d block;
  in the process, disproved the original todo's premise that `*-forward-poll.sh` launchers needed the same
  treatment — all 10 were verified to already be bounded, `VM_SHUTDOWN_ON_COMPLETION=true` tasks already covered
  by existing wiring, and one genuinely new gap (`launch-defi-forward-poll.sh`, a variable `--operation` flag) was
  found and tracked separately instead. 12 new test cases added (`TestVmExecMultiBucketWatchdog`,
  `TestSetupScriptWiresCompoundAndLiveLaunchers`), 3 pre-existing tests updated for the restructured nested-loop
  shape, all 34 passing. Also flipped the operator-rejected 18→5 job-consolidation todo to a CANCELLED marker (it
  was sitting unchecked despite being resolved on 2026-08-17) and updated
  `/codex/05-infrastructure/manifest-consolidator-ssot.md`'s coverage accounting to match.

- **2026-08-17 (interactive session, remaining watchdog-coverage todos)**: resolved the two genuinely-open
  watchdog-coverage todos without needing an operator decision — both resolved cleanly from investigating the
  actual launcher code rather than being a real judgment call. **Compound-VM_SERVICE**: added native
  comma-separated multi-bucket support to `vm-exec-with-gcs-tee.sh`'s watchdog (rejected the "pick one primary
  bucket" alternative — it would leave the unpicked bucket's orphaned-shard risk unmonitored, defeating the
  mechanism). **Continuous/live**: wired `market_tick_data_service`+`live_websocket` launchers via a new §5d block;
  in the process, disproved the original todo's premise that `*-forward-poll.sh` launchers needed the same
  treatment — all 10 were verified to already be bounded, `VM_SHUTDOWN_ON_COMPLETION=true` tasks already covered
  by existing wiring, and one genuinely new gap (`launch-defi-forward-poll.sh`, a variable `--operation` flag) was
  found and tracked separately instead. 12 new test cases added (`TestVmExecMultiBucketWatchdog`,
  `TestSetupScriptWiresCompoundAndLiveLaunchers`), 3 pre-existing tests updated for the restructured nested-loop
  shape, all 34 passing. Also flipped the operator-rejected 18→5 job-consolidation todo to a CANCELLED marker (it
  was sitting unchecked despite being resolved on 2026-08-17) and updated
  `/codex/05-infrastructure/manifest-consolidator-ssot.md`'s coverage accounting to match.

- **2026-08-18 (interactive session, cost-gain interim check)**: real `bq` pull against
  `billing_export.gcp_billing_export_resource_v1_016B25_109840_AF2ACB` (corrected table name — this doc had
  mis-transcribed it as `..._v1_resource_...` in the cost-gain-tracking todo above, fixed there too), 14-day window.

  | day | total manifest-consolidator net_usd |
  | --- | --- |
  | 08-13 | 124.17 |
  | 08-14 | 125.51 |
  | 08-15 | 120.38 |
  | 08-16 | 135.15 |
  | 08-17 | 95.12 |

  Only ONE day (08-17) post-dates the 2026-08-17 shipping date — not enough to separate the fix's effect from
  normal day-to-day variance. `market-data-cefi` specifically, isolated: 2.66 (08-15) → 5.06 (08-16, the emergency
  live `gcloud run jobs update` landed mid-session that day) → 7.93 (08-17, first full day + the `.tf` codification
  + the timeout-floor bump). **This is a CORRECT rise, not a regression** — before the fix this job was
  timeout-killed every cycle after ~3654s of pure waste (3 consecutive `Completed=False` runs, zero useful output);
  the fix trades a cheaper-but-useless cycle for a costlier-but-actually-completing one (~51s at 2x the resource
  allocation). A simple $/day delta is the wrong lens for this specific resource; the real win (incident resolved,
  canonical index no longer stale) isn't a cost line item. Verdict: genuinely too early, re-check once ~1 week of
  post-2026-08-17 data exists (see todo above, re-opened).

- **2026-08-18 (interactive session, CUD-revisit interim check)**: re-ran the live-service resource-name query from
  `/plans/active/compute_flexible_cud_sizing_analysis_2026_08_16.md` (not the full formal re-analysis — that stays
  scheduled for ~2026-09-15 — just an early look, since the original "wait for growth to stabilize" premise is
  worth checking against real data before assuming it still holds). 33-day pull, `mtds-{dex-swaps,perp-funding,
  dex-pools,live-cefi-consolidated,live-sports-odds-api-trades}` + `mdps-features-live-{cefi,defi}`:

  | period | trend |
  | --- | --- |
  | 07-15 to 07-18 | ~$1-2/day (negligible) |
  | 07-22 to 07-29 | ramping ~$1 → ~$15/day |
  | 07-30 to 08-05 | ~$28-35/day |
  | 08-06 to 08-08 | $8.56 → $0 → $0 (gap — same 2 zero-days appear in the manifest-consolidator pull above too,
    smells like a billing-export gap rather than coincidental real zero-usage across two unrelated resource sets,
    not investigated further here) |
  | 08-09 to 08-13 | recovered, climbed to a peak of $40-48/day |
  | **08-14 to 08-17** | **declining 4 days straight: 38.71 → 35.77 → 32.92 → 16.93** |

  This is materially different from the 2026-08-16 doc's "still growing" finding — the population isn't just
  plateauing, it's actively falling over the most recent 4 days. Cause not investigated (could be a real stabilization,
  a temporary dip, or something got stopped — worth a separate look if it persists). **This argues for waiting
  LONGER, not shorter** — sizing a 1-year commitment against a population moving in an unclear direction (up, down,
  or about to reverse) carries the same risk whichever direction it's moving. Recommend shortening the re-check
  cadence from the original 30-day wait to ~1-2 weeks specifically to resolve whether this is a real trend before
  the scheduled 2026-09-15 full re-analysis, rather than waiting the full window blind to this new signal.

- **na-eligibility-audit 2026-08-18** (infra tranche) [body-hash:abc124b3751e0a04]: KEEP-NA, valid — unchanged at
  the doc level since 2026-08-17. New since then: a 5th open item surfaced 2026-08-17
  (`launch-defi-forward-poll.sh` watchdog coverage) not previously assessed by this skill. Tagging
  MISCLASSIFIED_LIKELY_AO_ELIGIBLE for a future run's re-assessment rather than extracting now: its 3 completed
  siblings (ml_service, compound-VM_SERVICE, bespoke `*_daily_cron` watchdog wiring) all needed real per-launcher
  investigation before turning out to be non-judgment-calls, so this one's own boundedness isn't yet confirmed;
  combined with this file's own extensively-documented concurrent-edit fragility (lost content, duplicated Progress
  Log entries — see entries above), a conservative touch was made this round. The other 4 open items (cost-gain
  tracking — confirmed genuinely too early per the 2026-08-18 interim check; cold-start investigation; periodic
  instruments-sports OOM re-check with no concrete trigger; the operator-rejected 18→5 consolidation, already
  CANCELLED) remain genuine judgment/time-gated/research work, not worker-determinable.

- **na-eligibility-audit 2026-08-18** (infra tranche, dispatch agt-80fafa, slot 29) [body-hash:10a82d75ddb34c7c]:
  RECLASSIFY (per-todo split) — closed the loop on the `launch-defi-forward-poll.sh` watchdog-coverage item this
  same doc's prior same-day marker (above, dispatch agt-6a3d46) tagged `MISCLASSIFIED_LIKELY_AO_ELIGIBLE` pending a
  second look. Confirmed bounded: its 3 completed siblings (ml_service, compound-VM_SERVICE, bespoke `*_daily_cron`
  watchdog wiring) were all resolved without an operator decision once the real launcher code was investigated, and
  this item's own framing carries the identical "confirm real write target, then wire" shape — no design fork
  evident. Conflict-check clear (grepped every active `assigned_vm: planning` doc in `parent_epic:
  infrastructure_master` for `defi-forward-poll`: 2 hits, both non-overlapping —
  `data_completion_to_100_all_ag_2026_06_21.md` is about running/deploying the live poller, not watchdog wiring;
  `infra_satellite_ao_dispatch_batch17_2026_08_16.md` fixed an unrelated duplicated-block/stale-string bug in the
  same script file, already shipped; no draft-status legacy satellite doc references it). Extracted to
  `infra_satellite_ao_dispatch_batch20_2026_08_18.md` item 1. The other 4 open items (cost-gain tracking, cold-start
  investigation, periodic instruments-sports OOM re-check, the operator-rejected 18→5 consolidation already
  CANCELLED) re-confirmed genuine judgment/time-gated/research work on independent re-read — doc stays
  `assigned_vm: NA` for those.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
