# Resume prompt — Slot 2 / DeFi lane / C0 coding-closure → DRY RUN (handoff 2026-06-02, supersedes `slot_2_defi_c0_apply_handoff.md`)

You are **slot 2** (DeFi lane) in `.tabs/2`, branch `tab/ikennaigboaka/2` tracking `origin/live-defi-rollout` (LDR).
Operator: Ikenna. **Read this whole file + the SSOTs it names + `SUB_AGENT_MANDATORY_RULES.md` before doing anything.**
Boot:
`cd .tabs/2 && for r in unified-trading-pm market-tick-data-service unified-api-contracts unified-trading-library deployment-service instruments-service features-service market-data-processing-service; do git -C $r fetch origin live-defi-rollout -q && git -C $r pull --ff-only origin live-defi-rollout 2>/dev/null; done`

## Mission

Take the DeFi C0 lane **all the way through the apply-path DRY RUN with NO coding task left unturned** — every code item
needed BEFORE the dry run AND every code item needed AFTER it (so when backfills/apply/delete resume there is zero code
debt). Plan-of-record: `plans/active/defi_manifest_canonicalisation_2026_06_01.md` (§A items A1–A12 + §C0-RD). Naming
SSOT: `codex/02-data/defi-canonical-naming-ssot.md`.

## READ FIRST (do not act from memory)

- `plans/active/defi_manifest_canonicalisation_2026_06_01.md` — §A (A1–A12) + §C0-RD (C0-RD3c shipped, RD4/RD5/RD6
  open) + §MASTER cross-plan order.
- `codex/02-data/defi-canonical-naming-ssot.md` — operator-locked canonical forms (dex_pool_state/dex_pool_swaps,
  pipeline_mode=, HYPERLIQUID, DeFi perpetual).
- `codex/06-coding-standards/quality-gates.md` § "QG-sweep batching + shared-host concurrency" — **HOW to gate
  efficiently without breaking other slots (read this — it governs your QG cadence).**
- `codex/05-infrastructure/gcs-object-operations.md` + `codex/05-infrastructure/vm-tarball-deployment.md` — migration
  perf + tarball + post-launch verification.
- The migration tool: `market-tick-data-service/market_tick_data_service/scripts/migrate_defi_full_v9_canonical.py` (DRY
  by default; `--apply` writes).

## DONE + ON LDR (do NOT redo) — slot-2 2026-06-02 session

Honest-absence + canonical-bucket + attribution code, all QG-green + plan-flipped:

- **A8/A8b** `IS@17309f05`+`IS@359f245c` — IS subgraph + REST + uniswap_v3-cascade adapters RAISE on transient fetch
  failure (200-with-errors/missing-data/missing-key) instead of silent empty → caller records `attempted_failed`. Shared
  helpers `assert_subgraph_payload` + `extract_rest_list_or_raise` in `instruments-service/.../defi_utils.py`.
- **A9** `mtds@45dced01` — MTDS `dex_swaps_handler` balancer branch raises like the cascade.
- **A10a** `uac@10e69f08` — UAC `was_instrument_alive(available_from, available_to, day)` lifecycle primitive
  (facade-exported).
- **A10b** `utl@44d762d9` + `uac@daf1888c` — UTL `ManifestWriter.record_zero_rows(*, row_key, reason, was_expected, …)`
  routing helper (was_expected→`record_failed(EmptyFromLiveInstrumentError)` else `record_empty`) + facade-export
  `EmptyFromLiveInstrumentError`.
- **A11a** `mtds@7ebfa749` — MTDS `data_manifest_handler` resolves buckets via `resolve_bucket_name()` (env-tiered
  `-prd`) not hardcoded f-strings.
- **A11b + state.py 5.90** `deployment-service@2e91ab2` — deployment-service data-status
  (`manifest_reader`/`catalog`/`data_status_checkers`) routes through `resolve_bucket_name()`; `state.py /data-status`
  now attaches canonical honest-coverage via `compute_coverage_for_bucket`/`compute_honest_coverage` (STEP 5.90
  fixed). + `cloud-providers.yaml` gained 6 DeFi `kind`s
  (lending-indices/lst-rates/oracle-prices/perp-funding/gas-fees/liquidations, gcp+aws).
