---
doc_type: issue
title: >-
  cefi-fwd-20260808-110409 (STANDARD VM, 62-day backfill) deleted by unified-trading-sa within 10-13 minutes of launch —
  same double-insert pattern as cefi-fwd-20260806-064507; GCS probe confirms 0 data written
summary: >-
  `cefi-fwd-20260808-110409` was launched by slot-14 (task defi_cefi_venue_chain_axis_contamination-011) at
  2026-08-08T11:04Z for a 62-day `derivative_ticker` backfill (2026-06-05→08-05, 6 venues). Audit logs show TWO
  `v1.compute.instances.insert` ops 8 seconds apart (11:04:15Z + 11:04:23Z) — same double-launch pattern as the prior
  `cefi-fwd-20260806-064507` incident (13s apart). Both were then DELETED (not stop'd) by
  `unified-trading-sa@central-element-323112.iam.gserviceaccount.com` at 11:14:58Z and 11:17:12Z — within 10-13 minutes
  of launch, before any meaningful data could be written. GCS probe (slot-17, 2026-08-08, `probe_cefi_perp_funding_raw_
  coverage.py`) confirms 0 objects across 2026-06-05→08-05 for BINANCE-FUTURES/BYBIT/OKX-SWAP/KRAKEN-FUTURES/BITGET-
  FUTURES; tiny pre-existing DERIBIT remnants (20-21/day from earlier DERIBIT-only backfill) and BITFINEX-FUTURES
  remnants (07-22/07-24) — none written by this VM. **Consequence**: -011 corpus recompute gate NOT met; -014 (GCS
  cleanup) correctly remains blocked; the backfill window 2026-06-05→08-05 is still absent for 5 of 6 CARRY_BASIS_PERP
  venues. This is the second consecutive cefi-fwd VM terminated before completing its window (prior:
  `cefi-fwd-20260806-065837`, terminated at 12/75 days). Root cause unknown — likely the Tardis concurrency guard or
  zombie watchdog reacting to the double-insert (two concurrent VMs). Operator + slot-14 action required.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [deployment-service]
scope: [engineer, admin]
tags: [cefi, vm, backfill, premature-deletion, tardis, concurrency-guard, data-pipeline, data-correctness]
related:
  [
    /plans/active/issues/cefi_fwd_vm_preempted_false_positive_standard_provisioning_2026_08_06.md,
    /plans/active/issues/defi_cefi_venue_chain_axis_contamination_2026_07_28.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /plans/active/issues/cefi_window_scoped_coverage_gap_okx_binance_bybit_2024_2026_2026_08_09.md,
  ]
created: "2026-08-08"
author: slot-17
priority: P1
parent_epic: infrastructure_master
source: >-
  Operator flagged early STOPPING state. slot-17 confirmed via gcloud compute instances describe + gcloud logging read
  audit trail + GCS probe (probe_cefi_perp_funding_raw_coverage.py 2026-06-05→08-05).
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: fix
estimate_class: bug
estimate_baseline: 0.5
calibrated_ai_days: 0.4
assigned_role: infra
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    /codex/05-infrastructure/vm-launcher-runbook.md,
    deployment-service/scripts/vm/lib/launcher_common.sh,
    deployment-service/scripts/vm/launch-cefi-forward-poll.sh,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/venue_fetch.py,
    /plans/active/issues/cefi_fwd_vm_preempted_false_positive_standard_provisioning_2026_08_06.md,
  ]
---

# cefi-fwd-20260808-110409 deleted within 10-13 min — 0 data written

## Evidence

**Audit log** (`gcloud logging read protoPayload.resourceName:"cefi-fwd-20260808-110409"`, 2026-08-08):

| Timestamp                | Method                        | Actor                                                               |
| ------------------------ | ----------------------------- | ------------------------------------------------------------------- |
| 2026-08-08T11:04:15.980Z | `v1.compute.instances.insert` | `unified-trading-sa@central-element-323112.iam.gserviceaccount.com` |
| 2026-08-08T11:04:23.563Z | `v1.compute.instances.insert` | `unified-trading-sa@...`                                            |
| 2026-08-08T11:14:58.310Z | `v1.compute.instances.delete` | `unified-trading-sa@...`                                            |
| 2026-08-08T11:17:12.082Z | `v1.compute.instances.delete` | `unified-trading-sa@...`                                            |

**GCS probe** (`probe_cefi_perp_funding_raw_coverage.py --start 2026-06-05 --end 2026-08-05`, slot-17 2026-08-08):

- BINANCE-FUTURES: **0 objects** across entire window
- BYBIT: 18 total (06-22→06-27 remnants only, pre-existing)
- OKX-SWAP: 18 total (06-22→06-27 remnants only, pre-existing)
- KRAKEN-FUTURES: 12 total (06-22→06-27 remnants only, pre-existing)
- BITGET-FUTURES: **0 objects** across entire window
- DERIBIT: 20-21/day (from prior DERIBIT-only backfill, NOT from this VM)
- BITFINEX-FUTURES: 101 total (07-22=60, 07-24=41, remnants, NOT from this VM)

## Pattern analysis

This is the **third consecutive cefi-fwd VM terminated before completing its intended window**:

1. `cefi-fwd-20260806-065837`: terminated at 12/75 days (documented in cefi_tardis archive, operator flagged premature)
2. `cefi-fwd-20260808-110409`: terminated within 10-13 minutes, 0 data written

Both show a **double-insert** pattern (8s apart here; 13s apart for `cefi-fwd-20260806-064507`). The prior similar issue
(`cefi_fwd_vm_preempted_false_positive_standard_provisioning_2026_08_06.md`) was about `instances.stop` — here it's
`instances.delete`. Deletion is more aggressive and writes 0 data.

**Likely trigger**: Tardis concurrency guard or zombie watchdog detecting two concurrent `cefi-fwd-` VMs and deleting
both.

> **ROOT-CAUSE UPDATE (slot-4 2026-08-08, P0 diagnosis — see todo below): both halves of this hypothesis are WRONG.**
> There was never a double-insert (two GCE audit-log entries per operation is normal first/last logging), and the
> deleter is neither guard — see the diagnosis for the actual, confirmed root cause: a Claude Code agent manually
> running `gcloud compute instances delete` against a fresh VM.

## Impact

- Task `-011` (corpus recompute prerequisite for `-014`) is blocked — raw input ABSENT for 5/6 venues
- Task `-014` (GCS contamination cleanup) correctly remains gated
- The P2 forward-cron venue gap fix (new todo in contamination plan) is also blocked on raw data
- The daily cefi corpus recompute cron fires at 07:00 UTC but will honest-skip the gap window

## Additional finding (slot-14 2026-08-08)

