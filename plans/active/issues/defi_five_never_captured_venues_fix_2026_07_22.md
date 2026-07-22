---
doc_type: issue
title: >-
  Five DeFi venues (FLASHBOTS/ACROSS/STARGATE/FRAX/ALCHEMY) have never had real production capture -- root-caused, fix
  designed + partially implemented, IN FLIGHT via a background workflow
summary: >-
  Follow-up to defi_venue_phase_live_definition_contradiction_2026_07_22.md's zero-row investigation. Of the 11 DeFi
  venues originally surveyed, 5 turned out to have real, distinct, currently-open defects rather than "just needs the
  OR-registry fix": FLASHBOTS/ACROSS/STARGATE were NEVER scheduled (no Cloud Run Job ever existed), FRAX's only data is
  a dead one-time migration artifact from 2026-07-19, and ALCHEMY's real scheduled cron crash-loops (OOM/timeout) due to
  a manifest freshness-cache wait exceeding the job's own timeout, plus a separate venue-mislabel bug. A
  design->implement->adversarial-verify->ship workflow is IN FLIGHT (see "Resume mechanism" below) fixing all of this;
  this doc exists so a session with zero memory of this one can check on or resume it without re-deriving anything.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, deployment-service]
scope: [engineer]
tags: [defi, scheduling, crash-loop, venue-mislabel, terraform, in-flight]
related:
  [defi_venue_phase_live_definition_contradiction_2026_07_22.md, distinct_values_noncanonical_audit_2026_07_20.md]
created: "2026-07-22"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: data
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
source: operator ("ok for these 5 lets fix them all then"), 2026-07-22
---

## Resume mechanism (READ THIS FIRST if picking this up cold)

