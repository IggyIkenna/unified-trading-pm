---
doc_type: issue
title:
  ldr_to_main_fleet_promote.sh's Tier-A ci_status gate can deadlock unrecoverably on a PR-time-vs-push-time dependency
  race — instruments-service main red since 11:46Z, promotion permanently self-blocked
summary: >-
  instruments-service's `quality-gates-v2` went red on `main` at 2026-08-09T11:46:23Z (run 31311616796, commit 9de51c54
  = promote PR #1135, LDR sha 096bc5647a99) from a genuine PR-time-vs-push-time content race, not a code defect: #1135
  validated GREEN at PR-time against a content-first `unified-api-contracts` clone taken at that moment, then
  `push:[main]` re-cloned UAC at a NEWER live-defi-rollout tip that had since gained `SUSHISWAP_V2-ARBITRUM` to the
  venue registry — `test_resolved_version_not_in_registry_falls_through` (still asserting NOT-in-registry on the
  promoted-from tree) failed against that fresher dependency content. `live-defi-rollout` itself was and remains fully
  self-consistent/green throughout (verified directly: its own copy of the same test already asserts IN-registry,
  matching current UAC; every direct LDR `quality-gates-v2` run stayed green). The failing push wrote Firestore
  `ci_status=FAILING` (branch=main). `ci_status_store.py`'s `resolve_status()` has a deliberate symmetric guard — `if
  prev_status == "FAILING" and prev_branch == "main" and branch != "main": return prev_status` — so only another
  main-branch signal can ever clear a main-originated FAILING (by design, to stop a non-main green from laundering a
  real on-main regression). But `ldr_to_main_fleet_promote.sh`'s Tier-A gate refuses to even attempt a fresh promote PR
  while `ci_status=FAILING` (`_done BLOCKED; return 0`, before any PR is opened). Net: the ONLY thing that could produce
  a fresh main-branch GREEN (a new promotion) is preemptively vetoed by the very status a fresh promotion would fix — a
  genuine unrecoverable deadlock, not a transient flake. Confirmed BLOCKED at both the 12:00Z and 12:17Z fleet-bot
  ticks; by 12:17Z the blast radius had grown to also block `system-integration-tests` via dep-order (a dependent of
  instruments-service). A `workflow_dispatch` quality-gates-v2 run directly against LDR (12:09-12:12Z, success) was
  tried and confirmed NOT to clear the block — exactly per the symmetric guard's design (branch=live-defi-rollout can't
  speak for main).
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm, instruments-service]
scope: [engineer, admin]
tags: [ci-cd, ci_status, tier-a-gate, promotion-deadlock, ldr-to-main, firestore, dependency-race]
related:
  [
    /plans/archive/issues/mtds_ldr_red_promote_churn_four_prs_2026_07_19.md,
    /plans/active/issues/ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md,
  ]
created: 2026-08-09
last_updated: "2026-08-09"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.3
assigned_role: cicd
drift_direction: advance-code
depends_on: []
source: "cicd escalation agt-086274, 2026-08-09, wall_type=main_ci_red, escalation BLK-96d38ee3"
resolved_by:
locked_by:
locked_since:
context_scope: []
---

## What happened

1. `instruments-service` promote PR #1135 (head `096bc5647a99`, `chore(promote): LDR → main (Option-B direct)`) ran its
   PR-time `quality-gates-v2` green and merged to `main` at `2026-08-09T11:43:39Z`.
2. The `push:[main]` re-verification (run `31311616796`, `2026-08-09T11:46:23Z`) re-cloned `unified-api-contracts`
   content-first at LDR HEAD — by then already past the point where `SUSHISWAP_V2-ARBITRUM`/`SUSHISWAP_V3-ARBITRUM` were
   added to `ALL_DEFI_VENUES` — and
   `tests/unit/scripts/test_canonicalize_defi_manifest_venue_factory_resolution.py::TestCanonicalVenueFactoryResolution::test_resolved_version_not_in_registry_falls_through`
   (still asserting `"SUSHISWAP_V2-ARBITRUM" not in ALL_DEFI_VENUES` on the promoted-from tree) failed.
3. `live-defi-rollout`'s own copy of that same test already asserts `"SUSHISWAP_V2-ARBITRUM" in ALL_DEFI_VENUES` —
   confirmed via
   `git show origin/live-defi-rollout:tests/.../test_canonicalize_defi_manifest_venue_factory_resolution.py`. LDR is
   not, and was never, red for this.
4. The push failure recorded `ci_status=FAILING` with `branch=main` in Firestore (`ci-status-update.yml` →
   `ci_status_store.py`).
5. `scripts/cicd/ldr_to_main_fleet_promote.sh`'s Tier-A gate
   (`GATE BLOCK $REPO: ci_status=FAILING ... — LDR CI is red; fix before LDR→main`) fires on EVERY subsequent tick
   because `ci_status` for instruments-service stays `FAILING`, and returns immediately — no fresh promote PR is even
   opened.
6. Because no fresh promote PR is opened, no fresh main-branch signal is ever produced, so `ci_status` never clears —
   the deadlock is self-sustaining.
7. By the 12:17Z tick, `system-integration-tests` (a dependent of instruments-service) was ALSO blocked via dep-order,
   growing the blast radius.

## Why this is a design flaw, not a one-off

`ci_status_store.py`'s `resolve_status()` symmetric guard (added 2026-07-20, see its own header comment) is correct in
isolation: it stops a non-main green from silently clearing a genuine on-main regression. But combined with the Tier-A
gate's own refusal to even TRY a fresh promotion while `ci_status=FAILING`, the two correct-in-isolation rules compose
into a hole: there is no code path left that can ever produce the "another main signal" the guard requires, whenever the
FAILING was itself caused by a PR-time-vs-push-time content race (LDR moved between PR validation and push
re-verification) rather than a genuine on-main code defect. This is a distinct failure mode from
`mtds_ldr_red_promote_churn_four_prs_2026_07_19.md` (closed 2026-07-22) — that incident was a genuinely red LDR churning
promote PRs harmlessly; THIS is a genuinely green LDR permanently locked out of promoting because of a transient,
already-resolved-on-LDR content mismatch at the promotion boundary.

## What was done this session (cicd escalation agt-086274 / BLK-96d38ee3)

- Diagnosed root cause (above), verified LDR is fully green/self-consistent (both by reading file content directly and
  via the existing `ldr_ci_monitor.py` heartbeat dispatch).
- Escalated via `/blocked` (`BLK-96d38ee3`) rather than pushing to `main` directly (outside cicd-agent mandate — "a
  separate promotion campaign owns LDR→main").
- Per main's answer: opened prep PR
  [`instruments-service#1136`](https://github.com/IggyIkenna/instruments-service/pull/1136)
  (`promote/instruments-service/159c0ebe0ebd` → `main`, cut from the LDR tip current at prep time) and got its
  `quality-gates-v2` (promote PR) required check to a genuine GREEN + `mergeable: MERGEABLE` — confirming the fix is
  exactly "promote current LDR content," nothing more. **Not merged** — merge-to-main authorization was escalated to the
  operator (see `BLK-96d38ee3`, `authority: operator_pending`).

