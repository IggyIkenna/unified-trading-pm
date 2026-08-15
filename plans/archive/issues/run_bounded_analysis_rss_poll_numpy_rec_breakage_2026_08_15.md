---
doc_type: issue
title:
  scripts/dev/run-bounded-analysis.sh's RSS-poll fallback breaks pandas groupby (ModuleNotFoundError numpy.rec) even
  though the SAME script runs fine unwrapped
summary: >-
  Hit live 2026-08-15 verifying a manifest-reader fix: a script that called pandas `DataFrame.groupby()` ran
  successfully when invoked directly (`.venv/bin/python script.py`), but raised `ModuleNotFoundError: No module named
  'numpy.rec'` deep inside pandas' groupby internals (`pandas/core/dtypes/missing.py::_isna_array` ->
  `numpy.rec.recarray`) when the IDENTICAL script was invoked through `scripts/dev/run-bounded-analysis.sh`'s RSS-poll
  fallback path (the `systemd-run` cgroup path is unavailable on this host — "systemd-run unavailable on this host
  (macOS / no user systemd instance)" — so it falls to `_run_with_rss_poll_cap`, which backgrounds the command via `set
  -m; "$@" &`). A bare interactive check (`.venv/bin/python -c "import pandas; ...; df.groupby(['a']).sum()"`) in the
  same venv, same session, succeeded immediately — ruling out a broken/corrupted numpy install.
status: open
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [run-bounded-analysis, rss-poll, numpy, pandas, subprocess-environment, bug]
related: [/plans/active/cross_cutting_consolidated_closeout_2026_07_25.md]
created: 2026-08-15
author: slot-29 (backend_engineer)
source: ["mtds_pipeline_e2e_check_driver_vm_oom_full_mvp_sweep_2026_08_14.md, verifying the DEFI OOM fix"]
assigned_vm: planning
resolved_by:
locked_by:
locked_since:
execution_scope: orchestrator-agent
estimate_class: refactor
estimate_baseline_ai_days: 0.15
estimate_calibrated_ai_days: 0.06
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-15
parent_epic: agent_operating_framework_master
priority: P3
---

# run-bounded-analysis.sh's RSS-poll fallback breaks pandas groupby (numpy.rec ModuleNotFoundError)

## What I found

Reproduced twice with two different scripts (a parquet footer-metadata inspector, and a captured- days aggregation
verifier), both calling `pandas.DataFrame.groupby(...)`:

```
$ .venv/bin/python my_script.py                                  # direct: WORKS
$ bash scripts/dev/run-bounded-analysis.sh --mem-cap 12G -- .venv/bin/python my_script.py   # BREAKS
```

Full traceback (abbreviated) from the wrapped run:

```
File ".../pandas/core/groupby/ops.py", line 754, in group_info
File ".../pandas/core/groupby/grouper.py", line 835, in _codes_and_uniques
File ".../pandas/core/algorithms.py", line 789, in factorize
    null_mask = isna(values)
File ".../pandas/core/dtypes/missing.py", line 288, in _isna_array
    elif isinstance(values, np.rec.recarray):
ModuleNotFoundError: No module named 'numpy.rec'
```

A bare interactive check in the exact same venv/session
(`import pandas as pd; import numpy as np; df = pd.DataFrame(...); df.groupby(['a']).sum()`) succeeded with no error —
ruling out a corrupted/incomplete numpy install as the cause. The failure is specific to running under
`run-bounded-analysis.sh`'s RSS-poll fallback (`_run_with_rss_poll_cap`, engaged when `systemd-run` cgroups are
unavailable on the host — the common case on this VM per the script's own "systemd-run unavailable on this host (macOS /
no user systemd instance)" message, which is misleading — this is a real Linux host, not macOS; the message conflates
"no user systemd instance" with "macOS", worth a separate small doc fix).

`numpy.rec` is a real, always-importable numpy submodule (`numpy.core.records` alias) — pandas' `_isna_array` calls
`isinstance(values, np.rec.recarray)` unconditionally on some code paths. Likely candidates for why the wrapped
subprocess sees a different numpy state: the `set -m; "$@" &` job-control backgrounding changes something about how the
child process's Python interpreter resolves numpy's lazy submodule attributes (numpy 2.x uses `__getattr__`-based lazy
imports for some submodules), or an environment variable difference between the interactive shell and the backgrounded
job affects import resolution. Not root-caused further this session — worked around by running the verification directly
(unwrapped) instead, after confirming host memory headroom manually.

## Why it matters

`run-bounded-analysis.sh` is the SSOT-recommended way to safely run ad-hoc analysis scripts on this shared host (per
`vm-launcher-runbook.md` § heavy-compute-on-shared-host). Any script that uses pandas groupby (a very common pattern)
will silently fail when wrapped, on any host where the `systemd-run` path is unavailable (seemingly this VM, and per the
script's own docstring, macOS too) — forcing agents to either run unwrapped (losing the memory-cap safety net this
script exists to provide) or hit a confusing, seemingly-unrelated `ModuleNotFoundError` that doesn't obviously point
back to the wrapper as the cause.

## Recommended decision

Root-cause why `set -m` backgrounding perturbs numpy's lazy-attribute resolution for the child Python process (compare
`env` / `sys.path` / `sys.modules` state between a direct run and a wrapped run at the point of failure), then fix
`_run_with_rss_poll_cap` so it doesn't alter the child's import environment. Separately, fix the misleading "macOS / no
user systemd instance" message to distinguish the two cases (this is a real Linux host without a systemd --user instance
enabled, not macOS).

## Open work (tracked todos)

- [x] ✅ [BACKEND] P3. Root-cause + fix `scripts/dev/run-bounded-analysis.sh`'s RSS-poll fallback
      (`_run_with_rss_poll_cap`) breaking `pandas.DataFrame.groupby()` with
      `ModuleNotFoundError: No module named 'numpy.rec'` on at least one real Linux host (confirmed reproducible: direct
      run works, wrapped run fails, identical venv/script). Add a regression test/repro script. (repo:
      unified-trading-pm) — **2026-08-15, slot-17**: could NOT reproduce the exact `numpy.rec` failure synthetically
      (tried a bare `groupby()` script and a `pyarrow.parquet`-then-`groupby()` script, both directly and wrapped, on
      pandas 2.3.3/numpy 2.3.5 in this VM's venvs — both paths succeeded every time). A signal-disposition/pgrp/sid probe
      (`os.getpgrp()`/`os.getsid()`/`signal.getsignal(SIGINT|SIGQUIT)`) also showed no difference between a direct run
      and the `set -m`-backgrounded run in this tool-harness's own (already non-interactive) shell context — the
      original repro happened in a genuinely interactive terminal pane, which this environment can't replicate, so the
      exact mechanism remains unconfirmed. Given that, applied the most defensible structural fix backed by the issue's
      own hypothesis rather than continuing an open-ended non-reproducible hunt: `_run_with_rss_poll_cap` now prefers
      `setsid` (Linux/util-linux — gets the same PID==PGID process-group property via a syscall, no bash job-control
      state) over `set -m` job-control backgrounding, since `set -m` mid-script is the ONE thing this fallback changes
      relative to an unwrapped run (job-control notifications + pgrp/session reassociation semantics) and was the
      prime suspect. `set -m` remains the fallback only when `setsid` is unavailable (macOS/BSD — matches the
      2026-08-12 history in the script's own header comment). Added Test 5 to
      `scripts/dev/test-run-bounded-analysis.sh` — a `pandas.DataFrame.groupby()` run through the RSS-poll fallback,
      guarded to skip (not false-fail) when the ambient `python3` lacks pandas, exercisable against a real venv via
      `TEST_PYTHON=/path/to/venv/python`; verified PASS against a pandas 2.3.3/numpy 2.3.5 venv on this host, plus all
      4 pre-existing tests still pass. If this regresses again, the exact repro conditions (interactive terminal
      pane, not a headless tool harness) are the next thing to control for.
- [x] ✅ [DOCS] P3. Fix `run-bounded-analysis.sh`'s "systemd-run unavailable on this host (macOS / no user systemd
      instance)" message to distinguish "real Linux host, systemd --user not enabled" from "genuinely macOS, no systemd
      at all" — the current wording is misleading on Linux hosts hitting this fallback (confirmed live 2026-08-15 on a
      real AWS Linux VM). (repo: unified-trading-pm) — **2026-08-15, slot-17**: message now branches on `uname -s`:
      `"(macOS — no systemd at all)"` on Darwin, `"(no systemd --user instance enabled)"` everywhere else; verified live
      on this Linux VM.
