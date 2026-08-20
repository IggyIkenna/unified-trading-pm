---
doc_type: issue
title: >-
  agent-orchestrator's full `pytest --cov=server` run dies silently (no traceback, not OOM) near 96-97% completion on
  this shared host under concurrent-session load — full suite without `--cov` completes cleanly in 211s
summary: >-
  While fixing a coverage-ratchet regression (agent-orchestrator PR#847, escalation agt-5581af), the full
  `quality-gates.sh` pytest+coverage invocation (~5236 tests, single process, `--cov=server`) reproducibly died with no
  traceback/OOM evidence near 96-97% completion, every time, on this host (13+ concurrent Claude sessions, load avg
  ~13/16 cores) — but the SAME suite WITHOUT `--cov` completed cleanly in 211s. Root-caused to `--cov` instrumentation
  itself (not OOM, not cgroup/pids limits, not tracer-backend choice — `COVERAGE_CORE=sysmon` also crashed at the same
  relative point). Workaround found and verified twice: split test files into two halves, run each as a separate pytest
  invocation with its OWN `COVERAGE_FILE` (not `--cov-append` onto one shared file — that reproduced the same crash on
  the second half), then `coverage combine` + `coverage json`/`report --fail-under` + the ratchet check as separate
  lightweight steps. This is NOT yet a durable fix in `scripts/quality-gates.sh` — only a manual workaround used once
  this session. Filed because this looks like the same failure class as the currently-open repo-blocker
  `RB-34953de6` (different slot/escalation, symptom: "coverage SQLite OperationalError... after 1133-1145 passes with
  thousands of collection errors, dashboard QG reports missing @vitest/coverage-v8") — both are agent-orchestrator local
  QG runs failing under concurrent host load, though the exact failure signature differs (silent death here vs. SQLite
  OperationalError + collection errors there), so they may share a root cause (host resource contention under heavy
  concurrent `--cov` usage) without being the identical bug.
status: open
archive_exempt: true
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [ci, quality-gates, coverage, pytest, host-contention, qg-infra, flaky]
related:
  [/plans/epics/infrastructure_master.md, /plans/active/infra_consolidated_closeout_2026_07_25.md]
created: 2026-08-20
author: slot-33 (cicd)
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.64
assigned_role: backend_engineer
drift_direction: advance-code
sequential: false
locked_by:
context_scope:
  [
    agent-orchestrator/scripts/quality-gates.sh,
    agent-orchestrator/scripts/quality_gates/check_coverage_ratchet.py,
    /codex/06-coding-standards/quality-gates.md,
  ]
resolved_by:
source: >-
  Discovered 2026-08-20 (slot-33, cicd one-shot escalation agt-5581af) while diagnosing why the local
  `quality-gates.sh` pytest+coverage step would not complete in order to ship a coverage-ratchet regression fix for
  agent-orchestrator PR#847.
depends_on: []
---

# agent-orchestrator full `pytest --cov` dies silently under host load — split-coverage workaround found, not yet a durable fix

## What I found

Running agent-orchestrator's full test suite (`tests/` ~5236 tests) with coverage instrumentation
(`python -m pytest tests/ -q -p no:cacheprovider --cov=server --cov-report=term-missing --cov-report=json:coverage.json --cov-fail-under=72`,
the exact invocation `scripts/quality-gates.sh` uses) reproducibly died with **no traceback, no error output, no OOM-kill
evidence anywhere** — checked `/proc/vmstat` (`oom_kill=0`), the `orchestrator.service` cgroup (`memory.max=26GB` /
`memory.current=9.8GB`, real headroom; `pids.max=10000` / `pids.current=438`, real headroom), and `journalctl`/kernel
messages (nothing relevant) — near 96-97% completion, every single time, across 4+ full-suite attempts.

Ruled out, in order:

1. **OOM** — no oom_kill events, cgroup memory had headroom.
2. **pids/process limits** — cgroup pids had headroom.
3. **The specific test at the death point** — isolated single-file run of the file at the crash boundary passed cleanly
   in 64s.
4. **Tracer backend** — `COVERAGE_CORE=sysmon` (Python 3.13's low-overhead `sys.monitoring` backend) crashed at the
   same relative point as the default tracer.

**Confirmed trigger**: `--cov` instrumentation itself, under sustained load, in a single long-running process. A full
run WITHOUT `--cov` completed cleanly: `5234 passed, 2 skipped, 2 warnings in 211.56s (0:03:31)`. Every `--cov`-enabled
full run died at 340-420s regardless of tracer backend.

**Working workaround** (verified twice — both times against the true current HEAD, re-run after an unrelated
concurrent commit landed on the branch mid-session):

1. Bisect `tests/test_*.py` alphabetically into two file-lists.
2. Run each half as a **separate pytest invocation** with its **own `COVERAGE_FILE`** env var, e.g.:
   `COVERAGE_FILE=.coverage.half1 python -m pytest <half1 files> -q -p no:cacheprovider --cov=server --cov-report=`
   (empty `--cov-report=` suppresses that half's own report/fail-under enforcement).
3. `python -m coverage combine .coverage.half1 .coverage.half2`
4. `python -m coverage json -o coverage.json` then `python -m coverage report --fail-under=72` as separate steps.
5. `python scripts/quality_gates/check_coverage_ratchet.py --report coverage.json` unchanged.

**Critical detail**: this must use **separate `COVERAGE_FILE` values**, NOT `--cov-append` onto one shared `.coverage`
file. An earlier attempt using `--cov-append` had half 1 succeed but half 2 — which had to reload and append onto the
already-large accumulated dataset — crash at its OWN 94% mark. This proves the trigger is **live growth/reload of an
in-process coverage dataset**, not raw wall-clock duration or raw test count: two fresh, independent, smaller coverage
datasets survive; one growing shared dataset does not.

## Why it matters

This is a **shared-host** condition (13+ concurrent Claude sessions observed this session, load avg ~13 on 16 cores) —
any agent/slot running a full `quality-gates.sh` on this host can hit it, not just this session. It looks like the same
failure class as the currently-open repo-blocker **`RB-34953de6`** (agent-orchestrator, filed by a different
escalation/slot the same day: "coverage SQLite OperationalError unable to open database file after 1133-1145 passes
with thousands of collection errors"). The exact symptom differs (silent death here vs. SQLite `OperationalError` +
collection errors there), so I did NOT resolve that blocker off this finding — but both point at the same underlying
class (agent-orchestrator's full-suite `--cov` run failing under concurrent host load) and a durable fix here would
likely also close that blocker's condition. The workaround above was applied manually, once, for one commit — it is not
wired into `scripts/quality-gates.sh` itself, so every future full local QG run on a loaded host hits this again unless
someone repeats the workaround by hand.

## Recommended decision

Two independent tracks:

1. **Durable fix in `scripts/quality-gates.sh`** (closes this for every future run): permanently split the pytest+`--cov`
   invocation into N chunks (file-list bisection or `pytest-xdist`-style sharding) each with its own `COVERAGE_FILE`,
   then `coverage combine` before the ratchet check — mirroring the manual workaround above. This trades one long
   single-process run for several shorter independent ones, which is what actually avoided the crash.
2. **Host-level investigation** (why does `--cov`'s live dataset growth trigger an unexplained silent death under load,
   with zero OS-level evidence?) — genuinely uncharacterized beyond the ruled-out causes above. Lower priority since
   track 1 sidesteps it, but worth a dedicated investigation if this recurs elsewhere (e.g. inside `RB-34953de6`'s own
   diagnosis) since an unexplained silent process death is itself a signal something in the host/coverage.py/Python
   3.13 interaction is not well understood.

## Todos

- [ ] [BACKEND] P2. Wire the split-coverage-with-separate-`COVERAGE_FILE`-then-`coverage combine` workaround into
      `scripts/quality-gates.sh`'s pytest+coverage step permanently, so every local/CI full-suite run on this host is
      immune to this failure mode rather than requiring a manual workaround each time. Repo: agent-orchestrator.
- [ ] [BACKEND] P3. Cross-check this finding against repo-blocker `RB-34953de6`'s own diagnosis (different slot/
      escalation, same day, same repo, same class of symptom: coverage/collection failures under concurrent host load)
      once that blocker is worked — confirm whether it's the identical root cause or a distinct one, and fold findings
      together if so. Repo: agent-orchestrator.

## Progress Log

- **2026-08-20 (slot-33, cicd one-shot escalation agt-5581af)**: Filed after root-causing and working around this
  failure while shipping a coverage-ratchet regression fix for PR#847. The actual escalation (coverage ratchet fix) was
  shipped and closed independently (agent-orchestrator@52e153d65a) — this issue tracks the underlying host/QG-infra
  finding, which is out of scope for that one-shot task but too valuable to lose.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries).
