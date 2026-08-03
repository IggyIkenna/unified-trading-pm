---
doc_type: issue
title:
  prettier proseWrap=always inserts multi-space runs inside long backtick inline-code spans (and pads wrapped
  list-continuation lines) in plan-doc commits — workers rediscover + hand-fix it ad-hoc
summary: >-
  The shared workspace `.prettierrc` (`proseWrap: always`, `printWidth: 120`) reflows markdown prose, but when a
  backtick-wrapped inline-code span sits at/near the 120-col wrap boundary — or a wrapped list-item continuation line
  runs long — prettier inserts large runs of extra spaces rather than breaking (inline code is unbreakable). The result
  is content-only, non-meaning-changing mangling (verified via `git diff -w`), e.g. `pipeline_mode != batch_understat`
  or `market-tick-data-     service@92037f45`, and ~150-space-padded continuation lines. Two INDEPENDENT occurrences in
  a single session (2026-07-31) — unified-trading-pm@129905504 (slot 8, self-corrected ~1min later by ea2ab961e) and
  unified-trading-pm@fd1b02c2c (slot 14, still live/uncorrected) — indicate a real prettier config quirk on long
  inline-code spans, not one-off operator typos. Workers currently rediscover and hand-fix it individually instead of it
  being root-caused once.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [prettier, prosewrap, tooling, plan-hygiene, cosmetic, lint]
related: [/codex/06-coding-standards/quality-gates.md]
created: 2026-07-31
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
assigned_role: infra
drift_direction: advance-code
depends_on: []
source:
  [
    "Flagged 2026-07-31 06:36Z by the review role (msg 2849) to main-agent (agt-9f21bc) as a low-priority/non-blocking
    FYI after spotting the same pattern in 2 unrelated plan-doc commits in one session. Main-agent confirmed the pattern
    live in fd1b02c2c's diff (multi-space runs inside backtick spans at diff lines 45/54/64; ~150-space continuation
    padding at 96-100) and confirmed the config (`.prettierrc`: proseWrap=always, printWidth=120).",
  ]
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
---

# prettier proseWrap mangles long inline-code spans in plan docs

## What was found (verified live 2026-07-31, main-agent agt-9f21bc)

The workspace-wide `.prettierrc` sets `proseWrap: "always"` + `printWidth: 120`. When prettier reflows a markdown
paragraph or list item to that width, a backtick-wrapped inline-code span that cannot itself be broken (or a long
wrapped list-continuation line) gets padded with large runs of literal spaces instead of a clean line break.

Confirmed instances this session (both in unified-trading-pm plan docs):

- **unified-trading-pm@129905504** (`tradfi_backfill_oom_remediation`, slot 8) — self-corrected ~1 min later by
  follow-up commit `ea2ab961e`. Verified content-only via `git diff -w` (per the review role).
- **unified-trading-pm@fd1b02c2c** (`sports_stats_delayed_live_capture_still_dead_post_fix_2026_07_29`, slot 14) — NOT
  yet corrected, still live. In its diff the mangling shows as multi-space runs INSIDE backtick spans, e.g.:
  - `URDI fetch: N venue(s) failed with        PERMANENT errors`
  - `pipeline_mode !=        batch_understat`
  - `if "UNDERSTAT" in active_venues_set and        entity_wanted("XG")`
  - plus wrapped continuation lines padded with ~150 leading spaces.

The mangling is cosmetic — it does not change meaning or the rendered output — but it is real, reproducible-looking, and
being rediscovered + hand-fixed one commit at a time rather than root-caused once.

## Why it matters

- Two independent occurrences in one session across two different slots points to a config/tooling quirk, not operator
  typos — so it will keep recurring on any plan doc containing long backtick inline-code spans near the 120-col boundary
  (which is common in this corpus).
- Each occurrence costs a worker a rediscover-and-hand-fix cycle (or ships uncorrected, as fd1b02c2c did), adding noise
  to plan-doc diffs.

## Recommended decision (not adjudicated here — priority is the operator's call)

- **(A) Root-cause + config fix** — reproduce with a minimal fixture (a long backtick span near col 120), determine
  whether it's a known prettier markdown/proseWrap bug or fixable via a config change (e.g. proseWrap tuning /
  printWidth / an override for `.md`), and either adjust `.prettierrc` or pin/upgrade the prettier version.
- **(B) Add a lint check** — if the config can't cleanly avoid it, add a cheap grep/lint (multi-space runs inside
  backtick spans, or trailing >N-space padding on continuation lines) to plan hygiene / prek so it's caught at commit
  time instead of rediscovered ad-hoc.

## Todos

