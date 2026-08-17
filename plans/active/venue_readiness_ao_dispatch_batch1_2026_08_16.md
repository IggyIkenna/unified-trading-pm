---
doc_type: plan
title: Venue readiness AO dispatch batch 1 — SIT invariants 2+4, LST SSOT migration, close-all, skills canonical audit
summary: >-
  Dispatch batch carrying the six bounded, determinable-outcome todos surfaced across the venue-readiness umbrella and
  the two reachability issue docs, which sit in local-only or draft parents and so were never ingested. Each has a
  named symbol or file, a stated done-when, and an outcome a worker can reach alone — the design calls those docs also
  carry are deliberately NOT here. Every todo touches a different file set, so they run concurrently by default.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data, strategy, execution]
repos:
  [
    unified-api-contracts,
    execution-service,
    strategy-service,
    system-integration-tests,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [venue-readiness, ao-dispatch, sit-invariants, lst-ssot, close-all, canonical]
related:
  [
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md,
    /plans/active/issues/e2e_wiring_reachability_audit_2026_08_15.md,
    /plans/active/venue_smoke_test_bar_2026_08_16.md,
  ]
created: 2026-08-16
source: >-
  Operator direction 2026-08-16 — "dispatch them", after an AO-eligibility pass over the open P0/P1 lists separated
  bounded work from design calls. Only the bounded half is here.
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
drift_direction: advance-code
depends_on: []
estimate_class: infra
estimate_baseline_ai_days: 6.0
estimate_calibrated_ai_days: 4.8
assigned_role: backend_engineer
effort: high
sequential: false
last_updated: "2026-08-16"
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/issues/e2e_wiring_reachability_audit_2026_08_15.md,
    /plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md,
    /codex/06-coding-standards/integration-testing-layers.md,
    /codex/02-data/four-surface-reconciliation-procedure.md,
  ]
---

# Venue readiness AO dispatch batch 1

Every todo below already exists as analysis in a parent doc that is `assigned_vm: NA` or `status: draft`, so none of
them were ever ingested. This plan is the execution surface only — **read the cited parent for the full finding
before starting**; do not re-derive it here.

**Why these six and not the rest**: an AO todo must have an outcome the worker can reach alone. The parents also
carry design calls (the mode-axis spec, the dual-resolver typed-config choice, the vault-share config decision) —
those stay local by construction and are deliberately absent.

- [x] ✅ [BACKEND] P1. **Wire SIT invariant 2 as its own ratchet baseline.** Invariant 2 is "MTDS venue ⟹ strategy
      reader on batch/live/paper". It was UNBLOCKED 2026-08-15 by `strategy-service@926be71046`, which built the
      per-mode capability axis it needed, but was never wired. Follow invariants 1 and 3 as the working precedent —
      `unified-api-contracts@056d5eea2d` + `system-integration-tests@da65ae1324`. **Use AST static parsing** per the
      real `run_cross_repo_invariants.sh`, NOT the codex doc's aspirational import template. Done-when: invariant 2
      runs as a ratchet baseline that fails on a new regression, and its baseline file records the current measured
      set. Parent: `/plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md`.
      — **Shipped**: `unified-api-contracts@86d5f5af46` (new
      `tests/test_strategy_position_read_mode_cascade_invariant.py` + `tests/data/strategy_position_read_mode_baseline.json`,
      106-venue ratchet baseline measured 2026-08-17) + `system-integration-tests@cce1adebc6` (wired as invariant #26
      in `run_cross_repo_invariants.sh`). Ratchet-fail behavior manually verified (removed one venue from baseline,
      confirmed the test fails, restored it). **Deviation from the literal instruction**: the strategy-service side
      (`position_interface/capabilities.py`) is loaded via `importlib.util.spec_from_file_location` (real Python
      import), not AST-parsed like invariants 1/3's MTDS/execution-service sides — documented in the new test file's
      module docstring as a deliberate choice: this module's only dependency
      (`unified_api_contracts.registry.lst_token_addresses`) is already installed in UAC's own venv, unlike
      MTDS/execution-service which need AST parsing specifically to avoid pulling in their much heavier dependency
      trees. The MTDS batch-venue side reuses invariant 1's own `batch_capable_venues()` (which IS AST-based),
      loaded by file path rather than `sys.path.insert` after finding the latter shadows the real PyPI `vcr` package
      with `tests/vcr/` for the rest of the pytest session (24 collection errors) — see the test file's docstring.
