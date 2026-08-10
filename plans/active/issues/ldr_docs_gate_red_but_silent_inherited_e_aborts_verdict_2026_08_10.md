---
doc_type: issue
title:
  ldr-docs-gate red for 10+ hours with zero Slack pages — inherited `-e` aborts the gate step before it writes
  `verdict=red`, skipping every notify/escalate job
summary: >-
  `ldr-docs-gate.yml`'s "Corpus frontmatter check + per-file attribution" step runs under GitHub Actions' default shell
  `bash --noprofile --norc -e -o pipefail`. The step's own `set -uo pipefail` does NOT clear that inherited `-e`, so
  when `check_frontmatter_schema.py` exits non-zero the step dies AT the `OUT="$(...)"` capture — before `RC=$?`, before
  `echo "$OUT"`, and before the `{ echo "verdict=..."; ... } >> "$GITHUB_OUTPUT"` block. `verdict` is therefore never
  written on exactly the runs where it matters. All three downstream jobs key on `needs.frontmatter-gate.outputs.verdict
  == 'red'` (`notify-broken-docs`, `escalate-plan-health`, and the RESOLVED bookend), so every one of them silently
  skips: the gate is RED and the channel is SILENT. Measured 2026-08-10 during a /ci-reconcile sweep: 10+ consecutive
  hourly runs failed from 2026-08-09T22:07Z onward, each emitting zero stdout and zero Slack. The failure was invisible
  to a Slack-driven sweep and was only caught by enumerating every standing monitor's live run conclusion directly.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci, ci-alerting, ldr-docs-gate, silent-failure, alert-accuracy, live-incident]
related:
  - /plans/active/issues/na_corpus_ratchet_diff_base_vs_lagging_main_deadlocks_promotion_2026_08_10.md
  - /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md
  - /plans/active/cross_cutting_closeout_observability_and_monitoring_2026_08_09.md
created: 2026-08-10
author: /ci-reconcile (interactive, slot-2·laptop)
parent_epic: infrastructure_master
priority: P1
source: >-
  /ci-reconcile § 0b standing-monitor sweep, 2026-08-10 — `ldr-docs-gate` was the one red monitor of 23, and had posted
  nothing to #ci-failures in the entire sweep window.
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-infra
depends_on: []
locked_by:
supersedes:
superseded_by:
resolved_by: ""
last_updated: 2026-08-10
context_scope:
  [
    unified-trading-pm/.github/workflows/ldr-docs-gate.yml,
    unified-trading-pm/scripts/plan-hygiene/check_frontmatter_schema.py,
    unified-trading-pm/codex/04-architecture/ci-alerting.md,
  ]
---

# A red `ldr-docs-gate` that pages nobody

## Evidence

- `gh run list --workflow=ldr-docs-gate.yml --limit 10` → **10/10 `failure`**, hourly, 2026-08-09T22:07:11Z through
  2026-08-10T07:31:53Z (still red at time of writing).
- Job breakdown on run `31366227686`: `Doc frontmatter gate (LDR) :: failure`, then `escalate-plan-health :: skipped`,
  `notify-broken-docs :: skipped`, `Slack — ldr-docs-gate RESOLVED :: skipped`.
- Raw step log between `##[endgroup]` and `##[error]Process completed with exit code 1` is **empty** — the step produced
  no stdout at all, which is impossible if it had reached its own `echo "$OUT"`.
- Nothing from `ldr-docs-gate` appears in `#ci-failures` for the window.

## Root cause

The step body opens with `set -uo pipefail` — `u` and `o`, deliberately **not** `e`. But the shell GitHub launches it
with is already `bash --noprofile --norc -e -o pipefail`, and `set -uo pipefail` does not turn `-e` off. So the
inherited `-e` is live for the whole step, and `OUT="$(... check_frontmatter_schema.py ...)"` is a simple assignment
whose exit status is the substitution's — non-zero on a red corpus — which terminates the step immediately.

The workflow's existing comment at the `if: always()` guard shows the author had already reasoned about `-e` skipping
later _steps_; the gap is that `-e` also aborts _inside_ this step, upstream of the `$GITHUB_OUTPUT` write that every
downstream notifier depends on.

**This is a general trap, not a one-off**: the `set -uo pipefail` + `OUT="$(cmd)"` + `RC=$?` idiom is silently broken in
any GH Actions `run:` block, and it fails closed-and-quiet precisely when the checker reports a problem.

## What shipped (2026-08-10)

