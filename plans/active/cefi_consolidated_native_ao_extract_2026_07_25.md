---
doc_type: plan
title: CeFi consolidated closeout — native todo AO extraction (2026-07-25)
summary: >-
  Fresh AO-eligibility triage of cefi_consolidated_closeout_2026_07_18.md's OWN 32 native `- [ ]` todos (not the
  satellite-doc digest, already covered by cefi_satellite_ao_dispatch_batch1_2026_07_25.md). Classified every open
  native todo against task_template.md §4's bounded-outcome bar. 12 survive as AO-eligible (2 split off a code-only
  slice from a mixed code+prod-op parent todo; 2 Track-7 sub-items merged into 1 to preserve verify-before-backfill
  ordering without serializing the whole plan). 20 stay human — mostly real judgment/coordination/operator-gated work on
  the live Track-1/Track-8 canonicalization migration critical path, but a materially-sized subset (5 of the 20: the 3
  carried-over "execution log" todos at the parent's lines 690/692/694, plus line 701's writer-fix half and the line-870
  P0) are STALE — their underlying work already shipped per the parent doc's own later Deferred-work-table entries and
  cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md Finding 5, but the parent's checkboxes were never
  flipped. 2 of the 12 AO-eligible candidates (BITGET-FUTURES catalogue rollup, _DRYRUN_COLS fix) are net-new scoped
  tasks derived from that staleness finding, not literal re-drafts of a stale line.
status: draft
nature: process
asset_group: [cefi]
stage: [data]
repos:
  [
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    deployment-api,
    unified-api-contracts,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, native-extraction, stale-checkbox-audit]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_consolidated_closeout_aggregated_sources_2026_07_24.md,
    /plans/active/cefi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/cefi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md,
    /plans/active/cefi_4surface_migration_execution_log_2026_07_24.md,
    /plans/active/issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 2.2
