# Next-Agent Handoff — MTDS to-100% closeout (2026-05-06 21:00 UTC)

**Branch:** `live-defi-rollout` across all repos. **Workspace root:**
`/Users/ikennaigboaka/Code/unified-trading-system-repos/` **You are the third agent on this thread.** Read this whole
doc before touching anything.

---

## Why this handoff exists

The user's running goal: drive the MTDS to-100% picture closed (data complete, manifest honest, downstream consumers can
trust the shard atom). Two prior agents (this Claude session + CosmicTrader / `semver-rollout[bot]`) have been working
in parallel through the day. Active PM plans went 7 → 5 with significant supersession + flip work. **Most architectural
code work is now owned by the shard-granularity-SSOT-propagation stream** — the residual work for you is verification,
audit, and the few items that are explicitly not in that stream.

---

## Required reading before any action

In this order:

1. **`unified-trading-pm/cursor-configs/CLAUDE.md`** — full workspace rules. The "Shard-granularity SSOT (CRITICAL)"
   section is the single most-important new framing — every code action must be tagged [UAC] / [UTL] / [per-service] /
   [deployment-api/ui] before being implemented.
2. **`unified-trading-pm/plans/active/shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md`** (commit `d591416d`,
   locked to `live-defi-rollout`) — the active architectural stream. **Coordination rule** (line 109): "If your audit
   surfaces a fix that overlaps Items 1 or 2, don't ship it — ping the user first."
3. **`unified-trading-pm/plans/active/market_tick_data_to_100pct_2026_05_05.plan.md`** — the to-100% parent plan. Read
   the Live operations log near the bottom (newest entries first); the checkbox state is now mostly accurate post-flips.
4. **Memory entries (auto-loaded into your context)** — especially:
   - `project_mtds_plans_triage_2026_05_06.md` — what just happened
   - `project_run_lifecycle_ssot_rollout_2026_05_06.md` — the new UTL helper + base-service.sh STEP 5.63 gate
   - `project_tradfi_mvp_closeout_2026_05_06.md` — TradFi 76.8% → 98.8% coverage closeout context
   - `feedback_databento_adapter_silent_drop_root_cause.md` — pending adapter fix in MTDS

---

## Active streams you must coordinate with

### Stream A — Shard-granularity SSOT (CosmicTrader-owned, locked)

**Plan:** `shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md` + companion plan being drafted (PM `f657288c`
scaffold).

**In-flight code work** — DO NOT TOUCH these surfaces:

- **UTL** `manifest_writer.py` — adding 4-pillar write-gates (row-count, NaN ratio, schema, cluster coverage) directly
  into `ManifestWriter.record_captured`. Tests at `tests/unit/test_manifest_writer_cluster_coverage.py` (uncommitted in
  working tree at handoff time). UTL is 1 commit behind origin and dirty.
- **UAC** `registry/__init__.py` (dirty in working tree) — likely cluster-coverage taxonomy export.
- **MDPS** `candle_write_mixin.py` + `cli/main.py` — fan-out simplification for the per-instrument pipeline. The
  chain-bundle dispatch regression (`test_legacy_ticks_parquet_recovers_instrument_id_from_data` in
  `test_per_instrument_pipeline.py`) is being fixed here.
- **Databento adapter silent-drop fix** — MTDS `tradfi/databento_adapter.py` `download_batch_df` lines 677, 683.
  Returning `(df, list[_PerSchemaFailure])` so the orchestrator can `record_failed` per (date, data_type). Reference
  incident memory: `feedback_databento_adapter_silent_drop_root_cause.md`.

**Audit findings already shipped** (PM `90c3b535`, `cb3460e9`, `552f0d04`) — instruments-service, features-onchain,
features-sports, features-delta-one, UAC prediction SSOT findings. Stream is mid-walk through the per-service
verify/fix/lift/build checklist.

### Stream B — TradFi MVP follow-ups (parallel to A, narrower)

3 items per HANDOVER lines 60–93:

