---
doc_type: issue
title:
  cassette-drift-check has never run its check since the script was relocated out of PM — it calls a deleted path,
  swallows the failure via `|| drift_detected=true`, and exits GREEN; flipping it to self-hosted would additionally
  ACTIVATE a shared-slot-venv poisoning that its stale 3.12 pin was accidentally preventing
summary: >
  `cassette-drift-check.yml` runs `python unified-trading-pm/scripts/dev/detect_cassette_drift.py` (:73). That file was
  DELETED from PM by `c2e58f200` ("chore(testing): relocate mock infrastructure scripts to UIC/UAC packages (Phase 1
  B3)", -293 lines) and now lives at `unified-api-contracts/unified_api_contracts/testing/detect_cassette_drift.py`. The
  workflow was never repointed. python therefore exits non-zero every run — but the step is `python … && echo
  drift_detected=false || { echo drift_detected=true; }`, so the `||` branch succeeds, the STEP exits 0, and the JOB
  reports **success**. Verified: absent on both `origin/main` and `origin/live-defi-rollout`; last 3 scheduled runs all
  `success`. So the nightly cassette-drift check has not actually checked anything since the relocation — it reports
  `drift_detected=true` on a missing file, not on real drift. SECOND, INDEPENDENT DEFECT (this is why the CI-cost flip
  skipped it): the install step is `uv pip install -e . --system 2>/dev/null || uv pip install pydantic pyyaml --system`
  (:62-63) against UAC, whose `requires-python = ">=3.13,<3.14"`. The workflow pins `actions/setup-python` to **3.12**
  (:54), so `-e .` ALWAYS fails and silently takes the fallback — confirmed in the 2026-07-17 log (`Successfully
  installed uv-0.11.29` … `|| uv pip install pydantic pyyaml --system` … `Installed 6 packages`). On the self-hosted
  glue pool `python3` IS the SHARED slot venv on 3.13, so `-e . --system` would SUCCEED and install an EDITABLE UAC into
  that shared venv pointing at a `_work` directory the JIT runner deletes after the job — leaving every subsequent job
  on that runner with a dangling editable install. The stale, wrong 3.12 pin is the only thing currently preventing
  that. Hence: do not flip until repointed + isolated.
status: resolved
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, unified-api-contracts]
scope: [engineer, admin]
tags:
  [ci-cd, cassette-drift, silent-failure, green-but-wrong, self-hosted-runners, slot-venv, shared-state, backstop-rot]