`set +e` added immediately before the capture in `.github/workflows/ldr-docs-gate.yml`, with a comment stating why it is
required rather than redundant. `-e` is deliberately left off for the remainder of the step (matching the author's
original `set -uo pipefail` intent) — restoring it would abort the attribution loop, whose `grep` legitimately exits 1
when the violation list is empty.

## Todos

- [x] ✅ [BACKEND] P1. **The gate's redness was a FALSE POSITIVE, root-caused once the signal came back.** With `set +e`
      live, a `--ref live-defi-rollout` dispatch finally emitted the excerpt: every violation was a
      `related:`/`context_scope:` citation of a SIBLING-REPO doc — seven `instruments-service/docs/*.md` files
      (ADAPTER_ARCHITECTURE, CEFI/DEFI/PREDICTION/SPORTS/TRADFI_INSTRUMENTS, SETUP_GUIDE) plus
      `market-tick-data-service/QUALITY_GATE_BYPASS_AUDIT.md`. **All seven instruments-service docs exist and are
      tracked in git.** `docspec.py`'s resolution step 5 looks for sibling repos at `pm_root.parent`, but
      `ldr-docs-gate.yml`'s job clones ONLY PM — so with no siblings on disk, every real cross-repo citation fell
      through to `HARD: does not exist`. Fail-UNSAFE, exactly like the `DIFF_BASE_REF` class: when the thing you would
      compare against is absent, it must degrade to "cannot verify", never to "violation". FIXED 2026-08-10
      (`scripts/docs/docspec.py`): a citation whose first segment names a repo in `workspace-manifest.json` but whose
      directory is not checked out is SKIPPED as unverifiable; if the sibling IS checked out and the file genuinely is
      not there, it still flags. Membership comes from the manifest (26 repos, dict-keyed) rather than "any unrecognised
      first segment", so a typo'd PM-internal path (`plns/foo.md`) is still a real violation. The full-QG path clones
      siblings and still checks these for real, so no coverage is lost. Verified: local full corpus still 2022 docs /
      zero violations; simulated PM-only checkout skips the two real cross-repo citations and still flags the typo.
- [ ] [BACKEND] P2. `market-tick-data-service/QUALITY_GATE_BYPASS_AUDIT.md` is cited by
      `/plans/active/issues/mtds_type_ignore_ratchet_blocks_prek_intel_mac_fix_2026_08_03.md` but exists only as an
      UNTRACKED local file in at least one slot checkout — so it is dead for everyone else and will still flag once MTDS
      is checked out alongside PM. Either commit it in market-tick-data-service or drop the citation. Repo:
      market-tick-data-service / unified-trading-pm.
- [ ] [BACKEND] P2. **A `workflow_dispatch`/`schedule` workflow runs the file from the DEFAULT branch (main), not the
      checked-out ref** — so this doc's own `set +e` fix was inert for every scheduled run the moment it landed on LDR,
      and stays inert until promotion carries it to main. That is a circular dependency: the fix for a silent-alert bug
      is gated behind the promotion it exists to help unblock. Any future fix to a scheduled workflow's own YAML has the
      same property. Document it in `/codex/08-workflows/ci-cd-flow.md` next to the existing "a scheduled/push workflow
      fires ONLY from the DEFAULT branch" line, and note the `gh workflow run <wf> --ref <branch>` escape hatch used to
      verify this one. Repo: unified-trading-pm.
- [ ] [BACKEND] P2. **Sweep the fleet for the same `-e` trap.** Grep every workflow for a `run:` block that sets
      `-uo pipefail` (without `e`) and then captures a checker's output into a variable whose failure is meant to be
      handled by a following `RC=$?`: `rg -n 'set -uo pipefail' -A 4 .github/workflows/ | rg -B1 'RC=\$\?'`. Each hit is
      a monitor that fails closed-and-quiet the same way. Repo: unified-trading-pm (+ any per-repo copies).
- [ ] [BACKEND] P2. **A monitor whose failure path cannot page is a coverage hole, not just a bug.** Add a
      meta-assertion: any job that publishes a `verdict` output consumed by a notify job must emit that output on the
      failure path too (e.g. write `verdict=red` in a `trap`/`if: always()` step rather than inline in the gate step).
      Cross-reference `/codex/04-architecture/ci-alerting.md`'s dedup/read-back contract — this is the same class as a
      suppressed post, but caused upstream of the notifier rather than inside it. Repo: unified-trading-pm.

## Progress Log

- **2026-08-10 (/ci-reconcile, slot-2·laptop)** — Found during the § 0b standing-monitor enumeration; would not have
  been found from the Slack channel, since the defect's whole effect is the absence of a Slack message. Concrete support
  for this skill's own § 6 rule that silence is not evidence of health.
