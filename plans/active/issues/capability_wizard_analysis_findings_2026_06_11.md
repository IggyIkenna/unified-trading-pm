# Capability wizard — analysis findings (bugs / conflicting truths / dual implementations)

**Purpose** (operator direction 2026-06-11): running log of issues found WHILE building the capability wizard/manifest —
distinct from the [gap tracker](capability_wizard_gap_discovery_2026_06_11.md) (which tracks missing
_capabilities/registries_). This doc tracks: **bugs in code**, **gaps in understanding**, **conflicting truths** (two
sources disagree about reality), and **dual-but-different implementations** of the same concept. Every agent working the
[capability wizard plan](../capability_wizard_and_manifest_2026_06_11.md) appends findings here as they surface
(Findings-Triage rule still applies: fix-in-place when ≤30 min and in-scope; log here regardless so nothing is lost).

Format per entry: `### F<N> — <title>` + status (`OPEN | FIXED <repo>@<sha> | TRIAGED → <plan/issue>`), what was found,
why it matters, evidence paths.

## Seeded 2026-06-11 (session pre-audit)

### F1 — Three conflicting truths about which services exist

**Status**: OPEN (Phase 0 fixes). `scripts/openapi/generate_unified_spec.py` SERVICE_REGISTRY (hardcoded, lists 10+
phantom pre-consolidation services), `workspace-manifest.json` (registry), and the actual disk layout disagree about the
service set. Generators run against phantoms; 4 real services (features-service, ml-service,
fund-administration-service, greeks-service) are invisible to the OpenAPI/config extraction.

### F2 — Generator enforcement warns instead of failing → silent rot

**Status**: OPEN (Phase 0 fixes). `_validate_service_coverage()` warns on disk-vs-registry mismatch; nothing fails. The
suite drifted for ~3 weeks after the features/ml consolidation with no signal. Same class as the dead
`check-no-service-deps.py` gate already tracked in `utl_uac_reuse_consolidation_remediation_2026_06_10.md`.

### F3 — architecture_v2 enums invisible to extraction (mechanism, not omission)

**Status**: OPEN (Phase 0 fixes). `extract_uic_enums()` only walks package-root exports of
`unified_api_contracts.internal`; architecture_v2 enums live in submodules and are not re-exported at root — so the
entire v2 taxonomy (53 archetypes, capability registry, kill switches, risk gates) never reached
`ui-reference-data.json`. Understanding gap: consumers may believe ui-reference-data.json is the complete enum surface.

### F4 — Dual truth: ARCHETYPE_CAPABILITY_REGISTRY (code) vs archetype_capability_manifest.json (serialized)

**Status**: OPEN — verify. A serialized `archetype_capability_manifest.json` exists alongside the Python registry.
Establish which is generated from which and whether a drift check exists; if none, this is a dual-implementation risk
(two sources of archetype×instrument truth).

### F5 — Source-mode capability matrix: manual doc vs no registry

**Status**: OPEN (Phase 1 codifies). `source-mode-capability-matrix_2026-06-07.md` encodes batch/live/replay × source ×
transport truth as a hand-written audit doc only; `SOURCE_PRIORITY`/`default_transport_for_source` in UAC encode parts
of it. Same fact, two homes, no reconciliation.

### F6 — strategy_master epic had a duplicated "Assigned active plans" section

**Status**: FIXED in working tree 2026-06-11 (this session, with the related_plans frontmatter update). Two identical
`## Assigned active plans` blocks (auto-populate script `populate_epic_bodies_2026_05_21.py` likely appended instead of
replacing — check the script for idempotency before next run).

### F7 — Collateral policy is derivation, not declaration

**Status**: TRIAGED → gap tracker (missing*registry). Wallet-hierarchy doc states DeFi 20/80, CeFi 0/100; no
declarative, queryable registry; per-venue accepted collateral/haircuts/LTV/maintenance margin live nowhere.
Cross-listed because prospectus/risk answers currently require \_inferring* policy from deployment config — an
understanding gap with correctness consequences.

## Discovered during build (append below — date + agent + entry)

### F4-CONFIRMED — Dual truth: archetype_capability_manifest.json is committed alongside Python registry; no drift check

**Status**: OPEN — no drift check exists. Confirmed 2026-06-11 during Phase 0 build.

**Evidence**: `unified_api_contracts/internal/architecture_v2/archetype_capability_manifest.json` (1958 lines,
committed) is the "deterministic serialised form" loaded at import into `ARCHETYPE_CAPABILITY_REGISTRY`. The SSOT
docstring says the manifest is generated first and the Python registry loads it — so the JSON is the truth and the
Python objects are derived. BUT: there is no drift-check script between the JSON and `archetype_capability.py` — if
someone edits `ARCHETYPE_CAPABILITY_REGISTRY` in Python without updating the manifest, or vice versa, the mismatch would
be invisible.

**Why it matters**: Two authoritative representations of archetype×instrument truth. The
`sync-archetype-capability-to-ui.sh` script propagates manifest → UI `coverage.ts`, but there is no test that the Python
objects match the manifest content. A codex parity test (Phase 10 in the code comment) is planned but not yet
implemented.

**Remedy**: Add a pytest in UAC that re-serialises `ARCHETYPE_CAPABILITY_REGISTRY` to JSON and diffs against the
committed manifest (same pattern as `check_openapi_drift.py`). Until then, treat the manifest JSON as the SSOT and the
Python loader as read-only derived.

### F8 — features-service and ml-service have no root config.py (per-family split)

**Status**: DOCUMENTED — not a bug, by design. Confirmed 2026-06-11 during Phase 0 CONFIG_REGISTRY sweep.

**Evidence**: `features-service` has 8 per-family configs (`calendar/config.py`, `delta_one/config.py`, etc.) but no
`features_service/config.py`. `ml-service` has `training/config.py` + `inference/config.py` but no root config. The
consolidated monorepo architecture uses family-level config isolation, not a single root class.

**Why it matters**: CONFIG_REGISTRY previously listed phantom per-family services (features-calendar-service etc.) with
their old config classes. After consolidation there is no single top-level config to list. Registry comment documents
this explicitly: "configs live per-family — no root FeaturesServiceConfig exists."

**Remedy**: None required for Phase 0. Phase 1 capability manifest extraction should enumerate per-family configs
individually where needed. If a top-level config is ever added to the consolidated repos, update CONFIG_REGISTRY.

### F9 — StrategyArchetype value count grew from 53 (audited) to 57 (current) unnoticed

**Status**: INFORMATIONAL — not a bug, but plan language lags code.

**Evidence**: Phase 0 pre-audit said "53 archetypes". The actual value in `enums.py` is 57 as of 2026-06-11. 4 new
archetypes were added after the audit without a plan update.

**Why it matters**: Success criteria in the plan say "Phase 1: manifest covers all 53 archetypes" — this number should
be "57" (or dynamic). The `ui-reference-data.json` now correctly reflects 57. No code breakage, but the plan prose
hardcodes 53.

**Remedy**: Success criteria updated by Phase 0 progress log entry (57 confirmed). Future plans should reference
`len(StrategyArchetype)` rather than a hardcoded count.

### F10 — TimeInForce had no canonical UAC definition

