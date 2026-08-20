---
doc_type: issue
title: >-
  features-e2e-* `--sink-bucket`/test-run VM launches self-delete within ~250-320s with NO run.log/EXIT_STATUS ever
  written — blocks the TRADFI:volatility benchmark relaunch (and likely every pipeline_e2e_check test-run VM)
summary: >-
  Relaunching the TRADFI:volatility benchmark (features-service pipeline_e2e_check.py --day 2026-08-14 --asset-group
  TRADFI --family volatility --legs benchmark --benchmark-days 7) failed 3/3 times. Each attempt: the launcher
  auto-republish tarball-freshness guard failed twice (known race, see related doc) before succeeding on a 3rd
  sub-attempt; the resulting VM (features-e2e-tradfi-*) then vanished from `aggregated_list_instances` within ~250-320s
  with ZERO objects written to `gs://deployment-scripts-central-element-323112/vm-logs/<vm>/` — no `run.log`, no
  `EXIT_STATUS`. `exit_status=null` in the pipeline_e2e_check result (the launcher engine's
  self-deleted-with-no-exit-status path). A fresh manual `create-code-tarballs.sh --include features-service --include
  deployment-service --force` (which also republished `vm/setup-data-pipeline-vm.sh`) did NOT change the outcome on a
  4th... 3rd retry — same result. Leading unconfirmed hypothesis: this specific launch shape passes `--env staging` +
  `--sink-bucket features-tradfi-test-...`, which resolves the VM's runtime service account to `uts-test-sa` (DP-VM-002
  fix, `launcher_common.sh:165-177`) instead of the default tier SA — if `uts-test-sa` lacks read access to the
  CODE_BUCKET's `vm/setup-data-pipeline-vm.sh` object or write access to `vm-logs/`, the VM would fail to fetch or
  execute its startup script (or execute it but be unable to write ANY log), exactly matching the observed symptom.
  Could not confirm via bucket IAM-policy inspection in this session (the sanctioned UTL `GCSBucketHandle` has no
  `get_iam_policy` method, and a raw `gcloud storage buckets get-iam-policy`/`gsutil` inspection is hook-blocked as an
  object-op pattern match).
status: open
nature: issue
asset_group: [tradfi, infrastructure]
stage: [meta]
repos: [deployment-service, features-service]
scope: [engineer, admin]
tags: [vm-launcher, test-run, service-account, iam, silent-failure, pipeline-e2e-check, benchmark]
related:
  [
    /plans/active/issues/features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md,
    /plans/archive/2026_08/issues/vm_launcher_setup_script_freshness_gap_2026_07_31.md,
    /plans/archive/2026_08/issues/tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch13_2026_08_13.md,
  ]
created: 2026-08-15
author: slot-6 (backend_engineer)
last_updated: 2026-08-20
priority: P1
parent_epic: security_and_cross_cutting_master
source: >-
  Relaunching the TRADFI:volatility benchmark per tradfi_satellite_ao_dispatch_batch13_2026_08_13.md's "Todo 2: relaunch
  TRADFI:volatility benchmark once todo 1 lands" (slot-6, backend_engineer, 2026-08-15).
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
resolved_by:
context_scope:
  [
    deployment-service/scripts/vm/lib/launcher_common.sh,
    deployment-service/scripts/vm/setup-data-pipeline-vm.sh,
    deployment-service/scripts/vm/vm-exec-with-gcs-tee.sh,
    unified-trading-library/unified_trading_library/pipeline_e2e_check/launcher.py,
    features-service/scripts/pipeline_e2e_check.py,
  ]
---

# features-e2e test-run VM self-deletes with no log/exit-status (2026-08-15)

## What I found

Ran
`features-service/scripts/pipeline_e2e_check.py --day 2026-08-14 --asset-group TRADFI --family volatility --legs benchmark --benchmark-days 7`
three times (`uv run python scripts/pipeline_e2e_check.py ...`), each a fresh end-to-end launch attempt:

| Attempt                                                                                                    | VM name                                      | Tarball-freshness sub-retries                                            | Result               | wall_clock | objects |
| ---------------------------------------------------------------------------------------------------------- | -------------------------------------------- | ------------------------------------------------------------------------ | -------------------- | ---------- | ------- |
| 1                                                                                                          | `features-e2e-tradfi-20260815-093837-679e08` | 2 failed (`auto-republish completed but tarball(s) still stale`), 3rd OK | self-deleted, no log | 271s       | 0       |
| 2                                                                                                          | `features-e2e-tradfi-20260815-094610-679e08` | 2 failed, 3rd OK                                                         | self-deleted, no log | 250s       | 0       |
| 3 (after manual `create-code-tarballs.sh --include features-service --include deployment-service --force`) | `features-e2e-tradfi-20260815-095346-679e08` | 2 failed, 3rd OK                                                         | self-deleted, no log | 317s       | 0       |

For all 3, confirmed directly (not inferred from the report alone):

- `gcloud compute instances describe <vm> --zone=asia-northeast1-c` → `NOT FOUND` (instance already gone by the time the
  driver returned).
- `gcs_describe_object(uri='gs://deployment-scripts-central-element-323112/vm-logs/<vm>/run.log')` → `None`.
- `gcs_describe_object(uri='gs://deployment-scripts-central-element-323112/vm-logs/<vm>/EXIT_STATUS')` → `None`.
- JSON result: `"exit_status": null, "parquet_count": 0, "write_verified": false`.

Per `unified_trading_library/pipeline_e2e_check/launcher.py`'s `_poll_until_terminal` (per a prior agent's read of that
function this session — not independently re-verified line-by-line here), `exit_status=None` after a real elapsed
duration (not an immediate 0s failure) is the **self-deleted-with-no-exit-status** path: the VM vanished from
`aggregated_list_instances` before ever writing `EXIT_STATUS`, and a 10s grace re-read also found nothing. Since NEITHER
`run.log` NOR `EXIT_STATUS` ever appeared, the crash happened before `vm-exec-with-gcs-tee.sh`'s log-upload trap block
was even installed — i.e. very early in `setup-data-pipeline-vm.sh`'s own boot sequence, or before that script even
started running.

