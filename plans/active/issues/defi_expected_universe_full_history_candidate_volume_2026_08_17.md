---
doc_type: issue
title: DeFi --full-history expected-universe enumeration exceeds 100M candidates — cap/machine sizing genuinely unknown
summary: >-
  Three real production VM runs of enumerate_expected_universe.py --full-history --apply-write
  for asset_group=defi each hit the --max-writes-per-run halt-safety cap in turn (1M → 15M →
  100M), with no sign of leveling off — the true candidate count is unmeasured but exceeds
  100,000,001. Root cause is NOT a bug in per-instrument date-bounding (available_from is 100%
  populated with real dates) — it is that the defi catalog has grown to 78,802 instruments, 10x
  the "7,895" figure baked into launch-expected-universe-v2-vm.sh's own MACHINE_TYPE-sizing
  comment (now corrected in the same commit as this issue). The --full-history codepath's own
  code comment already flags it as "not implicated in the 2026-08-01 DeFi OOM — the daily cron
  never passes --full-history", i.e. genuinely untested at this scale.
status: blocked
nature: issue
asset_group: [defi]
stage: [data]
repos: [instruments-service, deployment-service]
scope: [engineer]
tags: [defi, expected-universe, honest-coverage, halt-safety, oom-risk, escalation]
related:
  [
    /plans/active/defi_satellite_ao_dispatch_batch16_2026_08_17.md,
    /plans/active/lst_rate_honest_coverage_2026_07_21.md,
  ]
created: "2026-08-17"
author: worker (slot-3, data_engineering craft)
assigned_vm: planning
parent_epic: defi_master
resolved_by:
source: >-
  Live execution of defi_satellite_ao_dispatch_batch16_2026_08_17.md todo "[IS] P1 Execute the
  LST catalogue + expected-universe v2 regen" — the operator-ruled (2026-08-12, reconfirmed
  2026-08-15) literal regen-script run.
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
last_updated: "2026-08-17"
locked_by:
locked_since:
---

# DeFi `--full-history` expected-universe enumeration exceeds 100M candidates

## What I found

Executing `instruments-service/scripts/enumerate_expected_universe.py --asset-group defi
--enumerator-version v2 --full-history --apply-write` against real prod infra (per the
2026-08-12 operator ruling requiring a literal regen-script run, not just invariant-test
confirmation) via `deployment-service/scripts/vm/launch-expected-universe-v2-vm.sh` (extended
this session with a `FULL_HISTORY=true` env passthrough — `deployment-service@28272cafd3`):

| Attempt | VM | Machine | `--max-writes-per-run` | Result | Time to halt (post manifest-load) |
|---|---|---|---|---|---|
| 1 | `expected-universe-v2-defi-20260817-054923` | e2-standard-16 (64GB) | 1,000,000 (default) | `EXIT_STATUS=5`, 1,000,001 candidates | ~1 min |
| 2 | `expected-universe-v2-defi-20260817-060458` | e2-standard-16 (64GB) | 15,000,000 | `EXIT_STATUS=5`, 15,000,001 candidates | ~4.75 min |
| 3 | `expected-universe-v2-defi-20260817-062508` | e2-highmem-16 (128GB) | 100,000,000 | `EXIT_STATUS=5`, 100,000,001 candidates | ~25 min |