**Status**: OPEN (canonical home now exists). 2026-06-11, UAC schemas agent: workspace grep found zero pre-existing
TimeInForce enum in UAC — order TIF semantics were implicit per venue adapter. Canonical enum now lives in
`unified_api_contracts/internal/architecture_v2/order_semantics.py` (UAC@6f31f59). Follow-up scan: any adapter-local
TIF/order-type enums in execution-service are now dual implementations to remediate against the canonical.

### F11 — Backtest OHLC fill interpolation method undiscoverable by grep

**Status**: OPEN — needs_code_scan. `MatchingModel.CANDLE_OHLC_INTERPOLATED → BenchmarkFillMode` mapping left None: the
exact interpolation the strategy-service backtest runner uses could not be established by grep (empty results). Route
through Phase 5 agent escalation; answer lands in SIM_ASSUMPTIONS_REGISTRY + manifest annotation.

### F12 — config-registry.json cannot regenerate without `.venv-workspace`; on-host regen EMPTIES it (destructive)

**Status**: OPEN — environmental constraint, NOT a code bug. 2026-06-11, capability-exporter agent (slot-4).
`generate_config_registry.py` imports per-service `config.py`/`service_config.py` modules. On a host with only the UAC
`.venv` + per-service `.venv`s (no aggregate `.venv-workspace`), it extracts **0/32** configs and writes an essentially
empty `config-registry.json` (−9970 lines vs committed). Running it here and committing would silently WIPE the real
registry.

**Why it matters**: the autonomous full-suite regeneration of `generate-unified-openapi.sh` cannot be completed on a
non-workspace-venv host without destroying `config-registry.json`. Mitigation taken: regenerated only the UAC-importable
outputs (`ui-reference-data.json` — byte-identical to committed, already current post-Phase-0;
`capability-manifest.json`

- new), and `git checkout`-restored the emptied `config-registry.json`. The full `unified-trading-system.openapi.json`
  regeneration is likewise blocked (needs every service importable in one interpreter). The `uic-openapi-sync` CI
  workflow regenerates on its own runner regardless, so committed-output staleness self-heals there.

**Remedy**: full-suite regen + `config-registry.json` refresh must run where `.venv-workspace` exists (the laptop / the
CI runner), OR `generate_config_registry.py` should be hardened to per-service-venv subprocess extraction (same idiom
the capability exporter uses for exec/features/ml) so it works on any host. Tracked as a Phase-0 leftover note.

### F13 — `SOURCE_PRIORITY` has no clean (non-`canonical.`) facade; only `registry.possible_manifest` re-exports it

**Status**: OPEN — minor import-surface gap. 2026-06-11, capability-exporter agent. `Transport` +
`default_transport_for_source` ARE re-exported at the `unified_api_contracts` root facade, but `SOURCE_PRIORITY`
(defined in `canonical/crosscutting/source_priority.py`) is only reachable via the deep
`canonical.crosscutting.source_priority` path (blocked by the STEP 5.23 import-surface gate) or the secondary
`registry.possible_manifest` re-export (a `registry.*` deep path, which the gate permits). The exporter imports from
`registry.possible_manifest` to stay gate-clean.

**Why it matters**: consumers wanting `SOURCE_PRIORITY` from the public facade can't
(`from unified_api_contracts import SOURCE_PRIORITY` fails). Other source-mode capability constants are similarly
scattered.

**Remedy**: add `SOURCE_PRIORITY` to the UAC root (or `registry`) facade `__all__` so it joins `Transport` /
`default_transport_for_source`. UAC-source change → not made in this unit (UAC-source edits out of scope for the
exporter task; only `openapi/` outputs committed).

### F14 — `uic-openapi-sync` workflow syncs TS types ONLY, not the registry JSONs (capability-manifest.json included)

**Status**: OPEN — workflow-coverage gap. 2026-06-11, capability-exporter agent. The per-repo `uic-openapi-sync.yml`
(e.g. `unified-trading-system-ui/.github/workflows/`) consumes only `*.openapi.json/yaml` to regenerate
`lib/types/api-generated.ts` on a `repository_dispatch` from UAC. It does **NOT** copy `ui-reference-data.json` /
`config-registry.json` / `system-topology.json` / `capability-manifest.json` into `lib/registry/`. Those registry JSONs
reach the UI ONLY via `generate-unified-openapi.sh`'s own UI-sync block (which the exporter wired for
`capability-manifest.json`).

**Why it matters**: the plan's Phase-1 [VERIFY] todo "manifest ships to `unified-trading-system-ui/lib/registry/` via
the existing uic-openapi-sync workflow" is INACCURATE — that workflow won't ship the manifest. The shipping path is the
generator script's sync block, run on a workspace-venv host or the CI runner that runs `generate-unified-openapi.sh`.
The Phase-1 uic-openapi-sync shipping todo is therefore left UNticked (see plan progress log).

**Remedy**: either (a) extend `uic-openapi-sync.yml` to copy the registry JSONs (it would need UAC to publish them as a
release artifact the workflow can fetch), or (b) re-word the plan todo to point at the `generate-unified-openapi.sh`
sync block as the canonical delivery path. Decision deferred to the UI-phase owner.

**Unit 3 CI-regen audit (2026-06-12):** Confirmed — no CI workflow exists in any repo that runs
`generate-unified-openapi.sh`. Available UAC workflows: quality-gates-v2, schema-health, semver-agent, agent-audit,
canary-offline, backmerge workflows. The `uic-openapi-sync` lives in `unified-trading-system-ui` and
`fund-administration-service` and ships TS types only (F14 confirmed). No new CI infrastructure was built per mandate.
Phase 0 todo annotated with this finding. Unblocking requires operator provisioning `.venv-workspace` on a CI runner OR
operator running `generate-unified-openapi.sh` locally with a full workspace venv.

<!-- AUDIT CONTRADICTION FINDINGS (auto-appended by audit_prospectus_vs_codex.py) -->

**F15:** Venue-category contradiction — `CARRY_BASIS_PERP_INV`

- Codex frontmatter `venue_universe` claims: venue_universe field references CEFI venues: [AAVE, MORPHO, HYPERLIQUID,
  BYBIT]
- ARCHETYPE_CAPABILITY_REGISTRY says: ARCHETYPE_CAPABILITY_REGISTRY has no CEFI capability cells
- Action: Update codex frontmatter OR add capability cells to registry. Severity: WARNING

### F16 — Latent strategy-service bug: log_event(service_name=) TypeError

**Status**: OPEN — strategy-service owner (LOGIC FREEZE prevented in-flight fix). 2026-06-11, stepper agent:
`strategy_service/engine/core/strategy_config_loader.py:83` calls `log_event("ADAPTER_FETCH_FAILED", …, service_name=…)`
but UTL `log_event()` has no `service_name` kwarg → TypeError. Only triggers on the GCS-config path
(`load_initial_positions_from_gcs` with a `strategy_type` hint + missing `GCP_PROJECT_ID`). Stepper sidesteps via the
direct-constructor path.

### F17 — Kill-switch/stop-loss predicates are runtime-fired, not engine-exposed

**Status**: OPEN — post-unfreeze enhancement. `BaseArchetypeEngineV2` has no internal daily-loss/drawdown/stop-loss
predicate; the runtime risk layer fires `orchestrator.on_kill_switch(reason)` externally and the engine only exposes
post-fire `killed`/`kill_reason`/`self_check()→REJECTED`. The scenario stepper therefore reports these as
`introspection_gap=True` (threshold known from config, distance unknowable). Engine-side predicate tracing = named
post-LOGIC-FREEZE todo.

