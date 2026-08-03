---
doc_type: issue
title:
  "unified-api-contracts/scripts/check_sdk_version_alignment.py — stale hardcoded INTERFACES list (11/16 dead) and
  api-contracts' own pyproject.toml is missing 3 SDK pins that SCHEMA_VERSIONS.md already documents"
summary:
  "While fixing check_sdk_version_alignment.py's D13-blind api-contracts-version-overlap check
  (ci_satellite_ao_dispatch_batch1-029, which removed that dead sub-check and fixed an adjacent stale-directory-name bug
  in the surviving SDK-schema-alignment check), found two further, genuinely separate problems in the same file/repo,
  out of that todo's scope. (1) The script's hardcoded INTERFACES list (16 repo paths) is majority-stale: only 5 of 16
  still exist in the current 25-repo fleet (workspace-manifest.json repositories{}); the other 11 are old-architecture
  interface/per-feature-service repo names with no current-fleet successor confirmed, so the SDK-alignment check only
  ever actually exercises 5 consumers today, silently. (2) Running the now-unmasked SDK-alignment check live surfaces a
  real, currently-true gap: api-contracts' own pyproject.toml [project.optional-dependencies.schema-validation] does not
  pin databento/ccxt/ib_insync at all, even though SCHEMA_VERSIONS.md's 'Pinned [schema-validation] Dependencies' table
  (lines 58-61) already documents specific target ranges for exactly these three (plus tardis-client, which the script
  does NOT flag as missing) and the schema modules for all three genuinely exist under unified_api_contracts/external/.
  Also noted in passing: tests/unit/test_schema_version_alignment.py's test_schema_validation_deps_match_schema_versions
  only asserts version-equality for packages ALREADY present in the schema-validation extras — it never flags a
  SCHEMA_VERSIONS.md-documented package that's entirely ABSENT from pyproject.toml, which is exactly how finding 2 went
  undetected by the one test that should have caught it."
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-api-contracts]
scope: [engineer, admin]
tags: [ci, cicd, version-alignment, stale-config, fleet-consolidation, schema-validation]
related: [/plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md]
created: 2026-08-03
last_updated: 2026-08-03
priority: P3
parent_epic: infrastructure_master
source:
  "Found while working ci_satellite_ao_dispatch_batch1-029 ([INFRA] P3, check_sdk_version_alignment.py's
  _get_api_contracts_version() D13-blindness) — two distinct, adjacent staleness/drift bugs in the same file/repo, out
  of that todo's scope (which was specifically about the api-contracts-version-overlap sub-check, since removed)."
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: refactor
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    unified-api-contracts/scripts/check_sdk_version_alignment.py,
    unified-api-contracts/SCHEMA_VERSIONS.md,
    unified-api-contracts/tests/unit/test_schema_version_alignment.py,
    /plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
  ]
---

## What I found

Working `ci_satellite_ao_dispatch_batch1-029`, after removing the dead api-contracts-version-overlap check and fixing a
stale `api_contracts_external` → `external` directory-name bug in `_schema_module_exists()` (both in scope for that
todo), I ran the script live to verify the surviving SDK-schema-alignment check (databento/tardis-client/ccxt/ib_insync
version-overlap vs. api-contracts' `[schema-validation]` pins). Two further problems surfaced, both pre-existing and out
of that todo's scope:

### 1. The hardcoded `INTERFACES` list is majority-stale

Of the script's 16 `(name, Path("../repo"))` entries (the default sweep target when `--interface-path` isn't passed),
only 5 still exist in the current fleet (`workspace-manifest.json`'s `repositories{}`, 25 repos):
`unified-trading-library`, `instruments-service`, `strategy-service`, `alerting-service`,
`market-data-processing-service`. The other 11 — `unified-market-interface`, `unified-trade-execution-interface`,
`unified-reference-data-interface`, `unified-cloud-interface`, `market-tick-data-handler`, `execution-services`,
`ml-inference-service`, `ml-training-service`, `features-volatility-service`, `features-onchain-service`,
`features-calendar-service`, `features-delta-one-service` — are absent from both the manifest and a full-fleet slot's
directory listing. Plausible current-fleet successors by name/CLAUDE.md system-map similarity
(`execution-services`→`execution-service`, `market-tick-data-handler`→`market-tick-data-service`,
`ml-inference-service`+`ml-training-service`→`ml-service`, the four `features-*-service` entries→`features-service`) are
NOT verified — this needs a real per-repo dependency check, not a name-similarity guess. The 4 `unified-*-interface`
entries have no obvious successor at all.

Because `main()`'s default sweep does `if not iface_path.exists(): continue`, this is entirely silent — the script (when
it does eventually get wired somewhere, or when run manually) only ever checks the 5 survivors and never errors or warns
about the 11 unreachable paths.