Each attempt reloads the manifest present-set from scratch (~7-11 min; `present=150,610,557`,
`captured=29,873,931` as of this run) before candidate generation even starts, and the
`--full-history` codepath (`enumerate_expected_universe.py` main(), the `if not full_history:`
branch's else-arm) drains the FULL per-day candidate generator into one in-memory Python list
before range-encoding — it is NOT chunked/streamed the way the bounded-window daily-cron path is
(that streaming fix, `V2_STREAM_CHUNK_SIZE`, was built specifically to fix the 2026-08-01 DeFi
OOM, but the code's own comment states the full-history branch was never exercised by that
incident and is untested at scale: "Not implicated in the 2026-08-01 DeFi OOM — the daily cron
never passes --full-history").

**Root-cause check performed** (to rule out a per-instrument date-bounding bug before assuming
this volume is "just how big defi is"): downloaded and inspected the live
`gs://instruments-store-defi-prd-central-element-323112/prod/catalog.parquet` directly.
`available_from` is populated on **100% of 78,802 rows** (zero nulls) with a real date
distribution (2022-2026) — so per-instrument lifecycle-window narrowing IS working correctly, not
silently defaulting every pool to "since 2018". The volume is real, not a bounding bug.

**The actual stale assumption**: `launch-expected-universe-v2-vm.sh`'s own `MACHINE_TYPE`-sizing
comment said "defi is the largest at 7,895 instruments" (dated to whenever it was last measured).
The live catalog is now **78,802 rows** — a 10x undercount had been silently baked into every
sizing decision anyone made off that comment, including my own initial `MACHINE_TYPE=e2-standard-16`
choice for attempt 1/2. **Fixed in the same commit as this issue** (comment corrected, no other
launcher change).

## Why it matters

- The 2026-08-12/2026-08-15 operator ruling requires this literal regen run to close
  `defi_satellite_ao_dispatch_batch16_2026_08_17.md`'s `[IS] P1` todo (catalogue half already
  shipped `instruments-service@fd0d12a9`/regenerated 2026-08-15; only the
  `_index/expected_universe_ranges.parquet` companion — last real write 2026-07-03 — remains
  stale). That todo cannot honestly close until a run actually completes.
- Continuing to blindly multiply `--max-writes-per-run` (1M→15M→100M, each ~10-6x the last, each
  still insufficient) is now firmly in "guessing, not engineering" territory: each attempt costs
  real VM-minutes (13/17/29 min so far, escalating machine cost e2-standard-16→e2-highmem-16), and
  the NEXT guess (e.g. 300M-1B) risks a genuine OOM mid-`range_encode()` (which builds a groupby
  dict over the SAME already-materialized list, roughly doubling peak memory at the compaction
  step) rather than a clean halt-safety exit — a real OOM wastes the full run with zero
  diagnostic value, unlike the halt-safety path which at least reports the exact candidate count.
- This is the SAME code shape (unbounded full-history drain) that already caused the tracked
  `defi_v2_expected_universe_enumerator_oom_2026_08_01.md` 19-day OOM incident on the
  BOUNDED-window path before it was fixed with streaming — the `--full-history` branch was
  explicitly NOT covered by that fix and is not chunked at all.

## Recommended decision

Given the true candidate count is unmeasured but demonstrably >100,000,001 and climbing without
sign of a plateau, I recommend **one of**:

1. **(Preferred, cheapest)** Add streaming/chunked accumulation to the `--full-history` branch's
   candidate drain + `range_encode()` (mirror the `V2_STREAM_CHUNK_SIZE` fix already applied to
   the bounded-window path) — this is a real code change to `enumerate_expected_universe.py`,
   scoped to `instruments-service`, and removes the need to guess a cap at all. Not attempted in
   this session (out of a single P1 todo's scope; needs its own reviewed change).
2. **(Fallback, more $ but no code change)** One more attempt on a much larger machine
   (`e2-highmem-32`, 256GB) with `--max-writes-per-run` raised generously (e.g. 500,000,000) —
   accepts real OOM risk; if it OOMs, the ONLY signal recovered is "still not enough", another
   dead end with no candidate count learned (unlike halt-safety, which reports the count it hit).
3. **(Operator-decision)** Revisit whether the 2026-08-12 ruling's "must be a literal
   regen-script run" requirement can be satisfied by a narrower, still-correct scope for JUST the
   2 target denominator cells this todo actually needs
   (`(CHAINLINK-ETHEREUM, SPOT_PAIR, oracle_prices)` + `(AAVE, spot_asset, oracle_prices)`) —
   NOTE: `--data-types oracle_prices` narrowing was considered and REJECTED in this session
   because `_write_range_artifact`'s write is last-writer-wins over the WHOLE
   `_index/expected_universe_ranges.parquet` blob (not additive) — a narrower run would silently
   DROP every other data_type's previously-written range rows, a regression, not a safe shortcut.
   A genuinely safe narrower approach would need the write path to merge with the existing
   artifact instead of overwriting it (also a code change).

I have not picked one of these unilaterally — it's a genuine judgment call (accept more $ risk vs.
scope a code fix vs. revisit the ruling's literal-run requirement) that the operator/main agent
should weigh in on.

## Todos

- [ ] [OPERATOR] P1. Decide which of the 3 options above to pursue for closing
      `defi_satellite_ao_dispatch_batch16_2026_08_17.md`'s `[IS] P1` regen todo — see this issue's
      "Recommended decision" section for the tradeoffs. Repo: n/a (decision only).
- [ ] [IS] P2. If option 1 is chosen: add chunked/streaming accumulation to
      `enumerate_expected_universe.py`'s `--full-history` branch (mirror
      `_stream_write_v2_absent_rows`'s `V2_STREAM_CHUNK_SIZE` pattern, adapted for
      `range_encode()`'s need to see the full per-key day-set before compacting — likely needs a
      per-key incremental range-merge instead of a single upfront `range_encode(v2_absent)` call
      over the whole drained list). Repo: instruments-service. Done when: a defi
      `--full-history --apply-write` run completes without needing any `--max-writes-per-run`
      override, verified against the live 78,802-row catalog.
- [ ] [SCRIPT] P3. Audit every OTHER asset_group's `--full-history` viability under the same
      unbounded-drain code shape (cefi/tradfi/prediction/sports) before anyone else hits this same
      wall blind — sports in particular is flagged elsewhere
      (`asia_northeast1_c_spot_preemption_storm_2026_08_04.md`) as having a 448K+-instrument
      catalog, likely an even worse candidate-volume case. Repo: instruments-service. Done when:
      each asset_group's live catalog row count is measured and compared against its
      `--full-history` feasibility, findings folded into this issue or a fresh one per
      asset_group.

## Progress Log

- **2026-08-17 (worker, slot-3, data_engineering craft)**: filed after 3 real production VM
  attempts (evidence table above) all hit the halt-safety cap; root-cause-checked and ruled out a
  per-instrument date-bounding bug (available_from 100% populated); found + fixed the stale
  "7,895 instruments" launcher comment (actual: 78,802) in the same commit. Not resolving further
  autonomously — this is a genuine judgment call per the "Recommended decision" section, escalated
  via `/blocked` on the same turn.
