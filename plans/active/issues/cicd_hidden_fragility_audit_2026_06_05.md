---
title: CI/CD pipeline hidden-fragility audit — silent-failure & instability risks
created: 2026-06-05
author: harshkantariya
source:
  - 6-agent parallel CI/CD subsystem audit (slot-1, 2026-06-05)
  - independent verification against live workflows + GitHub Actions run history
locked_by: live-defi-rollout
related:
  - plans/active/cicd_contract_hardening_2026_06_01.md
---

## What I found

A fragility audit of the whole CI/CD pipeline (≈52 workflows + `quickmerge.sh` + the promotion/SIT/ci_status/tab-mirror
machinery), focused on **hard-to-detect** instability — things that report GitHub Actions **green** while silently
breaking, stalling, or mis-promoting. The audit was driven by the rapid 2026-06-01 → 06-05 migration ("old way vs new
way"), so most findings are **incomplete-rollout / regression** class.

**Verification legend:**

- `[VERIFIED]` — independently confirmed this session (file:line read + quoted, or live probe / `gh` run history).
- `[PENDING]` — strong agent file-evidence; final independent confirmation in progress.
- `[REFUTED]` — checked and found NOT to be a real issue (kept for the record).

### The meta-pattern (the real risk)

Not one bug — a **class**, all created by the fast migration:

1. **Incomplete rollouts** — the SSOT template/script was fixed but the _deployed copy_ or the _default value_ wasn't
   (wrong host, dead workflow name, 22 un-rolled templates). Each looks green; the triggering event just never arrives.
2. **Concurrency-group fragmentation** — several workflows write the shared `workspace-manifest.json` _outside_ the
   `manifest-update` lock group → silent lost-updates.
3. **Self-silencing watchdogs** — the very mechanisms meant to catch silent failure (dead-man switch, SIT-starvation
   detector, template-drift guard) have blind spots or one-shot flags that disable them.

---

## Findings

### CRITICAL

#### C1 — Escalations POST to the wrong host (SPA, not the API); bridge is dead but green `[VERIFIED]`

- **Evidence:** `.github/workflows/escalate-to-orchestrator.yml:151`
  `ORCH_URL: ${{ vars.ORCHESTRATOR_URL || 'https://agent-orchestrator.odum-research.com' }}`. `vars.ORCHESTRATOR_URL` is
  unset → default used. Every other orchestrator caller uses the `api.` host: `main-backmerge-to-ldr.yml:190`,
  `tab-mirror-to-ldr.yml:193/382` (`https://api.agent-orchestrator.odum-research.com`). A POST to the bare host hits the
  Vite SPA → HTTP 200 + `<!doctype html>`, no `escalation_id`; the job still concludes `success`.
- **Detectability:** extreme — green run, only a Slack WARNING; escalations never reach a worker.
- **Failure mode:** conflict/failure walls are never handed off → they persist → re-detected every cron tick → feeds the
  storm (C3).
- **Old-vs-new:** regression. The internal secret was wired 2026-06-03 ("bridge verified green") but that verified the
  secret exists, not the host; the wrong URL shipped.
- **Fix:** default URL → `https://api.agent-orchestrator.odum-research.com` (or set the `ORCHESTRATOR_URL` Actions var).

#### C2 — PM's semver-agent triggers on a workflow name that doesn't exist → PM never version-bumps `[VERIFIED]`

- **Evidence:** `.github/workflows/semver-agent.yml:38` `workflows: ["Quality Gates"]`, but the actual workflow is
  `quality-gates-v2.yml:13` `name: quality-gates-v2`. `workflow_run` matches by name → it never fires. Contrast
  confirmed: `instruments-service` + `market-tick-data-service` semver-agents correctly use
  `workflows: ["quality-gates-v2"]`. **PM alone** uses the dead name.
- **Detectability:** maximal — an event that never arrives (no error, no failed run).
- **Failure mode:** PM never bumps → never promotes staging→main → and PM is the manifest/template **SSOT host**, so its
  frozen version desyncs the `staging_versions` baselines other repos' semver-agents read.
- **Old-vs-new:** regression — the canonical `.tmpl` was fixed + rolled to service repos, but PM's own copy (PM is
  special-cased out of the rollout) was missed; 2 stale legacy templates (`scripts/templates/semver-agent.yml`,
  `scripts/propagation/templates/semver-agent.yml`) also still carry the dead name.
