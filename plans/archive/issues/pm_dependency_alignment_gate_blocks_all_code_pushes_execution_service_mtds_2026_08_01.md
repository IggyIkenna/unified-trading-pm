---
doc_type: issue
title:
  PM STAGE 1.5 dependency-alignment gate blocks EVERY code-carrying quickmerge to unified-trading-pm
  (execution-service/market-tick-data-service tier-exception mismatch)
summary: >-
  quickmerge.sh's STAGE 1.5 "Dependency Alignment (PM)" check (scripts/manifest/check-dependency-alignment.py, strict
  zero-tolerance, no baseline/ratchet) has returned "aligned": false since execution-service@050ed797 (2026-08-01
  08:28:17Z, slot 6) landed a companion workspace-manifest.json edit declaring `market-tick-data-service` as an
  execution-service dependency. execution-service's pyproject.toml never declares it as a real `[tool.uv.sources]` or
  `dependencies=[...]` entry (only as a basedpyright `extraPaths` type-check hint) — deliberately, because doing so
  would trip fix-internal-dependency-alignment.py's TIER_VIOLATION check (execution-service importing
  market-tick-data-service violates the no-service<->service-deps tier DAG). The import itself
  (`market_tick_data_service.reader` in execution_service/algo_library/mtds_book_provider.py) is a REAL, deliberately
  tracked tech-debt exception already recorded in UAC's `service_contract_map.py` `forbidden_exceptions` for
  execution-service (id `execution_service_mtds_reader_dep`, "tracked in deprecation_ledger.yaml", pending a
  CanonicalParquetReader-to-UTL promotion). check-dependency-alignment.py has NO knowledge of UAC's forbidden_exceptions
  allowlist — it only compares workspace-manifest.json's declared `dependencies` against pyproject.toml's derived
  internal deps, with an existing PER_REPO_EXTERNAL_EXCEPTIONS mechanism (dependency-exceptions.yaml) for EXTERNAL
  package-version divergences only — there is no equivalent allowlist for INTERNAL dependency mismatches. Result: any
  commit to unified-trading-pm that isn't a plans-only docs(plans) commit (which uses the direct-push carve-out,
  bypassing quickmerge.sh's gate chain entirely) is currently BLOCKED at STAGE 1.5, fleet-wide, until this is resolved.
  Discovered blocking an unrelated P3 task (cloud_build_unified_api_contracts_publish_ordering_race-004); confirmed
  pre-existing via a clean-HEAD stash test and by tracing the exact commit + comment that introduced the mismatch.
status: resolved
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm, execution-service, unified-api-contracts]
scope: [engineer, admin]
tags: [ci-cd, dependency-alignment, quickmerge, tier-dag, execution-service, market-tick-data-service, blocking]
related:
  [
    /plans/archive/issues/cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md,
    /plans/archive/issues/dependency_alignment_red_multi_repo_ceiling_drift_2026_07_13.md,
  ]
created: 2026-08-01
last_updated: 2026-08-03
priority: P1
parent_epic: infrastructure_master
source:
  "discovered while shipping cloud_build_unified_api_contracts_publish_ordering_race-004, slot 8, cicd craft dispatch,
  2026-08-01"
execution_scope: orchestrator-agent
assigned_role: cicd
drift_direction: advance-code
context_scope: [/codex/08-workflows/ci-cd-flow.md, scripts/manifest/check-dependency-alignment.py, scripts/manifest/dependency-exceptions.yaml, unified-api-contracts/unified_api_contracts/registry/service_contract_map.py]
depends_on: []
assigned_vm: planning
resolved_by:
  pm_dependency_alignment_gate_blocks_all_code_pushes_execution_service_mtds-001--ruling (slot 9, 2026-08-03
  investigation)
locked_by:
locked_since:
---

> **🟢 ARCHIVED 2026-08-03** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. Moved by a `cicd` escalation (agt-5c37f6) triaging the `check_archive_candidates` /
> `check_terminal_status_archived` hard gate failures. No content was rewritten.

# PM dependency-alignment gate blocks every code-carrying quickmerge (execution-service/MTDS tier exception)

## What I found

- `bash scripts/quickmerge.sh ... --agent --files '<any code files>'` for `unified-trading-pm` fails at STAGE 1.5 every
  time, unconditionally, with:
  ```
  [unified-trading-pm] ❌ Dependency alignment FAILED
  ```
  `python3 scripts/manifest/check-dependency-alignment.py --json` returns:
  ```json
  {"aligned": false, "issues": [{"repo": "execution-service", "type": "internal_in_manifest_not_pyproject",
    "dep": "market-tick-data-service"}], "count": 1, ...}
  ```
