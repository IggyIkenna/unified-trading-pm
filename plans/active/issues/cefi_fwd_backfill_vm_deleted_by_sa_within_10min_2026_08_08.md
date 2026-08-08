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
      (`google-cloud-sdk gcloud/569.0.0 ... agent-name/claude_code        command/gcloud.compute.instances.delete`),
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
      prefix=`raw_tick_data/by_date/     day={day:%Y-%m-%d}/pipeline_mode=batch_tardis/asset_group=cefi/venue={venue}/instrument_type=perpetual/     data_type=derivative_ticker/`.
      Use the `probe_cefi_perp_funding_raw_coverage.py` script for the final gate only. **Frontier at 2026-08-09T13:45Z
      (25h elapsed)**: all 6 venues complete through 2026-06-22; 06-23 in-progress (OKX-SWAP at 146/~340). **Updated
      frontier (~28h elapsed)**: 06-23 complete (OKX-SWAP 346); 06-24 in-progress (BIN=563, BYB=484, OKX=224/~344,
      KRA=252, BITGET=493, BITFINEX=58 — OKX-SWAP actively writing). **Confirmed Tardis archive gaps**: 06-19 and 06-20
      are 0 across ALL venues (VM has now processed through 06-23 and returned full coverage at 06-21 → 06-19/06-20 are
      genuine Tardis data absences, NOT a processing order artifact). Also 06-18: OKX-SWAP=0 and KRAKEN=0 only (other 4
      venues have data) — Tardis gap for those two venues on that day. Pre-existing remnants on 06-25 (BYBIT/OKX/KRAKEN
      ~3 objects each) are NOT from this VM.
- [ ] [CODE] P2. **Fix MTDS pre-flight code bug**: `venue_fetch.py:526-552` missing positive `if has_instruments:`
      branch that populates `venue_instrument_ids` from IS data. When IS data IS available, `venue_instrument_ids` stays
      None → empty expected_atoms → false "fully covered" for any venue+date with EXPECTED_* atoms. Fix: fetch IS
      instrument IDs when `has_instruments=True` (or treat `_expected_atoms = {}` as "no filter" in
      `_apply_preflight_skip_filter` to disable skip when no instrument filter is active).
- [x] ✅ [INFRA] P1. **Harden the singleton-lock refusal against the confirmed agent-deletes-fresh-VM recurrence**
      (repo: deployment-service) — deployment-service@bc48b09b. Removed the raw, directly-executable
      `gcloud compute instances delete ... --quiet` line from the singleton-lock/collision refusal message in
      `lib/launcher_common.sh`'s `lc_singleton_check` AND every inline-duplicate copy of the same refusal block
      (`grep -rl "If confirmed stale:" scripts/vm/` found 62 files total — the shared function + 61 launcher scripts,
      including `launch-cefi-forward-poll.sh`), replacing the trailing "If confirmed stale: <raw delete command>" with a
      pointer to `infra.md` STEP 0.65's 3-signal staleness check ("construct the delete command by hand — this refusal
      intentionally does not print one to copy-paste"). Verified via `bash -n` on all 62 changed files + full
      `quality-gates.sh` green (sentinel bc48b09b) + quickmerge landed on live-defi-rollout, ancestry-verified.

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