### 2. api-contracts' own `[schema-validation]` extras are missing 3 documented SDK pins

A live run (`uv run python scripts/check_sdk_version_alignment.py`, 2026-08-03, post-fix) reports:

```
ERROR: unified-trading-library: uses databento but api-contracts [schema-validation] does not pin databento (add to pyproject.toml)
ERROR: instruments-service: uses databento but api-contracts [schema-validation] does not pin databento (add to pyproject.toml)
ERROR: instruments-service: uses ccxt but api-contracts [schema-validation] does not pin ccxt (add to pyproject.toml)
ERROR: instruments-service: uses ib_insync but api-contracts [schema-validation] does not pin ib_insync (add to pyproject.toml)
```

Confirmed via direct `tomllib` parse: `pyproject.toml`'s `[project.optional-dependencies.schema-validation]` is
currently EMPTY. But `SCHEMA_VERSIONS.md` (lines 58-61, "Pinned [schema-validation] Dependencies" table) already
documents specific target ranges for exactly these packages: `databento >=0.32.0,<1.0.0`,
`tardis-client >=1.3.7,<2.0.0`, `ccxt >=4.5.24,<5.0.0`, `ib_insync >=0.9.86,<1.0.0` (script doesn't flag `tardis-client`
missing — not checked here whether that one differs). The schema modules themselves genuinely exist
(`unified_api_contracts/external/{databento,ccxt,ibkr}/`), so this isn't a "no schema support" gap — just the
version-pin declaration never landed in `pyproject.toml`, even though the doc SSOT already specifies exactly what it
should say.

**Why the existing test didn't catch it**: `tests/unit/test_schema_version_alignment.py`'s
`test_schema_validation_deps_match_schema_versions` only asserts version-equality for a package
`if pkg in schema_validation` — i.e. it validates packages ALREADY present in the pyproject extras against
SCHEMA_VERSIONS.md, but never asserts that a SCHEMA_VERSIONS.md-documented package must be PRESENT at all. An
entirely-missing pin is invisible to it by construction.

## Why it matters

Neither is urgent — `check_sdk_version_alignment.py` is not wired into any workflow (confirmed in
ci_satellite_ao_dispatch_batch1-029), so nothing currently gates on either finding. But both are real, currently-true
drift, and (1) undermines the value of keeping the SDK-alignment check alive at all (11/16 blind spots), while (2) is
exactly the kind of silent schema/SDK version mismatch the check exists to catch.

## Recommended decision

- [ ] [INFRA] P3. Add the 3 missing SDK pins to `unified-api-contracts/pyproject.toml`'s
      `[project.optional-dependencies.schema-validation]` — `databento>=0.32.0,<1.0.0`, `ccxt>=4.5.24,<5.0.0`,
      `ib_insync>=0.9.86,<1.0.0` (copy SCHEMA_VERSIONS.md's already-documented target ranges verbatim; also confirm
      whether `tardis-client` is already pinned or has the same gap, since the live run didn't flag it — check before
      assuming it's fine). **Done when**: a live `uv run python scripts/check_sdk_version_alignment.py` run no longer
      reports a missing-pin error for any of the three, `tests/unit/test_schema_version_alignment.py` stays green, and
      `quality-gates.sh` is green. Repo: unified-api-contracts.
- [ ] [INFRA] P3. Replace `check_sdk_version_alignment.py`'s hardcoded `INTERFACES` list with the fleet's real current
      api-contracts consumers. Derive the list by grepping every repo in `workspace-manifest.json`'s `repositories{}`
      for a `unified-api-contracts` dependency in its `pyproject.toml` (do not guess successor names from the old list —
      verify each). Drop entries with no current-fleet repo; add any real consumer missing from the old list. **Done
      when**: the list contains only real, existing repo paths confirmed via the manifest, a live
      `uv run python scripts/check_sdk_version_alignment.py` run exercises all of them (no silent `continue`-skips on
      missing paths — spot-check by temporarily logging skip count), and `quality-gates.sh` is green. Repo:
      unified-api-contracts.
- [ ] [INFRA] P3. Harden `test_schema_validation_deps_match_schema_versions` (in
      `unified-api-contracts/tests/unit/test_schema_version_alignment.py`) to also assert every
      SCHEMA_VERSIONS.md-documented `[schema-validation]` package (except the already-special-cased `pydantic`) is
      PRESENT in pyproject.toml's schema-validation extras, not just version-equal when present — this is the exact
      blind spot that let finding 2 above go undetected. **Done when**: a synthetic test fixture with a
      documented-but-absent package fails pre-fix and passes post-fix (or: passes today because todo 1 above already
      closed the specific gap — either order is fine, just don't let the test regress silently again). Repo:
      unified-api-contracts.

## Progress Log

- **context-scout 2026-08-03**: populated context_scope (4 entries).
