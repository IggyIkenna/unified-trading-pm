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
3. `StrategyInstanceDefinition` requires 9 fields including business fields (`family`, `client_id`, `share_class`, etc.) —
   `venues`/`instruments`/`params` are NOT direct fields on the model.
4. `GroupBRunner.register_instance` takes `initial_equity` (not `target_equity`) as a separate Decimal arg.
5. `ArbitragePriceDispersionEngine.REQUIRED_PARAMS = frozenset({"candidate_venues"})` — comma-separated venue list
   must be in the params dict; derived from `config.venues`.
6. `resolve_bucket_name()` in UTL takes keyword-only args `(cloud, kind, asset_group)` — no positional form.
7. `BacktestGroup` enum values are `A_ML_TRAINING`, `B_STRATEGY`, `C_EXECUTION_ALPHA` (NOT bare `B`).
8. `StrategyFamily.ARBITRAGE_STRUCTURAL` is the correct family for `ARBITRAGE_PRICE_DISPERSION` archetype.

The precheck always fires `PRECHECK_UNAVAILABLE` in CLOUD_MOCK_MODE (expected). The wiring (GroupBRunner
exercised over 30 synthetic ticks, result JSON + markdown written) is the deliverable.
