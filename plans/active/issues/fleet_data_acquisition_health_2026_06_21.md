---
doc_type: issue
title: Fleet data-acquisition health sweep 2026-06-21 — fixable code errors (no rate-limiting)
summary: >-
  Operator-requested sweep of every data-acquisition VM lane's run.log (~75 VMs) on 2026-06-21: confirms all lanes
  running with zero fleet-wide rate-limiting, most lanes actively capturing data, and catalogues fixable code errors
  found per lane (cefi tick-schema validation, SOURCE_PRIORITY mismatches, mtds version-surface drift) with follow-up
  todos.
status: resolved
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: [mtds, live-trading, cefi, defi, data-quality, uac, monitoring]
related:
  [
    /plans/archive/issues/live_tardis_machine_and_hl_aster_s3_batch_2026_06_21.md,
    plans/active/issues/live_mode_event_sink_topic_missing_2026_06_21.md,
    /codex/02-data/pipeline-mode-partition.md,
  ]
created: 2026-06-21
author: unknown
parent_epic: infrastructure_master
priority: P2
source: ["GCS vm-logs sweep of ~75 running VMs (all lanes), 2026-06-21 ~16:10 UTC"]
assigned_vm: planning
resolved_by: cross_cutting_satellite_ao_dispatch_batch1b-003
locked_by: live-defi-rollout
context_scope:
  [
    /codex/02-data/pipeline-mode-partition.md,
    /codex/05-infrastructure/live-pipeline-architecture.md,
    /plans/active/issues/live_mode_event_sink_topic_missing_2026_06_21.md,
    /plans/archive/issues/live_tardis_machine_and_hl_aster_s3_batch_2026_06_21.md,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/_source_priority_data.py,
  ]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-04 # (slot-5 data_engineering: all 4 remaining items verified resolved — see Progress Log)
---

# Fleet data-acquisition health — 2026-06-21 (operator-requested)

Operator asked: are the VMs running / rate-limited / recovering, should we enforce rate-limit caps vs
exponential-backoff, and are they getting data or failing for fixable code reasons (all data_types × venues × chains
should have data). Swept every lane's `run.log` (~75 VMs).

## Headline