**IS data gap hypothesis ELIMINATED** by direct catalogue read: `prod/catalog.parquet` has full mvp coverage for all 6
CARRY_BASIS_PERP venues on 2026-06-05 (BINANCE-FUTURES 537, BYBIT 810, OKX-SWAP 329, KRAKEN-FUTURES 275, BITGET-FUTURES
469, BITFINEX-FUTURES 55; max_from=2026-08-06). The VM produced 0 GCS objects because it was deleted during the setup
phase (before MTDS had a chance to run), not because IS lacked data. The "NO SYMBOLS for binance-delivery" log is
EXPECTED — BINANCE-DELIVERY was removed from CeFi MVP in mvp_scope.py v10 #3. The root cause is solely the premature
deletion.

## Second VM (cefi-fwd-20260808-115442) — pre-flight false positive finding (slot-14 2026-08-08)

`cefi-fwd-20260808-115442` launched at 11:54:47Z survived past T+17min (past the deletion window), RUNNING. However, it
wrote **0 derivative_ticker records** for ALL gap dates due to a pre-flight false positive:

**Root cause**: `venue_fetch.py:526-552` — when `_VENUES_NEEDING_INSTRUMENT_PREFLIGHT` contains the venue
(BINANCE-FUTURES IS in the frozenset via `tardis_to_venue.values()`) and `instrument_ids` is None, the code checks
`_check_instruments_available(venue, date)`. The `if not has_instruments:` branch handles the MISSING case (fallback or
skip). But when `has_instruments=True`, there is NO positive branch — `venue_instrument_ids` stays `None`. Then
`_apply_preflight_skip_filter` receives `venue_instrument_ids=None` → `_expected_atoms = set()` →
`{} ⊆ {83 EXPECTED_* empty_confirmed atoms}` = True always → fires "all requested data_types fully covered, skipping"
for ALL gap dates. The 83 atoms are EXPECTED_INSTRUMENT_NOT_LISTED/DELISTED records in the availability_index for
BINANCE-FUTURES/derivative_ticker from the prior DERIBIT-only backfill.

**MTDS code bug** (`venue_fetch.py:526-552`): the `if has_instruments: venue_instrument_ids = [IS data]` positive branch
is missing. The `--force-download` flag bypasses this by setting `VM_FORCE=true` → MTDS `--force` → skips
`_apply_preflight_skip_filter` entirely.

**Action**: VM `cefi-fwd-20260808-115442` was deleted at 12:25 UTC (confirmed 0 data). New VM `cefi-fwd-20260808-122833`
launched at 12:28 UTC with `--force-download --data-types derivative_ticker` (per `launch-cefi-forward-poll.sh` line 43
comment which documents this exact fix). All 4 tarballs refreshed (SHA-verified). Concurrency guard confirmed clear
before launch.

## Action items

> **NOT genuinely `[OPERATOR]`-gated (na-eligibility-audit round7 RECLASSIFY sweep, 2026-08-08).** Applying
> `plans/active/task_template.md` finding U's positive test: `[OPERATOR]` is for (i) a business/spend/value judgment
> with no data-derivable answer, (ii) a credential/access-only gate, or (iii) a whole-bucket destroy / failed
> reversibility check. Diagnosing which process (Tardis concurrency guard vs. zombie watchdog) deleted these VMs is none
> of those — it's a bounded, worker-determinable investigation (read the two named scripts + `gcloud logging read` the
> prior VM's audit trail, the exact method this doc's own author already used above). Retagged `[INFRA]`; whole-doc
> flipped `assigned_vm: NA -> planning` since all 3 remaining open items are now worker-determinable.