1. Cluster-aware bundle validation (lands in UTL — covered by Stream A's write-gates).
2. Databento 429 silent-drop fix (MTDS, in flight per above).
3. VIX forward-poll wiring (`umi_tick_provider.py` CBOE+ohlcv_15m → `YahooFinanceAdapter.download_15min_vix()`).
   **Single-line addition. Mentioned only so you don't accidentally re-do.** Not your scope unless explicitly asked.

---

## What's left for YOU to do (priority order)

### P0 — Bounded operator-runnable items

1. **Phase 1.5a-3 vault venue rename** (~30 sec one-shot script run):
   - Script: `market-tick-data-service/scripts/rename_vault_venue_canonical.py` (already shipped MTDS `bf81219`).
   - Target: `gs://market-data-tick-defi-central-element-323112/_index/availability_index.parquet`.
   - Action: rename rows where `data_type='vault_share_price' AND venue ∈ {MORPHO_VAULTS, YEARN_V3}` → `MORPHOVAULTS` /
     `YEARNV3`. Backup-then-write. FRAX + MAKER already canonical.
   - **Coordination**: confirm no other writer is mid-flight against the DeFi manifest before running. (BUG-X2 flip on
     the CEFI side already done in prod — see PM `94213212` evidence.)
   - After run: re-read manifest, confirm zero rows with the legacy underscore venues, delete the backup blob, **flip
     the 1 remaining HUMAN P0 todo** in `market_tick_data_to_100pct_2026_05_05.plan.md` Phase 1.5a-3 done.
   - **DO NOT autonomously gcloud-execute this without operator confirmation** — it mutates production manifest state.
     Ask first.

2. **Verify the live operations log entries are accurate** in `market_tick_data_to_100pct_2026_05_05.plan.md`:
   - Read top 30 entries; cross-check against actual git log + GCS state where possible.
   - The plan's checkbox state is now ~95% accurate post-this-session's flips, but newer entries from CosmicTrader's
     stream may need integration.

### P1 — Post-Stream-A items (will unblock once Stream A lands)

3. **Phase 1.5a-4 disk migrations** — DEFERRED per PM `94213212` to the shard-granularity stream (existing
   `migrate_tradfi_to_hive.py` writes per-day-aggregate but the new shard-key matrix requires per-instrument/per-root).
   MTDS `eeb03c3` already fixed the `category=` → `asset_group=` path template; the migrate logic itself needs rewriting
   for shard-atom alignment. **Don't try to ship the rewrite — that's Stream A's domain.**

4. **MDPS QG re-run** after the chain-bundle fan-out fix lands. Currently
   `test_per_instrument_pipeline.py::TestPerInstrumentPipelineFix::test_legacy_ticks_parquet_recovers_instrument_id_from_data`
   fails. Once Stream A's MDPS edits commit, run `cd market-data-processing-service && bash scripts/quality-gates.sh`
   and flip the corresponding todo in `mtds_canonical_sharding_alignment_2026_03_31.plan.md`.

5. **CanonicalParquetReader Phase 1.5 axis extensions** (added this session in PM `527d3f91`):
   - DeFi `chain` axis — UAC `CHAIN_RPC_TEMPLATES` already exists; can extend `CanonicalParquetReader.read_shard()`
     signature with `chain: str | None = None` validating against those keys. **Defer if Stream A is mid-flight on
     `reader.py`.**
   - Prediction `canonical_question_group` axis — gated on UAC SSOT for `market_id → canonical_question_group` mapping
     (per HANDOVER line 143, "most likely greenfield bit"). **Don't build until that SSOT lands** — owned by Stream A.

### P2 — Independent UI track (untouched this session)

6. **Phase 0 UI blockers** in `instruments_and_market_tick_data_completion_2026_05_01.plan.md`:
   - Day-shard infinite scroll (`deployment-ui/src/components/DataStatusTab.tsx#L4480` `.slice(0, 60)` limit).
   - CSV download headers-only bug (deployment-api endpoint inconsistency).
   - Sports league/day CSV button wiring.
   - Schema modal coverage across data types.
   - ~2-3 days of UI work. Independent of Streams A/B. Confirm with user before starting.

### Sports / Phase 0 prediction picture

The active sports stream (`features_sports_honest_coverage_2026_05_05.plan.md`) is owned by yet another agent track.
Memory `project_features_sports_honest_coverage_2026_05_05.md` has the latest. CosmicTrader has shipped useful fixes
there — `git log --since=2026-04-29` across deployment-service / deployment-api / unified-trading-system-ui /
unified-trading-pm / unified-api-contracts / instruments-service / market-tick-data-service before touching that
surface.

---

## Things you must NOT do

- **Don't build NormalisingManifestWriter as a wrapper class.** Phase 1.5a-2 is explicitly SUPERSEDED by Stream A's
  in-class write-gates. Per HANDOVER coordination rule: "Don't build a parallel mechanism."
- **Don't autonomously run gcloud / production migrations** — Phase 1.5a-3 vault rename + Phase 1.5a-4 disk migrations
  need operator approval. Ask first.
- **Don't quickmerge** with concurrent dirty deps. UTL is 1 commit behind origin AND dirty in working tree (CosmicTrader
  mid-edit on the write-gate work). If you commit anything that depends on UTL, push UTL first or use direct `git push`
  like this session did. See workspace CLAUDE.md "Push before quickmerge" rule.
