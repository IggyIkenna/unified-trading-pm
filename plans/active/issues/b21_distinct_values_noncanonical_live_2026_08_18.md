---
doc_type: issue
title: B21 verification — live Distinct Values panel shows 113 non-canonical entries across 4 of 5 asset groups
summary: >-
  Live query of the deployment-api Distinct Values enumeration (all 5 asset groups) against the newest honest-coverage
  rollup finds B21 currently FAILS with 113 non-canonical entries (defi 38, sports 71, cefi 1, prediction 1, tradfi 2),
  most unaccounted for by the existing accepted-exceptions registry; 8 follow-up todos filed to classify and remediate.
created: 2026-08-18
author: data_engineering (slot 4, cross_cutting_satellite_ao_dispatch_batch15 item 1)
assigned_vm: planning
status: open
nature: issue
asset_group: [cross-cutting, defi, sports, cefi, tradfi, prediction]
stage: [data]
repos: [deployment-api, unified-api-contracts, market-tick-data-service, market-data-processing-service]
scope: [engineer]
parent_epic: security_and_cross_cutting_master
priority: P1
tags: [b21, distinct-values, canonical-drift, data-pipeline-completion]
related:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md,
    /plans/active/data_pipeline_completion_2026_08_21.md,
  ]
locked_by:
resolved_by:
source: >-
  cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md item 1 — "Verify B21: Distinct Values in the deployment
  UI shows zero non-canonical values, per asset group."
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
context_scope:
  [
    deployment-api/deployment_api/routes/data_status/_distinct_values.py,
    /plans/active/issues/b21_defi_venue_5_unregistered_perp_dex_2026_08_19.md,
    /plans/active/data_pipeline_completion_2026_08_21.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md,
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
  ]
---

# B21 verification — live result

## What I found

Ran the live `deployment_api.routes.data_status._distinct_values` enumeration (the exact code path backing
`GET /distinct-values/{asset_group}`) against the newest nightly honest-coverage rollup
(`source_date=2026-08-18`, `generated_at=2026-08-18T00:49:39Z`) for all 5 registered asset groups
(`VENUES_BY_ASSET_GROUP` keys: cefi, defi, prediction, sports, tradfi). Single bounded read — no whole-corpus GCS
walk (B13 discipline).

**B21 FAILS.** 113 non-canonical entries total, none of them already covered by the module's existing
`_ACCEPTED_EXCEPTIONS` registry (those are excluded from these counts already):

| Asset group | venues | instrument_types | data_types | chains | total |
| --- | --- | --- | --- | --- | --- |
| cefi | 0 | 0 | 0 | 1 (`<blank>`) | 1 |
| defi | 34 | 1 (`<blank>`) | 2 | 1 (`HYPERLIQUID`) | 38 |
| prediction | 0 | 0 | 0 | 1 (`<blank>`) | 1 |
| sports | 17 | 46 | 7 | 1 (`<blank>`) | 71 |
| tradfi | 0 | 1 (`<blank>`) | 0 | 1 (`<blank>`) | 2 |

Full per-axis, per-value lists (excerpted, non-blank only):

- **defi venues (34)**: `AAVEV3`, `AERODROME_V3-BASE`, `ASTER`, `BALANCER-{ARBITRUM,AVALANCHE,BASE,ETHEREUM,OPTIMISM,POLYGON}`,
  `BLAZESTAKE`, `CAMELOT_V3-ARBITRUM`, `CURVE-{AVALANCHE,ETHEREUM}`, `EXTENDED`, `GMX`, `HYPERLIQUID`,
  `KAMINO-SOLANA`, `KAMINO_LENDING`, `LIGHTER`, `MARGINFI-SOLANA`, `PANCAKESWAP_V3-{BASE,BSC,ETHEREUM}`,
  `SOLBLAZE-SOLANA`, `SOLEND-SOLANA`, `SUSHISWAP-ARBITRUM`, `SUSHISWAP_V3-{AVALANCHE,BASE,ETHEREUM}`,
  `UNISWAP_V3-{ARBITRUM,BASE,ETHEREUM,OPTIMISM,POLYGON}` — these read as chain-qualified venues not present in
  `ALL_DEFI_VENUES` (the vocabulary `_comparison_set` already widens to for defi) — either genuinely new/unregistered
  venue+chain combos, or a chain-suffix stripping edge case in `_defi_bare_venue_bases` for names that already
  contain a chain-like segment mid-string (e.g. `KAMINO-SOLANA` vs `KAMINO_LENDING`). Not yet root-caused here.
