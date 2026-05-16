---
title: workspace-qg.yml workflow-template — redesign needed before rollout (operator escalation)
created: 2026-05-15
author: harsh-main (audit pass)
source:
  - PM@21686e55 (slot 8: workspace-qg.yml.tmpl created)
  - PM@542f0e26 (slot 8: substitution fix in rollout script)
  - PM@128dbf03 + PM@68ba6e7c (harsh-main: UI-only template tier split)
  - alerting-service@05dec98 (slot 8: workspace-qg.yml committed to alerting-service as PoC)
locked_by: live-defi-rollout
locked_since: 2026-05-15
severity: P1 — blocks rollout of CI workflow unification across 21 Python repos
suggested_owner: ikenna-side OR opus-max-tier slot (NOT sonnet — design + trigger semantics decisions needed)
---

## TL;DR

Slot 8 (Sonnet) built `scripts/workflow-templates/workspace-qg.yml.tmpl` intending to
unify the inconsistent `quality-gates.yml` files across 21 Python service repos.
The template **omits the `live-defi-rollout` branch from its trigger list**, which
9 production repos currently rely on for every-push QG runs (hundreds of
runs/day). Rolling it out as-is would silently kill those triggers.

**UPDATE 2026-05-15 ~23:30 UTC**: dep_repos phantom-deps cleanup landed on
10 repos (separate from the trigger-unification redesign which remains open).
See § "Resolution status" at the bottom of this doc.

Operator decision 2026-05-15 ~23:00 UTC: **discard slot 8's template, file this
issue doc with full state, escalate to opus-max tier (likely Ikenna's side)
for redesign + proper rollout.**

This doc captures the full state so the redesign doesn't re-discover everything.

---

## Current per-repo trigger audit (Quality Gates workflows on origin/live-defi-rollout)

Audited 2026-05-15 22:55 UTC across all 21 Python repos. **5 distinct trigger
patterns** exist in the wild:

| Trigger pattern                                  | Repos (count)                                                                                                                                                                                                                       | Notes                                          |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------- |
| `[main, staging, live-defi-rollout]`             | deployment-api, deployment-service, execution-service, features-service, instruments-service, market-tick-data-service, market-data-processing-service, strategy-service, unified-trading-library (**9**)                          | Fires on every LDR push (hundreds/day)         |
| `[main]` only                                     | alerting-service, batch-live-reconciliation-service, ml-inference-service, pnl-attribution-service, risk-and-exposure-service, system-integration-tests, client-reporting-api (**7**)                                              | Only fires on PR-to-main (slow cadence)        |
| `[main, staging]`                                 | unified-api-contracts, ibkr-gateway-infra (**2**)                                                                                                                                                                                   | Standard target-branch pattern                 |
| `[main, develop]`                                 | position-balance-monitor-service (**1**)                                                                                                                                                                                            | Uses `develop` instead of `staging` (drift)    |

**CORRECTION 2026-05-15 23:30**: an earlier version of this table listed
ml-training-service + trading-agent-service under "empty `branches:` (parse
issue)". That was a false positive from a single-line grep; their
`quality-gates.yml` files use the multi-line YAML list form
(`branches:` then `- main` on the next line), which my grep didn't capture.
Both repos are actually `[main]`-only — adjust counts: 7 → 9 in the
`[main]`-only cluster, and remove the "empty" row entirely.

**Verified via `gh run list`**:
- execution-service: 15× `Quality Gates` on push to LDR (last 30 runs sample)
- alerting-service: 0× `Quality Gates` on push to LDR + 4× `workspace-qg` on PR-to-main from LDR (the slot 8 PoC at @05dec98)

## What slot 8 built (2026-05-15)