- **Fix:** `semver-agent.yml:38` → `workflows: ["quality-gates-v2"]`; delete the 2 stale templates.

#### C3 — Escalation re-dispatch storm + bypassed idempotency `[VERIFIED]`

- **Evidence:** `scripts/repo-management/ci_failure_watcher.py:143` gates on
  `_ESCALATION_LABEL = "escalation-dispatched"`, but `.github/workflows/conflict-resolution-agent.yml` has **no** label
  check (grep: 0 hits) — a second escalation source that bypasses idempotency. Live `gh run list`
  (escalate-to-orchestrator): bursts of **7 runs within 30s** (11:00Z), **3 within 5s** (11:28Z), all `success`.
- **Detectability:** silent — all green; only run-density reveals it.
- **Failure mode:** combined with C1 (conflicts never resolve → re-qualify every tick) = runaway loop now; once C1 is
  fixed it becomes a **cost storm** (each conflict dispatch spawns an Opus Max-plan worker; duplicate workers on the
  same PR).
- **Old-vs-new:** regression from the multi-source escalation design — only the watcher path got the label gate.
- **Fix:** label-gate `conflict-resolution-agent.yml` (+ `deterministic-promotion-conflict-resolve.yml`), or route all
  escalation through the single gated path.

### HIGH

#### H1 — ci_status auto-advances FEATURE_GREEN→STAGING_GREEN on a stale green (no SHA check) `[VERIFIED]`

- **Evidence:** `.github/workflows/ci-status-reconciler.yml:96-110` advances iff `CUR==FEATURE_GREEN` AND latest staging
  v2 `== success` AND `ahead_by(staging…LDR)==0`. It **never compares the green run's `headSha` to staging HEAD**. A
  GITHUB_TOKEN merge that didn't re-trigger v2 leaves staging at an untested SHA while the last green is an older SHA →
  repo marked STAGING_GREEN on untested code, which `staging-to-main` dep-gate then trusts.
- **Detectability:** silent; the comment even claims it's "truthful + non-over-promoting."
- **Old-vs-new:** new (2026-06-04, `abe2ec3ae`).
- **Fix:** require `headSha == staging HEAD`; else re-trigger v2 instead of advancing.

#### H2 — Manifest writers outside the `manifest-update` concurrency group → lost updates `[VERIFIED]`

- **Evidence:** `cascade-qg-ordering.yml:33` (group `cascade-qg-ordering`), `sit-debounce-trigger.yml` (group
  `sit-debounce-check`), `sit-starvation-detector.yml` (group `sit-starvation-check`) all mutate
  `workspace-manifest.json` but are NOT in `concurrency: group: manifest-update` (which
  `ci-status-update`/`sit-gate`/`sit-unlock`/ `staging-to-main` share) and lack the 5× rebase-retry the others have.
- **Detectability:** silent — last-writer-wins / non-FF push rejected with `check=False`.
- **Failure mode:** a real FEATURE_GREEN→STAGING_GREEN transition or a STAGING_PENDING invalidation is lost;
  `staging_status` (incl. SIT lock / retry counters) corrupts.
- **Old-vs-new:** regression — the `manifest-update` unification + rebase-retry were added to close the lock race for 3
  writers but these 3 were left out.
- **Fix:** move all three into `concurrency: group: manifest-update` + add the rebase-retry loop.

#### H3 — SIT dangling-lock alarm silences itself permanently (`locked_alert_sent` never reset) `[VERIFIED]`

- **Evidence:** `.github/workflows/sit-starvation-detector.yml` sets `m['staging_status']['locked_alert_sent'] = True`
  (line 64) after a stale-lock alert, and short-circuits on `if locked_alert_sent: exit` (line 48). Grep confirms **no
  workflow ever resets it to False** (only references are in this one file: read at 42, check at 48, set at 64). When
  the lock later clears (`if not locked: exit` at 44-46), the flag is left True.
