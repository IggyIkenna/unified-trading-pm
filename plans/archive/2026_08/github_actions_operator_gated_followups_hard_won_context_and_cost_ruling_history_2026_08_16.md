---
doc_type: plan
title:
  GitHub Actions operator-gated followups — Progress Log history II (Hard-won context 2026-07-17/22 + the 2026-07-23
  self-hosted cost ruling)
summary: >-
  Second line-cap remediation extraction from plans/active/github_actions_operator_gated_followups_2026_07_17.md's
  "Hard-won context the next session should inherit rather than rediscover" and "Cost ruling 2026-07-23" sections,
  moved verbatim (same pattern as the first extraction,
  plans/archive/2026_08/github_actions_operator_gated_followups_progress_log_history_2026_08_03.md) so the live plan
  stays under the 1000-line hard cap after regrowing to 1006-1007L. Both sections are closed historical record — the
  2026-07-17/22 post-migration system-check narrative + operational lessons, and the semver-agent cost-revert
  decision — no open todo in the live plan depends on this narrative. Applied under the 2026-08-15 plan-reconcile
  Trust Mode ruling (plan-splitting is no longer parked when a proven in-corpus pattern already exists for the exact
  same doc) — see plans/active/issues/operator_ruling_record_ci_line_cap_splits_2026_08_16.md for the full reasoning.
status: complete
nature: record
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, github-actions, cost, self-hosted-runner, history, line-cap-remediation]
related:
  [
    /plans/active/github_actions_operator_gated_followups_2026_07_17.md,
    /plans/archive/2026_08/github_actions_operator_gated_followups_progress_log_history_2026_08_03.md,
    /plans/archive/2026_08/operator_ruling_record_ci_line_cap_splits_2026_08_16.md,
  ]
created: 2026-08-16
last_updated: 2026-08-16
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: script
drift_direction: none
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  - "plan_reconciler ci-tranche run agt-4f7ad9, 2026-08-16 — line-cap split under Trust Mode"
---

# GitHub Actions operator-gated followups — Progress Log history II

Extracted verbatim from `plans/active/github_actions_operator_gated_followups_2026_07_17.md`'s "Hard-won context the
next session should inherit rather than rediscover" and "Cost ruling 2026-07-23" sections on 2026-08-16, to bring the
live plan back under the workspace's 1000-line hard cap (`scripts/plan-hygiene/check_line_caps.sh`). No content
changed — only relocated. Read the live plan's "Deferred work after 2026-07-17" / "Deferred work after 2026-07-23"
tables for the still-open decision ledger this history supports.

---

### Hard-won context the next session should inherit rather than rediscover

- **Evidence shape**: a run-level `runner_name` is MEANINGLESS for a cross-boundary workflow — a glue job + a hosted
  KEEP-D/MOVE-C job in one run is BY DESIGN. **Always read per-JOB.** (I truncated that column once and was ~1 minute
  from reporting "5 workflows silently failed to move".)
- **Billing**: `/timing.billable.total_ms` **UNDER-REPORTS — it returns 0 for jobs that plainly ran.** GitHub bills a
  **1-minute minimum PER JOB**, so COUNT JOBS, never ms. `billable: {}` (no UBUNTU key at all) is the real zero.
- **Never `2>/dev/null` a measurement.** `gh api` has no `--arg` flag; swallowing that error rendered a broken query as
  a clean "0 runs overnight" — the literal `curl -sf || echo ""` bug this plan documented, committed by me a day later.
  Also: `gh api --paginate --jq '[...]'` emits **one array PER PAGE**, so `jq length` counts only the first.
- **Cron delivery measured ~80-90%**, NOT the ~37% in CLAUDE.md's throttle note (hourly crons landed 9/10; `*/30` landed
  16/20). Re-check that figure before tuning any cooldown to it.
- **The security invariant is the TRIGGER AUDIT, not the private flag** — visibility is a settings toggle; "no
  self-hosted workflow carries a `pull_request` trigger" is a property of the workflows and survives it. Re-run it
  before adding such a trigger to any self-hosted workflow. **It is one command — a rule with no command is a rule that
  gets skipped, so here it is** (expect ZERO output; any line is a workflow that would run PR-authored code on our VM):
  ```bash
  grep -lE '^\s*runs-on: \[self-hosted' .github/workflows/*.yml \
    | xargs grep -lE '^\s*(pull_request|pull_request_target):'
  ```