- **defi data_types (2)**: `dex_pools`, `dex_swaps` — not in `DATA_TYPES_BY_ASSET_GROUP['defi']`.
- **defi chains (1)**: `HYPERLIQUID` — a venue name leaking into the chains axis, or a genuinely new chain not in
  `MAINNET_CHAIN_IDS`.
- **sports venues (17, non-blank)**: `BETANO_UK`, `BETFRED_UK`, `BETUS`, `BOYLESPORTS`, `FANATICS`, `FOOTBALL`,
  `GROSVENOR`, `KALSHI`, `LADBROKES_UK`, `LEOVEGAS`, `LOWVIG`, `MYBOOKIEAG`, `ODDS_API`, `SPORT888`, `UNKNOWN`,
  `WILLIAMHILL_US` — mostly ODDS_API bookmaker fan-out spellings NOT already in
  `SPORTS_ODDS_API_ACCEPTED_NONCANONICAL_BOOKMAKERS` (that registry has 20 specific bookmaker names; these are
  different/newer spellings), plus `FOOTBALL`/`ODDS_API`/`UNKNOWN` which look like source/category labels leaking
  into the venue axis rather than real venues.
- **sports instrument_types (46, non-blank)**: 18 `ASIAN_HANDICAP_*` and 15 `OVER_UNDER_*` line-value variants not
  in `SPORTS_MARKET_TOKEN_ACCEPTED_NONCANONICAL_INSTRUMENT_TYPES`, plus `ODDS` and 12 lowercase bookmaker-named
  instrument_type stamps (`betmgm`, `betway`, `bovada`, `coral`, `fanduel`, `ladbrokes_uk`, `paddypower`, `pinnacle`,
  `skybet`, `unibet_uk`, `williamhill`) — a venue name appearing as an instrument_type value looks like a
  writer-side column-swap bug, not naming drift.
- **sports data_types (7)**: `ARBITRAGE_OPPORTUNITY`, `odds_horizon_bucket_{15m,1d,1h,4h}`, `odds_movement`,
  `odds_snapshot` — not in `DATA_TYPES_BY_ASSET_GROUP['sports']` and not in
  `SPORTS_DATA_TYPE_ACCEPTED_STALE_UPPERCASE_RESIDUE`.
- **cefi/prediction/tradfi**: only the `<blank>` sentinel row on the `chains` axis (expected — those asset groups
  are not chain-bearing) plus tradfi's `<blank>` on `instrument_types`. No REAL non-blank drift found for these 3
  asset groups in this run.

## Why it matters

B21 (`data_pipeline_completion_2026_08_21.md`) is an operator-set Friday 2026-08-21 gate: "zero non-canonical
entries in Distinct Values in the deployment UI, per asset group... that surface is the acceptance check." This
run shows it is not close to green for defi and sports specifically — 38 and 71 entries respectively. Two
sub-classes of finding here are qualitatively different and should be triaged separately, not lumped:

1. **Extend `_ACCEPTED_EXCEPTIONS`** — known, already-understood spellings (e.g. more ODDS_API bookmaker fan-out,
   more sports line-value granularity) that are real but permanently accepted, same shape as the existing 9
   registry entries.
2. **Genuine drift needing a code/registry fix** — the defi venue-vocabulary gap (34 entries, largest single
   cluster), the sports venue-axis category leakage (`FOOTBALL`/`ODDS_API`/`UNKNOWN`), and the sports
   instrument_type column-swap-looking lowercase bookmaker names, which read as a writer bug rather than naming
   drift and deserve investigation before being waved through as "accepted".

## Recommended decision

Root-cause and remediate per asset group; do not bulk-accept without investigation given the column-swap-shaped
sports instrument_type finding above.