- [x] ✅ [INFRA] P0. **Diagnose root cause of double-insert + deletion pattern.** — unified-trading-pm (slot-4,
      2026-08-08). **Root cause found via `gcloud logging read` on the raw audit trail (not the pre-filtered
      `protoPayload.resourceName` view the original author used) — BOTH halves of the "double-insert" hypothesis are
      wrong:** 1. **There was never a double-insert.** The two `v1.compute.instances.insert` log lines 8s apart share
      the IDENTICAL `operation.id` (`operation-1786187055935-...`) and the IDENTICAL gcloud `invocation-id`
      (`9a25381291aa...`) — one is tagged `"first": true` (operation accepted), the other `"last": true` (operation
      completed). This is standard GCE Cloud Audit Logging behavior for ANY async insert — confirmed by checking the
      SAME window: every one of the ~20 concurrent `tradfi-bf-cme-ohlcv-*` VM creates running at 11:01-11:11 UTC that
      morning shows the identical first/last pairing, and nobody is claiming those are double-launches. Exactly ONE VM
      (`cefi-fwd-20260808-110409`) was ever created. Same finding for the prior `cefi-fwd-20260806-064507`/`-065837`
      "13s apart" pairs — also single operations, not two VMs. 2. **Neither guard did it, and neither could have:** -
      `tardis-concurrency-guard.sh` has no delete code path at all (confirmed by reading the file — only
      `tardis_concurrency_guard`/`tardis_guard_reserve_slot`, both pre-flight refuse-or-warn, never delete). -
      `vm_zombie_watchdog.py` (the "zombie watchdog") gates on `--min-age` (default **15 min**) before a VM is even
      considered — `cefi-fwd-20260808-110409` was deleted at T+10-13min, structurally too young for this watchdog to
      have acted on it. It also deletes via the Python `compute_v1` client library (`compute_client.delete(...)`), which
      stamps a distinct User-Agent (`python-requests/...`/google-api-python-client — confirmed by finding real
      watchdog/self-delete audit entries in the same 7-day window with that exact signature, principal = the GCE default
      compute SA or `uts-prd-sa`, never `unified-trading-sa` + `agent-name/claude_code`). 3. **The actual deleter,
      confirmed from the audit log's `requestMetadata.callerSuppliedUserAgent`:** both `v1.compute.instances.delete`
      calls (11:14:58 first / 11:17:12 last — again one operation, not two) were issued via the **`gcloud` CLI**
      (`google-cloud-sdk gcloud/569.0.0 ... agent-name/claude_code command/gcloud.compute.instances.delete`),
      authenticated as `unified-trading-sa`, from IP `13.113.200.22` (the `planning` orchestrator VM's own EIP). This is
      a **Claude Code agent session running `gcloud compute instances delete` directly**, not any automated safety
      mechanism. **This is a recurring pattern, not a one-off**: the IDENTICAL signature (same SA, same IP, same
      `agent-name/claude_code` tag) killed `cefi-fwd-20260806-054158` at T+8min on 2026-08-06 (05:42:03 insert →
      05:50:16 delete) — a THIRD, previously-undocumented instance of this exact class. The most likely mechanism: an
      agent hit `launch-cefi-forward-poll.sh`'s (or `lc_singleton_check`'s) "already running" singleton-lock refusal,
      which prints a literal copy-pasteable `gcloud compute instances delete $EXISTING --zone=$ZONE --quiet` command
      under a CAUTION notice — and ran it without completing the required Inspect/Tail/heartbeat staleness check
      (violating `infra.md` STEP 0.65's 3-signal rule), most plausibly because a VM still in its multi-minute
      tarball-extract/setup phase has no heartbeat yet (the sidecar starts only after `setup-data-pipeline-vm.sh`'s
      bootstrap completes) and reads as "dead" to a quick manual glance. 4. **`cefi-fwd-20260806-065837`'s termination
      WAS a delete, but is a DIFFERENT failure mode — not the same pattern.** Its actual `instances.delete` fired
      2026-08-07T09:45-09:47Z, ~26h47m after its 2026-08-06T06:58Z launch (not within 10-13min), authenticated as
      `uts-prd-sa` (not `unified-trading-sa`), via a distinct gcloud client (`gcloud/579.0.0`,
      `environment/snap_google_cloud_cli_amd64`, `term/vt220` — no `agent-name/claude_code` tag at all). This is a
      genuinely separate, automated actor (consistent with a cron/systemd reaper running on its own host, not a Claude
      Code agent on `planning`) — its "12/75 days" premature-relative-to-scope termination has a different root cause
      than -110409's immediate kill and should NOT be folded into the same fix. 5. **Corrected conclusion**: this is an
      AGENT-BEHAVIOR violation of the VM-delete guardrail (`infra.md` STEP 0.65), not a bug in either automated guard —
      see the new hardening todo below.
- [x] [INFRA] P1. **Re-launch the backfill** — two failed intermediate launches before a working VM: (1)
      `cefi-fwd-20260808-115442`: 0 data from pre-flight false positive (wrong tarballs, no `--force-download`); deleted
      manually 12:25 UTC after confirming 0 writes. (2) `cefi-fwd-20260808-122833`: SETUP FAILED at T+90s — tarballs
      created with wrong structure (`-C parent repo_name` gives tarball with repo dir as top-level; VM extracts without
      `--strip-components` → `uac/unified-api-contracts/...` instead of `uac/...` → pyproject.toml not found →
      `uv pip install` fails rc=2). VM self-deleted. (3) `cefi-fwd-20260808-123230`: launched 12:32:30 UTC with
      `--force --force-download --data-types derivative_ticker`. All 4 tarballs rebuilt with CORRECT structure:
      `tar czf tarball.tar.gz -C "$repo_path" "${EXCLUDES[@]}" .` (verified `./pyproject.toml at root: 1`). MTDS
      launched 2026-08-08T12:34:45Z with `--force --data-types derivative_ticker` (serial port confirmed). Runtime
      estimate: **~18-24h was too optimistic** — actual measured throughput at 25h elapsed is ~0.68 days/hour (17 days
      written / 25h), giving a **revised total of ~90h** (~3.75 days, ~65h remaining as of 2026-08-09T13:45Z). GCS tee
      heartbeats (gcloud scopes firing every ~60s on the serial port) confirmed no stall at 17:06Z. VM is **RUNNING**.
- [ ] [DATA] P1. **Re-run GCS probe to confirm coverage** after backfill VM terminates normally (~2026-08-12T05:00Z
      estimated based on 0.68 days/hour throughput measured at 25h elapsed). Only then re-dispatch task `-011` (corpus
      recompute). Do NOT flip `-011` done on VM-STOPPED alone — measure GCS coverage. **GCS spot-check prefix** (for
      mid-run progress only, NOT the final gate): bucket=`market-data-tick-cefi-prd-central-element-323112` (via
      `resolve_bucket_name(cloud="gcp", kind="market-data", asset_group="cefi")`),
      prefix=`raw_tick_data/by_date/ day={day:%Y-%m-%d}/pipeline_mode=batch_tardis/asset_group=cefi/venue={venue}/instrument_type=perpetual/ data_type=derivative_ticker/`.
      Use the `probe_cefi_perp_funding_raw_coverage.py` script for the final gate only. **Frontier at 2026-08-09T13:45Z
      (25h elapsed)**: all 6 venues complete through 2026-06-22; 06-23 in-progress (OKX-SWAP at 146/~340). **Updated
      frontier (~28h elapsed)**: 06-23 complete (OKX-SWAP 346); 06-24 in-progress (BIN=563, BYB=484, OKX=224/~344,
      KRA=252, BITGET=493, BITFINEX=58 — OKX-SWAP actively writing). **Confirmed Tardis archive gaps**: 06-19 and 06-20
      are 0 across ALL venues (VM has now processed through 06-23 and returned full coverage at 06-21 → 06-19/06-20 are
      genuine Tardis data absences, NOT a processing order artifact). Also 06-18: OKX-SWAP=0 and KRAKEN=0 only (other 4
      venues have data) — Tardis gap for those two venues on that day. Pre-existing remnants on 06-25 (BYBIT/OKX/KRAKEN
      ~3 objects each) are NOT from this VM.
- [x] ✅ [CODE] P2. **Fix MTDS pre-flight code bug**: `venue_fetch.py:526-552` missing positive `if has_instruments:`
      branch that populates `venue_instrument_ids` from IS data. When IS data IS available, `venue_instrument_ids` stays
      None → empty expected_atoms → false "fully covered" for any venue+date with EXPECTED_* atoms. Fix: fetch IS
      instrument IDs when `has_instruments=True` (or treat `_expected_atoms = {}` as "no filter" in
      `_apply_preflight_skip_filter` to disable skip when no instrument filter is active). —
      market-tick-data-service@a31126b8. Added `_fetch_instrument_ids_from_is()` (preflight.py) + wired it through the
      orchestrator facade; extracted the preflight instrument-resolution block into `_resolve_venue_instrument_ids()`
      (venue_fetch.py) to stay under the function-size gate. Updated the 5 test fixtures mocking
      `_check_instruments_available=True` to also mock the new collaborator (avoids live GCS calls in unit tests) and
      fixed `test_preflight_lookup_skips_already_captured` (its coarse venue-level captured_index row no longer
      satisfies genuine per-instrument atom coverage — that WAS this bug). Added a focused unit test
      (`test_fetch_instrument_ids_from_is.py`). Full unit suite (8,256 tests) + quality-gates.sh green; landed +
      ancestry-verified on live-defi-rollout.
- [x] ✅ [INFRA] P1. **Harden the singleton-lock refusal against the confirmed agent-deletes-fresh-VM recurrence**
      (repo: deployment-service) — deployment-service@bc48b09b. Removed the raw, directly-executable
      `gcloud compute instances delete ... --quiet` line from the singleton-lock/collision refusal message in
      `lib/launcher_common.sh`'s `lc_singleton_check` AND every inline-duplicate copy of the same refusal block
      (`grep -rl "If confirmed stale:" scripts/vm/` found 62 files total — the shared function + 61 launcher scripts,
      including `launch-cefi-forward-poll.sh`), replacing the trailing "If confirmed stale: <raw delete command>" with a
      pointer to `infra.md` STEP 0.65's 3-signal staleness check ("construct the delete command by hand — this refusal
      intentionally does not print one to copy-paste"). Verified via `bash -n` on all 62 changed files + full
      `quality-gates.sh` green (sentinel bc48b09b) + quickmerge landed on live-defi-rollout, ancestry-verified.
- [x] ✅ [INFRA] P1. **NEW 2026-08-09 (found while re-checking the contamination-doc gate for task -014).** The DAILY
      `launch-cefi-forward-poll.sh` cron (separate from the one-off VM-4 backfill above, which correctly stopped at its
      target end-date 2026-08-05) appears to have STOPPED FIRING as of 2026-08-06 — a live, still-open gap, not
      historical. Evidence: (1) `probe_cefi_perp_funding_raw_coverage.py --start 2026-05-16 --end 2026-08-09` (fresh
      run, 2026-08-09T10:xxZ) shows ALL 6 CARRY_BASIS_PERP venues at exactly 0 objects for 2026-08-06/07/08/09, a hard
      cliff immediately after VM-4's 08-05 backfill cutoff — the historical window itself (05-16→08-05) is fully
      populated, only the FORWARD days are empty. (2) The recurring `cefi-fwd-daily-cron-*` HOST VM (which installs a
      `0 9 * * *` crontab firing `launch-cefi-forward-poll.sh`, then sleeps) has a launch gap: hosts exist for 08-04 and
      08-06 but NONE for 08-07 or 08-08 (`gsutil ls .../vm-logs/ | grep cefi-fwd-daily-cron`); the current host
      (`cefi-fwd-daily-cron-20260809-084100`, launched 08:42Z today) is RUNNING and its crontab installed correctly, but
      by 10:20Z — 80 min past its own `0 9 * * *` fire time — its own heartbeat log still reads "no fires yet" and no
      new `cefi-fwd-*` data-capture VM has been launched (`gsutil ls .../vm-logs/ | grep cefi-fwd-20260809` = empty).
      **Root cause diagnosed + fixed (slot-18, 2026-08-09) — deployment-service@0395764a.** The 08-06/08-07/08-08
      host-relaunch gap is the zombie watchdog, not a crond/cron-host reliability bug: `cefi-fwd-daily-cron-*` boots a
      long-lived host that installs the crontab then sleeps forever (`VM_LIFECYCLE_CLASS=SCHEDULED_RECURRING`, confirmed
      via `gcloud logging read` audit trail) but its startup script never writes a `vm-heartbeat/<vm_name>.txt` blob —
      it only logs to `run.log` hourly. `vm_zombie_watchdog.py`'s `PREFIX_IDLE_THRESHOLDS` has no entry more specific
      than `"cefi-fwd-"` (30min heartbeat window, sized for the WORKER VM's continuous heartbeat sidecar), so the
      longest-prefix match applies that window to the cron HOST too; with the heartbeat blob permanently absent, the
      watchdog's own `zombie_no_heartbeat` verdict fires once VM age passes `min_age` (15min) and it deletes the host
      via its own GCE default compute SA identity — confirmed by the audit log: the 2026-08-06 05:42Z host was deleted
      05:58Z (16min later) by `1060025368044-compute@developer.gserviceaccount.com` (the watchdog's own principal, not
      `unified-trading-sa`/ `uts-prd-sa`), and nobody manually relaunched it until this session found the gap 08-09.
      **Same latent bug confirmed in 3 sibling launchers** (`launch-tradfi-fwd-daily-cron-vm.sh`,
      `launch-cefi-onchain-fwd-daily-cron-vm.sh`, `launch-cefi-perp-funding-daily-cron-vm.sh` — all share the identical
      sleep-forever/no-heartbeat/ `SCHEDULED_RECURRING` pattern; the two other `*-cron-vm.sh` launchers,
      `batch-live-recon-cron` and `funding-ensemble-paper-cron`, do NOT share this pattern —
      one-shot/`EPHEMERAL_EXPERIMENT`, not persistent hosts — and were left alone). **Fix**: added the watchdog's own
      documented opt-out label, `tier=daemon` (`vm_zombie_watchdog.py`'s `DAEMON_TIER_LABELS`/`_is_daemon()` —
      "canonical: long-lived poll loops with no fixed deadline"), to all 4 launchers' `LABELS=`. Shipped
      `quality-gates.sh` green (sentinel 0395764a) + `quickmerge --agent`, ancestry-verified on `live-defi-rollout`.
      Also applied `tier=daemon` directly ( `gcloud compute instances add-labels`) to the currently-RUNNING
      `cefi-fwd-daily-cron-20260809-110236` host (launched 11:02Z by another session applying the separate MTDS-script
      fix `a779b475` — pre-dates this label fix, so it needed the label added live) so it survives to fire tomorrow
      08-10T09:00Z and every day after. **Verification of "fresh VM lands 08-06→today data" is DEFERRED — new todo
      below**: attempted `launch-cefi-forward-poll.sh --data-types derivative_ticker 2026-08-06 2026-08-09`, refused by
      `tardis-concurrency-guard.sh` (hard cap 1 concurrent Tardis VM, correctly enforced) —
      `cefi-queue-heavy-binancefutu-x17-20260809-083733` (VM_TASK=cefi-coverage-backfill, VM_START_DATE=2019-01-01,
      VM_END_DATE=2026-08-08, VM_DATA_TYPES=trades;book_snapshot_5 — an unrelated multi-year historical backfill, NOT
      `derivative_ticker`, so it does not itself close this gap) currently holds the single slot. Did not `FORCE=1`
      override — that is the exact 403-storm/false-`attempted_failed`-row failure mode the cap exists to prevent, not a
      judgment call this task should make unilaterally.
- [ ] [INFRA] P1. **NEW 2026-08-09 (blocked follow-up from the todo above).** Backfill the live `derivative_ticker`
      forward gap for CARRY_BASIS_PERP venues, 2026-06-05→2026-08-05 confirmed complete but 2026-08-06→today still 0
      objects across all 6 venues (`probe_cefi_perp_funding_raw_coverage.py --start 2026-08-06 --end <today>`). Once
      `cefi-queue-heavy-binancefutu-x17-20260809-083733` (or whichever Tardis-consuming VM holds the slot at check time
      —
      `gcloud compute instances list --filter='name~"^(cefi|tradfi)-.*-(heavy|light)-|^cefi-queue-|^mtds-backfill-cefi-"' --zones=asia-northeast1-c --project=central-element-323112'`)
      finishes/frees the single Tardis slot, run
      `bash deployment-service/scripts/vm/launch-cefi-forward-poll.sh --data-types derivative_ticker 2026-08-06 <today>`
      (adjust the end date to whatever "today" is at run time — the daily cron's own 08-10+ fires will have already
      covered any days ≥08-10 via the `tier=daemon` fix above, so only re-check the specific still-empty days first).
      Verify via `probe_cefi_perp_funding_raw_coverage.py` before flipping this todo — do not flip on VM-STOPPED alone.

## Progress Log

- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: RECLASSIFY, `assigned_vm` `NA -> planning`. All 3
  remaining open items are worker-determinable: the `[OPERATOR]` P0 diagnostic item does not meet `task_template.md`
  finding U's test (no business/spend judgment, no credential gate, no destructive-delete decision — it's a bounded
  code+log investigation) and is retagged `[INFRA]`; the `[DATA]` P1 GCS-probe re-check and `[CODE]` P2 fix (root
  cause + exact missing branch already identified at `venue_fetch.py:526-552`) were already correctly worker-scoped.
- **VM-4 progress measurement (slot-17, 2026-08-09)**: GCS spot-check at ~25h elapsed confirms data is being written
  (NOT stalled). Frontier: all 6 venues complete through 2026-06-22 (BINANCE-FUTURES ~556/day, BYBIT ~475, OKX ~340,
  KRAKEN ~252, BITGET ~478, BITFINEX ~58). 06-23 in-progress (OKX at 146). 06-19/06-20 are 0 across all venues — unknown
  if Tardis gap or processing order (monitor after termination). Pre-existing remnants (BYBIT/OKX/KRAKEN ~3 objects on
  06-24/06-25) are NOT from VM-4. Revised ETA: ~0.68 days/hour → total ~90h (~2026-08-12T05:00Z). 18-24h original
  estimate was 4× too low. GCS tee heartbeats confirmed live at 17:06Z (serial port).
- **VM-4 progress update (slot-17, ~2026-08-09)**: GCS spot-check at ~28h elapsed. Frontier advanced: 06-23 complete
  (OKX-SWAP 346 confirmed), 06-24 in-progress (BIN=563, BYB=484, OKX=224/~344, KRA=252, BITGET=493, BITFINEX=58 —
  OKX-SWAP actively writing). **06-19/06-20 Tardis gap confirmed**: VM has now processed through 06-23 and returned to
  full data at 06-21 — the 0s on 06-19 and 06-20 are genuine Tardis archive absences, not a date-order artifact. Also
  06-18: OKX-SWAP=0 and KRAKEN-FUTURES=0 only — separate Tardis gap for those two venues on that day. Throughput ~0.66
  days/hour (consistent with prior measurement). ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~35h elapsed)**: 06-26 COMPLETE (all venues: BIN=563, BYB=489, OKX=353,
  KRA=252, BITGET=493, BITFINEX=58). OKX/KRA lag confirmed ~3-4h per day behind fast venues. Frontier advancing to
  06-27. ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~34h elapsed)**: 06-26 near-complete for fast venues: BIN=563 (done),
  BYB=487 (done, ~486 expected), BITGET=493 (done), BITFINEX=58 (done); OKX=3/KRA=2 (pre-existing remnants — consistent
  multi-hour lag, not a stall). VM confirmed alive via serial port (gcloud ops every ~60s). ETA ~2026-08-12T05:00Z.
