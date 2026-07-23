---
doc_type: issue
title: >-
  RETRACTED premise: STADER/STAKEWISE/SWELL/MANTLE already have full, working lst_rates_handler.py registry entries
  since 2026-04-10 (my earlier grep searched the wrong strings); real remaining gap is a single day (2026-07-17,
  whole-execution crash) + a rare late-stage OOM/timeout tail + an unresolved MAKER duplicate-axis question
summary: >-
  CORRECTED 2026-07-22 (same day, later pass) after direct re-verification against real prod GCS + `gcloud run jobs
  executions list` + `gcloud logging read`. The original claim below ("zero registry entries for these 4 venues", "cron
  crash-loops", "wrong-date-targeting bug") was a `grep-then-conclude` mistake: I grepped `lst_rates_handler.py` for the
  venue display names (`STADER|STAKEWISE|SWELL|MANTLE`), but the handler's `_EVM_LST_ABI_METADATA` dict keys on the
  TOKEN SYMBOL (`ETHx`/`osETH`/`swETH`/`mETH`), not the venue name -- a real grep-then-READ violation (CLAUDE.md `Agent
  behavior` rule). `git blame` shows this handler code (with etherscan-derived contract addresses in
  `_instruments_metadata.py`, correct decimals, a documented selector-typo fix for mETH) shipped 2026-04-10/04-29/06-16
  -- months before this session. A day-by-day GCS scan of `day=2026-04-10` through `day=2026-07-21` (103 days) found
  real, sane captured data (exchange rates 1.09-1.13, consistent LST premium, real block numbers) for all 4 tokens on
  **102 of 103 days** -- the single miss is `day=2026-07-17`, and it is a WHOLE-EXECUTION gap (LIDO/ANKR/ETHERFI/ETHENA
  are ALSO missing that day), not a per-venue bug -- matching `gcloud run jobs executions list` execution `xx5p2` (ran
  2026-07-18, targeted yesterday=2026-07-17, `failedCount=1`, "container exited with an error" in <1m, i.e. crashed
  before any writes). Separately, `uts-prod-mtds-collect-lst-rates` does have a REAL rare failure mode -- `gcloud
  logging read` on executions `xrhf8` (2026-07-21, OOM) and `4f99t` (2026-07-22, 1200s timeout) shows both crashes hit
  LATE (~19-20 min into the run, RSS spiking 535MiB->1493MiB), and both days' EVM LST rows (incl. our 4 target tokens)
  were ALREADY WRITTEN to GCS by the time the crash hit -- the failure is almost certainly in a later stage (Solana
  3-tier fetch or the 19 extended EVM/LRT configs), not the core 13-token EVM loop, so it costs job-health signal +
  probably Solana coverage, not EVM LST data. The "wrong-date-targeting" claim is also WRONG as stated: the log line
  "Batch mode: no explicit dates provided -- defaulting to yesterday=<D>" is the CORRECT T+1 batch fallback (same
  BatchPayload.date pattern `vault_share_price_handler.py` uses) -- the handler already accepts an explicit historical
  date when one is passed, exactly like the GTUSDCP re-run did. Real remaining scope, corrected: (1) a single-day
  backfill for `day=2026-07-17` (all LST venues, not just these 4), (2) optionally root-cause the rare late-stage
  OOM/timeout (Solana fetch is the leading suspect) for job-health + Solana coverage, (3) the MAKER duplicate-axis
  question is CONFIRMED real and unresolved -- `vault_share_price_handler.py` has its own sDAI/MAKER ERC-4626
  `convertToAssets` entry (protocol="MAKER") AND `lst_rates_handler.py` has a separate sDAI entry (`_token_to_protocol`
  -> "maker") -- same on-chain rate, captured twice under two different `data_type` labels (`vault_share_price` vs
  `lst_rates`); needs an explicit keep-both-as-cross-check vs consolidate decision, not a unilateral delete. NOT
  investigated / explicitly out of scope here: whether the operator wants a full since-real-launch historical backfill
  (Stader ETHx 2023-07-10 / StakeWise osETH 2023-11-28 / Swell swETH 2023-04-25 / Mantle mETH 2023-12-04/2024-01-26)
  predating this handler's 2026-04-10 first-capture date -- that is a ~2.5-3 year, much bigger, separate decision that
  should not be silently assumed in or out of scope.
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, deployment-service, unified-api-contracts]
scope: [engineer]
tags:
  [
    defi,
    lst-rates,
    stader,
    stakewise,
    swell,
    mantle,
    ankr,
    maker,
    cron-crash-loop,
    backfill,
    manifest-freshness,
    grep-then-conclude,
    false-premise-correction,
  ]