- **Don't run quickmerge with `--dep-branch`** — agent-mode is forbidden; quickmerge reads `active_feature_branch` from
  `workspace-manifest.json` automatically (currently `live-defi-rollout`).
- **Don't try to fix the MDPS test failure** — it's in Stream A's lane. CosmicTrader has in-flight
  `candle_write_mixin.py` + `live_workers.py` edits (visible in `git stash list` if needed) that simplify the fan-out
  and resolve the regression.
- **Don't archive plans without `[unlock-plan]`** in the commit — every active MTDS plan is
  `locked_by: live-defi-rollout`.

---

## Repo state snapshot at handoff

| Repo                             | HEAD       | Origin in-sync?         | Dirty (not yours)                                                                                                        |
| -------------------------------- | ---------- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `unified-trading-pm`             | `94213212` | ✓                       | `WORKSPACE_MANIFEST_DAG.svg` + `workspace-manifest.json` (advisory regen)                                                |
| `market-tick-data-service`       | `eeb03c3`  | ✓                       | clean                                                                                                                    |
| `unified-api-contracts`          | `9599e8fb` | ✓                       | `registry/__init__.py` (CosmicTrader in-flight)                                                                          |
| `unified-trading-library`        | `2bfac941` | ✗ origin ahead 1 commit | `__init__.py` + `manifest_writer.py` + new `tests/unit/test_manifest_writer_cluster_coverage.py` (CosmicTrader Stream A) |
| `market-data-processing-service` | `1dfae3b`  | ✓                       | clean                                                                                                                    |

When you start, run `git fetch origin && git status` in each repo before any action.

---

## Plans state at handoff

**Active (5):**

- `cefi_tradfi_tick_data_backfill_2026_04_10.plan.md` — TradFi MVP closeout almost done (98.8% coverage); ES_OPT
  2020-2022 fill VM still running per memory; phantom-audit port for tradfi outstanding.
- `instruments_and_market_tick_data_completion_2026_05_01.plan.md` — Phase 0 UI blockers + sports backfill verifications
  outstanding.
- `market_tick_data_to_100pct_2026_05_05.plan.md` — Phase 1.5a 1+2+3 done/superseded; 1.5a-3 vault rename + 1.5a-4
  deferred to Stream A; main Phase 1.5 manifest rebuild blocked on Stream A landing.
- `mtds_canonical_sharding_alignment_2026_03_31.plan.md` — MTDS QG green; MDPS QG blocked on Stream A.
- `mtds_per_instrument_download_api_2026_04_24.plan.md` — Phase 1 done; new Phase 1.5 (DeFi chain + Prediction
  canonical_question_group axes) added 2026-05-06; gated on Stream A's UAC SSOTs.
- `shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md` — active stream, locked.

**Recently archived (2):** `mtds_defi_data_normalization_2026_04_14` +
`mtds_multi_dimensional_shard_architecture_2026_04_12` — both per existing `superseded_by:` frontmatter, with
`[unlock-plan]` in PM `3697c3f1`.

---

## First-message protocol when you start

1. Run `git fetch origin` across all 5 repos.
2. Re-pull this handoff doc (`HANDOFF_NEXT_AGENT_2026_05_06.md`) — it may have been updated.
3. Confirm with the user what they want next — most likely: P0 item 1 (vault venue rename in prod with their approval)
   OR P2 item 6 (UI work) OR continue Stream A audit follow-ups. Don't assume.
4. Update your TodoWrite list before touching code.

Good luck.
