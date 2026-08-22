---
doc_type: issue
title: execution-service quality-gates.sh RED — UniswapConnector.mint_position() over the 50-line method cap
summary: >-
  execution-service's quality-gates.sh hard-fails repo-wide (unrelated to any
  in-flight task's own diff) because UniswapConnector.mint_position()
  (uniswap.py) is 61 lines against the 50-line method cap. A first-pass fix
  (extract the V4 branch into its own method) shrinks it to 53L -- still over
  -- and pushes uniswap.py itself from ~900 to 911 lines, past the 900-line
  file-size cap too. This needs a real trim, not a mechanical one-line split.
status: superseded
superseded_by: execution_service_qg_red_mint_position_method_size_2026_08_22
nature: issue
asset_group: [cross-cutting]
stage: [execution]
repos: [execution-service]
scope: [engineer]
tags: [quality-gates, method-size-cap, file-size-cap, uniswap, repo-blocker]
related: [/plans/active/cross_cutting_consolidated_closeout_2026_07_25.md]
created: "2026-08-22"
parent_epic: system_readiness_master
assigned_vm: planning
priority: P2
source: [slot-7, w15_execution_service_venue_adaptor_security_audit_2026_08_20]
author: slot-7
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
context_scope:
  - execution-service/execution_service/defi_execution/protocols/uniswap.py
---

# execution-service quality-gates.sh RED — UniswapConnector.mint_position() over the 50-line method cap

## What I found

While shipping an unrelated fix (Orca/Raydium liquidity account-derivation,
`w15_execution_service_venue_adaptor_security_audit_2026_08_20.md` item
"Resolve full Orca Whirlpool / Raydium CLMM account derivation..."), a full
`bash scripts/quality-gates.sh` run on execution-service failed the
hard (non-ratcheted) function/class/method-size gate:

```
❌ Function/class/method size exceeded:
  ./execution_service/defi_execution/protocols/uniswap.py:533:UniswapConnector.mint_position(): 61L (method cap 50)
```

Verified pre-existing, not caused by my own diff: `git stash` (removing my
Orca/Raydium/solana_base.py changes entirely) reproduces the identical
failure on an otherwise-clean tree at `origin/live-defi-rollout` HEAD. Last
commit touching `uniswap.py` is `ca9eda1b` ("feat: Uniswap V2 and V4
execution wiring alongside the existing V3 path").

Attempted a one-line fix (extract the `version == "V4"` branch of
`mint_position()` into a new `_mint_position_v4()` helper, same pattern used
elsewhere in this codebase for method-size compliance): this shrinks
`mint_position()` to 53L -- **still over the 50L cap** -- because the
docstring plus the remaining V3-dispatch logic alone exceeds it, and the new
method's own signature/docstring lines push `uniswap.py` from its current
length to 911L, past the file's own 900-line cap
(`❌ Files exceed 900 lines: ./execution_service/defi_execution/protocols/uniswap.py: 911 L`).
Reverted that attempt (`git checkout -- uniswap.py`) rather than ship an
incomplete fix that trades one hard-gate failure for two.

## Why it matters

Both gates are HARD (not baseline/ratchet-tracked), so this blocks
`quality-gates.sh` for **every** worker touching execution-service, not just
this task -- per RULES.md § 2 ("commit only from a `quality-gates.sh`-green
tree") and § 4b ("BLOCKED ON THE REPO, not your task"), any unrelated staged
work in this repo cannot ship until this clears.

## Recommended decision

`mint_position()` needs a real trim, not a mechanical split: either shorten
its docstring further, or extract the V3-dispatch tail (the
`preflight_validate_operation`/`fee_tier` validation + the final
`self._mint_position_v3(...)` call construction) into a second helper
alongside the V4 one, so BOTH new methods are small and the orchestrating
`mint_position()` itself drops well under 50L without growing the file past
900L net (may also require trimming a few otherwise-unrelated lines
elsewhere in the file to stay under the file cap, since two new `def`/
docstring blocks add lines a pure extraction can't avoid).

## Todos

- [ ] [BACKEND] P2. Trim `UniswapConnector.mint_position()` (uniswap.py) under
      the 50-line method cap AND keep `uniswap.py` under the 900-line file
      cap -- verify with `bash scripts/quality-gates.sh` (both the
      function-size and file-size hard gates must pass), not just a visual
      line count. Repo: execution-service.

## Progress Log

- **2026-08-22 (slot-7)**: Filed after discovering + verifying (stash-based)
  this pre-existing repo-wide QG-red condition while shipping an unrelated
  Orca/Raydium fix. Declaring a `qg_red` repo-blocker for execution-service
  per RULES.md § 4b rather than attempting a second fix pass under this
  task's own scope.
- **2026-08-22 (slot-7, dedup pass)**: `POST /api/repo-blockers` came back
  `created: false` -- slot-24 had already filed the identical finding
  (same method, same both-caps interaction) minutes earlier as
  `execution_service_qg_red_mint_position_method_size_2026_08_22.md`
  (`unified-trading-pm@579b295113`), with an open blocker `RB-f94cb3d7` I've
  now joined as a waiter. Marking this doc `superseded` rather than deleting
  it -- the two findings are independently-derived confirmation of the same
  root cause, not additional information the canonical doc lacks.
