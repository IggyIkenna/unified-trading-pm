---
doc_type: issue
title:
  digest-drift-sweep has been a SILENT NO-OP since birth (2026-06-19) — `secrets.GITHUB_TOKEN` cannot read another
  repo's contents, so all 16 image repos are misreported as "Dockerfile not found" and ZERO digest refreshes have ever
  been dispatched
summary: >
  `digest-drift-sweep.yml` is the fleet-wide safety net that refreshes stale `ARG BASE_IMAGE_DIGEST` pins for cases (b)
  UAC/base-layer republishes that don't ride a UTL version-bump and (c) new repos not yet in the UTL dep-graph. It
  fetches each repo's Dockerfile via `GET /repos/{owner}/{repo}/contents/Dockerfile` using `GITHUB_TOKEN: ${{
  secrets.GITHUB_TOKEN }}` (digest-drift-sweep.yml:77). The default `GITHUB_TOKEN` is scoped to the WORKFLOW'S OWN repo
  (unified-trading-pm) and cannot read contents of sibling repos, so every cross-repo fetch 404s. The fetch uses `curl
  -sf ... || echo ""` (:128-131), which converts that 404 into an empty string, and the empty string is then
  misinterpreted by the next branch (:138-142) as "Dockerfile not found — skipping (repo may not be image-building)".
  The sweep therefore reports `Dispatched: 0 / Already fresh: 0 / No ARG found: 16` and exits GREEN. It has NEVER
  dispatched a single digest refresh. Verified by direct experiment: the exact curl from the workflow returns HTTP 200 +
  3719 bytes + a valid pin with a PAT, and HTTP 404 without cross-repo scope. All 16 repos DO have a Dockerfile carrying
  `ARG BASE_IMAGE_DIGEST`, and ALL are stale vs the current UTL `:latest` (`sha256:5122f7ab…`) — they sit on at least 5
  distinct older digests (`b7e391f8…` ×4, `be51b33f…`, `d15fb29b…`, `9594091a…`, `56bd0fe5…`). Born broken in 0d5663d4d
  (2026-06-19); `git log -S` confirms the token line was NEVER `GH_PAT`. ~27 days x 4 runs/day ≈ 110 green runs that did
  nothing. NOT caused by the CI-cost runner flip (23ce709cc touched only `runs-on:`); the flip merely caused the log to
  be read. The second-order bug: the `POST /dispatches` at :160-176 uses the SAME out-of-scope token, so fixing only the
  fetch would surface a wave of 403/404s at the dispatch step instead.
status: open
nature: notes
asset_group: [ci]
stage: [meta]
repos:
  [
    unified-trading-pm,
    agent-orchestrator,
    alerting-service,
    batch-live-reconciliation-service,
    client-reporting-api,
    deployment-api,
    deployment-service,
    execution-service,
    features-service,
    fund-administration-service,
    greeks-service,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
    ml-service,
    strategy-service,
    trading-agent-service,
  ]
scope: [engineer, admin]
tags:
  [ci-cd, digest-ratchet, base-image, github-token, token-scope, silent-failure, green-but-wrong, supply-chain, fleet]
related:
  [
    /plans/archive/2026_06/build_operability_smoke_all_repos_2026_06_19.md,
    /plans/archive/2026_07/github_actions_ci_cost_reduction_2026_07_15.md,
    /plans/archive/issues/base_image_digest_sweep_broken_fleet_builds_red_2026_07_18.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-07-16
author: unknown
parent_epic: deployment_and_user_management_master
priority: P1
source:
  github_actions_ci_cost_reduction_2026_07_15 batch-2 validation, slot 1, 2026-07-16 — found while proving the flipped
  workflows land on the glue pool; reading the sweep's log to confirm it was safe to re-dispatch revealed it had never
  done anything
assigned_vm: NA
execution_scope: local-only
assigned_role: cicd
drift_direction: advance-code
last_updated: 2026-07-16
locked_by:
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/issues/post_cutover_silent_assumption_sweep_2026_07_23.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    .github/workflows/digest-drift-sweep.yml,
  ]
resolved_by:
depends_on: []
---

# digest-drift-sweep: green for 27 days, dispatched nothing

> ## 🟢 3-of-4 FIXED (2026-07-26) — token + silent-failure hardening shipped; only the dormant-cascade question remains
>
> _(2b/2c/3 fixed 2026-07-26 per `plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md` todo 3, slot-5/infra.
> Prior measurement 2026-07-26 by `/plan-reconcile ci` — rows below updated against the live file post-fix.)_
>
> This doc's root-cause section still reads present-tense (`digest-drift-sweep.yml:77` passes
> `GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}`). **That is no longer true.** Scoring this doc's own § "Revised
> recommendation" 1-4:
>
> | recommendation                                                                  | state now                                                                                                                                                                                                                                                                  |
> | ------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
> | 2a. token → `secrets.GH_PAT`, **both** the fetch and the dispatch POST          | ✅ **DONE** — `:82 GH_PAT: ${{ secrets.GH_PAT }}`, `:122 TOKEN="${GH_PAT}"` feeds both `:134` (fetch) and `:166` (dispatch). `unified-trading-pm@f6e98bbdd` (2026-07-18 11:51:54, verified ancestor of `origin/live-defi-rollout`)                                         |
> | 2b. capture the HTTP status on the FETCH (`404` benign · `401/403` fail loudly) | ✅ **DONE** — the fetch now uses `-o "$BODY_FILE" -w '%{http_code}'`; `200` parses, `404` on both branches is a benign skip (still counted in `SKIPPED_NO_ARG`), anything else (`401`/`403`/etc.) `exit 1`s the step loudly. `unified-trading-pm@6cb21eca3` (2026-07-26)   |
> | 2c. self-auditing assertion (`dispatched + fresh == 0` ⇒ exit non-zero)         | ✅ **DONE** — the summary now asserts `Dispatched + Already fresh + Capped == 0` (over a non-empty `IMAGE_REPOS`) and `exit 1`s; `CAPPED` counts as "found and would have dispatched" so a cap-bound run is never mistaken for the failure. `unified-trading-pm@6cb21eca3` |
> | 3. add a dispatch cap (`--max-dispatches`)                                      | ✅ **DONE** — `workflow_dispatch.inputs.max_dispatches` (default `5`) bounds real `/dispatches` POSTs per run; repos beyond the cap are deferred to the next tick and counted separately. `unified-trading-pm@6cb21eca3`                                                   |
> | 1. investigate the dormant primary cascade FIRST                                | ❔ unchanged by this note — still open                                                                                                                                                                                                                                     |
>
> Proven via `scripts/quality-gates-base/tests/test-digest-drift-sweep-silent-failure-hardening.sh` (extracts the live
> workflow's embedded bash and exercises all 8 cases: benign-absent-Dockerfile negative test, 401/403 loud-failure,
> dispatch-cap bounding, and the self-audit assertion's positive/negative cases — all 8 pass against the fixed workflow,
> the structural anchor fails against the pre-fix commit). The loud-failure path (401/403) was proven this way rather
> than via a live `workflow_dispatch` run: forcing a real 401/403 would require deliberately de-scoping the shared
> `GH_PAT` secret that other production dispatches also depend on, which is not an acceptable side effect for a routine
> hardening change.
>
> **Independent corroboration that the token fix landed and changed behaviour**: the sibling doc
> [/plans/archive/issues/base_image_digest_sweep_broken_fleet_builds_red_2026_07_18.md](/plans/archive/issues/base_image_digest_sweep_broken_fleet_builds_red_2026_07_18.md)
> records the same commit; and
> [/plans/active/issues/post_cutover_silent_assumption_sweep_2026_07_23.md](/plans/active/issues/post_cutover_silent_assumption_sweep_2026_07_23.md)
> § F4 now observes `"Dispatched 16 / Already fresh 0"` — the sweep is reaching Dockerfiles, which the pre-fix
> `No ARG found: 16` proved it never did. F4 flags a **new** problem in its place (it never converges and fans out to
> `ubuntu-latest`, so it now costs real money) — that non-convergence is tracked as an open todo there, not here.
>
> Net: this doc is **not** resolved; it is 3-of-4 done. The remaining open item is recommendation 1 — investigate why
> the primary `update-dependency-version.yml` cascade has been dormant — which this doc itself said should be
> investigated FIRST/alongside, and which is out of scope for the hardening todo that closed 2b/2c/3.

## What it was supposed to do

`digest-drift-sweep.yml` (added 0d5663d4d, 2026-06-19) is the periodic backstop for the FROM-digest ratchet. Every 6
hours it should: resolve the current UTL `:latest` digest, read each image repo's `Dockerfile`, compare
`ARG BASE_IMAGE_DIGEST` against it, and `POST /dispatches` a `dependency-update` to any repo whose pin is stale. It
covers the two cases the normal UTL version-bump cascade misses:

- (b) UAC / other base-layer republishes that don't ride a UTL version-bump
- (c) new repos not yet in the UTL dep-graph (never received a prior `dependency-update`)

SSOT:
[/plans/archive/2026_06/build_operability_smoke_all_repos_2026_06_19.md](/plans/archive/2026_06/build_operability_smoke_all_repos_2026_06_19.md)
Phase 5 fix-c _(archived; path repointed 2026-07-26)_.

## What it actually does

Nothing. Every run since birth:

```
  agent-orchestrator: Dockerfile not found — skipping (repo may not be image-building)
  ... (x16, every repo) ...
  Dispatched:    0
  Already fresh: 0
  No ARG found:  16
