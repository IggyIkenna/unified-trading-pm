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

**Status**: TRIAGED → gap tracker (missing_registry). Wallet-hierarchy doc states DeFi 20/80, CeFi 0/100; no
declarative, queryable registry; per-venue accepted collateral/haircuts/LTV/maintenance margin live nowhere.
Cross-listed because prospectus/risk answers currently require _inferring_ policy from deployment config — an
understanding gap with correctness consequences.

## Discovered during build (append below — date + agent + entry)

### F4-CONFIRMED — Dual truth: archetype_capability_manifest.json is committed alongside Python registry; no drift check

**Status**: OPEN — no drift check exists. Confirmed 2026-06-11 during Phase 0 build.

**Evidence**: `unified_api_contracts/internal/architecture_v2/archetype_capability_manifest.json` (1958 lines, committed)
is the "deterministic serialised form" loaded at import into `ARCHETYPE_CAPABILITY_REGISTRY`. The SSOT docstring says the
manifest is generated first and the Python registry loads it — so the JSON is the truth and the Python objects are
derived. BUT: there is no drift-check script between the JSON and `archetype_capability.py` — if someone edits
`ARCHETYPE_CAPABILITY_REGISTRY` in Python without updating the manifest, or vice versa, the mismatch would be invisible.

**Why it matters**: Two authoritative representations of archetype×instrument truth. The `sync-archetype-capability-to-ui.sh`
script propagates manifest → UI `coverage.ts`, but there is no test that the Python objects match the manifest content.
A codex parity test (Phase 10 in the code comment) is planned but not yet implemented.

**Remedy**: Add a pytest in UAC that re-serialises `ARCHETYPE_CAPABILITY_REGISTRY` to JSON and diffs against the committed
manifest (same pattern as `check_openapi_drift.py`). Until then, treat the manifest JSON as the SSOT and the Python
loader as read-only derived.

### F8 — features-service and ml-service have no root config.py (per-family split)

**Status**: DOCUMENTED — not a bug, by design. Confirmed 2026-06-11 during Phase 0 CONFIG_REGISTRY sweep.

**Evidence**: `features-service` has 8 per-family configs (`calendar/config.py`, `delta_one/config.py`, etc.) but no
`features_service/config.py`. `ml-service` has `training/config.py` + `inference/config.py` but no root config.
The consolidated monorepo architecture uses family-level config isolation, not a single root class.

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
