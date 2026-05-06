---
type: handover
companion_plan: shard_granularity_ssot_propagation_2026_05_06.plan.md (TBD)
locked_by: live-defi-rollout
locked_since: 2026-05-06
---

# Shard-Granularity SSOT Propagation — Executor Handover

**Branch:** `live-defi-rollout` **Status:** Awaiting plan draft + pre-audit Explore agent return. **Companion plan:**
`shard_granularity_ssot_propagation_2026_05_06.plan.md` (drafting next; not yet committed).

---

## Why this plan exists

Most of this is already implemented across previous plans. **This plan is a redo-and-test pass to verify end-to-end
consistency, not greenfield.**

Goal: every shard atom is identical across (a) writer atomicity, (b) manifest row key, (c) data-status display, (d)
downstream pre-flight gate, (e) deployment-UI drill-down. Drift between any two = silent correctness bug. Recent
incidents trace exactly to this drift:

- TradFi MVP partial bundles (ES.OPT 18/839 historical bundles passed manifest as captured)
- MDPS empty-placeholder bars (1440 NaN OHLC bars/day/venue for years; manifest said `captured`)
- Databento per-schema silent drop (bundled `ohlcv_1m;trades` lost ohlcv on 429; orchestrator marked complete)

---

## Your role in this plan

You're the **verifier**, not the UI builder. Walk every service's writer + manifest + data-status surface and **check
whether the existing structures match the target shapes in this brief**. Where they don't match, report findings back to
me — don't try to fix the UI/download side yourself. Specifically:

- IF a writer writes at the right shard key → ✓ note it
- IF pre-flight reads at coarser granularity than the writer → ❌ flag it
- IF `available_at` isn't stamped, or is derived rather than written → ❌ flag it
- IF a manifest on disk has drifted from v5 shape → ❌ flag it + estimate migration shape
- IF a fallback reader exists for a non-canonical shape that should have been migrated → ❌ flag it
- IF a UTL-grade utility is duplicated per-service → ❌ flag it

Your deliverable is a per-service audit report (one section per service, structured by the verify/fix/lift/build
checklist below) plus a list of confirmed migration items. Code fixes you take on directly should be the per-service
writer / pre-flight / `available_at` / write-gate work — that's where the correctness bugs live. UI download + schema
view work stays with me.

---

## Co-evolving stream — TradFi MVP follow-ups

A separate parallel stream is shipping three TradFi MVP follow-ups. Be aware so you don't step on it OR duplicate work
in your audit:

### Item 1 — Cluster-aware bundle validation (lands in UTL, affects your scope)

`ManifestWriter.record_captured` gets two new params: `expected_root_clusters: dict[str, int]` +
`cluster_extractor: Callable[[str], str]`. At write-time, rows are counted per cluster; any expected-active cluster
below its `min_rows` triggers `record_failed(ClusterCoverageError(missing=..., observed=...))` instead of writing the
parquet. ES.OPT 11-cluster taxonomy is the seed; generalises to futures combos, prediction canonical-question bundles
(BTC up/down clusters), sports fixture bundles.

**For your audit:** treat this as part of the write-gate trio (row-count > 0, NaN ratio < threshold, cluster coverage ≥
expected) when verifying each service. **Don't build a parallel mechanism** — once the UTL change lands, services just
need to pass the clusters dict for any shard that's a bundle (`options_chain`, `futures_chain`, prediction canonical
groups, sports per-fixture aggregates). Flag in your audit which services need this wired.

### Item 2 — Databento 429 silent-drop fix (MTDS, overlaps your scope)

`market-tick-data-service/.../tradfi/databento_adapter.py` `download_batch_df` lines 677, 683 currently swallow
per-schema failures (`if dbn_store is None: continue`, `except Exception: continue`). Patching to return
`(df, list[_PerSchemaFailure])` so the orchestrator can `record_failed` per (date, data_type). Shard-level isolation, no
silent absence.

**For your audit:** this is exactly the partial-shard / silent-absence bug the SSOT plan exists to catch. When you walk
MTDS adapters, this one is being fixed in parallel — note that, but **DO scan every other adapter** in MTDS for the same
anti-pattern (`except: continue` swallowing per-schema or per-instrument failures inside `download_batch_df`-shaped
loops). Report findings; I'll route them.