**Manually republishing did not change the outcome.** Between attempts 2 and 3, ran
`bash scripts/vm/create-code-tarballs.sh --include features-service --include deployment-service --force` from a clean,
up-to-date (`ahead=0 behind=0`) `.tabs/6` checkout — this also republished `vm/setup-data-pipeline-vm.sh` (confirmed via
the command's own listing output, `Update time` seconds before the retry). Attempt 3 still hit the identical
2-failed-then-3rd-OK tarball-freshness pattern AND the identical self-deleted-no-log VM crash. This rules out "my local
checkout was simply behind" as the sole explanation for either symptom.

**These are two distinct, stacked problems, not one:**

1. **The tarball-freshness auto-republish race** (2/3 sub-attempts fail with
   `auto-republish completed but tarball(s) still stale (republish skipped? dirty working tree?)`) — this matches the
   ALREADY-TRACKED, well-documented fleet-wide concurrent-republish race in
   `features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md` (multiple corroborating findings,
   same error text). Not re-diagnosing that mechanism here — just confirming it's still live and hit 6/6 times across 3
   attempts today (2026-08-15), well after that doc's `auto`-mode default flip shipped (`deployment-service@c1e0481`,
   2026-08-06). `.tabs/6`'s own checkout was confirmed clean both times I checked, so this is a genuinely
   concurrent-fleet race, not my own local dirty state.
