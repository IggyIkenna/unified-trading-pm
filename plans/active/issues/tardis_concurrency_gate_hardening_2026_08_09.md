---
doc_type: issue
title:
  Tardis concurrent-VM cap hardening — bypass launcher fixed, missing per-VM reserve closed on 5 launchers, post-launch
  self-check added
summary: >-
  Operator-directed audit (triggered by a live DP_RUN_MOSTLY_EMPTY alert traced to a cefi backfill hitting Tardis while
  another VM held the single allowed slot) of every launcher that's supposed to be wired into
  `tardis-concurrency-guard.sh` (operator HARD RULE: at most 1 Tardis-consuming VM, both clouds). Found and fixed: (1) a
  TOTAL BYPASS — `launch-cefi-massive-rollout.sh` (up to 364-VM fan-out, batches of 100) never sourced the guard at all,
  despite its own header explicitly citing the shared Tardis IP-allowlist as its region-choice rationale; (2)
  `launch-cefi-week-test.sh` fanned out 7 concurrent Tardis VMs relying on each spawned sub-launcher's OWN pre-flight
  check rather than checking itself, silently wasting N-1 doomed background jobs whenever the guard correctly refused
  them; (3) 5 of 6 already-guarded launchers called only the pre-flight `tardis_concurrency_guard` (an estimate) and
  never the mandatory `tardis_guard_reserve_slot` immediately before the actual `gcloud compute instances create` — the
  guard's own header documents this exact gap as a proven live-breach class (the 2026-07-20 DERIBIT+BINANCE-FUTURES
  incident); only `launch-cefi-sharded-backfill.sh` did both correctly. Also found and fixed: a hardcoded (rather than
  filter-derived) planned-VM-count in `launch-targeted-options-chain-backfill.sh` that falsely refused
  legitimately-scoped single-shard launches (training operators toward `FORCE=1`); an AWS launcher
  (`launch-cefi-sharded-backfill-aws.sh`) mistagging the CAP-EXEMPT HYPERLIQUID venue as a Tardis consumer (over-counts,
  safe direction, but pollutes the live-fleet count for every other launcher's guard); and a latent (currently harmless
  only by string-convention coincidence) variable-namespace collision between `launch-cefi-forward-poll.sh`'s own
  `--force` flag and the guard's `FORCE=1` override — both bare `FORCE`, sharing the same process via `source`. Added a
  POST-launch self-check (`vm_zombie_watchdog.py`'s existing 5-min sweep) since none existed: an independent live-fleet
  recount every cycle that kills the newest excess Tardis-consuming VM(s) if the count ever exceeds cap, a backstop for
  the one residual race the guard's own header names (near-simultaneous launches from different processes/launchers).
  Live-state check (2026-08-09): exactly 1 Tardis-consuming VM running
  (`cefi-queue-heavy-binancefutu-x17-20260809-083733`, SINGLE_VM_QUEUE mode) — no current cap violation.
  `mtds-live-cefi-consolidated-20260809-121034` and `mtds-dex-swaps-backfill` (the two VMs the operator named) are
  confirmed non-Tardis (live-websocket producer with no `VM_TARDIS_CONSUMER` stamp, and DeFi respectively). No active
  plan/issue found scheduling a second concurrent Tardis launch; one coordination note added to
  `cefi_satellite_ao_dispatch_batch9_2026_08_07.md` todo 2 (unrelated open TOCTOU-fix todo touching the same file I
  edited, `launch-cefi-forward-poll.sh`) so the next worker rebases against current `HEAD` instead of a stale diff.
status: open
nature: issue
asset_group: [cefi, cross-cutting]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [tardis, vm-launcher, concurrency, rate-limit, cefi, hardening, zombie-watchdog]
related:
  [
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /plans/active/cefi_track2_coverage_backfill_checkpoints_2026_07_25.md,
    /plans/active/cefi_satellite_ao_dispatch_batch9_2026_08_07.md,
    /plans/active/issues/tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md,
    /plans/active/issues/cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md,
  ]
created: "2026-08-09"
author: agent (interactive, tab-2)
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: data_engineering
drift_direction: fix
depends_on: []
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  [
    deployment-service/scripts/vm/tardis-concurrency-guard.sh,
    deployment-service/scripts/vm/launch-cefi-massive-rollout.sh,
    deployment-service/scripts/vm/launch-cefi-week-test.sh,
    deployment-service/scripts/vm/launch-targeted-options-chain-backfill.sh,
    deployment-service/scripts/vm/launch-cefi-sharded-backfill-aws.sh,
    deployment-service/scripts/vm/launch-tier3-cefi-backfill.sh,
    deployment-service/scripts/vm/launch-cefi-forward-poll.sh,
    deployment-service/scripts/vm/launch-mtds-backfill-vm.sh,
    deployment-service/scripts/vm/vm_zombie_watchdog.py,
    "gcloud compute instances list --filter='name~mtds OR name~cefi OR name~tardis' (central-element-323112,
    asia-northeast1-c), run 2026-08-09",
  ]
