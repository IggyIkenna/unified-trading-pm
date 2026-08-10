---
doc_type: plan
title:
  "Remove the Kaiko provider scaffold fleet-wide (operator ruling 2026-08-10: Kaiko is banned outright, not
  execution-only) — 7 files across MTDS, UAC and PM, plus close the credential ask"
summary: >-
  On 2026-08-09 a session scaffolded a NEW Kaiko on-chain-analytics adapter in market-tick-data-service
  (`adapters/onchain/kaiko.py` + test + `PLANNED_VENUES` entry + a UAC `SourceCapability`) and filed
  `glassnode_kaiko_credential_ask_2026_08_09.md` asking the operator to provision `kaiko-api-key`. CLAUDE.md's
  removed-providers line already names Kaiko as "do NOT reference", but that line sits under the "Working on DeFi
  EXECUTION?" heading, so the scaffolding session could read it as execution-scoped and not applicable to MTDS
  analytics. Raised to the operator 2026-08-10, who ruled the ban is **workspace-wide, not execution-only**: the ask is
  stale, and the scaffold is deleted per the no-shims rule rather than left parked. This plan removes every live
  reference (7 files, ~70 occurrences) in one change per the entity-rename/split consumer-migration rule, and closes the
  Kaiko half of the credential ask while preserving the Glassnode half, which is unaffected.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags: [kaiko, removed-provider, adapter-removal, credential-ask, no-shims, operator-ruling]
related:
  [
    /plans/active/issues/glassnode_kaiko_credential_ask_2026_08_09.md,
    /plans/active/kaiko_provider_removal_2026_08_10_finalize.md,
    /codex/02-data/external-data-always-available-rule.md,
    /codex/04-architecture/defi-execution-overview.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
effort: medium
drift_direction: none
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/glassnode_kaiko_credential_ask_2026_08_09.md,
    /codex/02-data/entity-rename-and-split-consumer-migration-rule.md,
    /codex/04-architecture/defi-execution-overview.md,
  ]
source: >-
  Operator ruling 2026-08-10 (interactive session, slot 1), in answer to a flagged SSOT ambiguity: CLAUDE.md bans Kaiko
  but under a DeFi-EXECUTION-scoped heading, while the 2026-08-09 ask scaffolds it for MTDS analytics. Operator ruled
  the ban is outright. Consumer set enumerated live in the same session via `rg -il kaiko` across all repos excluding
  `.venv`/`build`/archives.
---

# Remove the Kaiko provider scaffold fleet-wide

## The ambiguity that caused this, and why it is worth fixing at the source

`cursor-configs/CLAUDE.md` lists Kaiko among removed providers — but inside the conditional bullet **"Working on DeFi
EXECUTION?"**. A worker scaffolding an on-chain **analytics** adapter in MTDS is not "working on DeFi execution", so the
ban did not obviously apply, and the scaffold was written in good faith. The operator ruled 2026-08-10 that the ban is
workspace-wide. Todo 4 below fixes the wording so the next worker cannot make the same correct-looking mistake.

## Enumerated consumer set (verified live 2026-08-10, `rg -ci kaiko`)

| File                                                                         | Refs | Disposition                                                     |
| ---------------------------------------------------------------------------- | ---: | --------------------------------------------------------------- |
| `market-tick-data-service/.../market_interface/adapters/onchain/kaiko.py`    |   28 | DELETE the file                                                 |
| `market-tick-data-service/tests/unit/test_kaiko_adapter.py`                  |   24 | DELETE the file                                                 |
| `market-tick-data-service/.../market_interface/adapters/onchain/__init__.py` |    4 | remove the export                                               |
| `market-tick-data-service/.../market_interface/factory.py`                   |    1 | remove `"kaiko": "analytics"` from `PLANNED_VENUES` (line ~213) |
| `unified-api-contracts/.../capability_declarations/_altdata.py`              |    8 | remove `KAIKO_BASE_URL` + the `_KAIKO` `SourceCapability`       |
| `unified-api-contracts/.../capability_declarations/__init__.py`              |    2 | remove the re-export                                            |
| `unified-trading-pm/scripts/quality-gates-base/base-service.sh`              |    3 | update the QG carve-out comment that names `kaiko.py`           |