A Workflow is (or was, as of this doc's last edit) actively running to implement this fix. Workflow runs persist
server-side independent of any chat session — check on it before re-deriving anything:

- **Script path**:
  `/Users/ikennaigboaka/.claude/projects/-Users-ikennaigboaka-Code-unified-trading-system-repos--tabs-3/b9601b29-97ab-4add-b37b-9fa11a514b3b/workflows/scripts/defi-five-broken-venues-full-fix-wf_98feeeca-f6c.js`
- **Run ID**: `wf_98feeeca-f6c` (most recent resume task ID was `wbfr2tjg6`)
- **To check status / resume**: `Workflow({scriptPath: "<path above>", resumeFromRunId: "wf_98feeeca-f6c"})` --
  completed phases replay from cache instantly; only incomplete/failed phases re-run.
- **Known failure mode hit twice already**: transient `API Error: Unable to connect to API (ENOTFOUND)` / "Response
  stalled mid-stream" on individual agent calls -- NOT a logic failure, just resume it again.
- **Phases**: Research (4 parallel, DONE) -> Design (DONE) -> Implement (3 parallel: gas-fees fix, schema-contract test
  coverage, Terraform scheduling) -> AdversarialVerify -> Ship. As of this doc's last edit, Implement had produced real
  uncommitted diffs in 3 repos (see "Current uncommitted state" below) and AdversarialVerify/Ship had not yet produced a
  final result.
- **If the workflow is confirmed dead/abandoned and nothing resumes it**: everything needed to redo this by hand is in
  this doc (exact diffs, exact root causes, exact file:line citations) -- you do not need to re-investigate, just
  re-implement from the findings below.

## Background

`distinct_values_noncanonical_audit_2026_07_20.md`'s DeFi-venue survey originally claimed 14/15 protocols had "working,
production-proven capture." A follow-up investigation (this session, 2026-07-22) found that claim did not hold up
against the live production manifest for 11 of them. 6 were accuracy-verified-but-manual-only and already shipped
(`unified-api-contracts@91b6f094` -- see `defi_venue_phase_live_definition_contradiction_2026_07_22.md`). **The other 5
are the subject of this doc** -- each has a real, distinct, currently-open defect, not a documentation problem.

## Per-venue root cause (all independently verified against real GCS/Cloud Run/Cloud Scheduler state)

### FLASHBOTS (mev_events) -- NEVER SCHEDULED

- Zero GCS objects, ever, anywhere (exhaustive scan of all partitions/pipeline_modes).
- `--operation collect-mev-events` exists in code (`market-tick-data-service/market_tick_data_service/cli/main.py:572`,
  `cli/handlers/mev_events_handler.py`) but **no Cloud Run Job has ever invoked it**.
- **Correction to the original task premise**: the `(defi, spot_asset, mev_events)` SchemaContract was assumed missing
  -- it is NOT. Verified 3 ways (static read of
  `unified-api-contracts/unified_api_contracts/internal/schemas/_defi_v2_contracts.py:197-213`, a live
  `lookup_contract()` call, and an end-to-end `write_defi_rows()` call producing a real path with zero error). This
  entry has existed since commit `13db4a9c`. Nothing to fix here.
- **Fix**: add one entry to the existing `for_each`-driven map in
  `deployment-service/terraform/gcp/defi_collection_scheduler.tf` -- no new resource blocks, no new IAM, no new secret.
  See "Terraform diff" below.
- **Non-blocking follow-up found, not folded into this fix**: the handler only pages ~100 newest relay rows/day
  (hard-exits after first page) -- under-covers any day with >100 payloads. File separately.

### ACROSS + STARGATE (bridge_events) -- NEVER SCHEDULED

- Zero GCS objects, ever, for either venue.
- **Correction to the original task premise**: assumed to need a `the-graph-api-key` secret and a missing SchemaContract
  -- both stale. `bridge_events_handler.py` was rewritten TODAY (2026-07-22, commits `a32dd58c`/`4c21c7f6`) to stop
  using The Graph entirely and read real on-chain `eth_getLogs` via Alchemy instead. It calls `alchemy-api-key` (not
  TheGraph), which is already provisioned (`deployment-service/terraform/gcp/main.tf:73`) and already reachable
  (`google_project_iam_member.unified_trading_secret_accessor`, `main.tf:610-613`, project-wide `secretAccessor`, no new
  IAM needed). The SchemaContract `(defi, spot_asset, bridge_events)` already exists (`_defi_v2_contracts.py:155-173`,
  registered at `:466`), column-for-column matching the handler's real row shape.
- **Fix**: one more entry in the same Terraform map. See "Terraform diff" below.
- **Cost note**: cheap -- ~1 `eth_getLogs` call/day for ACROSS, ~11 for STARGATE (one per pool), plus ~2 dozen
  block-resolution calls. A daily cron is the right shape; genesis is 2021-11-11 (ACROSS) / 2022-03-17 (STARGATE) so a
  **historical backfill must NOT reuse this daily-cron entry** -- that needs its own bounded, explicit
  `--start-date`/`--end-date` invocation, filed separately.
- **Flag, not yet resolved**: `defi_collection_scheduler.tf`'s own header comment says the whole 11-job stagger must
  finish by 02:25 UTC for `features-onchain` T+1 freshness -- `solana-defi` alone (02:05 start, 1500s timeout) can
  already finish ~02:30, i.e. the deadline looks pre-existing-violated before this change. Notify whoever owns
  `t1_batch_scheduler.tf:124-128`; do not silently make it worse without notice.

### FRAX (vault_share_price) -- NEVER SCHEDULED, "already working" claim was FALSE

- The only data that exists (977 days, `day=2026-04-08`..`2026-06-21`) is a **one-time historical migration artifact**
  -- every object has `creation_time=2026-07-19`, one file is literally named
  `_migrated_FRAX_ETHEREUM_1782043200.parquet`. Nothing since 2026-06-21, including all of July.
- `--operation collect-vault-share-price` (`cli/main.py:576`, `vault_share_price_handler.py`) has **no Cloud Run Job**,
  ever.
- **Fix**: one more Terraform map entry. See "Terraform diff" below.
- **Cost note**: trivially cheap -- 1 chain, 1 block-resolution call, 8 `eth_call`s (one per vault), 5 tiny parquet
  writes/day. Lighter than the already-scheduled `lst-rates` job.
- **This same handler also covers MAKER and MORPHOVAULTS** -- see next section, this is not a FRAX-only fix.

### MORPHOVAULTS (vault_share_price, shares FRAX's handler) -- real, currently-live bad data point found

This was NOT one of the 5 venues in the operator's "fix these 5" instruction (MORPHOVAULTS was already reported "fixed"
earlier in the session), but the investigation into FRAX's handler surfaced a real problem with it that must not be
silently dropped:

- MORPHOVAULTS' `GTUSDCP.parquet` (day=2026-06-21, part of the same 2026-07-19 migration-artifact batch as FRAX/MAKER)
  contains `vault_address=0xc080f56504e0278828A403269DB945F6c6D6E014` (the OLD, WRONG address) and
  `share_price=1.06341e+12` -- garbage, exactly the bug that `market-tick-data-service@6bf6012a` (earlier today) fixed
  **in code only**.
- That fix corrected the in-code address registry but **never re-ran capture** -- the live production parquet for
  MORPHOVAULTS still holds the pre-fix garbage value today. Checked `day=2026-07-22` for MORPHOVAULTS/FRAX/MAKER under
  both pipeline_modes -- zero objects, confirming nothing has captured since.
