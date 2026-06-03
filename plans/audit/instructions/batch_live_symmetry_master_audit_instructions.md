---
name: batch_live_symmetry_master_audit_instructions
type: audit-instructions
epic: batch_live_symmetry_master
assigned_vm: vm-cross-cutting
tier: L4
last_updated: 2026-06-03
---

# Batch=Live Symmetry Master — Audit Instructions

## Epic Scope

Per-service batch=live audit across all 19 epic code surfaces. Reconciliation scripts. The invariant: batch and live are
operational modes of the SAME pipeline — identical schemas, data_types, fields. Banned: separate live-only data_types;
distinct field sets; `available_at` derived at read-time.

Codex SSOTs: `codex/02-data/service-output-emission-semantics.md`,
`plans/active/writegate_honest_coverage_endtoend_2026_05_06.md`,
`codex/02-data/pipeline-mode-and-batch-live-reconciliation.md`

`pipeline_mode` is the column that makes batch↔live reconciliation a `GROUP BY pipeline_mode` over the SAME manifest.
Implementation shipped via `plans/active/pipeline_mode_implementation_2026_05_28.md` (Phases 0–6 complete) +
audit/derivation sub-doc `plans/active/pipeline_mode_audit_2026_05_28.md`. The on-disk `pipeline_mode=` partition is the
one deferred piece (Phase 5 → named successor `pipeline_mode_partition_migration_<next-window-date>.md`, lands at the
next whole-corpus migration window). This audit is the continuous-verification surface that catches regressions of that
work and any future asset_group that needs pipeline_mode column-fill / manifest or GCS backfill.

## Triggers

- Weekly (minimum cadence)
- After any new adapter ships (must verify both modes present **and** that the adapter sources `pipeline_mode` from the
  UTL resolver — see checklist (g))
- When A3 manifest divergence shows `DIVERGENT_EMPTY` (batch/live parity gap)
- After any writegate phase change
- **Before any whole-corpus GCS migration window** — the deferred `pipeline_mode=` on-disk partition (Phase 5 successor)
  must be bundled into that walk per single-walk discipline; this audit flags it if still pending.
- After any new asset_group bucket is provisioned (must verify its manifest rows carry non-null, in-enum
  `pipeline_mode`)

## Checklist

- [ ] (a) **Batch adapter count == live adapter count**: for every service and every asset_group. Run:
      `python3 plans/audit/results/a6_batch_live_adapter_parity.py` — report any gaps (batch_count ≠ live_count)

- [ ] (b) **No standalone live-only data_types**: every data_type that exists in `--mode live` also exists in
      `--mode batch` for the same service. Grep: `rg "mode.*live\|live.*only" --include="*.py"` — review any hits for
      data_type isolation

- [ ] (c) **No distinct field sets between live and batch**: the schema for each data_type is identical regardless of
      mode. Check: `a1_scan_codified_shape_compliance.py` output — no schema divergence between modes

- [ ] (d) **available_at not derived at read-time**: no adapter sets `available_at` from `datetime.now()` or equivalent
      at the point of consumption/reading. Grep:
      `rg "available_at.*datetime.now\|available_at.*utcnow" --include="*.py"` — should be 0 hits in live adapters
      (write-time derivation only is permitted)

- [ ] (e) **All services have --mode batch and --mode live in CLI**: every service CLI exposes both modes. Grep:
      `rg "\-\-mode.*batch|\-\-mode.*live" --include="*.py"` across all service entry points

- [ ] (f) **a6 script runs clean**: `a6_batch_live_adapter_parity.py` produces a report with no unclassified rows (every
      adapter is either "paired" or "BLOCKED-CREDENTIALS"). Run:
      `python3 plans/audit/results/a6_batch_live_adapter_parity.py` — zero unclassified rows

- [ ] (g) **`pipeline_mode` populated + in-enum across ALL asset_groups**: every captured manifest row carries a
      non-null, in-`PipelineMode`-enum value. For each asset-group bucket (cefi env-tiered + legacy, defi, tradfi,
      sports, prediction, instruments-store-\*) and its `_index/per_vm/` shards, confirm
      `count(*) WHERE pipeline_mode IS NULL OR pipeline_mode = ''` equals 0 (or a documented exempt count for an active
      VM writing pre-Phase-2 rows). Re-run `unified-trading-pm/scripts/migration/backfill_pipeline_mode.py --verify` per
      bucket. Any non-zero non-exempt count → a backfill/migration is owed; file it against `batch_live_symmetry_master`
      (NOT a silent defer).

