---
doc_type: issue
title:
  "Capability-preflight `except Exception: pass` silent-swallow pattern — cross-cutting audit resolved, confirmed live
  at execution-service defi_execution/protocols/base.py"
summary: >-
  Follow-up to sports_adapter_dead_code_fallback_duplicate_audit_2026_08_01.md's operator-ruling todo -012: investigated
  the 3 named non-sports call sites (`instruction_router.py`, `defi_execution/protocols/base.py`, MTDS `factory.py`) for
  the same zero-logging `except Exception: pass  # Graceful degradation` capability-preflight swallow found at the 7
  sports_execution sites (Finding 12). A full workspace grep for every `validate_operation(...)` call site (30 files
  across execution-service, instruments-service, market-tick-data-service, unified-api-contracts) confirms the bare
  zero-logging swallow is present at exactly ONE of the 3 named sites —
  `execution-service/execution_service/defi_execution/protocols/base.py::preflight_validate_operation` — which gates 60+
  real-money DeFi operation call sites (supply/withdraw/borrow/repay/flash_loan/place_order/cancel_order/exchange/
  mint_position/burn_position across 21 protocol connectors: aave, morpho, kelpdao, yearn, pendle, solblaze, karak,
  uniswap, puffer, hyperliquid, etherfi, rocket_pool, jito_restaking, convex, aster, eigenlayer, beefy, idle, symbiotic,
  renzo, lido). `instruction_router.py` and MTDS `factory.py` were checked and found COMPLIANT — both already emit real
  observability (`classify_and_emit_error(...)` and `_logger.debug(...)` respectively) in their equivalent broad-except
  branches, so they are NOT instances of the Finding-12 bug class. Every other `validate_operation()` call site
  workspace-wide (trade_execution/factory.py, instruments-service router.py/factory.py, etc.) catches the specific
  `CapabilityResolutionError`/`UnsupportedOperationError` and logs via `_logger.debug` — also compliant. This is
  therefore NOT a workspace-wide anti-pattern; it is one additional confirmed defect, scoped and ready to fix the same
  way the sports_execution sites were fixed (execution-service@7bba972a).
status: resolved
nature: issue
asset_group: [defi]
stage: [execution]
repos: [execution-service, unified-trading-pm]
scope: [engineer]
tags:
  [defi, capability-preflight, silent-fallback, cross-cutting-audit, adapter-dead-code-and-fallback-ban, honest-absence]
related:
  [
    /codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md,
    /plans/archive/issues/sports_adapter_dead_code_fallback_duplicate_audit_2026_08_01.md,
  ]
created: 2026-08-03
last_updated: 2026-08-03
priority: P1
parent_epic: defi_master
source:
  "Operator ruling on sports_adapter_dead_code_fallback_duplicate_audit_2026_08_01.md todo -012 (worked by slot 13,
  2026-08-03) — the todo asked to investigate 3 named non-sports call sites and, if the pattern was confirmed present at
  any of them, file this follow-up."
assigned_vm: planning
resolved_by: execution-service@b68bc236 (fix) + slot-3 2026-08-03 (both docstring correction and logging fix shipped)
locked_by:
execution_scope: orchestrator-agent
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: backend_engineer
drift_direction: advance-code
locked_since:
depends_on: []
supersedes:
superseded_by:
context_scope:
  [
    /codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md,
    /plans/archive/issues/sports_adapter_dead_code_fallback_duplicate_audit_2026_08_01.md,
  ]
---

# Capability-preflight silent-swallow pattern — cross-cutting audit resolved

## What I found

The parent audit's todo -012 flagged that the same textual `except Exception: pass  # Graceful degradation` pattern
found at 7 sports_execution call sites (Finding 12, already fixed at `execution-service@7bba972a` — logging added, no
control-flow change) was also seen during that audit at 3 other, out-of-scope locations: `instruction_router.py`,
`defi_execution/protocols/base.py`, and market-tick-data-service `factory.py`. This task investigated all 3, plus ran a
full workspace grep for every `validate_operation(` call site to check whether this is genuinely a workspace-wide
convention.

**Confirmed present (the actual bug — bare `except Exception: pass`, zero logging):**