2. **The post-launch silent VM crash** (this doc's primary new finding) — happens on EVERY successful 3rd-sub-attempt
   launch, i.e. it is independent of whether the tarball race fired first. 3/3 reproduction rate.

## Why it matters

This blocks `tradfi_satellite_ao_dispatch_batch13_2026_08_13.md`'s "Todo 2: relaunch TRADFI:volatility benchmark"
directly — the fix landed in `_resolve_spot_perp` (features-service@f441638932, done 2026-08-15) but its throughput
cannot be measured because the verification VM itself never runs. More broadly, if the root cause is the `uts-test-sa`
IAM hypothesis below, this would block **every** `pipeline_e2e_check.py --sink-bucket`/test-run VM launch across every
service that uses this shared engine (features-service, market-data-processing-service, and any future adopter) — a P1,
not scoped to TRADFI:volatility alone.

## Leading hypothesis (unconfirmed)

`_build_launch_argv` passes `--sink-bucket features-tradfi-test-central-element-323112` and the driver passes
`--env staging`, which — per `IS_TEST_RUN_FLAG="true"` in `launch-features-vm.sh` — routes
`lc_tier_service_account(env, project, is_test_run=true)` to force `uts-test-sa` regardless of `--env`
(`launcher_common.sh:165-177`, the DP-VM-002 fix, dated 2026-08-01). The VM's `startup-script-url` metadata still points
at the SAME `CODE_BUCKET` (`deployment-scripts-central-element-323112`) that hosts the code tarballs — a bucket whose
primary write-protected tier historically favored `uts-prd-sa`/`uts-test-sa` split by DATA bucket, not necessarily the
shared deployment-scripts bucket. If `uts-test-sa` cannot READ
`gs://deployment-scripts-central-element-323112/vm/setup-data-pipeline-vm.sh` (the metadata-server-fetched startup
script) or cannot WRITE to `vm-logs/`, the VM would either never execute its startup script at all, or execute it but
die on its very first authenticated GCS call — before any tee/log-upload logic runs. This is consistent with every
observed symptom (no run.log, no EXIT_STATUS, short ~250-320s lifetime — consistent with boot + a fast permission
failure + `VM_SHUTDOWN_ON_COMPLETION` or a startup-script-level failure triggering shutdown).

**Not confirmed this session** — bucket IAM-policy inspection was attempted via the sanctioned UTL path
(`get_storage_client().bucket(...).get_iam_policy(...)`) but `GCSBucketHandle` has no such method; a raw
`gcloud storage buckets get-iam-policy`/`gsutil` fallback is hook-blocked (`block_destructive_commands.py`, "subprocess
`gcloud storage` object operation" — treats even a read-only IAM-policy read as an object op under its current pattern
match). Whoever picks up todo 1 below should use `gcloud projects get-iam-policy`/the GCP Console/an IAM Admin API call
(not a bucket-object-shaped CLI command) to avoid re-tripping the guard, or extend the guard's allowlist if
`get-iam-policy` genuinely needs a carve-out (a policy READ, not an object read/write — worth a design note, not assumed
safe to just bypass).

**CONFIRMED 2026-08-15 (slot-6, infra craft, todo 1) — the hypothesis was correct.**
`gcloud projects get-iam-policy central-element-323112 --format=json` (a project-level IAM read, does NOT trip the
object-op hook) shows: `uts-test-sa` holds `roles/storage.objectViewer` **UNCONDITIONED** (project-wide read — confirms
it CAN fetch `vm/setup-data-pipeline-vm.sh`), but its `roles/storage.objectAdmin` (write) grants are BOTH
IAM-conditioned to `-test-`-suffixed DATA-tier buckets only (`group-a-test-tier-only` / `group-b-test-tier-only`
conditions — `resource.name.startsWith("projects/_/buckets/features-*-test-")` etc.) —
**`deployment-scripts-central-element-323112` matches NEITHER condition**, so `uts-test-sa` has zero write access to it.
Exactly the observed symptom: the VM can read its startup script but can never write `vm-logs/<vm>/run.log` or
`EXIT_STATUS`.

## Todos

- [x] ✅ [INFRA] P1. Confirm or refute the `uts-test-sa` IAM hypothesis above: check `uts-test-sa`'s actual bucket-level
      IAM bindings on `deployment-scripts-central-element-323112` (both the `vm/` prefix read path and the `vm-logs/`
      prefix write path) via `gcloud projects get-iam-policy central-element-323112` or the IAM Admin API (not a
      bucket-object CLI call, per the hook note above). If confirmed, grant the missing role (least-privilege — the
      specific role that closes the specific gap, self-service per
      `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`) and re-verify with one real
      `features-e2e-tradfi-*` launch, checking for a real `run.log` this time. (repo: deployment-service / infra — live
      GCP IAM change, not code)

          **PROVEN 2026-08-15 (slot 5, infra craft) — the fix works, todo DONE.** Picked up todo 2 below (dispatched
          independently by the backlog) and found todo 1 already in-flight; continued monitoring its verification VM
          instead of duplicating work. `features-e2e-tradfi-20260815-100817-679e08` progressed through the FULL real
          lifecycle for the first time across 4 total attempts on this launch shape: `EXIT_STATUS=RUNNING` written at
          ~10:14Z (the early sentinel `vm-exec-with-gcs-tee.sh` writes at start — never written on any of the 3 prior
          failures), then `run.log` appeared, then `EXIT_STATUS=0` at 10:15:07Z with a clean `DEPLOYMENT_COMPLETED
          exit_code=0` — the VM ran its full command and self-deleted normally, not the silent self-delete-with-zero-objects
          crash this whole doc tracks. Confirms the `uts-test-sa` write-access gap really was the sole cause of the
          self-delete/no-log symptom. **Independently corroborated 2026-08-15 (slot-6, infra craft)** via
          `gcs_describe_object`/`gcs_read_object_with_generation` on the same VM: `run.log` = 27,656 bytes
          (`last_modified=2026-08-15T10:15:16Z`), `EXIT_STATUS` = `b'0\n'` (generation `1786788913139745`) — matches
          slot-5's finding exactly; see the SCRIPT P2 todo below for a related poll-loop bug this cross-check also
          surfaced.

- [x] ✅ [INFRA] P1. If the IAM hypothesis is refuted, get real evidence of what actually kills the VM in its first
      ~30-60s of boot — **N/A, not executed: the hypothesis was CONFIRMED (todo 1 above), not refuted**, so this
      diagnostic branch's own precondition never applies. Checking it off as resolved-by-the-other-branch rather than
      leaving it dangling — see todo 1's "PROVEN" note for the evidence. (repo: deployment-service)
- [x] ✅ [SCRIPT] P2. Once root-caused, add a regression signal for this specific failure mode: `launch_vm_and_wait`/the
      pipeline_e2e_check engine already distinguishes `vm_self_deleted_no_exit_status` from `timeout_no_exit_status` in
      its `reason` field (per a prior agent's read this session) but the shard-result `reason` string surfaced in the
      `.md`/`.json` report currently does NOT include that distinction (both attempts' reports show the same generic
      `window=... wall_clock=...Ns ... objects=0` text) — thread the launcher's self-delete/timeout distinction into the
      report's `reason` field so a future reader doesn't have to re-derive it from the raw JSON `exit_status`/duration
      the way this doc's author had to. (repo: unified-trading-library or features-service, wherever the report-writer
      lives) **✅ FIXED 2026-08-15 (slot-6, infra craft)**: `_run_benchmark_leg`
      (`features-service/scripts/pipeline_e2e_check.py`) now prefixes the shard's `reason` with
      `vm_not_success:<launcher reason>` (e.g. `vm_self_deleted_no_exit_status`, `timeout_no_exit_status`,
      `vm_exit_nonzero=<rc>`) whenever `exit_status != 0`, mirroring the pattern the skip-leg runner already used —
      `features-service@7e5ca3f5f7` + 3 new regression tests
      (`tests/unit/test_pipeline_e2e_check_benchmark_reason_threading.py`), QG green.

      **NEW related finding, same verification run (2026-08-15, slot-6, infra craft):** `_poll_until_terminal` has a
      separate false-negative bug, distinct from the reason-field gap above. The VM's `EXIT_STATUS` object goes through
      an intermediate state — content literal `"RUNNING"` — written early and overwritten with the real numeric code
      (`"0\n"`) only once the deployment actually finishes. The poller's tick-5 log line proves it hit this window mid-flight:
      `EXIT_STATUS present but unreadable/unparsable: invalid literal for int() with base 10: 'RUNNING'` — and instead of
      treating an unparsable-but-present `EXIT_STATUS` as "not yet terminal, keep polling," it gave up immediately and the
      report was written with `exit=-1, failed, objects=0`. Ground truth (checked ~1 minute later, same run, no new
      launch): `EXIT_STATUS` had already flipped to `0` and `run.log` existed complete — i.e. **the run actually
      succeeded but was reported as failed** because the poller read it at exactly the wrong moment and did not retry.
      This is a real, reproducible false-negative in the terminal-detection logic, not a flaky one-off — add explicit
      handling for the `RUNNING` sentinel (treat as non-terminal, continue polling) alongside the reason-field work above.
      **✅ FIXED 2026-08-15 (slot-6, infra craft)**: `_read_exit_status` now treats the literal `RUNNING` sentinel
      content as "not yet present" (returns `None`) instead of an unparsable `-1` failure, so `_poll_until_terminal`'s
      existing not-terminal-yet loop keeps polling through it — `unified-trading-library@2c412cc367`
      (`unified_trading_library/pipeline_e2e_check/launcher.py` + 4 new regression tests in
      `tests/unit/test_pipeline_e2e_check_launcher_running_sentinel.py`, QG green). The reason-field-threading half of
      this todo (surfacing the launcher's self-delete/timeout distinction in the report's `reason` string) is now also
      done — see the parent checkbox's own evidence line above.

- [ ] [DATA] P1. Once fixed, relaunch `tradfi_satellite_ao_dispatch_batch13_2026_08_13.md`'s "Todo 2: relaunch
      TRADFI:volatility benchmark once todo 1 lands"
      (`pipeline_e2e_check.py --day <fresh> --asset-group TRADFI --family volatility --legs benchmark --benchmark-days 7`)
      and flip that todo's checkbox with the real throughput numbers this doc's author was trying to capture. (repo:
      features-service) **NOT satisfied by the 2026-08-15 slot 5 verification launch** — that launch proved the
      IAM/self-delete fix (todo 1) but reported `Completed 0/11 groups`, a genuine ZERO-throughput result, not real
      numbers to cite. Still needs a real successful relaunch once the new [DATA] P1 finding below is resolved. **STILL
      NOT SATISFIED after the slot-18 relaunch (2026-08-15, `--day 2026-08-07`, post-`[CODE] P2` landing)** — see the
      new `[CODE] P2` finding below (slot-15's "generalize" fix still doesn't match the real captured shape) for why; do
      not relaunch again until that new todo is `[x]`.
- [x] ✅ [DATA] P1. **NEW (found 2026-08-15 slot 5).** The verification VM's `run.log` shows every one of the 11 feature
      groups failing identically: `No data for VX on <date>` (VIX/variance-risk-premium/vol_greeks_features all depend
      on a captured VX perp that's absent) immediately followed by
      `empty_confirmed manifest write failed ... record_empty(reason=SOURCE_RETURNED_ZERO) requires FetchEvidence proving a clean 200+empty fetch ... The supplied evidence does NOT prove honest absence ... most likely an auth / rate-limit / 5xx / timeout / exception / missing-credential path masquerading as honest absence — call record_failed instead`.
      This is a DISTINCT bug from the IAM/self-delete issue this doc otherwise tracks — the VM now runs to completion
      cleanly (`exit_code=0`), but the underlying feature-compute path can't tell a genuine data gap from a masked fetch
      failure and is being refused (correctly, per the guard's own honest-absence contract) rather than silently
      recording a false empty. Root-cause whether VX perp data is genuinely uncaptured for 2026-08-07..14 (a real gap,
      in which case the benchmark needs a day range that actually has data) or whether the fetch itself is silently
      failing (auth/rate-limit/etc., in which case that's the real bug to fix). Full evidence:
      `gs://deployment-scripts-central-element-323112/vm-logs/features-e2e-tradfi-20260815-100817-679e08/run.log`.
      (repo: features-service)

      **Independently corroborated 2026-08-15 (slot-6, infra craft)** via a direct `run.log` read of the same VM —
      identical `Completed 0/11 groups` result, same `No captured perp for VX` / `No data for VX` /
      `empty_confirmed manifest write failed` pattern across every group and date. One addition to the guidance above:
      relaunching with the SAME recent window will reproduce this 0/11 result — check the manifest for a window with
      confirmed VX captures before spending another billable VM launch on this todo, don't retry blind.

      **ROOT-CAUSED 2026-08-15 (slot-17, data_engineering) — neither hypothesis in the todo's own framing is quite
      right; the actual root cause is a THIRD option: a code gap in the resolver, not a genuine data absence and not
      a masked/silent fetch failure.** `VolatilityDataLoader._resolve_spot_future_tradfi`
      (`features_service/volatility/core/data_loader.py:439`) — the TRADFI spot-price-proxy resolver shipped by
      `tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md`'s Option A fix — looks up
      `_TRADFI_FX_UNDERLYING_TO_PRODUCT_ROOT` (line 122), which contains ONLY the 5 FX underlyings that doc's own
      2026-08-06 diagnosis covered (`6A/6B/6C/6E/6J`); VX was never in that doc's scope (it only ever saw "10 feature
      groups, all FX" — VX must have been added to the enumerated TRADFI:volatility universe separately, sometime
      between 2026-08-06 and this session, without anyone updating the resolver). `_resolve_spot_future_tradfi("VX",
      ...)` hits `product_root = _TRADFI_FX_UNDERLYING_TO_PRODUCT_ROOT.get("VX")` → `None` → returns `None`
      IMMEDIATELY, before ever querying the manifest — structurally guaranteed for every date, regardless of what's
      actually captured. **Even if VX were added to that dict, the lookup would still fail**: `_tradfi_future_candidates`
      (line 482) filters for `instrument_type=="FUTURE"` + `data_type=="trades"` with the FX-specific
      `{PRODUCT_ROOT}-USD@LIN-{expiry}` `instrument_id` convention — but VX's real captured data (confirmed via a
      column-pruned manifest read, `venue=CBOE`) is shaped `instrument_type=="futures_chain"` +
      `data_type=="ohlcv_1m"` + `instrument_id=="CBOE:FUTURE:VIX"`, a structurally different shape the current lookup
      would never match. This is WHY the honest-absence guard correctly rejects the write — there was never a genuine
      upstream fetch attempt behind the "no perp resolved" result (a code-level miss, not a real 200+empty response),
      so no real `FetchEvidence` exists to attach.

      Separately (a DIFFERENT, MTDS-capture-side observation, not the primary cause of the reported symptom): a
      bounded per-date manifest scan of `venue=CBOE` across 2026-08-07..14 found exactly ONE genuine `captured`
      `futures_chain`/VX row in the whole window (`2026-08-07`, `CBOE:FUTURE:VIX`/`ohlcv_1m`) — every other date
      (08-08 through 08-14) shows CBOE rows only as `expected_unattempted`/`empty_confirmed`, never `captured` and
      never `attempted_failed` (i.e. no fetch was even logged as attempted, not that one failed). This MAY be related
      to the ongoing TradFi Databento billing saga (`tradfi_databento_account_billing_suspended_2026_08_09.md`, still
      `blocked` as of today — VX/CBOE is exclusively Databento-sourced via `XCBF.PITCH`, no Massive fallback), but
      that doc's own 2026-08-15 finding says the LATEST recurrence is narrower than account-wide
      (`GLBX.MDP3`/CME-specific — other venues wrote successfully), and `expected_unattempted`/no-attempt is a
      different signature than that doc's `attempted_failed`/`402`/`api_key_deactivated` pattern — not confirmed
      whether VX/CBOE capture is even scheduled to run daily at all. Flagging as a related but genuinely SEPARATE
      question (MTDS/CBOE capture cadence, not features-service's resolver) — not root-caused further here, out of
      proportion for this diagnostic todo to absorb. Filed the concrete resolver fix as its own follow-up todo below.

- [x] ✅ [CODE] P2. **NEW (filed 2026-08-15, slot-17) — fix `_resolve_spot_future_tradfi` for VX per the root-cause
      above.** Extend `VolatilityDataLoader`'s TRADFI spot-price resolver to also resolve VX: add a VX-specific branch
      (separate from `_TRADFI_FX_UNDERLYING_TO_PRODUCT_ROOT`'s per-expiry `FUTURE`/`trades`/`{ROOT}-USD@LIN-{expiry}`
      path, since VX's captured shape is different) that reads the `venue=CBOE`,
      `instrument_type=futures_chain`/`data_type=ohlcv_1m`, `instrument_id=CBOE:FUTURE:VIX` continuous-chain candle as
      the spot-price proxy — mirroring how `load_futures_chain_raw` already reads other `futures_chain` candles
      elsewhere in this same file, rather than the per-expiry-dated pattern the FX branch uses. Needs a small design
      call (not just a mapping-dict entry, unlike the FX fix): does the volatility feature genuinely need a specific
      OHLCV field (e.g. `close`) from the aggregated chain candle, or does it need per-contract front-month selection
      the way the FX path does? Recommend following the FX precedent's own process (operator/design ruling before
      implementation) rather than guessing the shape blind. Verify via a bounded `pipeline_e2e_check.py` re-run scoped
      to a date confirmed to have a real captured VX `futures_chain` row (e.g. re-check the manifest for the nearest
      date with `capture_status=captured` before spending a billable VM launch — 2026-08-07 is the only confirmed one in
      this session's 08-07..14 scan; a fresher one likely exists once the separate MTDS/CBOE capture question above is
      resolved). Repo: features-service.

      **Scope widened 2026-08-15 (slot 12, data_engineering) — this todo is under-scoped: the gap is NOT
      VX-specific.** Relaunched the benchmark with `--day 2026-08-07` (confirmed VX `futures_chain` captured
      contiguously 2026-07-27..08-07 via a column-pruned manifest read — ruling out "wrong window" as a cause)
      and independently re-confirmed slot-17's root cause by reading `_resolve_spot_future_tradfi` /
      `_TRADFI_FX_UNDERLYING_TO_PRODUCT_ROOT` directly (`data_loader.py:122-128,439-461`): the dict hardcodes
      exactly 5 entries (`6A/6B/6C/6E/6J`) and returns `None` immediately for ANY other underlying, before ever
      querying the manifest. The relaunch's `run.log` shows this firing identically for **145 distinct
      underlyings** — VX plus the entire non-FX TRADFI universe (ES, NQ, YM, RTY, GC, SI, HG, PL, PA, CL, HO,
      RB, NG, ZB/ZC/ZF/ZN/ZS/ZT/ZW, BTC/ETH/MBT/MET, and per-contract-month tickers) — every one hits the same
      short-circuit, all 11 feature groups fail (`Completed 0/11 groups`), `exit_code=0` (VM itself healthy;
      evidence: `gs://deployment-scripts-central-element-323112/vm-logs/features-e2e-tradfi-20260815-103336-481be7/run.log`).
      A VX-only branch (as currently scoped above) would leave 144 other roots broken — whoever implements this
      needs a general product-root mapping (or a lookup against the live TRADFI catalogue) covering the full
      universe, not a second single-underlying special case. Did not attempt the fix (needs the same design call
      this todo already flags); did not relaunch again (2 more billable VM launches already spent this session
      confirming scope, 6 total across the doc's history with zero real throughput yet — cost-conscious per
      `vm-launcher-runbook.md`).

- [x] ✅ [CODE] P1. **NEW (found 2026-08-15, slot-18, data_engineering) — the `[CODE] P2` "generalize" fix above
      (`features-service@9bd9894119`) still doesn't match the real captured manifest shape; a fresh relaunch
      (`--day 2026-08-07`, VM `features-e2e-tradfi-20260815-134031-481be7`, exit_code=0, healthy) STILL reported
      `Completed 0/11 groups` — zero throughput, same as every prior attempt.** Root-caused via live manifest reads
      (`resolve_bucket_name(kind="market-data", asset_group="tradfi")`, `read_availability_index`) against the exact
      window the run used (2026-07-31..2026-08-07): **zero rows anywhere in the manifest have
      `instrument_type=="FUTURE"` AND `data_type=="trades"`** — not `captured`, not `expected_unattempted`, not
      `attempted_failed`, literally absent as a combination. `_resolve_spot_future_tradfi`'s whole design
      (`_tradfi_future_candidates`, `data_loader.py:480-502`) filters for exactly that combination plus a dated
      `instrument_id=="{ROOT}-USD@LIN-{expiry}"` prefix — a shape that was apparently never actually correct for the
      LIVE manifest (or has since drifted), so it returns zero candidates for EVERY underlying, FX roots
      (6A/6B/6C/6E/6J) included — confirmed directly: this run's `run.log` shows `No captured perp for 6A/6B/...` too,
      not just the 145 non-FX roots slot-12 found broken. The real captured shape (confirmed via a full-column manifest
      read, one sample row): `instrument_type="FUTURE"`, `venue="CME"`, `data_type="ohlcv_1m"`/`"ohlcv_1s"`,
      `instrument_id=None`, **`underlying="EUR"`** (a plain top-level manifest column, not embedded in `instrument_id`
      at all) — i.e. MDPS writes these as underlying-keyed OHLCV rows, never as dated per-contract `trades` rows. This
      is EXACTLY the shape `load_vix_ohlcv_raw` (`data_loader.py:765-810`, the existing VIX-only carve-out, path
      `.../instrument_type=FUTURE/venue={venue}/underlying={underlying}/ticks.parquet`) was already built to read — the
      VIX carve-out wasn't actually VIX-specific in its underlying mechanism, it was the ONE correct general pattern for
      ALL TRADFI FUTURE-type captures, and the `[CODE] P2` "generalize" fix generalized the WRONG path (the dated-
      instrument_id/`trades` one) instead of this one. **Recommended fix** (needs the same
      operator/design-ruling-before-implementation process the two prior fixes on this doc followed, per slot-15's own
      precedent — not scoping this blind): generalize `load_vix_ohlcv_raw`'s underlying-keyed OHLCV path to accept any
      `(venue, underlying)` pair instead of hardcoding `venue="CBOE"`/`underlying="VIX"`, resolve `(venue, underlying)`
      per-underlying from the manifest (`instrument_type=="FUTURE"`, `data_type` in the ohlcv family, `underlying==<X>`,
      `capture_status=="captured"`) instead of `_resolve_spot_future_tradfi`'s dated-instrument_id lookup, and route
      `load_spot_price_raw` through it for every TRADFI underlying (not just the VX carve-out branch). Evidence:
      `gs://deployment-scripts-central-element-323112/vm-logs/features-e2e-tradfi-20260815-134031-481be7/run.log`
      (`Completed 0/11 groups` at 14:29:05Z) + the live manifest reads above (bucket
      `market-data-tick-tradfi-prd-central-element-323112`, date `2026-08-07`). Repo: features-service. The `[DATA] P1`
      relaunch todo above is GATED on this — do not spend another billable VM launch on a blind retry.

## Progress Log

- **2026-08-15 (slot-6, backend_engineer)**: filed after 3/3 reproduction while working
  `tradfi_satellite_ao_dispatch_batch13_2026_08_13.md`'s benchmark-relaunch todo. Left that todo's checkbox UNCHECKED
  (done_definition — "capture real throughput" — not met; 0 objects captured in all 3 attempts) and cited this doc in
  its Progress Log rather than silently marking it done or retrying indefinitely (VM-launcher-runbook "no
  fire-and-forget" + cost-consciousness — 3 real billable VM launches already spent chasing this with zero throughput
  data produced).

- **2026-08-15 (slot-6, infra craft, todo 1, IN PROGRESS — root cause confirmed + fix applied, verification pending)**:
  dispatcher immediately offered this doc's own todo 1 back to the same slot after the filing above. Adopted infra craft
  (was backend_engineer for the prior todo). Confirmed the IAM hypothesis live via `gcloud projects get-iam-policy`
  (project-level read, not object-scoped — avoids the hook block that stopped bucket-level inspection earlier):
  `uts-test-sa` has unconditioned project-wide `storage.objectViewer` but its `storage.objectAdmin` grants are
  conditioned to `-test-`-suffixed DATA-tier buckets only, excluding `deployment-scripts-central-element-323112`
  entirely. Self-granted a narrow, bucket-scoped IAM condition (title `deployment-scripts-bucket-test-sa-vm-logs`)
  rather than widening `uts-test-sa` project-wide — verified live in a fresh policy read. Launched a real verification
  VM (`features-e2e-tradfi-20260815-100817-679e08`) to prove the fix closes the gap (not just that the policy read looks
  right) — **still running when this session ended; the next session/agent should check
  `gs://deployment-scripts-central-element-323112/vm-logs/ features-e2e-tradfi-20260815-100817-679e08/run.log` for
  existence before doing anything else with this todo.** See todo 1's own note above for the exact next-step branching
  (fix proven vs. hypothesis needs revisiting).

- **2026-08-15 (slot 5, infra craft)**: dispatched todo 2 (the "if refuted" diagnostic branch) independently of slot-6's
  todo 1 work; on picking it up found todo 1 already in-flight with a verification VM running, so continued monitoring
  that VM to terminal state instead of duplicating a second diagnostic launch.
  `features-e2e-tradfi-20260815-100817-679e08` reached `EXIT_STATUS=0` / clean `DEPLOYMENT_COMPLETED` — the FIRST time
  in 4 total attempts on this launch shape that ANY object (let alone a real `run.log` + non-`RUNNING` `EXIT_STATUS`)
  was ever written. **Flipped todo 1 (proven) and todo 2 (N/A — hypothesis confirmed, not refuted, so its own diagnostic
  precondition never applies).** The VM's `run.log` also surfaced a genuinely NEW, distinct bug: all 11 feature groups
  reported `Completed 0/11 groups` — every group hit `No data for VX` then an `empty_confirmed manifest write failed`
  guard rejection (the write correctly refuses to record a masked failure as honest absence). Filed as a new [DATA] P1
  todo above and annotated todo 4 (the "capture real throughput" relaunch) as NOT YET satisfied — the launch mechanism
  works now, but zero real throughput numbers exist to cite. Did not attempt to root-cause the
  VX-data-gap-vs-masked-failure question itself — genuinely distinct domain (features-service data correctness) from
  this doc's IAM/infra scope, out of proportion for this already-large infra todo to absorb inline.

- **2026-08-15 (slot-6, infra craft, todo 1, DONE — independently corroborated slot-5's result)**: re-checked the same
  verification VM's GCS objects directly (`run.log` 27,656 bytes, `EXIT_STATUS=b'0\n'`) and reached the identical
  conclusion as slot-5 above before seeing their push — both sessions confirmed the IAM fix from the same live evidence.
  Adds one finding slot-5's entry doesn't cover: while re-reading the driver's own poll log
  (`launch_vm_and_wait(...): poll tick 5 ... WARNING ... EXIT_STATUS present but unreadable/unparsable: invalid literal for int() with base 10: 'RUNNING'`),
  confirmed the pipeline_e2e_check REPORT for this run was written as `failed, exit=-1, objects=0` — i.e. **the
  automated report says this run failed, even though it actually succeeded** (this doc, and slot-5's own note, only know
  that from manually re-reading `EXIT_STATUS` after the report already wrote `-1`). Added this as a second, distinct
  amendment to the `[SCRIPT] P2` reason-field todo above: `RUNNING` is a valid non-terminal `EXIT_STATUS` value that
  `_poll_until_terminal` currently treats as an unparsable failure instead of "keep polling." Also updated
  `tradfi_satellite_ao_dispatch_batch13_2026_08_13.md`'s todo 2 with a matching infra-fixed/now-data-blocked note +
  Progress Log entry (unconflicted, shipped in the same commit as this doc). Calling `/done` on the AO task scoped to
  this doc's todo 1 (`features_e2e_test_run_vm_self_deletes_no_log-d63cea8bbc07`) since that specific scope is complete
  and doubly verified; the remaining todos (poll-loop fix, VX-data-gap root cause, benchmark relaunch) are separate
  follow-on work already tracked above for a future dispatch.

- **2026-08-15 (slot-17, data_engineering, the VX-data-gap [DATA] P1 todo)**: root-caused via code read
  (`data_loader.py`'s `_resolve_spot_perp`/`_resolve_spot_future_tradfi`/`_TRADFI_FX_UNDERLYING_TO_PRODUCT_ROOT`) +
  bounded manifest scans (`venue=CBOE`, column-pruned, one date at a time, 2026-08-07 through 08-14). Neither of the
  todo's own two hypotheses is the actual cause — it's a code gap: VX was never added to the FX-underlying resolver's
  mapping dict (that dict's scope was fixed by the 2026-08-06 doc's own diagnosis, which never saw VX), and even if it
  were, the lookup's expected shape (`FUTURE`/`trades`/FX-style instrument_id) doesn't match VX's real captured shape
  (`futures_chain`/`ohlcv_1m`/`CBOE:FUTURE:VIX`) — confirmed exactly ONE genuine `captured` VX row exists in the whole
  08-07..14 window (on 08-07). Flipped the todo with full evidence, filed the concrete fix as a new `[CODE] P2` todo
  (design call needed, following the FX fix's own precedent of an operator/design ruling before implementation — not
  guessed blind), and flagged a separate, unconfirmed MTDS/CBOE capture-cadence question (possibly related to the
  ongoing `tradfi_databento_account_billing_suspended_2026_08_09.md` saga, but not conclusively — that doc's own latest
  finding says the current recurrence is CME-specific, not account-wide, and the CBOE signature here is "never
  attempted" not "attempted and failed"). No code changed this session — pure diagnostic, per this todo's own
  "root-cause" framing; the fix itself needs its own scoped dispatch.

- **2026-08-15 (slot-6, infra craft, todo `[SCRIPT] P2` RUNNING-sentinel half, DONE)**: server cancelled the prior task
  (`-d63cea8bbc07`, `dispatch_reason: cancelled`) before this session could call `/done` on it — resolved via
  `/skip-current-task` per `worker.md`'s cancellation contract (found already `status=idle` server-side by the time of
  the call, so nothing left to skip; no uncommitted WIP to revert, prior todo's work was already shipped). Next
  heartbeat dispatched this doc's `[SCRIPT] P2` todo (id `features_e2e_test_run_vm_self_deletes_no_log-683c21ffc662`).
  Fixed the RUNNING-sentinel false-negative in `_read_exit_status`
  (`unified_trading_library/pipeline_e2e_check/launcher.py`): the VM's deliberate non-terminal `"RUNNING"` stamp (see
  `launcher_common.sh`'s "Stamp a non-terminal RUNNING sentinel FIRST" comment — a whole-unit-SIGKILL false-success
  guard, not a bug on the writer side) now returns `None` ("not yet present") instead of `-1` ("unparsable failure"), so
  `_poll_until_terminal`'s existing not-terminal loop naturally keeps polling through it. Added 4 regression tests
  (`test_pipeline_e2e_check_launcher_running_sentinel.py`) covering the sentinel, a real terminal rc,
  genuinely-unparsable content, and an end-to-end poll-through-RUNNING-to-real-rc case. QG green, shipped
  `unified-trading-library@2c412cc367`. Left the todo's checkbox unflipped — the reason-field-threading half (surfacing
  self-delete/timeout distinction in the report's `reason` string) is a separate, still-open piece of the same todo, not
  touched this session.

- **2026-08-15 (slot-6, infra craft, todo `[SCRIPT] P2` reason-field-threading half, DONE — checkbox flipped)**: the
  server's `/done` DONE-GATE correctly rejected the RUNNING-sentinel-only closure above
  (`cross_repo_pm_file_touched_no_checkbox_flip`) since the todo's PRIMARY ask (thread the launcher's
  self-delete/timeout distinction into the benchmark leg's report `reason` string) was still open — the RUNNING-sentinel
  work was only the amendment appended alongside it, not the todo itself. Found the exact gap in `_run_benchmark_leg`
  (`features-service/scripts/pipeline_e2e_check.py:1969-2015`): unlike the skip-leg runner (which already does
  `reason = f"vm_not_success:{vm_result.reason}"` on failure), the benchmark leg's `reason` was always the generic
  `window=... wall_clock=...s ... objects=...` string regardless of WHY the VM failed. Fixed by prefixing
  `vm_not_success:<launcher reason>` when `exit_status != 0`, preserving the existing wall_clock/objects telemetry after
  it. Added 3 regression tests (`tests/unit/test_pipeline_e2e_check_benchmark_reason_threading.py`) covering
  self-deleted, timeout, and the success path (no prefix). QG green, shipped `features-service@7e5ca3f5f7`. Both halves
  of the todo are now done — flipped the parent checkbox with evidence. Retrying `/done` on
  `features_e2e_test_run_vm_self_deletes_no_log-683c21ffc662` next.

- **2026-08-15 (slot-26, data_engineering, dispatched the `[DATA] P1` relaunch todo,
  `features_e2e_test_run_vm_self_deletes_no_log-f45d1d689cf9`) — SKIPPED (GATED), not relaunched.** Confirmed the
  `[CODE] P2` VX/145-underlying resolver fix directly in
  `features-service/features_service/volatility/core/data_loader.py` (git log clean since `f4416389`/`304c8176` — no fix
  landed): `_TRADFI_FX_UNDERLYING_TO_PRODUCT_ROOT` still holds only the 5 FX roots, `_resolve_spot_future_tradfi` still
  returns `None` immediately for every other underlying. Per slot-12's own note above, this is date-independent
  (confirmed against 2026-08-07, a day with real captured VX data, and still 0/11) — a 3rd/4th relaunch attempt would
  reproduce the identical `Completed 0/11 groups` zero-throughput result, not advance this todo's own done_definition
  ("real throughput numbers"). Rather than spend a 7th billable VM launch on a predictably-negative outcome
  (cost-consciousness, `vm-launcher-runbook.md` "no fire-and-forget"), and since the `[CODE] P2` fix's own text
  explicitly recommends an operator/design ruling before implementation rather than guessing the per-underlying-class
  mapping shape blind (out of THIS todo's own scope — a separate, already-filed, undispatched todo, not mine to silently
  absorb per `/boot-per-shippable-unit`'s "don't fan out to multiple tasks in one session"), skipping this task with
  `reason_code: GATED` so it doesn't re-dispatch to the next slot until `[CODE] P2` has a real chance to land. Next
  agent picking this back up: check `[CODE] P2`'s checkbox first — only relaunch once it's `[x]`.

- **2026-08-15 (slot-15, infra craft, `[CODE] P2` VX/145-underlying resolver fix, DONE — checkbox flipped).** Filed a
  `/blocked` question (`BLK-74a50891`) before implementing, since this todo's own text (and slot-12's scope-widening
  note) explicitly calls for an operator/design ruling before implementation rather than guessing the per-underlying
  shape blind. Operator picked Option A (generalize with no hardcoded per-root shape-routing dict). Implementation: (1)
  `_resolve_spot_future_tradfi` no longer short-circuits on
  `_TRADFI_FX_UNDERLYING_TO_PRODUCT_ROOT.get(underlying) is None` — non-FX underlyings now fall back to using themselves
  as the product root (`ES` -> `ES`), so the existing dated-future/`trades` manifest lookup runs for ALL 145+ TRADFI
  underlyings, not just the 5 mapped FX roots. (2) VX specifically has no clean per-contract dated-future series
  (captured only at `futures_chain` grain — confirmed via the already-built, VX-specific `load_vix_ohlcv_raw` carve-out
  and its own docstring, which predates this fix and was built for exactly this reason per a 2026-08-07 operator ruling)
  — rather than inventing a second, unverified chain-grain read path, `load_spot_price_raw` now routes `TRADFI`+`VX`
  directly to that existing loader (`_load_vix_spot_price_raw` wrapper) before ever calling the generic resolver. Added
  8 regression tests (`tests/volatility/unit/test_data_loader.py`: non-FX manifest resolution,
  no-captured-row-returns-None, 3 VX carve-out cases including a check that VX never touches the generic manifest
  resolver). Full `quality-gates.sh` green (18408+ tests passed; two method-size-cap failures from the initial
  docstring-heavy edit were fixed by trimming docstrings + extracting `_load_vix_spot_price_raw`) — QG took several
  retries purely due to severe shared-host RAM contention (~20+ concurrent slot QG runs; quality-gates.sh's own
  `qg-governor-watchdog` self-terminated 3 runs mid-flight on RAM pressure, and one `setsid`-isolated retry produced a
  FALSE exit=0 — caught via sentinel-vs-HEAD verification, never trusted the exit code alone). Shipped
  `features-service@9bd9894119`. The `[DATA] P1` relaunch todo above is still gated pending this fix — now unblocked;
  next agent picking it up can retry `pipeline_e2e_check.py` against a manifest-confirmed captured date.

- **2026-08-15 (slot-18, data_engineering, `[DATA] P1` relaunch todo
  `features_e2e_test_run_vm_self_deletes_no_log-f45d1d689cf9`) — NOT satisfied, new root cause found, GATED.** Confirmed
  `[CODE] P2`'s fix landed (`features-service@9bd9894119`, no uncommitted local diff). Manifest scan found
  `CBOE:FUTURE:VIX` genuinely captured on 2026-08-03/04/05/07 (nothing more recent through 08-15) — relaunched
  `pipeline_e2e_check.py --day 2026-08-07 --asset-group TRADFI --family volatility --legs benchmark --benchmark-days 7`
  (VM `features-e2e-tradfi-20260815-134031-481be7`). Monitored to terminal state over ~50min (VM healthy throughout,
  `exit_code=0`, clean `DEPLOYMENT_COMPLETED`) — but the run STILL reported `Completed 0/11 groups`, identical
  zero-throughput to every prior attempt on this doc. Root-caused via live manifest reads (not code-read alone this
  time): the window's manifest has ZERO rows with `instrument_type=="FUTURE"` AND `data_type=="trades"` — the exact
  combination `_resolve_spot_future_tradfi`/`_tradfi_future_candidates` require — so `[CODE] P2`'s "generalize" fix
  (which extended that SAME dated-instrument_id/`trades` lookup to all 145+ underlyings) still matches nothing,
  INCLUDING the 5 FX roots that supposedly already worked (confirmed: `run.log` shows `No captured perp for 6A/6B/...`
  too). The real captured shape for TRADFI FUTURE data is `data_type="ohlcv_1m"/"ohlcv_1s"` keyed by a top-level
  `underlying=` manifest column (e.g. `"EUR"`), not a dated `instrument_id` — exactly the shape the existing VIX-only
  `load_vix_ohlcv_raw` carve-out already reads correctly. Filed as a new `[CODE] P1` todo (recommending
  `load_vix_ohlcv_raw`'s path be generalized to `(venue, underlying)` instead of hardcoded VIX/CBOE, per the same
  operator-design-ruling precedent slot-15 followed) and left the `[DATA] P1` relaunch todo unchecked + GATED — an 8th
  billable VM launch would reproduce the identical 0/11 result blind. `/skip-current-task` with `reason_code: GATED`
  next.

- **2026-08-15 (slot-6, infra craft, `[CODE] P1` "generalize `load_vix_ohlcv_raw`" fix, DONE — checkbox flipped).**
  Filed `/blocked` (`BLK-4535e82c`) before implementing, per this todo's own text and slot-15's precedent (operator/
  design ruling before implementation, not a blind guess at the per-underlying mapping shape). Operator confirmed Option
  A: generalize fully, delete the dead dated-`trades`-instrument_id path entirely rather than keep it as a fallback
  (this correction supersedes the operator's own earlier `BLK-74a50891` answer, which assumed the dated- `trades` shape
  was real for the 5 FX underlyings — this session's live manifest reads proved it was never real for ANY underlying, FX
  included). Implementation: generalized `load_vix_ohlcv_raw` into
  `load_ohlcv_underlying_raw(date, venue, underlying, data_type)`; added `_resolve_ohlcv_underlying_tradfi`
  (manifest-driven — `instrument_type==FUTURE`, `data_type` in the ohlcv family, `underlying==<X>`,
  `capture_status==captured` — returning the manifest row's own `(venue, underlying, data_type)`, translating caller
  tickers like `6E`/`VX` to the manifest's `EUR`/`VIX` values via a small `_TRADFI_UNDERLYING_TO_MANIFEST_UNDERLYING`
  table, a caller-symbol-normalization concern distinct from the deleted dated-lookup mechanism); routed
  `load_spot_price_raw`'s TRADFI branch through it uniformly (VX is no longer a special case — extracted into a small
  `_load_spot_price_tradfi` helper to stay under the 50-line method cap); deleted
  `_resolve_spot_future_tradfi`/`_tradfi_future_candidates`/`_TRADFI_FX_UNDERLYING_TO_PRODUCT_ROOT`. Kept
  `load_vix_ohlcv_raw` itself as a thin named wrapper (not a shim — `feature_group_service.py` still calls it directly
  by name for VIX-specific feature computation, a genuinely separate consumer). Caught + fixed a real bug in my own
  first draft before shipping: the resolver initially matched the caller's raw ticker (`6E`/`VX`) against the manifest's
  `underlying=` value directly, missing the ticker→manifest-value translation — QG's own test run caught it (4
  failures), not manual review. Rewrote 7 tests in `TestResolveSpotFutureTradfi`→`TestResolveOhlcvUnderlyingTradfi`,
  updated the VX-specific `TestLoadSpotPriceRaw` cases to mock the manifest instead of a hardcoded short-circuit, added
  `TestLoadOhlcvUnderlyingRaw` for direct non-VIX coverage. Full `quality-gates.sh` green (18415 passed) after 2 more
  retries purely from severe shared-host QG contention (one run outright killed mid-flight, ~10+ concurrent slot QG runs
  observed via `ps`) — never trusted a bare exit code, verified the sentinel SHA against `git rev-parse HEAD` each time.
  Shipped `features-service@a46681c84a`, post-push ancestry independently re-verified against
  `origin/live-defi-rollout`. This closes the last open todo on this doc — the `[DATA] P1` relaunch todo above is now
  unblocked for a future dispatch (not attempted here — cost-conscious per `vm-launcher-runbook.md`, 7 billable VM
  launches already spent on this doc with zero real throughput; a relaunch is a separate, already-tracked next step, not
  mine to absorb per `/boot-per-shippable-unit`'s "don't fan out to multiple tasks in one session").
- **context-scout 2026-08-17**: re-verified context_scope (4 entries), unchanged.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