```

`Already fresh: 0` is the tell. If the sweep were working and the fleet were current, this would read
`Already fresh: 16`. Zero in BOTH the "dispatched" and "fresh" buckets means it never successfully looked at a single
Dockerfile — it just doesn't say so, because the branch it lands in is worded as a benign skip.

## Root cause

`digest-drift-sweep.yml:77` passes the default token:

```yaml
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

The default `GITHUB_TOKEN` is minted per-run and scoped to **the workflow's own repository**. A cross-repo
`GET /repos/IggyIkenna/<other>/contents/Dockerfile` returns **404** (GitHub returns 404 rather than 403 for unauthorised
reads, to avoid leaking repo existence).

Two coding choices turn that 404 into a green run:

1. `:128-131` — `CONTENT=$(curl -sf ... || echo "")`. `-f` makes curl exit non-zero and emit nothing on HTTP >= 400;
   `|| echo ""` swallows it. The HTTP status is never captured or checked.
2. `:138-142` — an empty `CONTENT` is attributed to a benign cause:
   `"Dockerfile not found — skipping (repo may not be image-building)"`. A permission failure and a genuinely
   Dockerfile-less repo are indistinguishable at this point, and the code guesses the harmless one.

### Verification (not inference)

The exact curl from the workflow, run against `execution-service`:

| Auth                      | Result                                                                 |
| ------------------------- | ---------------------------------------------------------------------- |
| PAT with cross-repo scope | `HTTP 200`, 3719 bytes, `ARG BASE_IMAGE_DIGEST=sha256:b7e391f8…` found |
| No cross-repo scope       | `HTTP 404` → `curl -sf` → empty → "Dockerfile not found"               |

And the repos are demonstrably image-building — local workspace check, all carry the ARG:

```
agent-orchestrator        sha256:b7e391f8…      instruments-service       sha256:be51b33f…
execution-service         sha256:b7e391f8…      market-tick-data-service  sha256:d15fb29b…
ml-service                sha256:b7e391f8…      deployment-api            sha256:9594091a…
strategy-service          sha256:b7e391f8…      features-service          sha256:56bd0fe5…
```

Current UTL `:latest` = `sha256:5122f7ab87a26d13a7c544529ae779fcd9393c3e386cd6b764734bd69ed24de4`. **None match.** Every
sampled repo is stale, on at least 5 distinct older digests — consistent with "the drift net has never caught anything".

### Provenance

- `0d5663d4d` (2026-06-19) — born with `secrets.GITHUB_TOKEN`.
- `git log -S'GITHUB_TOKEN: ${{ secrets.GH_PAT }}'` on the file → **no commits**. It was never correct.
- `23ce709cc` (2026-07-16, CI-cost B1 batch 2) — touched `runs-on:` only. **Not the cause**; it is how the log came to
  be read.

## Impact

The digest ratchet's (b)/(c) safety net has been absent since it was written. Any base-layer republish that didn't ride
a UTL version-bump has gone unpropagated, and any repo outside the UTL dep-graph has never been refreshed. The fleet's
observed digest spread (5+ distinct pins) is the visible symptom. Severity is bounded by the fact that the PRIMARY path
(the UTL version-bump cascade) still works — this is the backstop, not the main line — but it means base-image security
patches only reach repos that happen to get a version-bump.

