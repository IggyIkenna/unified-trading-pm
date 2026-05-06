# Handover — Master Plan Audit (continued from 2026-05-06)

**You are picking up from a multi-stage plan-vs-plan audit + reduction session.** The previous agent reduced active
plans from 148 → 88 across 8 stages, made 3 architectural decisions, shipped one UTL fix, and identified scope-clarified
resolutions for two would-be code refactors. This doc tells you what's done and what's left.

---

## 1. Current state (read these first, in this order)

1. `unified-trading-pm/plans/active/master_to_live_defi_2026_05_23.plan.md` — the master plan (Q&A 1-16, drift-audit
   table, risk register, week-by-week DAG, 7-group/23-item readiness checklist).
2. `unified-trading-pm/codex/10-audit/MASTER_READINESS_LIVE_DEFI_2026_05_23.md` — codex SSOT companion (durable
   readiness model + doc-touchpoint map).
3. `unified-trading-pm/cursor-configs/CLAUDE.md` "Master Plan" section — pointer to both, doc-as-intent principle.
4. Memory entry `project_master_plan_audit_session_2026_05_06.md` — full session log with commit SHAs.

**Active branch**: `live-defi-rollout`. Today: 2026-05-06. Live DeFi cutover deadline: 2026-05-23.

---

## 2. What's already done

### Plan archives (60 total)

- 17 self-tagged superseded (commit `c5532ae8`)
- 21 reference-only / 0-todo plans (`0c34d59c`)
- 7 MEDIUM folded into cluster leads (`a8665b70`)
- 1 archive + 12 todo flips (`e99d95ad`)
- 3 likely-shipped (`a8fe96e7`)
- 5 cluster-fold archives (`ee268683`)
- 6 cluster-fold archives (`2d8dab48`)

### Code changes shipped

- **UTL `ba83a6f1`** — `check_shard_freshness` extended with `retry_failed: bool = True` param (default-on);
  `ATTEMPTED_FAILED` rows treated as stale. Unblocks sports flip-and-retry; `truthset_recovery` DELETE-shard hack now
  optional. 8 unit tests in `test_check_shard_freshness_retry_failed.py`.

### RESOLVED-by-re-read (no code shipped, just plan + doc updates)

- **UAC `ES_OPTIONS_CLUSTERS` rename** — earlier proposal was a misread. The 11-cluster ES taxonomy IS genuinely
  ES-specific (CME futures regex). When Deribit BTC etc. land, add **sibling symbols** (`DERIBIT_BTC_OPTIONS_CLUSTERS` +
  extractor + calendar fn), not a generic dispatcher.
- **MTDS orchestrator bundle-check wiring** — already implemented at `engine/orchestrator.py:2126-2193` for ES.OPT
  (CME-OPTIONS venue branch). Generalisation to non-ES bundle types deferred until 2nd bundle adapter exists.

### Architectural decisions made (Q&A 14-16 in master plan)

- **HIGH-1 VIX 15m source layering**: Phase 3b in `cefi_tradfi_tick_data_backfill_2026_04_10` is **OBSOLETE**. CLAUDE.md
  "VIX 15m source layering" SSOT is canonical: Yahoo serves post-`BARCHART_VIX_LAST_DATE`, `2025-11-13 → today−60d` is
  honest gap.
- **HIGH-2 sports `data_available_at` → `available_at`**: rename sports adapters +
  `InstrumentsWriteGate.DEFAULT_AS_OF_COLUMNS` + one-time GCS column migration. **NOT yet shipped — code change
  pending.**
- **HIGH-3 `_create_full_day_empty_output` delete (writegate Phase 2.A)**: Option A — audit consumers, delete iff safe.
  **NOT yet shipped — needs grep audit.**

---

## 3. What's left (priority order for next session)

### A. Pending code changes from Stage 6 decisions

**A1. Sports `data_available_at` → `available_at` rename (HIGH-2).**

- Sports adapters (instruments-service `instruments_service/reference_data/adapters/sports/...`) currently write
  `data_available_at`.