---

# Tardis concurrent-VM cap hardening — 2026-08-09

## Trigger

A `DP_RUN_MOSTLY_EMPTY` CRITICAL alert (`asset_group=cefi, data_type=derivative_ticker`, 18,478 `attempted_failed`
cells) was traced to a cefi backfill hitting Tardis while another VM already held the single allowed concurrent slot,
403ing and recording every cell as `attempted_failed`. Operator asked for the concurrency cap to become a canonical
pre-launch HARD gate (not just a courtesy check most launchers happen to call), plus a self-check/zombie-kill fallback,
plus a check for any currently-active work that could reproduce the same failure mode.

## What `tardis-concurrency-guard.sh` already does right (baseline, unchanged)

- **Fail-closed**: any enumeration failure (gcloud/python3 missing, API error, unparseable output) REFUSES rather than
  reading as "0 running".
- **Self-declaring metadata model**: `VM_TARDIS_CONSUMER=1` (GCP metadata / AWS tag), unioned with a legacy name-pattern
  fallback — counts RUNNING+PROVISIONING+STAGING (closes the ~40s create-to-RUNNING visibility race).
- **Two-call contract, by design**: `tardis_concurrency_guard <planned_count>` (pre-flight estimate) THEN
  `tardis_guard_reserve_slot` immediately before every actual `gcloud compute instances create` (binds the cap to ACTUAL
  creation, not a possibly-wrong estimate — this is exactly the mechanism the 2026-07-20 DERIBIT+BINANCE-FUTURES
  incident forced into existence). The header states plainly: "BOTH calls are mandatory."
- Cross-cloud (GCP ∪ AWS) union count; `FORCE=1` operator override on both calls.

## Gaps found + fixed (all in `deployment-service`)

| #   | Launcher                                                                                                                                                                         | Gap                                                                                                                                                                                                                                                                                                           | Severity                                                                                                                       | Fix                                                                                                                                                                                                                                                               |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `launch-cefi-massive-rollout.sh`                                                                                                                                                 | Never sourced the guard at all — up to 364-VM fan-out (100/batch) of real CeFi Tardis backfills, despite its own header naming the shared Tardis IP-allowlist as the region rationale                                                                                                                         | **Critical — total bypass**                                                                                                    | Sourced the guard; added `VM_TARDIS_CONSUMER=1` metadata stamp; added a hard pre-flight `tardis_concurrency_guard $TOTAL` before the batch loop (refuses any TOTAL>1 unless `FORCE=1`); added `tardis_guard_reserve_slot` inside `_launch_one` before each create |
| 2   | `launch-cefi-week-test.sh`                                                                                                                                                       | Fanned out 7 concurrent Tardis VMs relying only on each spawned `launch-cefi-forward-poll.sh` sub-process's own pre-flight check; never checked itself, so it silently spawned N-1 doomed background jobs (logged only to `/tmp`) whenever the guard correctly refused them                                   | Medium — not a live bypass (sub-launcher guard already blocked it), but misleading UX that could mask a real problem           | Added its own hard pre-flight `tardis_concurrency_guard $DAY_COUNT` so it fails fast with one clear message instead                                                                                                                                               |
| 3   | `launch-targeted-options-chain-backfill.sh`, `launch-cefi-sharded-backfill-aws.sh`, `launch-tier3-cefi-backfill.sh`, `launch-cefi-forward-poll.sh`, `launch-mtds-backfill-vm.sh` | Pre-flight `tardis_concurrency_guard` called, but `tardis_guard_reserve_slot` never called before the actual create — advisory-not-fully-hard-blocking against the exact race the guard's own header documents                                                                                                | High for the 3 multi-VM batch launchers, lower (defense-in-depth) for the 2 single-VM launchers                                | Added `tardis_guard_reserve_slot` immediately before each `gcloud compute instances create` (CEFI/Tardis-venue-scoped where the launcher also serves non-Tardis shards)                                                                                           |
| 4   | `launch-targeted-options-chain-backfill.sh`                                                                                                                                      | `PLANNED_TARDIS_VMS` hardcoded to 21 regardless of `--venue`/`--year` scoping — a genuinely single-shard `--venue DERIBIT --year 2024` launch was falsely refused, training operators toward `FORCE=1` even when no real violation was ever going to occur                                                    | Medium — false-refusal, not a bypass, but a `FORCE=1`-habit-forming footgun                                                    | Computed from the actual `SELECTED_VENUE`/`SELECTED_YEAR` filters, mirroring `_launch_shard`'s own filter exactly                                                                                                                                                 |
| 5   | `launch-cefi-sharded-backfill-aws.sh`                                                                                                                                            | Tagged EVERY venue (including cap-exempt HYPERLIQUID) `VM_TARDIS_CONSUMER=1` — over-counts the live fleet, which would make every OTHER Tardis launcher's guard refuse for no reason while a HYPERLIQUID shard runs                                                                                           | Low — safe direction (over-refusal, not under-counting), but pollutes the shared signal                                        | Excluded HYPERLIQUID from the tag + from the new `tardis_guard_reserve_slot` call                                                                                                                                                                                 |
| 6   | `launch-cefi-forward-poll.sh`                                                                                                                                                    | Latent variable-namespace collision: the launcher's own `--force` flag used a bare `FORCE` shell variable, `source`d into the same process as the guard, which reads `${FORCE:-0}` as ITS OWN override. Currently safe only by STRING-VALUE COINCIDENCE (launcher uses "true"/"false", guard checks `== "1"`) | Latent — not a live bug, but one convention change away from silently disabling the Tardis cap on every `--force` forward-poll | Renamed the launcher's local variable to `LAUNCHER_FORCE`                                                                                                                                                                                                         |

