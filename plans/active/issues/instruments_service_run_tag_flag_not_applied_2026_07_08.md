---
doc_type: issue
title: "instruments-service's --run-tag CLI flag doesn't do what its help text says"
summary: >-
  --run-tag's help text promises a "GCS output prefix tag," but instruments-service never calls UTL's apply_run_tag()
  anywhere — the value never reaches any output path. The only real effect is a narrow raw-argv string match
  (`--run-tag=t1-recon`) that self-defaults the date window to today. An operator relying on --run-tag to isolate a
  test/experimental run's output would get no isolation at all.
status: open
nature: notes
asset_group: [meta]
stage: [meta]
repos: [instruments-service]
scope: [engineer]
tags: [cli, bug-fix, p2, instruments-service]
related:
  [
    ../instruments_service_docs_consolidation_2026_07_08.md,
    ../canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md,
  ]
created: 2026-07-08
parent_epic: instruments_master
priority: P2
source:
  "Found during a dedicated CLI-argument audit (2026-07-08) — operator asked for a full audit of whether every
  instruments-service CLI flag actually filters/scopes execution end-to-end, prompted by removing a dead
  single-venue-fetch convenience function and wanting to confirm --venues was a safe real replacement (confirmed it is).
  The audit's other finding, --trigger, is self-documented in the code as pending Phase B.1+ work — not a regression.
  --run-tag is a real, undocumented gap."
assigned_vm: NA
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
last_updated: 2026-07-08
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
resolved_by:
---

## The bug

`instruments-service/instruments_service/cli/main.py:253-260` defines `--run-tag` with help text describing it as a "GCS
output prefix tag" (default `"batch"`). But `unified_trading_library`'s `apply_run_tag()`
(`config_interface/paths/registry.py:264`) — the real function that would actually route output under a tagged prefix —
is never called anywhere in instruments-service. The parsed value never reaches any output path.

The **only** real consumer of `--run-tag` in the whole repo is `cli/main.py:328`, and it doesn't even read
`args.run_tag` — it does a raw string match against `sys.argv`
(`if _arg_value(argv, "--run-tag") != "t1-recon": return`) to decide whether to self-default `--start-date`/`--end-date`
to today. That's a narrow, unrelated behavior, not the "output prefix tag" the flag's own help text promises.

**Real operator impact**: anyone using `--run-tag` expecting isolated/tagged output (e.g. for a test run, or to compare
two experimental captures without clobbering the real batch output) gets no isolation — the run writes to the exact same
paths a tagless run would.

## Todos

- [x] [DECISION] P2. **Decide the fix direction — RESOLVED 2026-07-10 (operator): option (a), wire it through.** This
      was framed as an open operator call, but it isn't — `/codex/08-workflows/t1-batch-dag.md` already documents the
      target `--run-tag` behavior verbatim ("data goes to `t1-recon/`... implementation steps: CLI arg, GCS writer
      prefix, event writer prefix"), and `main.py`'s existing `"t1-recon"` string-match special-case proves the flag was
      added with that contract in mind — it just never finished the wiring. The code should be brought into compliance
      with the already-documented target, not have its help text rewritten to describe the narrower, incomplete current
      behavior. (See `instruments_remaining_work_audit_2026_07_10.md` §1a item 11.)
- [ ] [SCRIPT] P2. **Wire `--run-tag` through to `apply_run_tag()`** per `t1-batch-dag.md`'s documented steps (CLI arg →
      GCS writer prefix → event writer prefix), add a regression test confirming the real behavior now matches the codex
      SSOT.
- [ ] [SCRIPT] P2. **Ship via quickmerge**, quality-gates green.

## Progress Log

- **2026-07-08** — Filed from a dedicated CLI-argument audit. Root cause confirmed via direct grep+read: `main.py:328`
  is the only consumer, and it string-matches raw argv rather than reading the parsed flag or calling `apply_run_tag()`.
- **2026-07-10** — Decision resolved (operator, confirming a review finding): wire it through per the already-
  documented `t1-batch-dag.md` target, not an open call. Implementation still pending. No fix applied yet.