- **This is a real, currently-live wrong-data-in-production issue**, distinct from "needs scheduling." Scheduling
  `collect-vault-share-price` (the FRAX fix above) stops this from recurring going forward but does **NOT**
  retroactively correct the existing bad row.
- **Deliberately not fixed in this pass**: correcting/deleting that one historical GCS object is a prod-bucket data
  mutation -- per this workspace's GCS delete/mutate-safety protocol, that's operator-gated, not something to fold
  silently into a scheduling fix.
- `- [ ] [OPERATOR] P2. Correct or delete MORPHOVAULTS' `GTUSDCP.parquet`for`day=2026-06-21`(garbage`share_price=1.06341e+12`, wrong vault address) once `collect-vault-share-price` is confirmed running cleanly -- either delete it (a gap is more honest than garbage) or re-run the handler for that specific historical day to overwrite it with a correct value. Human-gated per prod-bucket mutation rules.`

### ALCHEMY (gas_fees) -- STILL BROKEN, root cause confirmed (not a guess)

**This is the one venue with an already-existing, already-scheduled cron (`uts-prod-mtds-collect-gas-fees`, daily 00:00
UTC) that is actively crash-looping**, and it has a separate real bug on top.

**Crash-loop root cause** (log-evidence-backed across 4 sub-attempts, 2 incidents):

- 2026-07-21: hung at ~0% CPU for the full 30-min window, hit the Cloud Run task timeout (1800s), wrote zero records.
- 2026-07-22: OOM-killed twice in a row (RSS jumped from ~535MiB to ~2039MiB in one 30s sample, then killed), never
  logged a single per-chain fetch line.
- **In all 4 attempts, the decisive first log line the 12-chain `eth_feeHistory` sweep would emit never appears** -- the
  job dies before touching chain #1. The already-parallelized `GasFeeClient.get_historical_fees` (added for an earlier,
  unrelated 2026-06-19 incident) is a red herring -- it never gets a chance to run.
- **The actual failure is inside `GasFeeHandler._setup_process_infra()` -> `ManifestFreshnessCache.bulk_load()`**,
  called once at startup, before the chain loop. Traced through `unified-trading-library`: when the consolidated
  manifest blob is stale, the slow path polls (`time.sleep(5.0)`) waiting for the DeFi consolidator's in-flight lock,
  bounded by `AG_CONSOLIDATOR_INFLIGHT_HORIZON_SEC["defi"] = 4200` seconds
  (`unified_trading_library/manifest_writer/_staleness_budget.py:41`) -- **larger than this job's own Cloud Run timeout
  of 1800s** (`deployment-service/terraform/gcp/defi_collection_scheduler.tf`, `"gas-fees"` entry). Whenever the DeFi
  consolidator is legitimately mid-cycle when `gas-fees` fires at 00:00 UTC (plausible -- 11 DeFi collect-* jobs are
  staggered 00:00-02:05 UTC, all writing per-VM shards into the same bucket), `gas-fees` either times out mid-wait, or
  the wait resolves and decoding the just-caught-up (large) consolidated index blows the 2Gi memory ceiling.
- **This exposure is not unique to gas-fees** -- all 11 DeFi collect-* jobs have timeouts (1200-2400s) shorter than the
  4200s DeFi in-flight horizon; gas-fees is just first in the stagger, most likely to race the tail of a prior
  consolidator cycle.

**Minimal fix** (confined to `gas_fee_handler.py`, does not touch the shared UTL manifest reader used by 11+ other
jobs): bound the freshness-cache warm-up to 90s via a `ThreadPoolExecutor` timeout; on timeout, proceed with freshness
skip-checks disabled (fail-open, never blocks) rather than waiting further. Thread a `freshness_ready: bool` through
`_setup_process_infra()` -> `process()` -> every `is_now_skip_worthy(...)` call site (EVM/Solana/BTC).

**Separate venue-naming bug, same file** -- `write_defi_rows(records, venue=chain_name, ...)` is called instead of
`venue=_GAS_FEE_VENUE` ("ALCHEMY") at 4 call sites (`_write_defi_date_rows`/EVM, `_write_solana_historical_shard`,
`_write_solana_live_shard`, `_write_btc_shard`). GCS objects land under `venue=<CHAIN>` while the manifest recorder
claims `venue="ALCHEMY"` -- a real GCS-vs-manifest identity mismatch. `gas_fee_handler.py` is the **only** handler in
the whole directory that does this (every other multi-chain DeFi venue passes `venue=<protocol>` + `chain=<chain>` as
independent fields, confirmed by grepping every `write_defi_rows(` call site). Fix: rename to `_GAS_FEE_VENUE` at all 4
sites, `chain=` untouched (chain granularity already preserved independently -- nothing to invent). Verified safe
against schema resolution: `DEFI_SPOT_ASSET_GAS_FEES` is a venue-agnostic registry key (no `VENUE_CONTRACT_OVERRIDES`
entry for ALCHEMY/SOLANA/BITCOIN or any chain name), so the same contract resolves before and after the rename.