Two launchers with prose mentioning "tardis-concurrency-guard" were verified as legitimate, correctly-scoped exemptions
(NOT gaps): `launch-cefi-funding-timestamp-fix-vm.sh` and `launch-cefi-extended-starknet-funding-timestamp-vm.sh` are
pure GCS-migration one-offs (verified via import grep — no Tardis client, only UTL storage calls), explicitly documented
as out-of-scope for the cap. `launch-mtds-live.sh`'s `--live-source tardis-machine` is the unauthenticated local sidecar
per the guard's own design ("AUTHENTICATED batch consumers only") — confirmed no `VM_TARDIS_CONSUMER` stamp on the live
`mtds-live-cefi-consolidated-20260809-121034` VM. `launch-canonical-migration-vm.sh`'s Tardis filename-migration script
was verified via import grep to make zero live Tardis API calls (GCS rewrite only).

## Post-launch self-check (item 3 of the ask) — did not exist, added a minimal version

`vm_zombie_watchdog.py` (the existing 5-min-poll external liveness watchdog, already covering every RUNNING VM
fleet-wide) had NO Tardis-cap-specific logic — it only checks heartbeat/shard staleness and EXIT_STATUS. Added a third
pass (`_enforce_tardis_cap`, wired into `main()`, on by default, `--tardis-max-concurrent` default 1 matching the guard,
`--no-tardis-cap-check` opt-out): every sweep independently re-lists the live Tardis-consuming fleet (mirrors the
guard's own counting logic — name-pattern ∪ `VM_TARDIS_CONSUMER=1` metadata, RUNNING+PROVISIONING+STAGING), and if more
than the cap are found, kills the NEWEST excess VM(s) (oldest keeps the slot — it legitimately passed pre-flight first),
persisting a `tardis_cap_violation` alert per kill via the existing alert-ledger writer. This is deliberately
independent of the heartbeat-zombie logic: a cap-violating VM can be perfectly healthy and still needs to die, because
its mere existence is what corrupts the manifest via 403 storms.

**Not yet live**: the currently-running `vm-zombie-watchdog-20260807-075242` VM will not pick up this code change until
relaunched (per the launcher's own documented update procedure — it never re-fetches its script mid-loop). Tracked as
todo 1 below.

## Live-state check (2026-08-09, `central-element-323112`)

`gcloud compute instances list --filter='name~mtds OR name~cefi OR name~tardis'` (asia-northeast1-c) + per-VM metadata
describe, cross-referenced against `VM_TARDIS_CONSUMER`:

| VM                                                 | `VM_TARDIS_CONSUMER` | Verdict                                                                                                                                                             |
| -------------------------------------------------- | -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `cefi-queue-heavy-binancefutu-x17-20260809-083733` | `1`                  | **The one legitimate Tardis-consuming VM** (SINGLE_VM_QUEUE mode, driven by `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`, `assigned_vm: planning`, P0) |
| `mtds-live-cefi-consolidated-20260809-121034`      | absent               | Not Tardis — live-websocket producer, no authenticated-batch stamp                                                                                                  |
| `mtds-dex-swaps-backfill`                          | absent               | Not Tardis — DeFi, `VM_ASSET_GROUP=DEFI`                                                                                                                            |
| `mdps-backfill-cefi-*` (×3)                        | absent               | Not Tardis — MDPS candle-derivation reads already-captured GCS ticks, never calls Tardis live (verified via import grep)                                            |
| `cefi-fwd-daily-cron-*`                            | absent               | Not Tardis — the persistent cron HOST, not a worker (correctly excluded by the launcher's own digit-anchor name filter)                                             |
| `mtds-backfill-odds-*`, `mtds-live-sports-odds-*`  | absent               | Sports odds-api, different guard (`odds-api-concurrency-guard.sh`)                                                                                                  |

**Verdict: no current live violation.** Fleet = 1 Tardis-consuming VM against a cap of 1.

## Plan/issue conflict check

Grepped `plans/active/`+`issues/` for anything scheduling a second concurrent Tardis launch. No active todo found that
would launch a competing Tardis VM without going through the (now-hardened) guard. One coordination note added:
`cefi_satellite_ao_dispatch_batch9_2026_08_07.md` todo 2 (an unrelated, still-open `launch-cefi-forward-poll.sh`
singleton-lock TOCTOU fix) touches the same file this session edited (the `LAUNCHER_FORCE` rename +
`tardis_guard_reserve_slot` addition) — annotated so the next worker rebases against current `HEAD` instead of a stale
diff, per the "fits another plan → annotate it, don't fix" triage rule.

## Verification

- `bash -n` clean on all 7 edited `.sh` files; `shellcheck --severity=error` clean on all 7 (matches
  `TestShellcheckClean`'s existing gate in `tests/unit/test_vm_zombie_watchdog.py`).
- Code-review-level simulated cap-violation check (live VM creation not exercised — would cost real money/risk a real
  403 storm against the shared licensed key): with the fix, `launch-cefi-massive-rollout.sh probe <date>` (TOTAL=364)
  now hits `tardis_concurrency_guard 364 ...` before any VM is created and REFUSES (`total <= cap` is false) unless
  `FORCE=1` — traced by hand through the guard's own `tardis_concurrency_guard()` function body. Previously this same
  invocation would have proceeded straight to the batch loop with zero gate.
- `bash scripts/quality-gates.sh --no-fix` run for `deployment-service` (includes `TestShellcheckClean` +
  `test_vm_zombie_watchdog.py`'s existing suite over the new `_enforce_tardis_cap`/`_is_tardis_consumer` code paths via
  import) — see Progress Log for the run's outcome/evidence.

## Todos

- [ ] [OPS] P1. **Relaunch `vm-zombie-watchdog-20260807-075242`** (kill old + `bash launch-vm-zombie-watchdog.sh`) once
      this fix ships, so the Tardis-cap self-check pass actually goes live — the running instance will not pick up the
      code change on its own. Verify via a dry-run log line ("Tardis-cap self-check: N Tardis-consuming VM(s) found,
      cap=1, 0 excess") within one 5-min cycle of relaunch. Repo: deployment-service.
- [ ] [SCRIPT] P3. Add a focused unit test for `_is_tardis_consumer`/`_enforce_tardis_cap` in
      `tests/unit/test_vm_zombie_watchdog.py` (fake compute client fixture already exists in that file —
      `_FakeComputeClient`/`_FakeComputeInstance`) covering: name-pattern match, metadata-stamp match, neither (not
      counted), and a 3-VM-over-cap-1 scenario asserting the 2 newest are killed and the oldest is kept. Repo:
      deployment-service.

## Progress Log

- **2026-08-09, interactive session (tab-2)**: Full audit + fixes as described above. 7 launcher `.sh` files +
  `vm_zombie_watchdog.py` edited in `deployment-service`; 1 coordination annotation added to
  `cefi_satellite_ao_dispatch_batch9_2026_08_07.md` in `unified-trading-pm`. `bash scripts/quality-gates.sh --no-fix`
  PASSED clean (1482s; a `⚠️ below the DTZ/TID251 baseline` note is a ratchet IMPROVEMENT, not a failure). Shipped via
  `quickmerge.sh --agent --files`: `Evidence: deployment-service@58af2ab1303e4d91093f4f5371fc2d9c4667622f`, landed on
  `live-defi-rollout`, post-push ancestry verified. Quickmerge needed 2 retries purely on shared-host contention (a
  peer's LDR→main backmerge moved `HEAD` mid-ship, invalidating the QG sentinel; the first re-gate attempt was SIGKILLed
  under genuine host memory pressure — confirmed via `vm_stat`/process audit, not a code issue — the second re-gate
  passed clean in 439s and shipped). No content changes were needed across the retries.
- **2026-08-09, same session, final live-state re-check**: `gcloud compute instances list` re-run post-ship — fleet
  unchanged from the pre-ship check: still exactly 1 Tardis-consuming VM (`cefi-queue-heavy-binancefutu-x17-...`,
  `VM_TARDIS_CONSUMER=1`), cap=1, no violation.
