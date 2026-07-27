---
doc_type: issue
title: >-
  instrument_id_format_canonicalization_2026_07_08 -- Orchestration state history (split off 2026-07-27, line-cap
  remediation)
summary: >-
  Pure historical/archival split of the "Orchestration state, 2026-07-09" section out of
  plans/active/issues/instrument_id_format_canonicalization_2026_07_08.md, which had grown to 1,309 lines (over the
  1000-line hard cap) -- this section is a dated, context-loss-recovery narrative record with zero open todos of its own
  (all actionable items live in the source doc's own Todos section, untouched by this split). No content was edited,
  only relocated; the source doc's own "What this is NOT"/Todos/Progress Log sections are unaffected.
status: resolved
nature: notes
asset_group: [cefi, defi, prediction]
stage: [data, meta]
repos: [instruments-service, unified-api-contracts, market-tick-data-service]
scope: [engineer, admin]
tags: [instrument-id, canonicalization, archived-history, line-cap-split]
related:
  [
    /plans/active/issues/instrument_id_format_canonicalization_2026_07_08.md,
    /plans/active/na_docs_validity_and_ao_eligibility_audit_2026_07_26.md,
  ]
created: 2026-07-08
last_updated: "2026-07-27"
parent_epic: instruments_master
priority: P3
resolved_by: >-
  Split action itself resolves this doc's purpose (archival record preserved, not an open question) -- 2026-07-27.
locked_by:
source: >-
  Split from plans/active/issues/instrument_id_format_canonicalization_2026_07_08.md's "Orchestration state, 2026-07-09"
  section during na_docs_validity_and_ao_eligibility_audit_2026_07_26.md's Phase 2 -- that doc was 1,309 lines (over the
  1000-line hard cap), blocking its own assigned_vm reclassification.
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
---

## Orchestration state, 2026-07-09 — durable record of in-flight parallel work (for context-loss recovery)

Following the operator's directive to execute this doc's findings entirely including data migration, "so there is zero
trace of the old formats in doc, data, or manifest," work was fanned out across multiple `Workflow` tool runs (scripts
persisted to disk, resumable independent of any chat session). If context is lost, use
`Workflow({scriptPath, resumeFromRunId})` with the paths below — completed agent() calls replay from cache, only the
unfinished tail re-runs.

**Landed on `origin/live-defi-rollout` (verified via direct `git fetch` + log comparison, not agent self-report):**

- `unified-api-contracts@06edd868` + `07d22bdf` — 900-line file-size split (`mvp_scope.py`/`honest_coverage.py`/
  `source_priority.py`/`tradfi_ticker_universe.py`) + `canonical_id_builder.py`'s `margin_marker` kwarg.
- `instruments-service@176d4610` (Bybit/Kraken-Futures margin-type bugs + `@LIN`/`@INV` builder), `@554ef058` (OKX
  margin-type inversion bug), `@7fbc38c1` (Deribit OPTION `@LIN`/`@INV`-`YYYYMMDD`), `@4e072d93` (DEX-pool fee-tier
  dash+bps), `@0d0c3742` (Prediction underlying + cross-venue canonical_instrument_id).
- `market-tick-data-service@19357ad4` (OKX venue-key fix), `@1e8870b1` (on-chain-perp live connectors + manifest
  migration script).

**UPDATE 2026-07-09 — `wf_41d76b71-c79` COMPLETED and independently verified (SHA + content + isolated clean-worktree
test run, not self-report).** `instruments-service@6a1122e5` (`git rev-parse HEAD origin/live-defi-rollout` both return
`6a1122e5b59c1d57b50f9e6d5f676eac8ea7fb12`) plus the 3 previously-local commits (`a326f6b9`, `57f8a754`, `1a696db7`) are
now ALL genuinely on `origin/live-defi-rollout` — this section's prior "committed locally, not yet on origin" is now
stale, kept only as history. Also landed: `unified-trading-pm@f05b57f93`, a real `quickmerge.sh` bug fix (the "already
committed, skip to push" check previously required the WHOLE working tree to be porcelain-clean, essentially never true
in this heavily concurrent shared-tree session — scoped to `--files` instead; may reduce false quickmerge blocks for
every other in-flight agent). Verification also reconfirmed the catalog-durability finding above with direct evidence
(91/312 rows re-surfaced identically after a roll-up 6h post-fix, 0 new pollution).

**In-flight `Workflow` runs (script + run ID, resumable):**

1. `wf_41d76b71-c79` — `tradfi-combo-inherit-and-land` — **COMPLETE**, verified landed (see update above). Script:
   `/Users/ikennaigboaka/.claude/projects/-Users-ikennaigboaka-Code-unified-trading-system-repos--tabs-3/75f22ce1-df33-490d-921e-c63d29f3656f/workflows/scripts/tradfi-combo-inherit-and-land-wf_41d76b71-c79.js`
2. `wf_c4796aec-f35` — `canonical-id-full-historical-sweep` — real (non-smoke-test) catalog + per-day-corpus + GCS
   filename migrations for Bybit/Kraken, Deribit, OKX, on-chain-perp, DEX-pool, Binance. Script:
   `/Users/ikennaigboaka/.claude/projects/-Users-ikennaigboaka-Code-unified-trading-system-repos--tabs-3/75f22ce1-df33-490d-921e-c63d29f3656f/workflows/scripts/canonical-id-full-historical-sweep-wf_c4796aec-f35.js`
3. `wf_118d8268-18c` — `mtds-canonical-symbol-migration` — discovers + migrates MTDS raw trade-tick/orderbook `symbol`
   values (not the full instrument_id) to the canonical symbol shape, per venue family (operator: "every single value,
   parquet file, etc., needs to be part of the scope" — full instrument_id prefix not required for raw ticks, but the
   symbol portion is). Script:
   `/Users/ikennaigboaka/.claude/projects/-Users-ikennaigboaka-Code-unified-trading-system-repos--tabs-3/75f22ce1-df33-490d-921e-c63d29f3656f/workflows/scripts/mtds-canonical-symbol-migration-wf_118d8268-18c.js`

**Still queued:** wiring the shared live-construction path
(`instruments_service/reference_data/adapters/cefi/ tardis/adapter.py`, `ccxt_adapter.py`) for
Bybit/Kraken/OKX/Deribit/Binance's PERPETUAL/FUTURE/OPTION `instrument_key` — every sibling agent this session deferred
touching this shared file due to lock contention with the TradFi WIP, now cleared per the update above; dispatching now.
A final cross-repo zero-old-format-traces verification pass is also queued behind all of the above.

**UPDATE 2026-07-09 — dispatched `wf_9e5f13e3-962`** — `live-wiring-plus-legacy-naming-audit` — wires the shared
live-construction path (`tardis/adapter.py`, `ccxt_adapter.py`) so new captures emit `@LIN`/`@INV` directly, PLUS the
generalized CeFi + DeFi legacy-GCS-naming audit decided below, then verifies both. Script:
`/Users/ikennaigboaka/.claude/projects/-Users-ikennaigboaka-Code-unified-trading-system-repos--tabs-3-unified-trading-pm/75f22ce1-df33-490d-921e-c63d29f3656f/workflows/scripts/live-wiring-plus-legacy-naming-audit-wf_9e5f13e3-962.js`

**UPDATE 2026-07-09 — `wf_118d8268-18c` (MTDS raw-tick symbol migration) COMPLETE, all 10 stages (5 discover + 5
migrate) done.** Real per-family outcome:

- **on-chain-perp — 100% COMPLETE.** Code shipped `market-tick-data-service@b416ffce96e9` (PR #498, CI green, pending
  automerge); real bugs fixed across all 5 venues' native write paths + live filename sanitization. Historical migration
  independently, comprehensively verified (not sampled): **38,883/38,883 real files canonical, 0 remaining** for
  LIGHTER-ZKSYNC/PACIFICA-SOLANA/EXTENDED-STARKNET (a real duplicate-shape consolidation found and fixed along the way),
  plus EXTENDED-STARKNET's manifest (1,175/1,209 rows). Survived 6 background-process kills via idempotent restarts,
  verified against real GCS state each time. ASTER/HYPERLIQUID's own historical rename + Tardis-archive post-fetch remap
  for LIGHTER/PACIFICA/EXTENDED were correctly deferred (real file-lock conflicts with concurrent sibling agents, not
  scope avoidance) — flagged as follow-ups.
