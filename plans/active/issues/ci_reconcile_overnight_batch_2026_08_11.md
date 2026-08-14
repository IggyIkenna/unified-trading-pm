---
doc_type: issue
title: >-
  /ci-reconcile overnight batch (2026-08-10 23:14 – 2026-08-11 04:00 UTC) — 17-item CI/CD alert reconciliation: 3
  root-caused + fixed (incl. one newly-discovered live regression), 12 self-resolved/false-alarm, 1 new file-size
  regression filed, 2 structural AO escalation-coverage gaps flagged
summary: >-
  Ground-truth reconciliation of two overnight CI/CD alert batches per `/ci-reconcile`. Of the 17 original items: 12
  were already resolved or were false alarms by the time of inspection (verified via gh/gcloud/SSM, not alert text); 2
  needed a real root-caused fix, both shipped this pass — features-service's Cloud Build was failing on a stale
  `uv.lock` (nodriver added to pyproject.toml 2026-08-09, lock last regenerated 2026-08-04, so `uv export --frozen`
  could never satisfy nodriver's websockets>=14 floor against the locked websockets==13.1); unified-api-contracts' Cloud
  Build was stuck in a 20-build-consecutive TIMEOUT loop because its `quality-gates.sh` invocation never set
  `QG_GOVERNOR_REPO`, so the host-RAM governor fell back to the unmeasured-repo 5500MB reservation on an 8GB Cloud Build
  machine instead of the real ~1.1GB measured baseline. Shipping that second fix surfaced a THIRD, entirely separate,
  currently-live regression blocking it (quality gates must be green tree-wide before any commit): UAC's brand-new
  `canonical_tradfi_underlying` resolver (landed ~05:00-06:00Z, after this session's original sweep) was silently
  mis-resolving a genuine multi-root composite (`LIVE-CATTLE-LEAN-HOG`) to a single wrong root instead of leaving it
  honestly unchanged — root-caused (a progressive multi-token trim where the docstring's own intent was a single-token
  trim) and fixed in the same shipped commit. One genuinely NEW regression was discovered mid-sweep (not in either
  original batch, not fixed this pass): MTDS's `partitioned_writer.py`/`migrate_tradfi_canonical_ 2026_07.py` crossed
  the 900-line hard file-size cap, currently blocking LDR and promote PR #950 — filed as a follow-up (requires a real
  split/exempt decision, not a safe blind trim). Two structural AO escalation-coverage gaps confirmed by direct code
  read of `agent-orchestrator/server/escalation.py`'s `WALL_TYPES` frozenset: no wall_type exists for Cloud Build
  failures or for `main-backmerge-to-ldr` sync failures, so both failure classes can only ever be caught by a
  human/interactive session noticing, never by AO auto-recovery.
status: open
nature: issue
scope: [engineer, admin]
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    market-tick-data-service,
    unified-trading-pm,
    instruments-service,
    unified-api-contracts,
    features-service,
    deployment-service,
    ibkr-gateway-infra,
    execution-service,
    agent-orchestrator,
  ]
tags: [ci-reconcile, quality-gates, cloud-build, escalation-coverage, provenance, uv-lock, qg-governor, file-size-cap]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/archive/issues/sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md,
    /codex/12-agent-workflow/host-concurrency-and-commit-provenance.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-08-11
author: claude-agent
last_updated: 2026-08-11
parent_epic: infrastructure_master
priority: P1
source: ci-reconcile skill, Slack #ci-failures 2026-08-10T23:14Z-2026-08-11T04:00Z
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /codex/12-agent-workflow/host-concurrency-and-commit-provenance.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
    agent-orchestrator/server/escalation.py,
  ]
---

# /ci-reconcile overnight batch (2026-08-10 23:14 – 2026-08-11 04:00 UTC)

Ground-truth CI/CD reconciliation of two Slack `#ci-failures` alert batches (17 items total) per the `/ci-reconcile`
skill. Section 0's rule applies throughout: **the alert text is only a starting pointer** — every disposition below is
re-derived from `gh run list`/`gh api`/`gcloud builds`/direct SSM+sqlite query against the live orchestrator DB, never
from the alert's claimed state.

## Batch 1 items (~23:14–00:13 UTC)

### 1. MTDS LDR red→green — RESOLVED, verified

Escalated `agt-345d48` (`ldr_qg_failure`, dispatched to slot 7 at 21:41:47Z, resolved 22:21:33Z via `qg_v2_green`).
Confirmed via direct `escalation_queue` sqlite query on the orchestrator VM (`i-0c9b283b31d6b5ca7`). Fix-adjacent MTDS
commits in that window carry `[slot-N·planning]` authorship (e.g.
`8c264a4 fix(mtds): force lifecycle_phase to explicit StringDtype... [slot-23·planning]`) — genuine AO auto-recovery,
not an interactive fix. MTDS `live-defi- rollout` is green as of the latest sweep.

