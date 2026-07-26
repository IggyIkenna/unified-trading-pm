---
doc_type: issue
title:
  Two small residual findings from defi_satellite_ao_dispatch_batch2-018 (spot_venue axis + capability-manifest UI sync)
summary: >-
  While closing defi_satellite_ao_dispatch_batch2-018 (unified-api-contracts@13266bf8, strategy-service@1bf99b8e), found
  two small, real gaps that were mentioned in the plan-flip prose but never converted into tracked todos: (1)
  CARRY_STAKED_BASIS_DATED's spot_venue is still hardcoded (the base CARRY_STAKED_BASIS archetype's spot_venue axis is
  fully shipped; the DATED variant was out of that todo's scope but never separately tracked); (2) UAC's regenerated
  openapi/ capability manifests have no established sync path into unified-trading-system-ui's lib/registry/ copies
  (unlike coverage.ts, which has sync-archetype-capability-to-ui.sh) -- so a raydium-for-CARRY_BASIS_PERP-style fix
  landing in UAC does not automatically reach the wizard UI.
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [strategy-service, unified-api-contracts, unified-trading-system-ui]
scope: [engineer]
tags: [defi, wizard, capability-manifest, sync, staked-basis, residual]
related:
  [
    /plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md,
    /plans/active/issues/e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md,
    /plans/active/issues/ci_registry_drift_uac_utl_stale_tag_version_conflict_2026_07_26.md,
  ]
created: 2026-07-26
parent_epic: defi_master
priority: P3
estimate_class: refactor
assigned_vm: planning
resolved_by:
  All 5 recommended-decision items actioned 2026-07-26 (slots 2 + 6). The two CI-automation todos (items 4-5) are
  DESIGNED + locally byte-identical-verified but blocked on real-CI verification by a separate, pre-existing, unrelated
  CI defect — split out to its own issue doc (ci_registry_drift_uac_utl_stale_tag_version_conflict_2026_07_26.md) with
  its own open follow-up todos, so this doc closes at the scope it committed to.
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
source:
  [
    strategy-service/strategy_service/engine/strategies/v2/target_universe/catalog_staked_basis.py,
    unified-trading-pm/scripts/openapi/generate_capability_manifest.py,
    unified-trading-pm/scripts/propagation/sync-archetype-capability-to-ui.sh,
  ]
---

> **🟢 RESOLVED 2026-07-26 — ACKED-INTO-CODE** — all 5 recommended-decision items actioned (slots 2 + 6):
> `strategy-service@4d1bbb18`, `unified-trading-system-ui@bd527d83`/`@3715d3ec`, `unified-api-contracts@449d1b3d`; the
> two CI-automation todos are designed + locally byte-identical-verified but blocked on real-CI verification by a
> separate, pre-existing, unrelated CI defect, split out to
> `ci_registry_drift_uac_utl_stale_tag_version_conflict_2026_07_26.md`. Archived per the terminal-status backlog sweep.

## What I found

**Finding 1 — `CARRY_STAKED_BASIS_DATED` spot_venue still hardcoded.** The base `CARRY_STAKED_BASIS` archetype's
spot_venue axis (`catalog_staked_basis.py`'s `_STAKED_BASIS_ETH_SPOT_VENUES` / `_STAKED_BASIS_SOL_SPOT_VENUES`) is
already fully shipped per the 2026-06-17 operator directive — orca/raydium/jupiter/binance are all selectable, and a
regression test (`test_carry_staked_basis_spot_venue_axis.py`) covers it. `build_carry_staked_basis_dated()` (same file,
~line 386-451) is a separate function for the `_DATED` variant and still hardcodes `"spot_venue": "BINANCE-SPOT"` (line
~439) with no equivalent axis. This was out of scope for `defi_satellite_ao_dispatch_batch2-018`'s done-when (which only
named "staked-basis", not "staked-basis-dated"), so it was never fixed — but it was also never filed as a tracked todo,
so it would be forgotten.

**Finding 2 — UAC's regenerated capability manifests have no established UI sync path.** While closing item (1) of
batch2-018 (the CARRY_BASIS_PERP Solana-DEX spot-leg gap),
`unified-api-contracts/openapi/capability-verdict-matrix.json`