- **cefi-dated-perps — code shipped, historical backfill NOT completed this session (environmental, not a code
  defect).** `market-tick-data-service@3ee21c8c` fixes 3 real bugs: OKX-FUTURES dated futures silently written as
  `perpetual` (regex never matched OKX's dash+6-digit shape), Bybit's glued base/quote parsed wrong
  (`BTCUSDT-10JUL26`→`BTC` needed quote-suffix stripping), and a dead `normalise_kraken_futures_symbol` now wired into
  the write path. The historical migration script is real and tested (a clean 81/81-file dry-run) but hit a reproducible
  environmental GCS stall (list/download calls 4-5x slower than normal) across 3 attempts with **zero real writes
  landed** — needs a re-run in a less-contended window, the tool itself is ready.
- **TradFi single-leg — code fixed, historical migration running (now on VM, see below), and a large NEW gap found**:
  120,946 CME `options_chain` entries (**~187.5M rows**) sit under a different, unverified legacy per-contract/spread
  flat layout this fix does NOT cover — correctly excluded rather than risked at that scale, documented in
  `docs/TRADFI_INSTRUMENTS.md` as its own open follow-up, not silently dropped.
- **DEX-pool — code shipped `market-tick-data-service@0ce28623`, historical migration running (now on VM, see below),
  and 2 NEW gaps found**: (1) a **second, distinct writer path** (`0x<address>.parquet` per-pool files, no
  `symbol`/`venue`/`chain` columns, under `pipeline_mode=batch_onchain_subgraph`, confirmed live for CURVE) whose
  forward code is already fixed (different commit `0713c01a`) but whose historical backlog needs its own separate
  migration — correctly skipped, not mis-touched, by the current script; (2) confirmed via repo-wide grep that
  `uniswap_v2`/`uniswap_v4`/`trader_joe_v2`/`velodrome_v2` have **zero forward capture code at all** in
  `dex_pools_handler.py`/`dex_swaps_handler.py` — a real, pre-existing, separate gap.
- **Prediction — code + a real performance bug fixed, historical migration running (2 of 5 shards now on VM)**: found or
  worker counts above 32 made throughput WORSE (128 workers slower than 32) due to undersized HTTP connection pools on 3
  separate client instances (main session, OAuth refresh session, listing client) — fixed by widening the pool. A
  further hardening fix was tested clean but not committed (its own QG run was CPU-starved by the 5 live migration
  shards, correctly not force-shipped) — flagged as a follow-up.

All 5 families' migration scripts are real, backup-first (copy-to-new-key or explicit backup-before-overwrite), and
idempotent/resumable — safe against interruption. The TradFi and DEX-pool historical runs referenced above are the same
ones already moved to VMs in the local-migration-audit update further up this Progress Log.

**OPERATOR DECISION 2026-07-09 — prefer real VM-based execution over session-tied agent execution for the remaining
heavy migrations, because "I will have to leave my laptop at some point."** All 4 `Workflow` runs above execute as
background tasks tied to the operator's current interactive session — if that session ends (laptop closed/asleep), any
in-progress, not-yet-committed/not-yet-written work in them is at risk. Real GCS spot VMs, once launched and verified
started, run independently of any laptop or session — matching this workspace's existing
`/codex/05-infrastructure/spot-vms-for-backfill.md` pattern (SPOT by default, no fire-and-forget: verify STARTED<60s +
real progress within the first ~10min, then let it run unattended to completion). Dispatched a survey+launch agent to:
(1) check real current state so no VM is launched for work the session agents already finished, (2) launch real spot VMs
for genuinely large remaining pieces (Binance per-day corpus if still pending, on-chain-perp's ~19,255-object
legacy-naming gap, MTDS's real migration once its discovery scope is known, and any large CeFi/DeFi legacy-naming
migration found), each verified-started before being left to run unattended. **Operator also confirmed (same message)**:
every migration in this effort should move straight from smoke-test-verified to the real full run, not pause for a
second go/no-go — already the standing instruction given to every dispatched agent this session, reconfirmed here.
Report pending — once it lands, this section will be updated with real VM names/instance IDs and how to check on them
from a future session.

**UPDATE 2026-07-09 — VM survey/launch agent reported back. Real result: mostly NOT needed (session agents already
finished the big items); the one genuine VM candidate was ATTEMPTED and FAILED, reverted to local.** Confirmed DONE and
durable via real log evidence (no VM needed): Binance per-day corpus (9,234 files), Bybit/Kraken per-day corpus (9,560
files), Deribit per-day corpus (5,342 files), DEX-pool catalog write-back (`instruments-service@bcfdef1a`). **The one
real VM candidate — on-chain-perp LIGHTER-ZKSYNC/PACIFICA-SOLANA/EXTENDED-STARKNET (38,884 files, ~60min projected) —
did NOT end up durably on a VM**: v1 launch failed at boot (`unified-api-contracts` install failure, fixed via
`SETUPTOOLS_SCM_PRETEND_VERSION`), v2 booted and briefly ran real work then stalled (process alive via SSH but zero new
log lines for 5+ min) — agent deleted it under time pressure rather than debug further, and reverted to running the job
**locally** (session-tied again, reduced to 20 workers to fix a real connection-pool contention root cause). No orphaned
VMs confirmed (`onchain-perp-symbol-canon-20260709-123056` verified TERMINATED via direct
`gcloud compute instances list`, not billing). **This directly does not yet satisfy the operator's stated durability
need** — flagging for a proper retry with real stall-debugging (SSH in and diagnose, don't abandon after 5 min) rather
than accepting local execution as the final state.

**Also found, real and still open:**

- ASTER/HYPERLIQUID legacy bare-symbol-shape gap (~19,255 objects): the path-based venue-parsing regex extension looks
  complete in code but is UNCOMMITTED and unvalidated; a fresh dry-run for real numbers has been running 25+ min on the
  initial GCS listing alone (confirmed still alive via direct process check, not obviously hung — GCS listing over a
  huge prefix can genuinely take a while — but no real numbers yet as of this update).
- OKX per-day `@LIN`/`@INV` migration: **no script exists yet** (only a narrower margin_type-only fix shipped earlier);
  confirmed via direct GCS sampling the per-day corpus is still 0% migrated. Blocked on
  `ccxt_adapter.py`/`tardis/adapter.py` live-wiring landing first (`wf_9e5f13e3-962`, still in flight).
- **NEW real finding — CeFi/DeFi legacy-naming audit surfaced a genuine ghost-venue-merge problem**, e.g.
  `UNISWAPV2-ETHEREUM` vs `UNISWAP_V2-ETHEREUM`, `AAVEV3-*` vs `AAVE_V3-*` (echoes the already-known AAVE_V3-OPTIMISM
  misspelling finding 5 above, but broader) — large real scope (many venue-pairs × 1,000-2,300 days each); a sibling
  agent has scaled this to a full local `--apply --workers 48` run as of 13:41 BST — durability status of that run not
  yet independently confirmed.
- TradFi single-leg product-root extension + Prediction instrument-id wrap: both newly-written, still in incremental
  sample-size validation, not yet at full scope.

**UPDATE 2026-07-09 — real gap found in the VM launch itself: it was NOT properly registered for monitoring.** Operator
asked directly whether these migration VMs launch through deployment-service such that they surface in the real
monitoring (deployment-ui `/deployments`, `/cockpit`, Slack, fleet reconciliation) — verified via direct code read that
they did NOT. `deployment-service/scripts/vm/vm_zombie_watchdog.py:762-768`'s `VM_PREFIX_TO_BUCKET` registry (the SSOT
`classify_deployment_target()` longest-prefix-matches against, raising `UnclassifiedDeploymentError` — never a silent
default, per `/codex/05-infrastructure/deployment-observability.md`) only recognizes
`canonical-migration-{cefi,tradfi,defi,prediction,legacy}-` prefixes. The prior agent's ad hoc VM name
(`onchain-perp-symbol-canon-...`) matched none of them — it would have surfaced as `UNKNOWN` in
`/api/fleet/reconciliation` (subject to classify-or-kill), never shown in deployment-ui/cockpit/Slack. Real, existing,
purpose-built tool found: `deployment-service/scripts/vm/launch-canonical-migration-vm.sh`
(`Epic: infrastructure_master`, `Lifecycle: oneoff`) already does correct naming/bootstrap (`setup-data-pipeline-vm.sh`,
durable log streaming)/labels — but its `_script_for()` is hardcoded to the older v9 flat→hive canonical-migration
tools, not this session's `@LIN`/`@INV`/legacy-naming scripts. **Corrected instruction issued to the in-flight retry
agent**: either extend `launch-canonical-migration-vm.sh` with a new case for this session's real migration scripts
(preferred — ships via quickmerge in `deployment-service`), or at minimum name any new VM
`canonical-migration-cefi-<timestamp>[-suffix]` (on-chain-perp is already classified under the `cefi` asset group) +
reuse `setup-data-pipeline-vm.sh` + the same metadata/label shape — never an unregistered ad hoc prefix. Report pending.

**UPDATE 2026-07-09 — on-chain-perp symbol-canonicalization DONE, verified, real completion evidence.** Diagnosed the
earlier 404 volume as harmless: 3-4 overlapping local copies of the same idempotent job were hammering the same GCS
prefix from one laptop's network stack, starving connection pools — not a real data bug (download→backup→
upload-new→delete-old ordering makes an interrupted run always safely resumable, confirmed by reading the script).
Relaunched the VM (still the ad hoc `onchain-perp-symbol-canon-*` name — real gap above NOT yet fixed, flagged as a
"don't reuse as-is" for the next migration VM rather than fixed this time since there was no pending future launch to
correct) — booted clean this time, processed all **38,884 files in ~9 minutes**,
`{'skip_already_migrated_prior_run': 9232, 'migrated': 29652}` (sums to 38,884, 0 errors), self-terminated after. Real
GCS spot-check post-run confirms canonical filenames present, zero bare-symbol shapes remain in the sample checked.
Redundant local copy killed once the VM was confirmed healthy. **The naming-registration gap is NOT yet fixed in code**
— next VM launch for this effort MUST either extend `launch-canonical-migration-vm.sh` or use a properly-registered
prefix; do not reuse the scratchpad script again.

**Ghost-venue-merge** (`instruments-service/scripts/legacy_naming_audit_dexpool_ghost_venue_merge_2026_07_09.py`,
`UNISWAPV2-ETHEREUM` vs `UNISWAP_V2-ETHEREUM` etc., `--apply --workers 48`): **DONE** —
`total=33003 ok=32992 failed=11 total_ghost_rows=2309519 total_merged_rows=2823314`, real completion log confirmed
(`full_apply_run.log`), 99.97% success.

**UPDATE 2026-07-09 — real audit of ALL concurrently-running local migrations found the durability risk was broader than
the single job first flagged, and a real (not cosmetic) data-loss mechanism.** A full re-check found **9 real local
Python migration processes running simultaneously**, none on a VM. Re-verified real current ETAs (not the stale
first-pass numbers): TradFi single-leg (~6.5h), **DEX-pool symbol-shape (~12.6h — actually the longest, not TradFi)**,
on-chain-perp HL/ASTER (~5-6h, mid-scan), on-chain-perp LIGHTER/PACIFICA/EXTENDED (~1.1h), 5 sharded Prediction jobs
(~1.3h/1.3h/2.3h/**8.2h**/**9.1h**).