estimate_calibrated_ai_days: 1.8
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Operator-directed fresh AO-eligibility triage (2026-07-25) of cefi_consolidated_closeout_2026_07_18.md's OWN 32 native
  `- [ ]` todos, deliberately distinct from the satellite-doc digest extraction already shipped as
  cefi_satellite_ao_dispatch_batch1_2026_07_25.md (which never touched this parent doc's native todos).
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# CeFi consolidated closeout — native todo AO extraction

> **Status: draft.** Per CLAUDE.md's plan-destination rule, never auto-shipped to `active` — flip only after operator
> review. All 12 todos below are same-priority-within-doc and touch distinct files (verified per-todo below; the one
> real ordering dependency, Track 7's verify-then-backfill, was resolved by MERGING the two steps into one todo rather
> than relying on plan-file order, since same-priority todos dispatch concurrently by design) so they are safe to
> dispatch concurrently once activated.

## Per-todo classification (all 32 native open todos in the parent doc)

Full table cited in the session report (not duplicated here per the "plan references, doesn't duplicate" rule) —
summary: **12 AO-eligible** (drafted below), **20 stay human**, of which **5 are flagged STALE/likely-already-resolved**
(need a checkbox reconciliation, not fresh dispatch — see the finalize plan's todo 2) and the rest are genuine
judgment/coordination/operator-gated work on the live Track-1/Track-8 migration critical path (the DERIBIT quote fix +
prod/catalog.parquet rebuild, the Track-1 cutover itself, the POST-CUTOVER smoke-check flip, the enumeration-audit
terminal checkpoint, the Track-2 backfill resume + its MID/POST checkpoints, the two already-`[OPERATOR]`-tagged items,
the two scope-unclear/decide-the-cadence items, the PM consolidate+archive todo that edits this same parent doc, and 3
items explicitly "FENCED" to another named agent/live process).

## Todos

- [ ] [REVIEW] P2. **Resolve the `*_ccxt.py`/`*_native.py` parallel-file question for BINANCE/BYBIT/OKX.** Audit
      `instruments-service/.../adapters/cefi/tardis/`, MTDS's `.../adapters/cefi/`, and every cefi venue file in
      `execution-service/.../trade_execution/adapters/` for dead code, stale fallback paths, and duplicate logic: is
      each `*_ccxt.py`/`*_native.py` pair genuinely both live-routed by design, or is one file in the pair dead code
      nothing calls? Cite `/codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md`. If a file is confirmed
      dead (nothing calls it, no shim needed), delete it in the same pass — this is ordinary dead-code removal, not a
      prod-data delete, so no `[OPERATOR]` gate applies. Repos: instruments-service, market-tick-data-service,
      execution-service. **Done when**: a written per-venue verdict (both-live-with-reason, or
      one-dead-then-deleted-no-shim) for binance/bybit/okx is recorded in this plan's Progress Log or a new issue doc;
      any deletion ships with `quality-gates.sh` green. Source: `cefi_consolidated_closeout_2026_07_18.md` (Track 5).
- [ ] [DATA] P3. **Sweep for any non-Tardis cefi VM class with multi-hour+ single-VM runtime that is not already
      cross-machine-sharded** (Tardis-consuming VMs are EXEMPT — hard concurrency cap of 1, see
      `/codex/05-infrastructure/vm-launcher-runbook.md` § Tardis cap). Repo: deployment-service (read-only fleet audit).
      **Done when**: a list of every non-Tardis cefi VM class with its measured typical runtime, a PASS/FAIL verdict per
      class against the "shard across machines once multi-hour+" bar, and a follow-up todo filed for each FAIL, is
      recorded in this plan's Progress Log. Source: `cefi_consolidated_closeout_2026_07_18.md` (Track 6).
- [ ] [DATA] P1. **Run `/data-pipeline-check-is` for cefi as a dated PRE-BACKFILL baseline** (independent of when the
      Track-2 coverage backfill itself actually launches — establishes a dated reference point regardless). Repo:
      instruments-service (skill run, no code change). **Done when**: the skill's report path + run date is cited in
      this plan's Progress Log. Source: `cefi_consolidated_closeout_2026_07_18.md` (Track 2 checkpoint cadence).
- [ ] [DATA] P1. **Run `/data-pipeline-check-mtds` for cefi as a dated PRE-BACKFILL baseline** (same independence
      rationale as the `-is` baseline above — a real dated run distinct from any prior skill-upgrade-only todo). Repo:
      market-tick-data-service (skill run, no code change). **Done when**: the skill's report path + run date is cited
      in this plan's Progress Log. Source: `cefi_consolidated_closeout_2026_07_18.md` (Track 2 checkpoint cadence).
- [ ] [BACKEND] P1. **Land the already-shipped deployment-api "data status" axis-value-census restoration via
      quickmerge, once its blocking dirty deps are actually clear.** Code is COMPLETE and `quality-gates.sh`-green
      already (`.qg_last_passed_sha` written at a specific HEAD — re-verify the sentinel still matches current HEAD
      before running anything, since the working tree may have moved since the parent doc's note was written). First:
      re-check whether the 3 previously-DIRTY sibling deps (`unified-trading-library`, `unified-api-contracts`,
      `deployment-service`) are now clean (no live/recently-touched WIP on the same fold-A cross-repo migration cited in
      the parent doc). If clear, run the exact cited command:
      `cd deployment-api && bash scripts/quickmerge.sh     "feat(data-status): restore raw manifest axis-value census — non-canonical-naming / duplication detector     (Track-8)" --agent --files 'deployment_api/routes/data_status/__init__.py     deployment_api/routes/data_status/_axis_census.py tests/unit/test_route_data_status_axis_census.py     deployment_api/services/data_status/manifest.py'`.
      If any of the 3 deps is still genuinely live/dirty, do NOT inherit-commit through it (per multi-agent safety) —
      record the still-blocked status instead and leave the parent todo open. Repo: deployment-api. **Done when**:
      either the quickmerge lands (cite the resulting commit + a green CI run per `gh run list`), or a recorded
      confirmation that the dep is still genuinely live (with evidence) and the todo remains blocked. Source:
      `cefi_consolidated_closeout_2026_07_18.md` (Track 8, POST-CUTOVER "data status" enumeration item).
- [ ] [DATA] P2. **Confirm UPBIT's live-wiring status in the cefi manifest.** UPBIT is codex-MVP
      (`/codex/02-data/mvp-scope-canonical.md`) but has zero mentions anywhere in the parent plan's audit trail. Query
      the live cefi manifest for `venue=UPBIT` captured-row counts and check for any open backfill/issue doc. Repo:
      instruments-service (read-only). **Done when**: a recorded row count + PASS/FAIL verdict against the MVP
      definition is landed in this plan's Progress Log (or a new issue doc if a real gap is found). Source:
      `cefi_consolidated_closeout_2026_07_18.md` (MVP universe section).
- [ ] [DATA] P2. **Verify + execute the Track-7 candle bundle-collision fix for the remaining 6 of 8 affected days (one
      combined todo — the backfill step in part (b) must only run if part (a) confirms raw-tick presence for ALL 8 days,
      so this is written as one linear task rather than two concurrently-dispatchable todos, avoiding the need to
      serialize this whole plan for a single ordering dependency):** (a) Verify raw-tick presence in `raw_tick_data/`
      for the remaining 6 of 8 affected `(day, venue)` cells (2023-06-01, 2023-08-02, 2024-02-01, 2024-02-02,
      2025-11-01, 2026-01-01 for BYBIT `futures_chain`/DERIBIT `options_chain` — 2023-11-02 and 2024-07-01 already
      confirmed present). (b) ONLY if all 8 days confirm raw-tick presence: run the targeted MDPS candle backfill
      (`--force`) for all 8 affected `(day, venue)` cells against PROD, and verify the regenerated `ticks.parquet`
      bundles contain every leg's data (row/symbol count check against the pre-delete per-leg object count) — not just
      the previous race-winner's. Do NOT delete the 149 stale legacy per-leg objects listed in
      `plans/audit/results/cefi_todo19_149_residual_objects_2026_07_23.csv` — that step stays `[OPERATOR]`-gated in the
      parent doc, out of scope here. Repos: market-data-processing-service, market-tick-data-service. **Done when**: (a)
      has a recorded PASS/FAIL raw-tick-presence verdict for each of the 6 days (with the 2 already-known days re-stated
      for completeness); if all 8 pass, (b)'s regenerated-bundle verification (per-leg data present, row counts matching
      pre-migration per-leg totals) is recorded in this plan's Progress Log or the source issue doc; if any of the 6
      days fails presence, this todo stops at (a) and records why, without attempting (b). Source:
      `cefi_consolidated_closeout_2026_07_18.md` (Track 7).
- [ ] [BACKEND] P1. **Fix the MTDS writer-side `:PERP:` → `:PERPETUAL:` shorthand emission for HL/LIGHTER/ASTER cefi
      captures (writer-side code fix ONLY — no data motion).** The manifest-side rewrite already shipped
      (`instruments-service@555ddf1c`, Script 3's `resolve_canonical`), but new captures for these venues can still
      write the `VENUE:PERP:RAW` shorthand at source. Locate the cefi capture write path that stamps `instrument_type`
      for HL/LIGHTER/ASTER perpetuals (grep for the literal `PERP` instrument-type constant in the cefi capture handlers
      under `market-tick-data-service/market_tick_data_service/market_interface/`) and change it to emit `PERPETUAL`
      directly, mirroring the same decompose logic already proven correct in
      `market-tick-data-service/scripts/_cefi_canonical_resolver_migration_2026_07_18.py`'s `resolve_canonical`. This is
      safe to ship alone (prevents future non-canonical writes; does not touch any existing GCS object) — the separate
      on-disk GCS content rename for the 374,272 already-written rows stays out of scope here (timing-coupled to the
      still-pending, human-coordinated Track-1 cutover). Repo: market-tick-data-service. **Done when**: new captures for
      HL/LIGHTER/ASTER perpetuals write `instrument_type=PERPETUAL` (never the `PERP` shorthand), proven by a
      new/extended unit test; `quality-gates.sh` green. Source: `cefi_consolidated_closeout_2026_07_18.md` (Track 8,
      `:PERP:` → `:PERPETUAL:` rewrite item — writer-side half only).
- [ ] [BACKEND] P1. **Enumerate every caller of `get_expected_instruments_for_venue` fleet-wide (audit only — the
      removal decision itself stays a separate `[OPERATOR]` todo in the parent doc).**
      `unified_api_contracts.registry.market_data_categories.get_expected_instruments_for_venue`
      (`market_data_categories.py`) still falls back to the per-venue MVP seed
      (`registry/defi_prediction_instrument_seeds.py`) when `instruments_provider` is None or a present catalogue lacks
      a specific venue. For each caller, record whether it depends on the fallback firing in the
      present-catalogue-missing-venue case (i.e., would silently regress if the fallback were removed). Repo:
      unified-api-contracts. **Done when**: a written caller list with a safe-to-remove/blocks-removal verdict per
      caller is recorded in this plan's Progress Log or a new issue doc — the actual removal decision is explicitly NOT
      this todo's job (that stays the parent doc's `[OPERATOR]` todo). Source:
      `cefi_consolidated_closeout_2026_07_18.md` (Operator dispositions, UAC per-venue seed fallback audit).
- [ ] [DATA] P1. **Build + run a dry-run + apply script to rename LIGHTER-ZKSYNC's ~11,283 bare-numeric-market-index GCS
      object stems to their resolved symbol form**, using the already-shipped `resolve_market_index()`
      (`instruments-service/instruments_service/reference_data/adapters/cefi/lighter.py`). Follow the established safe
      idempotent rename pattern already used elsewhere in this codebase (dry-run first → `--apply`: copy to the
      resolved-symbol path → crc32c-verify → delete the old numeric-stem source + write one captured manifest row per
      object), mirroring
      `market-tick-data-service/scripts/restamp_lighter_ohlcv_batch_tardis_to_lighter_api_2026_07_18.py`'s shape — this
      self-justifies the delete step per `task_template.md` §3 finding O (an established, already-proven-safe
      copy→verify→delete pattern, not a novel unreviewed delete). **Conflict-check / coordination requirement**:
      `cefi_satellite_ao_dispatch_batch1_2026_07_25.md` has a separate, already-dispatchable LIGHTER-ZKSYNC `ohlcv_1m`
      `pipeline_mode` repartition todo touching the SAME venue on a DIFFERENT mutation axis (partition path, not
      filename stem) — before running this todo's `--apply`, confirm that batch-1 todo has not started against
      overlapping objects; if it has, re-derive a safe order by reading both scripts' path-enumeration logic rather than
      assuming either order is safe. Repo: market-tick-data-service. **Done when**: the dry-run's planned-rename count
      is sane against the ~11,283 estimate (investigate if wildly different), the `--apply` run completes with
      `moved`/`already-done` for every enumerated object and zero unresolved collisions, and a fresh manifest query
      shows the LIGHTER-ZKSYNC numeric-stem objects resolved to canonical symbol form. Source:
      `cefi_consolidated_closeout_2026_07_18.md` (execution-log carryover, LIGHTER-ZKSYNC map item — the resolver itself
      already shipped per the parent's own Deferred-work table item 6; this todo is the remaining GCS rename).
- [ ] [DATA] P2. **Re-run the CeFi instrument catalogue rollup to resolve the 33 BITGET-FUTURES CME-letter-month gap
      rows** (`BTCUSDH26`-style dated futures currently at 0 catalogue rows against on-disk data that exists) — per the
      parent doc's own Deferred-work table item 5: the gap-measurement script is already shipped
      (`instruments-service@f6f16785`, live-measured 211 gap rows: OKX-SPOT 174, COINBASE-SPOT 4, BITGET-FUTURES 33),
      and BITGET-FUTURES "just needs a catalogue rollup re-run, no code change" — unlike OKX-SPOT/COINBASE-SPOT, which
      need an operator decision on widening UAC's `_CEFI_VENUE_QUOTE_EXTENSIONS` and stay out of scope here. Repo:
      instruments-service. **Done when**: a fresh run of the gap-measurement script (`instruments-service@f6f16785`)
      shows the BITGET-FUTURES CME-letter-month gap count at 0 (or explains any residual), cited with before/after row
      counts in this plan's Progress Log. Source: `cefi_consolidated_closeout_2026_07_18.md` (Deferred-work table
      item 5) — this exact candidate was previously identified and EXCLUDED from
      `cefi_satellite_ao_dispatch_batch1_2026_07_25.md` because its only citable source at the time was the
      too-large/risky `cefi_4surface_migration_execution_log_2026_07_24.md`; the same measured fact independently
      appears in this parent doc's own (stable, non-excluded) Deferred-work table, so it is re-drafted here from that
      stable citation instead.
- [ ] [SCRIPT] P2. **Confirm (and land if still missing) the dry-run chain-drop blind-spot fix in
      `complete_cefi_manifest_canonical_dedup_v2_2026_07_20.py`.** Grep-check whether `"chain"` is present in
      `_DRYRUN_COLS` today. **Context — downgraded from the parent doc's P0 because the acute risk has already passed**:
      per `issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` Finding 5, the Surface-C v2 `--apply`
      this blind-spot P0 was protecting against has ALREADY RUN SUCCESSFULLY (`instruments-service@654d694f` folded
      `underlying`+`chain` into the dedup key; a real prod apply completed with 28 `TOLERATED` chain-lossy groups and 0
      CAPTURED rows lost, canonical-fraction 99.24%) — so the live danger this todo exists to prevent did not recur.
      This todo just confirms the underlying code-hygiene gap (dry-run unconditionally reporting `(0, 0)` for this
      invariant) is actually closed for FUTURE runs, not still latent. If `"chain"` is still absent from `_DRYRUN_COLS`,
      add it (small perf cost) or add an explicit log line noting the check is structurally skipped in dry-run mode.
      Repo: instruments-service. **Done when**: either a grep confirms `"chain"` is already in `_DRYRUN_COLS` (record
      the confirming commit/line), or the fix is landed with a regression test proving a synthetic dry-run now surfaces
      a nonzero chain-lossy count when the full schema has one; `quality-gates.sh` green either way. Source:
      `cefi_consolidated_closeout_2026_07_18.md` (new tracked P0 todo, 2026-07-24 ~13:35Z DELTA).

## Deferred — human-only remainder from the 32-todo native triage

### Stays human — live migration critical path (judgment/coordination/operator-gated)

- **Track 1 cutover** (`[PM] P0.` execute the minutes-gap hybrid) — the central 4-script canonical-ID migration's
  drain+apply; still gated on multiple other still-open P0 items below, needs human-coordinated timing.
- **DERIBIT quote fix** (`[BACKEND] P0.`) — the code fix alone is inconsistent without its paired "coordinated ~38-min
  prod op" `prod/catalog.parquet` rebuild; both together GATE the Track-1 cutover — kept as one human-coordinated unit
  rather than split, unlike the `:PERP:` item above (whose writer-side half genuinely stands alone with "no data
  motion").
- **Track-2 backfill resume** (`[DATA] P1.`) — explicitly sequenced "AFTER the Track-1 Phase-D re-enable," itself
  human-gated; not safely dispatchable until that lands.
- **MID-BACKFILL / POST-BACKFILL checkpoints** (4 of the 6 checkpoint todos, both skills) — timing-coupled to when the
  still-unlaunched Track-2 backfill actually runs; a worker dispatched today has no way to know "midway" or "after,"
  unlike the 2 PRE-BACKFILL baselines drafted above which are meaningful regardless of timing.
- **POST-CUTOVER smoke-check + downloader flip** (`[BACKEND] P0.`) — explicitly "MUST land with (or immediately after)
  the cutover `--apply`"; landing early would break the smoke-check against the still-mostly-non-canonical current data.
- **Enumeration-audit terminal checkpoint** (`[DATA] P1.`) — explicitly gated on "the Track-1 cutover drain-gate lifts";
  premature now.
- **`[OPERATOR]` Decide whether to remove the UAC per-venue seed fallback** — already correctly tagged, feeds off the
  audit todo drafted above.
- **`[OPERATOR]` Delete the 149 Track-7 stale legacy objects** — already correctly tagged + delete-safety-cited in the
  parent doc; out of scope here by design (the drafted Track-7 todo above explicitly excludes it).
- **`cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` scope** (`[BACKEND] P1.`) — the parent doc's own text
  says "SCOPE UNCLEAR... confirm which phases are the pre-migration ask" — a judgment call needing operator
  clarification before any bounded todo can be written against it.
- **`adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md` cadence** (`[VERIFY] P2.`) — mixes a
  bounded spot-check with "decide the reconciliation cadence," an open policy decision with no stated target.
- **`[PM] P1.` Consolidate + archive** `cefi_layer1_denominator_gaps_2026_07_03.md` + others — its own text says "pull
  forked-elsewhere todos into THIS plan" (edits the parent doc itself) and "any other otherwise-complete cefi plans"
  (open-ended scope, no defined list) — both disqualify it from a bounded AO todo as written.

### Stays human — 3 items explicitly FENCED to another named agent/live process, all found STALE on inspection

The parent doc's own text warns these "predate later child-log entries that may have since resolved them... verify
current status against the child's DELTA history before assuming still-open." Verified against
`cefi_4surface_migration_execution_log_2026_07_24.md` this session — **all 3 are confirmed stale**, not fresh work:

- `[SCRIPT] P0.` Script 2 `_PATH_RE` embedded-slash tolerance (KRAKEN-SPOT 25,131) — **RESOLVED**: the parent doc's own
  Deferred-work table item 1 confirms KRAKEN-SPOT's rename ran to completion 2026-07-23 with the retry-hardened fix
  ("KRAKEN-SPOT Surface A is genuinely, fully clean").
- `[DATA] P0.` De-duplicate the 658 ambiguous catalogue wire keys — **RESOLVED**: the child execution log shows this
  number was re-measured (658→1,018, DERIBIT-driven) and re-scoped as its own live todo on 2026-07-22, which the parent
  doc's own Deferred-work table item 4 then confirms SHIPPED (213/216 fixed 2026-07-23, 3 permanently unresolvable by
  design — a genuinely closed terminal state, not a gap).
- `[DATA] P0.` Enumerate the ≈5,413 healthy-venue catalogue-gap residue — **PARTIALLY RESOLVED**: the "enumerate" ask is
  done (parent Deferred item 5, script shipped + 211 gap rows measured); the two genuinely-still-open pieces are
  BITGET-FUTURES (drafted above, code-free rollup re-run) and OKX-SPOT/COINBASE-SPOT (stays human — needs an operator
  decision on widening `_CEFI_VENUE_QUOTE_EXTENSIONS`, no defined target yet).

Also stale on the same evidence basis (found during this triage, not originally in the "FENCED" trio):

- `[DATA] P2.` "Design the COMBO-in-perp-partition move for DERIBIT" — a terse, undefined-target design ask; the actual
  design already exists (`plans/active/issues/deribit_combo_perpetual_partition_move_2026_07_21.md` §7, cited by the
  parent doc's own Track-7-adjacent item and Deferred-work item 7) — this checkbox is stale, not open design work.
- `[DATA] P1.` DERIBIT combo mispartition, part (a) (the writer-side guard-widen) — **RESOLVED**: parent Deferred-work
  item 7 confirms `mtds@2ddc6d4a` already shipped this; part (b) (the 15,119-row partition-move) stays human by its own
  explicit text (needs a fresh, specific operator go-ahead, not yet given).
- `[DATA] P2.` "Register PACIFICA-SOLANA (265) in the fail-hard quarantine set" — kept human, not drafted: no defined
  target mechanism cited (ambiguous whether this means the already-shipped launcher-registry cull
  `deployment-service@9b13679`, a different manifest-side quarantine, or something else) — needs human disambiguation,
  not a fresh independent AO guess at which registry.

## Reconciliation

Once a todo here ships, flip the corresponding checkbox in `cefi_consolidated_closeout_2026_07_18.md` itself, citing
this plan's commit as evidence. Gated via a companion `cefi_consolidated_native_ao_extract_2026_07_25_finalize.md`
(`depends_on: [cefi_consolidated_native_ao_extract_2026_07_25]` — `gate_on_depends: true`), which ALSO reconciles the 5
stale-checkbox findings above (flip-with-citation, since those require editing the parent doc — deliberately deferred to
the finalize plan rather than done here, since the parent doc's own edit surface should be touched once, coherently, not
piecemeal across two docs in the same session).

## Codex SSOTs

No new durable contract is created by this plan — every todo either executes an already-decided spec from the parent
doc, or is a bounded audit/measurement feeding a still-open human decision recorded there.