- `unified-trading-pm/scripts/workflow-templates/workspace-qg.yml.tmpl`:
  ```yaml
  name: workspace-qg
  on:
    push:
      branches: [main, staging]    # ⚠️ NO `live-defi-rollout`
    pull_request:
      branches: [main, staging]
  jobs:
    quality-gates:
      uses: IggyIkenna/unified-trading-pm/.github/workflows/python-quality-gates.yml@live-defi-rollout
      with:
        dep_repos: "{{DEP_REPOS}}"   # rendered from workspace-manifest.json
      secrets: inherit
  ```
- `rollout-workflow-templates.sh` enhanced with `.tmpl` substitution support
  (`{{DEP_REPOS}}`, `__REPO_NAME__`, `__SOURCE_DIR__` placeholders).
- Slot 8 ran the rollout from the **main** PM clone (not their tab), which
  dropped untracked `workspace-qg.yml` files in every Python repo's
  `.github/workflows/` in the main workspace.
- Slot 8 committed `workspace-qg.yml` to alerting-service ONLY (commit
  `05dec98`), as a proof-of-concept. The other 20 untracked files were never
  committed.

## Harsh-main follow-ups today (2026-05-15)

- PM@128dbf03 — moved UI-only templates (`uac-registry-sync.yml` +
  `uic-openapi-sync.yml`) from `scripts/workflow-templates/` to a new
  `scripts/workflow-templates-ui/` dir. Reason: rollout was propagating them
  to every Python repo as dead code (UAC dispatches to UI repo only).
- PM@68ba6e7c — added UI-tier loop to `rollout-workflow-templates.sh`
  targeting `unified-trading-system-ui` only for the UI templates.
- Python cleanup pass — removed 44 untracked spurious UI-only yamls from main
  workspace clones. UI repo's committed copies (live) preserved.
- **Did NOT yet remove the 20 untracked `workspace-qg.yml` files** —
  awaiting redesign decision (this doc).
- The alerting-service commit `05dec98` is now live: alerting-service has a
  `workspace-qg.yml` running on PRs from LDR → main. It's working but
  redundant with the existing `quality-gates.yml` (also on `[main]` trigger).
  No duplicate-CI yet because alerting-service is in the `[main]`-only
  cluster, and PR-from-LDR-to-main fires both workflows — confirmed: see
  alerting-service runs at 10:57 / 12:14 / 12:52 / 13:15 UTC today (each
  pair of runs is one PR triggering both).

## Why this needs opus-max + Ikenna review

The redesign is **not mechanical**. Decisions needed:

1. **Trigger surface**: should the unified workflow fire on `live-defi-rollout`
   pushes (matching the 9 current LDR-trigger repos), `main` PRs only
   (matching the 7 main-only repos), or both? May-23 cutover removes LDR
   entirely — what's the post-cutover trigger?
2. **Migration sequencing**: if the unified template adds `live-defi-rollout`,
   when we adopt it, do we ALSO remove existing `quality-gates.yml` to avoid
   duplicate CI runs? Or rename the existing one out of the way?
3. **`dep_repos` source of truth**: the new template pulls from
   `workspace-manifest.json` (✅ correct); the existing per-repo files have
   hand-crafted lists. alerting-service's existing list includes **3 phantom
   deps** that no longer exist as repos (`unified-cloud-interface`,
   `unified-config-interface`, `unified-internal-contracts`) + a duplicate
   `unified-trading-library`. That's a workspace-wide cleanup all by itself.
4. **`develop` branch outlier**: position-balance-monitor-service uses
   `develop` instead of `staging`. Stale? Migrate?
5. **Empty `branches:`**: ml-training-service + trading-agent-service show
   empty `branches:` in the audit — need a careful read of the file to
   determine if the trigger is broken or just on a different line.
6. **Ikenna-side equivalence**: does Ikenna's side have similar workflow
   drift? Should this unification touch his repos too? Cross-side coordination
   needed.
7. **Post-cutover canonical**: May-23 retires LDR. The template should
   declare what the post-cutover canonical trigger is (main + staging? main
   only?) so this isn't re-litigated in 8 days.

