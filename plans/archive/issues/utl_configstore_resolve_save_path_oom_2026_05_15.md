---
doc_type: issue
title: UTL OOM root-cause + workspace audit + UTL architecture review (2026-05-15)
summary:
status: ROOT-CAUSE FIXED ✅ (utl@93ff771); follow-ups documented for triage
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    alerting-service,
    batch-live-reconciliation-service,
    client-reporting-api,
    deployment-api,
    instruments-service,
    market-tick-data-service,
  ]
scope: [engineer, admin]
tags: []
related:
  [
    /codex/06-coding-standards/quality-gates-memory-governance.md (today's MEM_WRAP cgroup cap),
    plans/active/issues/utl_qg_preexisting_failures_2026_05_14.md (slot 6's ongoing UTL QG cleanup),
  ]
created: 2026-05-15
author: harsh-claude (forensic audit + reproduction + workspace sweep)
resolved: 2026-05-15
resolution:
  ROOT-CAUSE FIXED — utl@93ff771 fixes the 75GB OOM at persistence.py:388. P1-P3 follow-ups documented for triage.
severity: P0 fixed (root cause); P1-P3 follow-ups documented
locked_by: live-defi-rollout
locked_since: 2026-05-15
sources:
  [
    kernel dmesg (OOM,
    controlled cgroup-capped reproduction confirming culprit + standalone repro at /tmp/oom_repro_minimal.py,
    workspace-wide pattern scan (Pattern A unbounded-while-on-mock; Pattern B sys.modules MagicMock pollution; Pattern C
    session-autouse fixtures),
    UTL full QG memory profiling (5.29 GB peak combined; pytest 636 MB / basedpyright 1.6 GB isolated),
  ]
---

# UTL OOM forensic + workspace audit + architecture review

This doc is the comprehensive landing page for the 2026-05-15 OOM incident. It covers:

1. **Section 1** — The bug + the fix (already shipped at `utl@93ff771`)
2. **Section 2** — Sibling risks across the workspace (other repos with the same patterns)
3. **Section 3** — UTL architecture smells discovered during the audit (separate from the OOM)
4. **Section 4** — Quality-gates.sh local-vs-CI mode (verified correct; usage clarification for future agents)
5. **Section 5** — Recommended follow-up actions with priority tiers

---

## Section 1 — The OOM bug + fix (SHIPPED)

### TL;DR

`ConfigStore._resolve_save_path` had `while storage.blob_exists(...)` with no upper bound. When `storage` is a
`MagicMock` (which it was — see Section 1.4), `blob_exists` returns a truthy `MagicMock` and the loop runs forever,
accumulating ~4.44 KB/iteration into `MagicMock.call_args_list` at ~57k iter/sec → **75 GB RSS in ~5 minutes** → kernel
OOM killed all parallel agents.

### 1.1 Forensic chain

| OOM | Wall-clock IST | Killed PID         | Anon RSS | Source          |
| --- | -------------- | ------------------ | -------- | --------------- |
| #1  | 16:41          | 2554667 (`python`) | 79.6 GB  | KDE Konsole tab |
| #2  | 18:51          | 3210963 (`python`) | 74.1 GB  | KDE Konsole tab |

Both: single Python process, `oom_score_adj=100`, ~2h apart, identical mechanism.

### 1.2 Reproduction (cgroup-capped, sequence of bisections)

| Scope                                                                                                                                                                     | Peak RSS               | Time  | Verdict                          |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------- | ----- | -------------------------------- |
| Slot 6's exact 7-dir pytest invocation                                                                                                                                    | 35.34 GB (hit cap)     | 2m34s | reproduced both real OOMs        |
| Bisect → `tests/config_interface/integration/test_library_deps_integration.py::TestUnifiedCloudInterfaceIntegration::test_config_store_save_load_with_real_local_storage` | 3.04 GB (hit 3 GB cap) | ~10s  | **culprit**                      |
| Standalone repro `/tmp/oom_repro_minimal.py` (just the loop, no pytest)                                                                                                   | 2.17 GB                | 9s    | mechanism: 4.44 KB/iter, 57k/sec |

Math check: 75 GB ÷ 4.44 KB/call = ~17M calls ÷ 57k/sec = **~5 min** → matches both real OOMs.

### 1.3 Code root cause

[`unified-trading-library/unified_trading_library/config_interface/persistence.py:376-393`](../../unified-trading-library/unified_trading_library/config_interface/persistence.py#L376)
(pre-fix):

```python
def _resolve_save_path(self, storage: StorageClient, timestamp: str) -> str:
    sequence = 0
    path = self._config_path(timestamp)
    while storage.blob_exists(self.bucket_name, path):    # ← infinite on truthy mock
        sequence += 1
        path = self._config_path(timestamp, sequence)
    return path
```

### 1.4 Why MagicMock made `blob_exists` truthy

[`tests/config_interface/conftest.py:18-50`](../../unified-trading-library/tests/config_interface/conftest.py#L18)
installs `sys.modules["unified_trading_library.cloud_interface"] = MagicMock()` as a `scope="session", autouse=True`
fixture. A bare `MagicMock` returns a `MagicMock` from any attribute access or call. Every `MagicMock` is truthy by
default (`bool(MagicMock())` → `True`). So `storage.blob_exists(bucket, path)` returns a truthy `MagicMock`
indefinitely.

### 1.5 Fix shipped at `unified-trading-library@93ff771`

Three changes:

1. **[persistence.py](../../unified-trading-library/unified_trading_library/config_interface/persistence.py#L376)** —
   bounded loop with `_MAX_RESOLVE_SEQUENCE = 10_000` and clean `ConfigStoreError` on overflow:

   ```python
   while storage.blob_exists(self.bucket_name, path):
       sequence += 1
       if sequence > _MAX_RESOLVE_SEQUENCE:
           raise ConfigStoreError(
               f"_resolve_save_path exceeded {_MAX_RESOLVE_SEQUENCE} attempts for "
               f"{self.bucket_name}/{path} — storage.blob_exists may be misconfigured ..."
           )
       path = self._config_path(timestamp, sequence)
   ```

2. **[conftest.py](../../unified-trading-library/tests/config_interface/conftest.py#L43)** — make the mock terminate any
   caller's loop:

   ```python
   cloud_interface_mock.get_storage_client.return_value.blob_exists.return_value = False
   ```

3. **[tests/config_interface/unit/test_resolve_save_path_bounded.py](../../unified-trading-library/tests/config_interface/unit/test_resolve_save_path_bounded.py)**
   — 4 regression tests: bounded-error, fast-termination (<5s), happy path, real collision.

### 1.6 Verification

| Check                                                 | Before fix      | After fix                                                                               |
| ----------------------------------------------------- | --------------- | --------------------------------------------------------------------------------------- |
| Regression tests                                      | n/a             | 4/4 pass in 0.73s ✅                                                                    |
| Previously-OOMing integration test                    | 35+ GB / killed | 0.51s clean fail (`ConfigStoreError: No active config` — separate test design issue) ✅ |
| `tests/config_interface/` peak RSS                    | 35+ GB → killed | 633 MB ✅                                                                               |
| `ruff format --check` + `ruff check` on touched files | n/a             | clean ✅                                                                                |
| New test failures introduced                          | n/a             | 0 (17 pre-existing failures unchanged) ✅                                               |

---

## Section 2 — Sibling risks workspace-wide

After the fix shipped, swept the workspace for the same patterns. Findings:

### 2.1 Pattern A — `while x.method():` where `x` could be a mock

Workspace-wide grep for `while [a-z_]+\.(blob_exists|exists|has_|contains|next|peek|fetch|poll|read|wait_for_)`:

| Location                                                                      | Risk                                                                                                                                                                                                          | Status                                                                        |
| ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `unified-trading-library/.../persistence.py:388`                              | OOM (was 75 GB)                                                                                                                                                                                               | ✅ **FIXED** in `93ff771`                                                     |
| `strategy-service/.../domain_event_logger.py:361` `while f.read(1) != b"\n":` | "Tail file" pattern reading byte-by-byte backwards. Bounded by file size (seek goes to byte 0 → `OSError` → caught). NOT OOM-class but slow on large files. Not mock-vulnerable (file handle, not interface). | 🟡 P3 smell — replace with `tail -1` equivalent or read fixed buffer from end |

**Net: only the UTL bug was OOM-class. No other workspace `while x.method():` patterns are mock-vulnerable.**

### 2.2 Pattern B — `sys.modules[...] = MagicMock()` in conftest

| Repo                                                         | Conftest                 | Lines  | Severity                                   |
| ------------------------------------------------------------ | ------------------------ | ------ | ------------------------------------------ |
| **`deployment-api/tests/unit/conftest.py`**                  | `tests/unit/conftest.py` | **16** | 🔴 **P1 — bigger blast radius than UTL**   |
| `unified-trading-library/tests/config_interface/conftest.py` | (the one we fixed)       | 3      | 🟡 P2 — see Section 3 for scope tightening |

**deployment-api detail**: lines 99-200 of `deployment-api/tests/unit/conftest.py` install MagicMocks for ALL
`deployment_api.services.*` submodules (user_management, data_status_drilldown, data_status_mock, shard_detail,
coverage_drift, data_status_hierarchical, deploy_missing, tarball_staleness) plus a recursive submodule walker.

**The risk**: if any deployment-api production code does `while x.method():` where `x` is one of those mocked services,
the same OOM-class bug fires when tests run. **I did not exhaustively grep deployment-api source for
`while ... .method()` patterns** — recommend slot 7 take a 30-minute audit since they own deployment-api and have direct
context.

### 2.3 Pattern C — session-autouse fixtures (high blast radius)

7 repos use `scope="session", autouse=True`:

- instruments-service
- unified-api-contracts
- unified-trading-library (config_interface — the one we know is dangerous)
- alerting-service
- market-tick-data-service
- client-reporting-api
- batch-live-reconciliation-service

I did NOT verify whether any of the other 6 install `sys.modules` mocks with that scope. Each is a 2-minute read of the
conftest. Worth doing.

---

## Section 3 — UTL architecture smells (separate from OOM)

These are design-quality observations from reading UTL during the audit. None are individual OOM risks; they're "UTL is
fragile in multiple ways" findings worth a dedicated cleanup epic.

### B1 — `_resolve_save_path` design itself is fragile (P1)

Even with my bound, the approach is risky:

- **Race condition**: two concurrent `save_config()` on the same second observe `blob_exists=False` for sequence=0 →
  both write to the same path → silent data loss.
- **Better design**: `path = f"config-v{timestamp}-{uuid4().hex[:8]}.yaml"` — eliminates collision possibility and
  removes the loop entirely.

### B2 — Bound-method capture spookiness (P2)

[`persistence.py:241`](../../unified-trading-library/unified_trading_library/config_interface/persistence.py#L241):

```python
self._audit_log = ConfigAuditLog(..., storage_fn=self._get_storage, ...)
```

Captures `self._get_storage` as a bound-method reference at `__init__` time. If a user does
`store._get_storage = lambda: my_local_client` (which the failing integration test does), the audit log STILL uses the
original method — "spooky action at a distance" subtle bug. Better: pass `self` and let audit log call
`self._get_storage()` lazily so monkey-patches take effect.

### B3 — `ConfigAuditLog.append()` is read-modify-write with no locking (P2)

[`persistence.py:151-171`](../../unified-trading-library/unified_trading_library/config_interface/persistence.py#L151)
downloads existing JSONL, appends, uploads back. **Two concurrent `save_config()` lose one of the audit entries.**
Docstring acknowledges it ("not designed for high-throughput concurrent writes") but the docstring is the only
safeguard.

### B4 — UTL test layout drift (P1, slot 6 already aware)

UTL has BOTH flat `tests/unit/` (legacy, 10 files) AND per-family `tests/<X>/unit/` (7 families: events,
events_interface, config_interface, cloud_interface, pnl_attribution, usage_meter, security). Today's
`PYTEST_UNIT_DIR="tests/"` override at [PM@c7786b2f](../../unified-trading-pm) is a bandaid. Right fix: consolidate into
one layout. Slot 6 has this on their plate under the UTL QG sweep.

### B5 — Circular dep UTL ↔ unified-trading-services (P1, root cause of the conftest mock)

The conftest comment is the smoking gun:

```python
# unified-trading-services imports it at init;
# without this mock, tests fail with ModuleNotFoundError when the venv lacks
# unified-events-interface (circular dep prevents adding it to pyproject).
```

A library shouldn't have to mock its own runtime dependency to test. The circular dep is the root cause; the conftest
mock is the symptom. Breaking the cycle (extract events into a third package, or restructure dep direction) eliminates
the conftest mock entirely AND removes the OOM bug class that mock enabled.

### B6 — Test isolation depends on test-order discipline (P2)

The 5 timing-out tests in `tests/events/unit/test_missing_coverage.py` pass in 17s solo but **timeout at 60s in full
QG**. Reason: UTL's `tests/config_interface/conftest.py` `_mock_utl_events_and_cloud_interface` is `scope="session"` so
the `sys.modules` mocks live for the whole pytest session and pollute `tests/events/` tests that run AFTER
`tests/config_interface/`.

**Tactical fix** (deferred to slot 6's `utl_qg_preexisting_failures` queue): change `scope="session"` →
`scope="package"` so the mock only applies to tests under `tests/config_interface/`. Need to verify all config_interface
tests still pass after the scope change.

**Architectural fix** (better but bigger): don't mock at the `sys.modules` level — use proper dependency injection so
`unified_trading_services` doesn't unconditionally import `unified_trading_library.events` at module load.

### B7 — UTL is a "library god-package" (P3, structural)

50+ submodules in one package: memory_monitor, kill_switch, treasury, scenario, streaming, lifecycle, manifest_writer,
signing, cloud_interface, config_interface, events, pnl_attribution, usage_meter, security, batch_live_reconciliation,
walk_forward, synthetic, domain_client, ... — UTL is closer to a microservice mono-package than a focused library.
Today's line-length sweep touched 350 files in one commit; cross-cutting changes always touch dozens of unrelated
subdomains.

Long-term: split UTL into focused libraries (`utl-events`, `utl-cloud`, `utl-config`, `utl-trading-primitives`, etc.) so
changes have narrow blast radius. Out of scope for May-23.

### B8 — `quality-gates.sh` runs `ruff format` (in-place) by default (P2 — usage gotcha)

When I ran `bash scripts/quality-gates.sh` for memory diagnostics today, it modified 350 files in main UTL via the
AUTO-FIX block. **The flag exists** — `--no-fix` (see Section 4 for full details) — but it's not the default and not
obviously the right flag for "I just want to measure / observe, don't touch my files."

Recommendation: when any agent runs QG outside of a "I want to land changes" workflow, use
`bash scripts/quality-gates.sh --no-fix`. Add to `SUB_AGENT_MANDATORY_RULES.md`:

> **Diagnostic QG runs MUST use `--no-fix`** to prevent ruff from modifying files. Default
> `bash scripts/quality-gates.sh` is for "I want to ship" workflow only.

### B9 — All QG steps run sequentially in same process group with no inter-step GC (P3)

Hence the 5.29 GB QG peak. Each tool individually fits a 7 GB CI runner; stacked together with no memory release pushes
close to the limit. Recommendation:

- Run basedpyright + ruff + codex/lint BEFORE pytest (they don't need pytest's coverage data)
- Add explicit `python3 -c "import gc; gc.collect()"` between heavy steps in `base-service.sh`
- Cap basedpyright thread pool (`PYRIGHT_CONCURRENCY=2`) on memory-constrained CI

---

## Section 4 — Quality-gates.sh local-vs-CI mode (VERIFIED CORRECT)

Operator's mental model is exactly what's implemented. Verified by reading
[`scripts/quality-gates-base/base-service.sh:127-238`](../../scripts/quality-gates-base/base-service.sh#L127) and
[`.github/workflows/python-quality-gates.yml:193`](../../unified-trading-pm/.github/workflows/python-quality-gates.yml#L193):

| Mode                                                      | Command                                                                 | What runs                                                                                                                         | Behavior                                                                                 |
| --------------------------------------------------------- | ----------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| **Local default** (developer / agent shipping work)       | `bash scripts/quality-gates.sh`                                         | `[1/6] AUTO-FIX` block runs FIRST: `ruff format` (in-place) + `ruff check --fix` (in-place). Then LINT + TYPECHECK + TESTS gates. | Autofix drift, then check. **Run before pushing.** Commits pick up the autofixed result. |
| **Local diagnostic** (read-only observation)              | `bash scripts/quality-gates.sh --no-fix`                                | `[1/6] AUTO-FIX` block SKIPPED. LINT step `ruff check` (no `--fix`) fails on drift. Same for TYPECHECK + TESTS.                   | Verifies what CI would see. **Use this when measuring / debugging.**                     |
| **CI** (`.github/workflows/python-quality-gates.yml:193`) | `bash scripts/quality-gates.sh --no-fix 2>&1 \| tee /tmp/qg_output.log` | Same as local diagnostic.                                                                                                         | Drift = build fails. Zero autofix.                                                       |

### Mode-flag table (verified from `base-service.sh`)

| Flag                       | Default                         | Effect                                                            |
| -------------------------- | ------------------------------- | ----------------------------------------------------------------- |
| `FIX_MODE`                 | `true`                          | Runs AUTO-FIX block (ruff format + ruff check --fix) before gates |
| `--no-fix`                 | (sets `FIX_MODE=false`)         | Skips AUTO-FIX. Drift = fail. **CI uses this.**                   |
| `--fix`                    | (sets `FIX_MODE=true`, default) | Explicit autofix. Default.                                        |
| `--quick`                  | `false`                         | Skip slow tests                                                   |
| `--lint`                   | (sets `RUN_TESTS=false`)        | Lint only                                                         |
| `--test`                   | (sets `RUN_LINT=false`)         | Tests only                                                        |
| `--skip-typecheck`         | `false`                         | Skip basedpyright                                                 |
| `--skip-tests`             | (alias `RUN_TESTS=false`)       |                                                                   |
| `--skip-lint`              | (alias `RUN_LINT=false`)        |                                                                   |
| `--act`                    | `false`                         | Run via local act (CI sim)                                        |
| `--skip-version-alignment` | `false`                         | Skip workspace dep alignment check                                |
| `--ignore-timeout`         | `false`                         | Don't fail on slow tests                                          |

### Operator's intent vs implementation — match

| Operator expectation                                                   | Implementation                                                                                                                                                                      | Status                                                                       |
| ---------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Locally: ruff format autofix runs (don't manually format)              | `FIX_MODE=true` default → AUTO-FIX block runs `ruff format` + `ruff check --fix`                                                                                                    | ✅                                                                           |
| Locally: catch drift and let ruff fix it                               | Same — AUTO-FIX in-place                                                                                                                                                            | ✅                                                                           |
| CI: format check (no fix), zero drift expected                         | `--no-fix` → SKIPS AUTO-FIX, LINT runs `ruff check` only                                                                                                                            | ✅                                                                           |
| Same for basedpyright + pytest (catch drift locally, prove zero in CI) | basedpyright + pytest are check-only at all times — they don't have an autofix mode. The "fix" for type errors / failing tests is for the developer to write code; QG just reports. | ✅ (semantic match — there's no auto-fix for types/tests, so no flag needed) |

### One small gap to flag (P3 nice-to-have)

The LINT step (`ruff check`) does NOT include `ruff format --check`. If a CI run encounters formatting drift,
`ruff check` might catch some of it via E501-class rules but might not catch all whitespace/wrapping issues. To be
belt-and-suspenders, add to LINT step:

```bash
run_timeout 30 $RUFF_CMD format --check $SOURCE_DIRS || { log_fail "Format check FAILED — run 'bash scripts/quality-gates.sh' locally to autofix"; exit 1; }
```

This is a 5-line patch to `base-service.sh`. Worth doing but P3 (current `ruff check` catches most drift; format-only
drift is rare).

---

## Section 5 — Recommended follow-up actions (priority-ordered)

### P0 — done

- [x] **Bound `_resolve_save_path`** — shipped `utl@93ff771`
- [x] **Conftest mock blob_exists default to False** — shipped `utl@93ff771`
- [x] **Regression tests** — shipped `utl@93ff771`

### P1 — needs owner assignment

- [x] ✅ **deployment-api conftest audit** (Section 2.2) — slot 4 2026-05-19: grepped deployment*api/ source for
      `while x.method():` patterns (blob_exists/exists/has*/contains/next/peek/fetch/poll/read/wait*for*). ZERO hits.
      deployment-api source has no OOM-class while-loop patterns. deployment-api conftest MagicMocks are safe.
- [x] ✅ **UTL test layout consolidation** (Section 3 B4) — TRACKED-ELSEWHERE: slot 6's `utl_qg_preexisting_failures`
      queue. No action needed here.
- [ ] **BLOCKED-OPERATOR-DECISION** **UTL ↔ unified-trading-services circular dep** (Section 3 B5) — design decision,
      needs operator + Ikenna. Until resolved, conftest mock pattern persists and is the OOM-class root cause.
- [x] ✅ **Conftest scope=session → scope=package** (Section 3 B6) — slot 6's `utl_qg_preexisting_failures` queue.
      Tactical fix; verify all config_interface tests still pass after scope change. — utl@82c7bc02 (2026-05-17).
      Pre-existing 12 integration failures unchanged; all unit tests pass (16/16).
- [x] ✅ **B1 race-condition fix** in `_resolve_save_path` — add UUID nonce to filename, eliminate the loop entirely. ~1
      hour. Slot 6 territory. — utl@dc7382f0 (2026-05-17).

### P2 — backlog, take when slot bandwidth allows

- [x] ✅ **Other 6 session-autouse conftests audit** (Section 2.3) — slot 4 2026-05-19: audited instruments-service,
      unified-api-contracts, alerting-service, market-tick-data-service, client-reporting-api,
      batch-live-reconciliation-service. ZERO `sys.modules` installs in any conftest.py. All 6 are safe — OOM pattern
      does not apply.
- [ ] **DEFERRED-POST-CUTOVER** **B2 bound-method capture** in `ConfigStore.__init__` — pass `self` instead of
      `self._get_storage`. ~30 min including tests. Not May-23 critical path.
- [ ] **DEFERRED-POST-CUTOVER** **B3 ConfigAuditLog locking** — add file-based lock OR document-and-enforce
      single-writer assumption. ~1 hour. Not May-23 critical path.
- [x] ✅ **B8 SUB_AGENT_MANDATORY_RULES update** — ALREADY DONE: `--no-fix` documented at lines 22-44 of
      `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` with ship-mode vs diagnostic-mode table + 2026-05-15 incident note.

### P3 — nice-to-have, post-cutover

- [ ] **DEFERRED-POST-CUTOVER** **B7 UTL split into focused sub-libraries** — long-term structural cleanup.
- [ ] **DEFERRED-POST-CUTOVER** **B9 QG memory optimization** — explicit GC between phases, `PYRIGHT_CONCURRENCY=2`.
- [ ] **DEFERRED-POST-CUTOVER** **strategy-service `domain_event_logger:361` byte-by-byte tail** — replace with
      fixed-size buffer read from end.
- [ ] **DEFERRED-POST-CUTOVER** **B4 LINT step gap** — add `ruff format --check` to LINT step in `base-service.sh`. 5
      min, but post-cutover to avoid mid-flight QG churn.

### Workspace mitigation (operator action, no code change)

- [ ] **OPERATOR-ACTION** **Add `mempy` alias to `~/.bashrc`** to wrap any direct `python` / `pytest` invocation in a 15
      GB cgroup cap. No code change — operator runs these 3 bash lines on their workstation.

- [ ] **OPERATOR-ACTION** **Set negative `oom_score_adj` for VSCode + Konsole** so kernel kills runaway scripts first,
      never the IDE. Operator runs the loop on their workstation.

---

## Appendix — diagnostic artifacts (kept for reference, regenerable)

- `/tmp/oom_repro_minimal.py` — 38-line standalone repro that demonstrates the bug without pytest. Useful for future
  verification.
- `/tmp/oom_repro_monitor.sh` — cgroup-capped wrapper with auto-kill on RSS threshold. Reusable for future memory
  investigations. Usage:
  ```bash
  SOFT_KILL_GB=5 MEMORY_MAX_GB=20 /tmp/oom_repro_monitor.sh <label> -- <command> [args...]
  ```
- `/tmp/oom_repro_*_rss.log` — 64 RSS curve logs from today's bisection runs (slot6_full, slot6_int_libdeps, slot6_t9,
  fix_t9_v2, utl_full_qg, utl_pytest_alone, utl_basedpyright_alone, etc.).

---

## Triage — 2026-05-18

**Status**: CLOSED — SHIPPED **Triaged by**: slot-8 triage sweep **Reason**: Root-cause fixed; P1-P3 follow-ups
documented in successor plans