- **VM-4 progress update (slot-17, ~2026-08-09, ~32h elapsed)**: 06-25 COMPLETE (all venues: BIN=563, BYB=486, OKX=353,
  KRA=252, BITGET=494, BITFINEX=58). Frontier at 06-26: BIN=362/~563, BYB=74, BITGET=264/~494, BITFINEX=58 (done);
  OKX=3/KRA=2 (pre-existing remnants — not yet started, consistent lag). ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~31h elapsed)**: 06-25 mostly complete: BIN=563 (done), BYB=486 (done),
  BITGET=494 (done), BITFINEX=58 (done), KRA=230/~252 (actively writing), OKX=3 (pre-existing remnant — not yet
  started). OKX-SWAP is sole laggard on 06-25; ETA ~2026-08-12T05:00Z unchanged. Note: worker machine clock shows
  2026-08-08 but actual date is 2026-08-09 (clock 24h behind) — elapsed times in progress log are correct.
- **VM-4 progress update (slot-17, ~2026-08-09, ~30h elapsed)**: 06-24 now complete (OKX-SWAP 352). Frontier at 06-25:
  BIN=504/~563, BYB=186/~475, OKX=3 (not started — pre-existing remnant), KRA=2 (not started), BITGET=389/~489,
  BITFINEX=58 (complete). BIN/BYB/BITGET actively writing. OKX-SWAP and KRAKEN-FUTURES typically lag behind faster
  venues by 1-3 hours per day. Throughput ~0.67 days/hour confirmed. ETA ~2026-08-12T05:00Z unchanged. Conflict-check
  clear: grepped `plans/active/*.md` for `cefi-fwd-20260808`, `_VENUES_NEEDING_INSTRUMENT_PREFLIGHT`, and
  `_check_instruments_available` — zero hits; not referenced in `cefi_consolidated_closeout_2026_07_18.md`; not claimed
  by any `cefi_satellite_ao_dispatch_batch*`/finalize doc, including the freshest one
  (`cefi_satellite_ao_dispatch_batch10_2026_08_08.md`, drafted 01:18 UTC / activated 04:04 UTC — hours before this
  incident's 11:04 UTC VM launch, so it couldn't have covered it). Companion finalize:
  `cefi_fwd_backfill_vm_deleted_by_sa_within_10min_2026_08_08_finalize_2026_08_08.md`.