- `InstrumentsWriteGate.DEFAULT_AS_OF_COLUMNS` lists `data_available_at`.
- UTL `assert_available_at_present` checks for canonical `available_at`.
- Action:
  1. Grep workspace for every `data_available_at` write site + `DEFAULT_AS_OF_COLUMNS` reference.
  2. Rename adapters to write `available_at`.
  3. Update `InstrumentsWriteGate.DEFAULT_AS_OF_COLUMNS` to use `available_at`.
  4. Write one-time migration script `instruments-service/scripts/migrate_sports_available_at_column.py` that renames
     the column in existing GCS sports parquets (per "manifest migration not fallback" rule).
  5. Run migration on a same-region GCE VM (cross-region is 18× slower).
  6. Quality-gate sports adapters; verify writegate Phase 2.C `LookaheadBiasError` strict-mode no longer hard-fails on
     sports.
- Required before writegate Phase 2.C ships.

**A2. `_create_full_day_empty_output` consumer audit + delete (HIGH-3).**

- File: `market_tick_data_service/adapters/tradfi/ohlcv_passthrough.py:89` (and any other adapters with same helper).
- Action:
  1. Grep features-volatility + features-cross-instrument + features-delta-one source for `market_state == "CLOSED"` and
     `market_state ==` patterns.
  2. If zero consumers → delete `_create_full_day_empty_output`. Replace with
     `record_empty(capture_status=empty_confirmed)` for closed days.
  3. If consumers exist → refactor consumers to read manifest `capture_status == empty_confirmed` instead of in-row
     `market_state == "CLOSED"`.
- Then unblock writegate Phase 2.A.

**A3. New codex doc: "empty upstream means no expectation of data downstream"** — **SHIPPED 2026-05-06.**

- Doc: `unified-trading-pm/codex/02-data/honest-absence-downstream-handling.md` (new dedicated downstream-consumption
  SSOT; manifest doc remains write-side SSOT).
- Cross-references: bidirectional with `availability-manifest-and-data-status.md` § 6 + CLAUDE.md "Honest absence vs
  fake placeholders" principle.
- Content shipped: principle statement, three causes of "no data" (calendar / honest empty / unexpected pipeline gap)
  with different downstream actions, MUST-NOT list, MAY tolerance patterns (NaN passthrough / rank skip /
  bounded-forward-fill / drop-with-min-rows / per-row available*at gating), per-service pre-flight responsibility,
  anti-pattern catalogue (`fillna(0)`, sentinel values,
  `\_create*\*\_empty_output`placeholders,`--skip-dependency-check` bypass), reference incidents.

### B. Stage 6 MEDIUM/LOW conflict items not yet shipped (from earlier audit, deferred)

**B1. NaN-ratio threshold migration timing** — features-onchain `WriteGateConfig.nan_threshold = 0.95` is
workspace-default-tuning. Once UAC `feature_group → nan_threshold` SSOT lands per writegate plan, migrate
features-onchain to consume the per-group lookup; keep 0.95 as a per-DeFi-feature_group override in UAC, not a global
default.

**B2. Callsite count drift** — `shard_granularity_ssot_propagation_2026_05_06.plan.md:981` says "17 callsites" of
`_create_empty_output`. writegate Phase 0 audit found 37 actual callsites (16 A / 15 B / 5 C / 2 ?). Update
shard_granularity reference to point at writegate Phase 0 audit.

**B3. `flush()` vs `write()` pattern note** — codify in writegate Phase 5 reconcilers section + CLAUDE.md: one-shot
scripts use `flush()`; long-running services use `write()` (the 30s throttle is intentional for the latter).

**B4. Sports Phase 0.6 sequencing prereq** — features_sports_honest_coverage Phase 0.6 launches
`features-sfi-progressive-` VM that reads from `progressive_stats` reference data. Add prerequisite: "verify no
`sfi-backfill-*` VMs RUNNING before launch."

**B5. CSV endpoint axes extension** — `instruments_and_market_tick_data_completion_2026_05_01.plan.md:125` declares
unified CSV endpoint signature `(service, asset_group, venue, day, instrument_type, data_type, [instrument_ids])` — 7
axes. Predictions plan adds `canonical_question_group` axis; multi-axis plan adds `chain` for DeFi. Extend endpoint
signature todo to include both as optional axes per CLAUDE.md per-asset-group shard-key matrix.