related:
  - defi_five_never_captured_venues_fix_2026_07_22.md
  - defi_venue_phase_live_definition_contradiction_2026_07_22.md
  - vault_share_price_handler_capture_gap_since_2026_06_22.md
  - plans/active/lst_rate_honest_coverage_2026_07_21.md
created: "2026-07-22"
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.15
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
resolved_by: this-doc-self-corrected-2026-07-22
locked_by:
source: [operator-approved-2026-07-22-chat, self-correction-2026-07-22-same-day]
---

# RETRACTED: original "3 ordered steps" below

Everything under "What's actually needed" and its "Deferred work" table (as originally filed) assumed steps 1 and most
of step 2 were unstarted greenfield work. Direct re-verification (this same day, later pass) shows step 1 was already
done in April 2026 and step 2's premises don't hold as stated. See "What I found on re-verification" below for the real
picture and the real remaining work. The original text is struck through, not deleted, so the mistake and its shape stay
visible (this is exactly the kind of grep-then-conclude error `codex/12-agent-workflow/` warns about, and future readers
should be able to see how it happened).

## 1. ~~Implement real `lst_rates_handler.py` registry entries for STADER, STAKEWISE, SWELL, MANTLE~~ -- ALREADY DONE, since 2026-04-10

~~Not yet started.~~ **False.** `_EVM_LST_ABI_METADATA` (`lst_rates_handler.py:119-151`) has had full `mETH`/`swETH`/
`ETHx`/`osETH` entries -- correct selectors, decimals, a documented selector-typo fix for mETH -- since commits
`f543e73aa` (2026-04-10) and `7208f46d6` (2026-04-29). `_EVM_LST_STATIC_CONTRACT_ADDRESSES`
(`_instruments_metadata.py:108-118`) has had etherscan-derived addresses for all 4 since `9ee6cab08` (2026-06-16).
`LST_TOKEN_GENESIS` (`unified_api_contracts/registry/chain_env.py`) has real launch dates for all 4 protocols. A 103-day
GCS scan (`day=2026-04-10` through `day=2026-07-21`) found real, sane exchange-rate data (1.09-1.13 range, real block
numbers matching the day's other LST venues) for all 4 tokens on 102 of 103 days. **My original claim of "zero registry
entries, confirmed via direct grep" was a false negative**: I grepped for the venue display names
(`STADER|STAKEWISE|SWELL|MANTLE`), but the dict keys on the token symbol (`ETHx`/`osETH`/`swETH`/`mETH`) and
`_token_to_protocol` maps them to lowercase protocol names (`stader`/`stakewise`/`swell`/`mantle`) -- neither form
matches an uppercase venue-name grep. No new handler code, addresses, or tests are needed for these 4 venues.

## 2. ~~Fix `uts-prod-mtds-collect-lst-rates`'s own crash-loop + wrong-date bug~~ -- partially real, much smaller than described

- **"Wrong-date targeting" -- FALSE.** The log line
  `Batch mode: no explicit dates provided -- defaulting to yesterday=<D>` is the CORRECT T+1 batch fallback (same
  `BatchPayload.date`-first pattern `vault_share_price_handler.py` uses, confirmed in `process()`: it reads
  `payload.date` before falling back to `datetime.now(UTC)`). A historical re-run with an explicit date already works
  exactly like the GTUSDCP fix did. Nothing to fix here.
- **"Crash-loop" -- real, but rare and mostly non-lossy for these 4 venues.** `gcloud run jobs executions list`
  (30-execution window) shows: a solid failure streak `2026-05-25` through `2026-06-08` (every day, exit code 1, fast
  crash before writes -- this predates the 2026-04-10 handler code only by six weeks, so it doesn't contradict anything
  above), then a ~39-day gap with ZERO executions (`2026-06-08` to `2026-07-17` -- unexplained, worth a follow-up but
  not urgent), then a mixed recent run: `07-17` failed fast (exit 1, the one real GCS gap, see below), `07-18` failed
  fast (exit 1), `07-19`/`07-20` succeeded clean, `07-21` OOM'd, `07-22` hit the 1200s timeout. `gcloud logging read` on
  `xrhf8` (07-21 OOM) and `4f99t` (07-22 timeout) shows both crashes hit LATE -- ~19-20 min into a run, RSS spiking
  535MiB->1493MiB right before the kill -- and the day's core EVM LST rows (all 13 tokens, incl. our 4) were **already
  written to GCS** by the time the crash hit. The failure is almost certainly downstream of the core EVM loop -- the
  Solana 3-tier fetch or one of the 19 extended EVM/LRT configs is the leading suspect, not yet root-caused. Fixing it
  protects job-health signal and probably Solana coverage; it is NOT currently costing EVM LST data for
  STADER/STAKEWISE/SWELL/MANTLE/ANKR/etc.

## 3. ~~Run the 90+ day backfill~~ -- real gap is ONE day, not 90+

A 103-day day-by-day GCS scan (`2026-04-10` .. `2026-07-21`) found exactly one missing day: **`day=2026-07-17`**, and it
is a WHOLE-EXECUTION gap -- LIDO/ANKR/ETHERFI/ETHENA are also missing that day, matching execution `xx5p2` (ran 07-18,
targeted yesterday=07-17, exit code 1, completed in <1m -- crashed before any per-venue writes, not a per-venue defect).
Real backfill scope: one day, all LST venues, once someone either root-causes the fast exit-1 crash or just confirms a
plain re-run succeeds (the same job has run clean on adjacent days). Separately: whether the operator wants a full
since-real-launch backfill (2023 launch dates through the 2026-04-10 first-capture date, ~2.5-3 years) is a much bigger,
distinct, NOT-yet-decided question -- do not fold it into "the 90-day backfill" without an explicit scoping decision.

# MAKER duplicate-axis question -- CONFIRMED real, still unresolved

`vault_share_price_handler.py` has its own sDAI/MAKER entry (protocol="MAKER", ERC-4626 `convertToAssets`,
`vault_share_price_handler.py` MakerDAO sDAI section) AND `lst_rates_handler.py` has a separate sDAI entry
(`_EVM_LST_ABI_METADATA["sDAI"]`, `_token_to_protocol` -> `"maker"`) -- the identical on-chain rate, captured twice,
under two different `data_type` labels (`vault_share_price` vs `lst_rates`). This is a real design question (keep both
as an intentional cross-check vs. consolidate to one axis and stop paying for the duplicate RPC call + storage) that
needs an explicit decision, not a unilateral delete of either working path.

# Why this doc exists separately from `lst_rate_honest_coverage_2026_07_21.md`

That plan is actively being edited by a concurrent session/agent this same evening (confirmed live, large ongoing Phase
0-6 effort) and is scoped to a broader LST honest-coverage initiative already covering
lido/rocketpool/coinbase/ankr/idle/marinade/sanctum. This doc is scoped narrowly to the 4-6 venues from the
five-venues-fix thread specifically, to avoid editing a file another live session owns right now. Whoever picks this up
should check that plan's current state first (`plans/active/lst_rate_honest_coverage_2026_07_21.md`'s own `RESUME POINT`
section) in case the two efforts have since merged or one has superseded the other.

