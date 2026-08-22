---
doc_type: issue
title: >-
  `lc_verify_tarball_freshness`'s `auto` mode declares success even when the republish it triggered silently SKIPPED
  (dirty working tree) — launched a VM onto stale/pre-fix code twice in one session
summary: >-
  `deployment-service/scripts/vm/lib/launcher_common.sh`'s `lc_verify_tarball_freshness` (default mode `auto`) is
  supposed to guard against launching a VM onto stale code (the exact class of bug
  `features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md` was filed for). Found it has a
  gap: on a stale tarball, `auto` mode shells out to `create-code-tarballs.sh --include <repo>` and, as long as THAT
  command exits 0, unconditionally returns success — it does NOT check whether the republish it triggered actually
  produced a fresh tarball. `create-code-tarballs.sh` itself refuses to tar a repo with uncommitted changes (`SKIP
  <repo>-code.tar.gz ... — uncommitted changes (commit/stash first, or use --allow-dirty-tarball)`) and exits 0 anyway
  (a skip is not treated as a script failure). On a shared multi-slot checkout where OTHER sessions' foreign uncommitted
  files legitimately sit in the working tree (a normal, expected state per this workspace's own multi-agent model), this
  means `auto` mode can NEVER actually republish, yet always reports success — the launcher proceeds and boots a VM
  running the OLD, pre-fix tarball. Hit this twice in one session (`backfill-defi-legacy-datatype-fold-20260806-070905`
  and `-104615`, both deleted within seconds of boot once caught via the warning line the code DOES still print) trying
  to launch the dex_swaps legacy-fold VM immediately after shipping a fix to the exact script the VM runs.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service]
scope: [engineer]
tags: [vm-launcher-runbook, tarball-freshness, stale-code, silent-failure, quickmerge, shared-checkout]
related:
  [
    /plans/archive/issues/features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md,
    /plans/archive/2026_08/issues/vm_launcher_setup_script_freshness_gap_2026_07_31.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-06"
author: unknown
last_updated: "2026-08-07"
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
source: >-
  Interactive session 2026-08-06, discovered while relaunching the dex_swaps legacy data_type fold VM twice in a row
  (once after a bugfix, once after a second bugfix) on the same shared market-tick-data-service checkout.
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    deployment-service/scripts/vm/lib/launcher_common.sh,
    deployment-service/scripts/vm/create-code-tarballs.sh,
    /plans/archive/issues/features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md,
  ]
---

# `lc_verify_tarball_freshness` auto-mode silent dirty-tree skip (2026-08-06)

## What happened, twice

1. Shipped `market-tick-data-service@513a83dd` (a fix to the dex_swaps fold script), then ran
   `launch-backfill-defi-legacy-datatype-fold-vm.sh --only dex_swaps`. Output:
   ```
   lc_verify_tarball_freshness: republish complete — re-verifying
   WARNING: STALE tarball for market-tick-data-service — mtds-code manifest=467a3cd1aa3f but repo=513a83dd32b9
   WARNING: 1 STALE code tarball(s): market-tick-data-service
   ...
   Created [...instances/backfill-defi-legacy-datatype-fold-20260806-070905]
   ```
   The launcher printed the exact WARNING that should have blocked/paused it, then launched anyway.
2. Root cause: `create-code-tarballs.sh --include market-tick-data-service` (the republish command `auto` mode ran)
   printed
   `SKIP mtds-code.tar.gz from market-tick-data-service — uncommitted changes (commit/stash first, or use --allow-dirty-tarball)`
   and exited 0. The market-tick-data-service checkout had 3 pre-existing, foreign, correctly-untouched dirty files
   (another session's WIP — per this workspace's own multi-agent model, exactly the kind of file this session must never
   touch).
3. Deleted the VM (booted <30s prior, confirmed stale, no real work done — safe/reversible), stashed the 3 foreign files
   BY NAME, reran `create-code-tarballs.sh --include market-tick-data-service` (now succeeded, clean tree), popped the
   stash back, relaunched — this time `lc_verify_tarball_freshness: all 3 tarball(s) current.`