**Sequencing**: crash-loop fix ships and gets manually verified FIRST (it's an active production break, higher urgency
than 3 never-scheduled jobs); venue-naming rename ships as a separate commit AFTER the crash-loop fix is confirmed
non-crashing (don't stack an unverified control-flow change and a path-changing rename in one deploy). The rename
changes GCS paths going forward -- pre-existing historical objects under the wrong `venue=<CHAINNAME>` prefix won't
retroactively move; that's a separate, operator-gated path-migration concern, filed not folded in.

## Terraform diff (deployment-service/terraform/gcp/defi_collection_scheduler.tf)

Three new entries added to the existing `local.defi_collect_operations` map (no new resource blocks -- the `for_each`
module + scheduler cron both auto-derive from new map keys):

```hcl
    "vault-share-price" = {
      schedule    = "10 1 * * *"
      cpu = "1"; memory = "2Gi"; timeout = 900
      description = "DeFi collect-vault-share-price -- ERC-4626 convertToAssets snapshots (Yearn V3, Ethena, Maker sDAI, Frax sFRAX, Morpho MetaMorpho USDC)."
    }
    "mev-events" = {
      schedule    = "10 2 * * *"
      cpu = "1"; memory = "2Gi"; timeout = 900
      description = "DeFi collect-mev-events -- MEV-Boost relay stats via Flashbots relay API."
    }
    "bridge-events" = {
      schedule    = "15 2 * * *"
      cpu = "1"; memory = "2Gi"; timeout = 1200
      description = "DeFi collect-bridge-events -- ACROSS + STARGATE transfer events via Alchemy eth_getLogs."
    }
```

(`bridge-events` at `15 2 * * *`, not `10 2 * * *` -- mev_events and bridge_events were researched independently and
both proposed the same minute; caught and fixed during design synthesis, before either shipped.)

Verified via `ENV=prod ./tofu.sh plan` (real prod backend, real prod project) diffed against a `git stash`-isolated
baseline: **exactly 6 new resources** (3 `google_cloud_run_v2_job` + 3 `google_cloud_scheduler_job.defi_collect_cron`),
nothing existing modified or destroyed. The baseline plan's own "67 to change" / "9 to add" are confirmed pre-existing
drift from unrelated in-flight Terraform (other agents' concurrent work in this same repo this session), not caused by
this diff.

## Rollout posture -- manual-first-run required for every piece, per this workspace's no-fire-and-forget rule

None of these 4 fixes (gas-fees code fix, mev-events, bridge-events, vault-share-price scheduling) are
"already-proven-safe cadence" -- each needs
`gcloud run jobs execute <job> --region asia-northeast1 --project central-element-323112` run manually immediately after
deploy/apply, watched to a terminal state, with a real manifest row confirmed (not just "job exited 0") before the
Scheduler cron is trusted to run it unattended:

| Job               | Progress-signal proof                                                         | Manifest proof                                                                                                                                                                                                                                        |
| ----------------- | ----------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| gas-fees (fixed)  | the previously-never-seen "fetching chain X" log line appears within ~90-120s | `record_captured` for all 12 chains, not `attempted_failed`                                                                                                                                                                                           |
| mev-events        | Flashbots relay GET fetch log                                                 | `record_captured`, venue=FLASHBOTS                                                                                                                                                                                                                    |
| bridge-events     | per-protocol log/pool-fetch lines (1 ACROSS + 11 STARGATE calls)              | `record_captured`, venue=ACROSS and venue=STARGATE                                                                                                                                                                                                    |
| vault-share-price | per-vault `convertToAssets` log, 8 vaults                                     | `record_captured` for YEARN_V3/ETHENA/MAKER/FRAX/MORPHO_VAULTS -- **and no `SchemaContractNotFoundError`** (this contract was never independently live-verified the way mev_events/bridge_events were, treat as unconfirmed until this run proves it) |

Re-verify each at T+10min (still terminal, no hung retry, no unexpected re-fire) before leaving the Scheduler cron
unattended.

## Current uncommitted state (as of this doc's last edit -- check freshness before trusting)

- `market-tick-data-service`: `market_tick_data_service/cli/handlers/gas_fee_handler.py`, `_gas_fee_helpers.py`,
  `tests/unit/test_gas_fee_handler.py` -- uncommitted, contains the crash-loop fix (bounded warmup). Venue-naming rename
  may or may not be in this same diff depending on how far Implement got -- check the actual diff, don't assume.
- `deployment-service`: `terraform/gcp/defi_collection_scheduler.tf` -- uncommitted, the 3-entry diff above,
  `tofu plan`-verified ADD-only.
- `unified-api-contracts`: `tests/internal/unit/test_schema_contracts.py` -- uncommitted, +98 lines of regression-test
  coverage locking in that the mev_events/bridge_events contracts already existed and resolve correctly (no
  registry/contract code change, since none was needed).
- **None of this has been committed or pushed as of this doc's writing** -- it was mid-flight in an actively-running
  background workflow when this pre-compact pass ran. Durability for this content currently rests on this doc + the
  workflow's own persistence, not on git.

## Deferred work after 2026-07-22

| Item                                                                                                                | State                                                       | Blocked-on                                                                                                                                                      |
| ------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Ship gas-fees crash-loop fix + manually verify                                                                      | Implemented, uncommitted, not yet verified/shipped          | The in-flight workflow's AdversarialVerify + Ship phases (resume via mechanism above)                                                                           |
| Ship venue-naming rename (separate commit, after crash-loop fix confirmed healthy)                                  | Designed, may be partially implemented                      | Same workflow; sequenced after the crash-loop fix ships clean                                                                                                   |
| Apply Terraform for mev-events/bridge-events/vault-share-price + manual-trigger-verify each                         | Diff ready, `tofu plan` ADD-only confirmed, not yet applied | Same workflow's Ship phase                                                                                                                                      |
| Ship schema-contract regression tests (no registry change needed)                                                   | Implemented, uncommitted                                    | Same workflow's Ship phase (low-risk, could ship independently if the workflow stalls again)                                                                    |
| File the mev_events >100-payload/day pagination gap                                                                 | Not filed                                                   | Nobody -- pick up any time, independent of the rest                                                                                                             |
| File the 02:25 UTC T+1 features-onchain freshness deadline concern                                                  | Not filed                                                   | Notify `t1_batch_scheduler.tf`'s owner                                                                                                                          |
| File the gas-fees historical `venue=<CHAINNAME>` path-migration (pre-existing objects won't move)                   | Not filed                                                   | Operator decision on whether/how to migrate old paths                                                                                                           |
| Correct/delete MORPHOVAULTS' `day=2026-06-21` garbage `GTUSDCP.parquet`                                             | Not started                                                 | **Operator-owned** -- prod-bucket mutation, do after vault-share-price is confirmed running                                                                     |
| 90-day local backfill for the 6 already-shipped accuracy-verified venues (ANKR/STADER/STAKEWISE/SWELL/MANTLE/MAKER) | Designed (no VM needed, ~2,340 RPC calls), not run          | Should happen after the gas-fees crash-loop fix ships, since it's the same underlying manifest-freshness-wait bug class affecting the shared LST-rates cron too |

**Recommended next action for whoever picks this up**: resume the workflow first (cheap, cached phases replay
instantly). If it's genuinely dead, the fastest path is committing the 3 already-implemented, already-designed diffs
directly (gas-fees fix, Terraform, schema-contract tests) after re-running each repo's `quality-gates.sh` fresh, then
doing the manual-trigger verification table above by hand -- everything needed to do that without re-investigating is in
this doc.

## Lessons for future sessions

- **"Already working" claims from an earlier survey need re-verification against the live manifest, not just a
  successful API call.** The original 14/15-protocols-working claim conflated "the adapter can successfully call the
  API" with "the pipeline is capturing this venue" -- these are different claims, and the gap between them is exactly
  where 5 real, distinct production defects were hiding.
- **A code fix to a wrong constant (MORPHOVAULTS' vault address, `mtds@6bf6012a`) does not retroactively fix
  already-written bad data.** "Fixed the code" and "corrected the data" are two different, separately-verifiable claims
  -- check both.
- **A crash-looping job's real error can be entirely upstream of the code you'd naturally suspect.** The 12-chain
  `eth_feeHistory` sweep (already fixed once for a different incident) was a complete red herring -- the actual failure
  was in shared startup infra (`ManifestFreshnessCache.bulk_load()`) that 11+ other jobs also depend on, discovered only
  by reading full logs for the decisive ABSENCE of an expected log line across all 4 failed attempts, not by reading the
  handler's business logic first.