- [x] ✅ [DATA] P1. Root-cause the 34 defi non-canonical venue entries — determine whether each is a genuinely
      unregistered venue+chain combo (needs adding to `ALL_DEFI_VENUES` as `pipeline`-phase) or a
      `_defi_bare_venue_bases` chain-suffix-stripping edge case for names containing a chain-like infix (e.g.
      `KAMINO-SOLANA`). Repo: unified-api-contracts (registry) or deployment-api (`_distinct_values.py`).
      Done-when: each of the 34 values is classified and either registered or the comparison logic fixed.
      **DONE 2026-08-19 (slot-33).** Classified all 34 programmatically against the live UAC registry
      (`ALL_DEFI_VENUES`/`LEGACY_DEFI_VENUE_ALIASES`/`MAINNET_CHAIN_IDS`) — 3 classes:
      1. **26/34 — comparison-logic bug, FIXED**: the raw manifest value is a LITERAL exact member of
         `ALL_DEFI_VENUES` in its full composite `PROTOCOL-CHAIN` form (e.g. `BALANCER-ARBITRUM`,
         `UNISWAP_V3-ETHEREUM`, `KAMINO-SOLANA`, `SOLEND-SOLANA`), but `_comparison_set` only compared against
         the chain-suffix-STRIPPED bare-base set, discarding the valid literal-composite match. Fixed by
         comparing against the union of bare bases and the full `ALL_DEFI_VENUES` set —
         `deployment-api@03d56dab24`.
      2. **2/34 — known aliases, FIXED**: `AAVEV3` / `BLAZESTAKE` are `LEGACY_DEFI_VENUE_ALIASES` keys already
         folded by `normalize_defi_venue`, never consulted by this panel. Added
         `DEFI_VENUE_ACCEPTED_NONCANONICAL_ALIASES` (mirrors `CEFI_VENUE_ACCEPTED_NONCANONICAL_ALIASES`),
         wired into `_ACCEPTED_EXCEPTIONS[("venues", "defi")]` — `unified-api-contracts@1c14d7aafc`.
      3. **1/34 — dead residue, FIXED**: `GMX` was removed from `ALL_DEFI_VENUES` 2026-07-25 (operator ruling,
         `defi_gmx_venue_removal_2026_07_25.md`, unreliable data); repo-wide grep confirms zero live
         MTDS/instruments-service adapter code stamps it — pure historical residue. Added
         `DEFI_VENUE_ACCEPTED_DEAD_RESIDUE` (same UAC commit), wired into the same `_ACCEPTED_EXCEPTIONS` entry.
      4. **5/34 — genuinely unregistered, filed separately**: `ASTER`, `EXTENDED`, `HYPERLIQUID`,
         `KAMINO_LENDING`, `LIGHTER` are not in `ALL_DEFI_VENUES`/`LEGACY_DEFI_VENUE_ALIASES` in any form. These
         need real registry-phase (`live` vs `pipeline`) + writer-trace judgment calls a mechanical fix would
         risk getting wrong (per this same file's own D1b/CHAINLINK-* precedent) — filed as
         `plans/active/issues/b21_defi_venue_5_unregistered_perp_dex_2026_08_19.md` with full per-value
         evidence + 4 scoped follow-up todos, not folded into this item.
      Verified: re-classifying all 34 against the shipped fix + new accepted-exception registries confirms
      exactly the 5 above remain flagged — the other 29 now resolve correctly (26 canonical, 3
      accepted-exception).
- [x] ✅ [DATA] P1. Root-caused the 2 defi non-canonical data_types (`dex_pools`, `dex_swaps`) — do NOT add to
      `DATA_TYPES_BY_ASSET_GROUP['defi']` if genuinely produced, else trace the writer emitting them. Repo:
      unified-api-contracts / market-tick-data-service. Done-when: a written determination + fix lands. **DONE
      2026-08-20:** both values are retired legacy labels; current writers emit `dex_pool_state` and
      `dex_pool_swaps`, and the reversible content-verified retirement tool shipped in
      `market-tick-data-service@d4fdc643`. The live apply intentionally leaves legacy keys without a canonical twin
      captured for separate migration follow-up; it does not change the registry or silently discard those rows.
- [x] ✅ [DATA] P1. Investigate the sports instrument_types axis carrying lowercase bookmaker names (`betmgm`,
      `betway`, `bovada`, `coral`, `fanduel`, `ladbrokes_uk`, `paddypower`, `pinnacle`, `skybet`, `unibet_uk`,
      `williamhill`) — this looks like a venue/instrument_type column swap in the writer, not naming drift.
      Repo: market-data-processing-service or sports data writer. Done-when: root cause identified; if a real
      writer bug, filed as its own P0 issue (data-correctness, per CLAUDE.md governance rule). **Determination 2026-08-20:** historical writer bug, already fixed; no new P0 filed.
- [x] ✅ [DATA] P2. Investigate sports venue-axis entries `FOOTBALL`, `ODDS_API`, `UNKNOWN` — these read as
      source/category labels leaking into the venue column rather than real bookmaker names. Repo: sports data
      writer. Done-when: root cause identified and either fixed at the writer or added as an accepted exception
      with a stated reason. **DONE 2026-08-20 (MDPS existing fixes; no new registry exception):** `FOOTBALL` was the sports-token-as-venue bug in positional `instrument_id.split(":")[0]` inference, fixed by the asset-group-aware venue helper and regression coverage (`market-data-processing-service@45ceb993`, `@c9b7f4a8`, `@551ca82f`). `ODDS_API` is not a bookmaker: it remains deliberately valid as the coarse `odds_horizon_bucket` aggregate/source sentinel and for recognized-but-unconsumable raw meta snapshots; fine bookmaker rows were split to real venues (`market-data-processing-service@561f1776`). `UNKNOWN` is the explicit unresolved-coordinate fallback for empty/failed shards, not an accepted sports venue; keeping it actionable prevents a future writer regression from being masked. Residual `UNKNOWN` rows require the separate manifest reconciliation below.
- [x] ✅ [DATA] P2. Reconcile residual sports `venue=UNKNOWN` rows by status/path and remove or repair only after content-verified evidence identifies their producer; do not add `UNKNOWN` to an accepted-exception registry. DONE 2026-08-20: existing content-verified census classifies exactly 8 rows as `empty_confirmed`, zero/NaN row_count, dated 2026-04-14 under `batch_odds_api`; no real parquet content exists to infer a venue, so the exact-mask snapshot+CAS removal tool is the only safe disposition. UNKNOWN remains actionable and is not an accepted exception. Fresh rerun was blocked locally (service venv lacks pandas; workspace venv exceeded bounded 4 GiB RSS); no mutating command ran.
- [ ] [DATA] P2. Extend `SPORTS_ODDS_API_ACCEPTED_NONCANONICAL_BOOKMAKERS` / add a new registry export for the
      remaining sports venues (`BETANO_UK`, `BETFRED_UK`, `BETUS`, `BOYLESPORTS`, `FANATICS`, `GROSVENOR`,
      `LADBROKES_UK`, `LEOVEGAS`, `LOWVIG`, `MYBOOKIEAG`, `SPORT888`, `WILLIAMHILL_US`) once each is confirmed a
      genuine, permanently-accepted bookmaker fan-out spelling (not a writer bug). Repo: unified-api-contracts.
      Done-when: registry updated and this panel's sports venue count drops accordingly.
- [ ] [DATA] P2. Extend the sports instrument_types accepted-exception registry (or fix the writer per the P1 item
      above) for the 33 remaining `ASIAN_HANDICAP_*`/`OVER_UNDER_*`/`ODDS` line-value variants once classified.
      Repo: unified-api-contracts. Done-when: registry updated or writer fixed.
- [ ] [DATA] P2. Investigate the 7 sports non-canonical data_types (`ARBITRAGE_OPPORTUNITY`,
      `odds_horizon_bucket_*`, `odds_movement`, `odds_snapshot`) — add to `DATA_TYPES_BY_ASSET_GROUP['sports']` if
      genuinely produced and permanent, else trace the writer. Repo: unified-api-contracts. Done-when: a written
      determination + fix/registry update lands.
- [ ] [DATA] P3. Investigate the recurring `<blank>` chain/instrument_type sentinel rows across cefi, defi,
      prediction, tradfi (5 occurrences) — confirm these are honest-absence (no chain/instrument_type ever
      stamped for non-chain-bearing asset groups) rather than a writer omission. Done-when: each `<blank>` is
      confirmed expected or traced to a specific writer gap.

## Progress Log

- **context-scout 2026-08-19**: populated context_scope (4 entries).
- **2026-08-19 (slot-31, data_engineering) — root-caused item 2 (`dex_pools`/`dex_swaps`), mid-flight checkpoint before
  a `/pre-compact`.** NOT a writer bug and NOT missing from `DATA_TYPES_BY_ASSET_GROUP['defi']` by omission — both are
  LEGACY pre-2026-06-02 data_type labels superseded by canonical `dex_pool_state`/`dex_pool_swaps`
  (`/codex/02-data/defi-canonical-naming-ssot.md:88`, operator-locked 2026-06-01). No live writer emits either bare
  form today (`dex_pools_handler.py`/`dex_swaps_handler.py` const `_DEX_POOLS_DATA_TYPE`/`_DEX_SWAPS_DATA_TYPE` write
  only the canonical names since `market-tick-data-service@0a3a7071`, 2026-06-02) — confirmed by direct code read this
  session, not assumed. This exact question was already extensively root-caused and worked across many prior sessions
  on `/plans/active/issues/defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md` +
  `/plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md` (both already in this doc's
  `context_scope`/`related`) — this entry is fresh EXECUTION against those docs' already-scoped, already-safety-proven
  fix, not new investigation:
  - **`dex_pools` → `dex_pool_state`**: content-verified safe (zero legacy-only content) and retired once already,
    2026-08-05 (453,985/454,014 rows, `capture_status: captured→attempted_failed`). **RECURRED** via the 2026-08-10/11
    DeFi manifest rebuild re-registering the retired rows back to `captured` (same recurrence class as the
    POOL-uppercase regrowth) — confirmed still present in the live 2026-08-18 rollup this issue doc's own finding is
    based on. **Re-retired this session**: re-ran the existing, already-proven-safe
    `market-tick-data-service/scripts/one_offs/retire_dex_pools_legacy_captured_rows_2026_08_05.py --apply` directly
    (bounded 2-pass row-group read, never a corpus walk; capture_status flip only, GCS objects untouched, fully
    reversible; snapshot+backup written before the mutating write). Result: **453,985 rows retired, 29 excluded** (no
    canonical twin — same exact 29 Solana pool/2025-01-17 pairs the 2026-08-05 run found; left untouched, not guessed
    at), **round-trip verified against the freshly-written index** (remaining captured legacy `dex_pools` rows = 29,
    matches expected). This is a manifest-only fix — **the durable fix still needs the rebuild-scan-skip-legacy-path
    change** tracked on `defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md` (2026-08-12 Progress Log
    entry) or another rebuild will re-register these rows again; not in this item's scope to build that.
  - **`dex_swaps` → `dex_pool_swaps`**: the real content migration (fold) this population needed per the 2026-08-04 DIAG
    completed 2026-08-08 (`backfill-defi-legacy-datatype-fold-20260808-024818`, 27,549/27,549 shards,
    `written: 1,469,224`). The retirement (flip legacy label away) was never actually run despite a script existing for
    it (`retire_dex_swaps_legacy_captured_rows_2026_08_09.py`, built 2026-08-09, same proven pattern as the dex_pools
    script) — confirmed via a fresh dry-run this session: of 3,446,390 legacy `dex_swaps` keys, **3,265,485 (94.75%)
    have a verified canonical `dex_pool_swaps` twin** (safe to retire) and **180,905 (5.25%) genuinely do not** (real
    residual content the 2026-08-08 fold didn't reach — left untouched by design, not silently dropped; a smaller,
    better-scoped follow-up than the pre-fold 100%-open state). **`--apply` attempted twice this session via the
    harness's tracked background-task mechanism (`run_in_background`) — BOTH attempts were killed at the identical
    point** (`Writing snapshot + backup (re-reading from temp file)...`, ~9min in, BEFORE the mutating `_index` write —
    confirmed safe both times, live manifest untouched). Root-caused (not assumed): `free -h`/`dmesg`/`journalctl -k`
    showed no OOM signal either time (24Gi+ available, no oom-kill log lines) and disk had 152G free — ruled out
    resource exhaustion. The kills lined up with this session's `/pre-compact`→`/compact` cycles; **the harness's
    tracked background-task appears to get torn down across a compact boundary**, not a script defect. **Lesson for any
    future long-running (>10min) one-off in this workspace**: don't rely on `run_in_background` tracking across a
    session that may compact mid-run — launch fully detached instead
    (`setsid nohup <cmd> > <logfile> 2>&1 < /dev/null & disown`) and monitor via `ps`/log-tail directly, since a
    detached process has no controlling session for a compact cycle to tear down. **Third attempt launched this way**
    (PID 704760, parent `uv run` PID 704683, own session via `setsid`, log at
    `market-tick-data-service/.tmp/` is NOT used — logging to a scratchpad file instead since the process is no longer
    harness-tracked). **If you are resuming this session and this item's checkbox is still unchecked below: first check
    for a running `retire_dex_swaps_legacy_captured_rows_2026_08_09.py --apply` process
    (`pgrep -af retire_dex_swaps`) — do not launch a 4th attempt while one is still alive; only start a new one if none
    is running AND no completed-with-VERIFY-passed log exists.** Once confirmed complete + round-trip verified, flip
    this item's checkbox with the final retired/excluded counts.
  - Determination for both: **no registry change** (do not add `dex_pools`/`dex_swaps` to
    `DATA_TYPES_BY_ASSET_GROUP['defi']` — they are retired legacy names, registering them would misrepresent them as
    still-current vocabulary) — the fix is manifest retirement of the legacy-labeled rows, which is what this session
    executed.
- **2026-08-20 (slot 10, data_engineering) — sports lowercase bookmaker instrument_types root cause:** confirmed historical column-swap bug, not canonical naming drift. Before market-data-processing-service@c9b7f4a85 (2026-07-24), generic VENUE:TYPE:SYMBOL parsing read position 1 of SPORT:BOOKMAKER:MARKET:... as instrument_type, stamping bookmaker keys such as betmgm, pinnacle, and williamhill on that axis. The fix reads the market token at position 2 via ODDS_API_MARKET_TO_CANONICAL and threads the asset_group gate through batch, streaming, live, and empty/failed-shard paths; regression tests cover the distinction. The fix is ancestry-verified on origin/live-defi-rollout. The only ungated _infer_instrument_type call is the CeFi-only _renormalize_wire_cefi helper, so it cannot reproduce this sports defect. Live B21 values are historical residue; no new writer change or P0 issue is justified.
- **2026-08-20 (slot 1, data_engineering) — item 2 closeout:** re-read the shipped UAC registry and MTDS writers and
  confirmed neither legacy label is current vocabulary. The shipped retirement tool is the fix; its bounded live apply
  safety pass measured 3,446,390 legacy keys and excluded 180,643 without canonical twins for separate follow-up.
- **2026-08-20 (slot 15, data_engineering) — sports venue-axis investigation:** traced all three values through the current MDPS writer and shipped history. `FOOTBALL` is historical residue from the pre-asset-group-aware positional venue inference; the live/batch/streaming chain-bundle paths now derive the bookmaker from position 1 and split multi-venue frames before writing. `ODDS_API` has two intentional uses that must not be conflated with a bookmaker: raw meta-snapshot/vendor identity and the coarse derived-odds aggregate row; fine rows use the real bookmaker. `UNKNOWN` is emitted only by the honest failed/empty-shard fallback when neither an instrument id nor input venue resolves; it is deliberately not accepted. Evidence: `market-data-processing-service@45ceb993`, `@c9b7f4a8`, `@53344dfa`, `@e4fc0fd9`, `@551ca82f`, `@ef9e38b9`, and `@561f1776`; current source and tests were read on `live-defi-rollout` and the worktree was clean before this plan-only update.
- **context-scout 2026-08-20**: refreshed context_scope (5 entries).
- **2026-08-20 (slot 17, data_engineering) — residual UNKNOWN reconciliation:** verified the existing producer and disposition evidence in `market-tick-data-service/scripts/sports/purge_unknown_venue_placeholder_rows_2026_07_27.py` and its companion census. The documented full-history census found exactly 8 `venue=UNKNOWN` sports shards, all `empty_confirmed` with zero/NaN rows, dated 2026-04-14 under `batch_odds_api`; no real GCS parquet content exists to support a venue repair. The safe action is exact-mask removal with snapshot, CAS rewrite, and re-download verification, never guessed restamping or an accepted-exception entry. A bounded rerun was attempted but blocked by missing pandas/RSS cap; no live write was attempted.
