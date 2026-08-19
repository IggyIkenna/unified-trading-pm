---
name: gate-evaluation
description: >-
  Re-run /plans/active/data_pipeline_completion_2026_08_21.md's 53-gate BATCH/PAPER/LIVE readiness register as a
  live evaluation instead of a point-in-time snapshot -- the same shape as the readiness-state-dump and
  honest-coverage-dump skills it shares its coverage.json read path with. Readiness is DERIVED, never declared (the
  2026-08-16 operator ruling readiness-state-dump already follows): a gate with no genuine machine oracle reports
  `unverified`, never a fabricated PASS/FAIL. Only 3 of the 53 gates (B1 availability, B8 honest-coverage-100%, B16
  denominator-declared) have a real, already-existing machine check wired today -- all three reuse
  honest-coverage-dump's already-computed coverage.json verbatim, never recomputed. The other 50 report `unverified`
  honestly, each tagged with whether it has an owning plan/issue doc (per the register's own 2026-08-18 cross-link
  pass, 29/53 have none) so a reader sees immediately whether the gap is "go read `<doc>`" or "no tracked work exists
  for this at all". Item 10 of `cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md`. Trigger on
  `/gate-evaluation`, "run the gate evaluation", "re-run the data pipeline gate register", "which BATCH/PAPER/LIVE
  gates pass", "is B8 at 100%", "evaluate the readiness gates".
---

# gate-evaluation

Makes `/plans/active/data_pipeline_completion_2026_08_21.md`'s 53-gate BATCH/PAPER/LIVE readiness register
**re-runnable** rather than a point-in-time snapshot someone typed once — the same treatment
`readiness-state-dump` (Tuesday deliverable 1) and `honest-coverage-dump` (Tuesday deliverable 2) already got, and
the register plan's own item 10 (`cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md`) explicitly asks for
this to mirror that shape.

## Run it

**Requires** a Python whose venv has `unified-trading-library` installed (GCS reads go through UTL's
`cloud_interface` only, via the shared `shard_universe.py`/`dump_coverage.py` this skill imports from its sibling
`honest-coverage-dump/scripts/` directory — a subprocess `gcloud`/`gsutil` call is a hard workspace ban).
`instruments-service`'s venv is the natural choice, same as its two sibling skills:

```bash
cd instruments-service && .venv/bin/python3 \
    ../unified-trading-pm/cursor-configs/skills/gate-evaluation/scripts/evaluate_gates.py
```

```bash
python evaluate_gates.py                    # full 53-gate register, summary + failures
python evaluate_gates.py --verbose           # every gate's verdict, bar, owning_doc and detail
python evaluate_gates.py --category BATCH    # filter to one gate set (BATCH/PAPER/LIVE)
python evaluate_gates.py --json              # machine-readable, for a downstream consumer or a diff
python evaluate_gates.py --date 2026-08-17   # pin a specific coverage.json date
```

## What it is, and what it deliberately is NOT