- **Detectability:** extreme — it's the failure of the detector built to catch silent stalls.
- **Failure mode:** after the _first_ alert ever, every future dangling SIT lock is suppressed → staging can stay locked
  fleet-wide invisibly → all promotions stall until a human notices.
- **Old-vs-new:** regression — detector added 2026-06-03; the reset half was never wired into the lock-set/lock-clear
  path.
- **Fix:** reset `locked_alert_sent = False` when `sit-gate` sets `locked = True` (or when unlocked).

#### H4 — 22 repos' `tab-mirror-to-ldr.yml` diverge from SSOT template (drift unrolled) `[VERIFIED]`

- **Evidence:** `python3 scripts/quality_gates/detect_template_drift.py --workflows --json` → **24 current drift,
  baseline 3, 22 new** (every repo's `tab-mirror-to-ldr.yml`). The 2026-06-04/05 edits (active-host filter +
  alert-routing + 15-min settle window) were made in the template but never rolled out via
  `rollout-workflow-templates.sh`.
- **Detectability:** silent — the local QG would block (`new_drift` → exit 1) but it degrades to a no-op in CI, and LDR
  carries no required check; only a full-workspace local PM run catches it (which a single-repo VM worker never runs).
- **Failure mode:** the fleet's divergence/name-collision monitor runs **stale alert-routing logic** across all 22 repos
  — diverged-tab alerts fire/suppress on the wrong allowlist.
- **Old-vs-new:** regression 2026-06-04/05.
- **Fix:** `bash scripts/workflow-templates/rollout-workflow-templates.sh` then confirm
  `detect_template_drift.py --workflows` exits 0 (do NOT `--baseline-write`; see M5).

#### H5 — Green-sentinel skip re-stamps the QG SHA sentinel without running tests `[VERIFIED]`

- **Evidence:** `scripts/quality-gates-base/base-service.sh` — tests are skipped on a sentinel HIT (`:322`
  `if [ "$RUN_TESTS" = true ] && [ "$_QG_SENTINEL_HIT" != true ]`), typecheck too (`:497`). But the SHA-sentinel write
  (`:2605-2618`) is guarded only by
  `RUN_TESTS==true && RUN_LINT==true && QUICK_MODE==false && ACT_MODE==false && no SKIP_CODEX` — **not** by
  `_QG_SENTINEL_HIT`. The code's own comment (`:2614-2615`) states: _"This block also runs on a green-skip (sentinel-HIT
  keeps RUN_TESTS=true), so the SHA sentinel is refreshed on fast-green too."_ So a content-hash HIT re-stamps
  `.qg_last_passed_sha = HEAD` with tests skipped.
- **Failure mode:** during the active dep-version migration a consumer whose deps changed underneath (own tree
  byte-identical) skips tests yet refreshes the sentinel → `quickmerge --agent` sails through on a repo whose tests
  would now fail.
- **Fix:** gate the SHA-sentinel write additionally on `[ "$_QG_SENTINEL_HIT" != true ]`.

#### H6 — FF-pull cron self-update = single-commit fleet kill-switch `[VERIFIED]`

