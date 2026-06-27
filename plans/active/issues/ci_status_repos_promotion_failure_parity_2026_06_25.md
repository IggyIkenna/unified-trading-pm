---
title:
  "ci_status /repos shows MAIN_GREEN while a promotion PR's v2 FAILED + paged Slack CRITICAL — Slack↔/repos parity gap"
created: "2026-06-25"
parent_epic: "infrastructure_master"
assigned_vm: vm-cross-cutting
status: "resolved"
priority: "P1"
locked_by: "live-defi-rollout"
source:
  "operator-2026-06-25 (deployment-ui /repos showed PM as MAIN_GREEN while LDR→main PR #547 python-quality-gates-v2
  FAILED + paged Slack CRITICAL)"
---

# ci_status /repos ↔ Slack promotion-failure parity gap

## What I found (root cause — confirmed + reproduced on PM #547)

The deployment-ui **/repos** CI/CD page reads a repo's headline status from the manifest `repositories.<repo>.ci_status`
(FEATURE_GREEN | STAGING_GREEN | MAIN_GREEN | FAILING). That field is **branch-PUSH-conclusion based** — it tracks the
`quality-gates-v2` conclusion of a PUSH to `main`/`staging`/LDR. A **promotion PR** (head=`live-defi-rollout`/`staging`
into `staging`/`main`) runs v2 as a **`pull_request`** event whose head BRANCH is `live-defi-rollout`, NOT a push to
`main` — so a FAILING promotion PR is invisible to the branch-push reads.

Confirmed chain for PM `live-defi-rollout → main` PR #547 (head `09242e0e`, `python-quality-gates-v2` FAILED on a
frontmatter-schema violation, Slack paged `:rotating_light: CRITICAL`):

1. **v2 dispatch** (`.github/workflows/python-quality-gates-v2.yml` "Record CI status"): for a PR,
   `TRIGGER_BRANCH = github.head_ref = live-defi-rollout`, `BASE_REF = main`. Since `BASE_REF != staging`,
   `EFFECTIVE_BRANCH = live-defi-rollout` and on failure it dispatches `ci-status-update` with
   `status=FAILING, branch=live-defi-rollout`. The writer DOES write FAILING.
2. **The reconciler then RESETS it back to MAIN_GREEN** (`scripts/cicd/ci_status_reconciler.py` +
   `ci-status-reconciler.yml`, every 15 min). `expected_from_v2` scans branch v2 conclusions in precedence
   `main → staging → ldr` and returns at the FIRST definitive one. `latest_v2 PM main` reads the **last GREEN main
   push** (`777e073d` success) → returns `MAIN_GREEN` → `decide()` hits **Drift-1 missed-recovery**
   (`cur=FAILING, expected=MAIN_GREEN`) → reconciles FAILING **back to MAIN_GREEN**. The correctly-written FAILING is
   masked by the green main push. (Measured live 2026-06-25: `latest_v2 PM main = success`, while
   `--branch live-defi-rollout` carried the `pull_request` **failures** `09242e0e` / `086dfb74` / … — the promotion-PR
   heads.)
3. **The read path** (`deployment-api/deployment_api/routes/_repo_ci_manifest.py::ci_status_for` → MAIN_GREEN;
   `repo_ci.py::_overview_row`) surfaced MAIN_GREEN. The only "status lies" guard
   (`deployment-ui/src/lib/repoCi.ts::classifyStall.ciStatusStale`) fires only on a git **content delta** (staging ahead
   of main with `files_changed>0`), which a squash-merged drained repo does NOT show — so the failing promotion was
   fully masked. (PM's manifest `ci_status` reading "empty" was a false alarm from a wrong top-level `.get` — it is a
   per-repo field `repositories['unified-trading-pm'].ci_status`, value `MAIN_GREEN`.)

## Why it matters

A failing promotion that pages Slack CRITICAL was invisible on the dashboard at a glance — Slack and /repos disagreed,
exactly the silent-rot class the repo-CI dashboard exists to kill. The reconciler actively un-did the correct FAILING
every 15 min.

## The fix (backend/data — parity with Slack, no UI-render hack)

Two coordinated layers, both data-driven (GitHub ground truth = the same source Slack pages off):

- **Reconciler promotion-awareness (stop the masking + self-correct)** —
  `scripts/cicd/ci_status_reconciler.py::decide()` gains a `promo_concl` arg (the latest v2 conclusion of the repo's
  OPEN promotion PR). A FAILING open promotion PR is **authoritative**: it forces FAILING and SHORT-CIRCUITS before the
  missed-recovery reset can mask it. Fail-safe — `promo_concl=""` (no open/failing promotion PR) is a pure no-op, so the
  branch-based logic is unchanged for every other repo. `ci-status-reconciler.yml` adds `promo_pr_v2()` (newest open
  LDR→main / LDR→staging / staging→main PR's head-sha v2 conclusion) and passes `--promo`; the reconciler already
  iterates PM, so PM self-corrects too (dispatches `branch=main` → CRITICAL severity, matching Slack).
- **deployment-api read derivation (immediate parity on /repos)** —
  `deployment_api/routes/_repo_ci_stuck.py::derive_promotion_blocked()` (pure, unit-tested) returns True when an OPEN
  promotion-contract PR is stuck on a human-actionable BLOCKING class (`failing_check` / `conflicting` /
  `skip_ci_jammed`) — reusing the per-PR `stuck_class` the overview already classifies from GitHub. Surfaced as a new
  `RepoOverviewDict.promotion_blocked` field (wired in `repo_ci.py::_overview_row`
  - `_repo_ci_mocks.py`). It reads ground truth, so it can never go stale-green or disagree with Slack, and — unlike
    `drain_stalled` — does NOT require a content-ahead delta, so a squash-merged drained repo whose LDR→main PR failed
    still surfaces. deployment-ui (`client.ts` type + `repoCi.ts`): `ciStatusLabel` appends `· PROMOTION FAILING` and
    `rowSeverity` returns 3 (top of the attention queue) when `promotion_blocked`.

## Tests

- `unified-trading-pm/tests/unit/test_ci_status_reconciler.py` — 7 new cases incl.
  `test_promotion_failing_overrides_green_main_does_not_reset_to_main_green` (the literal PM #547 bug:
  `decide("MAIN_GREEN", main="success", …, promo="failure") → FAILING`). 14 pass.
- `deployment-api/tests/unit/test_repo_ci_stuck.py::TestDerivePromotionBlocked` — 6 new cases (failing_check blocks;
  self-healing classes don't; no PR / unstuck → not blocked). 25 pass.

## How /repos now shows a failing promotion

`promotion_blocked=true` on the repo row → headline reads `MAIN_GREEN · PROMOTION FAILING` and the row sorts to the top
(severity 3) — matching the Slack CRITICAL page. The reconciler no longer resets the FAILING the v2 dispatch writes, so
the manifest `ci_status` itself tracks the failing promotion within one ~15-min tick instead of flapping back to
MAIN_GREEN.