### F18 — deployment-ui jsdom unit suite pre-broken (ESM/CJS)

**Status**: OPEN — pre-existing. Entire jsdom vitest suite fails `ERR_REQUIRE_ESM` on `@exodus/bytes` v1.15.0 (ESM-only)
required CJS-style by `html-encoding-sniffer` (jsdom 29 dep). Partial mitigation committed (`server.deps.inline` in
vitest.config.ts); capability-tab tests use `@vitest-environment node`. Full fix needs upstream bump.

### F19 — deployment-ui rolldown native binding vs Node 20.18

**Status**: OPEN — pre-existing CI concern. Fresh `npm ci` skips `@rolldown/binding-linux-x64-gnu` because Node 20.18 <
the binding's 20.19 engine floor; built only after manual extraction. Node bump or pin needed.

### F20 — GroupBRunner API signature (Phase 5 wire-up findings)

**Status**: RESOLVED — documented for future agents. Phase 5 backtest-on-demand agent (2026-06-11) discovered the
following API signatures that differ from what a naive reading of UAC enums might suggest:

1. `GroupBRunner.__init__` takes only `default_benchmark_mode: BenchmarkFillMode` (not `backtest_group` or `fill_mode`).
2. `V2Subscription` is a NamedTuple with `(strategy_instance_id, venue, instrument)` — NOT `archetype_id`.
3. `StrategyInstanceDefinition` requires 9 fields including business fields (`family`, `client_id`, `share_class`, etc.)
   — `venues`/`instruments`/`params` are NOT direct fields on the model.
4. `GroupBRunner.register_instance` takes `initial_equity` (not `target_equity`) as a separate Decimal arg.
5. `ArbitragePriceDispersionEngine.REQUIRED_PARAMS = frozenset({"candidate_venues"})` — comma-separated venue list must
   be in the params dict; derived from `config.venues`.
6. `resolve_bucket_name()` in UTL takes keyword-only args `(cloud, kind, asset_group)` — no positional form.
7. `BacktestGroup` enum values are `A_ML_TRAINING`, `B_STRATEGY`, `C_EXECUTION_ALPHA` (NOT bare `B`).
8. `StrategyFamily.ARBITRAGE_STRUCTURAL` is the correct family for `ARBITRAGE_PRICE_DISPERSION` archetype.

The precheck always fires `PRECHECK_UNAVAILABLE` in CLOUD_MOCK_MODE (expected). The wiring (GroupBRunner exercised over
30 synthetic ticks, result JSON + markdown written) is the deliverable.

### F22 — Capability registry collapses multi-leg archetypes into a single instrument cell (operator-caught in wizard)

**Status**: OPEN → fix dispatched (leg-spec model). 2026-06-11, operator walkthrough: choosing carry/staked-basis
offered ONLY "Staking" at the Instruments stage. Root cause is the data model, not the wizard filter:
`ARCHETYPE_CAPABILITY_REGISTRY` models CARRY_STAKED_BASIS as ONE cell `(DEFI, staking)`; the real 3-leg structure
("3-leg ATOMIC (stake + lending + perp)") lives in the cell's prose `notes`, and the CeFi perp hedge venues
(binance/bybit/deribit/okx + hyperliquid/gmx/drift) are mixed into a flat `venue_ids` list with no instrument_type or
leg role. The engine DOES know legs (`CarryStakedBasisEngine._derive_structure` gates on
`accepted_perp_collateral(perp_venue)` — the staked-vs-straight-basis conditional) — code-knows vs registry-says =
conflicting truth. Operator requirement: per-archetype restrictions must be **exhaustive and structural** (legs, roles,
instrument types per leg, conditional collateral constraints), not prose.

**Update 2026-06-11 (Phase 2.6 SHIPPED — leg-spec registry landed):** `ARCHETYPE_LEG_STRUCTURES` is now the leg-truth
SSOT in UAC (`unified_api_contracts/internal/architecture_v2/archetype_leg_spec.py`): `ArchetypeLegRole` (11 closed
roles), `LegConstraintKind` (3 closed kinds incl. `requires_collateral_acceptance`), `LegConstraint` (params +
`fallback_variant`), `ArchetypeLegSpec`, `ArchetypeLegStructure`. Seeded 11 archetypes (CARRY_STAKED_BASIS + \_DATED,
CARRY_BASIS_PERP/\_INV, CARRY_BASIS_DATED/\_INV, CARRY_RECURSIVE_STAKED, CARRY_RECURSIVE_BORROW_LENDING_ONLY,
YIELD_STAKING_SIMPLE, YIELD_ROTATION_LENDING, ARBITRAGE_PRICE_DISPERSION), each leg citing engine/codex/cell source. The
staked-basis `requires_collateral_acceptance(LST, hedge_venue)` conditional with `straight_basis` fallback is modelled
structurally; CeFi (binance/bybit/deribit/okx) + DeFi (hyperliquid/gmx_v2/drift) hedge venues are now differentiated
per-leg. The PM capability-manifest exporter emits `leg` nodes + `has_leg`/`trades_instrument`/`supports`/
`leg_constraint` edges; archetypes without a leg spec get one `not_registered` gap edge each (46 today); the two-sided
audit gained a (d) legs-in-prose drift heuristic; the prospectus has a "Leg Structure" table (honest gap line where
absent).

**FOLLOW-UP (P1, tranche, NOT yet done):** the flat `ARCHETYPE_CAPABILITY_REGISTRY` cells **should eventually be DERIVED
FROM the leg specs** (flatten legs → `(asset_group, instrument_type)` cells) so there is a single authored source, plus
a parity drift-check between the two representations. Today the cell model + `archetype_capability_manifest.json` remain
the SSOT for the flat coverage matrix (F4: consumers depend on the JSON, no drift check) and the leg registry is the
SSOT for leg truth — an intentional dual representation documented in the `archetype_leg_spec.py` module docstring. The
6 archetypes the (d) drift heuristic flags (EVENT_DRIVEN, LIQUIDATION_CAPTURE, MARKET_MAKING_CONTINUOUS,
RULES_DIRECTIONAL_EVENT_SETTLED, STAT_ARB_CROSS_SECTIONAL, VOL_TRADING_OPTIONS — cell notes imply legs but no leg spec)
are the first backfill candidates for that tranche.

### F25 — generated_from_commit self-reference keeps committed manifest one-commit stale

**Status**: OPEN — minor design wart. `capability-manifest.json` embeds the UAC HEAD sha; committing the regenerated
file advances HEAD, so an immediate regen differs by exactly that field (observed after UAC@b1a5419). Options: stamp the
SOURCE commits of the registries instead of repo HEAD, or accept one-commit lag (current choice). Determinism within a
fixed HEAD verified unaffected.

### F26 — Cell notes say "3-leg ATOMIC", leg-spec registry derives 4 legs