- **Evidence:** `scripts/dev/install-slot-cron-ff-pull.sh:76-77` — both `SELF_PULL_FF` and `SELF_PULL_VERIFY` do
  `git checkout -q origin/live-defi-rollout -- <script> ... || true` as the first crontab clause, with **no `bash -n`
  syntax gate** (grep: zero). The header comment (`:72-74`) confirms this is intentional ("local edits to them are
  overwritten each tick by design"). The verify cron self-updates `verify-slot-host-symmetry.sh` the same unguarded way.
- **Failure mode:** one bad commit to `slot-cron-ff-pull.sh` propagates to every laptop + VM within ≤5 min → FF-pull
  stops fleet-wide → every slot silently stops tracking LDR → stale code everywhere; and because the verify cron
  self-updates identically, a commit breaking both disables its own watchdog.
- **Fix:** syntax-gate the self-pull (`checkout → tmp; bash -n tmp && mv tmp <path>`), adopt only a parse-clean copy.

### MEDIUM

#### M1 — quickmerge sentinel pins HEAD, but `--files` commits a _later_ tree `[VERIFIED]`

- **Evidence:** `scripts/quickmerge.sh` — the agent fast-path sentinel check at `:1019-1029` verifies
  `_SENTINEL_SHA == _CURRENT_SHA` (`git rev-parse HEAD`). The `--files` flow then runs prettier `--write` (`:1169`) and
  stages+commits (`:1184-1218`, `git add "$f"` … `git commit`) **after** that check — so the committed/pushed tree can
  differ from the HEAD the sentinel certified.
- **Reachability caveat:** benign if agents always commit before quickmerge; live if they rely on quickmerge's own
  `--files` staging or its prettier reflow changes a file. Path exists and is reachable.
- **Fix:** in `--agent` mode require a clean working tree at sentinel-check time, or re-verify sentinel == post-commit
  SHA before push.

#### M2 — Branch-protection drift traps (stale scripts + Terraform + prefix-only verifier) `[VERIFIED]`

- **Evidence (3 parts, all confirmed):**
  - `scripts/repo-management/set-branch-protection.sh:65` `--field "required_status_checks[contexts][]=agent-audit"`;
    `ops/branch-protection-template.json:7` `"contexts": ["quality-gates"]` — both retired contexts that no current run
    emits (the live context is `Quality Gates (<repo>) / quality-gates-v2`). Re-running either dead-locks non-admin
    merges (masked by `enforce_admins=false`).
  - `terraform/github-branch-protection/main.tf:40-57` hardcodes 9 repos to the retired `quality-gates` suffix (e.g.
    `:41-43` batch-live-reconciliation-service / client-reporting-api / deployment-api) — a `terraform apply` rolls them
    back to a context no run emits.
  - `scripts/repo-management/verify_branch_protection_check_names.py:73` only
    `m[0].startswith(f"Quality Gates ({repo})")` → blind to v1↔v2 _suffix_ drift; iterates a static 17-repo list
    (misses agent-orchestrator + new repos). So the drift detector reports GREEN on the most likely drift.
- **Fix:** sync/delete the stale IaC; verifier should assert the full derived context + drive the repo list from
  `workspace-manifest.json`.

#### M3 — Dep-order gates fail-open on blank/missing `ci_status` `[VERIFIED]`

- **Evidence:** `scripts/cicd/tier_c_promotion_gate.py:108-118` —
  `if not name or name not in repos: continue # untracked dep → safe-default pass` and
  `if not dep_status: continue # unset → safe-default pass`. Same pattern in `staging-to-main.yml`.
- **Failure mode:** a dep whose ci_status was never written (new repo, reset, or dropped by a reconcile path) is treated
  as on-main → dependent promotes out of order. **Amplified by C2/H2** which are exactly what produce blank ci_status.
- **Fix:** for a dep that exists in the manifest, treat unset ci_status as BLOCK (fail-closed); keep fail-open only for
  deps genuinely absent from the manifest.

#### M4 — Permanently-dirty worktree falls arbitrarily far behind LDR with no alert `[VERIFIED]`

- **Evidence:** `scripts/dev/slot-cron-ff-pull.sh:208` `log "[skip:dirty] ${repo_name} ... — uncommitted changes"` then
  skips (returns 0, log-only). `verify-slot-host-symmetry.sh` check #10 (`:244-259`) asserts only that `@{upstream}`
  _name_ == `origin/live-defi-rollout` — there is **no** behind-**distance** (commit-count) check anywhere; `behind`
  appears only in comments.
- **Failure mode:** a dirty slot rots unboundedly behind LDR (cf. the noted incident of a clone 1164 commits behind);
  the next agent on it builds/tests against stale code, and its quickmerge re-tangles against a far-diverged LDR.
- **Fix:** add a "behind LDR by > N commits AND dirty > T minutes" host-level alert to the verifier (`--alert` path
  already exists).

#### M5 — `--baseline-write` can silently loosen the drift ratchet `[VERIFIED]`

- **Evidence:** `detect_template_drift.py` `--baseline-write` (arg at :556-559) calls
  `_report_workflow_drift(..., write_baseline=True)` which rewrites the baseline to **current state** (help: "Rewrite
  the workflow-drift baseline to current state"). `quality-gates.sh` advertises it as the "if intentional" escape hatch.
  Nothing enforces monotonic shrinkage, so it can ADD new drift (bless breakage) in one line — exactly the H4 hole.
- **Fix:** make `--baseline-write` only REMOVE now-clean entries (refuse to add), or require a diff + justification.

#### M6 — `staging-to-main` idempotency guard is dead code `[VERIFIED]`

- **Evidence:** `.github/workflows/staging-to-main.yml:87` `echo "idempotent_skip=$?"` — the heredoc Python
  `sys.exit(0)`s on already-promoted (line ~83) and falls through (implicit exit 0) on proceed, so `$?` is **always 0**;
  `idempotent_skip` is referenced by **no later `if:`** (grep: written once at :87, read nowhere).
- **Failure mode:** the "skip if staging already promoted" protection does not exist → a re-dispatched run re-merges
  staging→main, re-appends `main_commits.history`, re-clears the lock (can stomp a concurrent sit-gate lock).
- **Fix:** `sys.exit(0)` only on already-promoted, distinct exit/echo on proceed, gate the promote steps on
  `idempotent_skip`.

---

## Why it matters

The pipeline is the path live trading code takes to production. Each finding individually reports green; together they
mean **failures and stalls do not surface** — a dead escalation bridge (C1) looks like "no failures," a frozen PM bumper
(C2) looks like "nothing to promote," a self-silencing SIT alarm (H3) looks like "no stale locks," and stale-but-green
ci_status (H1) + fail-open dep gates (M3) can promote untested / out-of-order code to main. The active churn keeps
widening these windows.

## Recommended decision

- **Quick wins (one-line, stop live bleeding):** C1 (host), C2 (semver name), C3 (label gate) — these are actively
  burning Actions minutes + Opus workers now.
- **Small design fixes:** H1 (SHA check), H2 (lock group), H3 (reset flag), M3 (fail-closed), M6 (real idempotency).
- **Operational:** H4 (run the rollout), H5/M5 (sentinel/ratchet hardening), H6/M4 (cron syntax-gate + behind-distance
  alert).
- **IaC hygiene:** M2 (sync/delete stale branch-protection scripts + Terraform).

Route to `cicd_contract_hardening_2026_06_01.md` (Ikenna owns the CI/CD area; this is active work). Items are
independent and parallelizable.

## Reconciliation vs existing issue docs + plans

Checked all of `plans/active/issues/` + the CI/CD master plan `cicd_contract_hardening_2026_06_01.md` (2532 lines).
**None of the 15 findings is a duplicate.** Several intersect existing items whose status is now **stale** — those are
the highest-value reconciliation outputs (a green-looking plan hiding a still-broken mechanism).

### Existing items my findings prove STALE (plan/CLAUDE.md need correction)

- **C2** ↔ plan **line 1362** `[x] ✅ DONE 2026-06-02` ("semver-agent watches DEAD name → fixed on 8 repos"). The
  item's own list **excludes `unified-trading-pm`**, and the live file `semver-agent.yml:38` is still
  `["Quality Gates"]`. **The ✅ is incomplete — PM was missed.** `CLAUDE.md` § Version/Workflow ("Promotion automation …
  REPAIRED 2026-06-02 — semver-agent now watches quality-gates-v2 … pipeline flows again") inherits the same overclaim.
  → reopen + add PM.
- **C1** ↔ plan **line 248** `[ ]` says "PM `escalate-to-orchestrator.yml` **does NOT exist**" (2026-06-02 re-audit),
  consolidated into "Observability+Reconciliation B". The workflow **exists now** and carries the wrong-host bug. →
  update: workflow present; root cause is the SPA-host default (`:151`), not absence.
- **H3** ↔ plan **line 1625** `[x] ✅ DONE` fixed the starvation detector's `locked_at`→`locked_since` field bug (made
  the age-check fire). My finding is a **separate residual**: `locked_alert_sent` is set once and never reset → after
  the first page it is silent forever. **The plan believes the dangling-lock watchdog is fixed; it is still partially
  dead.** → add residual sub-item.

### Existing mechanisms my findings EXTEND (gaps, not dups)

- **H1** — the FEATURE→STAGING auto-advance is Guard 3 (plan line 654 ✅); the missing **headSha** check is untracked.
  **This also explains the open "lead" in `ci_false_positive_alerts_infra_noise_2026_06_05.md` (UAC reads
  `STAGING_GREEN` despite a live red promote PR)** — that doc left it as a lead; H1 is the mechanism.
- **M2** — plan **line 187** `[ ]` ("prevent default-branch drift; extend the verifier") covers the
  static-list/default-branch part; the **suffix-blind `startswith` verifier + stale classic scripts
  (`set-branch-protection.sh`, `branch-protection-template.json`) + Terraform map** are untracked.
- **M3** — dependency-ordering is the `fleet_promotion_pipeline_repair_2026_06_05.md` workstream + STAGE 1.8; the
  **fail-open-on-blank-`ci_status`** default is the untracked nuance (and C2/H2 are exactly what produce blank
  `ci_status` → they widen this window).
- **H4** — the rollout SSOT + parity guard exist and were used for v1→v2 (plan line 159); the **current 22-repo
  `tab-mirror` drift is a fresh unrolled batch** (06-04/05 edits).
- **M6** — plan line 1084 describes idempotency as an intended staging-to-main step; the **implementation is dead code**
  (the bug, not the intent).

### Net-new (no existing item)

C3 (storm + label-bypass), H2 (concurrency-group fragmentation), H5 (green-sentinel skip), H6 (cron self-update), M1
(sentinel/`--files`), M4 (dirty-behind no alert), M5 (`--baseline-write` ratchet).

### Sibling issue docs filed today — adjacent, not dups

- `fleet_promotion_pipeline_repair_2026_06_05.md` — staging-behind-main backlog + 7 repos' genuine QG debt +
  dep-ordering (operational; corroborates the M3 theme).
- `ci_false_positive_alerts_infra_noise_2026_06_05.md` — `#ci-failures` over-paging on infra noise; its UAC `ci_status`
  lead is explained by my **H1**.

## Verification log

| ID  | Status   | Confirmed by                                                                         |
| --- | -------- | ------------------------------------------------------------------------------------ |
| C1  | VERIFIED | file:line + host contrast + live SPA-200 behavior                                    |
| C2  | VERIFIED | semver name vs workflow name + 2 service-repo contrast                               |
| C3  | VERIFIED | label-gate gap + `gh run list` burst density                                         |
| H1  | VERIFIED | `ci-status-reconciler.yml:96-110` no headSha compare                                 |
| H2  | VERIFIED | concurrency-group divergence across the 3 files                                      |
| H3  | VERIFIED | grep: `locked_alert_sent` never reset                                                |
| H4  | VERIFIED | `detect_template_drift.py` live: 24 drift / 22 new                                   |
| H5  | VERIFIED | `base-service.sh:322/497` skip vs `:2605-2618` write (comment self-confirms)         |
| H6  | VERIFIED | `install-slot-cron-ff-pull.sh:76-77` self-pull, no `bash -n`                         |
| M1  | VERIFIED | `quickmerge.sh:1019-1029` check before `:1169/1184-1218` commit                      |
| M2  | VERIFIED | `set-branch-protection.sh:65` + `template.json:7` + `main.tf:40-57` + verifier `:73` |
| M3  | VERIFIED | `tier_c_promotion_gate.py:108-118` safe-default pass                                 |
| M4  | VERIFIED | `slot-cron-ff-pull.sh:208` skip-only + verifier `:244-259` name-only                 |
| M5  | VERIFIED | `detect_template_drift.py --baseline-write` semantics                                |
| M6  | VERIFIED | `staging-to-main.yml:87` `$?` always 0, never read                                   |
