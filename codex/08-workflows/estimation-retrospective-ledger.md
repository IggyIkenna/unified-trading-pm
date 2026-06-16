---
scope: [engineer, admin]
---

# Estimation Retrospective Ledger

> Companion to [estimation-calibration.md](estimation-calibration.md). Every plan archive adds a row. When 8+ rows land
> for a given class with median ratio drifting more than ±20% from 1.0, propose an updated multiplier in a
> `docs(codex):` PR + the calibration SSOT.
>
> **Actual** = wall-clock AI-days from first commit on the plan to the last logical-unit commit, in continuous working
> days (skip weekends, exclude calendar-bound waits).
>
> **Ratio** = actual / calibrated. Above 1.0 = underestimated even after calibration; below 1.0 = room to compress.

---

## Seed entries (2026-05-11 codification)

These are the empirical observations that motivated the calibration framework. Re-derived from memory + commit history;
ratios are approximate but defensible.

| Plan                                                                           | Class    | Baseline | Calibrated | Actual | Ratio | Notes                                                                                                                                                                                                                                                                                                                 |
| ------------------------------------------------------------------------------ | -------- | -------- | ---------- | ------ | ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `code_freeze_migrate_backfill_sequencing_2026_05_10` (master write only)       | design   | 4        | 2.4        | 1      | 0.42  | Master-plan artefact + 8 cross-plan banners shipped in 1 session (PM@738fe86d + PM@1b9e6451). Phase execution is separate scope.                                                                                                                                                                                      |
| Tab 4 AWS migration close-out (work_split_2026_05_08_ikenna)                   | infra    | 6        | 4.8        | 1.5    | 0.31  | 10 buckets created + STS migration kicked + cloud-agnostic governance + UTL bucket_naming SSOT. 3 parallel sub-agents fanned out artefact-only; parent serialised commits.                                                                                                                                            |
| Writegate Wave 4 slice (a) — service-output emission policy floor              | design   | 4        | 2.4        | 1      | 0.42  | UAC 4-member StrEnum + UTL emitter + per-(service, output_data_type) seed dict + QG step + 2-service POC. 1 session.                                                                                                                                                                                                  |
| EPICS layer restructure (7 May-23 epics + 9 moved domain masters)              | refactor | 2        | 0.8        | 1      | 1.25  | No upfront estimate; reverse-engineered. Above-1.0 ratio because filename rename across 16 files + frontmatter alignment + cross-link audit took the full session despite being mechanical. Suggests `refactor` 0.4× may be too aggressive for filename-rename work; investigate after 3+ more refactor entries land. |
| CLAUDE.md trim sweep + SUB_AGENT_MANDATORY_RULES.md split (2026-05-11)         | refactor | 2        | 0.8        | 1.5    | 1.88  | 211KB→58KB CLAUDE.md trim + lean SUB_AGENT_MANDATORY_RULES.md write + per-repo symlink propagation + foot-gun #4 mid-cycle (rebase conflict + revert + re-push). Above-1.0 ratio driven by the foot-gun #4 incident, not the work itself. Excluding foot-gun rework: ~0.6 actual = 0.75 ratio.                        |
| Plan-link fix sweep (2026-05-11, unblock 10 repos' QG validators)              | refactor | 1        | 0.4        | 0.5    | 1.25  | 8 broken markdown refs across 7 plan files. Above-1.0 because foot-gun #4 caused first commit to land with 1 of 8 fixes; required re-stash + re-edit cycle. Excluding foot-gun rework: ~0.25 actual = 0.63 ratio.                                                                                                     |
| Cluster validation primitive + VIX 15m source layering (2026-05-06)            | design   | 3        | 1.8        | 1      | 0.56  | UTL `ClusterCoverageError` + `record_captured` kwargs + UAC VIX coverage constants + MTDS Yahoo route. 4 commits in 1 session.                                                                                                                                                                                        |
| MTDS parallelization fix (UTL ParallelPerSymbolRunner + 12 tests) (2026-05-07) | design   | 3        | 1.8        | 1      | 0.56  | Sequential→16-way parallel with shard-level isolation; atomicity preserved. 1 session.                                                                                                                                                                                                                                |

**Median ratios so far** (n=8):

- `design` (n=4): 0.42, 0.42, 0.56, 0.56 → **median 0.49**. Calibrated multiplier 0.6× still slightly conservative;
  track 4 more before adjusting.
- `refactor` (n=3): 1.25, 1.88, 1.25 → **median 1.25**. Calibrated multiplier 0.4× is _too aggressive_ for refactors
  that touch many files / have foot-gun risk. Consider raising to 0.6× after 5+ more refactor entries — but note 2 of 3
  above include foot-gun #4 rework, so the underlying rate may be closer to 0.6× on a foot-gun-clean run.
- `infra` (n=1): 0.31 → too few entries; track 4 more before adjusting.
- `brand-new` (n=0): no entries.
- `research` (n=0): no entries.

---

## Active entries (plans currently in flight; row finalised on archive)

_(Empty as of 2026-05-11. Owner agents append a row when the plan archives.)_

---

## Workspace-wide throughput observations

Separate from per-plan ratios — measures **delivered cal AI-days/day across the whole workspace**, derived from commit
counts × commit-type weighting. Feeds risk projections (May-23 cutover, capacity-vs-scope math).

**Commit-to-cal-AI-day weights** (apply to each commit; sum across day):

| Commit class             | Weight | Examples                                                         |
| ------------------------ | ------ | ---------------------------------------------------------------- |
| Substantive ship         | 1.5    | Master plan write, codex doc, multi-phase architectural commit   |
| Service code             | 1.2    | UAC schema add, UTL helper, MTDS adapter, service implementation |
| Plan flip / banner sweep | 0.15   | Checkbox flip, cross-plan banner add, doc(plans) flip commit     |
| Coordination ping        | 0.05   | LEDGER update, slot ping, single-line work-split tweak           |
| Bot commit               | 0.0    | semver-rollout[bot] auto-version-bump, dependabot                |

### Observation log

| Date       | Workspace commits | Class-weighted cal AI-days | Per-side rate | Notes                                                                                                                                                                                                                    |
| ---------- | ----------------- | -------------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 2026-05-11 | 343               | **~130**                   | ~65/side      | Heavy session: CLAUDE.md trim + calibration framework codify + 56-plan sweep + 2 work-splits authored; multi-slot active. PM 286, UAC 22, UTL 7, MDPS 0, MTDS 3, instruments 2, features 4, deployment 8, ui 1, bot ~10. |

### Derived ceiling estimates

- **Measured sustained throughput (1 day, 2026-05-11)**: ~130 cal AI-days/day workspace (~65/side).
- **7-day average (2026-05-04→11, commit-rate-derived ~250/day × 0.4 weight)**: ~100 cal AI-days/day workspace
  (~50/side).
- **Theoretical ceiling (8 slots × 8-12 cal AI-days/slot/day at peak)**: ~160-200/day workspace (~80-100/side).
- **CLAUDE.md correction (PM@e50a21bb)**: ceiling cited as "~50/side" was the **7-day average measured rate**, not the
  ceiling. Corrected to "~65-75 measured, ~80-100 theoretical."

### Track-forward

Append a row per "interesting" day going forward (heavy activity, density-push cycles, foot-gun-heavy days, freeze-gate
days). When 7+ rows exist, recompute the 7-day average + update the "measured sustained" line in the codex SSOT §
Workspace ceiling sanity check.

---

## Ledger governance

- **Append-only** during a calibration cycle. Once 8+ rows land for a class, a `docs(codex):` PR may compress duplicate
  entries from a single multi-phase plan into one row + propose an updated multiplier in
  [estimation-calibration.md](estimation-calibration.md).
- **Don't backfill historical plans** unless you authored them and remember the actual scope — reverse-engineered ratios
  become noise that drowns the signal.
- **Foot-gun annotations**: if `Actual` was inflated by a known foot-gun (#1-#4), state both numbers in `Notes`
  ("Excluding foot-gun rework: ~X actual = Y ratio") so the underlying-work ratio stays visible.