- **Attribution / C0-RD3c** `mtds@90aac6e1` — migration tool: oracle `contract→chain` (inverts
  `oracle_prices_handler._CHAINLINK_FEEDS_BY_CHAIN`+`_PYTH_FEEDS`) fills blank-chain oracle rows; + dry-run DIAGNOSTIC
  that logs distinct unattributable `(contract,feed)`/`(token,protocol)` identifiers. `_needs_attribution` stays
  HELD-never-guessed.
- **Docs**: 28k-uniswap_v3 issue archived→§D2; A7 corrected; defi-canonical-naming-ssot status table de-staled; A11/A12
  captured; QG-sweep technique codified (CLAUDE.md + codex/06).

## YOUR remaining work — NO coding left unturned (in order)

### Phase 1 — pre-dry-run CODE (finish before the VM dry run)

1. **A11c** [unified-api-contracts] — VERIFY `registry/market_data_categories.py` DeFi data_type list
   (`dex_pools`/`dex_swaps`): is it a logical MENU (intentional) or a physical-key source consumed by data-status? If
   physical/consumed → align to canonical `dex_pool_state`/`dex_pool_swaps` + reconcile
   `registry/data_type_capability.py` L336-345 "aspirational/deferred" note. Verify-first (read consumers) before
   editing.
2. **Unblock `mtds_mdps_master`** — read `plans/epics/mtds_mdps_master.md`; identify what gates it (likely Phase -1
   workspace-QG-green + the canonical-form items above). Close/record the gating items now that A8–A11+attribution
   shipped.
3. **A10d** [market-tick-data-service] — migrate DeFi handler `record_empty(SOURCE_RETURNED_ZERO)` callsites to
   `record_zero_rows(was_expected=…)` using the per-AG oracle (`was_instrument_alive` + venue-launch A1/A2). NOTE
   shard-granularity; for DeFi the venue-launch gate covers most.
4. **A10c** [per-service quality-gates] — add a QG STEP (5.70 family) failing any `record_empty(…SOURCE_RETURNED_ZERO…)`
   NOT routed through `record_zero_rows` (baselined ratchet + `# QG-allow:` waiver). Makes the backstop un-bypassable.
5. **A11d/A11e/A11f** [mtds + deployment-ui] — A11d OPERATIONS metadata reconcile; A11e remaining legacy-form test
   maskers (deployment-ui `DataStatusTab.phase8h.test.ts`); A11f residual `category=`→`asset_group=` writers
   (`market_interface/__init__.py` + live recorder alias).
6. **C0-RD6** [unified-api-contracts + market-data-processing-service] — fold the 2 dup-alias columns out of the
   `dex_swaps` superset union BEFORE apply (31→29) + drop from UAC `DEX_SWAPS_SCHEMA` + stop emitting in
   `swap_adapter.py`.

### Phase 2 — DRY RUN (VM op)

7. **Rebuild the tarball** at current HEADs (incl `mtds@90aac6e1` attribution):
   `bash deployment-service/scripts/vm/create-code-tarballs.sh --allow-dirty-tarball` from `.tabs/2`; note the new
   `mtds-code@<sha>` / `unified-api-contracts-code@<sha>` / `unified-trading-library-code@<sha>` pins + `gsutil ls`
   verify each.
8. **Busy-week re-dry** (NOT an arbitrary week — pick a HIGH-VOLUME week so the per-week throughput extrapolates to a
   real full-period ETA): `export UAC_TARBALL_SHA=<new> UTL_TARBALL_SHA=<new> MTDS_TARBALL_SHA=<new>` then
   `bash deployment-service/scripts/vm/launch-canonical-migration-vm.sh defi <busy-start> <busy-end> dry`. Confirm 0
   errors, data_type=`dex_pool_state`/`dex_pool_swaps`, `pipeline_mode=batch/` paths.