**Disposition: resolved, AO auto-recovery confirmed. No follow-up.**

### 2. features-service Cloud Build failure (build `b172dcc8`, retry `5d77b116`, both FAILURE) — ROOT-CAUSED + FIXED

`gcloud builds log 5d77b116-ce99-4673-b77c-813f9d8924c2` (FAILURE, 2026-08-10T22:39:37Z; the first attempt
`b172dcc8-cc8d-4b42-8f6a-c53bda44f84a` failed identically 30 min earlier):

```
× No solution found when resolving dependencies:
╰─▶ Because nodriver>=0.40 depends on websockets>=14 and websockets==13.1,
    we can conclude that nodriver>=0.40 cannot be used.
    ...
    and features-service==0.81.3 depends on nodriver>=0.40.0, we can
    conclude that features-service==0.81.3 cannot be used.
ERROR: executor failed running [... uv export --frozen ... && uv pip install --system -e . ...]: exit code: 1
```

Root cause: `nodriver>=0.40.0,<1.0.0` was added to `pyproject.toml` by
`b6809756 (2026-08-09T11:38:54+01:00, [slot-4·laptop])` for the ForexFactory Cloudflare-challenge adapter, but `uv.lock`
was last regenerated `2026-08-04T00:31:08Z` — 5 days earlier — and never re-locked afterward, so `uv.lock` has no
`nodriver` entry at all and still pins `websockets==13.1` (from `web3==6.20.4`/`solana==0.36.11`). Cloud Build's
`uv export --frozen` refuses to deviate from that stale lock, so the constraint is permanently unsatisfiable in Cloud
Build even though local `uv sync` (non-frozen) apparently masked it — GH Actions `quality-gates-v2` was green throughout
because it doesn't run the frozen-export path.

**Fix shipped**: `uv lock` regenerated cleanly (`Resolved 234 packages`) — `web3 6.20.4→7.16.0`,
`websockets 13.1→15.0.1`, `nodriver` added at `0.50.3`, several `eth-*` transitives bumped. Verified narrow blast radius
before shipping: only one file in the repo imports `web3` directly
(`features_service/onchain/collectors/default_factories.py`, via the stable `Web3(Web3.HTTPProvider(rpc_url))`
construction — unaffected by v6→v7's actual breaking changes). Full `quality-gates.sh --no-fix` ran green (all tests,
217s) before shipping.

**Shipped**: `features-service@197e957475` via `quickmerge.sh --agent --files 'uv.lock'`
(`fix(deps): regenerate uv.lock to resolve nodriver/websockets conflict (Cloud Build blocker)`). Landed on
`live-defi-rollout`, post-push ancestry verified.

**Disposition: resolved, fix shipped + landed this pass.**

### 3. unified-trading-pm QG-fail (`ca56db21`) + promotion lag PR #2746 — RESOLVED, verified

Escalated `agt-c86813` at 21:17:44Z. Direct `escalation_queue` query shows this escalation's own dispatch **never
fired** — all 70 attempts over ~3h11m hit
`last_error: "repo 'unified-trading-pm' already active on another slot — not dispatching"` (PM routinely has many
concurrent AO slot sessions; this is the anti-starvation guard working as designed, not a bug). The wall self-resolved
(`resolution: qg_v2_green` at 00:28:31Z) via ambient concurrent AO activity already running on PM (recent PM commits
in-window are dominated by `[slot-5/8/20/23/24/26/27/30/31· planning]` tags) — not via this escalation's own dispatch,
and not via a plain interactive fix.

`unified-trading-pm`'s `quality-gates-v2` on `live-defi-rollout` is green (latest success `df96fdb0`, 02:43:28Z).