- [ ] (h) **No inline `pipeline_mode` string literals at write sites**: every writer sources its value from
      `unified_trading_library.events.resolve_pipeline_mode(...)` or a `PipelineMode.X` enum member — no raw string
      literals. QG STEP 5.85 enforces; confirm it is green workspace-wide and that any new writer (new adapter / new
      service) was added to the sweep. Grep cross-check:
      `rg -n "pipeline_mode\s*=\s*[\"']" --glob '!*.venv*' --glob '!node_modules' --glob '!tests'` — review every hit.

- [ ] (i) **Reconciliation actually groups by `pipeline_mode`**: `batch-live-reconciliation-service` stage0
      distinguishes batch vs live row sets for the same shard via `_is_batch_mode()` / `_is_live_mode()` predicates (not
      an empty-column no-op). Reconciliation tests fail when `pipeline_mode IS NULL` appears in input.

- [ ] (j) **Deferred on-disk partition tracked, not lost**: confirm the Phase 5 successor
      `pipeline_mode_partition_migration_<next-window-date>.md` either (i) does not yet exist because no whole-corpus
      window has occurred, or (ii) exists and is scheduled into the upcoming window. A migration window that walked the
      corpus WITHOUT bundling the `pipeline_mode=` partition is a finding (single-walk discipline breach).

- [ ] (k) **Different-source batch↔live equivalence + accepted-divergence register (codified 2026-06-03)**: items
      (a)–(f) prove batch and live adapters EXIST in equal count with identical schema / field sets; this item proves
      that where batch and live acquire the SAME cell from a **different upstream source**, the two are _semantically_
      equivalent — count parity (a6) is blind to a live WS path that produces a different shape/cadence than the batch
      source. **Step 1 — enumerate the different-source pairs**: for every (service, asset*group, venue, data_type),
      record the batch upstream vs the live upstream from `codex/02-data/mtds-data-source-coverage-matrix.md` + the
      adapter code. Known classes: CeFi `trades` / `book_snapshot_5` = Tardis bulk CSV (batch) vs venue WebSocket
      (live); DeFi DEX = The Graph subgraph-historical (batch) vs subgraph-current / WS (live); Solana DEX
      (Orca/Raydium/Drift/Phoenix) = S3 archive / RPC snapshot (batch) vs WebSocket (live). **Step 2 — verify
      equivalence** on an overlapping window: same \_populated* field set (not merely same schema), comparable
      cadence/granularity, and a 1-pair reconciliation fixture where the two sources agree on overlapping-timestamp
      values within tolerance (no systematic shift, no field one source carries that the other silently drops). **Step 3
      — accepted-divergence register**: any pair that diverges BY DESIGN (e.g. Morpho batch skipped — no historical
      subgraph; Solana DEX snapshot-vs-WS granularity; any live-only or batch-only data_type) MUST appear in an explicit
      register in the result:
      `venue | data_type | batch_source | live_source | divergence | why-accepted | tracking-plan`. **An undocumented
      different-source divergence is RED** — a6 passing while the live source emits a different tick shape is the exact
      blind spot this item closes. GREEN = every different-source pair either reconciles on its overlap window OR is in
      the accepted-divergence register with a named tracking plan; zero silent divergences. Cross-ref:
      `mtds_mdps_master` item (k) (per-venue acquisition-method registry), `defi_master`, `cefi_master`.

### E2E Cross-Cutting Verification

- (e2e-batch-live) **Batch-live round-trip**: pick one (venue, data_type) pair, run batch adapter → confirm manifest row
  → run live adapter → confirm same schema row. Requires only one working adapter pair, not all.
- (mock-upstream) **Independent audit**: cross-cutting audits MUST be runnable with `CLOUD_MOCK_MODE=true` to test
  infrastructure, error classification, and isolation patterns without real cloud access.

## Success Criteria

- All 11 checklist items (a)–(k) GREEN
- `a6_batch_live_adapter_parity.py` shows 100% adapter parity (every batch adapter has a live counterpart)
- A3 manifest divergence: zero `DIVERGENT_EMPTY` across all services
- `count(*) WHERE pipeline_mode IS NULL OR pipeline_mode = ''` = 0 (or documented exempt) across every asset-group
  manifest + per-VM shard; QG STEP 5.85 green; deferred `pipeline_mode=` partition tracked against its named successor

## Output Format

Result file at `plans/audit/results/batch_live_symmetry_master_audit_YYYY_MM_DD.md`. Same structure as per
`../README.md`.

## Linked Results

| Date                      | Result file | Status |
| ------------------------- | ----------- | ------ |
| (populated as audits run) |             |        |
