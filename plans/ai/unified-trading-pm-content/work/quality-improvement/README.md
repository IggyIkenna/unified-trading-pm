# Service Quality Improvement — C- to A Grade

## Overview

Systematic plan to bring all services from C- (52/100) to A grade.
4 phases, 123 tasks, estimated ~93 hours across 4 parallel agents.

## Current Baseline (Feb 2026)

- Overall grade: C- (52/100)
- 3,900 violations across 1,843 files
- 3,560 print statements to replace with logger calls
- 276 broad exception catches to replace with @handle_api_errors
- 17 files >1,500 lines needing splitting
- 90 failing tests across services

## Phases

### Phase 1: Critical Fixes (~25h, F/D repos first)
Target services: 5 repos with F or D grade
Tasks: Fix quality gate failures, add missing test_event_logging.py, remove direct cloud imports
Estimated: 25 hours, 35 tasks

### Phase 2: Quality Gates (~18h)
Target: Silent quality gate failures across all services
Tasks: Fix ruff violations, fix basedpyright errors, ensure all tests pass
Estimated: 18 hours, 28 tasks

### Phase 3: Debt Reduction (~35h)
Target: Import fallbacks, datetime.utcnow(), print() statements, broad exceptions
Tasks: Remove all deprecated patterns, enforce library usage
Estimated: 35 hours, 42 tasks

### Phase 4: Excellence (~15h)
Target: Code polish, test coverage to 50%+, documentation alignment
Tasks: Clean up remaining technical debt
Estimated: 15 hours, 18 tasks

## Key Standards to Enforce

- No `os.getenv()` for API keys — use `get_secret_client()` from UCS
- No `datetime.utcnow()` — use `datetime.now(timezone.utc)`
- No `print()` in production — use `log_event()` from UEI
- No bare `except:` — use `@handle_api_errors` from UCS
- No direct `google.cloud.*` imports — use UCS abstractions
- No `pip install` — use `uv pip install`
- All files use `from unified_config_interface import UnifiedCloudConfig`
- All files use `from unified_events_interface import setup_events, log_event`

## Execution Strategy

Use 4 parallel fast agents (different repos = zero conflict risk).
Per agent: one repo at a time from their assigned list.
Human gate at start of Phase 2 and Phase 4.

## Source Material

Original plan: `.cursor/archive/AUDIT_TO_A_GRADE_ROADMAP/` (archived)
CI/CD alignment: `.cursor/plans/code_optimizations_and_ci_cd_alignment/` (to be archived after migration)
