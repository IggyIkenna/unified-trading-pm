---
doc_type: plan
title: Scoped reference-path hygiene pass over plans/archive/ — finalize
summary: >-
  Gated closeout for plans_archive_reference_path_hygiene_2026_08_02.md — machine-held via depends_on + gate_on_depends
  until both of that plan's todos are done. Re-verifies the reference-path ratchet actually moved (check_reference_paths
  back at/below the pre-regression baseline: format 161, exist 901), confirms no AMBIGUOUS/UNRESOLVED entry was silently
  dropped, and archives this plan pair once confirmed.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, reference-paths, ratchet, mechanical, finalize]
related:
  [
    /plans/active/plans_archive_reference_path_hygiene_2026_08_02.md,
    /codex/11-project-management/cross-reference-path-convention.md,
  ]
created: 2026-08-02
last_updated: 2026-08-02
parent_epic: plan_hygiene_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.04
assigned_role: review
drift_direction: correct-codex
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [plans_archive_reference_path_hygiene_2026_08_02]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/plans_archive_reference_path_hygiene_2026_08_02.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched (`assigned_vm: planning`) plan needs a gated
  finalize plan; this one shipped without its pair, tripping `check_finalize_plan_coverage.py`'s ratchet (baseline 0,
  regression 1). Authored same-session to close the regression, mirroring the shape of existing finalize plans (e.g.
  ao_satellite_ao_dispatch_batch3_finalize_2026_07_31.md).
---

# Scoped reference-path hygiene pass over `plans/archive/` — finalize

> **Machine-gated on `/plans/active/plans_archive_reference_path_hygiene_2026_08_02.md`** (`depends_on` +
> `gate_on_depends: true`) — will not dispatch until both todos in that plan are `done`.

## Todos

- [x] ✅ [SCRIPT] P2. **Re-verify the ratchet actually moved, not just that the apply ran.** Re-run
      `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` (or the standalone `check_reference_paths` checker it wraps)
      and confirm format violations are back at/below the pre-regression baseline (161) and exist violations at/ below
      baseline (901) — the two numbers named in the source plan's own "Why this plan exists" section. If either is still
      above baseline, re-open a follow-up todo naming the specific still-violating files rather than closing this doc.
      **RESULT (slot-15, 2026-08-03): ratchet confirmed moved and holding.** Ran both the standalone checker
      (`python3 scripts/plan-hygiene/check_reference_paths.py`) and the full `run_hygiene_sweep.sh --ci` — live counts:
      format 81/81 ✅ (exact match to the current baseline, itself already ratcheted down from the source plan's own
      final todo), existence 87/87 ✅ (exact match). Both are far below the 161/901 pre-regression numbers cited in this
      todo's own text (those numbers predate the `dfdb0887` archive-scope-exclusion + the source plan's own further
      `--update-baseline` to 81/87 — current `reference_paths_baseline.yaml` reads
      `format_count: 81, existence_count:     87`, and live == baseline exactly, so no drift since the source plan's
      last verified state). The full sweep's "Reference path convention (/plans, /codex — ratchet)" hard check reported
      ✅ PASS. The sweep DID report 3 unrelated hard failures this session (prettier proseWrap-continuation-padding
      ratchet, `assigned_vm:NA` corpus size ratchet, Archive-candidates ratchet) — all out of this todo's scope
      (different ratchets, not reference-path); not chased here.
- [ ] [REVIEW] P2. **Spot-check the AMBIGUOUS/UNRESOLVED triage.** For each entry the source plan's todo 2 recorded as
      hand-disambiguated or genuinely-dangling, re-read the actual file to confirm the recorded disposition matches
      what's on disk now (a concurrent edit could have moved the target again). Done when every entry is confirmed, or
      any drift found is logged as a new todo naming the specific file.
- [ ] [PLAN] P2. **Archive both plans** once the two todos above confirm clean — standard 6-step archival ritual
      (banner, referrer repoint, inventory regeneration) per
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`.

## Progress Log

- **2026-08-03 (slot-15)** — Worked todo 1: re-ran the ratchet check both standalone (`check_reference_paths.py`) and
  via the full `run_hygiene_sweep.sh --ci`. Live format/existence counts (81/87) match the current baseline exactly,
  well below the 161/901 pre-regression numbers named in the todo. Confirmed no drift since the source plan's own
  last-verified state. See the todo's own RESULT note for detail. Next: todo 2 (spot-check the AMBIGUOUS/UNRESOLVED
  triage).