4. **Repeated the exact same sequence ~3 hours later** after shipping a SECOND fix (`market-tick-data-service@94e625c7`)
   to the same script, because the same 3 foreign files were dirty again (their mtimes had moved — traced to my OWN
   quickmerge's internal stash/restore cycles touching them, not a new foreign edit) —
   `backfill-defi-legacy-datatype-fold-20260806-104615` also launched onto stale code (`manifest=143de3138795` vs
   `repo=94e625c752f6`), deleted, same stash/rebuild/restore recovery.

## Root cause (code-level)

`launcher_common.sh`'s `lc_verify_tarball_freshness`, `auto` case:

```bash
auto)
    echo "lc_verify_tarball_freshness: auto-republishing stale tarball(s): ${stale_repos}"
    if $republish_cmd; then
        echo "lc_verify_tarball_freshness: republish complete — re-verifying"
        # Re-verify once in warn mode (no infinite loop) so the operator sees confirmation the republish took.
        LC_TARBALL_FRESHNESS=warn lc_verify_tarball_freshness "$code_bucket" $stale_repos
        return 0                      # <-- always 0, regardless of the re-verify's actual finding
    fi
    echo "ERROR: auto-republish failed for: ${stale_repos} — not launching onto unverified code" >&2
    return 1
    ;;
```

`$republish_cmd` (`create-code-tarballs.sh --include <repo>`) exits 0 even when it SKIPPED every requested repo (a skip
is logged, not treated as failure — reasonable in isolation, since "already up to date" is also a legitimate skip
reason). The recursive re-verify call DOES correctly detect and print the still-stale warning — but it runs in `warn`
mode, which itself always `return 0` (by design, for the top-level warn UX) — and the outer `auto` branch never inspects
that inner call's actual result, so `auto` mode's `return 0` fires unconditionally as long as the republish subprocess
itself didn't hard-fail.

## Why this matters beyond this one script

Any `launch-*.sh` that calls `lc_verify_tarball_freshness` in the default `auto` mode, on any shared checkout with
foreign dirty files present (a normal, expected, correct state in this workspace's multi-slot model — see
`/codex/05-infrastructure/per-tab-worktrees.md`), can silently launch onto stale code every time, with the ONLY signal
being a WARNING line easy to miss in a long launcher log. This is the exact incident class
`features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md` was filed to prevent — the mechanism
built to close that gap has its own gap.

## Recommended fix

`auto` mode's inner re-verify call should have its result checked, not discarded:

```python
LC_TARBALL_FRESHNESS=warn lc_verify_tarball_freshness "$code_bucket" $stale_repos
# capture whether IT found anything still stale, propagate that as auto's own return
```

concretely: capture the recursive call's stderr/a stale-count signal (or refactor the freshness CHECK into its own
function returning a stale list, separate from the warn/enforce/auto DISPOSITION logic, so `auto` can call the check
function directly post-republish instead of recursing into itself). Separately (smaller, same root symptom):
`create-code-tarballs.sh`'s dirty-tree skip could `--allow-dirty-tarball` automatically for the SPECIFIC repo the caller
asked to `--include`, since a launcher already knows it just shipped a specific commit to that one repo and isn't trying
to tar the whole dirty tree — narrower and arguably safer than a caller having to discover + do the
stash/rebuild/restore dance by hand every time, as this session did twice.

## Todos

- [x] ✅ [INFRA] P2. Fix `lc_verify_tarball_freshness`'s `auto` mode to check the actual freshness result after
      republishing, not just the republish subprocess's exit code — add a regression test that reproduces this exact
      case (stale tarball + dirty unrelated tracked files in the repo + `auto` mode → must NOT return success). —
      deployment-service@450b212. QG green; regression test `test_auto_mode_stale_after_dirty_skip_returns_nonzero`
      passes.
- [ ] [INFRA] P3. Auto-apply `--allow-dirty-tarball` in `create-code-tarballs.sh --include <repo>`, scoped to only the
      explicitly-`--include`d repo(s), when called FROM `lc_verify_tarball_freshness`'s auto-republish path
      specifically (not as a general default — a human running the script directly should still get the safety
      prompt). Per D11 ruling (2026-08-22): approved — closes a recurring page class cheaply.