## Fix — and why it is NOT a one-liner to be applied unattended

The minimal change is `GITHUB_TOKEN: ${{ secrets.GH_PAT }}` at :77. **Do not apply it without deciding the blast radius
first**, for three reasons:

1. **It un-dams a 16-repo fan-out on the first run.** Every repo is stale, so the first correct sweep dispatches
   `dependency-update` to all 16 simultaneously, each of which opens a digest-refresh commit to LDR and triggers that
   repo's CI. That is a real fleet event and wants to be a deliberate, watched one — not a 6-hourly cron's surprise.
   `force_all` is NOT needed to trigger this; the staleness alone does it.
2. **The replacement token needs cross-repo scope on all 16 image repos** — `contents: read` **and** `POST /dispatches`.
   Missing either re-creates this exact failure in the same green-but-doing-nothing way, which is the hardest kind to
   catch because from the outside it is indistinguishable from the fix having worked. **Verify against a real cross-repo
   fetch before declaring this fixed** — the `curl` in § "Root cause" returns 200 with scope and 404 without; that is
   the test.
3. **The dispatch step has the same defect.** `:160-176` POSTs `/dispatches` with the same `$TOKEN`. Fixing only the
   fetch moves the failure from "silently reports not-found" to "loudly reports HTTP 403/404 at dispatch" — which is
   better, but is a second change, not a side effect of the first.

### Also fix the silent-failure class, not just this instance

The deeper bug is that a permission failure is reported as a benign skip. Even with the right token, this code would
silently no-op on any future scope regression. Recommended alongside the token fix:

- Capture the status: `-o body -w '%{http_code}'` instead of `-sf ... || echo ""`.
- Branch on it: `404` → genuinely absent (benign skip); `401/403` → **fail the step loudly**; `200` → parse.
- Make the summary self-auditing: if `Dispatched + Already fresh == 0` while `IMAGE_REPOS` is non-empty, exit non-zero.
  That single assertion would have caught this on day one, and is the reason it ran green ~110 times.

This is the same "green but wrong" class as `/codex/02-data/honest-absence-downstream-handling.md` — an absent result
must be distinguishable from an unreadable one, and must never be silently reported as the benign case.

## Negative test that must pass after the fix

A repo genuinely without a Dockerfile must still be a benign skip (not a hard failure), and must be counted in
`SKIPPED_NO_ARG` — otherwise the fix trades a silent no-op for a noisy false alarm.

---

## UPDATE 2026-07-17 — we MEASURED what the fix would do, before fixing it (operator request)

Replicated `digest-drift-sweep.yml`'s sweep step faithfully (same repo list + order, same LDR→main fallback, same
`^ARG BASE_IMAGE_DIGEST=sha256:<64hex>` extraction, same staleness rule) but with a cross-repo-scoped token and **no
POST**. Harness: **`scripts/propagation/simulate-digest-drift-sweep.sh`** (read-only; committed 2026-07-17 — originally
left in a scratchpad and labelled "one-off", which was wrong: **re-run it before acting on this doc**, because the
answer MOVES. UTL `:latest` advances on every release and repos drift, so the "15" below is a measurement with a date on
it, not a constant).

### Result: the first correct run would dispatch to 15 of 16 repos

```
Current UTL :latest = sha256:61445152e3587bd9c65279d076f24cfc4a5880136811d0e70e27b50f38f455f9  (UTL 0.55.0)

WOULD-DISPATCH : 15   (11 stuck on sha256:b7e391f8…, plus 9594091a… x2, 56bd0fe5…, be51b33f…)
fresh          :  1   (market-tick-data-service — already at :latest)
skipped        :  0
```

Blast radius = **15 `dependency-update` dispatches ⇒ 15 digest-refresh commits to 15 LDR branches ⇒ 15 CI runs**.
Verified all 16 repos DO have `update-dependency-version.yml`, so every dispatch would be accepted (204) — the `ERRORS`
path does not fire. This is a real fleet event; it should be run **once, deliberately, watched, off-hours** — not
discovered by a 6-hourly cron.

### The 15 is a SYMPTOM — the primary cascade is ALSO dormant