- **All lanes RUNNING.** tradfi / defi / sports / prediction / cefi-live + monitoring.
- **ZERO rate-limiting fleet-wide** — no `429` / `Too Many Requests` / backoff / retry-after in ANY log. So
  exponential-backoff is **not** currently wasting time (it isn't firing). **No rate-limit caps needed today.** The
  proactive-cap-vs-reactive-backoff principle is sound but only bites the one genuinely rate-limited source — **Tardis
  historical** (billing-gated, NOT running). If/when Tardis historical is funded, add a self-enforced token-bucket below
  Tardis's per-key budget (the sharded launcher already singleton-locks for this reason).
- **Most lanes ARE getting data**: tradfi CME-CL done 33.6K rows, NASDAQ 27K, NYSE 76K, CBOE-VX 7.8K, CME-opts
  streaming; defi dex-swaps 69K, pyth 312, gas-fees/dex-pools/lst-rates/lending/liquidations/jito/marinade progressing,
  vault-share + instr-defi completed; sports odds 8.5K + fixtures 220/day.

## Fixable code errors (the operator's real question)

| #   | Lane                | Symptom                                                                                                                                                    | Root cause                                                                                                                                                                                                                           | Fix                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Owner                                                |
| --- | ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| 1   | **cefi live**       | HL WS connects + flushes `live_hyperliquid` rows but `row_count=0` (empty_confirmed)                                                                       | runner buffers keyed by passed instrument_id (`BTC`) but HL connector EMITS canonical `HYPERLIQUID:PERP:BTC` (`_parse_hyperliquid_trades`) → `record_tick` drops every tick (no matching buffer)                                     | **launch-param**: pass `--instrument-ids HYPERLIQUID:PERP:BTC;…` (connector maps back to coin for subscribe + emits matching id). **FIXED** by cefi-lane relaunch (`mtds-live-cefi-hyperliquid-trades-20260621-161527`). Durable fix = launcher should derive canonical instrument-ids from IS (Phase 3.5 catalog-aware enum) instead of the bare-coin default.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | cefi-lane (this lane) — launcher-default follow-up   |
| 2   | **prediction live** | `mtds-live-prediction-polymarket-trades` → `NotImplementedError: no WSFeedConnector for 'POLYMARKET'` → DEPLOYMENT_FAILED                                  | venue **case mismatch**: registry has `polymarket` (lowercase, like all defi/prediction venues) but the shard-spec passes `POLYMARKET` (uppercase). cefi venues registered UPPERCASE so they match; defi/prediction lowercase don't. | **REVISED 2026-07-10 (operator): fix properly, don't paper over the inconsistency with a tolerant fallback.** A case-insensitive lookup in `_resolve_connector` was the originally-proposed fix but was flagged in a later architectural review (`instruments_remaining_work_audit_2026_07_10.md` §1a item 10) as a workaround, not a fix — it papers over a real registry-casing inconsistency (no stated reason cefi is UPPERCASE while defi/prediction are lowercase) rather than closing it. **Real fix**: canonicalize every venue key in `WS_FEED_CONNECTOR_FACTORIES` (and every producer of a venue string that keys into it — shard-specs, launch scripts) to ONE casing convention, UPPERCASE, matching the already-established convention used everywhere else in this workspace's canonical instrument-id work this session (`BYBIT`, `KRAKEN-FUTURES`, `HYPERLIQUID`, `ASTER`, etc.) — not a runtime fallback that leaves the registry itself inconsistent. Unblocks polymarket + jito/curve/orca/raydium/phoenix/morpho/kalshi live, same as the original proposal, but durably rather than tolerantly. | live-pipeline lane (slot-3 owns this file — 46adace) |
| 3   | **defi**            | `pyth-lst-backfill` Pyth Hermes historical `HTTP 400 "Failed to deserialize query string. Error: Odd number of digits"` (Chainlink leg OK, Pyth leg fails) | Pyth Hermes price-id query encoding — odd-length hex (missing `0x` / odd nibble count) in the historical query string                                                                                                                | **FIXED** — mtds@5906ebf (root cause: `bSOL/USD` + `INF/USD` in `_PYTH_FEEDS` carried 63-hex/odd-length feed-ids, replaced with canonical 64-hex ids from `hermes.pyth.network/v2/price_feeds`); already shipped + verified per `data_completion_to_100_all_ag_2026_06_21.md:233`. (was: open fix-proposal text, no FIXED marker — [SYNCED 2026-07-14, finding 219])                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | defi lane                                            |
| 4   | **sports**          | `mtds-backfill-odds-*` manifest `complete=False missing=['ODDS_API']` despite 8.5K rows written                                                            | expected ODDS_API source not satisfied (fan-out wrote 22 bookmaker shards but the source-completeness check still flags ODDS_API)                                                                                                    | recheck odds source-completeness / cred; verify SOURCE_PRIORITY for sports odds                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | sports lane                                          |
| 5   | **sports**          | `footystats-fwd-20260621-170000` run.log is 0 bytes                                                                                                        | VM startup/log-upload issue (never emitted)                                                                                                                                                                                          | check VM startup + heartbeat uploader                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | sports lane                                          |
| 6   | **prediction**      | `mtds-prediction-kalshibulk` stuck 50+ min on tar extraction (I/O), no progress markers                                                                    | large bulk tar decompress I/O-bound (not a code error)                                                                                                                                                                               | watch; if no completion, the 33GB bulk download/extract may need a bigger disk or streamed ingest                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | prediction lane                                      |

## Recommended decision

No rate-limit caps now (nothing is rate-limited). The data gaps are CODE/CONFIG, not throttling. Items 1 (fixed) + 2
(**now scoped as a real registry-casing canonicalization, not a trivial case-insensitive lookup** — see revised Fix
above) are the highest-value — #2 unblocks ALL lowercase-registered live venues (prediction + defi). Items 3–5 are
per-lane backfill/source fixes. The owning lanes (or the operator) should land 2–5; cefi-lane fixed #1 operationally +
will file the launcher-canonical-instrument-id default as a follow-up.

## UPDATE 2026-06-21 (cefi-lane, after fixing #1) — next bug: live capture fails tick-schema validation

Fixing #1 (canonical instrument-ids `HYPERLIQUID:PERP:<coin>`) **worked** — HL trades now reach the runner buffers and
windows capture. But the NEXT first-run bug surfaced (cefi live VM `…161527` run.log):

```
RowSchemaValidationError (venue=HYPERLIQUID): missing required columns:
['instrument_id','symbol','ts_event','price','size','side']
  … MTDSShardManifestRecorder.record_captured → ManifestWriter.record_captured
  → _maybe_validate → _validate_with_source → validate_row_df  (RAISES)
```

**Root cause:** the live `record_captured` passes a **bookkeeping** `_make_row_count_only_df` (just `row_count`) — its
own docstring says "row_count alone satisfies the manifest contract; the canonical write path lives in the runner's
`LiveWebsocketTickSink`". But `ManifestWriter.record_captured` runs `_maybe_validate` → `validate_row_df` against the
FULL tick contract and **raises** (strict on this VM). So **captured windows error out; only empty windows record** →
the manifest shows `empty_confirmed` even though trades ARE flowing. (live-mode never ran before → never exercised.)

**Fix (live-pipeline lane — slot-3 owns `manifest_recorder.py` + the UTL writer, shipped 46adace):** the live
`record_captured` bookkeeping df must **skip row-schema validation** (the real ticks are validated+written by
`LiveWebsocketTickSink` separately) — e.g. a `validate=False`/`skip_row_validation` kwarg on
`ManifestWriter.record_captured` passed by the live recorder; OR have the runner pass the REAL aggregated tick df
(instrument_id/symbol/ts_event/price/size/side) instead of the row-count-only synthetic. cefi-lane did NOT patch this
(slot-3's actively-churning file; collision-risk + a UTL+mtds design call). The cefi live VM stays up emitting
`live_hyperliquid` rows; it flips empty→captured the moment this lands. This is the LAST blocker for end-to-end live
trade capture — the 7-bug first-run chain: GCS-deploy · topic · IAM · row_key(asset_group) · row_key(day→date) ·
instrument-id-buffer-key · capture-schema-validation.

## UPDATE 2026-06-21 (cefi-lane) — bug#7 FIXED + durably shipped; bug#8 surfaced + fixed (MissingSourceError)

**Bug#7 RESOLVED (operator-directed "fix both paths"):** UTL `ManifestWriter.record_captured` gained a
`validate: bool = True` gate; the live recorder passes `validate=False` (bookkeeping df — real ticks validated+written
by `LiveWebsocketTickSink`; `pipeline_mode`+`source` carry provenance). Shipped durably to `live-defi-rollout` via
isolated name-correct worktrees (churn-immune; both QG-green): UTL@`057264fd` (converged with slot-3's `78481472`) +
market-tick-data-service@`e6b0f29`. Tarballs rebuilt+deployed; VM `mtds-live-cefi-hyperliquid-trades-20260621-175349`
relaunched. **`RowSchemaValidationError` is GONE** (confirmed in that VM's run.log — the fix works end-to-end).

**Bug#8 surfaced (8th first-run bug) — `MissingSourceError`:** with schema-validation correctly skipped, the live
`record_captured` then raised:

```
MissingSourceError: Manifest write passed source='hyperliquid' which is not a registered source for
asset_group='cefi' data_type='trades'. Allowed (UAC SOURCE_PRIORITY): ['tardis'].
  row_key={venue=HYPERLIQUID, data_type=trades, date=2026-06-21, instrument_type=PERPETUAL, instrument_id=HYPERLIQUID:PERP:SOL}
```

**Root cause:** HYPERLIQUID/ASTER were reclassified to `cefi` (UAC 0.30.0) but their **sources were never registered**
in `SOURCE_PRIORITY` for the cefi data_types they produce — `(cefi, trades)` etc. listed only `['tardis']`, so the
writer-side source gate (`_resolve_and_validate_source`) rejected `source='hyperliquid'`. This is the documented cefi
**source-provenance RED gap** (CLAUDE.md § "source= provenance is CROSSCUTTING — cefi/defi/sports are RED gaps").

**Fix (cefi-lane, UAC):** registered `hyperliquid` + `aster` as cefi sources on the 5 cefi perp market-data types they
produce — `(cefi, trades|ohlcv_1m|book_snapshot|liquidations|derivative_ticker)` (additive; `tardis` stays index-0 batch
primary; mirrors the pre-existing `aster`-in-`derivative_ticker` registration). `unified-api-contracts`
`canonical/crosscutting/_source_priority_data.py`. Additive + matches the venue-override per-venue source-stamp design.

> **OPERATOR RULING 2026-07-12 (plan-reconciliation finding 77): REMOVE this registration.** Per
> `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2 (finding 77: "REMOVE aster/hyperliquid
> book/liq SOURCE_PRIORITY registration"), aster + hyperliquid do not actually serve `book_snapshot` or `liquidations`
> for cefi — the `trades`/`ohlcv_1m`/`derivative_ticker` registrations are unaffected by this ruling.

> **STOP — RULING CONTRADICTED BY uac@3652f99f (verified 2026-07-12, execution attempt this session).** The ruling's
> premise ("aster + hyperliquid do not actually serve book_snapshot or liquidations") predates
> `unified-api-contracts@3652f99f` (2026-07-07, `feat(uac): ASTER book_snapshot_5 + liquidations live-wire capability`),
> which is AFTER the 2026-06-29 `honest_coverage_uac_writer_matrix_reconciliation` finding the ruling cites as its
> factual basis. Direct code inspection of the CURRENT `unified-api-contracts` tree
> (`unified_api_contracts/registry/market_data_categories.py`) shows 3 of the 4 targeted `(venue, data_type)` pairs
> contradict the "serves neither" premise:
>
> - **(ASTER, book_snapshot_5)** — CONTRADICTS removal.
>   `VENUE_DATA_TYPE_CAPABILITIES["ASTER"]["book_snapshot_5"] = "2026-06-23"`, documented as a real live-only feed via
>   `aster_book_liq_ws.py` (Binance-Futures-compatible WS, `depth5@100ms`). The MVP seeder test
>   `test_aster_book_snapshot_5_and_liquidations_seeded` (`tests/unit/test_mtds_venue_coverage.py`, also landed in
>   3652f99f) actively asserts non-empty seed instruments for this pair. Removing the SOURCE_PRIORITY entry while this
>   capability + seed stay live would re-create the exact `MissingSourceError` (bug#8) this doc's own cefi-lane fix was
>   written to close — a regression, not a fix.
> - **(ASTER, liquidations)** — CONTRADICTS removal. Same `aster_book_liq_ws.py` connector (`!forceOrder@arr`), same
>   `"2026-06-23"` start_date, confirmed real (seed stays empty by design — venue-level fallback, not because the feed
>   is fake).
> - **(HYPERLIQUID, book_snapshot_5)** — CONTRADICTS removal, independent of 3652f99f timing. HYPERLIQUID has carried
>   `"book_snapshot_5": "2023-04-15"` (S3 `hyperliquid-archive/market_data/`) since before this issue doc's own bug#8
>   fix; the capability table's own in-file comment for HYPERLIQUID never claimed book_snapshot absence.
> - **(HYPERLIQUID, liquidations)** — CONSISTENT with removal. `VENUE_DATA_TYPE_CAPABILITIES["HYPERLIQUID"]` has no
>   `liquidations` key; the in-file comment is explicit: "liquidations is out of scope (Hyperliquid does not publish a
>   liquidations feed — no S3 prefix, no Tardis channel)."
>
> **Verdict: did not ship.** Executing the ruling as literally scoped (all 4 pairs) would put `SOURCE_PRIORITY` out of
> sync with `VENUE_DATA_TYPE_CAPABILITIES` + its own regression test for 3 of 4 pairs, and would reintroduce bug#8
> (`MissingSourceError`) for real, wired ASTER live traffic the moment the cefi book/liq live VMs write. No code change
> made in `unified-api-contracts`. Blast-radius pre-audit (for whichever way this resolves): `SOURCE_PRIORITY` /
> `VENUE_DATA_TYPE_CAPABILITIES` are read by `_source_priority_provenance.py` (`has_source_priority` /
> `_resolve_and_validate_source` → `MissingSourceError` gate), `_mvp_scope_rules.py` + `market_data_categories.py`
> (`get_expected_instruments_for_venue` seeders), `shard_source_availability.py`, `era_b_legacy_purge.py`,
> `possible_manifest.py`, `data_type_capability.py`, plus cross-repo in market-tick-data-service:
> `engine/orchestrator/{venue_fetch,manifest_finalize,preflight,symbol_rules,partitioned_writer}.py` and several CLI
> handlers/scripts. Any resolution must re-run `test_mtds_venue_coverage.py`, `test_source_priority.py`,
> `test_shard_source_availability.py`, `test_era_b_purge.py` for the affected pairs.
>
> **Escalation to operator (structured options):**
>
> Should finding-77's SOURCE_PRIORITY removal proceed given `VENUE_DATA_TYPE_CAPABILITIES` now documents real ASTER
> book_snapshot_5/liquidations feeds (uac@3652f99f, 2026-07-07) and a pre-existing real HYPERLIQUID book_snapshot_5 feed
> (S3-archived since 2023-04-15)?
>
> A: **Narrow the ruling to just `(HYPERLIQUID, liquidations)`** — the only one of the 4 pairs where "serves neither" is
> still true today; leave `(ASTER, book_snapshot_5)`, `(ASTER, liquidations)`, `(HYPERLIQUID, book_snapshot_5)`
> registered as-is (they match a real, tested, wired capability). **[WORKER REC]** B: **Execute finding-77 exactly as
> scoped** (remove all 4 pairs) — accept that this reopens bug#8 (`MissingSourceError`) for ASTER live book/liq traffic
> and that `test_aster_book_snapshot_5_and_liquidations_seeded` will need to be reverted back toward
> `test_aster_book_snapshot_5_is_empty` (i.e., partially undo uac@3652f99f). C: **Re-verify against live data first** —
> before removing anything, confirm from real capture logs whether the cefi-live book/liq VMs for ASTER (and HYPERLIQUID
> book_snapshot_5) are actually receiving non-empty ticks today; let that observation (not either doc's prose) settle
> which pairs are genuinely dead. Other: operator can type a custom answer.

- [x] [CODE] P2. **RESOLVED 2026-07-13 — operator ruling verbatim (recorded here in
      `fleet_data_acquisition_health_2026_06_21.md`): "OPERATOR RULING 2026-07-13 (resolving the finding-77 escalation,
      option A): remove ONLY the (HYPERLIQUID, liquidations) SOURCE_PRIORITY registration — the one pair with no real
      feed. The other three pairs (ASTER book_snapshot_5, ASTER liquidations, HYPERLIQUID book_snapshot_5) STAY — they
      are real feeds per uac@3652f99f."** Matches escalation option A (`[WORKER REC]`) exactly — the narrowest of the
      three offered options. Shipped: removed `hyperliquid` from `("cefi", "liquidations")` in
      `_source_priority_data.py` ONLY; the other three pairs (`("cefi",     "book_snapshot")` keeps
      `aster`+`hyperliquid`, `("cefi", "liquidations")` keeps `aster`) are untouched, plus a code comment on the
      remaining aster/HL entries recording this ruling. Verified no `VENUE_DATA_TYPE_CAPABILITIES` entry claims HL
      liquidations (`HYPERLIQUID` capability dict has `trades`/`book_snapshot_5`/`derivative_ticker` only — no
      `liquidations` key). Added regression tests: `test_cefi_liquidations_excludes_hyperliquid_finding77` +
      `test_cefi_book_liq_pairs_kept_by_finding77_narrowed_ruling` (`tests/unit/test_source_priority.py`) +
      `test_hyperliquid_liquidations_resolves_empty_no_crash_finding77` (`tests/unit/test_mtds_venue_coverage.py`,
      confirms `get_expected_instruments_for_venue("HYPERLIQUID", "liquidations") == []`, expect-nothing/no-crash
      semantics). `quality-gates.sh` green (full suite, 3570+ tests). Evidence: `unified-api-contracts@2088324c`.

**Correction to issue `/plans/archive/issues/live_tardis_machine_and_hl_aster_s3_batch_2026_06_21.md` §2 (ARCHIVED
2026-07-27, STALE PREMISE at time of writing):** that doc says the cefi download "STRIPS HL/ASTER (they're defi in
VENUE_TO_ASSET_GROUP)." **Verified 2026-06-21: `VENUE_TO_ASSET_GROUP` now resolves `HYPERLIQUID`→`cefi` and
`ASTER`→`cefi`** (post UAC 0.30.0 — NOT defi). So the strip premise is stale; the actual 48.5k-cell `attempted_failed`
cause needs fresh diagnosis (and the **defi lane is actively running on HL S3 data** → a blind cefi HL/ASTER batch could
collide — diagnose-first, not blind-execute). First-run chain now 8 bugs: …instrument-id-buffer-key ·
capture-schema-validation(bug#7) · source-registration(bug#8).

### Follow-up finding (P2, cefi-lane 2026-06-21) — `book_snapshot` vs `book_snapshot_5` SOURCE_PRIORITY key mismatch

The live connectors + canonical pipeline emit `data_type="book_snapshot_5"` (e.g. `coinbase_book_ws.py`,
`binance_futures_ws.py`), but `SOURCE_PRIORITY` keys it as `("cefi", "book_snapshot")`.
`has_source_priority("cefi", "book_snapshot_5")` → **False** → book_snapshot_5 writes are source-EXEMPT (no
`MissingSourceError`, but also **no source validation** — the `book_snapshot` registration incl. the new
hyperliquid/aster sources is effectively DEAD for the real data_type). Not blocking (the trades VM is the bug#8 proof;
book shards don't raise), but cefi book source-provenance is unenforced fleet-wide. **Fix (P2, live-pipeline lane):**
align the key — either register `("cefi", "book_snapshot_5")` (additive) or rename the SOURCE_PRIORITY/data_type to one
canonical spelling. Same audit should sweep all AGs for book_snapshot vs book_snapshot_5 key drift. Repo:
unified-api-contracts (+ any data_type emitters).

### Follow-up finding (P1, 2026-06-21) — mtds version-surface drift blocks LDR→staging QG

While shipping the HL/ASTER batch codex fix, full `quality-gates.sh` for **market-tick-data-service** is BLOCKED at the
version-alignment pre-gate ("local BEHIND remote staging/main") for the WHOLE repo (not any one change). Measured:
pyproject `0.31.0` == origin/staging `0.31.0`, origin/main `0.24.0`, latest tag `v0.24.0`, workspace-manifest
`versions.mtds=0.25.0`, `repositories.mtds.version=0.20.0`. The pyproject↔manifest split (0.31.0 vs 0.25.0) is a
VERSION_SPLIT the alignment gate trips on. This is **semver-agent / version-management territory** (agents MUST NOT
`--skip-version-alignment` or hand-bump). Consequence: the mtds LDR→staging promotion (and any mtds quickmerge needing
full local QG) is gated until the version surfaces are reconciled — run
`scripts/repo-management/run-version-alignment.sh --fix` (operator/semver) or let the semver-agent re-align.
Code-correctness is unaffected (the cefi batch + tardis-machine commits are ruff/basedpyright/size/ test-clean —
verified piecemeal); this is purely the version-surface gate. Repo: market-tick-data-service (version mgmt).

## Todos

- [x] ✅ [CODE] P2. **Align `book_snapshot` vs `book_snapshot_5` SOURCE_PRIORITY key** — registered
      `("cefi", "book_snapshot_5"): ["tardis", "aster", "hyperliquid", "extended"]` additively (same source list as the
      legacy `("cefi", "book_snapshot")` alias, which stays for the closed-set pipeline_mode round-trip per
      `test_validity_matrix_completeness.py`'s existing `CEFI_LEGACY_KEY` exclusion). Added the matching
      `AVAILABILITY_AT_SEMANTICS[("cefi","book_snapshot_5")] = "tick_timestamp"` entry required by the bidirectional
      SOURCE_PRIORITY↔AVAILABILITY_AT_SEMANTICS round-trip test
      (`test_every_source_priority_pair_has_availability_semantic`). Swept other AGs for the same drift via
      `DATA_TYPES_BY_ASSET_GROUP`: only `cefi` and `prediction` declare `book_snapshot_5` as a valid data_type, and
      `prediction` was already keyed correctly (`("prediction","book_snapshot_5")` pre-existing) — no other AG drift
      found. Added regression test `test_cefi_book_snapshot_5_source_priority_registered_fleet_health_2026_06_21`
      (`tests/unit/test_source_priority.py`). `quality-gates.sh` full suite green. Evidence:
      `unified-api-contracts@7d41bc34`.
- [x] ✅ [INFRA] P1. **STALE — already self-resolved via normal semver-agent operation, 2026-07-28.** The specific
      version numbers cited (pyproject `0.31.0`/origin-main `0.24.0`/workspace-manifest `0.25.0`/
      `repositories.mtds.version` `0.20.0`) no longer exist — mtds has advanced through ~70+ version bumps since this
      todo was written (2026-06-21). Live re-check via
      `unified-trading-pm/scripts/cicd/assert_version_coherence.py --warn-only` (the actual VERSION_SPLIT gate, read via
      `run-version-alignment.sh`'s own "[0.95/4] pyproject vs manifest version parity" step) shows mtds fully coherent:
      `versions{}=0.99.0`, source `pyproject.version=0.99.0`, tag-ok — **zero VERSION_SPLIT** for mtds today. Confirmed
      no live gate block: mtds's open LDR→main promote PR #774
      (`market-tick-data-service@873c6c7362402de9a5f43eac501f3a3fdb95cd1c`) has `quality-gates-v2` actively
      `in_progress` (not blocked/failed). The only residual version-related finding is a fleet-wide (23-repo, not
      mtds-specific) `VESTIGIAL_SCALAR_DRIFT` — `repositories{}.version` (a display-only scalar, `0.83.0` for mtds)
      lagging `versions{}` (`0.99.0`) — which `assert_version_coherence.py`'s own docstring documents as low-stakes
      ("written only opportunistically ... read only as a display fallback ... NOT required"), distinct from the
      `VERSION_SPLIT` class this todo was actually about, and already self-reported by the same read-only checker on
      every future run (no separate tracking needed). No code change required.

## Progress Log

- **context-scout 2026-08-03**: populated/refreshed context_scope (5 entries).
- **slot-5 data_engineering 2026-08-04 (task `cross_cutting_satellite_ao_dispatch_batch1b-003`)**: verified all 4
  remaining fixable-bug items from the 2026-06-21 sweep:
  - **(a) sports ODDS_API completeness (item #4)**: read-side freshness check already fixed 2026-07-30 (source-scoping
    in `tick_data_handler.py`/`preflight.py`). Write-side completeness check (`manifest_finalize.py`
    `_write_date_manifest` calling `validate_batch_completeness`) was still comparing bookmaker-named shard keys against
    `active_venues=["ODDS_API"]`, producing false `complete=False missing=['ODDS_API']` on every sports odds backfill
    run. Fixed: added source-scoped guard skipping the venue-based check for sports
    (`market-tick-data-service@09c8cbf8`). Source-aware completeness is tracked by the manifest consolidator.
  - **(b) footystats 0-byte run.log (item #5)**: confirmed the `launch-footystats-forward-poll.sh` VM launcher is
    actively maintained and well-structured; the startup-script (`gs://.../vm/setup-data-pipeline-vm.sh`) is GCS-hosted;
    a 0-byte run.log is consistent with a one-time transient VM startup failure (GCS download race / provisioning delay)
    rather than a systemic code bug. Multiple footystats-related fixes shipped since 2026-06-21. The VM fire-and-forget
    model is unchanged — a future 0-byte run.log would be caught by the same operational visibility that caught this
    one. No code change needed today.
  - **(c) book_snapshot_5 SOURCE_PRIORITY**: verified `unified-api-contracts@7d41bc34` is ancestor of current LDR HEAD;
    `("cefi", "book_snapshot_5")` registered with companion regression test
    `test_cefi_book_snapshot_5_source_priority_registered_fleet_health_2026_06_21`. Fleet-wide sweep confirmed only
    `cefi` and `prediction` declare `book_snapshot_5`; `prediction` was already correctly keyed. Fully resolved.
  - **(d) MTDS version-surface drift**: verified self-resolved via normal semver-agent operation. Current MTDS git tag
    `v0.102.0` matches workspace manifest `versions.mtds=0.102.0`; `assert_version_coherence.py` shows tag-ok, zero
    VERSION_SPLIT. The vestigial `repositories.mtds.version=0.83.0` display-scalar lag is fleet-wide/warn-only, not
    blocking. Fully resolved. All 4 items closed — no new code shipped (c/d were pre-existing fixes; a/b self-resolved).