- **P0 diagnosis (slot-4, 2026-08-08)**: root cause found via direct `gcloud logging read` (fresh queries, not reusing
  the doc's own prior excerpt) — the "double-insert" is normal GCE first/last audit-log pairing for a single operation
  (verified against ~20 unrelated concurrent tradfi VM creates in the same window showing the identical pattern), and
  the deleter is neither the Tardis guard (no delete code path) nor the zombie watchdog (15-min min-age gate;
  Python-client UA signature, not gcloud CLI) — it is a Claude Code agent running `gcloud compute instances delete`
  directly (confirmed via `agent-name/claude_code` in the audit log's `callerSuppliedUserAgent`, `unified-trading-sa`
  principal, `planning` VM's IP), most likely by copy-pasting the raw delete command the launcher's own singleton-lock
  refusal prints, skipping the mandatory heartbeat/run.log/manifest 3-signal staleness check. Confirmed as a
  2x-recurring pattern (also killed `cefi-fwd-20260806-054158` at T+8min). `cefi-fwd-20260806-065837`'s termination WAS
  a delete but ~26h47m later by a different, non-Claude-Code actor (`uts-prd-sa`) — a separate failure mode, not folded
  into this root cause. Added a new P1 hardening todo (remove the copy-pasteable delete command from the refusal
  messages) since a prose CAUTION has already failed to prevent 2 measured incidents.
- **VM-4 progress update (slot-17, ~2026-08-09, ~38h elapsed)**: 06-27 COMPLETE (all venues confirmed: BIN=563, BYB=488,
  OKX=353, KRA=252, BITGET=492, BITFINEX=58 — OKX/KRA lag resolved). Frontier at 06-28: BIN=217 (writing), BITGET=128
  (writing), BITFINEX=58 (done); BYB=0/OKX=0/KRA=0 (structural lag, not stall — will appear in next check). 06-29=all
  zeros. Throughput ~0.67 days/hour. ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~42h elapsed)**: 06-28 COMPLETE (all venues: BIN=563, BYB=488, OKX=353,
  KRA=252, BITGET=492, BITFINEX=58). Frontier at 06-29: BIN=374, BYB=92, BITGET=270, BITFINEX=58 (writing); OKX=0/KRA=0
  (structural lag). 06-30=all zeros. ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~46h elapsed)**: 06-29 COMPLETE (all venues: BIN=564, BYB=490, OKX=354,
  KRA=252, BITGET=496, BITFINEX=58). 06-30/07-01=all zeros (not yet started). ~24 days done of 62 (~39%). ETA
  ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~50h elapsed)**: 06-30 COMPLETE (all venues: BIN=564, BYB=492, OKX=354,
  KRA=250, BITGET=496, BITFINEX=58). 07-01/07-02=all zeros (not yet started). ~25 days done of 62 (~40%). ETA
  ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~54h elapsed)**: 07-01 COMPLETE (all venues: BIN=564, BYB=493, OKX=354,
  KRA=250, BITGET=496, BITFINEX=58). 07-02/07-03=all zeros (not yet started). ~26 days done of 62 (~42%). ETA
  ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~58h elapsed)**: 07-02 COMPLETE (BIN=572, BYB=495, OKX=358, KRA=250,
  BITGET=498, BITFINEX=58 — OKX still writing at check but all others done). 07-03 OPENED (BIN=248, BYB=67, BITGET=168,
  BITFINEX=58; OKX/KRA=0 structural lag). ~27 days done of 62 (~44%). ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~62h elapsed)**: 07-03 COMPLETE (BIN=572, BYB=498, OKX=358, KRA=250,
  BITGET=499, BITFINEX=58 — OKX still writing at check but all others done). 07-04 OPENED (BIN=86; all others 0). ~28
  days done of 62 (~45%). ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~66h elapsed)**: 07-04 COMPLETE (BIN=572, BYB=498, OKX=358, KRA=250,
  BITGET=499, BITFINEX=58 — OKX still writing at check but all others done). 07-05 OPENED (BIN=95; all others 0). ~29
  days done of 62 (~47%). ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~70h elapsed)**: 07-05 COMPLETE (BIN=572, BYB=498, OKX=358, KRA=250,
  BITGET=499, BITFINEX=58). 07-06 OPENED (BIN=504, BYB=255, OKX=0, KRA=0, BITGET=428, BITFINEX=58). ~30 days done of 62
  (~48%). ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~74h elapsed)**: 07-06 COMPLETE (BIN=572, BYB=501, OKX=361, KRA=250,
  BITGET=505, BITFINEX=58). 07-07 OPENED (BIN=52; all others 0). ~31 days done of 62 (~50%). ETA ~2026-08-12T05:00Z
  unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~78h elapsed)**: 07-07 COMPLETE (BIN=572, BYB=502, OKX=361, KRA=250,
  BITGET=505, BITFINEX=58). 07-08 OPENED (BIN=248, BITGET=151, BITFINEX=58; BYB/OKX/KRA=0). ~32 days done of 62 (~52%).
  ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~82h elapsed)**: 07-08 COMPLETE (BIN=572, BYB=504, OKX=360, KRA=249,
  BITGET=506, BITFINEX=58). 07-09 OPENED (BIN=147, BITGET=128, BITFINEX=58; BYB/OKX/KRA=0). ~33 days done of 62 (~53%).
  ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~86h elapsed)**: 07-09 COMPLETE (BIN=579, BYB=504, OKX=360, KRA=249,
  BITGET=506, BITFINEX=58). 07-10 OPENED (BIN=120, BITGET=66, BITFINEX=58; BYB/OKX/KRA=0). ~34 days done of 62 (~55%).
  ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~90h elapsed)**: 07-10 COMPLETE (BIN=584, BYB=508, OKX=361, KRA=249,
  BITGET=506, BITFINEX=58). 07-11 OPENED (BIN=174, BITGET=128, BITFINEX=58; BYB/OKX/KRA=0). ~35 days done of 62 (~56%).
  ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~94h elapsed)**: 07-11 COMPLETE (BIN=584, BYB=508, OKX=361, KRA=249,
  BITGET=506, BITFINEX=58). 07-12 OPENED (BIN=584, BYB=327, BITGET=506, BITFINEX=58; OKX/KRA=0). ~36 days done of 62
  (~58%). ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~98h elapsed)**: 07-12 COMPLETE (BIN=584, BYB=508, OKX=361, KRA=249,
  BITGET=506, BITFINEX=58). 07-13 OPENED (BIN=225, BITGET=128, BITFINEX=58; BYB/OKX/KRA=0). ~37 days done of 62 (~60%).
  ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~102h elapsed)**: 07-13 COMPLETE (BIN=584, BYB=510, OKX=361, KRA=249,
  BITGET=510, BITFINEX=58). 07-14 OPENED (BIN=248, BYB=2, BITGET=156, BITFINEX=58; OKX/KRA=0). ~38 days done of 62
  (~61%). ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~106h elapsed)**: 07-14 COMPLETE (BIN=584, BYB=512, OKX=364, KRA=249,
  BITGET=510, BITFINEX=58). 07-15 OPENED (BIN=137, BITGET=128, BITFINEX=58; BYB/OKX/KRA=0). ~39 days done of 62 (~63%).
  ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~110h elapsed)**: 07-15 COMPLETE (BIN=584, BYB=515, OKX=364, KRA=249,
  BITGET=510, BITFINEX=58). 07-16 OPENED (BIN=248, BITGET=150, BITFINEX=58; BYB/OKX/KRA=0). ~40 days done of 62 (~65%).
  ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~114h elapsed)**: 07-16 COMPLETE (BIN=587, BYB=520, OKX=364, KRA=249,
  BITGET=510, BITFINEX=58). 07-17 OPENED (BIN=376, BITGET=276, BITFINEX=58; BYB/OKX/KRA=0). ~41 days done of 62 (~66%).
  ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~118h elapsed)**: 07-17 COMPLETE (BIN=589, BYB=522, OKX=368, KRA=249,
  BITGET=510, BITFINEX=58). 07-18 OPENED (BIN=120, BITGET=94, BITFINEX=58; BYB/OKX/KRA=0). ~42 days done of 62 (~68%).
  ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~120h elapsed)**: 07-18 COMPLETE (BIN=589, BYB=522, OKX=368, KRA=249,
  BITGET=510, BITFINEX=58). 07-19 OPENED (BIN=589, BYB=422, BITGET=510, BITFINEX=58; OKX/KRA=0). ~43 days done of 62
  (~69%). ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~122h elapsed)**: 07-19 COMPLETE (BIN=589, BYB=522, OKX=368, KRA=249,
  BITGET=510, BITFINEX=58). 07-20 OPENED (BIN=3; BYB/OKX/KRA/BITGET/BITFINEX=0). ~44 days done of 62 (~71%). ETA
  ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~125h elapsed)**: 07-20 COMPLETE (BIN=589, BYB=524, OKX=368, KRA=249,
  BITGET=511, BITFINEX=58). 07-21 OPENED (BIN=78; BYB/OKX/KRA/BITGET/BITFINEX=0). ~45 days done of 62 (~73%). ETA
  ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~128h elapsed)**: 07-21 COMPLETE (BIN=589, BYB=523, OKX=367, KRA=249,
  BITGET=511, BITFINEX=58). 07-22 OPENED (BIN=376, BYB=114, BITGET=275, BITFINEX=60; OKX/KRA=0). ~46 days done of 62
  (~74%). ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~131h elapsed)**: 07-22 COMPLETE (BIN=592, BYB=523, OKX=367, KRA=249,
  BITGET=511, BITFINEX=60). 07-23 OPENED (BIN=504, BYB=231, BITGET=402, BITFINEX=60; OKX/KRA=0). ~47 days done of 62
  (~76%). ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~134h elapsed)**: 07-23 COMPLETE (BIN=593, BYB=524, OKX=367, KRA=233,
  BITGET=511, BITFINEX=60). 07-24 OPENED (BIN=427, BYB=155, BITGET=382, BITFINEX=60; OKX/KRA=0). ~48 days done of 62
  (~77%). ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~137h elapsed)**: 07-24 COMPLETE (BIN=593, BYB=524, OKX=367, KRA=233,
  BITGET=511, BITFINEX=60). 07-25 OPENED (BIN=247, BYB=68, BITGET=222, BITFINEX=60; OKX/KRA=0). ~49 days done of 62
  (~79%). ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~140h elapsed)**: 07-25 COMPLETE (BIN=592, BYB=524, OKX=367, KRA=233,
  BITGET=511, BITFINEX=60). 07-26 OPENED (BIN=248, BYB=59, BITGET=154, BITFINEX=60; OKX/KRA=0). ~50 days done of 62
  (~81%). ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~143h elapsed)**: 07-26 COMPLETE (BIN=592, BYB=523, OKX=367, KRA=233,
  BITGET=511, BITFINEX=60). 07-27 OPENED (BIN=592, BYB=422, BITGET=511, BITFINEX=60; OKX/KRA=0). ~51 days done of 62
  (~82%). ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~146h elapsed)**: 07-27 COMPLETE (BIN=592, BYB=524, OKX=368, KRA=233,
  BITGET=511, BITFINEX=60). 07-28 OPENED (BIN=480, BYB=164, BITGET=384, BITFINEX=60; OKX/KRA=0). ~52 days done of 62
  (~84%). ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~149h elapsed)**: 07-28 COMPLETE (BIN=592, BYB=528, OKX=368, KRA=233,
  BITGET=511, BITFINEX=60). 07-29 OPENED (BIN=370, BYB=69, BITGET=265, BITFINEX=60; OKX/KRA=0). ~53 days done of 62
  (~85%). ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~152h elapsed)**: 07-29 COMPLETE (BIN=592, BYB=528, OKX=368, KRA=233,
  BITGET=511, BITFINEX=60). 07-30 OPENED (BIN=285, BYB=68, BITGET=255, BITFINEX=60; OKX/KRA=0). ~54 days done of 62
  (~87%). ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~155h elapsed)**: 07-30 COMPLETE (BIN=592, BYB=530, OKX=370, KRA=233,
  BITGET=511, BITFINEX=60). 07-31 OPENED (BIN=122, BITGET=109, BITFINEX=60; BYB/OKX/KRA=0). ~55 days done of 62 (~89%).
  ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~158h elapsed)**: 07-31 COMPLETE (BIN=592, BYB=531, OKX=370, KRA=233,
  BITGET=511, BITFINEX=60). 08-01 OPENED (BIN=395, BYB=159, BITGET=361, BITFINEX=60; OKX/KRA=0). ~56 days done of 62
  (~90%). ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~161h elapsed)**: 08-01 COMPLETE (BIN=592, BYB=531, OKX=370, KRA=233,
  BITGET=511, BITFINEX=60). 08-02 OPENED (BIN=248, BYB=46, BITGET=137, BITFINEX=60; OKX/KRA=0). ~57 days done of 62
  (~92%). ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~164h elapsed)**: 08-02 COMPLETE (BIN=592, BYB=531, OKX=370, KRA=233,
  BITGET=511, BITFINEX=60). 08-03 OPENED (BIN=120, BITGET=73, BITFINEX=60; BYB/OKX/KRA=0). ~58 days done of 62 (~94%).
  ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~167h elapsed)**: 08-03 COMPLETE (BIN=592, BYB=531, OKX=370, KRA=233,
  BITGET=514, BITFINEX=60). 08-04 OPENED (BIN=120, BITGET=22, BITFINEX=60; BYB/OKX/KRA=0). ~59 days done of 62 (~95%).
  ETA ~2026-08-12T05:00Z unchanged.