- Root cause: `execution-service@050ed797` (2026-08-01T08:28:17Z, slot 6,
  `chore(execution-service): remove 8 dead basedpyright extraPaths, resolve MTDS drift`) shipped a "companion PM commit"
  adding `market-tick-data-service` to `workspace-manifest.json`'s `repositories.execution-service.dependencies`.
  execution-service's own `pyproject.toml` does NOT declare `market-tick-data-service` as a real dependency anywhere —
  no `[tool.uv.sources.market-tick-data-service]`, no entry in the `dependencies = [...]` array. It appears ONLY in
  `[[tool.basedpyright.executionEnvironments]] extraPaths` (a static-type-check import-resolution hint, not an
  installed/resolved package).
- This is deliberate: `unified-api-contracts/unified_api_contracts/registry/service_contract_map.py` (execution-service
  contract, `forbidden_exceptions`) explicitly allows `market_tick_data_service.reader` as a TRACKED tech-debt exception
  (id `execution_service_mtds_reader_dep`) to the general `forbidden_imports={"market_tick_data_service", ...}` rule —
  pending a `CanonicalParquetReader`-to-UTL promotion or a UAC-contract read-path flip. The execution-service commit
  message itself says the workspace-manifest.json addition was made BECAUSE the import is real, while simultaneously NOT
  adding it to `dependencies=[...]` because that would trip `fix-internal-dependency-alignment.py`'s separate
  `TIER_VIOLATION` check.
- `check-dependency-alignment.py` (the actual STAGE 1.5 gate script) has **no knowledge of UAC's `forbidden_exceptions`
  allowlist at all** — its only exception mechanism, `PER_REPO_EXTERNAL_EXCEPTIONS` /
  `scripts/manifest/dependency-exceptions.yaml`, covers EXTERNAL package-version divergences only (schema requires a
  `spec:` field — an exact alternate version constraint string — which has no meaningful equivalent for an
  internal-dependency presence/absence mismatch). There is no `PER_REPO_INTERNAL_EXCEPTIONS` equivalent.
- Confirmed pre-existing, not caused by my own diff: reproduced identically via `git stash push --include-untracked` on
  a clean `HEAD` before any of my changes were staged, and again after a fresh `git pull --ff-only` (the mismatch
  persists across intervening unrelated commits). Also confirmed it doesn't affect `docs(plans):`-only commits — those
  ship via the sanctioned direct-push carve-out (CLAUDE.md § Git discipline, carve-out 2), bypassing `quickmerge.sh`'s
  full gate chain — which is why several plan-flip commits landed successfully today despite this break, while the first
  CODE-carrying quickmerge (mine) hit it.

## Why it matters

STAGE 1.5 has **no baseline/ratchet** (`"aligned": true` or hard `exit 1`) and is unconditional for every
`unified-trading-pm` quickmerge, regardless of which files are staged — so this blocks **every code change to PM**
fleet-wide (scripts, quality gates, propagation tooling, anything that isn't a pure plan-checkbox flip) until resolved.
Given the cadence of AO-dispatched PM work, this is a standing, silent throughput blocker, not a one-off.

## Recommended decision

Two candidate fixes, not mutually exclusive:

**(A) Remove the `market-tick-data-service` entry from `workspace-manifest.json`'s
`repositories.execution-service.dependencies`.** Lowest blast radius — doesn't touch execution-service's code, doesn't
touch the shared checker's logic, and workspace-manifest.json's `dependencies` list appears to model actual
installed/resolved uv packages (which this import genuinely is not — it's a lazy runtime import backed only by a
basedpyright typecheck path). The real "this exception is sanctioned" bookkeeping already lives in UAC's
`service_contract_map.py forbidden_exceptions` (id `execution_service_mtds_reader_dep`) — that already IS the SSOT for
this tracked tech-debt item; the manifest entry looks like it duplicated that intent into the wrong file. **Risk**: I
have not verified every consumer of `workspace-manifest.json`'s per-repo `dependencies` list (build ordering / SIT /
Cloud Build dep graph) — an operator or the execution-service@050ed797 author should confirm nothing else relies on this
specific entry being present before it's removed.