## Suggested resolution paths (not attempted here — scope/authorization boundary)

1. **Immediate unblock**: operator (or an agent with main-push authorization) merges
   [`instruments-service#1136`](https://github.com/IggyIkenna/instruments-service/pull/1136) once re-verified still
   green/up to date. This should self-clear `ci_status` (a genuine `push:[main]` GREEN, branch=main) and unstick both
   instruments-service and its now-blocked dependent `system-integration-tests`.
2. **Structural fix (the actual ask of this issue)**: `ldr_to_main_fleet_promote.sh`'s Tier-A gate should not be a hard,
   unconditional veto on attempting a fresh promote PR — it should still let a NEW promote PR be opened (whose OWN
   required `quality-gates-v2` check is the true, current-content gate) even while a STALE `ci_status=FAILING` is
   stored, since the fresh PR's checks are strictly more authoritative than a cached Firestore doc that may itself be
   exactly the kind of stale-content artifact described above. A safe middle ground: keep the veto on auto-merging a red
   promote PR, but drop it on the act of minting/checking one — the deadlock only exists because PR-creation itself is
   gated, not just merge-arming.
3. Consider whether the PR-time UAC clone and the push-time UAC clone should be made to agree (e.g., pin the push
   re-verification to the exact commit the PR validated against, rather than content-first re-resolving at HEAD) — this
   would eliminate the race at its source rather than only unblocking its downstream deadlock.

## Cross-refs

- Closed sibling incident (genuinely-red-LDR churn, different failure mode):
  `plans/archive/issues/mtds_ldr_red_promote_churn_four_prs_2026_07_19.md`.
- `scripts/cicd/ci_status_store.py` (`resolve_status()`, the symmetric main-only-clears-main guard).
- `scripts/cicd/ldr_to_main_fleet_promote.sh` (Tier-A gate, `GATE BLOCK $REPO: ci_status=FAILING` line).
- `scripts/repo-management/ldr_ci_monitor.py` (the separate, non-clobbering `ldr_ci_status` monitor axis — confirmed its
  green signal does NOT and should NOT clear the promotion `ci_status` axis).
- Dashboard escalation `BLK-96d38ee3` (question, options, main's answer, `authority: operator_pending`).

## na-eligibility-audit verdict

**na-eligibility-audit 2026-08-10** (ci tranche, autonomous, dispatch agt-74eff9) [body-hash:233a2ff9e6d06e7e]: KEEP-NA,
valid — TRAP CONFIRMED: zero `- [ ]` checkboxes exist in this doc (verified via the mandated grep, matches the given
phase0 figure of 0), but the doc is NOT archive-eligible -- `status: open`, `resolved_by:` blank in frontmatter, and
substantial PROSE-ONLY remaining work sits under '## Suggested resolution paths (not attempted here --
scope/authorization boundary)' as a numbered list that was never converted to tracked checkboxes (a violation of the
workspace's own 'every follow-up is a `- [ ]` todo, never prose' hard rule, though fixing that is outside my read-only
scope).