related:
  [
    /plans/archive/2026_07/github_actions_ci_cost_reduction_2026_07_15.md,
    /plans/active/issues/digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md,
    /plans/archive/issues/reconcile_release_tags_dead_since_d13_git_tag_migration_2026_07_17.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-17
parent_epic: deployment_and_user_management_master
priority: P1
source:
  github_actions_ci_cost_reduction_2026_07_15 STEP 2 batch 3, slot 1, 2026-07-17 — found while checking whether the
  "3.12 pin" caveat was load-bearing before flipping this workflow to the glue pool
assigned_vm: NA
execution_scope: local-only
assigned_role: devops
drift_direction: advance-code
last_updated: 2026-07-17
locked_by:
resolved_by: all 3 fixes + self-hosted-runner flip shipped, verified 2026-07-26 by /plan-reconcile ci
depends_on: []
---

> **🟢 RESOLVED 2026-07-17 (verified 2026-07-26) -- all fixes shipped and reachability-checked live. Remaining
> operator-scope items tracked in github_actions_operator_gated_followups_2026_07_17.md. Archived per
> issue-doc-lifecycle.**

# cassette-drift-check: green every night, has not checked anything since the relocation

> ## ✅ BOTH DEFECTS FIXED IN CODE 2026-07-17 — this doc's "Fix (all three together, or not at all)" is DONE
>
> _(Verified 2026-07-26 by `/plan-reconcile ci` — read the live workflow, ran the reachability checks; not inferred from
> another doc.)_
>
> The workflow was fixed **the same day this doc was filed**, and the doc was never updated. Both fix commits are
> verified ancestors of `origin/live-defi-rollout` (`git merge-base --is-ancestor`):
>
> | this doc's prescribed fix                                         | shipped                                                                                                                                                    |
> | ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
> | 1. **Repoint** at the relocated package module                    | ✅ `cassette-drift-check.yml:96` → `-m unified_api_contracts.testing.detect_cassette_drift` — `unified-trading-pm@f339ce5e8`                               |
> | 2. **Isolate the install** (never `--system`; throwaway venv)     | ✅ `:76` → `uv pip install -e ./unified-api-contracts --python "${RUNNER_TEMP}/uac/bin/python"`; the `\|\| pydantic pyyaml` fallback is gone — same commit |
> | 3. **Stop swallowing the exit code** (3 distinct states)          | ✅ `:100-102` → `0)` no drift · `1)` drift · `*) ::error:: … exit "${rc}"` — same commit                                                                   |
> | "Then drop `setup-python` + `pip install uv` and flip `runs-on:`" | ✅ `:34` `runs-on: [self-hosted, glue]`, `:51` records both steps removed — `unified-trading-pm@e9d02e5d6` ("37/37 movers now self-hosted")                |
>
> That last commit also **retires Defect 2's premise**: this doc says cassette-drift-check "is the 1 of 37 deliberately
> NOT flipped in STEP 2 batch 3" — it was flipped 6 minutes after the fix, making it 37/37. The shared-venv poisoning
> trap the stale 3.12 pin was accidentally preventing is now prevented _deliberately_ by the per-run `RUNNER_TEMP` venv.
>
> **Status deliberately left `open`.** Two operator-scope calls remain and are tracked as an open `[REVIEW] P0` in
> [/plans/active/github_actions_operator_gated_followups_2026_07_17.md](/plans/active/github_actions_operator_gated_followups_2026_07_17.md):
> (a) closing the 52 false `[Cassette Drift]` issues in `unified-api-contracts`, and (b) the detector's cassette→model
> matching being a filename-stem lottery. Per this corpus's convention (see the 2026-07-12 annotation in
> [/plans/archive/issues/aws_codebuild_pr_approval_status_noise_2026_06_25.md](/plans/archive/issues/aws_codebuild_pr_approval_status_noise_2026_06_25.md)),
> _"closing/resolving is an operator-scope call, not a mechanical doc-sync"_.
>
> **✅ EVIDENCED 2026-08-02** (`unified-api-contracts@7450e744`, confirmed ancestor of `origin/live-defi-rollout`): this
> doc's own "Negative test that must pass after the fix" is now covered —
> `unified-api-contracts/tests/unit/test_detect_cassette_drift.py` exercises `detect_cassette_drift.main()` directly for
> the three states the workflow's `case "${rc}" in 0) … 1) … *) …` branches on: a genuinely-empty cassette dir exits 0,
> a fabricated genuine-schema-drift cassette exits 1, and a nonexistent `--cassette-dir` (the broken-invocation case
> that used to silently report as drift) exits 2 and does not write a report. The two operator-scope items above remain
> open and unaffected by this.

## Defect 1 — it calls a file that does not exist, and hides it

`.github/workflows/cassette-drift-check.yml:73`:

```bash
python unified-trading-pm/scripts/dev/detect_cassette_drift.py \
  --cassette-dir unified-api-contracts \
  --output-json drift_report.json \
&& echo "drift_detected=false" >> "$GITHUB_OUTPUT" \
|| { echo "drift_detected=true" >> "$GITHUB_OUTPUT"; }
```

`scripts/dev/detect_cassette_drift.py` is **absent from `origin/main` and `origin/live-defi-rollout`**. It was removed
by:

```
2062afb5f  feat: add nightly cassette drift detection workflow and script (H5.1)   <- added
c2e58f200  chore(testing): relocate mock infrastructure scripts to UIC/UAC packages (Phase 1 B3)
           scripts/dev/detect_cassette_drift.py | 293 ---------------          <- deleted
```

It now lives at `unified-api-contracts/unified_api_contracts/testing/detect_cassette_drift.py`. The workflow was never
repointed.

**Why it is green anyway**: the `|| { … }` branch runs when python fails, and IT succeeds, so the step's exit status
is 0. A missing interpreter target is indistinguishable, from the outside, from "checked and found drift". Last three
scheduled runs: `success`, `success`, `success`.

This is the same failure class as the two sibling findings — an error rendered as a benign/actionable result — except
here the error is rendered as a **positive detection**, which is worse than silence: `drift_detected=true` is what the
"Create GitHub Issue on drift" step (:89-90) keys on.

## Defect 2 — the stale 3.12 pin is load-bearing BY ACCIDENT (this blocks the CI-cost flip)

```yaml
- uses: actions/setup-python@v6
  with:
    python-version: "3.12" # <- contradicts UAC's requires-python = ">=3.13,<3.14"
- run: pip install uv
- run: |
    cd unified-api-contracts
    uv pip install -e . --system 2>/dev/null \
      || uv pip install pydantic pyyaml --system
```

UAC declares `requires-python = ">=3.13,<3.14"`, so on 3.12 `uv pip install -e .` **cannot** resolve. It fails,
`2>/dev/null` hides it, and the fallback installs only `pydantic pyyaml`. Confirmed in the 2026-07-17 03:10 run log:

```
python-version: 3.12
Successfully installed uv-0.11.29
  || uv pip install pydantic pyyaml --system
Resolved 6 packages in 961ms   …   Installed 6 packages in 138ms
```

**The trap for the self-hosted migration**: on the glue pool the runner's `python3` IS the **shared slot venv** on
**3.13** (`scripts/self-hosted-runners/slot-venv-requirements.txt` — "THIS VENV IS SHARED, MUTABLE STATE"). There,
`uv pip install -e . --system` would **succeed** and install an **editable** UAC into that shared venv whose source path
is `…/_work/…/unified-api-contracts` — a directory the JIT-ephemeral runner **deletes when the job ends**. Every later
job on that runner would inherit a dangling editable install.

So the wrong, stale 3.12 pin is currently the ONLY thing preventing shared-venv poisoning. Flipping `runs-on` without
fixing the install would ACTIVATE a bug that the breakage was masking. `cassette-drift-check` is therefore the 1 of 37
deliberately NOT flipped in STEP 2 batch 3.

## Fix (all three together, or not at all)

1. **Repoint** at the relocated module — it is a package module now, not a loose script:
   `python -m unified_api_contracts.testing.detect_cassette_drift …`.
2. **Isolate the install** — never `--system` on a self-hosted runner. Build a throwaway venv per run and install into
   it explicitly: `uv venv .venv --python 3.13 && uv pip install -e . --python .venv/bin/python`, then invoke that
   interpreter. This also makes the step honest: `-e .` is now REQUIRED (the module lives inside UAC), so the
   `|| pydantic pyyaml` fallback must be DELETED — it can no longer satisfy the import and would only re-hide a failure.
3. **Stop swallowing the exit code.** Distinguish the three states: exit 0 → no drift; exit 1 (the script's real drift
   signal) → drift; any other exit / missing module → **fail the step loudly**. As written, "the tool is broken" and
   "drift found" produce the same output and the same GitHub issue.

Then drop `setup-python` and the `pip install uv` step (uv and the deps are pre-seeded — see
`slot-venv-requirements.txt`) and flip `runs-on` with the rest.

## Negative test that must pass after the fix

A genuine drift must still open the issue, and a genuinely-absent-drift run must still exit 0 — while a broken
invocation (bad path, unimportable module) must FAIL the job rather than report drift. Today all three are the same.