**(B) Extend `check-dependency-alignment.py` with an internal-dependency exception mechanism** mirroring the existing
`PER_REPO_EXTERNAL_EXCEPTIONS` / `dependency-exceptions.yaml` pattern (new `kind: internal` entries, or a parallel
file), citing `execution_service_mtds_reader_dep` as the `ssot`. Higher effort (new schema + loader + wiring + tests),
but keeps the manifest entry as an intentional cross-reference and generalizes the fix for any FUTURE
`forbidden_exceptions`-class tracked violation that needs the same manifest-vs-pyproject carve-out (this is not
necessarily the last one).

**My recommendation**: (A) now (fast, minimal, reversible, unblocks the fleet immediately) — (B) as a properly-scoped
follow-up if a similar case recurs (only one instance today; building the generalized mechanism for N=1 is arguably
premature).

## Todos

- [x] ✅ [OPERATOR] P1. Decide between option (A) (revert the `workspace-manifest.json` execution-service/
      market-tick-data-service dependency entry) and option (B) (build a `check-dependency-alignment.py`
      internal-dependency exception allowlist mirroring `PER_REPO_EXTERNAL_EXCEPTIONS`) — or confirm (A) per the
      recommendation above and let it ship as a follow-up commit. This blocks EVERY code-carrying `unified-trading-pm`
      quickmerge until resolved. (repo: unified-trading-pm, execution-service) — **DONE 2026-08-01, operator confirmed
      option (A) live (slot 16, while shipping an unrelated task blocked by this gate).** Verified before applying: the
      real dep-order/publish consumers (`assert_deps_published_to_ar.py`, `check-import-deps.py`) derive from each
      repo's own `pyproject.toml`, not this manifest field, so removing the entry has no build/promotion-order effect.
      Shipped `unified-trading-pm@4871d79fe`; `check-dependency-alignment.py --json` now returns `"aligned": true`.
      Repo-blocker RB-be17edbd resolved.

## Progress Log

- **2026-08-01, slot 16**: Resolved the `[OPERATOR]` decision live — operator authorized proceeding with option (A)
  while this gate was blocking an unrelated shippable task (`autostash_pop_restores_foreign_wip_into_the_index-001`).
  Removed the `market-tick-data-service` entry from `workspace-manifest.json`'s
  `repositories.execution-service.dependencies` (`unified-trading-pm@4871d79fe`). Confirmed
  `check-dependency-alignment.py --json` returns `"aligned": true` post-fix. `status` left `open` pending an operator or
  `execution-service@050ed797`-author sanity check that nothing else silently relied on that manifest entry (the
  recommendation's own stated risk) — flip to `resolved` once that's confirmed, or if a downstream break surfaces,
  reopen with the specifics.
- **context-scout 2026-08-03**: populated/refreshed context_scope (4 entries).
- **2026-08-03, slot 9**: Investigated directly per operator ruling (investigate rather than ask around). Findings: (1)
  `execution-service/pyproject.toml` still carries ONLY the intentional `basedpyright extraPaths` hint
  (`"../market-tick-data-service"`, line 117) — no `[tool.uv.sources]` or `dependencies=[...]` entry exists or was ever
  reintroduced; (2) `workspace-manifest.json`'s `repositories.execution-service.dependencies` confirmed to still NOT
  contain `market-tick-data-service`; (3) `check-dependency-alignment.py --json` currently returns `"aligned": true`,
  `"count": 0`; (4) reviewed the 3 `quality-gates-v2` CI failures on `unified-trading-pm`/`live-defi-rollout` since the
  fix landed (runs on shas `2bfa2022bd`, `0db25e69be`, `b3c48c7d90`) — none mention dependency-alignment or
  `internal_in_manifest_not_pyproject`; their actual causes are unrelated (NA-corpus ratchet, archive-candidate ratchet,
  VERSION_SPLIT warnings); (5) no `qg_red`/dependency-alignment repo-blocker has been filed for `unified-trading-pm`
  since the fix (checked `/api/repo-blockers` + orchestrator activity log); (6) 34+ real code-carrying quickmerge
  commits landed to `unified-trading-pm/scripts/` since the fix (2026-08-01T15:00 onward) — direct proof STAGE 1.5 has
  not blocked ordinary PM work. No evidence of reliance on the removed manifest entry and no downstream break surfaced.
  Flipping `status` to `resolved`.

## Todos (follow-up)

- [x] ✅ P2. Confirm that nothing silently relied on the removed `workspace-manifest.json`
      execution-service/market-tick-data-service dependency entry. Flip this doc to `status: resolved` once confirmed,
      or reopen with specifics if a downstream break surfaces. — **DONE 2026-08-03, slot 9, via direct investigation**
      (operator ruling: investigate rather than ask around). No evidence of reliance found — see Progress Log entry
      below. `status` flipped to `resolved`.