# Deferred work after 2026-07-22 (corrected)

| Item                                                              | State                                                                   | Blocked on                                                                                        |
| ----------------------------------------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| STADER/STAKEWISE/SWELL/MANTLE handler registry entries            | Done (2026-04-10, pre-dates this session)                               | Nobody -- no action needed                                                                        |
| `uts-prod-mtds-collect-lst-rates` wrong-date-targeting            | Not a bug                                                               | Nobody -- fallback-to-yesterday is correct T+1 behavior                                           |
| Single-day backfill, `day=2026-07-17`, all LST venues             | Done 2026-07-23, content-verified                                       | Nobody                                                                                            |
| MAKER sDAI duplicate consolidation                                | Done 2026-07-23 -- market-tick-data-service@28972ccc                    | Nobody                                                                                            |
| sUSDe/ETHENA duplicate consolidation                              | Done 2026-07-23 -- same commit as MAKER                                 | Nobody                                                                                            |
| 39-day execution gap `2026-06-08`..`2026-07-16` root cause        | Done 2026-07-23 -- deliberate operator PauseJob, not a bug              | Nobody -- see Resolution below                                                                    |
| Full since-real-launch (2023->2026-04-09) historical backfill     | Already done -- verified, not new work needed                           | Nobody -- see Resolution below                                                                    |
| Root-cause the rare late-stage OOM/timeout (Solana fetch suspect) | Investigated further, real mechanism found + quantified, NOT code-fixed | Filed as its own cross-cutting issue -- `defi_manifest_per_vm_shard_fallback_bloat_2026_07_23.md` |