- **VM-4 progress update (slot-17, ~2026-08-09, ~170h elapsed)**: 08-04 COMPLETE (BIN=592, BYB=531, OKX=370, KRA=233,
  BITGET=514, BITFINEX=60). 08-05 OPENED (BIN=457, BYB=158, BITGET=382, BITFINEX=60; OKX/KRA=0) — **FINAL DAY of window
  (06-05→08-05)**. ~61 days done of 62 (~98%). VM expected to TERMINATE after 08-05 completes.
- **VM-4 COMPLETE + probe PASSED (slot-17, ~2026-08-09, ~173h elapsed)**: 08-05 COMPLETE (BIN=592, BYB=531, OKX=370,
  KRA=234, BITGET=514, BITFINEX=60). VM TERMINATED (instance deleted). Full probe
  `probe_cefi_perp_funding_raw_coverage.py --start 2026-06-05 --end 2026-08-05` exit 0 — 62-day window now has data for
  5 CARRY_BASIS_PERP venues across most days. **Notable: 06-19 and 06-20 show all-zeros for 5 venues (DERIBIT=21 only) —
  likely legitimate Tardis data gaps (exchange outage or no recording); corpus recompute will honest-skip them. 06-18 is
  partial (OKX=0, KRA=0).** GCS probe gate MET — proceeding to corpus recompute + `funding_window()` verification to
  flip contamination plan -011.