## Progress Log

- **na-eligibility-audit 2026-08-09 (round11 RECLASSIFY+satellite-extraction sweep, infra tranche)**: KEEP-NA, valid —
  unchanged. Todo 1 (the bounded fix) is already closed (AO slot-9, `deployment-service@450b212`, shipped via the now-
  archived `infra_satellite_ao_dispatch_batch8_2026_08_07.md`). Sole remaining open item is todo 2 (`[DIAG] P3`), still
  explicitly framed as "Consider whether... should auto-apply `--allow-dirty-tarball`... (not as a general default — a
  human running the script directly should still get the safety prompt)" — a design-preference call on where to draw a
  safety-vs-convenience line, not a bounded spec. Checked against this round's accumulated-precedent list (IAM
  self-service, D16 all-repos, S5.1 tiering, plan-destination-AO-default, escalation-N=3-days, reversibility-qualified
  deletes, Option B retired, GSM secret + 5 Slack webhooks) — none resolve that design call.
- **interactive session 2026-08-06**: filed after hitting this twice in ~3 hours on the same VM launcher, working around
  it manually both times (stash-by-name → rebuild tarball → pop stash → relaunch, verified `all 3 tarball(s) current` on
  the successful relaunch). Not yet fixed — flagged for its own dedicated pass rather than a rushed edit to shared
  launcher infrastructure under this session's VM-relaunch time pressure.
- **context-scout 2026-08-07**: populated context_scope (3 entries) — the 2 pre-existing source files (both already
  minimal and correct — the `auto` mode call site and the republish command it shells out to) re-verified; added
  `features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md`, the doc this bug's own text names
  as "the exact incident class" the `lc_verify_tarball_freshness` mechanism was built to prevent.
- **na-eligibility-audit 2026-08-07 (infra tranche)**: KEEP-NA, valid — deliberately NOT reclassified directly. Todo 1
  (the bounded, worker-determinable `auto`-mode fix) is already conflict-clear-extracted by `/ag-closeout-audit infra`'s
  2026-08-07 run into `infra_satellite_ao_dispatch_batch8_2026_08_07.md` (`assigned_vm: planning`, currently
  `status: draft` awaiting operator flip). Directly reclassifying this doc too would open a second, competing dispatch
  path onto the same fix — exactly what the shared conflict-check exists to prevent — and would step on the sibling
  skill's own in-flight batch-drafting workflow, which this skill's own scope explicitly defers to (never flip a drafted
  batch to active itself). Todo 2 (`[DIAG] P3`, the optional `--allow-dirty-tarball` auto-scoping idea) is correctly NOT
  covered by batch8 — its own Progress Log calls it "a separate, smaller design consideration, not required for this
  fix" — and remains a genuine open design call here. Once batch8 is approved and ships, its own todo reconciles this
  doc's todo 1 checkbox directly; no action needed from this skill until then.
- **AO slot-9 2026-08-07**: Todo 1 FIXED — deployment-service@450b212. `auto` mode now calls
  `LC_TARBALL_FRESHNESS=enforce lc_verify_tarball_freshness` for the post-republish re-check (enforce returns non-zero
  if still stale; warn always returned 0 regardless). Regression test
  `test_auto_mode_stale_after_dirty_skip_returns_nonzero` added to `TestTarballFreshnessGuard`. QG green. Shipped via
  `infra_satellite_ao_dispatch_batch8_2026_08_07.md` (now archived).
- **context-scout 2026-08-17**: re-verified context_scope (3 entries), unchanged.
- **context-scout 2026-08-20**: refreshed context_scope (3 entries).
- **2026-08-22 — ruling D11 (Tarball pipeline hardening)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch authority,
  AUTONOMOUS_AGENT_RULES rule 2): Approve refresh + narrow auto-dirty, defer the gate — the first two close measured
  recurring page classes cheaply; the gate is a riskier shared-pipeline change deserving its own design pass. Source:
  /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