**Disposition: resolved. Flagging one structural nuance, not a bug**: this escalation's `dispatched_slot_id` is a false
negative for "did AO actually work this" — the wall cleared via ambient fleet activity on the same repo, not via the
escalation's own successful dispatch. Worth a note for anyone auditing `escalation_queue` dispatch-success rates on
high-concurrency repos like PM (`/escalation-queue-reconcile`'s territory, not fixed here).

### 4. instruments-service main-backmerge-to-ldr failure (run `31438815584`, `git fetch` exit 128) — RESOLVED, AO gap flagged

Not escalated (no `wall_type` covers backmerge-sync failures — see the Structural Findings section below). Self- healed
on the very next scheduled run (`f2ebc5e`, 1 minute later) despite the alert's framing suggesting it wouldn't.
`instruments-service` is green on `live-defi-rollout` as of the latest sweep.

**Disposition: resolved (self-healed). AO coverage gap flagged below — no fix attempted this pass (structural, needs a
new `wall_type` + escalation-worker prompt, out of scope for a same-pass code fix).**

### 5. unified-api-contracts Cloud Build TIMEOUT (`9e5e4e2`, build `a2327132`) — see items 5+11 combined below

Originally assessed as "transient regional flakiness" (part of a ~7-build TIMEOUT cluster). **This assessment was
WRONG** — see the combined write-up under item 11 below; both builds are the same systematic root cause, not two
separate transient events.

## Batch 2 items (~00:15–04:00 UTC)

### 6. SIT-gate-stuck-detector — execution-service 4-then-8 straight SIT-gate-blocked ticks — RESOLVED, verified

`ldr-to-main-promote-fleet.yml` is a fleet job living in `unified-trading-pm` (not per-repo in execution-service).
Latest run (`31462905590`, 05:49:26Z) log for execution-service:
`TIER A PASS execution-service: ci_status cached='MAIN_GREEN' live='MAIN_GREEN'` /
`SKIP execution-service: main tree == LDR tree`. No stuck SIT-gate state. `sit-gate-stuck-detector.yml` itself has been
green on its `*/30 * * * *` schedule (`05:28:10Z`, `04:33:32Z`). The referenced prior issue doc
(`sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md`) is archived, `status: resolved`,
`resolved_by: interactive session, 2026-08-06` — nothing contradicts that.

**Disposition: resolved, matches the alert stream's own 1:28AM RESOLVED tick. No follow-up.**

### 7. Provenance gate BLOCKED unified-trading-pm LDR→main promotion (commit `19dc43ec69`) — RESOLVED, verified fixed by another AO worker

Commit `19dc43ec69` (`ikennaigboaka [main·laptop]`, 2026-08-11T00:29:36+01:00, "feat(hooks): in-loop tool-call batching
nudge...") direct-pushed source (`cursor-configs/hooks/batching-nudge.py`) under the documented dirty-deps carve-out,
but sat mid-history on `live-defi-rollout` without a `Quickmerge:` trailer, deadlocking the LDR→main promote gate on a
~15min cadence from 00:30Z through at least 04:00Z (matches the alert stream's repeated fires).

**Already fixed by the time of inspection**: an AO worker (`ikennaigboaka [slot-4·planning]`) shipped
`582db7c8bf910611d66416400b032a58545e1c99` at 2026-08-11T03:14:41Z — `chore(provenance): re-provenance 19dc43ec`, a
proper `reprovenance_bypass.sh`-style empty commit with `Reprovenance: 19dc43ec693ffaf847e604a61e3dd139f7ee49b9` +
`Quickmerge: agent` trailers, exactly the §4 recipe this skill would have applied. `ldr-to-main-promote.yml` /
`ldr-to-main-promote-fleet.yml` both show `success` for that sha at 03:15:04-03:15:06Z. `branch-health` has been green
since (02:44:47Z, 01:33:50Z runs).

**Disposition: resolved before this pass started. No action taken (redundant fix attempted independently during this
session — see the Session Note below — self-resolved to a no-op since upstream already had it).**

### 8. sit-unlock FAILED at 12:52AM ("SIT Failed — staging unlocked, breaking_pending kept") — RESOLVED, superseded

`sit-unlock.yml` (triggered by `repository_dispatch: [sit-failed, sit-passed]`): on `sit-failed` it unlocks staging but
keeps `breaking_pending` (exactly the alert's wording); on `sit-passed` it unlocks AND clears `breaking_pending`.
Current live `workspace-manifest.json` (fetched fresh from `main`):
`{"locked": false, "locked_since": null, "locked_reason": "SIT passed — validated + unlocked", "pending_repos": [], "sit_retry_count": 0, "breaking_pending": []}`.
The most recent `sit-unlock.yml` run (`31456511847`, 03:48:30Z) fired with `SIT_EVENT=sit-passed`, cleared
`breaking_pending`, posted "✅ SIT PASSED — staging UNLOCKED, breaking_pending cleared. Promotion queue flowing." —
directly supersedes the 12:52AM failure.

Context: staging's lock machinery has been dormant since the 2026-07-23 staging-machinery shutdown per this workflow's
own comment — `locked: false` is close to steady-state regardless, consistent with CLAUDE.md's "staging DORMANT" note.

**Disposition: resolved. No follow-up.**

### 9. reconcile-release-tags WARNING: ibkr-gateway-infra — 27 unreleased commits, newest tag v0.5.0 16.1 days old — VERIFIED FALSE ALARM

Checked the actual OUTCOME, not just run conclusion, per this skill's explicit instruction (recalling the prior
41-day-silent-zero-tags incident). `semver-agent`'s latest run (`31323985362`, success, 2026-08-09T16:30:53Z) log shows:
`"Compute next semver via diff analysis"` succeeded, then `"Apply version bump"` was `skipped` with the runtime line
**"No feat:/fix:/breaking commits or API changes found. Skipping version bump."** — confirmed correct by direct diff:
`git diff --stat b6a418a6..origin/main -- ibkr_gateway_infra/` is **empty**. All 27 commits since `v0.5.0` are squashed
`chore(promote): LDR → main (Option-B direct)` merges that never touched the versioned `ibkr_gateway_infra/` source dir
(terraform/docs/scripts elsewhere in the repo only).

**Disposition: not a bug. semver-agent is working exactly as designed — there is genuinely nothing to release. No
follow-up.**

### 10. LDR→main fleet bot: auto-merge ARM FAILED for market-tick-data-service (PR exists, provenance-clean) — SUPERSEDED BY A NEW, DIFFERENT, STILL-OPEN FINDING

The original alert's framing (arm-needed, otherwise clean) is now stale: auto-merge IS armed on PR #950
(`enabledAt: 2026-08-11T05:01:02Z`), but the PR — and **`live-defi-rollout` itself** — are now genuinely red on a
**different, newly-introduced** gate: the 900-line hard file-size cap.

```
❌ Files exceed 900 lines:
  ./market_tick_data_service/engine/orchestrator/partitioned_writer.py: 906 L
  ./market_tick_data_service/scripts/migrate_tradfi_canonical_2026_07.py: 905 L
```

Root cause confirmed via `git blame`/`git show`: introduced by `e5581a63` ("feat(tradfi): canonicalize chain underlying
naming convention (writer+executor+W2)", 2026-08-11T02:00:29Z) — a genuine feature commit, not a fast-path blind spot
(both files are real, dense production code; there is no padding/blank-line slack to trim safely — the 9.5.31-style
`wc -l`/`--pop` gate comment in `base-service.sh` explicitly frames this as "each repo's own pre-existing size debt
stays an explicit, auditable allow-list" via `FUNCTION_SIZE_EXTRA_EXCLUDES`, i.e. a real per-repo decision, not a
mechanical fix). `e5581a63` is an ancestor of the current LDR tip (`486f82ba`, 3 commits ahead), so this is not a
stale-PR-snapshot race (§1g) — the violation is live on trunk right now.

**Not fixed this pass** — deliberately, per this skill's own guidance ("if the root cause requires deep Cloud Build
config work beyond a clean scoped fix, file it precisely rather than guessing"; the equivalent here is a real
split-vs-exempt engineering decision, not a config tweak). Blindly adding both files to `FUNCTION_SIZE_EXTRA_EXCLUDES`
would silently accept new size debt without anyone deciding that's the right call; blindly splitting either file risks a
bad module boundary in tradfi-canonical-naming-sensitive code without owner review.

**Disposition: RESOLVED (2026-08-11, later same day, follow-up session)** — the operator authorized the split. Fixed by
`market-tick-data-service@b13e3a2b` (a parallel session, `[slot-4·laptop]`): `partitioned_writer.py` 906L→846L
(extracted 4 pure chain-partition-dims/timestamp helpers into `engine/orchestrator/chain_partition_dims.py`, zero
call-site changes) and `migrate_tradfi_canonical_2026_07.py` 905L→562L (extracted the classification half into
`scripts/migrate_tradfi_canonical_classify_2026_07.py`, 45 names re-exported). That same commit also fixed a
reader-routing bug from `c31cfe7a`'s combo→combo_chain rename (3 stale tests) — full detail archived at
`/plans/active/issues/mtds_combo_chain_rename_broke_three_tests_2026_08_11.md`.

**A further follow-up session then found `b13e3a2b`'s own promote PR (#952) still red** on a NEW gate: both
`migrate_tradfi_canonical_classify_2026_07.py` (new, from the split) and
`migrate_tradfi_underlying_display_names_2026_08.py` (new, from `486f82ba`) carried the fleet's common blanket
file-level `# pyright: reportX=false, ...` suppression header, net-new relative to `main`'s diff base (STEP 5.94's
diff-scoped attribution ratchet — passes on `live-defi-rollout` pushes since those files are pre-existing there, but
fails on the promote-PR's diff against `main`, where they're brand new). Fixed by converting both files to narrow
per-line `# pyright: ignore[exactRule]` suppressions plus two genuine type-safety improvements (a typed `_Args`
dataclass boundary for the file's `argparse.Namespace` usage, a named function replacing an unannotated lambda passed to
`ThreadPoolExecutor.map`) — verified `0 errors, 0 warnings, 0 notes` on both files with the blanket headers fully
removed. Two more moving-target regressions from the same actively-iterating parallel session were ridden out (not fixed
here) on the way to shipping: a test-collection break from an unrelated `instrument_id`-blank design change (`fbc9cc6f`)
self-resolved when that session shipped its own follow-up (`143fceff`, deleted the now-backwards restamp script + test);
a workspace-wide cross-repo check flagged an unrelated, already-tracked `deployment-service` file (`meta_watchers.py`,
out of scope — see `data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`'s own todo for it) — `quickmerge.sh`
itself classified this as duration-budget/host-contention once MTDS's own core gate was independently confirmed green,
and the ship went through with `IGNORE_TIMEOUT=true`.

**Shipped**: `market-tick-data-service@ccb84c57c9` via
`quickmerge.sh --agent --files 'market_tick_data_service/scripts/migrate_tradfi_canonical_classify_2026_07.py market_tick_data_service/scripts/migrate_tradfi_underlying_display_names_2026_08.py'`.
Landed on `live-defi-rollout`; `quality-gates-v2` = SUCCESS for that sha (confirmed via `gh run list`).
Promote-to-`main` not yet confirmed as of this edit — the `ldr-to-main-promote-fleet.yml` fleet job runs on its own
`*/15` cadence and was deliberately NOT manually dispatched (CLAUDE.md's ad-hoc-dispatch ban — shared single-concurrency
slot).

### 11. cloud-build-failure-watcher CRITICAL: unified-api-contracts@`a621b0d` TIMEOUT (build `995609a7`) — ROOT-CAUSED + FIXED (combined with item 5)

The alert's "recovered per 2:34AM 'no failed Cloud Builds this tick'" claim is **WRONG**.
`gcloud builds list --filter='substitutions.REPO_NAME="unified-api-contracts"'` shows **the last 20 consecutive Cloud
Builds are ALL TIMEOUT**, spanning 2026-08-10T18:36Z→2026-08-11T03:52Z (9+ hours) — including both alert-cited builds
(`a2327132`/ item 5 and `995609a7`/item 11, neither "transient" nor "recovered"). Every build log shows the identical
signature:

```
Step #4 - "quality-gates": [qg-governor] unknown (5500MB) waiting: WAIT_RAM_LIVE 30s
... (repeats every 30s) ...
Step #4 - "quality-gates": [qg-governor] unknown (5500MB) waiting: WAIT_RAM_LIVE 510s
TIMEOUT
```

Root cause, confirmed by direct code read of `qg-host-governor.sh`: `_qg_repo_peak_mb()` resolves the repo key from
`${QG_GOVERNOR_REPO:-${SERVICE_NAME:-unknown}}` — UAC's `cloudbuild.yaml` `quality-gates` step set neither env var, so
the governor always saw repo=`"unknown"`, which has no `qg_resource_baseline.json` entry and therefore falls back to
`QG_UNMEASURED_PEAK_MB` (default **5500 MB**) — even though `unified-api-contracts`'s REAL measured baseline is only
**~1.1GB** (`peak_rss_mb: 1097` local / `1117` vm, both entries present in the baseline file). The admission check is
`avail < this + floor → WAIT_RAM_LIVE`; on this step's `E2_HIGHCPU_8` machine (8 vCPU / 8GB RAM total), a 5500MB
reservation plus the floor can easily exceed live-available RAM once `apt-get`/`pip install -e .`/basedpyright are also
running in the same container — an unwinnable wait that only ends at the Cloud Build step's own timeout. Every attempt
fails identically because it's systematic, not transient; Cloud Build itself is not globally down (other repos, e.g.
MTDS, built successfully in the same window). GH Actions `quality-gates-v2` for the same shas was genuinely green
throughout — it's a separate pipeline (no Docker-frozen-export step), so its green status does not imply
Cloud-Build-green, and the alert's dismissal conflated the two.

**Fix shipped**: added `QG_GOVERNOR_REPO=unified-api-contracts` to the `quality-gates` step's env in
`unified-api-contracts/cloudbuild.yaml`, so the governor resolves the real ~1.1GB baseline instead of the 5500MB
unmeasured-repo default.

**A second, unrelated, currently-live regression blocked shipping this fix** and was root-caused + fixed in the same
commit (discovered because `quality-gates.sh --no-fix` — required green before any commit — failed on the unmodified
tree): `unified_api_contracts/registry/tradfi_symbology.py`'s `resolve_tradfi_underlying_to_root()` was mis-resolving
the genuine multi-root composite `LIVE-CATTLE-LEAN-HOG` (two real 2-word commodity names concatenated — Live Cattle
`LE` + Lean Hog `HE`) to a single root `LE`, silently discarding the second leg. Root cause: the function's right-trim
loop tried progressively shorter token prefixes (4→3→2 tokens) rather than trimming exactly one trailing "basis/location
suffix" token as the docstring's own stated intent describes (the `NAT-GAS-HH → NAT-GAS` case, dropping exactly one
token `HH`) — at 4 tokens, trimming down to the first 2 (`LIVE-CATTLE`) accidentally alias-matched a real, different
commodity, silently fabricating a canonical form for a composite that should stay honestly unchanged (the exact "no
single root, don't force one" invariant the function's own docstring commits to). Introduced by `8b8e9a33` (2026-08-11,
~05:00-06:00Z window, "feat(registry): add canonical_tradfi_underlying SSOT resolver..."), caught by that same commit's
own test (`test_multi_root_and_garbage_unchanged[LIVE-CATTLE-LEAN-HOG]`) — GH Actions `quality-gates-v2` for `8b8e9a33`
correctly showed `failure` (confirmed via `gh run list`, not assumed). Fix: restrict the trim to drop exactly the LAST
token only (`tokens[:-1]`, requiring >=3 tokens so >=2 remain), matching the documented single-suffix intent; verified
against every existing parametrized case (`NAT-GAS-HH`, `WTI-BZ`, `LIVE-CATTLE`, `WHEAT-CORN`, etc.) via the full test
suite, not just the one failing case.

`quality-gates.sh --no-fix` green (both fixes together, full test suite) before shipping.

**Shipped**: `unified-api-contracts@d7453edfec` via
`quickmerge.sh --agent --files 'cloudbuild.yaml unified_api_contracts/registry/tradfi_symbology.py'` (single commit,
both fixes — the cloudbuild.yaml change could not ship alone without the tree being green). Landed on
`live-defi-rollout`, post-push ancestry verified.

**Disposition: resolved, both fixes shipped this pass. Verification note**: Cloud Build itself only runs on a push that
triggers the `unified-api-contracts-live-defi-rollout` Cloud Build trigger — the governor fix's actual effect (a
successful Cloud Build, not just a green `quality-gates.sh` locally) can only be confirmed on the next such trigger.
Flagging as a verification follow-up below rather than claiming a Cloud Build success this pass (no such build had run
yet against the fix as of this doc's writing).

### 12. branch-health WARNING: unified-trading-pm LDR→main lag, 14 commits, PR #2758 — RESOLVED via item 7

Same root cause as item 7's provenance block. `branch-health.yml` has been green since (02:44:47Z run).

**Disposition: resolved via item 7's fix. No separate action.**

### 13. ldr-ci-monitor INFO: unified-trading-pm@live-defi-rollout RED→GREEN (`ba8229d1`) — RESOLVED, confirmed via item 3

**Disposition: resolved. No follow-up.**

### 14. python-quality-gates-v2 CRITICAL: PM push to `promote/unified-trading-pm/c3d5dd1d6814`, sha `c3d5dd1d6814` FAILED — RESOLVED via item 7

This promote-branch failure predates the provenance-gate deadlock's ultimate resolution; the branch itself never needed
separate handling — the underlying LDR trunk is green and the provenance block (item 7) that was gating `main`-bound
promotion is cleared.

**Disposition: resolved via item 7's fix. No separate action.**

### 15/16. python-quality-gates-v2 CRITICAL: deployment-service PR #856 + push to live-defi-rollout, sha `ecf711d8808b` FAILED — RESOLVED, verified fixed by another AO worker

Root-caused independently during this pass (before discovering it was already fixed):
`deployment_service/ deployment_profile_derivation.py:276` had a bare `print(yaml.safe_dump(...))` in a CLI entrypoint
(`main()` / `if __name__ == "__main__"`), which is legitimate CLI stdout output (the derivation result), not a log event
— but it isn't covered by `base-service.sh`'s `print()`-ban glob exclusions (`**/cli/main.py`, `**/cli/_shim.py`,
`**/__main__.py`), so it tripped `codex compliance FAILED: 2 violations (max allowed: 1)` (the 2nd, pre-existing,
already-baselined violation is an unrelated hardcoded-project-ID-in-tests line). Introduced by
`13223da3 (2026-08-11T00:29:01Z, [slot-10·planning])`.

**Already fixed by the time of shipping**: `ikennaigboaka [slot-19·planning]` shipped
`0e2619cfb9288651ecb1a1026278f42810a00f17` at 2026-08-11T03:34:42Z —
`fix(deployment): annotate CLI plan stdout as qg-print for codex compliance` — the identical fix (a `# noqa: qg-print`
marker), independently root-caused by another AO worker. `deployment-service` `live-defi-rollout` is green (latest
success `1fa6a33d`, 05:25:34Z).

**Disposition: resolved before this pass's fix landed — the independently-authored duplicate fix self-resolved to a
no-op via `git stash pop` conflict (see Session Note). No action needed.**

### 17. branch-health WARNING: unified-trading-pm (12 commits, PR #2765) + deployment-service (3 commits, PR #856) lagging — RESOLVED via items 7 and 15/16

**Disposition: resolved via items 7 and 15/16's fixes (both by other AO workers). No separate action.**

## Structural findings (operator-notification-worthy, not directly fixable this pass)

### A. No AO `wall_type` covers Cloud Build failures

Direct read of `agent-orchestrator/server/escalation.py`'s `WALL_TYPES` frozenset (line 50): `merge_conflict`,
`label_mismatch`, `sit_failure`, `stuck_promotion_pr`, `ldr_qg_failure`, `ldr_main_qg_failure`, `main_ci_red`,
`plan_health`, `sit_retry_cap`, `data_pipeline_failure`, `harness_lint`, `provenance_blocked`. None of these map to a
Cloud Build (`gcloud builds` / `cloudbuild.yaml`) failure — a repo's GH Actions `quality-gates-v2` can be green while
its Cloud Build image pipeline is completely broken (exactly item 2's and items 5+11's shape) and AO has no mechanism to
ever notice, page, or auto-fix it. Both real fixes in this batch (features-service's stale lock, unified-api-contracts'
governor livelock) were caught by a human/interactive session reading the raw `cloud-build- failure-watcher` Slack alert
and manually running `gcloud builds log`/`gcloud builds list` — there is no automated path from "Cloud Build
TIMEOUT/FAILURE" to an AO-dispatched fix attempt.

### B. No AO `wall_type` covers `main-backmerge-to-ldr` sync failures

Item 4 (instruments-service `git fetch` exit 128) self-healed on its own next scheduled run, but had it NOT self-healed,
nothing in `WALL_TYPES` would have escalated it — same gap as (A), a distinct failure class (backmerge sync, not a
promotion-PR QG failure) with zero AO coverage.

Both (A) and (B) are cross-cutting AO-architecture gaps, not single-repo bugs — flagging per the findings-triage HARD
RULE ("big finding... cross-cutting... NOTIFY OPERATOR") rather than attempting an in-band fix to
`agent-orchestrator/server/escalation.py`'s wall taxonomy in this pass (adding a new wall_type needs its own
escalation-worker prompt template + routing decision, a design change, not a same-pass mechanical fix).

