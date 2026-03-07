# Unit Tests All Passing Plan

**Order:** 6 (see MASTER_PRE_DEPLOYMENT_PLAN_CHAIN.md) **Reference:** TEST_FAILURE_ACTION_PLAN.md (~98 T4 failures)

---

## Per-Repo Actions

1. Run pytest tests/unit/ -v
2. Categorise failures: import, fixture, mock, assertion
3. Fix in order; no skip without reason
4. Required: test_event_logging.py, test_config.py (services)

---

## Execution Order

T0→T1→T2→T3→services. Failing deps block consumers.