**Real finding on the connection-pool warnings**: two distinct phenomena. "Connection pool is full, discarding
connection" (thousands of occurrences) is cosmetic urllib3 noise, zero correlation with real failures. But real
`BrokenPipeError`/`ConnectionResetError`/`SSLEOFError` exceptions (logged as actual errors, each a genuinely
lost/skipped shard, not auto-retried) clustered in the same 1-2 second windows across unrelated processes — real local
resource contention from 9 concurrent processes (several 48-96 workers each) hammering GCS simultaneously. **Confirmed
causally**: DEX-pool's climbing error count (11→45→96) and on-chain-perp's went flat immediately after killing the 2
heaviest local processes — reducing local concurrency measurably improves correctness, not just laptop-closing
durability. Failure rate ~0.1-0.3% of objects, shard-isolated (no corruption) but not auto-retried — needs a small
follow-up remediation pass over each job's `error`-tagged shards once done.

**Moved to properly-registered VMs** (first real use of the corrected naming pattern):
`canonical-migration-tradfi-20260709-160919` (TradFi single-leg — real ~26x speedup once off the shared laptop
connection pool, 145 obj/s vs 5.5 obj/s local, new ETA ~15min not 6.5h) and `canonical-migration-defi-20260709-161510`
(DEX-pool — was the real worst offender: longest ETA + climbing real error count). Both bucket targets verified
byte-identical to the local runs before trusting them; both confirmed healthy via real `run.log` content. **Note**: the
TradFi run used `--skip-manifest` — the `_index/ availability_index.parquet` manifest rewrite is a separate follow-up
once the VM's GCS pass completes, not yet done.

**Left running locally, with real reasoning**: 3 short jobs (~1.1-2.3h each, low/zero errors) — fine as-is.
On-chain-perp HL/ASTER (~5-6h) — idempotent but already paid a 1.5h full-bucket-scan sunk cost with no resumable
worklist; moving now would re-pay that scan, so left running — **flag if the laptop needs to close before ~5-6h from
now, this one specifically would need a VM move first**. Prediction shard4c (~8.2h) and shard5b (~9.1h) — flat/near-
zero error rate (no active correctness signal, unlike DEX-pool), left running to bound this pass's blast radius, but
**explicitly recommended for a VM move if the laptop is closing within the next several hours** (same
`canonical-migration-prediction-` registered prefix, no file upload needed, same command as the local invocation).

**UPDATE 2026-07-09 — Prediction shard4c + shard5b also moved to VMs, both confirmed healthy.** Re-verified real current
state before acting (still multi-hour, 0-1 flat errors, not climbing) and script idempotency (copy-to-new-key

- `gcs_describe_object` pre-check = safe to kill/resume anywhere). `launch-canonical-migration-vm.sh prediction`'s
  hardcoded `_script_for` mapping points at a different, older tool — followed the same precedent as the tradfi/defi
  moves (direct `gcloud compute instances create` under the registered `canonical-migration-prediction-` prefix with a
  custom `VM_MIGRATION_CMD`, same startup-script/labels/metadata shape). Launched
  `canonical-migration-prediction-20260709-163134-shard4c` and `-shard5b`; health verified via real GCS-streamed
  `run.log` content before killing the local PIDs (the other, untouched 3 local processes are unaffected). Real speedup:
  shard4c 21→71 obj/s (~3.4x), shard5b 14.2→86 obj/s (~6x). New real ETA: shard5b ~2-2.5h (single POLYMARKET phase),
  shard4c ~4-5h total (KALSHI phase then POLYMARKET phase run sequentially). **Only one long-running local job remains:
  on-chain-perp HL/ASTER (~5-6h), deliberately left per the sunk-cost reasoning above** — needs an operator call if the
  laptop is closing within that window.