**Status**: INFORMATIONAL — leg registry is the richer truth. CARRY_STAKED_BASIS leg structure seeded from engine +
codex has FOUR legs (spot_long + stake + lend + hedge_short); the old capability cell's prose says "3-leg ATOMIC
(stake + lending + perp)". The spot acquisition leg was implicit in prose. Another instance of why prose `notes` are not
a restriction model. Also note: the requires_collateral_acceptance constraint sits on the STAKE leg (the leg dropped in
the straight-basis fallback), not the hedge leg — wizard renders it on both venue groups correctly.

### F27 — Carry-staked-basis blocked by venue-id CASE MISMATCH, not an empty registry (strategy-service)

**Status**: OPEN — strategy-service (READ-ONLY for the collateral backfill agent); a real correctness gate, NOT a
test-only quirk. The Phase-3.5 `csb_staked_basis_eth.json` scenario emitted 0 instructions and the note attributed it to
an "empty collateral registry". The actual root cause (2026-06-12): `CarryStakedBasisEngine._derive_structure`
(`strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py:225`) calls
`accepted_perp_collateral(cfg.perp_venue)`, but `cfg.perp_venue` is **lowercase** (`'hyperliquid'`, `'deribit'` — the
slot-config + catalog convention) while `VENUE_COLLATERAL_MATRIX` (`unified_api_contracts/registry/venue_collateral.py`)
keys venues **UPPERCASE** (`'DERIBIT'`). So `accepted_perp_collateral('deribit')` returns `[]` even though
`accepted_perp_collateral('DERIBIT')` returns `['BTC','ETH','USDC','stETH']` → `_derive_structure` always returns None →
the staked carry leg never emits for ANY venue via the default lowercase config. Verified: with `perp_venue='DERIBIT'`
(upper) + a valid non-banned combo, `_derive_structure` returns `LST_AS_MARGIN` (deribit stETH 7.5%, okx wstETH 10% —
exactly the COLLATERAL_REGISTRY backfill values). The default `STAKED_BASIS` slot is `etherfi-hyperliquid` (weETH +
USDC-only Hyperliquid) which is independently a genuine no-emit (weETH not accepted anywhere as perp margin) — masking
the case bug. **Recommended fix (strategy-service)**: normalise `cfg.perp_venue` to the matrix's case at the
`accepted_perp_collateral` call site (or make `venue_collateral.py` lookups case-insensitive). **Demonstrated in
e2e-testing (mine, NOT strategy-service)**: the stepper's `_seed_staked_basis_collateral` seeds `perp_venue` UPPERCASE
from the UAC registry → `csb_staked_basis_eth_lst_accepted.json` (lido stETH + deribit) now EMITS the staked carry leg
(e2e-testing@7075bd1). This is a two-sided-audit hit: the wizard/registry SAYS deribit accepts stETH (true), but the
engine code SILENTLY fails to honor it due to case — exactly "wizard-thinks-possible vs code-actually-does".

### F28 — Two in-repo collateral SSOTs DISAGREE on LST haircuts (venue_collateral.py vs lst_collateral_resolver.py)

**Status**: OPEN — conflicting truths; the collateral backfill followed `venue_collateral.py` (the Stream-A-audited,
per-row-cited SSOT). Two in-repo registries carry per-venue LST collateral haircuts that DISAGREE:
`unified_api_contracts/registry/venue_collateral.py` `VENUE_COLLATERAL_MATRIX` vs
`execution-service/execution_service/services/lst_collateral_resolver.py` `_LST_REGISTRY`. Conflicts: (a) **Hyperliquid
wstETH** — venue_collateral: NOT accepted (USDC-only, matches official Hyperliquid docs + codex playbook);
lst_collateral_resolver: accepted @5% haircut (collateral_factor 0.95). (b) **Bybit stETH** — venue_collateral 10% /
lst_collateral_resolver 15%. (c) **Deribit stETH** — venue_collateral 7.5% (matches official Deribit insights eff.
2026-01-13) / lst_collateral_resolver 20% (stale). (d) **OKX stETH** — venue_collateral NOT-on-discount-list /
lst_collateral_resolver accepted @15%. The COLLATERAL_REGISTRY backfill (uac@f997f3b) follows `venue_collateral.py` (the
audited SSOT, agrees with official docs) and documents each conflict in the entry's `collateral_notes` (F27 tag).
**Recommended decision**: pick `venue_collateral.py` as the single SSOT; either delete the `lst_collateral_resolver.py`
`_LST_REGISTRY` hardcode and have the resolver read `VENUE_COLLATERAL_MATRIX`, or reconcile its numbers to match — the
current divergence means strategy-service haircut sizing (via venue_collateral) and any execution-service consumer of
lst_collateral_resolver would size differently for the same venue/asset.

### F29 — deploy-ui.sh broken since 2026-05-08 script migration (REPO_ROOT drift)

**Status**: FIXED deployment-service@dcb5fdb. Found 2026-06-12 deploying the wizard to UAT: the canonical
`deployment-service/scripts/cloud-run/deploy-ui.sh` (migrated from unified-trading-system-ui/scripts/ on 2026-05-08)
kept `REPO_ROOT="${SCRIPT_DIR}/.."` — correct pre-migration (= UI repo root), post-migration it resolves inside
deployment-service: `--config` pointed at a nonexistent yaml and BOTH build contexts (--cloud submit + local docker)
targeted the wrong repo. Every `--cloud` UI deploy since 2026-05-08 would have failed loudly (config missing) — so
either nobody cloud-deployed the portal since, or they used a different path; worth checking how the current prod
revision was built. Fix: REPO_ROOT now resolves the UI repo explicitly + fail-loud check.

### F30 — Unpinned pnpm@latest in uts-ui Dockerfile broke all docker builds (same family as the setup-uv@v8 rule)

**Status**: FIXED unified-trading-system-ui@0f8f00d6. `corepack prepare pnpm@latest` pulled a new pnpm major whose
ignored-build-scripts handling (ERR_PNPM_IGNORED_BUILDS) fails `pnpm install --prod`, and which no longer reads
package.json pnpm settings. Pinned to pnpm@9.15.9 (the lockfile generation + local dev version). Rule: bump pnpm
deliberately WITH a lockfile migration, never via latest.

### F31 — Dangling .gitleaks.toml symlink breaks next build inside docker context

**Status**: FIXED unified-trading-system-ui@0f8f00d6. `.gitleaks.toml` is a symlink to ../unified-trading-pm (outside
the docker context) → Turbopack's stat walk ENOENTs → build error. Excluded via .dockerignore. Any other cross-repo
symlinks added to UI repos need the same treatment.

### F32 — Cursor-server bundled node (20.18) shadows system node 22 in interactive shells on this host

**Status**: DOCUMENTED — environmental. `~/.cursor-server/bin/.../node` precedes /usr/bin in PATH for Cursor-spawned
shells → vitest/vite fail with ERR_REQUIRE_ESM (require-of-ESM needs node ≥22) and rolldown's native binding is skipped
at install (engine floor 20.19). Remedy for agents on this host: `PATH="/usr/bin:$PATH"` for UI QG runs. System node is
22.22.3 (nodesource); repo standard node22 (.nvmrc).

### F33–F37 — Five selector contradictions: execution-algo truth disagrees across its own code paths