**Recommended next item**: the `day=2026-07-17` single-day re-run (cheapest, closes the one real gap), then the MAKER
decision (needs operator input), then the OOM/timeout root-cause if the operator wants Solana coverage hardened. The
original "4 new venue implementations" item is gone -- there was never a real gap there.

# Resolution (2026-07-23, same session, later pass)

Operator picked (via chat): do the single-day backfill + root-cause the rare crash, and consolidate the MAKER duplicate
(rather than keep both).

**Single-day backfill -- DONE, content-verified.** Ran
`market-tick-data-service --operation collect-lst-rates --mode batch --start-date 2026-07-17 --end-date 2026-07-17 --force`
against real prod GCP. Completed clean, all 24 venue/chain groups written (lido, rocketpool, coinbase, ethena, maker,
mantle, swell, stader, stakewise, ankr, etherfi, puffer, binance x2 chains, kelpdao, renzo, yearn_v3 x4, beefy x3, idle
x3, pendle x5, jito, marinade, blazestake, sanctum -- 4 Solana rows too, so this was not an aiodns-resolver-drop run).
Content-verified by reading the objects back directly:
`gs://market-data-tick-defi-prd-central-element-323112/.../day=2026-07-17/.../venue={STADER,STAKEWISE,SWELL,MANTLE,LIDO,ANKR}/.../{ETHx,osETH,swETH,mETH,stETH,ankrETH}.parquet`
all present with sane rates at block 25552267. The 103-day window (`2026-04-10`..`2026-07-21`) is now 103/103 complete
for these venues.

**OOM/timeout root-cause -- investigated, NOT conclusively pinned; documenting rather than overclaiming a fix.** Read
`_lst_extended_rates.py` (19 configs, sequential single eth_calls, bounded retry/backoff) and `solana_lst_archival.py`
(4-tier fetch, all single bounded HTTP calls with 15s timeouts) end to end -- neither shows an unbounded loop or a large
in-memory payload that would explain a ~1GB RSS spike in a single 30s window. Found one related-but-different bug that
was ALREADY fixed same-day, before I started this investigation: `market-tick-data-service@533514c2` (2026-07-22 18:12
UTC) fixed an `aiodns`-missing resolver crash that was SILENTLY dropping the whole Solana LST leg (bare
`try/except -> return []`) -- not a memory/timeout issue, but real data loss disguised as a clean run. Separately found
a plausible-but-UNCONFIRMED mechanism: the DeFi manifest bucket's `_index/per_vm/` fallback path (triggered whenever the
consolidated index blob is >120s stale --
`unified_trading_library/manifest_writer/_read_index.py:_read_and_merge_per_vm_shards`) reads + pandas-merges EVERY
per-VM shard in that shared directory; as of this check it holds a 113.6MB shard from an unrelated
`canonical-migration-defi-rebuild-20260722-194751` VM. Loading + merging a shard that size at process bootstrap (before
any LST-specific code even runs) would plausibly explain a rapid multi-hundred-MB memory spike -- BUT that specific
113.6MB shard did not exist yet at the time of the `xrhf8`/`4f99t` failures I was investigating (it's timestamped hours
after both), so I cannot claim it explains those SPECIFIC historical crashes, only that the mechanism is real and
current-day risky. This is a SHARED framework path used by every DeFi handler, not something specific to
`lst_rates_handler.py` -- fixing it (bounding the per-VM merge, or making the consolidator run more reliably) is a
bigger, cross-cutting change affecting many handlers and deserves its own properly-scoped investigation with an actual
memory profile attached to a live run, not a guess-and-patch inside this narrow LST task. Left as an open, documented,
non-urgent follow-up (see table below) rather than shipping a speculative fix.