### Item 3 — VIX forward-poll wiring (unrelated to your audit)

`umi_tick_provider.py` CBOE+ohlcv_15m route → wire `YahooFinanceAdapter.download_15min_vix()`. Single-line addition. No
structural overlap. Mentioned only so you don't accidentally re-do.

### Workspace principles already codified (re-use, don't re-derive)

1. **Manifest concurrency**: read-once + per-date TTL-cached freshness check (60s default) + write-time CAS. PM
   CLAUDE.md `77cd8713`. Reference impl `_refresh_captured_cache` / `_is_now_captured` in `/tmp/fill_missing_ohlcv.py`
   (mirrored at `gs://deployment-scripts-central-element-323112/audit-scripts/fill_missing_ohlcv.py`).
2. **Trading-calendar SSOT**: UAC `is_non_trading_day` / `clip_dates_to_trading_days` from `venue_trading_calendar.py`.
   No naive weekday filters.
3. **Per-(venue, data_type) coverage windows**: UAC `VENUE_DATA_TYPE_COVERAGE_WINDOWS` registry — new entries here, not
   legacy `TRADFI_TICK_DATA_WINDOWS`.
4. **Multi-hour backfills run on same-region GCE VM** (asia-northeast1-c), not local Mac. Pattern
   `mtds-{operation}-{ts}` VM names with `VM_BACKFILL_CMD` metadata pulling script from GCS at boot.

### Coordination rule

If your audit surfaces a fix that overlaps Items 1 or 2, **don't ship it — ping me first.** We'll route through the
parallel stream so the change lands once, in the right layer, with the right test coverage.

---

## The cross-cutting invariant

For every (service, data type), the **shard atom** must match across:

1. Writer atomicity boundary (parquet finalize + `record_captured`)
2. Manifest row key (v5 columns:
   `asset_group, venue, chain, data_type, instrument_type, instrument_id, league_id, timeframe, feature_group, model_family, ...`)
3. Data-status page rollup
4. Downstream service pre-flight gate
5. Deployment-UI drill-down + parquet download + schema view

If pre-flight reads at `(venue, data_type, date)` while writer writes at full v5 granularity, partial captures look
"complete" upstream. Find every such mismatch.

---

## Per-asset-group shard-key matrix (UAC SSOT — Phase 0)

| Asset group              | Shard key                                                                   | Bundling                                                                      | `empty_confirmed` triggers                                              |
| ------------------------ | --------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| **CeFi spot/perp**       | (ag, venue, dt, IT, instrument_id, day)                                     | per-instrument (35GB roots)                                                   | source 200+empty                                                        |
| **CeFi options/futures** | (ag, venue, dt, `options_chain`/`futures_chain`, root, day)                 | bundled by root                                                               | per-bundle                                                              |
| **TradFi futures**       | (ag=tradfi, venue, dt, IT, root, day)                                       | bundled by root                                                               | non-trading days via `venue_trading_calendar` (holiday + session close) |
| **TradFi ETFs**          | (ag=tradfi, venue, dt, IT, instrument_id, day)                              | per-instrument (IBIT, ETHA)                                                   | non-trading days                                                        |
| **TradFi options**       | (ag=tradfi, venue, dt, `options_chain`, root, day)                          | bundled                                                                       | non-trading + zero-vol strikes                                          |
| **DeFi**                 | (ag=defi, **chain**, venue/protocol, dt, instrument_id_or_protocol_id, day) | chain is first-class axis                                                     | pre-genesis dates per chain                                             |
| **Sports**               | (ag=sports, source, dt, league_id, fixture_id or day-aggregate, day)        | per-fixture or per-league-day                                                 | paused-league (`KNOWN_COVERAGE_GAPS`) + pre-`SOURCE_COVERAGE_START`     |
| **Prediction**           | (ag=prediction, venue, dt, **canonical_question_group**, day)               | canonical names (BTC up/down, S&P up/down) — analog of options-chain bundling | pre-launch + resolved-old                                               |

**Prediction canonical-question-grouping** is the most likely greenfield bit — verify whether UAC has a SSOT mapping raw
Polymarket market_id → canonical question group. If not, flag it as a build item.

---

## Layer discipline (CRITICAL)