**Status**: OPEN — transcribed declaratively in UAC `algo_compatibility.py::SELECTOR_CONTRADICTIONS` (UAC@180fb56, the
detail SSOT; manifest carries them as edges). Slugs: **F33 iceberg_path_split** (ICEBERG valid via manual API + live
selector + factory but excluded from canonical ALGORITHMS_BY_INSTRUCTION_TYPE), **F34 sor_naming_mismatch** (factory
keys SOR differently from the canonical name), **F35 ghost_algorithms** (SEQUENTIAL_LEGS/SPREAD_ROLL/
BEST_PRICE/KELLY_STAKE valid in enums but unimplemented), **F36 heuristic_selector_bypasses_instruction_type** (live
selection path ignores the instruction-type map), **F37 missing_ssot_doc** (no codex SSOT for algo selection). Exactly
the operator's "codebase isn't blocking impossible combinations" — now declared, blocked in the verdict matrix, and
awaiting execution-service remediation.

### F38 — IBKR modeled as a VENUE in ENDPOINT_REGISTRY (broker/venue conflation — operator-caught, system-design floor)

**Status**: FIXED (manifest layer) uac@cdb59bb + pm@4948325c + pm@613ee27c. Registry pipeline-key migration follow-up
OPEN (venue-axis vocabulary plan). `registry/_endpoint_registry_data.py:650: venue="ibkr"` and
`capability_declarations/_tradfi.py: source="ibkr"`. Operator: IBKR is a BROKER routing to exchanges (CME/ICE/CBOE); the
exchange is the venue; data pipeline/strategy is identical regardless of the final routing hop. CapabilityNodeKind
already has `broker`; collateral registry has BrokerEntry. Fix: manifest classifies ibkr as broker node +
venue⇠routed-via⇢broker edges; wizard renders brokers as the routing axis, not selectable venues. The deeper
ENDPOINT_REGISTRY key migration (venue="ibkr" is load-bearing for the tradfi data pipeline as a SOURCE id) is a tracked
follow-up under the venue-axis vocabulary plan — do NOT rename pipeline keys casually.

### F39 — Wizard offers ~13 venues; manifest has 183 — eligibility lists are hand-named subsets (operator-caught)

**Status**: PARTIALLY FIXED uac@def855c (kraken/bitget/coinbase added to \_CEFI_CLOB_VENUES + key leg seeds) +
pm@4074e49c (audit_venue_coverage.py). OPEN remainder: F42 (adapter-backed venues missing from VENUE_CATEGORY_MAP), F43
(NASDAQ/NYSE not in leg seeds). Missing DeFi venues (Curve, Sushi, PancakeSwap, Orca, Raydium, Phoenix, …) are among the
manifest's orphan venue nodes: present in venue registries but referenced by NO capability cell / leg-spec
eligible_venue_ids (which were seeded from hand-named cell venue lists). Either the execution adapter exists and the
eligibility list is too narrow (registry gap) or no adapter exists (unbuilt dead-end) — per-venue audit required:
instruments universe × ENDPOINT_REGISTRY × execution-service adapter inventory × archetype eligibility → widen
eligibility from ADAPTER INVENTORY (code truth), not hand-named lists.

### F40 — AO server persists runtime usage state into tracked accounts.json → perpetual dirty churn

**Status**: OPEN — recommended owner agent-orchestrator (orchestrator_master). 2026-06-12, operator-directed dirty-repo
cleanup: agent-orchestrator's only dirt was `data/config/accounts.json` rewritten by the SERVER itself — it persists
live usage fields (weekly_msgs_used, five_hour_msgs_used, rate_limited_until, last_used_at) into the operator-edited
tracked config, with ensure_ascii serialization (unicode → — escapes). Consequences: the repo re-dirties on every usage
tick (jams ff-pull cron per the stale-clone rule), and a `git checkout` of the file is safe ONLY because the server
re-persists from memory (verified via GET /api/accounts — live state intact). Remedy: split runtime usage state into an
untracked data/state/ file (or gitignore a dedicated state sidecar); keep accounts.json operator-edited-only; preserve
unicode on any rewrite. Same antipattern class as the generated-artifacts HARD RULE.

## Phase 6A findings (2026-06-12 registry/exporter wave)

### F41 — extract_archetypes_and_families + extract_leg_structures had no broker filter — ibkr leaked as a VENUE node

**Status**: FIXED pm@613ee27c. The F38 broker filter was correctly added to `extract_venues()` (which builds venue nodes
from VENUE_CATEGORY_MAP / DEFI_VENUE_TO_PROTOCOL), but TWO other functions also emit VENUE nodes and were missed: (a)
`extract_archetypes_and_families` iterates `cell.venue_ids` from `ARCHETYPE_CAPABILITY_REGISTRY` (which includes `ibkr`
in 8 archetype cells); (b) `extract_leg_structures` iterates `leg.eligible_venue_ids` from `ARCHETYPE_LEG_STRUCTURES`
(which includes `ibkr` in 4 leg seeds). Both call their own local `add_node()` with no broker guard. Evidence:
`capability-orphan-report.txt` showed `broker_classed_venues: 1  BROKER-AS-VENUE: venue:ibkr` after the initial manifest
regeneration. Fix: added `is_broker()` guard to both `add_node()` functions. broker_classed_venues 1→0. Cite:
`_capability_extract.py:88-97` (arch function), `_capability_extract.py:203-212` (legs function).

### F42 — Adapter-backed venues absent from VENUE_CATEGORY_MAP + ENDPOINT_REGISTRY (phantom adapter coverage)

**Status**: OPEN — logged for registry alignment follow-up. The venue coverage audit (F39, pm@4074e49c) found 6 venues
with real execution adapters that do NOT appear in `VENUE_CATEGORY_MAP` (UAC registry of known venues with category):

- FX (fx_adapter.py:24) — TradFi FX via IBKR; no VENUE_CATEGORY_MAP entry
- BITFINEX-SPOT (bitfinex_native.py:167) — CeFi CLOB; no VENUE_CATEGORY_MAP or ENDPOINT_REGISTRY entry
- BITGET-FUTURES (bitget_native.py:125) — CeFi CLOB; ENDPOINT_REGISTRY has `bitget` (generic) but not the suffixed form
- BITGET-SPOT (bitget_native.py:125) — same
- KRAKEN-FUTURES (kraken_rest_adapter.py:159) — CeFi CLOB; no VENUE_CATEGORY_MAP entry
- KRAKEN-SPOT (kraken_rest_adapter.py:159) — same Impact: these adapters can execute but the wizard/manifest has no
  venue node for them (the manifest picks them up via the adapter inventory seed in audit_venue_coverage.py, but they
  are NOT in VENUE_CATEGORY_MAP or INSTRUMENT_TYPES_BY_VENUE, so no venue node is emitted by `extract_venues()`).
  Remedy: add entries to `VENUE_CATEGORY_MAP` + `INSTRUMENT_TYPES_BY_VENUE` (UAC registry files) for each. Deferred to
  registry alignment phase.

### F43 — NASDAQ/NYSE adapters exist but venues not in any leg eligible_venue_ids (TradFi equities gap)