- `capability-manifest.json` were found stale (still listing removed `drift`/`gmx_v2` venues, missing
  `raydium`/`aster`/`kalshi_perp`/`polymarket_perp`) and were regenerated (`unified-api-contracts@13266bf8`). Looking
  for a corresponding UI-side sync mechanism:
  `unified-trading-pm/scripts/propagation/sync-archetype-capability-to-ui.sh` syncs a DIFFERENT source file
  (`unified_api_contracts/internal/architecture_v2/archetype_capability_manifest.json`) into
  `unified-trading-system-ui/lib/architecture-v2/coverage.ts` — but there is no equivalent sync script for
  `openapi/capability-manifest.json` / `capability-verdict-matrix.json` into
  `unified-trading-system-ui/lib/registry/capability-manifest.json` (confirmed via
  `grep -rln "lib/registry" unified-trading-pm/scripts/openapi/` — zero hits). So a fix landing in UAC's `openapi/`
  manifests (like the raydium addition) does not automatically propagate to whatever the wizard UI actually renders from
  its own `lib/registry/capability-manifest.json` copy — that file's provenance/update mechanism is unclear and wasn't
  investigated further (out of scope for a data_engineering-scoped todo; UI work is a different craft).

## Why it matters

Neither is urgent (both P3), but both are exactly the kind of small, easily-forgotten gap that resurfaces as a "why
doesn't the wizard show X" confusion later if left as prose instead of a tracked todo.

## Recommended decision

- [x] ✅ [REGISTRY] P3. **DONE 2026-07-26 (slot 6), `strategy-service@4d1bbb18`.** Made `spot_venue` a selectable axis
      for `CARRY_STAKED_BASIS_DATED`, mirroring the base archetype's `_STAKED_BASIS_ETH_SPOT_VENUES` pattern (ETH-only —
      no SOL equivalent exists for either archetype post-DRIFT-cull): `build_carry_staked_basis_dated()` now loops
      `(dated_expiry_tag × _STAKED_BASIS_ETH_SPOT_VENUES)` instead of hardcoding `spot_venue="BINANCE-SPOT"`, emitting 6
      slots (was 2) — `lido-deribit-eth-{uniswapv3,curve,binance}-{q1,q2}-usdc-v1-prod`. Added
      `TestDatedSpotVenueCatalogAxis` (4 tests) mirroring the base archetype's `TestSpotVenueCatalogAxis`, proving the
      slot count/spot-venue set/label-uniqueness and that spot_venue is the ONLY thing that varies per expiry tag.
      Updated 2 stale references (a comment + a test docstring) that assumed the old single-slot/2-slot shape; verified
      the 2 hardcoded-label backtest fixtures (`test_paper_run_passive.py`/`test_paper_run_attribution.py`) use the old
      label as an arbitrary passthrough string, not a real catalog lookup — unaffected. 94+107 tests green, full
      `quality-gates.sh` green.
- [x] ✅ [UI] P3. **DONE 2026-07-26 (slot 2), `unified-trading-system-ui@bd527d83` + `unified-trading-pm` (this doc +
      `docs/ui-alignment-ssot.md`).** Determination: the two files are NOT the same case. `ui-reference-data.json` IS
      synced — automated via `.github/workflows/uac-registry-sync.yml` (`repository_dispatch`-triggered auto-PR) and
      documented in `docs/ui-alignment-ssot.md` §1. `capability-manifest.json` / `capability-verdict-matrix.json` are
      **genuinely unsynced by automation** — confirmed by grep (zero `lib/registry` hits under `scripts/openapi/`), by
      `docs/ui-alignment-ssot.md` never mentioning them, and by finding **live drift at investigation time**: UAC's
      `capability-manifest.json` (`unified-api-contracts@13266bf8`, the same regen this issue doc's finding 2 describes)
      was 582 nodes / 2762 edges / 225 venues vs the UI's bundled copy (last synced `a0105d9f`, six minutes earlier) at
      574/2428/194 — i.e. the exact "raydium fix doesn't reach the wizard" scenario, happening for real, right now. The
      only existing safety net (`tests/unit/wizard/parity-gates.test.ts`'s sha256 hash-parity check) never fires in the
      UI repo's own standalone GitHub Actions CI (`ci.yml`'s `test` job checks out only this repo, no UAC sibling) — it
      only fires when a sibling UAC checkout happens to be present (an agent's `.tabs/<slot>/` workspace; a possible
      future fleet-wide CI). Manually re-synced both files (`unified-trading-system-ui@bd527d83`) and updated the 8
      hardcoded manifest-count assertions in `graph.test.ts` / `parity-gates.test.ts` that pinned the old
      574/2428/194/59 counts; full `quality-gates.sh` green (286 tests), shipped via quickmerge. Documented the gap +
      current manual mechanism in `docs/ui-alignment-ssot.md` new §1a. Building real automation (a
      `sync_capability_manifest_to_ui.py` + `uac-registry-sync.yml`-style workflow, or extending the `registry-drift`
      `ci.yml` job) is bigger than this P3 UI-craft todo — filed as its own follow-up below.
- [x] ✅ [SCRIPT] P2. **DONE-AS-SCOPING 2026-07-26 (slot 2), `unified-trading-pm` (this doc +
      `docs/ui-alignment-ssot.md` §1a).** Attempted to scope "extend `registry-drift` like `ui-reference-data.json` —
      that job already checks out UAC/UTL/PM, so it's the smaller lift" (this todo's own original text) and found that
      premise WRONG before writing any CI code: both `generate_capability_manifest.py` and
      `generate_capability_verdict_matrix.py` live-probe OTHER services' own built `.venv`s
      (`_run_service_probe(workspace_root, repo, ...)`, not a light pip-install) — the manifest generator soft-fails to
      a `gap_registry` node if execution-service/features-service are unreachable (so a UAC-only CI job would regenerate
      a manifest that's _structurally different by design_ every run vs. the current full-workspace-regen committed copy
      — 21 real `execution_algo` + 1 `feature_group` node today — i.e. a **permanent false-positive drift signal on
      every future PR**, not a real check), and the verdict-matrix generator HARD-FAILS (`raise RuntimeError`, F48)
      without strategy-service's `.venv`. Shipping a UAC-only version of either check would be a net regression (a CI
      job that always fails or never means anything) verified only by pushing to real GitHub Actions with no fast local
      iteration loop available in this session — did not do that blind. Re-scoped into the two properly-sized follow-ups
      below instead of a broken same-pattern-as-§1 copy-paste. Full writeup: `docs/ui-alignment-ssot.md` §1a.