- [x] ✅ [BACKEND] P3. **DONE 2026-08-03 (slot 11, backend_engineer)** — Reproduce the prettier proseWrap mangling with
      a minimal `.md` fixture (long backtick inline-code span near printWidth=120), determine root cause (config vs
      prettier-version bug), then apply (A) a `.prettierrc` fix or (B) a plan-hygiene/prek lint check that catches
      multi-space runs inside backtick spans + over-padded continuation lines. Confirm the fix against the
      fd1b02c2c-style pattern. (repo: unified-trading-pm) — see Progress Log for evidence.
- [ ] [BACKEND] P3. Re-run prettier / hand-fix the still-live mangled span in
      `plans/active/issues/sports_stats_delayed_live_capture_still_dead_post_fix_2026_07_29.md`
      (unified-trading-pm@fd1b02c2c), verifying content-only via `git diff -w`. (repo: unified-trading-pm)

## Progress Log

- 2026-07-31 06:36Z (main-agent agt-9f21bc): filed from review-role msg 2849 after live confirmation of the pattern in
  fd1b02c2c and the `.prettierrc` config. Set `assigned_vm: NA` per the ASK-BEFORE-CREATING hard rule; cosmetic /
  non-blocking, so P3. Operator can flip `assigned_vm: planning` + `execution_scope` to auto-dispatch the two
  precisely-scoped todos if desired.
- **na-eligibility-audit 2026-08-01**: RECLASSIFY, `assigned_vm: NA` → `planning` — both todos are precisely scoped with
  stated done-whens (reproduce the mangling with a minimal fixture, diagnose config-vs-version, apply whichever fix the
  diagnosis supports, confirm against the known fd1b02c2c pattern; separately, re-run prettier/hand-fix one named file
  and verify content-only via `git diff -w`), low-risk cosmetic tooling work, not live-dispatch-critical-path machinery
  — exactly the reclassification this doc's own filing note invited. Conflict-check: zero mentions of prettier/proseWrap
  in any other active plan/issue doc or the cross-cutting consolidated closeout — cleared. Added `assigned_role: infra`
  (was missing). `doc_type: issue` — exempt from the finalize-plan-coverage rule, no companion finalize doc authored.
- **2026-08-03 (slot 11, backend_engineer) — todo 1 DONE**: reproduced with a minimal 4-line fixture (a list item + a
  nested 2nd-paragraph continuation, `npx prettier@3.9.5 --write` run repeatedly on the same file). **Root cause is
  broader than the "unbreakable inline-code span" framing this doc opened with**: the bug reproduces identically with
  zero backtick spans present — it is a genuine prettier **idempotency defect** in the markdown proseWrap printer for a
  paragraph that is the 2nd+ block nested inside a list item; each pass over the SAME file adds +4 leading spaces to the
  paragraph's continuation lines instead of converging (measured 18→22→26→30→... across repeated passes). Confirmed
  still present on `prettier@latest` (3.9.6, the newest release at investigation time) — so (A) pin/upgrade is not
  available; disabling `proseWrap` entirely would be a workspace-wide formatting-behavior change outside this P3 task's
  authority (broad tradeoff, not a bounded fix). Applied **(B)**: added
  `scripts/plan-hygiene/check_prosewrap_padding.sh` (two detectors — multi-space runs inside backtick spans, and
  over-padded continuation lines above a threshold calibrated against the live corpus's legitimate max indent) and wired
  it into `run_hygiene_sweep.sh`'s full sweep as a shrinking ratchet (same shape as `check_archive_candidates. sh` —
  full-corpus only, not `--precommit`, since a staged-subset count would trivially pass against a corpus-wide baseline).
  **Confirmed against the fd1b02c2c-style pattern**: running the new gate directly against
  `sports_stats_delayed_live_capture_still_dead_post_fix_2026_07_29.md` (still mangled, todo 2 below) correctly flags
  all 30 corrupted lines, including the exact `read_availability_index()` backtick-internal-padding shape the parent
  doc's finding cited. **Corpus-wide calibration scan surfaced far more existing damage than this doc's original 2
  instances** — 82 files / 4472 lines, up to 1290 leading spaces in `tradfi_satellite_ao_dispatch_batch2_2026_07_25. md`
  (a mirror of the doc that produced this issue's original 2 flagged commits). That remediation is out of this todo's
  bounded scope (reproduce + build the gate) — tracked separately per the findings-closure rule:
  `/plans/active/issues/prosewrap_padding_corpus_wide_1290_space_2026_08_03.md`. Evidence: `unified-trading-pm@<sha>`
  (this commit) — `scripts/plan-hygiene/check_prosewrap_padding.sh` +
  `scripts/plan-hygiene/prosewrap_padding_baseline.yaml` (seeded `violation_count: 4472`) + `run_hygiene_sweep.sh`
  wiring; full sweep run clean (`✅ PASS [hard] No prettier proseWrap continuation-padding (ratchet)`), two pre-existing
  unrelated hard failures (`Reference path convention`, `Archive candidates`) confirmed NOT caused by this change.