`update-dependency-version.yml` **last ran 2026-06-28** in 5 of 6 sampled consumer repos (`agent-orchestrator`,
`execution-service`, `ml-service`, `market-tick-data-service`, `features-service`; `instruments-service` last ran
2026-07-13). So the cascade has not fanned out in ~19 days. **Both mechanisms that move a base-image pin are down**: the
sweep has never worked, and the cascade stopped. The sweep exists to catch the cascade failing — and it was dead when
the cascade failed, so the fleet drifted with no signal at all.

⇒ **Fixing the sweep's token treats the symptom.** If the cascade stays dormant, the backstop ends up doing the primary
path's job on every UTL release, forever. Answer "why has the cascade not fired since 2026-06-28?" BEFORE or ALONGSIDE
the token fix. That question is the real P1 here.

### Recurrence: `:latest` moves once per UTL release

The registry shows many intermediate untagged builds (7 in ~11h on 2026-07-16/17), but only a **release** carries the
`latest` tag (`0.55.0,latest`). So the sweep re-dispatches ~15 repos on each UTL release until the cascade is fixed —
UTL cut v0.48→v0.55 recently, so that is not rare.

### The sweep has NO throttle (add one)

`reconcile-release-tags` self-limits with `--max-creates 5`. `digest-drift-sweep` dispatches **every** stale repo in a
single run — there is no cap. Add `--max-dispatches` (or an equivalent) as part of the fix so the blast is bounded per
tick rather than fleet-wide-at-once.

### Also: the QG detector that already sees this is warn-only

PM's own `check_base_image_digest_drift` printed, during an unrelated 2026-07-17 QG run: _"Fleet digest INCONSISTENT — 5
distinct pins across 16 repos (missed fan-out from update-dependency-version.yml?)"_ + 15 stale repos + _"fleet pin … is
BEHIND :latest"_. It is **`warn-only, non-blocking`**, so it has scrolled past every QG run for weeks. Two independent
detectors agree on the state; neither is wired to anything that acts. Once the sweep works, that warn should become an
assertion — otherwise we keep a third detector nobody reads.

### Revised recommendation

1. Investigate the dormant cascade FIRST (or together) — the sweep is its safety net, not its replacement.
2. Fix the token (`secrets.GH_PAT`) **and** the silent-failure class (capture the HTTP status; 404 = benign skip;
   401/403 = fail loudly; assert `dispatched + fresh > 0`) **and** the dispatch POST (:160-176, same token defect).
3. Add a dispatch cap.
4. Run once, watched, off-hours, expecting 15 dispatches. Then let the cron take over.

## Todos

- [ ] [DEVOPS] P1. **Investigate why `update-dependency-version.yml`'s primary cascade has been dormant since
      2026-06-28** — recommendation 1 above remains the sole unresolved item; recommendations 2b/2c/3 already shipped
      2026-07-26.

## na-eligibility-audit verdict

**na-eligibility-audit 2026-07-30** (tranche `ci`, autonomous): KEEP-NA, valid — the sole remaining todo (why
`update-dependency-version.yml`'s primary cascade has been dormant since 2026-06-28) was re-triaged one day before this
run by `/plans/archive/2026_07/ci_satellite_ao_dispatch_batch2_2026_07_29.md` Deferred **E9**, which re-verified it
still open and concluded the root cause "is still unparked/unresolved, so no bounded fix exists to dispatch yet".
Recommendations 2b/2c/3 already shipped via ci batch1 todo 3.

**na-eligibility-audit 2026-08-01** (tranche `ci`, autonomous): KEEP-NA, valid — re-confirmed. The sole open todo is
still an unresolved root-cause investigation with no bounded fix identified; grepped `plans/active/*.md` for
"dormant"+"cascade" — the only hit (`ci_satellite_ao_dispatch_batch1_2026_07_26.md:142`) explicitly states this
investigation "remains open and out of this todo's scope," corroborating it is un-owned, not duplicated. Not
RECLASSIFY-eligible (open-ended diagnosis, not a checkable fact or scoped change).

- **context-scout 2026-08-03**: re-verified context_scope (4 entries) — all four still directly cited by the doc's own
  body; no change needed.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.

**na-eligibility-audit 2026-08-06**: KEEP-NA, valid — open-ended investigation, 3-of-4-FIXED banner, prior verdicts
stand