- `execution-service/execution_service/defi_execution/protocols/base.py:136-140` (`preflight_validate_operation`):
  ```python
  try:
      validate_operation(source_name, operation, env)
  except UnsupportedOperationError:
      raise
  except Exception:
      # Graceful degradation — registry not bootstrapped, source not registered, etc.
      pass
  ```
  The function's OWN docstring (lines 120-122) claims "All other errors (source not registered, bootstrap not run, etc.)
  are logged and swallowed" — this is FALSE; the actual implementation has zero logging call, only `pass`. This is a
  single shared function called from **60+ sites across 21 DeFi protocol connectors** immediately before real on-chain
  operations: `aave.py` (supply/withdraw/borrow/repay/flash_loan), `uniswap.py` (exchange/mint_position/burn_position),
  `hyperliquid.py`/`aster.py` (place_order/cancel_order), and 17 more supply-only connectors (morpho, kelpdao, yearn,
  pendle, solblaze, karak, puffer, etherfi, rocket_pool, jito_restaking, convex, eigenlayer, beefy, idle, symbiotic,
  renzo, lido). A `CapabilityResolutionError`/ `UnsupportedModeError`/`UnsupportedEnvironmentError` firing here (e.g.
  the capability registry failing to bootstrap) silently lets a DeFi operation proceed with zero log signal — same bug
  class as Finding 12, arguably higher-stakes given real on-chain capital movement.

**Checked and found COMPLIANT (NOT instances of the bug):**

- `execution-service/execution_service/engine/routing/instruction_router.py:229-234` (`_route_compose_preflight`'s outer
  `except Exception as exc:`) — calls
  `classify_and_emit_error(exc, service_name="execution-service", operation="compose_validation")` before falling
  through. This IS real observability (error classification + emission), not a silent `pass`. Compliant.
- `market-tick-data-service/market_tick_data_service/market_interface/factory.py:130-135` — catches
  `except Exception as exc:` and calls `_logger.debug("validate_operation probe failed (non-fatal): %s", exc)` before
  falling through. Has logging (debug level), not a bare `pass`. Compliant.
- Every other `validate_operation(` call site workspace-wide (grepped across execution-service, instruments-service,
  market-tick-data-service, unified-api-contracts — `trade_execution/factory.py`, instruments-service
  `reference_data/router.py`, `reference_data/factory.py`) catches the SPECIFIC `CapabilityResolutionError` (not a bare
  `Exception`) and logs via `_logger.debug(...)`. Compliant.

**Conclusion**: this is NOT a workspace-wide anti-pattern. The `except Exception: pass` / zero-logging swallow is
confined to two now-known locations: the 7 sports_execution sites (already fixed) and this one DeFi function. No further
workspace-wide sweep is warranted — the grep above already covered every `validate_operation()` caller in the cloned
workspace.

## Why it matters

`defi_execution/protocols/base.py::preflight_validate_operation` gates real supply/withdraw/borrow/repay/flash_loan/
place_order/cancel_order/exchange/mint_position/burn_position calls across every DeFi protocol connector in the repo. A
capability-registry failure (e.g. bootstrap not run, a misconfigured source mapping) should be observable — currently it
is invisible, and the function's docstring actively misrepresents the behavior as "logged", which could mislead a future
reader auditing this exact code path into believing it's already compliant.

## Recommended decision

Fix by adding observability, matching the exact pattern already used for the 7 sports_execution sites
(`execution-service@7bba972a` — `logger.warning` naming `type(exc).__name__` + the exception message, no control-flow
change) and correcting the docstring to match reality.

- [x] ✅ [BACKEND] P1. Fix
      `execution-service/execution_service/defi_execution/protocols/base.py::preflight_validate_operation` (lines
      136-140): add a `logger.warning`/`log_event` call naming `type(exc).__name__` + the exception message in the
      `except Exception:` branch before `pass`, so a `CapabilityResolutionError`/`UnsupportedModeError`/
      `UnsupportedEnvironmentError` firing in production ahead of a real DeFi operation is observable instead of silent
      — matching the fix already applied to the 7 sports_execution call sites (execution-service@7bba972a). Also correct
      the function's docstring (lines 120-122), which currently claims these errors are "logged and swallowed" when the
      actual code has no logging call — update it to describe the real (post-fix) behavior. No control-flow change
      (still swallow-and-continue for non-`UnsupportedOperationError` cases). (repo: execution-service) —
      execution-service@b68bc236

## Progress Log

**2026-08-03, slot 13**: Investigated per operator ruling on
`sports_adapter_dead_code_fallback_duplicate_audit_2026_08_01.md` todo -012. Grepped the exact `# Graceful degradation`
comment marker workspace-wide (found only at the 3 already-named sites, no others) and independently grepped every
non-test `validate_operation(` call site (30 files) to check each one's except-branch by hand. Result: one confirmed
defect (`defi_execution/protocols/base.py`), two compliant sites correctly ruled out (`instruction_router.py`, MTDS
`factory.py`), and no further occurrences anywhere else in the cloned workspace.

**2026-08-03, slot 3**: Fixed. Added `logger.warning` naming `type(exc).__name__` + `source_name`/`operation` in the
`except Exception:` branch of `preflight_validate_operation` (matching execution-service@7bba972a's pattern) and
corrected the docstring. QG green, shipped execution-service@b68bc236, verified on origin. All todos in this issue doc
are now done and unlocked — archiving next.