**MAKER duplicate consolidated -- shipped.** Removed the `sDAI` entry from `lst_rates_handler.py`'s
`_EVM_LST_ABI_METADATA` + its `_token_to_protocol` mapping (same contract `0x83F20F44975D03b1b09e64809B757c47f942BEeA`,
same `convertToAssets(1e18)` call as `vault_share_price_handler.py`'s own sDAI entry -- byte-for-byte duplicate RPC
read + storage). Updated `tests/unit/test_lst_rates_handler_coverage.py` (the old `test_sdai_maps_to_maker` ->
`test_sdai_no_longer_mapped_here`, plus a new `test_sdai_removed_duplicate_of_vault_share_price` mirroring the existing
`ezETH`-migrated-out test pattern) and the `--lst-tokens` CLI help text. `vault_share_price_handler.py` is now sDAI's
sole capture path (`data_type=vault_share_price`, the semantically correct home -- sDAI is an ERC-4626 vault, not a
staking token). QG-green, shipped `market-tick-data-service@28972ccc`.

**Related, NOT acted on (out of the approved scope)**: `sUSDe`/ETHENA has the exact same duplicate shape -- present in
BOTH `lst_rates_handler.py`'s `_EVM_LST_ABI_METADATA` AND `vault_share_price_handler.py`'s `_VAULTS`, same address
`0x9D39A5DE30e57443BfF2A8307A4256c8797A3497`. Only MAKER was in scope for this pass's operator decision; flagging sUSDe
here rather than silently also touching it.

**Still undecided, unchanged from the original correction**: whether the operator wants the full since-real-launch (2023
-> 2026-04-10) historical backfill scoped as its own effort. Not asked again this pass -- still open.

# Resolution, round 2 (2026-07-23, operator asked for all 4 remaining items "in full")

**sUSDe/ETHENA duplicate -- consolidated, same commit as MAKER.** Same exact shape (identical address
`0x9D39A5DE30e57443BfF2A8307A4256c8797A3497`, identical `convertToAssets(1e18)` call, present in both handlers). Removed
from `lst_rates_handler.py`'s `_EVM_LST_ABI_METADATA` + `_token_to_protocol`, added the mirroring
`test_susde_removed_duplicate_of_vault_share_price` / `test_susde_no_longer_mapped_here` tests, updated the
`--lst-tokens` CLI help text again. `vault_share_price_handler.py` is now sole owner. Shipped in the same commit as
MAKER, `market-tick-data-service@28972ccc`.