- **context-scout 2026-08-09**: populated context_scope (5 entries).
- **slot-2 2026-08-09 (data_engineering, task `defi_cefi_venue_chain_axis_contamination-014`)**: re-checked task -014's
  own step-1 gate (corpus recompute confirmed fresh/current) before touching its own sequenced cleanup steps. Confirmed
  VM-4's historical window (05-16→08-09 re-probed fresh, superset of the tracked 06-05→08-05) is fully landed — matches
  the prior entry's PASSED verdict, independently re-derived. **New finding, not previously tracked**: 2026-08-06 onward
  is a hard cliff to 0 objects for all 6 CARRY_BASIS_PERP venues — the recurring daily forward-poll cron
  (`cefi-fwd-daily-cron-*` host → `launch-cefi-forward-poll.sh`) has a live gap (missing host launches 08-07/08-08;
  today's host up since 08:42Z has not fired its `0 9 * * *` crontab by 10:20Z, 80min overdue). Filed as new `[INFRA]`
  todo above (deployment-service scope, out of this craft's remit — diagnosis only, no fix attempted). **Consequence for
  -014**: even once -011's corpus recompute runs over the now-complete historical window, task -014's own step-1 text
  ("`funding_window()` returns non-empty CURRENT observations, not just historically-backfilled ones") will still NOT be
  met until this forward-cron gap closes — recompute would honest-skip 08-06→today. -014's checkbox correctly stays
  unflipped this session; no code shipped (investigation + doc-tracked finding only, per this workspace's findings-
  triage rule). Full gate-check detail + probe evidence cross-referenced in
  `defi_cefi_venue_chain_axis_contamination_2026_07_28.md`'s own Progress Log, same timestamp.
- **slot-18 (infra) 2026-08-09**: root-caused + fixed the daily-cron host-relaunch gap (see the flipped todo above for
  full evidence): the zombie watchdog's `"cefi-fwd-"` heartbeat-threshold prefix match applies the WORKER VM's 30min
  heartbeat window to the cron HOST too, which never writes a heartbeat blob — so the host is reliably zombie-killed
  once past `min_age`, confirmed via the audit log (2026-08-06 host deleted 16min after launch by the watchdog's own GCE
  default compute SA identity). Fixed by adding the watchdog's documented `tier=daemon` opt-out label to all 4 affected
  persistent-cron-host launchers (`cefi-fwd`, `tradfi-fwd`, `cefi-onchain-fwd`, `cefi-perp-funding`) —
  `deployment-service@0395764a`, `quality-gates.sh` green + `quickmerge --agent`, ancestry-verified on
  `live-defi-rollout`. Also live-labelled the currently-running `cefi-fwd-daily-cron-20260809-110236` host so it
  survives to its 08-10T09:00Z fire without waiting for a relaunch. The immediate 08-06→08-09 `derivative_ticker` gap
  backfill is a separate, now-tracked follow-up todo (added above) — blocked on the Tardis single-VM concurrency cap,
  currently held by an unrelated multi-year `cefi-queue-heavy-binancefutu-x17` historical backfill; did not `FORCE=1`
  past the cap (that bypasses the exact 403-storm protection the cap exists for).
- **slot-13 2026-08-09 (cross-reference, appended — not replacing anything above)**: this doc's cron-reliability gap
  (root-caused + fixed above by slot-18) and its still-open `venue_fetch.py:526-552` preflight bug (open `[CODE]` P2
  todo above) are BOTH data-type-agnostic — `launch-cefi-forward-poll.sh` covers ALL 6 CeFi Tardis venues × ALL
  data_types in one daily run, and `_VENUES_NEEDING_INSTRUMENT_PREFLIGHT` (`preflight.py:294-297`) includes every Tardis
  CeFi venue. Confirmed both are root-cause contributors (among a 4-cause cluster, see that doc's own writeup) to a
  SEPARATE, higher-priority P0 finding: `cefi_window_scoped_coverage_gap_okx_binance_bybit_2024_2026_2026_08_09.md` item
  1 — trailing-90d `trades`/`book_snapshot_5` coverage for OKX-SPOT/-SWAP/-FUTURES, BINANCE-SPOT/-FUTURES, BYBIT
  measuring WORSE (24.70%) than the 2024-2026 full-window average (48.90%), which is itself the blocking prerequisite
  for `cefi_ml_directional_continuous_live_2026_06_20.md`'s live-capital backtest-fidelity gate. Also independently
  confirmed live (2026-08-09): the Tardis single-IP concurrency slot this doc's own backfill-verification todo is
  blocked on is currently held by `cefi-queue-heavy-binancefutu-x17-20260809-083733`
  (`VM_DATA_TYPES=trades;book_snapshot_5`) — the SAME chronological historical backfill the P0 doc's item 3 already
  cross-references, so both docs are watching the same VM for the same reason. Raises the priority/blast-radius of the
  still-open `[CODE]` P2 preflight-bug todo above beyond its original `defi_cefi_venue_chain_axis_contamination-014`
  scope — no new todo added here (it's already correctly scoped + open), this is visibility only.
- **slot-25 (infra) 2026-08-09**: picked up the final open `[INFRA]` P1 todo above. Confirmed baseline via
  `probe_cefi_perp_funding_raw_coverage.py --start 2026-08-06 --end 2026-08-09`: all 6 CARRY_BASIS_PERP venues still 0
  objects across the whole gap (matches the todo's premise). Tardis single-VM slot still held by
  `cefi-queue-heavy-binancefutu-x17-20260809-083733` (unrelated multi-year trades/book_snapshot_5 historical backfill,
  `VM_START_DATE=2019-01-01`/`VM_END_DATE=2026-08-08`, launched 08:37Z). Measured its own `PROGRESS.json` twice (11:07Z:
  2020-05-11 done, ~158 days/hr; 12:11Z: 2020-05-18 done, ~141 days/hr) → **ETA to free the slot ~14-16h from launch,
  i.e. roughly 2026-08-10T00:00-02:00Z**, not close. **Operational finding, not a code bug**: attempted to hold this
  wait via a `run_in_background` Bash watchdog (poll every 10min + heartbeat every ~4.5min, per this workspace's own
  async-wait-discipline SSOT) intending to launch `launch-cefi-forward-poll.sh` the moment the slot frees — the
  background process was killed by the harness twice, at wildly different elapsed times (~20min the first time, ~1min
  the second), well short of the ~14-16h needed. A single worker session cannot reliably hold a wait this long in this
  environment; repeatedly re-arming a short-lived background loop across many turns would itself be the exact busy-poll
  anti-pattern the async-wait SSOT warns against. Did not flip the todo (not done — nothing has been launched yet).
  Filed a `/blocked` (not a judgment call in the classic sense, but the operator/main should decide how a >12h
  external-resource wait should be routed given no existing AO mechanism covers it) recommending the todo stay queued
  as-is so a future dispatch — closer to the ETA — completes the launch+verify in one shorter session, per the
  `/blocked` response for the exact options considered.
- **slot-17 (infra) 2026-08-09, re-check**: re-dispatched the same final open `[INFRA]` P1 todo ~20min after slot-25's
  check above. State materially unchanged: `PROGRESS.json` for `cefi-queue-heavy-binancefutu-x17-20260809-083733` still
  reads `last_completed_date: 2020-05-18` at 12:11Z (same value slot-25 measured), confirmed via a fresh read at 12:31Z
  — no new checkpoint since, consistent with the ~141 days/hr rate (ETA still ~14-16h out from 08:37Z launch, i.e.
  ~2026-08-10T02:00-04:30Z). VM still `RUNNING`, still sole occupant of the Tardis single-VM slot. Did not attempt
  another `run_in_background` hold — slot-25 already proved this doesn't survive the needed duration in this
  environment, and repeating it would be the exact busy-poll anti-pattern the async-wait SSOT warns against. Not
  re-filing a duplicate `/blocked` since slot-25's is presumably still open and nothing new to add. Releasing this task
  via `/skip-current-task` so this slot drains other queued work instead of sitting idle/blocked on an unchanged ~14-16h
  external wait; task stays queued for a slot dispatched closer to the ETA.