- [x] ✅ [SCRIPT] P2. **DESIGNED + LOCALLY VERIFIED, BLOCKED ON REAL-CI 2026-07-26 (slot 2).** Built the
      `registry-drift` extension for `capability-manifest.json` per this todo's spec (checkout execution-service +
      features-service + strategy-service with real `uv sync`'d `.venv`s, regenerate, content-normalized diff) —
      confirmed the exact design LOCALLY: `uv sync` in all 3 services (each completed in well under a minute), ran
      `generate_capability_manifest.py` against the slot workspace, got a result **byte-identical** to the committed UAC
      copy once execution/features/strategy-service .venvs were present (this local run is ALSO how the separate
      manifest-completeness bug below was found and fixed). Pushed to a scratch branch + draft PR (#354, then #356) to
      verify against real GitHub Actions before merging (per this todo's own instruction) — the job failed before
      reaching my new steps, at the PRE-EXISTING (unmodified by me) `Install generator deps` step: a UAC/UTL pip
      version-resolution conflict that has broken this job on every push to `main` since 2026-07-21, completely
      unrelated to this work. Filed + partially fixed as its own issue doc:
      `ci_registry_drift_uac_utl_stale_tag_version_conflict_2026_07_26.md` (`unified-trading-system-ui@8c2f3590` ships
      the fetch-depth:0 half-fix; a deeper stale-tag-ancestry issue remains open there, gating cicd/infra). **Did not
      merge the unverified CI-check YAML** — it remains genuinely unexecuted end-to-end, preserved on branch
      `scratch/registry-drift-capability-ci-test` (unmerged, PRs closed) for whoever resumes once that blocker clears;
      the follow-up is tracked as its own todo in that issue doc (item 3). Also fixed, as a related discovery:
      `unified-api-contracts/openapi/capability-manifest.json` was itself **silently incomplete** — its last regen
      (`13266bf8`) ran from an environment missing execution-service/features-service `.venv`s, so 34 real
      `feature_group` nodes had silently degraded to a single gap-fallback node (soft-fail, not a hard error — went
      unnoticed). Regenerated + shipped with the full service environment: `unified-api-contracts@449d1b3d` (nodes
      582→614, edges 2762→2760, `feature_group` 1→35; UAC's own `quality-gates.sh` green, 261-308s) +
      `unified-trading-system-ui@3715d3ec` (bundled-copy re-sync + updated the 8 hardcoded manifest-count test
      assertions, full `quality-gates.sh` green, 113/113 wizard tests + 286/286 total).
- [x] ✅ [SCRIPT] P3. **DESIGNED + LOCALLY VERIFIED, BLOCKED ON REAL-CI 2026-07-26 (slot 2).** Same disposition as the
      P2 todo above — the `capability-verdict-matrix.json` CI-check was built + locally verified (strategy-service
      `uv sync` + `generate_capability_verdict_matrix.py` reproduced the committed UAC copy **byte-identical**,
      confirming F48's `ARCHETYPE_ENGINE_REGISTRY` live-probe resolves cleanly with a real strategy-service `.venv`),
      pushed in the SAME scratch branch/PRs as the manifest check (both checks share the `registry-drift` job and its
      checkout/install steps, so they hit the identical pre-existing blocker before either could execute). Not merged,
      for the same reason; tracked in the same follow-up issue doc.