**Is**: a machine-readable version of the register (`scripts/gate_registry.py` — 53 `Gate` records: id, category,
name, bar, owning_doc, transcribed verbatim from the source doc's own tables) plus an evaluator
(`scripts/evaluate_gates.py`) that runs the handful of gates with a genuine, already-existing machine oracle and
reports every other gate honestly as `unverified`.

**Is NOT** an attempt to wire all 53 gates to bespoke checks in one pass. Most gates require either a human judgment
call (B20 shard-name-orthogonality sign-off, the whole PAPER/LIVE ratification), a live drill (L9 DR/failover
exercised, L14 intraday recovery exercised), or deep service-internal investigation well beyond what a single
register-dump script can honestly automate in one session (P1 live-adapter-parity, L2 SLO attainment, etc.).
Fabricating a PASS/FAIL for those would be exactly the "proxy read as the property" failure mode CLAUDE.md's
measurement-claims-discipline rule exists to prevent — `unverified` is the honest, legitimate answer for a gate with
no real check, same as `readiness-state-dump`'s own stated policy.

## The 3 automated gates

| Gate                         | Check                                                                                                                                                                                                                                           | Source                                              |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| **B1** Availability          | Per shard: `captured > 0` OR the shard is a confirmed-empty legitimate absence (`empty_confirmed > 0`). FAILS the shard set if any shard has genuinely zero reached coverage (an `attempted_failed`-only or `expected_unattempted`-only shard). | `coverage.json`, via `dump_coverage.build_report()` |
| **B8** Honest coverage 100%  | `reachable_coverage_pct >= 100.0` across the loaded scope, denominator stated. Re-derives live the same figure the Friday-target table (`data_pipeline_completion_2026_08_21.md`) was hand-recorded from on 2026-08-18.                         | same                                                |
| **B16** Denominator declared | Structural check: all 4 capture-state labels (`captured`/`expected-absent`/`attempted-failed`/`expected-unattempted`) present as distinct keys, `reachable_denominator` carried alongside every percentage.                                     | same                                                |

All three reuse `honest-coverage-dump/scripts/dump_coverage.py`'s already-shipped `build_report()` verbatim — this
skill never re-reads `coverage.json` independently, never re-derives the expected universe, and never disagrees with
its two sibling skills about what a shard or a coverage percentage is (same "reuse, don't reimplement" discipline
those two document for each other).

## The other 50 gates — honestly `unverified`

Every gate not in the automated set reports `unverified`, with a `detail` field naming either the owning
plan/issue doc (`P1` → `venue_e2e_wiring_2026_08_16.md`, etc.) or, for the 29 gates with none, "no owning doc either
(per the 2026-08-18 cross-link pass)". This is not a placeholder to be filled in blindly — several of these gates
(B20, the whole PAPER/LIVE ratification) are `[OPERATOR]`-tagged human judgment calls that will legitimately stay
`unverified` by a script forever; others (P6 stream continuity, L2 SLOs, L12 access control) have zero existing
machine oracle anywhere in the corpus today and would need new instrumentation built elsewhere first. Wiring a NEW
gate here is a natural extension point once its owning doc ships a real check: add a `_check_<gate_id>_*()` function
to `evaluate_gates.py` and register its `gate_id` in the `CHECKERS` map + `gate_registry.AUTOMATED_GATE_IDS`.

## Registry drift guard

`gate_registry.py` asserts at import time that exactly 29 of its 53 `Gate` records carry `owning_doc=None` — the
same count the register doc's own 2026-08-18 cross-link pass found. If a future edit to
`data_pipeline_completion_2026_08_21.md`'s gate tables (a new gate, a newly-filled-in owning doc) is not mirrored
here, this assertion fails loudly at import rather than silently reporting a stale owning-doc picture. There is no
automated doc-to-registry sync — re-sync `gate_registry.py` by hand whenever the source doc's tables change, and
treat drift as a doc-hygiene finding like any other misleading-doc case.

## Shared shard enumeration — no independent GCS read

Imports `../honest-coverage-dump/scripts/{shard_universe,dump_coverage}.py` (via a `sys.path` insertion at the top
of `evaluate_gates.py`, the same pattern `readiness-state-dump` already uses to reach the same sibling directory).
Grain (2-tuple vs. 3-tuple) is whatever `coverage.json` currently carries, auto-detected — this dump never
hardcodes it and never disagrees with its two siblings about shard identity.

## Guardrails

Read-only end to end: reads `coverage.json` via UTL `cloud_interface` (through the shared `shard_universe.py`),
never writes GCS, never mutates a registry, never launches a VM, never calls a live venue API. If `coverage.json`
cannot be read, the 3 automated gates (B1/B8/B16) report `unverified` with the read error in their detail rather
than aborting the whole register — every other gate is unaffected, since it never depended on `coverage.json` in
the first place.

## First live run

Run 2026-08-19 (slot 31, infra) against production `coverage.json`:

```bash
cd instruments-service && .venv/bin/python3 \
    ../unified-trading-pm/cursor-configs/skills/gate-evaluation/scripts/evaluate_gates.py --verbose
```

See this skill's build-out todo (`cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md` item 10) for the
recorded output of this first run.

## Codex SSOTs

- `/codex/02-data/honest-coverage-model.md` — the coverage.json schema + denominator formula B1/B8/B16 reuse
- `/plans/active/data_pipeline_completion_2026_08_21.md` — the register this skill evaluates; SSOT for every gate's
  full bar text (this skill's own `bar` field is a concise paraphrase, not the full prose)
- `cursor-configs/skills/honest-coverage-dump/SKILL.md` — sibling skill, shared `coverage.json` read path
- `cursor-configs/skills/readiness-state-dump/SKILL.md` — sibling skill, the shape this skill mirrors
- `/codex/12-agent-workflow/measurement-claims-discipline.md` — why `unverified` beats a fabricated PASS/FAIL