Tag every plan item with placement before implementing:

- **[UAC]** — contracts, shard-key shapes, `feature_group → required_inputs` DAG, `SOURCE_COVERAGE_START` /
  `DATA_TYPE_COVERAGE_START` / `KNOWN_COVERAGE_GAPS`, `available_at` semantics per source, prediction canonical-question
  SSOT, `venue_trading_calendar`
- **[UTL]** — cross-service runtime utilities: `ManifestWriter`, dual-vocab probe utility (lift the 5 phantom-audit
  drift axes into one shared module), write-gate helper (row count + NaN ratio + schema), `LookaheadBiasError`,
  schema-introspection helper, `run_lifecycle`
- **[per-service]** — only what genuinely differs: source-specific `available_at` stamping, calculator/adapter business
  logic
- **[deployment-api / deployment-ui]** — per-service download endpoint + schema-view route, data-status tab drill-down

**Do not duplicate cross-service utilities per-service.** If you find one inlined (e.g. NaN-ratio check copy-pasted
across calculators), lift to UTL.

---

## Per-service verify/fix/lift/build checklist

For **each** of: `instruments-service`, `market-tick-data-service`, `market-data-processing-service`,
`features-onchain-service`, `features-sports-service`, `features-delta-one-service`:

- [ ] Writer shard key matches v5 manifest columns — verify
- [ ] `record_captured` / `record_empty` / `record_failed` fires at full shard granularity — verify
- [ ] Pre-flight `_should_skip_shard` reads at full shard granularity (NOT `(venue, data_type, date)`) — verify, fix if
      coarser
- [ ] Dual-vocab probe goes through shared UTL utility, not inlined — verify, lift if duplicated
- [ ] `available_at` column stamped at write-time per source rules — verify, build if missing
- [ ] Write-gates fire on row-count==0, NaN ratio above threshold, schema mismatch — verify, lift to UTL helper
- [ ] Downstream pre-flight checks ALL DAG inputs (not just one upstream) at correct shard granularity — verify
- [ ] Per-instrument progress events emitted with row counts (`INSTRUMENT_PROCESSED` etc.) — verify

---

## Data-status + UI checklist (audit only — report findings, don't fix)

Per service, walk the data-status tab and verify against target shape. Report gaps; do not implement UI changes.

Target shape:

- [ ] Manifest read at full v5 shard granularity (NOT `(venue, data_type, date)` rollup)
- [ ] `capture_status` displayed honestly: `captured` / `empty_confirmed` / `attempted_failed` with `error_reason`
- [ ] Drill-down path: `asset_group → venue/chain → data_type → instrument_type → instrument_id → day → leaf parquet`
- [ ] Per-leaf actions exist or are stubbed: download parquet, view schema (columns, types, row count, NaN ratio per
      column, `available_at` min/max)
- [ ] `empty_confirmed` rendered distinctly from missing — non-trading days, paused leagues, pre-genesis dates show as
      expected-empty, NOT red

For each service, report: which of the above match target, which don't, and what the current shape actually is. I'll
handle the UI/download fixes separately.

---

## Lookahead-bias rules (features-\* + MDPS)

For every feature compute at horizon t-N:

- Every input row consumed must satisfy `input.available_at <= kickoff_or_target_ts - N`
- Raise `LookaheadBiasError` loud (currently fires for `lst_yields`; extend to every features-\* calculator)
- `feature_group → required_inputs[]` DAG SSOT in UAC drives the check

### Sports temporal availability stamping rules

| Source                                                             | `available_at`                                                                                    |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------- |
| Lineups                                                            | `kickoff - 60min` (conservative; clip earlier leaks)                                              |
| Injuries                                                           | event-time of the injury report (so feature for fixture F sees only injuries from prior fixtures) |
| Pre-match odds                                                     | publication time per snapshot (opening days before, closing at kickoff)                           |
| Post-match (understat xG, fixture_stats, results, sfi_progressive) | `match_end_time` — NEVER available pre-kickoff                                                    |
| Weather forecasts                                                  | forecast-**issue** time, distinct from forecast-target time                                       |

If `available_at` is missing on disk for a source, **stamp it at backfill-replay time** before SSOT propagation
completes. Don't infer at read-time.

