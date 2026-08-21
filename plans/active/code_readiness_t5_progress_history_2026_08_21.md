---
doc_type: plan
title: Code readiness T5 — progress history (lessons carried forward)
summary: >-
  Pure historical record, split out of code_readiness_t5_readiness_observability_presentations_2026_08_19.md when
  the parent hit its 1000-line hard cap (2026-08-21). Carries the "Lessons carried forward (2026-08-20)" section
  verbatim. No open todos live here — the parent plan's Todos section is the live, authoritative list; this doc
  exists so the audit trail survives without re-inflating the active plan.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [code-readiness, tranche-5, history]
related: [/plans/active/code_readiness_t5_readiness_observability_presentations_2026_08_19.md, /plans/epics/system_readiness_master.md]
created: 2026-08-21
last_updated: 2026-08-21
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
locked_by:
locked_since:
context_scope: [/plans/active/code_readiness_t5_readiness_observability_presentations_2026_08_19.md]
supersedes:
superseded_by:
depends_on:
source: >-
  Split from the T5 tranche plan 2026-08-21 to satisfy the plan line cap while folding in the walkthrough-feedback
  pointer todo.
assigned_role: project_management
effort: low
drift_direction: advance-code
---

# Code readiness T5 — progress history

## Lessons carried forward (2026-08-20)

- **`bash cmd 2>&1 | tee LOG | tail -N` silently discards `cmd`'s real exit code** — the pipeline returns `tail`'s
  status. Confirmed live: `false | tee x | tail -5; echo $?` → `0`. This explains most of this session's own
  "exited with code 0 but the banner said FAILED" confusion, including in `quickmerge_exit_zero_on_failed_regate_
  and_silent_directory_files_2026_08_20.md`'s own Defect 1 evidence — re-measure with `${PIPESTATUS[0]}` before
  trusting a piped exit code again.
- **A diagnostic grep pattern is never exhaustive.** `ruff format --check` fails with `Would reformat: <path>`,
  matching neither `❌` nor `FAILED`/`ERROR`/`E `. When a "REAL failure" banner fires with no visible evidence,
  run each formatter/linter standalone against the exact files being shipped rather than trusting a keyword grep
  over the full log a second time.
- **Extending an existing check's dimensionality surfaces latent gaps in how it handles missing data.** Adding
  MANUAL as a 4th mode wasn't itself risky, but it immediately exposed `execution_instruction()` conflating
  "probe measured none" with "probe never had this field at all" — a real overclaim (`not_ready` instead of
  `unverified`) that existed for the 3 original modes too, just never triggered because every mode DID have a
  probe field. Adding an axis is a free correctness test for the axes that already existed.
- **A stash-quarantine collision is recoverable if the diff is a clean superset** — verified via
  `diff stash-version current-version` showing ONLY your own additions missing, nothing else different, before
  restoring. Don't restore blind even when you're confident; the check costs one command.
- **SHA ancestry doesn't survive a squash-style LDR→main promote** — `git merge-base --is-ancestor <sha> origin/main`
  can report "not an ancestor" for a fix that genuinely IS live, because "Option-B direct" promotes rewrite history.
  Content-diff the actual file against the target ref instead; that's what settled the `dp_cron_did_not_fire`
  serving-revision question this session, not ancestry.
- **A large-corpus bookkeeping triage parallelizes safely as read-only fan-out + serial human apply.** 15 sub-agents
  (3 waves of ≤5) each read ~20-25 docs in full and reported proposed old/new diffs — none edited or shipped. This
  let the expensive part (read + cross-check every doc) run in parallel on a live shared checkout without any
  concurrent-write collision risk, while I stayed the sole writer/shipper. Yield was consistently low (~24 real
  fixes across 352 docs) because this corpus already runs recurring audit skills — that's the correct outcome, not
  a wasted pass; the value was catching the ~24 genuine misses those recurring audits don't check for.
- **Even a pure checkbox-flip can trip `check_line_caps.sh` if the file was already over cap before you touched
  it** — the fix is never "shrink my edit," it's recognizing a pre-existing structural blocker and routing around
  it (revert, track the specific fix content as its own todo so it isn't lost, don't force through the gate).
- **Re-run the gate after editing evidence text, not just before shipping** — citing a regex pattern inside
  backticks in `ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md`'s evidence tripped the exact
  prosewrap-padding bug that same doc tracks. Caught by re-running `check_prosewrap_padding.sh` standalone before
  the ship attempt, not by the ship gate itself catching it first.