### C. More plan-vs-plan audits on the 88-plan set

Earlier audits flagged these candidates for fold-or-archive but they weren't shipped this session — re-audit and decide:

- `cefi_venue_universe_expansion_2026_05_01` Phase 1 (BITFINEX / BITGET / KRAKEN) — likely shipped per fleet evidence;
  flip done. Phase 2 (Extended / Pacifica / Lighter DEX-perps) is genuine open work.
- `data_pipeline_completion_2026_04_18` and `defi_data_types_completeness_2026_04_24` are already archived this session
  — verify nothing else points at them.
- Other smaller fold candidates on the 88-plan set — run a fresh Stage 7 audit (mirror the Stage 5 audit prompt; same
  agent type).

### D. Codex docs vs plans alignment audit (user explicit ask)

> "make sure that Codex docs are updated to not conflict, or vice versa, the plans are updated if the Codex docs look
> like a smarter implementation."

This is its own pass:

- For each codex SSOT doc in `unified-trading-pm/codex/`, identify which active plans reference it.
- Cross-check: does the plan's proposed implementation match the codex doc's design?
- If codex is current + plan is stale → update plan, don't update codex.
- If plan describes a refinement that should be SSOT → update codex first, then update plan to point at codex.
- Drift between codex / plan / code is a review-blocking failure per master plan principle "docs are the intent."

### E. CLAUDE.md + memory ongoing alignment

Stage-5b updates landed `869942d4`. As more plans get archived in Stage 7+, the CLAUDE.md references and master plan
service-readiness matrix may need further updates. Don't rewrite MEMORY.md historical entries — they accurately describe
what was true at the time of the session they document.

---

## 4. Critical workflow rules (from this session's painful lessons)

- **`live-defi-rollout` is the active branch.** Commit + push directly; no quickmerge when dep repos are dirty (per
  CLAUDE.md 2026-05-06 rule).
- **Prettier reformats files mid-commit.** When commits silently fail (no error in tail), `git status --short` — if
  `MM`, prettier rewrote them. Re-stage with `git add` and retry.
- **Conventional Commits hook** restricts types to `build chore ci docs feat fix perf refactor revert style test`. Use
  `docs(...)` for plan archive commits with `[unlock-plan]` tag in message body.
- **Don't touch other agents' uncommitted work.** Always stage MY files specifically (`git add path/to/specific/file`),
  never `git add -A`. PM repo will frequently have other agents' WIP.
- **`MEMORY.md` historical entries are accurate to their session timestamp.** Do NOT rewrite them retroactively — they
  document what was true at the time.
- **Plan archive workflow**: `git mv plans/active/X.plan.md plans/archive/X.plan.md` then commit with `[unlock-plan]` in
  message body. Do NOT use destructive git operations.

---

## 5. Reduction trajectory

| Stage | Action                                    | Active count | Commit     |
| ----- | ----------------------------------------- | -----------: | ---------- |
| Start | initial inventory                         |          148 | —          |
| 1     | 17 self-tagged superseded                 |          130 | `c5532ae8` |
| 3a    | 21 reference-only / 0-todo                |          108 | `0c34d59c` |
| 3b    | 7 MEDIUM folded                           |          101 | `a8665b70` |
| 4a    | 1 archive + 12 todo flips                 |          100 | `e99d95ad` |
| 4b    | 3 likely-shipped                          |           98 | `a8fe96e7` |
| 5a    | 5 cluster-fold                            |           94 | `ee268683` |
| 5b    | 6 cluster-fold                            |           88 | `2d8dab48` |
| Refs  | CLAUDE.md + master plan stale-ref updates |           88 | `869942d4` |

---

## 6. Headline goal (still locked in)

Two DeFi archetypes trade live on real wallet ≥7 continuous days by 2026-05-23: `carry_staked_basis` (ultimate priority
— recursive LST staking + perp short hedge) + `leveraged_funding_arb` (cross-venue funding spread). Six perp venues
live: Bybit / Deribit / Binance / OKX (CeFi) + Hyperliquid / Aster (DeFi DEXs). Copper wired DeFi-side, CEFFU manual for
Binance. Full AWS↔GCP cloud parity (data + batch + ML + live + monitoring).