9. **Read the needs_attribution DIAGNOSTIC** from the dry log (the new "distinct unattributable identifiers" lines). For
   oracle: confirm contract→chain resolved them (residual≈0). For lst: take the enumerated `(token,protocol)` →
   **A10/attribution lst-close** [unified-api-contracts]: add the real tokens to `LST_VENUE_TO_TOKENS`
   (`registry/capability_declarations/_defi_lst.py`) — NEVER guess; only add tokens the diagnostic actually surfaced
   (align to UAC/IS).
10. **Re-dry** (full range) → `needs_attr ≈ 0` (or operator-acked residual). This is the C0-RD4 precondition.

### Phase 3 — post-dry-run code/lane (so nothing is unturned after)

11. **A12** — upstream-data PREFLIGHT checks per consuming service (mtds/mdps/features/strategy/execution):
    canonical-SSOT reads + 0-vol/NaN→honest-absence (`record_zero_rows`) + manifest incomplete-expected marking +
    **live=batch check symmetry / divergent actions** (live=alert+circuit-breaker+halt; batch=fill-what-you-can).
    Audit-first; file per-service sub-items.
12. **§B0** run the `expected_unattempted` chain for DeFi (gated C-GREEN); **§A2a/A2b/A4/A5** writer fixes; **§D**
    features backfill; **§E** cefi-perp hedge; **§F** docs; **§G** Solana basis MVP.

> **NON-CODING ops after the coding closure (operator-gated, not part of "no code unturned" but the end-state)**: C0-RD4
> completeness+CF gate per bucket → **deploy the features/MDPS reader fixes to LIVE before any delete** → C0-RD5 legacy
> delete (owned by `bucket_name_ssot…` Phase 7, gated C-GREEN + pre-migration drain). See §MASTER.

## Hard-won gotchas (HONOUR THESE)