- **A composite action gets NOTHING ambient from the repo — only what the caller explicitly hands it.** GitHub withholds
  **both `secrets` and `vars`** so an untrusted third-party action cannot read org/repo values without an explicit
  opt-in. The docs state the `secrets` half and are SILENT on `vars`; the silence is not permission.
  `actions/runner#2551`.
- **Composite-action manifest errors are NOT containable.** Validation happens at LOAD, before any step runs, so
  `continue-on-error` on every step buys you nothing — a bad `action.yml` fails the CALLER's real job. With 22 callers
  that is 22 simultaneous failures. **Edit the manifest → prove on ONE caller → only then fan out.**
- **MEASUREMENT TRAPS hit this session (same family as the `--arg`/`2>/dev/null` ones above):**
  - **A compound background command reports the LAST command's exit code, not your tool's.**
    `qg.sh > log; echo "EXIT=$?"; tail log` → the harness reported **exit 0** for `tail` while QG's real status was in
    the log. Always print and read an explicit `EXIT=` marker.
  - **The Bash tool's own ceiling is 10 min (600000ms max).** Wrapping a longer job in `timeout 900` does NOT help — the
    harness SIGKILLs it first and you get a bare **137** that looks like OOM. PM's full QG exceeds 10 min ⇒ it MUST run
    `run_in_background`. (Checked: 69 GB free, no competing QG — it was never resource pressure.)
  - **`grep -rl 'self-hosted, glue'` counts your own COMMENTS.** The flip comment contains both `glue-writer` and
    `runs-on: ubuntu-latest` as literal strings, so file counts came out 37/22 and did not reconcile against 56. Anchor
    to `^\s*runs-on:` or you are measuring your own prose.
  - **A hand-wavy doc summary is an INFERENCE.** When you ask for a verbatim quote and get prose ("X appears in multiple
    keys that…"), you did not get an answer. **Search the error string first** — it is faster and it is ground truth.
- **Reading Slack directly**: `scripts/dev/slack-read-channel.py [channel] [hours]` (operator-directed 2026-07-17; auth
  = Secret Manager `SLACK_ALERTS_READER_BOT_TOKEN`, resolved in-process, never on disk). Trap it encodes: carrier posts
  keep the real content in Block Kit `blocks` — the `text` field is only the ":x: CRITICAL — <workflow>" headline, so
  grepping `text` tells you nothing about WHAT failed.
- **Session working-state (2026-07-17, slot 1)**: STEP 2c/2b work was done in a git WORKTREE of the slot-1 clone at the
  session scratchpad (`git worktree list` in `.tabs/1/unified-trading-pm` shows it; local branch `tmp/step2c-rollout`,
  fully pushed). If the scratchpad is gone, clean the stale registration with `git worktree prune` +
  `git branch -D tmp/step2c-rollout` — everything it held is on `origin/live-defi-rollout`. The worktree pattern itself
  is the documented way to work while the slot clone carries someone's live WIP.
- **5-day post-migration system check (2026-07-22)** — operator asked "is everything working, did anything break due to
  our migration?". Findings, evidence-first via `gh run list`/`gh api .../jobs`/`.../logs` (not Slack — this session's
  gcloud ADC needed an interactive reauth this tool couldn't do, so live Slack alert-volume re-verification was skipped;
  GH Actions run data is authoritative and sufficient on its own):
  - **`ldr-docs-gate` (shipped 2026-07-17 as the frontmatter backstop) had NEVER completed a single run** — 39/40
    sampled runs over 5 days show `cancelled`, 0 ever reached a verdict. Root cause:
    `concurrency: cancel-in-progress: true` on a static group name, racing against LDR's real push cadence (a new
    doc/plan push lands every few minutes fleet-wide, faster than this sub-minute check finishes) — every run got
    pre-empted by the next push before it could report anything. The backstop has been silently inert this whole time.
    **FIXED live this session**: `cancel-in-progress: false` (queue instead of cancel — self-hosted + sub-minute jobs
    make queuing free) → `unified-trading-pm@efdeb6f41`.
  - **CORRECTION #2 (real root cause, found only after the operator pushed back on my "resource limitation" theory
    2026-07-22 — that theory was WRONG, and the pushback was right)**: after the concurrency fix, runs were STILL 100%
    cancelled/stuck-queued (total population re-checked via `gh api .../runs?per_page=1` → `total_count: 1200`, not the
    40 I'd sampled earlier via a capped `--limit`; 1198 cancelled, 0 succeeded, 0 failed, ever — cross-checked against
    1402 real commits touching `plans/`/`codex/` in the same window, so the trigger itself was firing correctly). I
    first blamed shared self-hosted runner-pool CPU contention. Measured locally: the check itself runs in **2.04s** for
    the full 1670-doc corpus — nowhere near slow enough to explain a 90+-minute queue wait, and other `glue`-pool
    workflows (`cloud-build-router`, `change-freeze-check`, etc.) were completing in seconds in the EXACT same window a
    `ldr-docs-gate` job sat queued with `runner_name:""` — ruling out pool saturation outright (a saturated pool would
    starve everything, not one specific workflow). The actual cause: `runs-on: [self-hosted, Linux, X64, glue]` requires
    4 labels, but `scripts/self-hosted-runners/glue-runner-run.sh:190` registers every JIT-ephemeral runner in this pool
    with only `["self-hosted","glue"]` — no `Linux`/`X64` ever advertised. Label matching is a strict subset test, so a
    job needing all 4 can **never** match any runner in the pool — not eventually, structurally never.
    `ldr-docs-gate.yml` was the ONLY one of 36 workflows using this pool that specified the 4-label form; the other 35
    all correctly use the 2-label form matching the actual registration. **FIXED**: `runs-on: [self-hosted, glue]` →
    `unified-trading-pm@078c85dc3`. This is the REAL fix; the earlier concurrency change was necessary (a run that DID
    match a runner would otherwise still get killed by the next push) but was not sufficient on its own, and my "fixed"
    claim in the entry above was premature.
  - **LIVE PROOF (2026-07-22, same session)**: the very next `plans/**` push (this commit) triggered run `29910893758` —
    but it stayed `pending` with no job created, because the DEAD run from 08:36 (`29904643698`, created under the
    pre-fix 4-label config, which could never match a runner) was still sitting unresolved in the concurrency group and
    — since it was never cancelled by any of the ~15 pushes since — was silently jamming the whole queue behind it.
    Manually cancelled it (`gh api -X POST .../runs/29904643698/cancel`); the queue immediately unblocked and
    `29910893758` ran and completed in **12 seconds** (10:11:57→10:12:09) on `glue-ip-172-31-5-118-5`, conclusion
    `success`, `notify-broken-docs` correctly `skipped` (green verdict). First real completion in this workflow's 5-day
    existence. Three bugs total, now all fixed: (1) `cancel-in-progress:true` killing in-flight runs (`efdeb6f41`), (2)
    the labels mismatch preventing any match at all (`078c85dc3`), (3) an unresolvable zombie run parked in the
    concurrency queue with nothing to clear it (manually cancelled, no code fix needed — a genuinely dead run just needs
    cancelling once; it can't recur since (2) means no future run can get stuck the same way).
  - **Operator's 4 follow-on improvements (2026-07-22, now unblocked — the gate is confirmed working)**: (1) switch
    trigger from per-push (~240/day measured) to an hourly cron — per-push was never the right model for a check whose
    failure mode (a broken doc sitting undetected a bit longer) is low-consequence; (2) scope
    `check_frontmatter_schema.py` to just the changed files (`git diff --name-only`) instead of the bare/full-corpus
    call — the script already supports `[file ...]` args, `ldr-docs-gate.yml` just never used them; (3) add an
    existence-only check for frontmatter-referenced doc paths (`related`/`supersedes`/`parent_epic`) — confirmed via
    reading `docspec.py` that NO such check exists today (`related`-type fields are untyped `"free_list"`, never
    resolved against the filesystem); (4) Slack alert + optional AO-escalator dispatch on red, same as today just on the
    new cadence. None of these implemented yet — correctly gated on proving the actual fix works first.
  - **CORRECTION (caught when the operator asked "what is this test and should we bump it to 2s?")**: I initially
    reported UTL's `test_manifest_completeness.py::TestF1PerfGuard` (a perf-guard on `compute_completeness_fraction()`,
    added alongside the 16.7x `80d2497e` filter-then-build/memoize optimization, asserting a 1.2M-row completeness
    lookup stays fast so a revert to the old O(n) full-scan gets caught) as a **still-open** regression needing an
    operator decision on its budget. That was wrong — I hadn't checked failure timestamps against the fix's landing
    time. **It was already fixed by another agent BEFORE this system check started**: `unified-trading-library@9081e51c`
    (authored 2026-07-21T02:09:30Z, already on `live-defi-rollout`) bumped the budget 0.5s → **3.0s** for exactly this
    reason (docstring cites the same shared-host contention: "consistently measured 0.57–0.70s… ~4× headroom over the
    worst observed CI time… a revert… exceeds it by 3.5×"). Re-checked all 9 "F1 build" failures in the original sample
    — **every one is dated 2026-07-20T19:26Z–2026-07-21T01:35Z, i.e. before the 02:09Z fix**; every UTL failure _after_
    the fix (6 of them, through 2026-07-21T23:20Z) was the unrelated pip-audit/CVE issue, not F1PerfGuard; and the last
    15 UTL runs (through 2026-07-22T07:49Z) are all green. **Zero recurrences since the fix landed — already resolved,
    no operator decision needed, do not re-open or lower the budget.**
  - **Coincidental, NOT migration-caused, already fixed by others**: instruments-service's
    `TestWriteVenueCanonicalPartition` tests hit `pytest_socket.SocketConnectBlockedError` on `169.254.169.254` for a
    few hours today. Traced (via a dedicated sub-agent, `instruments-service` git history) to a same-day refactor
    (`a9be6ce9`, 03:20 UTC) that changed `_write_venue` to build its own real `get_data_sink()` instead of using the
    test's mocked sink, without updating the test's mocks — would have failed identically on a GitHub-hosted runner
    (pytest-socket's `--allow-hosts` is the same either way). Two slots raced a fix within ~50 min
    (`4ca56889`/`14a1548f`, reconciled `a74e0c46`); HEAD is clean.
  - **Real, currently-live, fleet-wide, but NOT migration-caused**: a freshly-disclosed CVE pair in `pyasn1==0.6.3`
    (CVE-2026-59885, CVE-2026-59886) is failing the pip-audit gate (part of the merged `checks` leg / Codex compliance)
    on every repo that depends on it — confirmed red on unified-trading-library, features-service, and alerting-service
    (instruments-service likely too). This predates and is unrelated to the CI-cost work; it needs a version bump/pin or
    a documented waiver. Not actioned here (out of this plan's scope) — flagged to the operator.
  - **Everything else sampled** (instruments-service hardcoded-test-project-ID / function-size / DeFi-citation-baseline
    / UAC-adapter-registration-drift failures; the single `Escalate to Orchestrator` failure on a
    `gh pr edit --add-label` call hitting GitHub's deprecated `projectCards` GraphQL field) is pre-existing/organic
    fleet churn, unrelated to A1/A2/A5/STEP2b/notify-slack/prek/cron-cadence — each caught correctly by gates that were
    unchanged by this plan's work.
  - **Verdict for the operator**: the CI-cost-reduction changes themselves (A1/A2/A5/STEP2b/alert-dedup/cron-cadence)
    are running clean — PM's own `quality-gates-v2` is 157 success / 12 failure / 31 cancelled (cancelled =
    concurrency-superseded, benign) over 5 days, and none of the fleet failures trace back to those specific changes.
    The one thing that WAS broken because of this plan's work (`ldr-docs-gate`) took two fix attempts — see the two
    CORRECTION entries above — and is now fixed pending live confirmation on the next real doc push. The F1PerfGuard
    finding above was itself later corrected too: it turned out to already be fixed by another agent before this check
    started, not an open regression.
- **`ldr-docs-gate` 4 operator-suggested improvements — SHIPPED 2026-07-22** (`unified-trading-pm@0349d1d15` +
  `51ce7c394`, same session as the LIVE PROOF above):
  1. Trigger switched `push` → `schedule: "0 * * * *"` + `workflow_dispatch` — cuts this workflow's own contribution to
     shared glue-runner load from ~240/day to 24/day.
  2. Full-corpus scan (not diff-since-last-push) KEPT deliberately — measured 2.04s for the whole 1670-doc corpus, so
     scoping buys negligible performance and doesn't map cleanly onto a periodic model anyway. What per-push attribution
     gave is recovered via a per-violating-file `git log -1` lookup instead — MORE precise than `head_commit` once
     hourly batching means several commits land between checks.
  3. New `docspec.validate_doc_references()`: existence-only check for frontmatter fields that reference other docs by
     relative path (`related`, `codex_ssots`, `supersedes`, `depends_on`, etc.), skipping bare slugs/prose by design
     (only entries containing `/` and ending `.md`/`.mdc`, no whitespace). Measured against the live corpus: 336 raw
     hits → 244 were references to a plan later completed+archived (a normal lifecycle event, now discounted via a
     `plans/archive/**` basename fallback) → 91 genuine dead links remain, seeded into
     `scripts/plan-hygiene/doc_reference_baseline.yaml` (same shrinking-ratchet convention as
     `defi_address_citation_baseline.yaml`) so the check gates NEW breakage only, not day-one pre-existing debt.
     Verified live: injecting a synthetic broken reference correctly failed with a
     `(NEW — not in doc_reference_baseline.yaml)` marker; reverted clean; `--update-doc-ref-baseline` confirmed
     idempotent (zero-diff re-run).
  4. On red, in addition to the existing Slack page, now ALSO dispatches `wall_type: plan_health` to
     `escalate-to-orchestrator.yml` (the SAME already-built resolver `plan-health-agent.yml`'s PR-gate uses —
     `server/plan_health.py` + `agents/plan-health.md`) via `pr_number: 0` (non-PR-scoped, sanctioned by that workflow's
     own contract), so a worker actually attempts the fix instead of only paging a human.
  - **NOT YET VERIFIED**: the `schedule:` trigger resolves against the repo's DEFAULT branch (`main`), which still had
    the pre-fix workflow file at commit time. Tried a direct push of just this one file to `main` — correctly REJECTED
    by branch protection (PR + required `quality-gates-v2` check, no exception; my assumption that the
    `.github/**`-direct-push carve-out meant a literal git-push bypass was WRONG for this repo's actual GitHub ruleset).
    It will reach `main` via the existing LDR→main auto-promote cycle (`ldr-to-main-promote(-fleet).yml`, `*/15`,
    v2-gated auto-merge) — new todo below to confirm the cron actually fires once that lands.
- **LESSON (2026-07-22): never pipe a secret value into visible tool output while inspecting the VM.** Twice this
  session — once reading the Slack bot token from Secret Manager to test auth, once running `ps aux`/`systemctl status`
  on the glue-runner cgroup (which embeds each JIT-ephemeral runner's registration token as a `--jitconfig` base64 CLI
  arg) — a live token landed in plaintext in tool output/the conversation transcript. Neither was written to a file
  (checked: no token-shaped string anywhere in this session's scratchpad), but both were avoidable: check a secret's
  exit code / length instead of `head -c`'ing its value, and never dump a bare `ps aux`/`systemctl status` on this
  specific cgroup — pipe through `ps -o pid,etimes,cmd | cut -c1-80` or grep for the process NAME only.

- **2026-07-23 — 1-week interim billing check (operator ask: "did the migration pay off?").** NOT the scheduled two-week
  Phase-5 re-pull below — an informal 1-week checkpoint, live-pulled from the same Enhanced-Billing ledger
  (`github-billing-token` → `GET /users/IggyIkenna/settings/billing/usage?year=2026&month=7`, 1,283 line items, 100%
  `product=actions`, token shredded from scratchpad immediately after the pull). Method: pre = Jul 1–15 (the plan's own
  Phase-0 baseline window); post = Jul 17–22 (6 full days — the first clean days after BOTH STEP 2, 37/37 movers, and
  STEP 2c, the composite-action conversion, landed 2026-07-17); Jul 16 excluded as the deploy/transition day (only 10/38
  flipped, canary testing in progress, spend that day was actually the month's 2nd-highest); Jul 23 excluded as a
  partial day (pulled mid-session).
  - **PM (the only repo STEP 2 touched) — real, measured win**: **$16.89/day → $10.94/day, -35.3%**
    (-$5.96/day;
    run-rate ~$513/mo → ~$333/mo, ~**$181/mo saved** if sustained;
    ~$36 actually saved over the 6 clean post-migration
    days). Against the tighter immediately-prior week (Jul 8–15 = $24.74/day,
    since spend was ramping into mid-July — see the Jul 13/14 spike that triggered this whole plan) the drop reads
    steeper: -55.8%, ~$420/mo run-rate. Report both; the true number is baseline-sensitive and the 2-week re-pull will
    tighten it.
  - **Fleet-wide total did NOT drop** — $35.51/day → $38.37/day (**+8.1%**), nowhere near the plan's own
    "~$1,000/mo →
    ~$300–400/mo" target. Root cause, isolated by repo: **every non-PM repo rose**,
    $18.61/day → $27.44/day (**+47%**, ~$566/mo → ~$834/mo run-rate) — and STEP 2 touched **zero** non-PM workflows, so
    this is not the migration backfiring. Per-day trace shows several repos (features-service, agent-orchestrator,
    deployment-api, market-tick-data-service) were already elevated on Jul 14–16, _before_ migration — a fleet-wide
    activity ramp this plan didn't touch, now masking PM's real saving in the naive fleet total. Not investigated
    further (out of this plan's scope) — worth a look if it doesn't revert on its own by the 2-week re-pull.
  - **Data-quality note**: this pull's Jul 1–15 fleet total
    ($532.58) is ~10% above the plan's originally-recorded
    baseline ($485, frontmatter `source:`) — Enhanced-Billing
    appears to backfill/revise a few days after the fact (the original was pulled ~Jul 15/16, before the period closed).
    Use this session's $532.58/$16.89-per-day-PM as the more complete Phase-0 reference going forward.
  - **Verdict**: PM's piece of the plan is working as designed, in the right direction, at roughly 36–100% of the item-1
    estimate ($400–500/mo) depending which baseline you trust — genuine progress, not yet provable as the full plan
    target, and invisible in a naive fleet-total check because of unrelated fleet growth. Don't re-derive this by hand
    next time — the pull command + math above is reusable verbatim for the scheduled 2-week comparison.

- **2026-07-23 (session end) — LESSONS worth more than the state.** Recorded because each cost real time today and none
  of it is inferable from the diffs:
  1. **I stated two things before verifying them, and both were materially wrong.** (a) Published
     "~$180–195/mo of
     staging waste, all GitHub-hosted" — PM's four drivers were ALREADY self-hosted since STEP 2 (in this plan's own
     MOVE list, which I failed to re-read); real figure ~$166/mo,
     ~97% of it in the two templates that CANNOT be self-hosted. (b) Repeated a sub-agent's "transient xdist flake"
     diagnosis — it was deterministic and concealed a P1 gate-bypass. **Rule: a sub-agent's DIAGNOSIS is a hypothesis,
     not a finding. Re-run the check yourself before it reaches a doc or the operator.**
  2. **`billable={}` (absence of the `UBUNTU` key) is the honest self-hosted check on this account.** `/timing`'s
     `total_ms` reads 0 for HOSTED jobs too — it proves nothing on its own. This is what made the wrong cost figure look
     plausible.
  3. **PM's LDR is too busy for the documented sentinel-race workaround alone.** The known P0 workaround (chain
     `quality-gates.sh --no-fix && quickmerge.sh` in one shell) was NOT sufficient — PM takes a push roughly every ~2
     min while its gate takes ~4, so the commit always arrived stale (failed 3×, drift of 3 → 1 → 1 commits). What
     worked: a bounded `for i in 1..5; pull --rebase --autostash; quickmerge; break-if-clean` loop — landed on
     attempt 2. Use the loop on PM; a single retry is not enough. NEVER `SKIP_BRANCH_DRIFT` (human-only).
  4. **Derive fleet-rollout order topologically from `workspace-manifest.json`, don't discover it by failure.**
     Yesterday's rollout blocked repo-by-repo on quickmerge's dep-audit. Today, computing dependency layers up front
     (Layer 1 `deployment-ui`/`unified-api-contracts`/`unified-trading-system-ui` → L2 `unified-trading-library` → L3 17
     repos → L4 `deployment-api`/`e2e-testing` → L5 `system-integration-tests`) let batches of 5-6 run cleanly in
     parallel. The one-liner that produces it is in the session transcript's audit step; re-derive with a topological
     sort over `repositories.<repo>.dependencies`.
  5. **gitleaks false-positives on ordinary prose — and the trap is RECURSIVE.** The `generic-api-key` rule blocked a
     `docs(plans):` commit twice today. Trigger shape (described, deliberately NOT reproduced here, see why below): a
     frontmatter line where the word "key" is followed by a comma and then a slash-joined token pair — gitleaks reads
     that token as a secret assigned to the "key". The recursion: my FIRST fix reworded the frontmatter, but then
     writing THIS lesson quoted the original string verbatim, which re-triggered the identical block on the very commit
     carrying the lesson. **So: describe such a trigger, never quote it.** Also: do NOT add a gitleaks suppression for a
     doc, and do not assume a gitleaks failure means you leaked something — read the `Finding:` line first, it prints
     the matched context.
  6. **Rejected approach, so it isn't re-walked:** self-hosting the two staging fleet templates to make them free. Not
     possible — all 8 runners are registered to `unified-trading-pm` ONLY (fleet repos measure 0;
     `orgs/IggyIkenna/ actions/runners` → 404, personal account, no org pool). Flipping their `runs-on` would hang all
     24 rendered copies. This is the plan's existing **KEEP-T** class, re-confirmed by measurement.

---

## Cost ruling 2026-07-23 — semver-agent stays DEAD; minting moves to the PM reconciler (option B)

Investigating the dead fleet release tagging (`plans/active/issues/post_cutover_silent_assumption_sweep_2026_07_23.md`
F2) surfaced a decision that belongs to THIS plan, because it is a spend decision, not a repair.

**Root cause of the tagging outage was not a bug — it was an orphaning.** `semver-agent.yml` triggers on
`push: [staging]`; the 2026-06-27 cutover made staging dormant, so the only thing that mints `v*` tags simply stopped
firing (last runs UTL 2026-06-28 / UAC 2026-06-27, matching each repo's newest tag exactly). Measured impact: **22
repos, 26–29 days, ~2,490 unreleased commits.**

**Reviving it was built, proven, and then REVERTED — on cost and noise:**

| axis         | measured                                                                                                                         |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| GHA cost     | `ubuntu-latest` (unmovable — self-hosted runners are PM-only, no org pool), ~~178 runs/day, 1-min billing minimum ⇒ **~~$32/mo** |
| commit noise | **733 PM `chore(manifest)` commits in 30 days — ~24/day, peak 84/day**, into the merge-driver file every slot rebases on         |

~$32/mo is a **~19% add-back** against this plan's ~$166/mo baseline, which is why it was rejected here rather than
treated as a straightforward fix. **Option B** puts minting in `reconcile_release_tags.py`, already scheduled `*/30` in
PM on **self-hosted runners (\$0)**, with ONE batched manifest commit per run instead of one per bump — same versions
and rollback capability, no new billable runs, no commit storm.

**Reverted, verified clean:** `unified-api-contracts@d9ff488b`, `unified-trading-library@df89ac54`,
`unified-trading-api@6987074`. The proven template is recoverable from the pre-revert shas cited in the issue doc.

**KEPT deliberately** (zero cost, zero noise, independent of the minter design):

- the release-stall **detector** in `reconcile_release_tags.py` — converts a silent 4-week outage into a `::warning::`
  naming the repos and their staleness (this is what measured the numbers above);
- `publish-package.yml` **fail-closed on `0.0.0.dev0`** + `fetch-depth: 0` (a shallow checkout has no tags, so hatch-vcs
  emitted a sentinel version — that wheel is in AR from 2026-07-03);
- `unified-trading-library@08b4d89a` — the `:VERSION` Docker tag is no longer re-pointed at new content.

**Lesson for this plan's cost model:** "revive the dead thing" is not automatically the right fix. The measurement that
mattered here was not whether it works, but what it costs per month and how many commits/day it generates — and both
were knowable before writing any code. Measure the running cost of a mechanism BEFORE restoring it.