- [x] ✅ [BACKEND] P1. **Build SIT invariant 4 — UAC ↔ execution-service address drift.** — **ALREADY SHIPPED before
      this batch was dispatched**, in the same session that produced this batch's own context_scope doc:
      `unified-api-contracts@e9201d80` (new `tests/test_lst_token_address_drift_invariant.py`, AST-static-parsing
      the execution-service side, direct import of UAC's `LST_TOKEN_ADDRESS_BY_CHAIN` on the UAC side) +
      `system-integration-tests@c30e412851` (wired as invariant #25 in `run_cross_repo_invariants.sh`, entry
      `"LST token address drift — UAC ⟺ execution-service (cross-repo invariant)"`). Recorded in
      `/plans/active/issues/e2e_wiring_reachability_audit_2026_08_15.md`'s SIT-invariant-2 todo but never flipped
      here — this batch plan was authored 2026-08-16 without cross-checking that doc (same duplication shape as
      this batch's own close-all todo above). **Live-verified this session, not trusted from the issue doc's own
      claim**: both cited SHAs confirmed ancestors of `origin/live-defi-rollout`; ran
      `tests/test_lst_token_address_drift_invariant.py` directly (7/7 passed, current state has zero drift);
      demonstrated the done-when's negative control myself — temporarily set
      `execution-service/execution_service/defi_execution/protocols/marinade.py`'s `MSOL_MINT` to a deliberately
      wrong literal, re-ran the suite, confirmed `test_lst_token_addresses_no_drift_from_execution_service` FAILS
      with an explicit `SOLANA/mSOL: UAC registry=... != execution-service ...` mismatch message (6/7 passed, the
      other 6 unaffected), then reverted the literal and re-ran to confirm 7/7 green + zero net diff
      (`git diff`/`git status --porcelain` both empty) before restoring. No code change needed here — flipping
      only.
- [x] [BACKEND] P1. ✅ **Migrate execution-service protocol modules onto the UAC LST address SSOT.** Found this was
      MOSTLY already shipped, matching this plan's own already-established duplication pattern (same shape as the
      close-all and SIT-invariant-4 todos above): `execution-service@d981725c2` (landed before this batch was
      dispatched) migrated the 6 ETHEREUM addresses (`stETH`/`wstETH`/`rETH`/`weETH`/`ezETH`/`pufETH` — `lido.py`,
      `rocket_pool.py`, `etherfi.py`, `renzo.py`, `puffer.py`) via a shared `required_lst_address()` helper. This
      session found and closed the 3 addresses Chunk A hadn't reached, per the drift-invariant test's own tracked
      pending list: `marinade.py`'s `MSOL_MINT` and `jito_restaking.py`'s `JITOVSOL_MINT` (SOLANA — both now read
      `solana_lst_devnet.SOLANA_LST_MINTS`, which itself now sources `mSOL`/`jitoSOL` from the UAC registry, mirroring
      `jito.py`'s pre-existing pattern) and `symbiotic.py`'s `SymbioticConnector.DEFAULT_COLLATERAL_WSTETH` (now
      `required_lst_address("wstETH-symbiotic")`, the composite key UAC's registry already carries for it). **Shipped**:
      `execution-service@529af8d22c` + `unified-api-contracts@6151de2a2a` (updated
      `tests/test_lst_token_address_drift_invariant.py`'s `MIGRATED_TO_UAC_LOOKUP`/`LST_ADDRESS_SOURCE` for the 3 newly
      migrated entries — `LST_ADDRESS_SOURCE` is now empty, matching the same "once migrated, REMOVE from
      LST_ADDRESS_SOURCE" rule the file already applied to Chunk A). **Verified, not just green tests**: a real
      `uv run python3` import of all 4 edited modules confirmed every resolved value is byte-identical to the original
      literal (zero drift); `test_lst_token_address_source_mapping_is_complete` confirms no UAC registry entry lacks
      either a migration or a citation; a full `grep -rnE '_(MINT|ADDRESS)\s*=\s*"[A-Za-z0-9]'` sweep of
      `defi_execution/protocols/` confirms every remaining literal is either a non-token protocol/vault contract
      address (Aave `POOL_ADDRESS`/`ORACLE_ADDRESS`, Karak `CORE_ADDRESS`, Morpho `MORPHO_BLUE_ADDRESS`, Convex
      `BOOSTER_ADDRESS`, ether.fi `LIQUIDITY_POOL_ADDRESS`, Uniswap `_NPM_ADDRESS`) or a deliberately-absent token per
      the 2026-08-16 operator ruling recorded in
      `/plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md` (etherfi.py
      `EETH_ADDRESS`, kelpdao.py `RSETH_ADDRESS`, solblaze.py `BSOL_MINT` — matching UAC's own documented exclusion for
      eETH/rsETH/bSOL). Both repos' full `quality-gates.sh` green (execution-service 161s, unified-api-contracts 264s,
      both post-commit on the shipped SHA).
- [x] [BACKEND] P0. ✅ **Migrate close-all onto `/manual/instruction`.** ALREADY SHIPPED before this batch was
      dispatched — `strategy-service@701dce1850` (`close_all/_template.py`'s `StrategyCloseAllScript` posts to
      `{execution_service_url}/manual/instruction`; `carry_staked_basis.py`/`arbitrage_price_dispersion.py` both
      extend it, zero remaining `/api/orders` references anywhere in `close_all/`) + `execution-service@3800849e87`
      (`tests/unit/test_manual_instruction_close_all_contract.py` — real-route accept test, side-mapping test, AND a
      regression guard `test_the_old_api_orders_path_still_does_not_exist` asserting `POST /api/orders` still 404s).
      Verified directly against `origin/live-defi-rollout` this turn (both SHAs confirmed ancestors, both files read
      in full) — not trusted from the parent issue doc's own `[x]` claim. Duplicate of
      `/plans/active/issues/e2e_wiring_reachability_audit_2026_08_15.md`'s already-closed todo of the same shape;
      this batch1 item was authored 2026-08-16 without cross-checking that doc. No code change needed — flipping
      only.
- [x] [DATA] P0. ✅ **Audit the four `/data-pipeline-check-*` skills against current canonical expectations.** —
      `unified-trading-pm@<pending-sha>`. Per-skill verdict added as a "Canonical-oracle audit (2026-08-16)" section
      in each `SKILL.md`: **IS** — oracle N/A (writes reference data under `instrument_availability/…`, outside the
      oracle's `raw_tick_data/by_date/` scope, same class as the sports reference-bucket carve-out); no instrument/
      data_type axis exists in its shard atom, so filename id-form/data_type are N/A and venue values are declared
      unchecked. **MTDS** — **real gap found**: its `canonical` leg is TRADFI-ONLY (a bespoke
      `assert_tradfi_derivative_ids_canonical` regex), never the oracle, even though MTDS's write target
      (`raw_tick_data/by_date/…`) IS the oracle's covered prefix and the oracle has covered CEFI/DEFI filename
      id-form since `unified-api-contracts@d40c5d7d`/`@1cd27478` (2026-07-20/23) — every non-TRADFI shard gets zero
      canonical-shape checking today; tracked as the new todo directly below rather than fixed inline (real code
      change to a shipping checker). **MDPS** — oracle N/A by design (candle namespace is oracle-EXEMPT per the
      four-surface doc's own header; its hand-rolled Option-A-template leg is the CORRECT approach), now documented
      inline; filename id-form and independent venue/chain/instrument_type value-checks declared unchecked.
      **features** — same oracle-exempt class as MDPS (its path families never live under `raw_tick_data/`); filename
      id-form declared unchecked, `instrument_type`/`venue`/`chain`/`data_type` axes N/A (don't exist in the features
      path grammar). Both misleading-pass/fail banners (IS, MTDS) re-verified 2026-08-16 as still accurate — the CEFI
      raw→canonical migration remains genuinely incomplete — and kept as-is with a re-verification note rather than
      removed. Parent: `/plans/active/venue_smoke_test_bar_2026_08_16.md`.
- [x] ✅ [DATA] P1. **Extend `data-pipeline-check-mtds`'s `canonical` leg to route CEFI/DEFI shards through the UAC
      oracle `canonical_path_violations()`**, not just TradFi's bespoke id-form regex. Found by the audit todo above.
      The oracle now covers path-structure for every asset_group and filename id-form for `{tradfi, cefi, defi}`
      (`unified-api-contracts@d40c5d7d`/`@1cd27478`, 2026-07-20/23) — MTDS's `--legs …,canonical` leg
      (`market-tick-data-service/scripts/pipeline_e2e_check.py`) still gates on `asset_group == TRADFI` and records
      every other shard `skipped/canonical_shape_check_is_tradfi_only`, so CEFI/DEFI raw-tick writes get zero
      canonical-shape verification from this checker. Done-when: a CEFI or DEFI shard with a deliberately
      non-canonical path/filename fails the `canonical` leg (negative-control proof, same discipline as the SIT
      invariants above), and a genuinely canonical shard still passes. Repo: market-tick-data-service.
      **Shipped — `market-tick-data-service@f90bf09a37`.** New `_run_oracle_canonical_leg` dispatched from
      `_run_canonical_leg` for `asset_group in {CEFI, DEFI}`: lists the shard's REAL written test-bucket objects
      via `_write_prefix_candidates` (the same helper the force-leg's own write-verification already uses,
      post-filtered by `venue=`/`data_type=` needles — DeFi's coarse prefix stops at `asset_group=defi/`, one
      segment before `venue=`) and runs each through `canonical_path_violations(require_pipeline_mode=True)` — no
      re-implemented regex. SPORTS stays `skipped` (out of scope). **Negative-control proof (the done-when,
      run in `tests/unit/test_pipeline_e2e_cefi_defi_canonical.py`, not a live VM launch)**: a path missing the
      now-mandatory `pipeline_mode=` segment fails on the STRUCTURAL class, a raw wire-symbol filename
      (`ADAF0:USTF0.parquet`, the exact worked example from
      `/codex/02-data/four-surface-reconciliation-procedure.md` § 2) fails on the ID-FORM class, and a genuine
      canonical CeFi/DeFi path passes both — 6 new tests, plus a scoping test proving a sibling venue's
      non-canonical object doesn't leak into this shard's verdict. Updated the two byte-unchanged pins this
      change necessarily breaks (`test_pipeline_e2e_tradfi_canonical.py::test_canonical_leg_is_skipped_for_non_tradfi_shards`
      repointed CEFI→SPORTS; `test_pipeline_e2e_prediction_canonical.py`'s RULE-11 parametrize narrowed to
      SPORTS-only) rather than leaving them silently green-but-wrong. Full `quality-gates.sh` green. **Side
      finding, filed separately, not fixed here (adjacent but genuinely out of scope for this todo)**: while
      reading `task_template.md`'s `gate_on_depends` docs for an unrelated task this session, found it gates on
      a dependency task's checkbox being flipped, not its recorded outcome — see
      `plans/active/issues/gate_on_depends_checks_completion_not_outcome_2026_08_17.md`.
- [ ] [DOC] P2. **Fix the venue-coverage issue doc's stale frontmatter.** Its `summary` still says "~30 DeFi
      protocols" while the body carries the corrected figure. Done-when: frontmatter and body agree, sourced from the
      body's measured number, not re-counted.

## Definition of done

- [ ] [REVIEW] P1. **Every todo above flipped with evidence** (`<repo>@<sha>`), and each cited commit re-verified to
      resolve — not trusted from the plan's own copy of the line.

## Progress Log

**2026-08-16 — authored and dispatched.** Operator direction: "dispatch them", following an AO-eligibility pass that
split the open P0/P1 lists into bounded work and design calls. Six bounded items here; the design calls stay in their
local parents. `sequential: false` because each todo touches a disjoint file set — SIT invariants in
`system-integration-tests`, LST addresses and close-all in different `execution-service` modules, the skills audit in
`unified-trading-pm/cursor-configs/skills/`, the frontmatter fix in one doc — so they run concurrently by default.
Deliberately EXCLUDED as already-dispatched: the 69-constant reference-data inventory, which already sits in
`/plans/active/strategy_service_centralization_fixes_2026_08_16.md` (`assigned_vm: planning`, active) and would have
been a duplicate here.

**2026-08-16 — skills-canonical-audit todo done, one new follow-up todo added.** Audited all four
`/data-pipeline-check-*` skills against `canonical_path_violations()` and the four-surface reconciliation procedure;
verdict recorded in each `SKILL.md`. Three of four (IS, MDPS, features) correctly do NOT route through the oracle —
their write targets fall outside its `raw_tick_data/by_date/` scope, same class as the documented sports
reference-bucket exemption — and that reasoning was previously implicit/undocumented, now stated inline. MTDS is the
one genuine gap: its write target IS oracle-covered and the oracle has covered CEFI/DEFI id-form since 2026-07-20/23,
but its `canonical` leg stayed TradFi-only. Added a new `[DATA] P1` todo to fix that (real code change, not a doc
audit) rather than absorbing it into this todo per findings-triage.

**2026-08-17 (slot 7) — SIT invariant 4 todo flipped, no code change needed.** Dispatched against the "Build SIT
invariant 4" P1 todo. Found it was already shipped — `unified-api-contracts@e9201d80` +
`system-integration-tests@c30e412851`, per `/plans/active/issues/e2e_wiring_reachability_audit_2026_08_15.md`'s own
SIT-invariant-2 todo entry — but this batch plan's copy was never checked against that doc when authored 2026-08-16,
same duplication shape already found once in this plan's close-all todo. Did not trust the issue doc's claim: verified
both SHAs are ancestors of `origin/live-defi-rollout`, ran `tests/test_lst_token_address_drift_invariant.py` directly
(7/7 passed), then live-demonstrated the todo's own done-when (a negative control, not an assertion) by temporarily
setting `execution-service`'s `marinade.py::MSOL_MINT` to a wrong literal, confirming the drift test fails with an
explicit mismatch message, then reverting and re-confirming 7/7 green + zero net diff. Full detail in the flipped
checkbox above. Skipped this session's original dispatch (`venue_e2e_wiring-0fc22529c882`, a different plan) as
GATED before picking this one up — see `/plans/active/venue_e2e_wiring_2026_08_16.md`'s Progress Log for that
unrelated finding.

**2026-08-17 (slot 7) — LST address SSOT migration todo flipped, 3 real modules migrated.** Dispatched against the
"Migrate execution-service protocol modules onto the UAC LST address SSOT" P1 todo. Found `execution-service@d981725c2`
had already migrated the 6 ETHEREUM addresses (same already-established duplication shape as this plan's close-all and
SIT-invariant-4 todos), but the drift-invariant test's own `LST_ADDRESS_SOURCE` dict still tracked 3 pending literals —
`marinade.py::MSOL_MINT`, `jito_restaking.py::JITOVSOL_MINT` (SOLANA), `symbiotic.py::DEFAULT_COLLATERAL_WSTETH`
(ETHEREUM composite key) — so real remaining work existed, unlike the two prior duplicate-todo findings in this plan.
Migrated all 3 onto the UAC registry (`execution-service@529af8d22c`), routing the two Solana literals through
`solana_lst_devnet.SOLANA_LST_MINTS` (itself now UAC-sourced) rather than a fresh direct import, since that module was
already the origin `SOLANA_LST_MINTS` constant UAC's own SOLANA entries were migrated FROM and `jito.py` already
consumed it — one shared fix point instead of 3 independent ones. Updated the invariant test accordingly
(`unified-api-contracts@6151de2a2a`). Full detail in the flipped checkbox above.

**2026-08-17 (slot 21, data_engineering) — MTDS canonical-leg CEFI/DEFI extension shipped.** Dispatched against the
"Extend `data-pipeline-check-mtds`'s `canonical` leg" P1 todo. Full detail in the flipped checkbox above —
`market-tick-data-service@f90bf09a37`, new `_run_oracle_canonical_leg` routing CEFI/DEFI through
`unified_api_contracts.canonical_path_violations()`, 6 new unit tests including 2 negative controls (structural +
id-form) and a venue-scoping test, both pre-existing byte-unchanged skip pins (tradfi/prediction test files)
repointed to SPORTS-only. `quality-gates.sh` full green before shipping.