**Status**: OPEN — logged for leg-seed follow-up. nasdaq_adapter.py:24 (venue_name="NASDAQ") and nyse_adapter.py:24
(venue_name="NYSE") exist as ibkr-routed TradFi adapters, but NASDAQ and NYSE do not appear in any archetype leg's
`eligible_venue_ids`. This means the wizard cannot select these venues for any leg in the current manifest, even though
execution is possible. The leg seeds were sourced from strategy-engine structs which focus on crypto/perp archetypes;
equities/equity-ETF archetypes (RULES_DIRECTIONAL_CONTINUOUS, ML_DIRECTIONAL_CONTINUOUS, EVENT_DRIVEN, STAT_ARB
variants) reference ibkr but not the downstream exchange venues. Remedy: add nasdaq/nyse to the relevant
equity-archetype leg seeds with citation to their adapter files. Deferred to next registry iteration.

### F44 — \_capability_extract.py extract_venues() had duplicate inline broker block after extract_brokers() was added

**Status**: FIXED pm@300 (via fix PR). The upstream commit (pm@4948325c) added `extract_brokers()` as a standalone
function AND retained an inline `_tradfi_brokers` dict inside `extract_venues()` (an intermediate implementation from a
prior partial agent). Both emitted broker nodes + routed_via edges, causing duplicate nodes. The inline block was
removed (pm@fix PR #300). broker:ibkr node count 2→1 in the regenerated manifest.

### F45 — Exposure normalization is undeclared: primitives exist, no service owns the netting pipeline

**Status**: OPEN — genuine capability gap (answers the `[AGENT] P1 exposure-normalization` gap-tracker item). 2026-06-13
code-scan across greeks-service / features-service / UTL / UAC. The PRIMITIVES for LST→underlying exposure equivalence
exist in UAC: `TOKEN_EQUIVALENCE_GROUPS` + `is_token_equivalent()`
(`registry/capability_declarations/_defi.py:870-940,1019` — full 20+ LST universe: ETH group {ETH,WETH,STETH,WSTETH,
CBETH,RETH,WEETH,…}, SOL group {SOL,WSOL,MSOL,STSOL,JITOSOL,…}) and `LST_BASE_ASSET` + `lst_adjusted_value()`
(`registry/token_wrapping.py:43-47,159` — 3 wrapped forms, oracle-ratio base-equivalent quantity). The OUTPUT schema
exists too: `RiskMetrics.delta_composite: dict[str,Decimal]` ("net delta per underlying", `internal/risk.py:82`) +
`gross/net/long/short_exposure` (`internal/risk.py:169-172`). greeks-service computes per-INSTRUMENT Black-Scholes
greeks (`kernels/black_scholes.py:75-183`). **But NO service owns the end-to-end pipeline** that (a) maps each LST leg
to its ETH/SOL underlying via the equivalence group, (b) multiplies position size × per-leg delta for base-currency-
denominated delta, (c) nets across legs into `delta_composite` / a USD-normalized exposure view. No `compute_net_delta`
/ `aggregate_delta` / `portfolio_delta` / `exposure_normalizer` exists in any scanned repo. **Why it matters**: the
prospectus Exposure section + the wizard's staked-ETH-vs-ETH-equivalence answer + any portfolio-mode netting all need
this. **Recommended owner**: a risk-service or strategy-service pre-trade layer consuming `lst_adjusted_value` + per-leg
greeks emitting `delta_composite`. Not built in this dispatch (no LOGIC-FREEZE-safe surface to add it); recorded for a
successor plan. The prospectus already emits an honest gap line for staked-vs-spot equivalence.

### F46 — Three CeFi perp adapters are NotImplementedError scaffolds (binance/bybit/okx) — BLOCKED-CREDENTIALS

**Status**: OPEN (pre-existing; surfaced by the 2026-06-13 order-semantics scan).
`trade_execution/adapters/ binance_native.py:326`, `bybit_native.py:318`, `okx_native.py:329` all raise
`NotImplementedError` on `place_order` — HMAC/v5 request SIGNING is implemented but the HTTP client is not injected, so
no order reaches the venue. Only hyperliquid (CCXT), deribit (perp+options), and drift (Solana CLOB) place
CeFi/DeFi-CLOB orders end-to-end today. This is the live-execution coverage truth now declared in
`VENUE_ORDER_SEMANTICS` (`auth_wired=not_registered` for the three scaffolds). Wiring them is BLOCKED-CREDENTIALS (needs
live API keys + the HTTP client injection). Not a wizard/manifest defect — the manifest now honestly reflects it.

### F47 — Verdict-matrix declares venue cells AVAILABLE that the v2 slot-label venue-token registry rejects

**Status**: OPEN (surfaced by EXECUTION, 2026-06-13 — the Wave-2 #3 config-space fuzzer
`e2e-testing/scripts/strategy/config_space_fuzzer.py`). The committed verdict matrix
(`unified-api-contracts/openapi/capability-verdict-matrix.json`) declares AVAILABLE leg cells for **9 venue ids whose
alnum-stripped form is NOT in `KNOWN_VENUE_TOKENS`** (`unified_api_contracts.internal.architecture_v2.venue_tokens`):
`balancer_v2`, `balancer_v3`, `betfair_direct`, `gmx_v2`, `jupiter`, `pancakeswap_v3`, `smarkets_direct`, `sommelier`,
`sushiswap_v3` (11 of 43 AVAILABLE venues fail the alnum-strip token test; the 9 above were the ones sampled). When the
fuzzer compiles such a cell to a v2 slot label (`{archetype}@{venue}-{instr}-usdt-prod`) the strategy-service parser
`split_scope_tokens` raises `ValueError: scope tokens (…) start with a non-venue token` — so **no v2 strategy slot can
be constructed for those venues at all**, even though the wizard would offer them as reachable. **Why it matters**: the
capability wizard can present a config (venue × archetype) the strategy engine literally cannot instantiate — a
mechanical dead-end between the manifest/verdict surface and the slot-identity grammar. Reproduced as a typed
`unbuildable_slot` dead-end across 20 sampled configs (3/archetype run; deterministic). **Recommended decision**: align
the two SSOTs — either add the missing venue tokens (with their `_vN`/`_direct` suffix normalisation) to
`KNOWN_VENUE_TOKENS` + `split_scope_tokens`, OR have the verdict-matrix generator + the wizard venue-eligibility list
exclude venues that have no slot-label token (compose with F39 "wizard offers ~13 venues; manifest has 183" — eligible
lists are already hand-named subsets). Not fixed in this dispatch (LOGIC-FREEZE on strategy-service + collision boundary
on UAC); recorded for a successor alignment plan. Companion smoke test:
`e2e-testing/scripts/strategy/test_config_space_fuzzer_smoke.py`.

### F48 — Verdict-matrix declares 22 archetypes reachable that have NO v2 engine registered (all VOL\_\* + MARKET_MAKING\_\*)

**Status**: OPEN (surfaced by EXECUTION, 2026-06-13 — the Wave-2 #3 config-space fuzzer). The verdict matrix enumerates
AVAILABLE `(venue × instrument_type × algo)` cells for **22 archetypes for which `V2BatchHarness` / the v2 engine
registry has NO engine** — every `VOL_*` family (`VOL_0DTE_GAMMA_SCALPING`, `VOL_ARB_RV_IV`, `VOL_CARRY`,
`VOL_CROSS_ASSET_SPREAD`, `VOL_DISPERSION`, `VOL_LEAPS_CONVEXITY`, `VOL_MARKET_MAKING`, `VOL_ML_LEAN`,
`VOL_OVERLAY_COVERED_CALLS`, `VOL_OVERLAY_PROTECTIVE_PUT`, `VOL_RATIO_SPREAD`, `VOL_SPREAD_STRUCTURES`, `VOL_STRADDLE`,
`VOL_SYNTHETIC_DELTA`, `VOL_TERM_STRUCTURE_ARB`, `VOL_TERM_STRUCTURE_SLOPE`, `VOL_VARIANCE_SWAP`) plus every
`MARKET_MAKING_*` family (`MARKET_MAKING_INVENTORY_SKEW`, `MARKET_MAKING_ML_LEAN`, `MARKET_MAKING_PASSIVE_SPREAD`,
`MARKET_MAKING_PREDICTION`, `MARKET_MAKING_QUEUE_MICROSTRUCTURE`). Compiling + stepping a sampled config for any of them
raises `KeyError: 'no v2 engine registered for archetype <X>'` at the first `on_tick`. **Why it matters**: the wizard's
reachability surface (derived from leg-structure / selector capability declarations) is WIDER than the runnable v2
engine set — a wizard user could configure + "promote" a VOL or market-making strategy that has no engine behind it, a
silent mechanical dead-end. Reproduced as a typed `no_v2_engine` dead-end across 63 sampled configs (deterministic).
**This is expected if VOL / market-making are intentionally out-of-scope for the v2 engine today** — but then the
verdict matrix (and the wizard) should mark those archetypes `not_registered` / blocked, not AVAILABLE. **Recommended
decision**: gate the verdict-matrix `available` verdict (and the wizard archetype list) on v2-engine-registration, OR
register the missing engines. Not fixed in this dispatch (LOGIC-FREEZE + collision boundary on UAC); recorded for the
successor alignment plan alongside F47.

### F49 — Custody/signing-surface dimension entirely unmodeled + `custody_provider` node-kind is a dumping ground

**Status**: OPEN (big — missing config dimension + categorization bug). UAC `SigningSurface` enum is REAL and config-relevant
(`registry/withdrawal_approval_rules.py` etc.: `CLOUD_KMS_ENCRYPTED` May-23, `COPPER_MPC`+`CEFFU` June-1, `FIREBLOCKS_MPC`
out-of-scope; per-wallet `signing_surface` per codex/04-architecture/custody-providers.md). But the capability manifest has
**0 nodes representing custody/signing surfaces**, and the wizard has **no custody stage**. Worse, the `custody_provider`
NODE KIND is used by `scripts/openapi/_capability_gaps.py` (lines 194/250/254/355) as a FALLBACK kind for risk-gate-layers,
kill-switches, gap-registries, and collateral venues — so its 28 nodes contain ZERO actual custody providers and the kind is
semantically meaningless. **Fix**: (a) introduce a SigningSurface/custody registry + emit real `custody_provider` nodes from
the UAC enum; (b) give risk_layer / kill_switch / gap_registry their OWN node kinds (or a generic `meta` kind) instead of
overloading `custody_provider`; (c) add a custody/signing-surface wizard stage (it constrains which wallets/venues a config
can use). Owners: UAC (registry) + PM exporter (node kinds) + uts-ui (stage).

### F50 — `fund_structure` registry backfilled but exporter emits 0 fund_structure-kind nodes

**Status**: OPEN (exporter bug). `OFFERED_FUND_STRUCTURES` (POOLED + SMA, backfilled 2026-06-13) produces only a single
`gap_registry:fund_structure` node (mis-kinded `custody_provider`); the manifest has **0 `CapabilityNodeKind.FUND_STRUCTURE`
nodes**. The exporter never walks OFFERED_FUND_STRUCTURES into per-structure nodes/edges. **Fix**: emit a fund_structure node
per offering (POOLED/SMA) with its share-classes/cadence metadata, like collateral venues are emitted. Owner: PM exporter.

### F51 — Chain nodes double-counted (numeric chain-id AND name for the same chain)

**Status**: OPEN (exporter dedup bug). 41 chain nodes = 35 numeric chain-ids (`1`,`10`,`137`,`42161`,…) + 6 names
(`ETHEREUM`,`ARBITRUM`,`BASE`,`BSC`,`OPTIMISM`,`AVALANCHE`) — the SAME chains represented twice (e.g. `chain:1` and
`chain:ETHEREUM`). Inflates the count + the wizard's chain universe. **Fix**: normalize to one canonical node per chain
(map numeric chain-id ↔ name; CHAIN_RPC_TEMPLATES is the SSOT). Owner: PM exporter (`_capability_extract.py`).

### F52 — `data_source` nodes mix internal services with external vendors

**Status**: OPEN (mislabel). `execution_service`, `instruments_service`, `features_onchain_service` are internal data
PRODUCERS, not external data sources — they sit alongside real vendors (databento, massive, helius_rpc, chainlink,
polymarket_clob/gamma, odds_api, api_football, footystats, eia, open_meteo). **Fix**: either a separate node kind for
service-derived feeds, or exclude services from `data_source`. Owner: PM exporter.

### F53 — ML models severely under-surfaced (1 node vs a real model registry)

**Status**: OPEN (registry under-coverage). Only 1 `ml_model` node (`variant_config`) despite ml-service having a real
model registry + ensemble trainers (`training/app/training/sports_ensemble_trainer.py`,
`inference/app/inference/ensemble_inference.py`, `core/training_orchestrator.py`). The wizard's "which ML model" dimension
is essentially empty. **Fix**: walk the ml-service model registry (per-archetype model variants) into `ml_model` nodes +
archetype→model edges. Owner: PM exporter (per-service venv import, like exec-algos/feature-groups) + ml-service registry.

---

## Risk-domain index (cross-cut roll-up — 2026-06-15)

Operator-requested view: the findings above grouped by RISK DOMAIN with current status + code evidence. This index is
the **current-truth roll-up** — individual `### F<n>` sections above may show a stale inline "Status: OPEN" (e.g.
F49–F53 are FIXED as of 2026-06-14); trust this table. Status taxonomy: **FIXED** · **OPEN** (actionable now) ·
**LOGIC-FREEZE** (engine fix gated on the strategy-service freeze lifting; surface-ready) · **BLOCKED-CREDENTIALS** ·
**BLOCKED-OPERATOR-DECISION**. Verified-in-code 2026-06-15 (grep-then-read).

| Domain | Findings | Status | Evidence |
| --- | --- | --- | --- |
| Unfinished adapters | F46 (binance/bybit/okx perp `place_order`) | BLOCKED-CREDENTIALS | `binance_native.py:326`/`bybit_native.py:318`/`okx_native.py:329` `raise NotImplementedError` |
| Unfinished adapters | F42 (6 adapter-backed venues absent from VENUE_CATEGORY_MAP), F43 (NASDAQ/NYSE in no leg eligibility) | OPEN | UAC registry |
| Catalogue ↔ engine | F47 (verdict-matrix venues v2 slot-token registry rejects), F48 (22 VOL_*/MARKET_MAKING_* archetypes, no v2 engine) | LOGIC-FREEZE | `e2e-testing/scripts/strategy/config_space_fuzzer.py` dead-ends |
| Catalogue ↔ engine | F27 (carry-staked-basis `deribit`≠`DERIBIT` case mismatch), F33–F37 (execution-algo selector contradictions) | LOGIC-FREEZE | strategy-service / execution-service |
| Catalogue ↔ engine | F22 (multi-leg collapsed to one cell) | FIXED (leg-spec registry) | derive-from-legs follow-up open |
| Collateral + movements | **F28 (two collateral SSOTs disagree on LST haircuts — 4 conflicts)** | OPEN | `venue_collateral.py` vs `lst_collateral_resolver.py:51-82` (HL wstETH; Bybit 10%vs15%; Deribit 7.5%vs20%; OKX absent vs 15%) |
| Collateral + movements | F7 (policy was derivation) | FIXED (registry backfilled) | — |
| Trader ledger | `transfer_purpose` + COLLATERAL_POSTED/MARGIN_RELEASED | UAC surface FIXED; **no emitter** (LOGIC-FREEZE) | symbols only in UAC `crosscutting/transfer_events.py` + `ledger/_enums.py`, zero consumers |
| PnL / attribution | **F45 (exposure netting — primitives exist, no service owns the pipeline)**, multi-leg inter-leg delta = no owner | BLOCKED-OPERATOR-DECISION (owner) | — |
| Balances | margin: `margin_event_emitter.py:98` hardcodes `venue_type="defi"`; `venue_balance_tracker.py` is sports-only; `margin_health.py:32` Phase-1 stub `return []` | LOGIC-FREEZE | strategy-service (3 files) |
| Balances | F40 (AO writes runtime state into tracked `accounts.json`) | OPEN | agent-orchestrator |
| Reconciliation | F1/F2/F3 (service-set truths; coverage warns-not-fails; v2 enums invisible) | FIXED (Phase-0) | — |
| Reconciliation | F12 (config-registry regen empties destructively on non-workspace-venv host) | OPEN (environmental) | — |
| Circuit breakers / kill-switch | F17 (predicates runtime-fired, not engine-introspectable), F16 (`log_event(service_name=)` TypeError on GCS-config path) | LOGIC-FREEZE | strategy-service |
| Circuit breakers / kill-switch | F49 (`custody_provider` node-kind was a dumping ground incl. kill_switch) | FIXED (Waves A/B/C) | — |
| Redundancy / duplication | F6, F41, F44, F51, F52 | FIXED | — |
| Registry under-coverage | F50 (fund_structure), F52 (data_source split), F53 (ml_model 1→8 + signal-grounded edges) | FIXED (Wave B/C 2026-06-14) | manifest 574/2433 |

## Open findings — tracked todos (2026-06-15, operator-requested capture)

> Converting the prose findings above into actionable checkboxes (Capture-Discoveries HARD RULE). LOGIC-FREEZE items are
> tracked but NOT actionable until the strategy-service freeze lifts — surface is ready. A full remediation wrapper plan
> (`parent_epic:` + `assigned_vm:` → epic-VM dispatch) is the next step if these are to be worked, per Findings-Triage.

**Actionable now (registry / config / infra — NOT engine-frozen):**

- [ ] [SPEC] P1. **F28 — reconcile the two collateral-haircut SSOTs** (`venue_collateral.py` vs
      `lst_collateral_resolver.py`): pick the correct per-venue LST haircut, delete the duplicate SSOT (4 known
      conflicts: HL wstETH accept?; Bybit stETH 10% vs 15%; Deribit 7.5% vs 20%; OKX 15% vs absent). Data-correctness
      risk. Target: confirm owner repo (UTL/strategy-service) + whether freeze-gated before flipping.
- [ ] [SCRIPT] P2. **F42 — register the 6 adapter-backed venues** (FX + BITFINEX/BITGET/KRAKEN spot+futures) in
      `VENUE_CATEGORY_MAP` + `ENDPOINT_REGISTRY`. Target: unified-api-contracts.
- [ ] [SCRIPT] P2. **F43 — add NASDAQ/NYSE to a leg's `eligible_venue_ids`** (TradFi equities adapters exist, no leg
      references them). Target: unified-api-contracts.
- [ ] [SCRIPT] P3. **F40 — gitignore AO runtime `accounts.json`** (server persists usage state into a tracked file →
      perpetual dirty churn). Target: agent-orchestrator.

**Tracked, gated (engine — strategy-service LOGIC FREEZE / credentials / operator decision):**

- [ ] [ADAPTER] P1. **F46 — implement binance/bybit/okx perp `place_order`** (scaffolds raise NotImplementedError).
      BLOCKED-CREDENTIALS (named venue API creds). Target: execution-service.
- [ ] [SPEC] P1. **F45 — assign an owner for the exposure-normalization / netting pipeline** (LST→underlying net delta;
      primitives exist, no service owns it; multi-leg inter-leg delta unmanaged). BLOCKED-OPERATOR-DECISION (which
      service owns netting). Target: strategy-service or UTL (operator pick).
- [ ] [LOGIC] P1. **F27 — carry-staked-basis venue-id CASE MISMATCH** (`deribit`≠`DERIBIT`) blocks emission.
      LOGIC-FREEZE. Target: strategy-service.
- [ ] [LOGIC] P2. **F47 — verdict-matrix declares venues the v2 slot-token registry rejects** (unbuildable slot).
      LOGIC-FREEZE. Target: strategy-service.
- [ ] [LOGIC] P2. **F48 — 22 VOL_*/MARKET_MAKING_* archetypes reachable with no v2 engine.** LOGIC-FREEZE. Target:
      strategy-service.
- [ ] [LOGIC] P2. **F33–F37 — reconcile the 5 execution-algo selector contradictions** (iceberg/SOR/ghost-algos/
      heuristic-bypass/no-SSOT). LOGIC-FREEZE. Target: execution-service.
- [ ] [BUG] P2. **F16 — latent `log_event(service_name=)` TypeError on the GCS-config path.** LOGIC-FREEZE. Target:
      strategy-service.
- [ ] [SPEC] P3. **F17 — expose kill-switch/stop-loss predicates for engine introspection** (currently runtime-fired
      only — invisible to the capability graph). Post-unfreeze enhancement. Target: strategy-service.

> The **CeFi-margin-traceability cluster** (CeFi margin emitter DeFi-only · `margin_health` stub · no CeFi balance
> tracker · collateral runtime consumer) is already tracked as `- [ ]` todos in
> [capability_wizard_gap_discovery_2026_06_11.md](capability_wizard_gap_discovery_2026_06_11.md) (margin audit) — not
> duplicated here.

## Follow-up todo — delete the dead version-bump landmine (2026-06-15)

- [x] ✅ [SCRIPT] P2. **Delete the dead `version-bump.yml` system** — DONE **PM@c8c4e0729** (2026-06-15). Removed
      `scripts/propagation/templates/version-bump.yml` + `scripts/propagation/rollout-version-bump-workflow.py` (the dead
      `[skip ci]` bump writer, superseded by `semver-agent.yml`, deployed to 0 repos but re-runnable → would have
      reintroduced the staging→main promote-PR deadlock) + added a SUPERSEDED banner to
      `docs/repo-management/version-cascade-flow.md` pointing to `semver-agent.yml`. Landing was held ~1h behind a
      transient PM version-alignment flap (local trailing main while the 5-day backlog drained fleet-wide); a watcher
      landed it the moment alignment held stably green. Root cause was already fixed + deployed: `semver-agent.yml.tmpl`
      apply step commits the bump with NO `[skip ci]` (2026-06-09) and was rolled out to all 24 repos 2026-06-15.