* **2026-07-09 — GENERALIZED FINDING + DECISION: legacy GCS filename/path conventions are a systemic risk, not just an
  on-chain-perp issue.** The on-chain-perp full-historical-sweep branch found that a real GCS narrow-prefix listing (not
  the manifest's summary count) shows ~99% of "captured" HL/ASTER historical objects (~19,255 of 19,435) sit under an
  EVEN OLDER bare-symbol filename shape (`AAVEUSDT.parquet`, `AAVE-PERP.parquet` — no venue, no type marker in the name
  at all) that neither the original nor the already-extended migration script's regex recognizes; they'd be silently
  skipped, not migrated. **Operator decision, 2026-07-09**: (1) extend that script to also parse venue from the object's
  GCS PATH (not just the filename) so this older shape is covered too, not left behind; (2) treat this as a general
  pattern, not an on-chain-perp-only bug — **audit CeFi (Binance/Bybit/Kraken/Deribit/OKX) and DeFi (13 DEX-pool
  protocols + lending/staking) historical GCS data for the same problem**: multiple coexisting filename/path naming
  conventions from different points in this workspace's history, only the most recent of which any current migration
  script recognizes. **Target**: exactly ONE canonical path/filename convention per venue going forward (per the
  filename-vs-instrument_id rule already settled above); every object under any OTHER legacy shape gets discovered and
  migrated to it — not just the already-known target-format gap this doc's findings 1-6 describe, but genuinely
  unknown-until-audited older shapes the way this one was. Dispatched as a dedicated discovery+migration workflow, see
  Orchestration state below.
* **2026-07-09 — `wf_118d8268-18c` onchain-perp venue-family slice (HYPERLIQUID/ASTER/PACIFICA-SOLANA/
  EXTENDED-STARKNET/LIGHTER-ZKSYNC) — real discovery + code fix + historical migration, MTDS.** Real discovery (live
  `gcloud storage`/parquet reads, not guesses) confirmed all 5 venues' raw-tick `symbol` column diverges from the
  `BASE-QUOTE@LIN` target: ASTER emitted the raw concatenated exchange symbol (`"BTCUSDT"`, no dash); HYPERLIQUID's S3
  archive + REST-fallback paths emitted the pre-2026-07-08 `"{coin}-PERP"` shape; LIGHTER-ZKSYNC/PACIFICA-SOLANA emitted
  a bare base-asset string (`"BTC"`); EXTENDED-STARKNET emitted a bare base-asset `symbol` alongside an already-dash-
  joined-but-unmarked `instrument_id` (`"BTC-USD"`). **Fixed (code, all 5 venues' NATIVE REST/S3 write paths)**:
  `market-tick-data-service@b416ffce` (confirmed on `origin/live-defi-rollout` via real `git fetch` +
  `merge-base --is-ancestor`, not just local HEAD) — `aster_adapter.py::_to_canonical_symbol`,
  `adapters/hyperliquid_s3.py::_canonical_perp_symbol`, `adapters/_umi_lighter.py::_lighter_canonical_symbol`,
  `adapters/_umi_pacifica.py::_pacifica_canonical_symbol`, `adapters/_umi_extended.py::_extended_canonical_symbol`, plus
  `live/websocket_runner.py::live_tick_blob_path` now sanitizes the filename component (colon-laden live filenames no
  longer diverge from the batch path's bare-symbol convention). 8 pre-existing unit tests updated to assert the new
  canonical values (`test_hyperliquid_s3_coverage.py`, `test_extended_candles.py`, `test_pacifica_candles.py`,
  `test_lighter_candles.py`); full targeted suite green (225 passed). **Historical migration (real, `--apply`,
  backup-first, real concurrency)**: LIGHTER-ZKSYNC (1,593 files) + PACIFICA-SOLANA (1,408 files) + EXTENDED-STARKNET
  (35,883 files) under `pipeline_mode=batch_tardis` — real scope discovered via a bounded per-day+venue-prefix scoped
  GCS list (2024-09-01..2026-07-08, NOT a whole-corpus walk). Elapsed time + final counts: see this session's completion
  report (agent-orchestrator task output) for the honest real numbers — not restated here to avoid this doc going stale
  the moment the doc is re-read. **Deliberately deferred, NOT a scope choice — real, confirmed live multi-agent
  conflict**: (1) ASTER/HYPERLIQUID historical GCS filename-rename + row-content symbol-column fix —
  `scripts/migrate_onchain_perp_perpetual_canonical_ 2026_07_08.py` was actively dirty (another agent's in-flight WIP,
  still dry-run-only as of this session, no `_index/backups/availability_index.pre_perpetual_canonical_*` found) at
  write time; touching the same GCS objects would race. (2) The Tardis-archive (`batch_tardis`) post-fetch `symbol`
  remap for LIGHTER-ZKSYNC/PACIFICA-SOLANA/ EXTENDED-STARKNET (the actual highest-volume current source for these 3
  venues) — `market_interface/adapters/cefi/ tardis_shared.py` + `market_interface/adapters/tradfi/tardis_adapter.py`
  were BOTH actively dirty (mtime 159s/228s at discovery, part of a larger actively-churning cluster also touching
  `partitioned_writer.py`, `kalshi_adapter.py`, `databento_enrichment.py`, `_dex_pools_*.py` — evidently this session's
  `wf_9e5f13e3-962` / `canonical-id-full-historical-sweep` work) at write time. **Insertion point identified for
  whichever agent picks this up next**: canonicalize the DataFrame's `symbol` column for these 3 venues before it
  reaches `finalise_rows_and_path`/`derive_row_instrument_id` in `tardis_cefi_shards.py`'s
  `finalise_and_write_cefi_shards`/`_tardis_cefi_shard_router` (both already group by the raw `symbol` column) — no
  `canonical_id_builder.py`/UAC change needed, since `_build_cefi_simple` just upper-cases and wraps whatever `symbol`
  string it receives (confirmed by reading `_build_cefi_simple` + `build_instrument_id`'s PERPETUAL dispatch directly).
  Full write-up + the LIGHTER-ZKSYNC market_id→symbol table (live-verified 2026-07-09 via
  `mainnet.zklighter.elliot.ai/api/v1/orderBookDetails`): `market-tick-data-service/docs/canonical-write-conventions.md`
  § "On-chain-perp `symbol` canonicalization".
* **2026-07-09 — CeFi legacy GCS naming-convention audit (the generalized finding's CeFi half) — COMPLETE, real gap
  found + fixed for OKX-SWAP/OKX-FUTURES, no gap for the other 4 target venues.** Real GCS listing (not the manifest
  summary — one flat `gsutil ls -r` over `instruments-store-cefi-prd-central-element-323112`'s
  `instrument_availability/by_date/`, 110,636 real objects, single walk) across BINANCE-FUTURES, BINANCE-DELIVERY,
  BYBIT, KRAKEN-FUTURES, DERIBIT, OKX-SWAP, OKX-FUTURES. **Found 4 distinct real path shapes** coexisting for the
  per-day snapshot corpus — all under the same fixed leaf filename (`instruments.parquet`; CeFi has NO
  bare-symbol-per-instrument-file shape anywhere, unlike the HL/ASTER on-chain-perp case that triggered this audit): (A)
  bare `day=D/venue=V/instruments.parquet` (33,602 real objects across the 7 target venues); (B) pipelined
  `day=D/pipeline_mode=batch_instruments_service/asset_group=cefi/venue=V/instruments.parquet`, a real coexisting
  duplicate write path spanning the SAME 2019-current range as shape A, not a superseded relic (28,710 real objects);
  (C) doubled-`day=` bug, pipelined variant (144 objects); (D) doubled-`day=` bug, bare variant (144 objects) — C/D both
  bounded to 18 real dates (2026-05-05..2026-05-22) across 12 venues, a real partition-key double-write bug, separate
  from the A/B duplication.
  - **Coverage, verified by exact reconciliation (real total objects vs. real `.bak` backup count already written, not
    just code inspection)**: `canonicalize_bybit_kraken_futures_catalog_2026_07_09.py`,
    `canonicalize_binance_futures_delivery_catalog_2026_07_09.py`, and `canonicalize_deribit_id_markers_2026_07_09.py`
    all list via a FLAT substring scan (`"venue=X/" in blob.name`) over the whole `by_date/` prefix — depth-agnostic,
    already covers every shape found. Full coverage confirmed: BYBIT+KRAKEN-FUTURES 9,540 real objects / 9,560 real
    `.bak` (the +20 is a separate, pre-existing, already-documented double-backup-of-a-backup artifact, not a coverage
    gap); BINANCE-FUTURES+DELIVERY 9,234/9,234 exact; DERIBIT 5,342/5,342 exact. **No new script needed for these 4
    venues.**
  - **Real gap found: `canonicalize_okx_margin_type_2026_07_09.py`'s `--by-day` mode.** Its listing
    (`_list_okx_day_files`) does a two-level DELIMITED (non-recursive) listing — `day=D/` prefixes, then checks only
    whether `venue=V/` is a DIRECT CHILD of each `day=D/` prefix — structurally can never see shape B (one level deeper,
    under `pipeline_mode=.../asset_group=cefi/`) or shapes C/D. Real reconciliation: 9,576 total real
    OKX-SWAP+OKX-FUTURES objects, only 4,762 (shape A, 49.7%) ever carried an `.okxmarginfix.` backup — **4,814 real
    objects (shape B 4,742 + shape C 36 + shape D 36) were silently never discovered**, still carrying the original
    margin-type-inversion bug that script exists to fix. This means the doc's own earlier "FIXED 2026-07-09, 0 remaining
    mismatches" claim for this corpus (`instruments-service/docs/CEFI_INSTRUMENTS.md`, since corrected) was wrong — its
    own re-verification pass shared the same blind spot as the fix it was verifying. Confirmed with real content, not
    just path inspection: sampled `day=2023-06-15` OKX-FUTURES — shape A (migrated) correctly showed `BTC-USD-230616` as
    `inverse`; the shape-B copy of the SAME (day, venue, instrument) still showed `linear` for all 60 real rows before
    this fix ran.
  - **Fix — new script `instruments-service/scripts/legacy_naming_audit_okx_2026_07_09.py`, real full sweep RAN
    2026-07-09.** Same `_expected_margin_type` correction rule as the original script (byte-for-byte identical formula),
    applied via a flat depth-agnostic listing (same proven pattern as the Bybit/Kraken/Binance/Deribit scripts). Real
    results (`--apply --confirm --full-sweep --workers 30`, all 9,576 real files scanned, shape A included idempotently
    to prove nothing was missed): `files_scanned=9,576, files_written=4,798, rows_fixed=155,614, errors=0`, elapsed 927s
    (15.5 min). A full-corpus re-verification dry-run immediately after confirmed
    `files_written=0, rows_fixed=0, errors=0` — 0 remaining legacy-shape-hidden mismatches across the ENTIRE real
    corpus, all 4 path shapes. Backup-first (`instruments.legacynamingauditokx.<ts>.bak.parquet` per touched file). Full
    write-up: `instruments-service/docs/CEFI_INSTRUMENTS.md` § "CeFi legacy GCS path-shape audit (2026-07-09)" (also
    corrects the OKX per-day section's and "Known limitations" table's prior false-completeness claims).
  - **DeFi half of the generalized finding** (13 DEX-pool protocols + lending/staking) audited in parallel by a separate
    in-flight sibling workflow this session
    (`instruments-service/scripts/legacy_naming_audit_dexpool_ghost_venue_merge_2026_07_09.py`) — not this entry's
    scope; see that script/its own commit for DeFi-side real findings.

* **2026-07-09 — DeFi legacy GCS naming-convention audit + migration COMPLETE** (the DeFi half of the generalized
  finding immediately above; `wf_9e5f13e3-962`'s DeFi scope). Real, narrow (single-venue-prefix) GCS listings — not the
  manifest summary — against `instrument_availability/by_date/` in BOTH `instruments-store-defi-prd-{pid}` (2,363 real
  day-partitions, 2020-01-20..2026-07-09) and the legacy env-less `instruments-store-defi-{pid}` (2,315, confirmed
  frozen since 2026-05-22 — 0 real writes past that date) covering the 13 DEX-pool protocols + 25
  lending/staking/yield/restaking venues. **Real finding, same class as the CeFi ghost-venue/shape-B findings above**: a
  ghost (no-underscore) vs canonical venue-token spelling was written IN PARALLEL for 28 real venue×chain pairs across
  ~4 years (2022-03-27..~2026-05-11, then stopped — `writers.py`'s `canonicalize_defi_venue_combined()` fix, 2026-05-22,
  already prevents new ghost writes but never touched the historical corpus) — 33,012 real ghost objects (31,968
  `-prd-` + 1,044 legacy-bucket-only), including 2 fully-orphaned cases (`PANCAKESWAPV3-ZKSYNC` 446/446 days,
  `VELODROME_V2-OPTIMISM` 1,044/1,044 days — zero canonical counterpart existed anywhere pre-migration). A real content
  diff (81 sampled pairs) proved ghost≠canonical duplicates — each side commonly holds real pools the other is missing
  (schema also differs: canonical 51 cols vs ghost 40) — so this was a MERGE migration (column+row union, canonical wins
  on identity-column conflict, ghost-only rows carried over honestly), not a blind rename, backed by a real before/after
  example (`AAVE_V3-OPTIMISM` day=2022-04-23: 12+12 rows, 3 unique each side → 15 merged, 0 lost, independently
  re-verified post-write). Executed via
  `instruments-service/scripts/legacy_naming_audit_dexpool_ghost_venue_merge_2026_07_09.py` — backup-first (every
  pre-migration object server-side-copied under `_migration_backup/legacy_naming_audit_dexpool_2026_07_09/` before any
  write), verify-then-delete (ghost only deleted after a post-write re-read confirms row-count ≥ the identity-deduped
  union floor), real `ThreadPoolExecutor` concurrency (48 workers). **Real final results**: 33,003/33,003
  (bucket,ghost,day) triples migrated successfully (100%, 0 remaining failures after an 11-item mop-up pass), a
  follow-up idempotent full re-scan of all 29 ghost-venue prefixes across both buckets confirmed **0 real ghost objects
  remain anywhere** — durable, not just catalog-level. Real elapsed time ~78 minutes wall-clock (main pass 4,568s +
  mop-up 41s + verification listings; measured throughput ramped 4.4→7.6 objects/sec). Real content recovered: 2,314,285
  total rows read from ghost objects, merged into canonical objects now totaling 2,828,070 rows. **Real mid-run bug
  found and fixed in the same pass**: 11/33,003 objects (1 transient GCS 503, 10 `UNISWAPV3-POLYGON` days) initially
  failed a post-write verify check SAFELY (ghost not deleted, no data at risk) — root cause: the verify floor compared
  against the ghost object's RAW row count, but a real source file can carry an internal duplicate identity value (e.g.
  `UNISWAPV3-POLYGON` day=2025-01-10: 476 raw rows, 475 unique `raw_symbol` — a real subgraph-pagination-overlap
  re-listing, not corruption); the merge already correctly deduped on the identity column, so the raw-row-count floor
  was rejecting a genuinely correct result as a false positive. Fixed (floor now uses the unique identity-column count)
  and all 11 re-ran clean. **Lending/staking finding**: of the 25 requested venues, only
  Aave_V3/Spark/Compound_V3/Morpho/Fluid have EVER written a real object to this path — the other 18 (Euler_V2, Radiant,
  Venus, Benqi, MarginFi, Solend, Renzo, KelpDAO, Puffer, RocketPool, Sanctum, Solblaze, Yearn_V3, Beefy, Karak, Idle,
  Symbiotic, Convex) have ZERO real objects under ANY naming variant — confirmed via a full real venue-token inventory
  (87 distinct tokens, full 2020-2026 history, both buckets) — NOT a naming gap (nothing to rename), a separate
  pre-existing "never backfilled" state, out of THIS audit's scope. **Note (2026-07-13): fixed for 4 of the 18 — VENUS,
  RADIANT, EULER_V2, BENQI now have real backfilled objects** (VENUS 6, RADIANT 8, EULER_V2 6, BENQI 2 rows), per the
  resolved `defi_lending_atoken_debttoken_instrument_split_2026_07_07.md`'s 2026-07-13 entry. MarginFi/Solend and the
  other 12 non-lending venues in this list are unaffected and still ZERO, per that same source. **Second finding,
  flagged not executed, mirrors CeFi's shape-B finding above**: a fully distinct real duplicate write path was found —
  `day={D}/pipeline_mode=batch_instruments_service/asset_group=defi/venue={V}/...` — mirroring ~104K of the flat tree's
  real objects in `-prd-` (2,353/2,363 days), confirmed dead going-forward (real writes stopped ~2026-06-30). Unlike
  CeFi's shape B (which the CeFi audit above found DOES carry stale/buggy unmigrated content in some cases), DeFi's
  shape-B samples checked (oldest `day=2020-01-20` + a recent `day=2026-06-10`, CRC32C+MD5 hash-verified) were
  byte-for-byte identical to their flat-shape sibling — but this was only 2 spot-checked samples, not a full
  reconciliation, so treat as a real-but-narrow finding, not a proven full-corpus guarantee. Confirmed UNREAD by every
  real consumer (`unified_trading_library`'s
  `instrument_lifecycle_loader.py`/`domain/instruments_client.py`/`domain_client/clients/instruments.py`/
  `options_cluster_lookup.py`/`core/cloud_data_provider.py` — all read the flat shape only). Recommended as its own
  dedicated SAFE-TO-DELETE audit (same pattern as MTDS's own
  `e2e-testing/scripts/defi/audit_legacy_gcs_dup_delete_list.py`, and the exact same shape-B pattern the CeFi audit
  above already found + partially fixed), NOT executed this pass. Full evidence + per-protocol table:
  `instruments-service/docs/DEFI_INSTRUMENTS.md` § "Legacy GCS naming audit — real per-protocol findings and migration
  (2026-07-09)". Evidence: instruments-service@11192be2 (landed on `origin/live-defi-rollout`, verified via
  `git merge-base --is-ancestor`).

**UPDATE 2026-07-09 — `wf_9e5f13e3-962` COMPLETE (4/4 agents), independently verified — one genuinely NEW,
previously-unreported bug caught by the verify pass.** Live-construction wiring (`instruments-service@8128189e`) and
both audits' completions above are all independently re-confirmed with real evidence (fresh byte-level GCS
downloads/diffs, not trusting self-reports): the OKX shape-B fix and the AAVE_V3-OPTIMISM ghost-merge sample both match
their claimed row counts exactly. The Deribit "no gap" and the 18-venue "never backfilled" claims both hold up under
independent spot-check too.

**Real new finding, not caught by either audit itself**: the ghost-venue-merge migration
(`legacy_naming_audit_dexpool_ghost_venue_merge_2026_07_09.py`'s `_merge_frames()`) concatenates ghost-only rows into
the canonical file via `pd.concat([canon_df, ghost_only], ignore_index=True)` **without rewriting those rows'
`instrument_key`/`venue` COLUMN VALUES** to canonical spelling — only the GCS _path_ is canonical now, the _data inside_
still literally reads `instrument_key='AAVEV3-OPTIMISM:A_TOKEN:ALINK'`/`venue='AAVEV3-OPTIMISM'` (no underscore) for
every ghost-only row that got merged in. Confirmed via direct download+read, not assumption. This directly contradicts
"zero trace of the old formats in data" — any downstream consumer that filters/joins on the `venue` COLUMN (not the GCS
path) will silently miss or mis-bucket these rows. The doc's own cited examples (`UNISWAPV3-OPTIMISM` day=2023-11-18 6
rows, `PANCAKESWAPV3-BSC` day=2024-10-07 59 rows) suggest this is very likely systemic across some fraction of the
29,840 same-day-collision pairs, not a one-off. **Real fix needed**: rewrite `_merge_frames()` to also correct
`instrument_key`/`venue` on the ghost-only rows before concat, then re-run a one-time pass over every (day,venue) pair
that had ghost-only rows (a subset of the already-known 29,840, not a fresh full-corpus walk). Not yet fixed — filing as
its own follow-up.

**UPDATE 2026-07-09 — `wf_c4796aec-f35` (full historical sweep) COMPLETE, all 7 agents (6 packages + verify) done.**
Real production migrations, verified: Bybit/Kraken-Futures catalog+full by_date corpus (`instruments-service@ba4f7d2e`,
9,540 files, 1.98M id relabels), Deribit catalog+full by_date corpus (263,979/263,979 + 5,342/5,342 files, 7.98M rows),
OKX catalog+full by_date corpus (6,053 + 4,762 files, ~156K rows), on-chain-perp GCS renames+manifest (134,855 renamed,
7.2M manifest rows) — all independently re-verified by the verify agent against live production GCS, not self-reports.

**Two urgent, real findings from the verify pass, not yet actioned:**

1. **A live-trading correctness bug sits uncommitted, local-only, right now**:
   `market-tick-data-service/market_tick_data_service/live/connectors/deribit_ws.py` has a real, correct fix already
   written (the `count("-")==2` dead-code check was misclassifying every real Deribit FUTURE trade as OPTION) but it has
   NOT shipped — **live trading is currently running the buggy classifier**. This is the single highest-priority item in
   this whole update.
2. **Real production migrations exist that are not reproducible from git** — 3 scripts that already ran real GCS
   mutations (`canonicalize_deribit_id_markers_2026_07_09.py`'s `--by-date-all` mode,
   `canonicalize_binance_futures_ delivery_catalog_2026_07_09.py`'s concurrency, and BOTH OKX scripts entirely) exist
   only in this one machine's working tree — a fresh clone of `origin/live-defi-rollout` cannot audit, reproduce, or
   re-run any of them. The underlying data mutations are real and independently verified against live GCS (not
   fabricated), but the audit-trail gap itself is real and needs closing — commit these scripts.

**Also found — a real regression exposed by this session's own earlier fix, currently blocking ALL new Bybit captures.**
The Bybit/Kraken-Futures migration agent found: 46 real legacy coin-margined quarterly futures (`BTCUSDH22`-shape, 4
still actively trading) fail to capture — `adapter.py`'s expiry-resolution fallback chain has no branch for this no-dash
CME-month-code shape, and the resulting uncaught `pydantic.ValidationError` **kills the entire BYBIT venue fetch, not
just these 46 symbols** — real command reproduces it:
`python -m instruments_service --operation instruments --mode batch --asset-group cefi --venues BYBIT --start-date 2026-07-09 --end-date 2026-07-09 --force`
→ 0 records for the whole venue. This is a live regression, exposed (not caused) by the earlier margin-type fix
(`176d4610`) which removed a guard that previously silently absorbed this case. Correctly not fixed by the migration
agent (belongs in `adapter.py`, locked by concurrent live-wiring work all session) — needs its own urgent fix once that
lock clears.

Real evidence for all of the above: `instruments-service/docs/CEFI_INSTRUMENTS.md`, `docs/DEFI_INSTRUMENTS.md`, plus the
verify agent's per-venue-family honest-status table (git-vs-origin, live GCS spot-checks) in the workflow journal.

**UPDATE 2026-07-09 — dispatched `wf_c59510fe-3f5`** — `urgent-postverify-fixes` — the 3 items above: ships the live
Deribit trading-classifier fix, commits the 4 orphaned production-migration scripts, and fixes the Bybit `adapter.py`
regression (now unlocked). Script:
`/Users/ikennaigboaka/.claude/projects/-Users-ikennaigboaka-Code-unified-trading-system-repos--tabs-3-instruments-service/75f22ce1-df33-490d-921e-c63d29f3656f/workflows/scripts/urgent-postverify-fixes-wf_c59510fe-3f5.js`

**UPDATE 2026-07-09 — the ghost-venue-merge contamination bug (line 892 above) is FIXED, tested, and the
already-migrated data is fully remediated with real, independently-verified evidence.**

**Bug confirmed for real** (read `_merge_frames()` in full before touching anything):
`pd.concat([canon_df, ghost_only], ignore_index=True)` carried ghost-only rows into the canonical frame without ever
rewriting those specific rows' `instrument_key`/`venue` column values — verified directly against 3 real production
files (`AAVE_V3-OPTIMISM` day=2022-04-23: 3/15 rows; `UNISWAP_V3-OPTIMISM` day=2023-11-18: 6/288 rows;
`PANCAKESWAP_V3-BSC` day=2024-10-07: 59/145 rows all still read the no-underscore ghost spelling in
`instrument_key`/`venue`, GCS path was already canonical). No other column in the real 51-column schema embeds the venue
token (checked all 3 samples column-by-column, only `instrument_key`/`venue` hit).

**Fix shipped**: `instruments-service/scripts/legacy_naming_audit_dexpool_ghost_venue_merge_2026_07_09.py` — new
`_rewrite_ghost_venue_columns(df, ghost_venue, canon_venue)` (generic over every object-dtype column: exact-match cells
like `venue` are replaced outright, `<ghost_venue>:`-prefixed cells like `instrument_key` are rewritten preserving the
suffix — not hardcoded to those 2 names, so a future column following the same convention is covered for free). Called
at the top of `_merge_frames` BEFORE any dedup/concat, so it covers all 3 branches uniformly: the identity-dedup branch,
the no-shared-identity-column branch, and the pure-orphan (`canon_df is None`) branch — this last one matters because
the old code's `return ghost_df.copy()` for 100%-orphan days (e.g. `PANCAKESWAP_V3-ZKSYNC`) was ALSO unfixed
contamination, not just the 29,840 same-day-collision pairs the original bug report focused on.

**UPDATE 2026-07-09 — `wf_c59510fe-3f5` COMPLETE, all 3 urgent items landed and independently verified.**

- Deribit live-trading classifier fix: `market-tick-data-service@c55c1509`, confirmed on origin, real regression test
  added (`test_real_future_instrument_one_dash_classified_as_future`). Live trading now classifies correctly.
- 4 orphaned production-migration scripts (Deribit by-date, Binance concurrency, both OKX scripts):
  `instruments- service@0fdba6f6`, confirmed on origin with real content (16-22KB each, not stubs). A fresh clone can
  now reproduce/audit all these already-run production migrations.
- Bybit `adapter.py` regression: `instruments-service@c2d3fbbc`, confirmed on origin. Real fix:
  `_parse_bybit_month_ code_expiry()` resolves the missing quarterly settlement-day convention (cross-checked against 42
  real sibling contracts' `availableTo` values, 0 exceptions), plus a per-item `try/except` so one bad symbol can never
  again zero a whole venue fetch. **Independently reproduced live** by the verify agent: the real capture command now
  writes 675 records for BYBIT (was 0 before this fix) — exact match to the fix's own claim, not trusted blindly.

All 3 verdicts: genuinely fixed, genuinely landed, no discrepancies found.

**Real test added**:
`instruments-service/tests/scripts/test_legacy_naming_audit_dexpool_ghost_venue_merge_2026_07_09.py` (10 cases) —
asserts a ghost-only row's `instrument_key`/`venue` are canonical-spelled AFTER merge (not just that the row survived),
covering the collision branch, the pure-orphan branch, the no-identity-column branch, and idempotency. Independently
verified to FAIL against the pre-fix code (10/10 fail with
`TypeError: _merge_frames() takes 2 positional arguments but 4 were given`, confirming these are real regression tests,
not vacuous) and PASS against the fix.

**Real, targeted remediation of already-migrated data** (new script:
`instruments-service/scripts/legacy_naming_audit_dexpool_ghost_venue_contamination_remediation_2026_07_09.py` — reuses
the fixed migration's own `GHOST_TO_CANON`/`_rewrite_ghost_venue_columns`/`_read_parquet` via dynamic module load, no
re-implementation; NOT a fresh full-corpus walk — every row this bug could reach lives under exactly the 29 canonical
venue prefixes in `GHOST_TO_CANON`, in the `-prd-` bucket only, since `_process_one` always wrote the merged frame to
the PRD bucket regardless of source bucket):

- **Real scoping**: a scoped per-canonical-venue-prefix GCS listing (mirrors the original migration's own
  `_list_ghost_days`, just on the canonical side) found **35,594 real (canon_venue, day) pairs** across all 29 venues in
  `instruments-store-defi-prd-central-element-323112`.
- **Smoke test on real infra first**: 50-pair dry-run + a real 5-pair `--apply` write, independently re-verified (backup
  existed, 0 ghost cells left, row counts unchanged) before the full run.
- **Real full remediation** (`--apply --workers 32`, ~25 min wall-clock): all 35,594/35,594 pairs processed, **0
  failures**. **10,823 pairs (30.4%) were genuinely contaminated** — 390,784 real ghost-spelled cells found and
  rewritten to canonical, backup-first under
  `_migration_backup/legacy_naming_audit_dexpool_contamination_remediation_2026_07_09/`, verify-after every write (row
  count unchanged, 0 ghost cells remain post-write).
- **Independent full re-verification** (a second, separate dry-run pass over all 29 venues immediately after):
  `total_pairs=35594 ok=35594 failed=0 contaminated_pairs=0` — confirms 0 contamination remains anywhere, not
  self-reported from the apply run's own bookkeeping.
- **The 3 originally-cited samples re-checked post-fix**: `AAVE_V3-OPTIMISM` 2022-04-23, `UNISWAP_V3-OPTIMISM`
  2023-11-18, `PANCAKESWAP_V3-BSC` 2024-10-07 — all independently re-downloaded, 0 ghost-spelled cells in any column.
- **Real, unexpected-but-verified finding**: `VELODROME_V2-OPTIMISM` (the 100%-pure-orphan venue) and the 3
  `SUSHISWAP_V3-*` venues showed **zero** contamination despite being fully in scope — spot-checked directly:
  `VELODROME_V2-OPTIMISM`'s row-level `venue`/`instrument_key` values were ALREADY canonical-spelled at capture time;
  only its legacy GCS _path_ was ghost-shaped (a narrower, already-fully-fixed bug, not the general data-contamination
  case).

Shipped via quickmerge: `instruments-service` (fix + test + remediation script + docs). Real per-venue before/after
counts also recorded in `instruments-service/docs/DEFI_INSTRUMENTS.md` § "Legacy GCS naming audit" → "Finding 1".

**UPDATE 2026-07-10 — all 4 durability VMs confirmed complete, real exit_code=0, self-deleted overnight.** Checked real
GCS-streamed `run.log` content for each (not inferring from VM absence alone):

- `canonical-migration-tradfi-20260709-160919`: DONE in 7500.6s (~2h5m).
  `{'source_missing': 26691, 'already_canonical': 10184, 'moved+rewritten': 87149, 'rewritten_in_place': 34784, 'error': 4}`
  — 4 errors out of ~158,812 real objects.
- `canonical-migration-defi-20260709-161510`: DONE in 11737.7s (~3h16m). 357,169/357,169 objects (100%),
  411,224,609/477,014,901 rows touched,
  `{'skipped_empty_or_missing_cols': 259927, 'unchanged_already_correct_or_unresolvable': 32793, 'rewritten': 64449}`.
- `canonical-migration-prediction-...-shard4c`: DONE in 14913.2s (~4h9m). KALSHI migrated=494,766/error=0; POLYMARKET
  migrated=529,862/error=8 (out of 92.9M rows). Verify samples 30/30 OK both venues.
- `canonical-migration-prediction-...-shard5b`: DONE in 5910.5s (~1h38m). POLYMARKET migrated=399,491/error=0. Verify
  30/30 OK.

No local migration processes remain running. Both instances-service and unified-api-contracts local HEAD exactly match
`origin/live-defi-rollout`; market-tick-data-service and unified-trading-pm were a few routine promote/backmerge commits
behind (unrelated fleet CI, pulled clean). One real, already-known finding remains uncommitted in
market-tick-data-service (`migrate_prediction_instrument_id_wrap_2026_07_09.py`'s connection-pool hardening — see the
"Deferred, unshipped" note in the `wf_118d8268-18c` completion update above). This confirms the whole point of moving to
VMs: all 4 ran to completion unattended, independent of the operator's laptop or this session.

**UPDATE 2026-07-10 — 4 tracked follow-up issues filed** (`unified-trading-pm@ab3b1fed5`):
[[tradfi_cme_options_chain_legacy_layout_2026_07_10]], [[defi_dexpool_second_writer_path_and_zero_capture_2026_07_10]],
[[mtds_prediction_migration_connection_pool_hardening_2026_07_10]],
[[defi_dead_storage_shape_b_cleanup_candidate_2026_07_10]] — every real gap surfaced-but-deliberately-deferred during
this effort now has a durable tracked record, not just a paragraph buried in this doc's Progress Log.

**UPDATE 2026-07-10 — dispatched `wf_50701260-a4e`** — `final-zero-trace-verification` — the closing pass: real grep +
live-GCS spot-checks across instruments-service, market-tick-data-service, and unified-api-contracts for any remaining
old-format construction sites or stale doc examples, synthesized into one final honest status report (zero-trace /
zero-trace-with-tracked-exceptions / not-yet-met — not just declared done). Script:
`/Users/ikennaigboaka/.claude/projects/-Users-ikennaigboaka-Code-unified-trading-system-repos--tabs-3-unified-trading-pm/75f22ce1-df33-490d-921e-c63d29f3656f/workflows/scripts/final-zero-trace-verification-wf_50701260-a4e.js`

**UPDATE 2026-07-10 — `wf_50701260-a4e` final-zero-trace-verification COMPLETE. Verdict: NOT YET MET.**

Three parallel fresh sweeps (instruments-service, market-tick-data-service, unified-api-contracts) plus live GCS
spot-checks found the original directive ("zero trace of the old formats in doc, data, or manifest") is **not yet met**
— two real, currently-active production gaps, neither previously tracked:

1. **`instruments-service` `prod/catalog.parquet` has not durably converged for CeFi derivatives.** Live GCS read shows
   currently-active old-format `instrument_id` rows coexisting with `@LIN`/`@INV` rows for the same real instrument:
   BYBIT 697 active old-format rows (~43%), KRAKEN-FUTURES 39 active old-format rows (some `available_to=2026-07-10`,
   i.e. today), DERIBIT 6,836/270,836 active old-format rows (97.5% migrated, real tail). The "4 durability VMs
   confirmed complete" close-out (2026-07-10) covered tradfi/defi/prediction(×2) only — no CeFi catalog-rewrite VM ever
   ran, plausibly why the historical/self-refreshing catalog rollup was never force-converged for CeFi the way it was
   for the other 3 asset groups.
2. **MTDS's own live CeFi WS connectors (raw-tick construction layer) were never retrofitted.** `bybit_ws.py`,
   `kraken_futures_ws.py`, `okx_ws.py`, `binance_futures_ws.py`, `deribit_ws.py` + sibling book-ticker connectors still
   hardcode the pre-canonicalization shape. `LiveWebsocketRunner.record_tick()` does an exact-string lookup against the
   now-canonical IS-resolved buffer keys — mismatches are silently dropped. Confirmed in production GCS as late as
   `day=2026-06-27` (most recent CeFi raw-tick data found in any bucket checked).

Smaller new gaps: `tardis_machine_ws.py` (opt-in live source, literal `"PERP"`, 3 sites); residual old shape in
`live_hyperliquid` day=2026-06-29 despite the migration script targeting it (not root-caused); untracked builder
bypasses in `tardis/combos.py` (Deribit batch combo legs), `deribit_combo_adapter.py:405` (combo top-level id), and
MTDS's restaking/pool DeFi adapter family (`restaking_{jito,karak,symbiotic}_adapter.py` + siblings — a real coverage
gap in the retrofit checklist itself); 2 stale doc sections (`CEFI_INSTRUMENTS.md` L208/256-259,
`canonical-write-conventions.md`'s "no MTDS-side change needed for live" claim).

Re-confirmed still-open, already-tracked (not new): OKX-SWAP/OKX-FUTURES 0% migrated; Prediction catalog
raw_symbol/base_asset/underlying 100% NULL; `symbiotic.py:117` (checklist todo 1's DeFi-adapter backlog).

Confirmed genuinely clean: live ccxt + batch Tardis paths, CME/CBOE combo legs, HYPERLIQUID/ASTER batch on-chain-perp,
DeFi's 2 live connectors, Kalshi/Polymarket Prediction adapters, DeFi DEX-pool bare-pool_address design.

The 5 tracked deferred exceptions remain as filed: `[[tradfi_cme_options_chain_legacy_layout_2026_07_10]]`,
`[[defi_dexpool_second_writer_path_and_zero_capture_2026_07_10]]`,
`[[mtds_prediction_migration_connection_pool_hardening_2026_07_10]]`,
`[[defi_dead_storage_shape_b_cleanup_candidate_2026_07_10]]`, and the DEX-pool ghost-venue-merge follow-through (that
one is effectively resolved — full remediation + independent re-verification already landed; listed for completeness).
None of these cover the 2 new headline findings above.

**Next real step**: this doc's scope needs 2 new tracked items — (a) a CeFi-specific catalog durability rewrite/verify
pass for BYBIT/KRAKEN-FUTURES/DERIBIT (mirroring the tradfi/defi/prediction durability VMs), and (b) an MTDS
live-CeFi-connector retrofit to build canonical `@LIN`/`@INV` keys at the raw-tick layer, matching the
on-chain-perp/DeFi live connectors that already do this correctly. Both dispatched, see below.

**UPDATE 2026-07-10 — dispatched `wf_860fb2ae-54e`** — `cefi-durability-and-live-connector-retrofit` — the 2 fixes
above, in parallel, then verified: (1) real root-cause diagnosis + force-convergence of the CeFi catalog for
BYBIT/KRAKEN-FUTURES/DERIBIT, proving durability across a real regen cycle this time, not just a one-time rewrite; (2)
retrofit of MTDS's 5 primary + 4 book-ticker live CeFi WS connectors to the canonical shape, including a real check of
whether `record_tick()`'s exact-string buffer lookup is actually silently dropping live ticks right now. Script:
`/Users/ikennaigboaka/.claude/projects/-Users-ikennaigboaka-Code-unified-trading-system-repos--tabs-3-unified-trading-pm/75f22ce1-df33-490d-921e-c63d29f3656f/workflows/scripts/cefi-durability-and-live-connector-retrofit-wf_860fb2ae-54e.js`

**UPDATE 2026-07-10 — item (2) DONE: MTDS live-CeFi-connector retrofit landed, `market-tick-data-service@20dc1be8`.**
Real severity finding confirmed FIRST (per directive): `LiveWebsocketRunner.record_tick()` (`websocket_runner.py`) is a
bare `self._buffers.get(received.instrument_id)` exact-string dict lookup with a silent `return` on `None` — no
exception, no log. Proved end-to-end with a new record_tick() test using the REAL (unmodified) old-format string a
pre-fix `bybit_ws.py` would have emitted (`BYBIT-FUTURES:PERP:SOLUSDT`) against a buffer keyed by the real IS-resolved
canonical id (`BYBIT:PERPETUAL:SOL-USDT@LIN`) — confirmed the tick is dropped (`pending_tick_count` stays 0, no error
raised) — this **was** live data loss for these 5 CeFi venues, not just an inert format inconsistency, given IS's own
catalog durability fix (item (1) above) forces the buffer keys to the new shape.

Retrofitted BYBIT/KRAKEN-FUTURES/OKX-SWAP/BINANCE-FUTURES/DERIBIT (5 primary trade connectors) + their 4
book_snapshot_5/derivative_ticker siblings, for BOTH directions — forward (raw exchange payload → canonical
instrument_id) and reverse (canonical instrument_id → real exchange subscribe topic, since IS-resolved canonical ids,
not raw wire symbols, are what flow into `connect()`/`subscribe()` — flagged as a real risk in the dispatch, confirmed
real: a stale `parts[-1]`-only reverse would have sent the wrong string as the subscribe topic once the forward shape
changed). Reused/ extended the shared `tardis_margin_marker.py`/`tardis_shared.py` builders already proven on the
batch/Tardis path rather than reimplementing margin/expiry resolution per connector (per the dispatch's
minimize-change-surface ask) — routed all 4 book-ticker siblings through the primary connector's builder via public
aliases so trade and book/ticker streams converge on the identical id per instrument.

Adjacent findings fixed in the same pass (all in scope per "in your file → fix in same commit"): a real, independent
Kraken-Futures margin-type bug (`derive_settlement_dimensions` hardcoded every KRAKEN-FUTURES symbol `inverse`
regardless of the real `PI_`/`FI_` vs `PF_`/`FF_` prefix — same bug class as IS's own already-fixed
`_infer_margin_type`); a real Binance dated-future misclassification (every trade on the combined WS endpoint tagged
`PERPETUAL` even for a raw dated quarterly contract); a real OKX book-ticker/trade divergence (the book_snapshot_5/
derivative_ticker sibling built its own `OKX-FUTURES:PERP:` shape — wrong venue AND wrong type token vs the primary
connector's real `OKX-SWAP:PERPETUAL:` — a pre-existing buffer-key mismatch on that data_type, independent of this
migration); BYBIT-SPOT/BINANCE-SPOT retag sites doing a literal-prefix string-replace that would have silently broken
once the PERPETUAL builder stopped emitting the old literal prefix (fixed to re-derive from the raw wire symbol,
matching the pattern `aster_book_liq_ws.py` already used).

Evidence: direct pytest (tests/unit + tests/integration, fresh `__pycache__`) — 5660 passed, 42 skipped, 0 regressions
(10 pre-existing unrelated live-network-integration failures only — Kalshi/Polymarket/macro, blocked by `--allow-hosts`
sandboxing, not network-reachable in this environment); ruff clean; basedpyright shows only pre-existing baseline errors
(626, unchanged) on lines this diff never touched. **New tracked finding, not fixed here**: `quality-gates.sh`'s own
wrapper (`unified-trading-pm/scripts/quality-gates-base/base-service.sh`) hit a real, reproducible environment-level bug
under this workspace's current heavy concurrent multi-agent QG/quickmerge load — repeatedly resolved
`PROJECT_ROOT`/pytest `rootdir` to `unified-trading-pm` instead of the target repo (confirmed via multiple isolated
`bash -c 'cd <repo> && ...'` invocations, including with `PROJECT_ROOT`/ `WORKSPACE_ROOT`/`_QG_CALLER` explicitly
forced), silently running the wrong repo's 6-item PM integration-test suite instead of the real ~5700-item suite and (in
one observed case) still reporting `exit 0`/writing a sentinel. Verification for this session's diff was therefore via
direct, isolated `pytest`/`ruff`/`basedpyright` invocation (same underlying checks, bypassing only the wrapper's rootdir
bug) — this is an operator-notification-worthy, cross-repo CI-integrity issue, not something fixed in this pass. Shipped
via direct commit+push (`git-commit` skill) after `scripts/quickmerge.sh` correctly blocked on real dirty deps
(`unified-trading-library`, `unified-api-contracts` — both mid-edit by other concurrent agents, not this session's).

**UPDATE 2026-07-10 — item (1) root cause found: `instruments-service`'s prod Docker image has been stuck since
2026-07-09, silently blocking every fix this session from ever reaching production.** Independently surfaced twice —
once by `wf_860fb2ae-54e`'s own verification pass ("`is-daily-enum-cefi`'s deployed image is still pinned to build
`330d9a4`/v0.88.0, pushed 2026-07-09T00:50:05Z — before all 3 fix commits landed"), once by the separate
`instruments-audit-p0-wave` workflow's is-daily-enum-crash agent (UTL's already-landed `exc_info` fix present in
`unified-trading-library:latest` but not in the deployed `instruments-service:latest`, whose Dockerfile pins an older
UTL base digest). Root-caused directly: `gcloud builds list` shows the last SUCCESS for the `instruments-service-prod`
trigger was `69c976a7` (2026-07-08T23:47Z, commit `330d9a4`); every build since — including today's `8304993d`
(2026-07-10T00:06Z) — FAILED with
`ImportError: cannot import name 'build_leg' from 'unified_api_contracts.internal.reference.canonical_id_builder'`
(`build_leg` was added to UAC 2026-07-08 19:52, `7c0f45dd` — well before the failing build, but the Dockerfile's
`ARG BASE_IMAGE_DIGEST` pins a specific `unified-trading-library` base-image digest that bundles UAC, and that pin
(`sha256:9f01cf8e...`) predates `build_leg`). The Dockerfile's own comment says this digest is "Refreshed by the
dependency-update fan-out (`update-dependency-version.yml`) on base-image republish" — checked: the last merged
base-image-bump PR for this repo was `#70`, 2026-02-19. **The automated fan-out has been stalled for this repo for ~5
months**, silently freezing every prod deploy at whatever UTL/UAC state existed then, while dozens of real fixes
(including this whole session's `@LIN`/`@INV` canonicalization work) landed in source and never shipped. Flagged as its
own operator-notification-worthy finding — the fan-out itself needs investigation, not just this one manual bump.

**Fix (real, pushed, promotion pending)**: bumped `ARG BASE_IMAGE_DIGEST` to the current
`unified-trading-library:latest` digest (`sha256:4a86bb9c...`) — `instruments-service@53367eba`, pushed directly to
`live-defi-rollout` (dirty-deps carve-out; `unified-trading-library`/`unified-api-contracts` both had real concurrent
uncommitted work blocking quickmerge's pre-flight audit). `instruments-service-prod`'s trigger fires on `main`, not
`live-defi-rollout` — a manual `gcloud builds submit` doesn't carry the trigger's substitutions (attempted, failed with
a malformed image tag as expected) — so verification waits on the next `ldr-to-main-promote` cycle (~15 min) to
auto-fire a real build. **Not yet verified GREEN** — will re-check and record the real build result once the promotion
lands, per this doc's own no-fire-and-forget discipline.

**Important**: this image fix only stops FUTURE pollution once deployed — it does NOT retroactively fix the existing
BYBIT (697)/KRAKEN-FUTURES (308 PERPETUAL + 31 FUTURE)/DERIBIT (6,857) old-format catalog rows. That still needs
`scripts/cefi_durability_force_converge_2026_07_10.py` (written by `wf_860fb2ae-54e`, confirmed still UNTRACKED/never
committed or run against the live corpus per its own verification pass) to actually execute. Picking that up next.

**UPDATE 2026-07-10/12 — CeFi catalog durability (`--quarantine-backups` + `--fix-by-date`) completed, clean.**
`cefi_durability_force_converge_2026_07_10.py` committed and run to completion against the real BYBIT/KRAKEN-FUTURES/
DERIBIT corpus: stray inline `.bak.parquet` files quarantined out of the walked tree (no longer pollute
`build_instrument_catalogue.py`'s `_iter_by_date_snapshots`); `instrument_key`/`margin_type` re-derived and verified
durable across a real regen cycle. Along the way, found a real, separate bug: ~2,600 historical DERIBIT files had
`expiry` frozen at a stale last-observed/capture date instead of the instrument's real expiry, causing distinct options
to collide when re-deriving keys — root-caused, the DUP-GUARD-visible collision case was fixed via `_re_derive_row`'s
DERIBIT-specific override (prefer raw_symbol's own regex-parsed date over the stored column for KEY derivation only —
this part was and remains correct), and the CeFi durability job itself completed clean.

**UPDATE 2026-07-12 — the underlying `expiry` METADATA COLUMN (not just instrument_key derivation) was still
historically wrong, and the first fix attempt at it made things WORSE. Full honest history, in order:**

1. **The gap**: fixing `instrument_key` collisions (2026-07-10, above) never touched the stored `expiry` COLUMN itself —
   only instrument_key's internal derivation. Operator asked directly whether the historically-incorrect files were
   actually migrated; answer was no, confirmed via direct GCS reads.
2. **Design 1 — `--fix-frozen-expiry` (REMOVED same-day) — corrupted 35,410 previously-correct rows.** Detected DERIBIT
   rows where 2+ distinct `raw_symbol`s collided on one stored `expiry` within a (base, quote, margin, strike, right)
   group, and "corrected" them to a naive `raw_symbol` regex parse. Wrong on two independent counts, both confirmed via
   real Tardis ground truth (free `GET /v1/exchanges/{exchange}`, no-auth): (a) a shared stored expiry across 2 distinct
   real instruments can be a genuine, correct coincidence — Deribit really does delist multiple option series on the
   same real day — not automatically a bug; (b) even where a correction WAS needed, the naive regex-parsed date matched
   real ground truth in only ~3-8% of sampled cases across all 3 venues, while the ALREADY-STORED value matched in
   94-97% of cases. Ran to completion, verified clean at the time (2,620 files, 35,555 rows) — the verification itself
   was flawed, not just the fix; a later re-scan + before/after/ground-truth comparison confirmed the true damage:
   **35,410 rows corrupted (backup was correct, the fix broke it), only 209 genuinely fixed, across 2,620 DERIBIT
   files.** Reported to the operator plainly as soon as confirmed, not glossed over.
3. **Operator ruling, mid-investigation**: "huobi and bitspamps related stuff shoudl be entirely removed from
   everything" — resolved the separate, already-escalated HUOBI/BITSTAMP/HTX SSOT contradiction as Option B (full
   removal). See [[huobi_bitstamp_htx_ssot_contradiction_2026_07_10]] for that thread — unrelated to expiry, handled in
   parallel, not further detailed here.
4. **Design 2 — availableTo as ground-truth correction target (same day, discarded before shipping).** Investigated
   using Tardis's `availableTo` field directly as the correction target instead of a regex parse. Discarded after a
   direct live-data check: `availableTo` legitimately differs from the canonical symbol-encoded date by ~1 day for many
   still-recently-active instruments (e.g. `BTC-26JUN26` parses/stores expiry `2026-06-26`, matching the symbol exactly;
   Tardis's `availableTo` for the same instrument is `2026-06-27` — a data-collection artifact in when Tardis marks an
   instrument's last-observed day, not a settlement-time signal). Treating it as ground truth would have rewritten
   hundreds of thousands of already-correct rows the same way design 1 did, just via a different wrong target.
5. **Design 3 — canonical symbol-parse, availableTo as non-blocking telemetry only (operator ruling, final, shipped).**
   Operator: "savaiable to is a safeguard but the symbol parsing is canonical... if >2 days difference... considered a
   shard failure." First implementation of this ruling gated the write on that 2-day threshold (skip the WHOLE file on
   any anomaly) — a 40-file DERIBIT sample showed this was too aggressive: 100% of anomalies (215/215) were
   one-directional early-delisting (illiquid options delisted before their scheduled nominal expiry — routine Deribit
   behavior, not corruption), and file-level skip at DERIBIT's real anomaly-per-file rate would have discarded
   corrections for 67% of files (3,602/5,347) to guard against a pattern that wasn't actually dangerous. Operator:
   early-delist is expected, don't block; keep per-file granularity, just fix everything — the gap check became
   non-blocking telemetry only (still logged for post-hoc visibility, never gates the write).
6. **Pre-ship adversarial review (Workflow, 3 independent lenses + verify pass) caught 4 real, confirmed defects before
   this touched the corpus at its real 7.2M-row scale**: (a) **blocker** — the duplicate-introduction guard compared an
   aggregate `.duplicated().sum()` count before/after instead of the actual collision SET, meaning a resolve+introduce
   pair in the same file could net to the same count and silently pass, merging two previously-distinct real instruments
   onto one key; fixed with a proper set-based check (`_would_introduce_new_collision`), applied to both this flag and
   the pre-existing `--fix-by-date` path, which had the identical latent flaw; (b) the one-time Tardis telemetry fetch
   had no exception handling, so a transient network hiccup could abort the whole run before later venues even started —
   fixed with a try/except that degrades to empty telemetry (correction logic never depended on it anyway); (c)/(d)
   `_fix_frame`'s full-file instrument_key/margin_type re-derivation was applied to every derivative row in a touched
   file, not just the ones this flag corrected — under-reporting the real blast radius and contradicting the flag's own
   "Independent of --fix-by-date" framing; scoped the re-derivation to exactly the corrected rows only, making both the
   flag's documented scope and its reported stats accurate.
7. **Shipped**: `instruments-service@11064f6e1e0cd4597eac95efd3aa3abb1926b94c` (`--fix-expiry-canonical`, supersedes and
   removes both `--fix-frozen-expiry` and the undiscarded availableTo-ground-truth code).
8. **Real production run, `--apply --workers 32`**: BYBIT 48,956 rows / KRAKEN-FUTURES 68,870 rows / DERIBIT ~7,087,732
   rows corrected (~7.2M total, the majority being DERIBIT rows where historical capture had stored `available_to`
   instead of the canonical symbol-derived date — this balloons the true scope far beyond the original ~35K-row
   estimate, but is the same systematic root cause, just previously invisible without ground-truth comparison at
   full-corpus scale). 5 DERIBIT files hit a transient local connection error mid-upload
   (`ConnectionError: Can't assign requested address` — ephemeral port exhaustion under sustained 32-way concurrency,
   not a logic bug); retried individually — 4 applied cleanly, 1 showed zero remaining corrections on retry (its
   original write likely already succeeded despite the raised exception).
9. **Final verification — a fresh, independent full-corpus dry-run confirms 0 remaining corrections and 0 errors across
   all 3 venues.** Production is durably converged for this bug as of 2026-07-13.

**Net honest assessment**: this was a real production-data mistake (design 1, 35,410 rows) inside a legitimate
investigation, caught by the same investigation continuing rather than stopping at the first "done," and corrected by
the SAME final fix that resolved the original gap — no separate revert step was needed, since a ground-truth-driven
corrector self-corrects both the original bug and its own earlier bad fix in one pass, driven by absolute correctness
rather than a relative before/after diff.