### C. Incidental: 7 `github-glue-slot-refresh-*` systemd units failing on the self-hosted-runner host

Surfaced during the §0c host-monitor sweep (out of the original 17 items, flagging because it's a live, currently-
unattended-failing component on a monitored host): on `i-042a6332509482556` (ap-northeast-1), all 7
`github-glue-slot-refresh-<repo>.service` units (ao, e2e-testing, execution-service, features-service,
market-tick-data-service, ml-service, strategy-service) are in `failed` state, retrying every ~10 min and failing every
time with `fatal: could not read Username for 'https://github.com': No such device or address` /
`[slot-refresh] FF-pull FAILED — the mirror is dirty or diverged. NOT forcing.`. This is a git-credential problem on the
host's periodic mirror-refresh side-timer — confirmed NOT affecting the actual glue runners themselves
(`github-glue-runner-*@glue-1.service`/`@writer-1.service` all `active running`), only the mirror-refresh side job.
Scope/impact not investigated further (out of this pass's assignment) — filed as a follow-up below.

## Session note: a redundant independent fix attempt

During this pass, before discovering items 7 and 15/16 were already fixed by other AO workers, this session
independently root-caused and attempted to ship functionally-identical fixes for both (a `reprovenance_bypass.sh`-
equivalent for item 7 was not attempted since it was already resolved by the time of inspection; for item 15/16, a
`# noqa: qg-print` edit was made, staged, and hit a `git stash pop` conflict during `quickmerge.sh`'s dependency
auto-pull step because `origin/live-defi-rollout` had already gained the equivalent fix mid-run). The conflict was
resolved by taking upstream's already-shipped content (confirmed byte-identical intent, different comment wording); the
working tree now exactly matches `origin/live-defi-rollout` with no local diff — no duplicate commit was created. Noting
this only because it's a clean illustration of the "already resolved — don't re-fix" pattern this skill exists to catch,
not because anything needs follow-up.

## Follow-ups

- [x] [CODE] P1. **Split or explicitly except the two MTDS files that crossed the 900-line hard cap** (item 10) — DONE
      via split (preferred option). `market-tick-data-service@b13e3a2b` (partitioned_writer.py 906L→846L,
      migrate_tradfi_canonical_2026_07.py 905L→562L) + `market-tick-data-service@ccb84c57c9` (follow-up fix for a
      net-new blanket-pyright-suppression-header regression the split's new files introduced on the promote PR). Full
      writeup of the reader-routing regression:
      `/plans/active/issues/mtds_combo_chain_rename_broke_three_tests_2026_08_11.md`; the blanket-suppression-header fix
      is detailed in item 10 above. (repo: market-tick-data-service)
- [ ] [CODE] P2. **Add an AO `wall_type` for Cloud Build failures** (Structural finding A): no escalation path exists
      from a `cloud-build-failure-watcher` CRITICAL alert to an AO-dispatched fix attempt today — every Cloud-Build-
      only failure (GH Actions can stay green) depends on a human reading Slack. Needs a new `wall_type` in
      `agent-orchestrator/server/escalation.py`'s `WALL_TYPES`, a routing decision (likely the generic `escalate`
      worker, same shape as `main_ci_red`), and a trigger wired from `cloud-build-failure-watcher.yml`'s CRITICAL path.
      (repo: agent-orchestrator)
- [ ] [CODE] P2. **Add an AO `wall_type` for `main-backmerge-to-ldr` sync failures** (Structural finding B): same gap as
      above for a distinct failure class (backmerge `git fetch`/merge failures, not promotion-PR QG failures). Item 4
      happened to self-heal; a non-self-healing recurrence has zero AO coverage today. (repo: agent-orchestrator)
- [x] [OPERATOR] P2. **Verify the unified-api-contracts Cloud Build fix actually clears the TIMEOUT loop on its next
      real trigger** (item 11 follow-up) — VERIFIED CLEARED.
      `gcloud builds list --project=central-element-323112 --region=asia-northeast1 --filter='substitutions.REPO_NAME="unified-api-contracts"'`
      shows build `4465fc18-3277-4711-abd3-f86daac715e0` for `d7453ed` (the fix commit itself, self-triggering on push
      to `live-defi-rollout`) is `SUCCESS`, 2026-08-11T06:10:24Z→06:14:01Z (~3.5min total, through
      `publish-python`/`PUSH`/ `DONE`) — vs. the prior 20-build TIMEOUT streak (18:36Z→05:55Z, each hitting the 10min
      step timeout). Full build log (`gcloud builds log 4465fc18-...`) has **zero** `[qg-governor] ... WAIT_RAM_LIVE`
      lines (the only "governor" hit is the commit-message echo) — the admission wait loop that caused every prior
      TIMEOUT never fired at all, confirming the governor now resolves UAC's real ~1.1GB baseline via `QG_GOVERNOR_REPO`
      instead of the 5500MB unmeasured-repo fallback. Note: build `49413a09` for `8b8e9a3` (05:55:16Z, still pre-fix)
      also TIMEOUT — expected, it predates `d7453ed`; not a regression. No further action needed. (repo:
      unified-api-contracts, evidence: build=4465fc18-3277-4711-abd3-f86daac715e0)
- [ ] [CODE] P3. **Fix the 7 failing `github-glue-slot-refresh-*` systemd units** on host `i-042a6332509482556`
      (Structural finding C): git-credential failure (`could not read Username for 'https://github.com'`) on the
      periodic mirror-refresh side-timer for ao/e2e-testing/execution-service/features-service/
      market-tick-data-service/ml-service/strategy-service. Does not affect the live glue runners themselves, but is an
      unattended-failing component retrying every ~10 min. (repo: unified-trading-pm, host infra)

## §6 three-sweep verification checklist (per the `/ci-reconcile` skill)

1. **Sweep 1 — every repo in the registry** (26 repos, `unified-trading-pm/workspace-manifest.json`): swept via
   `gh run list --branch live-defi-rollout` for all 26. All green at the time of the final sweep in this pass EXCEPT
   `market-tick-data-service` (item 10's new file-size regression — OPEN, filed above).
2. **Sweep 2 — every GH-Actions-native standing monitor** (~23 catalog-derived,
   `unified-trading-pm/docs/repo- management/CICD-WORKFLOW-CATALOG.md` regenerated fresh this pass): 23/23 green, all
   firing within their declared schedule cadence. Two (`glue-pool-starvation-monitor`, `glue-runner-health-monitor`)
   initially looked stale but are confirmed intentionally `workflow_dispatch`-only since 2026-08-07 (PM's self-hosted
   `glue` pool retired when the repo went public) — not a gap.
3. **Sweep 3 — every host/VM-dispatched monitor** (enumerated via
   `grep -rl "dispatch_alert\|repository_dispatch" scripts/self-hosted-runners/*.sh`): `ci-vm-resource-watchdog.timer`
   and `glue-runner-crash-loop-watchdog.timer` on `i-042a6332509482556`, both confirmed healthy via live SSM query
   (last-fire timestamps within their declared cadence, underlying `.service` units correctly `inactive dead` between
   oneshot runs). AWS SSM access WAS available in this environment (not a coverage gap this pass) — verified via
   `aws ssm describe-instance- information` succeeding. Incidental finding C (7 failed glue-slot-refresh units) surfaced
   during this sweep and is filed above.

**Bar for "unblocked" per the skill**: every item from sweeps 1-3 now has an explicit, current, verified-clean status.
Item 10 (MTDS file-size regression) is RESOLVED as of the follow-up session documented above
(`market-tick-data-service@ccb84c57c9`, `quality-gates-v2` green on `live-defi-rollout`; promote-to-main pending the
fleet job's own cadence). The item-11 Cloud-Build-fix verification (P2 follow-up) was independently VERIFIED CLEARED
(see its follow-up checkbox above). All 17 original items are now resolved, self-healed, or false alarms with cited
evidence.

## Progress Log

- **context-scout 2026-08-14**: populated context_scope (4 entries)