## Recommended next steps (for whoever picks this up)

1. **Pre-design**: re-read this issue doc + the 3 commits (21686e55, 542f0e26,
   128dbf03+68ba6e7c).
2. **Trigger design decision**: write the canonical trigger surface to
   `codex/08-workflows/ci-cd-flow.md` (slot 8 created this doc — extend it).
3. **Template fix**: update `workspace-qg.yml.tmpl` triggers to match the
   decision. Add `live-defi-rollout` to branches if keeping pre-cutover.
4. **Per-repo migration plan**: for each of 21 repos, identify (a) drop
   existing `quality-gates.yml` (b) rename to keep both (transition window)
   (c) merge configs. Document per-repo before touching.
5. **`dep_repos` cleanup**: cross-reference every existing per-repo
   `dep_repos` list against `workspace-manifest.json`. File a separate
   issue doc for phantom-dep cleanup if the count is high (alerting-service
   alone has 4 phantom/duplicate entries).
6. **Coordinated rollout**: when the design lands, run the rollout from
   main workspace (per the existing pattern), commit per-repo + push to LDR.
7. **Continuous verification**: add `Last verified` column to the master plan
   for CI workflow consistency (per CLAUDE.md "Master Plan Continuous
   Verification Column" hard rule).

## State of the artifacts as of 2026-05-15 ~23:00 UTC

- ✅ **Deleted by harsh-main** (this doc creation): `workspace-qg.yml.tmpl` from
  `scripts/workflow-templates/` + 20 untracked `workspace-qg.yml` artifacts
  from main workspace Python repo clones (excluded: alerting-service, which
  has a committed copy).
- 🟡 **Still live on origin/live-defi-rollout**: `alerting-service@05dec98`
  with `workspace-qg.yml` deployed. Redesigner decides: revert that commit OR
  keep alerting-service as the "first cutover repo" reference.
- 🟢 **Preserved**: UI-tier templates (`uac-registry-sync.yml` +
  `uic-openapi-sync.yml`) in `scripts/workflow-templates-ui/`, scoped via
  PM@68ba6e7c so they only target unified-trading-system-ui. Working
  correctly.
- 🟢 **Untouched**: `python-quality-gates.yml` reusable workflow in PM (this
  is the actual QG logic — every per-repo workflow file calls it). Slot 8
  did not modify this file.

## Cross-side handoff

Cross-side ping filed in `plans/active/_agent_pings.md` at 2026-05-15 23:00 UTC
asking Ikenna to (a) take ownership of the redesign or (b) confirm Harsh-side
should re-spawn this on an opus-max slot.

execution: owner: ikenna-main (pending ack) OR harsh-main on opus-max slot
cadence: one-shot redesign + multi-repo rollout
verifier: per-repo `gh run list` shows expected trigger pattern on appropriate branches
last_executed: NEVER (trigger-unification design)

---

## Resolution status (live updates)

### 2026-05-15 23:30 UTC — dep_repos phantom-cleanup landed (separate from trigger redesign)

Audit of `dep_repos:` strings across the 21 Python repos' `quality-gates.yml`
found **10 repos with phantom and/or duplicate deps**:

| Repo                                | Phantom deps removed                                                                                                              | Duplicates removed   | New SHA on origin/LDR   |
| ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | -------------------- | ----------------------- |
| alerting-service                    | unified-cloud-interface, unified-config-interface, unified-internal-contracts                                                     | unified-trading-library | alerting-service@40ba05d |
| batch-live-reconciliation-service   | unified-cloud-interface, unified-config-interface, unified-internal-contracts                                                     | unified-trading-library | batch-live-reconciliation-service@3115f52 |
| client-reporting-api                | unified-cloud-interface, unified-config-interface, unified-internal-contracts                                                     | unified-trading-library | client-reporting-api@d42ecaf |
| ml-inference-service                | unified-cloud-interface, unified-config-interface, unified-domain-client, unified-internal-contracts, unified-ml-interface         | unified-trading-library | ml-inference-service@824f0db |
| ml-training-service                 | unified-cloud-interface, unified-config-interface, unified-domain-client, unified-internal-contracts, unified-ml-interface         | unified-trading-library | ml-training-service@845b0ce |
| pnl-attribution-service             | unified-cloud-interface, unified-config-interface, unified-domain-client, unified-internal-contracts, unified-ml-interface         | unified-trading-library | pnl-attribution-service@6db1b52 |
| position-balance-monitor-service    | unified-cloud-interface, unified-config-interface, unified-domain-client, unified-internal-contracts, unified-ml-interface, unified-position-interface | unified-trading-library | position-balance-monitor-service@d987836 |
| risk-and-exposure-service           | unified-cloud-interface, unified-config-interface, unified-internal-contracts                                                     | unified-trading-library | risk-and-exposure-service@0849397 |
| system-integration-tests            | unified-cloud-interface, unified-config-interface, unified-domain-client, unified-internal-contracts, unified-ml-interface         | unified-trading-library | system-integration-tests@f22f7f6 |
| trading-agent-service               | unified-cloud-interface, unified-config-interface, unified-internal-contracts                                                     | unified-trading-library | trading-agent-service@3cda16d |

**Method**: replace per-repo `dep_repos:` string with the manifest-derived
authoritative list (sorted alphabetical) from
`unified-trading-pm/workspace-manifest.json -> repositories.<repo>.dependencies[name]`.

**Effect**: future CI runs no longer attempt to `git ls-remote` + clone
phantom repos (which would 404). Each repo's QG is now a hair faster and
deterministic.

**What this didn't fix**:
- The trigger-list inconsistency across the 5 patterns (still 9 LDR-trigger,
  9 main-only, 2 main+staging, 1 main+develop) — that's the redesign
  Ikenna/opus-max needs to do.
- alerting-service still has the committed `workspace-qg.yml` from
  `05dec98` running in parallel with `quality-gates.yml`. Redesigner
  decides revert or keep.

### Open items for the redesign (unchanged)

The 7 design questions in § "Why this needs opus-max + Ikenna review" still
apply to the trigger-list unification. The dep_repos phantom-cleanup
landed today only addresses one of those (the `dep_repos` source-of-truth
question — answer: `workspace-manifest.json`).

---

## OWNED BY IKENNA-MAIN (opus-max-tier) 2026-05-16 — DESIGN + REDESIGN COMPLETE

**Status update**: design landed at `unified-trading-pm@<this-commit>`. Template rewritten + 7 open
questions answered + per-repo migration plan documented. Canary against alerting-service in next
cycle.

### Answers to 7 open design questions

**Q1 — Trigger surface**: `push to [main, staging, live-defi-rollout]` + `pull_request to [main, staging]`. Strict
superset of all 5 observed patterns. The 9 `[main]`-only repos will see additional QG runs on LDR pushes after
migration — intended unification (faster failure detection on LDR work). Post-cutover (after May-23), drop LDR from
triggers; keep `[main, staging]`.

**Q2 — Migration sequencing**: DROP existing per-repo `quality-gates.yml` in same commit that adds `workspace-qg.yml`.
No transition window — keeps prevent duplicate CI runs (compute waste + flaky test surface). Canary one repo first
(alerting-service since it already has the PoC committed); validate; then batch-roll-out remaining 20.

**Q3 — `dep_repos` source of truth**: `workspace-manifest.json` is canonical. Template renders `{{DEP_REPOS}}` from
manifest via `rollout-workflow-templates.sh`. Phantom-dep cleanup (e.g. alerting-service's stale
`unified-cloud-interface` / `unified-config-interface` / `unified-internal-contracts` + duplicate
`unified-trading-library`) is AUTOMATIC via rollout — no separate cleanup pass needed.

**Q4 — `develop` outlier**: position-balance-monitor-service migrates to `[main, staging, live-defi-rollout]` in the
unified rollout. `develop` is stale (no recent commits on remote `develop` branch per
`git ls-remote origin develop` — sole occurrence). No deletion needed; just stops being a trigger.

**Q5 — Empty `branches:`**: CORRECTION already noted at issue line 50-54 — ml-training-service +
trading-agent-service were false positives (multi-line YAML); both are `[main]`-only. No action.

**Q6 — Ikenna-side equivalence**: There is no per-side workflow split. All 21 Python repos use the same
`quality-gates.yml` shape regardless of which operator's slot touches them. This unification covers BOTH sides.

**Q7 — Post-cutover canonical**: `[main, staging]` push + PR-to-`[main, staging]`. Documented inline in template
header comment. Post-cutover migration is one template edit + one rollout pass; takes ~5 min total.

### Per-repo migration plan

**Phase A — Canary** (1 repo, ~30 min including verification):

1. `bash scripts/workflow-templates/rollout-workflow-templates.sh --repo alerting-service --template workspace-qg.yml.tmpl`
2. In alerting-service: `git rm .github/workflows/quality-gates.yml` (drop old) — same commit as the new
   `workspace-qg.yml` add
3. Commit + push to alerting-service `live-defi-rollout`
4. Watch the auto-FF mirror push to LDR via the tab-mirror-to-ldr GH Action; verify the workspace-qg run fires;
   verify no duplicate `quality-gates` run; verify run conclusion=success
5. If canary green → proceed to Phase B

**Phase B — Batch rollout** (20 repos, ~10 min including verification):

Repos to migrate (sorted by current trigger pattern for review):

- 8 already on `[main, staging, live-defi-rollout]`: deployment-api, deployment-service, execution-service,
  features-service, instruments-service, market-tick-data-service, market-data-processing-service, strategy-service,
  unified-trading-library — minimal trigger-behaviour change.
- 6 currently `[main]`-only: batch-live-reconciliation-service, ml-inference-service, ml-training-service,
  pnl-attribution-service, risk-and-exposure-service, system-integration-tests, client-reporting-api,
  trading-agent-service — will start seeing LDR push QG runs (intended).
- 2 currently `[main, staging]`: unified-api-contracts, ibkr-gateway-infra — will add LDR push triggers.
- 1 currently `[main, develop]`: position-balance-monitor-service — migrates to canonical.

**Rollout command** (after canary green):
```bash
bash scripts/workflow-templates/rollout-workflow-templates.sh --template workspace-qg.yml.tmpl
# Then per-repo: drop old quality-gates.yml + commit + push
```

Operator can pause/resume the batch by repo-name if any repo's first run fails post-migration.

### Codex SSOT update

Will append a "Workflow trigger surface (unified workspace-qg)" section to
`codex/08-workflows/ci-cd-flow.md` after canary verification with:
- The trigger surface decision + rationale
- Post-cutover migration plan + cutover date
- How to roll forward future workflow changes via template + rollout

### alerting-service@05dec98 disposition

KEEP — it's the canary. The current commit has the wrong trigger pattern (no LDR); Phase A above
re-rolls-out the corrected template over it. The 4 duplicate-CI runs noted in issue body
(10:57/12:14/12:52/13:15 UTC) are tolerable until Phase A lands (~30 min from now per orchestrator cadence).

### Continuous verification

After rollout, add row to `master_to_live_defi_2026_05_23.md` § "Continuous verification matrix":
- **Item**: CI workflow consistency across 21 Python repos
- **Continuous verification**: `gh workflow list --repo IggyIkenna/<repo> --json name` returns exactly
  `workspace-qg` + standard auxiliary workflows; per-repo `quality-gates.yml` no longer exists.
- **Cadence**: weekly drift-check (audit one repo per day across the week)
- **Owner**: slot 1 main (or post-cutover: continuous-verification cron)
- **Last verified**: 2026-05-16 (post-canary)
