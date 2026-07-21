---
doc_type: issue
title:
  "market-tick-data-service LDR->main promotion (PR #671/#672) hit a chain of 3 independent walls — 2 fixed and shipped,
  1 root-caused with a ready fix pending a clean QG window, 1 open for investigation"
summary: >-
  cicd escalation agt-1903f8 (wall_type=ldr_qg_failure, PR market-tick-data-service#671) was dispatched because
  quality-gates-v2 failed on the LDR→main promotion PR. Root-caused and fixed the original 3 failing tests (already
  fixed on LDR@7ce100f9 by another agent before this escalation started — verified independently). Fixing that alone did
  not unblock the promotion because THREE further, unrelated walls were discovered in sequence: (1) a SIGPIPE bug in
  `ldr-to-main-promote-fleet.yml`'s LABEL-CHECK step silently dropped market-tick-data-service from every fleet tick's
  PROMOTED/BLOCKED/CONFLICTED summary — FIXED + shipped (unified-trading-pm@4f6db3099 on main, backmerged to
  LDR@5a2f0f012); (2) once that was fixed, PR #672 opened at the correct head but the provenance gate is refusing to arm
  auto-merge, citing 29 commits that "bypassed quickmerge" — OPEN, needs investigation (real violations vs. a known
  squash-blind marker-detection bug); (3) once that was worked around/understood, the ACTUAL quality-gates-v2 run on PR
  #672 failed on a freshly-disclosed pip-audit CVE (pyasn1 CVE-2026-59885/CVE-2026-59886, published 2026-07-21T19:11
  UTC, same day) — ROOT-CAUSED with a verified-safe fix (bump pyasn1 0.6.3→0.6.4, already within the existing
  `>=0.6.3,<0.7.0` constraint) but NOT shipped: severe host contention (load avg ~43, 9+ concurrent `quality-gates.sh`
  runs, swap saturated) killed 4 consecutive local QG verification attempts before the sentinel could be written, and
  MTDS is a product repo (not covered by the PM-only `.github/**` direct-push carve-out), so the fix could not be
  force-shipped without a green QG.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags:
  [quality-gates, ci-cd, ldr-to-main-promote, sigpipe, provenance-gate, pip-audit, cve, sentinel, quickmerge-blocked]
