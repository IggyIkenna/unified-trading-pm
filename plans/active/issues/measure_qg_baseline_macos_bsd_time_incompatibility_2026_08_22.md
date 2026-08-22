---
doc_type: issue
title: "measure-qg-baseline.sh --env local is unconditionally broken on macOS dev boxes — hardcoded GNU `/usr/bin/time -v`"
summary: >-
  scripts/dev/measure-qg-baseline.sh's measure_one() invokes `/usr/bin/time -v -o "$tlog" bash scripts/quality-gates.sh
  ...` to capture wall/cpu/peak-rss for a baseline entry. `-v` is a GNU-time-only flag; macOS ships BSD `time` at
  `/usr/bin/time`, which only accepts `-a`/`-l`/`-h`/`-p`/`-o`. On a Mac dev laptop this fails instantly with
  `/usr/bin/time: illegal option -- v` — the wrapped `quality-gates.sh` invocation never even starts, so the script
  writes a bogus `wall=0.0s peak_rss=0MB cpu=0.0s exit=1` entry-attempt (rejected/no-write in this instance only because
  nothing legitimate was produced to compare, not because the anomaly guard caught a real measurement). No GNU time
  (`gtime`, e.g. via `brew install gnu-time`) was installed on the box this was discovered on. `--env vm` almost
  certainly works (AWS worker VMs run Linux, where GNU time is the `/usr/bin/time` default) — this is specifically an
  `--env local` / macOS-laptop gap. Discovered 2026-08-22 while investigating whether strategy-service's committed QG
  CPU-time baseline (131.2s, measured 2026-06-17) was stale enough to explain a 451s CPU observed run under heavy host
  contention (load avg 200-400) — the re-baseline attempt itself failed on this bug before it could answer that
  question, forcing a documented one-time `IGNORE_TIMEOUT` bypass instead (see
  /plans/active/code_readiness_t1_contracts_library_externalapi_2026_08_19.md Progress Log, 2026-08-22 entry).
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [quality-gates, baseline, macos, bsd-time, gnu-time, tooling-gap, resource-drift]
related:
  [
    /plans/active/code_readiness_t1_contracts_library_externalapi_2026_08_19.md,
    /plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md,
    /plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md,
  ]
created: 2026-08-22
author: unknown
source: ["2026-08-22 — interactive session, discovered while investigating strategy-service QG resource-drift"]
last_updated: 2026-08-22
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P2
milestone: M3
estimate_class: refactor
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.04
assigned_role: infra
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
context_scope: [/scripts/dev/measure-qg-baseline.sh]
---

# measure-qg-baseline.sh `--env local` broken on macOS — hardcoded GNU `time -v`

## What happened

Running `bash scripts/dev/measure-qg-baseline.sh --env local --repos strategy-service` (no `--force`) on a macOS dev
laptop produced, in the tool's own summary line:

```
strategy-service: wall=0.0s peak_rss=0MB cpu=0.0s exit=1
```

Reproducing the wrapped command directly (the tool deletes its per-repo temp logs on exit via `trap ... EXIT`, so the
real error had to be captured manually):

```
$ /usr/bin/time -v -o /tmp/x.log bash scripts/quality-gates.sh --no-fix
/usr/bin/time: illegal option -- v
usage: time [-al] [-h | -p] [-o file] utility [argument ...]
```

`/usr/bin/time` on macOS is the BSD `time` builtin (part of the base system), not GNU time. BSD `time`'s flag set is
`-a`/`-l`/`-h`/`-p`/`-o` — no `-v`. GNU time's `-v` ("verbose": wall clock, user/system CPU seconds, maximum resident
set size, etc.) is exactly what `measure_one()` parses out of the captured log (`awk -F': ' '/Maximum resident set
size/{...}'`, `/User time/`, `/System time/`) — none of those lines exist in BSD time's output format even if the
flag mismatch were fixed, so this isn't a one-line flag swap; it needs either:

- prefer `gtime` (GNU time via `brew install gnu-time`) when present, falling back to a `/usr/bin/time -l` parse path
  (BSD's `-l` prints `maximum resident set size` too, differently formatted, no explicit user/system split line — needs
  its own awk pattern), or
- document `--env local` as Linux/CI-worker-only and have the script hard-fail with a clear "install gtime" message on
  macOS instead of silently producing a bogus zeroed measurement.

## Why this matters

This is the tool `/codex/06-coding-standards/quality-gates.md`-adjacent infra points to as THE sanctioned way to
re-profile a repo's committed QG resource baseline (`scripts/dev/qg_resource_baseline.json`) when a real, durable
change (test-suite growth, new heavy fixtures, etc.) makes the committed number stale. Right now that path is a dead
end for anyone on a Mac trying to get a `local` reading — they'll either see the same silent `exit=1`/zeroed line (if
they don't independently reproduce the command like this session did) and might mistake "the tool ran, found nothing
anomalous" for "the baseline is still accurate," or they hit the confusing raw BSD-time usage error with no framing
tying it back to this script. Either way, the only two currently-viable outcomes for a stale `local` baseline on
macOS are (a) measure on a Linux box/VM instead and merge that in, or (b) leave the `local` entry stale and lean on
the `vm` entry (`quality-gates-base/base-service.sh`'s 2x-drift WARN reads whichever env matches the running host,
so a stale `local` on a mac still fires nuisance/inaccurate WARNs there too).

## Follow-up (untracked elsewhere — real work, not done here)

- [ ] [SCRIPT] P2. Make `scripts/dev/measure-qg-baseline.sh`'s `measure_one()` detect GNU vs BSD `time` (prefer `gtime`
      if on PATH; else parse BSD `time -l` output with its own field patterns; else fail loudly with an actionable
      message instead of writing a zeroed/bogus timing line) so `--env local` baselines are measurable on macOS dev
      laptops, not just Linux CI/VM workers.