- **QG cadence — batch the GATE not the commits** (`codex/06-coding-standards/quality-gates.md`): edit the whole batch,
  run `quality-gates.sh` ONCE per repo, then per-shippable-unit commits+flips from the green tree. **Run ≤1–2 full QGs
  at once (host is SHARED across slots).** **NEVER bulk-kill pytest/QG/basedpyright procs** (may be another slot's).
  When only the `<300s`/inner-timeout meta-gate trips → `IGNORE_TIMEOUT=true` / `PYRIGHT_TIMEOUT=<n>` (sanctioned).
- **Promotion under shared-worktree races**: LDR is HOT + other sessions/orphan-wip workers rewrite refs/reformat files.
  Promote via a throwaway worktree off `origin/live-defi-rollout` (cherry-pick; on a linter-reformat conflict that's
  YOUR own inherited WIP, `git checkout <yourcommit> -- <file>` to take your superset version after VERIFYING the
  deletions are your own lines, not foreign). Verify against `origin/live-defi-rollout`, never `FETCH_HEAD`.
- **Foreign dirty files — do NOT stage**: deployment-service
  `docs/GCS_AND_SCHEMA.md`/`docs/HARDENING.md`/`RUNTIME_TOPOLOGY_DECISIONS.md`/`uv.lock`; mtds
  `backfill_drift_v2_historical.py`/`backfill_solana_dex_state.py`/`uv.lock`; uac/IS `uv.lock` + any test/json you
  didn't author. Stage by name, never `git add .`.
- **Naming operator-LOCKED**: `dex_pool_state`/`dex_pool_swaps` (EVM+Solana union), `pipeline_mode=` in path,
  `HYPERLIQUID`, DeFi `perpetual`. Do NOT re-split.
- **needs_attribution is HELD, never guessed** — close lst tokens ONLY from the dry diagnostic's real identifiers via
  the IS/UAC registry.
- **local gcsfs DNS flaky** — heavy GCS (dry/apply) runs on the in-region VM; `gcloud`/`gsutil` work locally.
- **Cross-plan**: `bucket_name_ssot` DeFi raw seed marked DO-NOT-RUN (unsafe) → C0 not blocked by it; its DELETE
  (Phase 7) AFTER your RD4-GREEN. solana_defi Gate-2 ⊥ C0 on the DeFi `_index`.
- **Rebuild tarball after ANY mtds/uac/utl commit** + verify the `@sha` pin before launch.

---

## Slot-2 session scoreboard 2026-06-02 (Half-3 deferred-work handoff) — plan: `plans/active/defi_manifest_canonicalisation_2026_06_01.md`

**SHIPPED + QG-green + flipped (LDR):** A11c expanded from "2 files" into a confirmed cross-repo data-correctness gap
and (operator-approved) the FULL canonical denominator collapse landed:

- `uac@a967121a` — `dex_pool_state`/`dex_pool_swaps` across all UAC coverage/capability DENOMINATOR registries
  (market_data_categories, expected_coverage.\_DEFI, defi_venue_capabilities, capability_declarations/\_defi,
  source_priority, availability_semantics, required_inputs, defi_prediction_instrument_seeds, venue_constants/mapping) +
  6 tests + data_type_capability note. Fixes `expected_coverage()` returning NOT_IN_SCOPE for migrated pool/swap cells
  (the reader/denominator-first gate before C0 apply).
- `mdps@56503c2` — swap candle adapter re-registered under canonical `dex_pool_swaps` (orchestrator selects by exact
  data_type) + adapter-registry tests.
- `deployment-api@14dfe2e` — data-status maps canonical (TESTS green; repo QG blocked ONLY by PRE-EXISTING acknowledged
  schema-provenance debt across many local DTOs — unrelated, flagged below).
- `mtds@b986a3e1` — 5 DeFi DEX adapters' SUPPORTED_DATA_TYPES/\_default_data_types/branch-dispatch + orchestrator
  `_TICK_REQUIRED_COLUMNS` + live `curve_defi_ws` connector + canonicalization test, all canonical (MTDS QG green).
- `mtds@20e5bd2d` — moved a pre-existing `# noqa: qg-deep-import` to the from-line in `polymarket_adapter.py` (unblocked
  mtds QG; unrelated to A11c).
- PM `venue_data_types.yaml` (PM+mtds copies) canonical.

**DECOUPLED + tracked (before-apply follow-ups, both have findings in the plan):**

- **C0-RD6** — the candle-output `_DEX_EXT` is SHARED by `swaps_ohlcv` AND `state_ohlcv`, so the dup-alias-column drop
  needs a schema SPLIT (not a flat drop). Provisional adapter drop was reverted. Owed: split `_DEX_EXT` +
  migration-union exclusion.
- **A11c-candle-enum** — UAC `candle_schema.DataType` has a DISTINCT Phase-2 `DEX_POOL_STATE="dex_pool_state"` that
  COLLIDES with the operator-locked canonical pool name; the candle_schema enum + schema-contract registry
  (contracts.py/\_defi_v2_contracts.py) were LEFT legacy to avoid a StrEnum alias collision. **Needs operator decision:
  merge snapshot↔timeseries, or distinct token.**

**Cross-repo pre-existing QG-red flagged (Harsh-side workspace-QG-green, NOT mine):** deployment-api schema-provenance
debt (local response DTOs in deploy_missing.py/shard_detail.py/recursive_borrow.py etc.; "acknowledged" since 2b4fed7).

**NOT STARTED (all tracked `- [ ]` in the plan):** A10d, A10c, A11d, A11e, A11f, mtds_mdps_master unblock (Phase 1);
tarball rebuild + busy-week DRY RUN + needs_attribution diagnostic + lst-close + re-dry (Phase 2 — INDEPENDENT of A11c,
migration tool already canonical); A12 preflight audit + B0/A2/A4/A5/D/E/F/G (Phase 3). **The DRY RUN needs a clean slot
worktree for the tarball + active T+10min→STOPPED babysitting — best run in a fresh-context session (no
fire-and-forget).**