**39-day execution gap -- ROOT-CAUSED via Cloud Audit Logs, NOT a bug.** `gcloud logging read` on
`protoPayload.resourceName="...jobs/uts-prod-mtds-collect-lst-rates-cron"` (Admin Activity audit logs, much longer
retention than the Data Access logs the earlier `resource.type="cloud_scheduler_job"` query hit -- that query came back
empty for the whole window and was a dead end) shows: `PauseJob` by `ikenna@odum-research.com` at `2026-06-08T04:15:31Z`
(a few hours after that day's normal 01:00 run -- explains why the last pre-gap execution, `lqt54`, is exactly
2026-06-08), then a `ResumeJob`/`PauseJob` blip at `2026-07-16T07:29`/`07:36`, then the `ResumeJob` at
`2026-07-16T09:30` that stuck -- matching the first post-gap execution (`c8lxn`, ran 2026-07-17, targets
yesterday=2026-07-16, succeeded). This was a deliberate human pause of the Cloud Scheduler trigger, not a crash, not a
Terraform drift, not a code defect. No fix needed; documenting the mechanism (and that Admin Activity audit logs, not
Data Access logs, are the right tool for this class of historical question) for next time.

**Full since-real-launch historical backfill -- ALREADY DONE, verified, no new work needed.** Before launching a VM (the
sanctioned `deployment-service/scripts/vm/launch-mtds-lst-rates-backfill-vm.sh` launcher exists and was ready to use),
checked the authoritative genesis dates MTDS actually reads at runtime
(`unified_api_contracts.registry.capability_declarations._defi_lst.LST_TOKEN_GENESIS` -- NOTE this differs slightly from
`chain_env.py`'s and `venue_launch_dates.py`'s dates for the same tokens; `_defi_lst.py` is the one
`get_lst_token_genesis()` actually returns and therefore the one that governs collection, so it's the one that matters):
swETH 2023-04-17, ETHx 2023-07-10, mETH 2023-10-06, osETH 2023-11-28. A spot-check turned up existing data at every
genesis date, so instead of launching a redundant VM I read the bucket's consolidated manifest
(`_index/availability_index.parquet`, 8.59M rows, ~95s to pull) and filtered to these 4 venues + `data_type=lst_rates`:
5,946 rows, **100% `capture_status=captured`, ZERO missing days across each token's genesis-to-2026-04-09 window**
(coverage actually extends well past that too, into the ongoing daily-cron range). Content-verified (not just
manifest-trusted) by reading 6 real parquet files spanning 2023-04-17 through 2025-03-01: every genesis-day rate is ~1.0
(correct -- a brand-new LST has no accrued yield yet) and rates increase monotonically over time with real, increasing
block numbers (e.g. STADER/ETHx: 1.0000059 on 2023-07-10 -> 1.0324 on 2024-06-15) -- real, sane, non-fabricated data.
Someone already ran this backfill (most likely the `mtds-lst-rates-*` VM lineage referenced in
`plans/active/lst_rate_honest_coverage_2026_07_21.md`, though that exact VM name no longer appears in
`gcloud compute instances list` -- terminated/deleted after finishing) before this session ever touched this thread. No
VM launched, no compute spent, no operator decision needed on backfill scope -- there was nothing left to backfill.

**Root-cause the rare late-stage OOM/timeout -- investigated further, real mechanism found and quantified, filed as its
own issue rather than a rushed shared-library fix.** Checked the manifest consolidator's own health
(`uts-prod-manifest-consolidator-market-data-defi`) -- it runs reliably (~60s cadence, mostly succeeding), ruling out
"the consolidator never runs" as the explanation. Re-checked the DeFi manifest's `_index/per_vm/` directory: the 113.6MB
`canonical-migration-defi-rebuild-20260722-194751.parquet` I found earlier had grown to **173.8MB and was still being
actively written** (a live, in-progress migration process, not touched). This means the shared
`_read_and_merge_per_vm_shards` fallback path (triggered whenever the consolidated manifest index is >120s stale) has no
size guard against a large, currently-growing shard from ANY concurrent process -- a real, live, worsening risk to every
DeFi handler's occasional fallback read, not something specific to `lst_rates_handler.py`. Still could NOT conclusively
pin this to the two SPECIFIC historical incidents (the 173.8MB shard postdates both). Filed as
`defi_manifest_per_vm_shard_fallback_bloat_2026_07_23.md` rather than patching the shared library in this LST-scoped
pass -- a wrong bound in a function every DeFi handler depends on is a worse outcome than a documented, correctly-scoped
follow-up.