---

## Manifest migration (NOT fallback)

- Identify any manifest that drifted from v5 canonical shape (pre-v5 row schema, off-canonical paths, wrong row keys)
- Write a one-time migration script per drift (precedent:
  `instruments-service/scripts/migrate_local_sfi_to_canonical.py`)
- **Remove** fallback reader logic that handled the legacy shape after migration
- One documented exception that survives: hive-vocab `category=` vs `asset_group=` on-disk legacy preservation per
  CLAUDE.md asset-group section. Reader tries canonical first, falls back to legacy. **Do NOT rekey on-disk data.**
- Everything else: migrate, then delete the fallback path. Workspace rule: no try/except fallback imports, no compat
  shims.

---

## Validation gates per `record_captured`

Three checks fire at the write boundary; any failure → `attempted_failed` with `error_reason`:

1. **Row count > 0** unless source response was legitimately empty (then `record_empty`, not `record_captured`)
2. **NaN ratio per column < threshold** (per-feature-group threshold in UAC; carry-tracer pattern)
3. **Schema matches contract** (columns + types match UAC schema declaration)
4. **(when Item 1 lands)** Cluster coverage ≥ expected for bundled shards

Without these, manifest is presence-only and partial bundles / empty placeholders pass silently. This is the lesson from
MDPS 2026-05-05 (1440 empty placeholder bars) and TradFi MVP 2026-05-06 (ES.OPT 18/839 partial bundles).

---

## Anti-patterns to refuse

- Pre-flight at coarser granularity than writer
- NaN-ratio gate inlined per calculator instead of UTL helper
- `available_at` derived at read-time instead of stamped at write-time
- Fallback readers for non-canonical manifest shapes (migrate instead)
- Per-service duplicate of cross-service utility
- Empty placeholder rows masking absence (1440 NaN OHLC bars instead of `record_empty`)
- Writing fresh manifests in a coarser shape than v5
- `except: continue` swallowing per-schema or per-instrument failures inside per-shard loops

---

## Workspace rules to respect

- `bash scripts/quality-gates.sh` per-repo (uses repo `.venv`, never workspace venv)
- `bash scripts/quickmerge.sh "msg" --agent --files "p1 p2"` — never `git push` directly. Agent mode requires `--files`.
- Push manually committed branches before quickmerge if branch has commits not on origin
- Don't quickmerge while local dep repos are dirty unless explicitly approved
- Plan format: Cursor checkboxes (`- [x]` / `- [ ]`) on every todo
- Locked to `live-defi-rollout` branch (lock plan via frontmatter)
- Citadel-grade planning: pre-audit manifest, phased DAG with parallel/sequential markers, QG gates between phases,
  success criteria per phase, downstream consumer fix list
- Sub-agents launched during execution must be injected with
  `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` content at top of prompt
- Asset-group vocabulary: `asset_group` everywhere new (not `category`); dict KEYS stay lowercase
- No `os.getenv()` — `UnifiedCloudConfig`
- No `# type: ignore` for architectural violations — fix root cause
- `basedpyright` (not `pyright`), with `run_timeout 120 basedpyright <source_dir>/`

---

## Output expectations per phase

- QG green per repo touched
- All affected downstream consumers updated in the same plan (no "fix later")
- Manifest reads + writes use same shard key
- Data-status surfaces match writer granularity (audit report, not UI fix)
- UI drill-down works for the service touched (audit report only)
- No fallback paths remain for migrated manifests
- Tests cover write-gates: row=0 → fail loud, high NaN → fail loud, schema mismatch → fail loud
- `available_at` end-to-end smoke: write feature at t-24, verify no input row consumed has
  `available_at > kickoff - 24h`

---

## Final deliverable from this audit

A per-service report (one markdown section per service) with:

1. ✓ items that match target shape
2. ❌ items that don't match (writer/pre-flight/available_at/write-gate/migration/UI)
3. 🔀 items implemented in the wrong layer
4. ❓ items where you couldn't verify (need clarification or codex pointer)

Plus a consolidated migration list (manifest drift instances + estimated migration shape) and a consolidated lift list
(UTL-grade utilities currently duplicated per-service).

I'll fold your report into the plan's pre-audit manifest and we'll phase the actual fix work from there.