**Not in scope**: `unified-trading-system-ui/docs/reference/*` and `public/presentations/*` mention Kaiko as a market
data vendor in narrative/marketing copy, not as a code dependency. Check each before touching — if it is describing the
vendor landscape rather than claiming we integrate Kaiko, leave it. Only fix copy that asserts an integration we do not
have.

## Todos

- [ ] [DATA] P2. **Remove Kaiko from `unified-api-contracts` first** (dependency order: UAC is T2, MTDS depends on it).
      Delete `KAIKO_BASE_URL` and the `_KAIKO` `SourceCapability` from
      `unified_api_contracts/registry/capability_declarations/_altdata.py` and its re-export from that package's
      `__init__.py`. **Done when**: `rg -ci kaiko` returns 0 across `unified-api-contracts/` (excluding `.venv`), and
      `bash scripts/quality-gates.sh` is green in that repo. Ship via quickmerge.
- [ ] [DATA] P2. **Remove the MTDS adapter and its wiring.** Delete
      `market_tick_data_service/market_interface/adapters/onchain/kaiko.py` and `tests/unit/test_kaiko_adapter.py`
      outright (no shim, no deprecation stub — CLAUDE.md's delete-deprecated-code rule), remove the export from
      `adapters/onchain/__init__.py`, and remove the `"kaiko": "analytics"` entry from `market_interface/factory.py`'s
      `PLANNED_VENUES`. Kaiko was parked in `PLANNED_VENUES` and never wired into `get_adapter()`, so no runtime
      resolution path changes — state that explicitly in the commit. **Done when**: `rg -ci kaiko` returns 0 across
      `market-tick-data-service/` (excluding `.venv`), and `bash scripts/quality-gates.sh` is green. Ship via
      quickmerge.
- [ ] [DATA] P3. **Update the PM QG carve-out comment.** `scripts/quality-gates-base/base-service.sh` (~line 3877)
      documents a 2026-08-09 carve-out naming `onchain/{glassnode,helius_solana,kaiko}.py`. Drop `kaiko` from that list
      and from the surrounding prose so the comment does not describe a file that no longer exists. Do NOT weaken the
      carve-out for the two remaining adapters. **Done when**: the comment names only the surviving adapters and PM QG
      is green. `scripts/**` reaches main via the D16 carve-out, not quickmerge.
- [ ] [DOCS] P2. **Fix the CLAUDE.md ambiguity that caused this.** The removed-providers list lives under the "Working
      on DeFi EXECUTION?" conditional bullet, which made a workspace-wide ban look execution-scoped. Move or restate it
      so the ban reads as fleet-wide regardless of the touching subsystem, honouring the file's ≤40 KB budget
      (`check_agent_rules_size_cap.py`) — condense elsewhere rather than growing the file, and never raise the cap.
      **Done when**: a worker reading only the always-on section would know not to scaffold a Kaiko adapter, and the
      size cap still passes.

## Codex SSOTs

- `/codex/02-data/entity-rename-and-split-consumer-migration-rule.md` — why every consumer migrates in ONE change
- `/codex/04-architecture/defi-execution-overview.md` — the removed-providers list this ruling widens
- `/codex/02-data/external-data-always-available-rule.md` — why the Glassnode half stays a live credential ask

## Progress Log

- **2026-08-10** — Authored after flagging the CLAUDE.md scope ambiguity to the operator, who ruled Kaiko banned
  outright. Consumer set enumerated live (7 files, ~70 refs). Confirmed Kaiko sits in `PLANNED_VENUES` only and is not
  reachable through `get_adapter()`, so removal carries no runtime behaviour change.