related: [mtds_canonical_stem_leaf_qg_regression_blocks_quickmerge_2026_07_21.md]
created: "2026-07-21"
parent_epic: infrastructure_master
priority: P1
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
source: [cicd escalation agt-1903f8, wall_type=ldr_qg_failure, market-tick-data-service#671]
resolved_by:
locked_by:
depends_on: []
---

# MTDS PR #671/#672 promotion — chain of 3 independent walls

## Timeline / what actually happened

1. **Original escalation** (`agt-1903f8`): `quality-gates-v2` red on PR #671 (`market-tick-data-service`, LDR→main),
   failing run https://github.com/IggyIkenna/market-tick-data-service/actions/runs/29855823924, job "QG slice (tests)" —
   3 canonical-stem/leaf-byte-match/catalog-decompose tests failing on head `f6176e8be49d`.
2. Investigation found this exact regression was **already root-caused and fixed** by another agent the same day — see
   `mtds_canonical_stem_leaf_qg_regression_blocks_quickmerge_2026_07_21.md` (status: resolved,
   `market-tick-data-service@7ce100f9`). Independently re-verified here: a full local `quality-gates.sh` run on
   `7ce100f9` completed the entire pytest suite with **6619 passed, 17 skipped, 0 failed** (the exact test class that
   was failing in CI). PR #671's head (`f6176e8b`) simply predates this fix — the fleet auto-promote bot had not yet
   opened a fresh promote PR at the newer LDR tip.
3. **Wall 2 — SIGPIPE silently drops the repo from every fleet tick.** Manually dispatched
   `ldr-to-main-promote-fleet.yml` (`--ref main -f only_repo=market-tick-data-service`) twice; both times the SIT gate
   passed (`sit_validated_tree == LDR tree`) but the run then hit: `line 558: printf: write error: Broken pipe`
   immediately after the SIT-GATE-PASS log line, and the repo vanished from the run's PROMOTED/BLOCKED/CONFLICTED
   summary (all read 0) — reproduced 2/2, on two different self-hosted runners (glue-1, glue-2). Root cause:
   `.github/workflows/ldr-to-main-promote-fleet.yml` line 683, `LATEST_SUBJECT=$(printf '%s\n' "$RANGE_MSGS" | head -1)`
   — `head -1` closes the pipe before `printf` finishes writing a large multi-line `$RANGE_MSGS` (the full `main..LDR`
   commit-subject range), and under `set -euo pipefail` the resulting SIGPIPE (exit 141) aborts the per-repo
   `process_repo` background subshell right there, silently — no error surfaces in the job's overall `conclusion` (which
   reads "success") because `process_repo` runs `&` per-repo with results collected via `$RESULT_DIR/$REPO` files, and a
   crashed subshell simply never writes its result file. **FIXED**: replaced the pipe with pure bash parameter expansion
   (`LATEST_SUBJECT="${RANGE_MSGS%%$'\n'*}"`, no subprocess). Shipped directly to `main`
   (`unified-trading-pm@4f6db3099`) per the CLAUDE.md carve-out ("PM scripts/** & any .github/** change that must reach
   main to unblock the pipeline"); automatically backmerged to `live-defi-rollout@5a2f0f012` via `main-backmerge-to-ldr`
   (no separate LDR push needed). **Verified fixed**: re-dispatched the fleet workflow after the push — SIGPIPE gone, PR
   **#672** opened at the current LDR head (`market-tick-data-service@7ce100f911ac`), superseding #671 (manually
   closed + its stale ref deleted, since the bot's own superseded-ref cleanup didn't fire that same tick — separate,
   not-yet-investigated minor issue, low priority since #671 is gone now).
   - **Blast radius**: only one occurrence of this exact `printf | head -1` pattern in this file, but check whether
     other ldr_main repos with large same-day commit ranges hit the same silent-drop (nothing indicates they did in this
     session, but nobody was actively looking either — a repo with `RANGE_MSGS` small enough to fit in one pipe buffer
     write would never trigger it, which is presumably why this went unnoticed until MTDS's unusually large same-day
     commit range hit it).
4. **Wall 3 — provenance gate blocks auto-merge on PR #672.** Once the ref/PR opened, the run logged:
   `⛔ provenance: market-tick-data-service has non-quickmerge CODE on LDR — NOT arming auto-merge (PR left open)`,
   listing **29 commits** flagged as bypassing quickmerge, e.g. `a7569298`, `3253cae3`, `d302f07a`, `c85af5b2`, and 26
   more (full list in the run log: https://github.com/IggyIkenna/unified-trading-pm/actions/runs/29864683343). The
   provenance-range detector logged `mode=fallback marker=∅ reachable=False → origin/main..origin/live-defi-rollout` —
   i.e. it could not find a "last-promoted" marker for this repo and fell back to the FULL `main..LDR` range. This is
   the same failure shape as the documented `provenance_gate_squash_perpetual_block_2026_06_17` bug class (a
   squash-promote never lands the promoted commit's SHA on `main`, so a marker-less repo re-flags its entire history
   forever) — **but this was NOT confirmed either way in this session**. Two possibilities, needing investigation: (a)
   these 29 commits are a **genuine governance violation** (real direct pushes to LDR bypassing quickmerge, which would
   be a real finding requiring root-cause + prevention), or (b) this is a **marker-detection false positive** (MTDS has
   simply never successfully promoted to `main` before via this mechanism, so no marker exists, and the fallback
   re-flags legitimately-quickmerged-but-unmarked history). NOT force-armed here — arming past a provenance gate without
   knowing which of these is true would be exactly the kind of "force-resolve to go green" the cicd role is barred from
   doing.
5. **Wall 4 — fresh pip-audit CVE.** The actual `quality-gates-v2` run on PR #672's head (run
   https://github.com/IggyIkenna/market-tick-data-service/actions/runs/29864755534) failed on the "QG slice (checks)"
   job: `❌ pip-audit vulnerabilities found` — `pyasn1 0.6.3: CVE-2026-59885` and `CVE-2026-59886` (GHSA-8ppf-4f7h-5ppj,
   "quadratic complexity in OBJECT IDENTIFIER / RELATIVE-OID processing", severity HIGH). Confirmed via OSV
   (`api.osv.dev`) this was disclosed **2026-07-21T19:11:03Z — the same day, mid-escalation** — a fresh CVE, not a
   pre-existing or code-introduced problem. **Fixed upstream in pyasn1 0.6.4** (released 2026-07-09, predates the
   disclosure but contains the fix per the advisory's "Patches" section). MTDS's existing `uv.lock` constraint on the
   dependent package is `>=0.6.3,<0.7.0`, so 0.6.4 is already in range — `uv lock --upgrade-package pyasn1` produces a
   clean 3-line `uv.lock` diff (`version = "0.6.3"` → `"0.6.4"` + updated sdist/wheel hashes), no `pyproject.toml`
   change needed, no MTDS code imports `pyasn1` directly (transitive via `pyasn1-modules`, itself likely pulled in by a
   GCP-auth chain). **NOT SHIPPED**: the host this session ran on was severely contended (load average ~43, 9+
   concurrent `bash scripts/quality-gates.sh` processes across other slots, `free -h` showing ~2GB free / 6GB swapped) —
   4 consecutive attempts to run a full local `quality-gates.sh` (required to write the `.qg_last_passed_sha` sentinel
   `quickmerge --agent` checks) were silently killed at increasingly early points (once mid-validators, once at TESTS
   start, once immediately after TESTS start, once at pytest's own startup) — consistent with OOM-kill under memory
   pressure, not a defect in the change itself. The `uv.lock` edit was **reverted** (not left as dirty/uncommitted WIP)
   rather than force-shipped, since (a) `quickmerge --agent` refuses without a green sentinel (by design — this is not a
   bypassable gate), and (b) MTDS is a product repo, not covered by the PM-only `.github/**`/`scripts/**` direct-push
   carve-out that Wall 2's fix used.

## Current state (as of this doc)

- PR **#671**: CLOSED (superseded, manually), ref deleted.
- PR **#672** (`market-tick-data-service@7ce100f911ac`): OPEN, `mergeStateStatus=BLOCKED`. Blocked on: (a) the Wall-3
  provenance gate (auto-merge not armed) AND (b) `quality-gates-v2` currently failing on the Wall-4 pip-audit CVE.
- `unified-trading-pm` `main`@`4f6db3099` / `live-defi-rollout`@`5a2f0f012`: carries the Wall-2 SIGPIPE fix, confirmed
  working (verified via 2 live re-dispatches after the fix).
- `market-tick-data-service` LDR@`7ce100f9`: has the ORIGINAL 3-test fix (verified). Does NOT yet have the Wall-4 pyasn1
  bump (reverted, not shipped).

## Todos

- [ ] 1. [DATA] P1. Ship the pyasn1 CVE fix once a clean QG window is available:
      `cd market-tick-data-service && uv lock --upgrade-package pyasn1` (produces the exact 3-line `uv.lock` diff
      described above — re-verify against the current LDR tip since more commits may have landed by the time this is
      picked up), `bash scripts/quality-gates.sh` full green, `quickmerge --agent --files 'uv.lock'`. Low risk
      (patch-only security bump, already in-range, no code touches pyasn1 directly) — this should not need a design
      decision, just a host with capacity for one clean full-QG run. (repo: market-tick-data-service)
- [ ] 2. [REVIEW] P1. Investigate the Wall-3 provenance-gate block on PR #672: pull the full list of the 29
      "non-quickmerge" commits (run log: https://github.com/IggyIkenna/unified-trading-pm/actions/runs/29864683343) and
      determine whether they are (a) genuine quickmerge-bypassing direct pushes (real governance violation — find
      who/how and prevent recurrence) or (b) a marker-detection false positive because MTDS has never successfully
      promoted to `main` via this mechanism before (in which case `scripts/cicd/promote_provenance_range.py`'s
      marker-fallback needs the same `provenance_gate_squash_perpetual_block_2026_06_17` class fix already applied
      elsewhere, or a one-time manual marker seed). Do NOT arm auto-merge on #672 until this is resolved one way or the
      other. (repo: unified-trading-pm, market-tick-data-service)
- [ ] 3. [INFRA] P2. Audit other `ldr_main`-opted-in repos for the same `printf | head -1` SIGPIPE pattern's blast
      radius — check whether any repo with a large same-day commit range silently sat un-promoted the same way MTDS did,
      now that the fix is live (`unified-trading-pm@4f6db3099`); also grep for the same anti-pattern elsewhere in
      `.github/workflows/*.yml` (the `ldr-to-staging-promote.yml`/`ldr-to-main-promote.yml`/`plan-health-agent.yml`
      `printf | grep | head -N` occurrences noted during this investigation are a DIFFERENT, lower-risk shape — grep
      buffers before `head`, so they're less likely to reproduce, but not proven safe either). (repo:
      unified-trading-pm)

## Codex SSOTs

`codex/08-workflows/ci-cd-flow.md` (LDR→main promotion, quickmerge, direct-push carve-outs).
