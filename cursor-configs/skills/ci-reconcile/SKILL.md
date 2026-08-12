---
name: ci-reconcile
description:
  Reconcile the whole fleet's CI/CD pipeline to actually-green, at the root cause — not just re-reading the ci-failures
  Slack channel. Cross-checks every repo's REAL GitHub Actions state against what Slack/ci_status claims (Slack
  timestamps and declared states are not ground truth and go stale fast), classifies every red/lagging item by root
  cause (fleet template-rollout breakage / genuine code regression / transient self-hosted-runner flake / dependency
  phantom-clone / alert-accuracy bug / promotion-lag / provenance-gate block / a standing monitor's own decision
  silently not taking effect, e.g. a release-tag minter that reports success while minting nothing), fixes each at the
  root via the correct documented recovery path, cross-checks whether the AO `ci_failure_watcher` escalation should have
  caught it and didn't, and re-sweeps EVERY repo AND every standing monitor before declaring done — the monitor
  population is re-derived fresh each run from BOTH the generated `CICD-WORKFLOW-CATALOG.md` (GitHub-Actions-native
  `schedule(...)` workflows) AND a `scripts/self-hosted-runners/*.sh` grep for host/VM-dispatched monitors (systemd
  timers on the CI runner boxes that page via `repository_dispatch` — invisible to the GH Actions catalog entirely),
  never a hand-picked list of "other alert sources I happened to notice," because that whack-a-mole pattern already
  produced two false "all quiet"/"unblocked" declarations this skill had to walk back — once for a monitor the catalog
  never listed, once for a monitor that doesn't run in GitHub Actions at all. Doesn't NEED Slack read access — every
  signal it checks has a directly-queryable system of record via `gh`/`gcloud`, so it runs identically whether invoked
  interactively or dispatched to AO; both now also have direct Slack read access (`scripts/dev/slack-read-channel.py`,
  `/codex/05-infrastructure/agent-slack-read-access.md`) usable as an optional § 0 bootstrap accelerant, never as a
  substitute for the gh/gcloud re-verification. Always auto-fixes — no
  separate `--fix` flag, no propose-then-wait; it ships corrections directly (quickmerge / reprovenance_bypass.sh / a
  reviewed template rollout) the same way this workspace's background agents already do, and reports what it found + did
  + verified, closing with a visible checklist of every repo and monitor swept so "unblocked" doesn't have to be taken
  on faith. A genuinely foreign/bulk/design-level decision (bulk-blessing someone else's bypass commits, a
  branching-model change) still stops for an operator decision with structured options — auto-fix means "don't ask
  before shipping an obvious fix," not "never ask." Also classifies + fixes two structural classes beyond the original
  five (2026-08-09): (f) a corpus-wide check that exists only in a repo's full gate, invisible to whatever fast path
  most commits take — migrate it to a staged-files-only `--only` mode as part of the fix, not just re-baseline it; (g)
  a whole-repo scalar ratchet tripped by a high-velocity promote-PR batching many commits at once, none of which
  individually crossed it locally — check whether it's already fixed on current LDR before re-bumping. Also
  (2026-08-11): (h) a false alarm — a monitor that fired with no real underlying problem — gets a structural fix to the
  monitor's own detection logic, not just a "false alarm, no action" dismissal, since an uncorrected false-positive mode
  erodes trust exactly like a missed real one and will keep re-paging (a PRIOR "false alarm" verdict is itself a claim to
  re-verify, not inherit — the ibkr-gateway-infra case here was previously written off as benign and hid a real
  always-empty-scope bug); (i) a regex/text ratchet checker counting a comment/docstring mention, broken by a pure
  prose-condensing commit — drop the stale baseline entry, don't revert the harmless edit; (j) a full-corpus
  `--regenerate-baseline` picking up leftover `.stale-pre-history-rewrite-*` checkout directories as live repos — diff
  any regenerate output before shipping it; (k) a 3-way manifest/JSON reconciler's field-classification allowlist
  missing a structurally-identical field under a different key, causing a mechanically-resolvable conflict to escalate
  as genuine — extend the classifier, don't hand-resolve once. And a "self-healed" verdict must be corroborated
  against an actual RECOVERED/GREEN post in the alert channel, not just inferred from current-green CI state — a missing
  recovery post is itself a small asymmetric-alerting finding. Also expect (and reconcile with, never blindly trust or
  silently duplicate) a concurrent `/ci-reconcile` pass — check `plans/active/issues/` and `ps aux` for a peer session's
  QG run on your target repo before diving in from scratch. A branch-scoped `gh run list` success is NOT proof a
  shipped fix is promote-PR-clean — check every touched repo's open promote PR too (a promote-PR check-suite can fail
  on a different diff base even when the plain branch push is green), and re-pull `#ci-failures` right before
  declaring done, not just once at session start — a single early Slack snapshot misses everything that fires later
  in a long session, and the read credential itself can expire mid-session without you noticing unless you retry. Under
  `/autonomous` this polls on an interval rather than doing one pass and stopping, since neither class has an
  automated detector elsewhere. Trigger on `/ci-reconcile`, "unblock the CI alerts", "fix these
  Slack CI alerts at the root", "reconcile the pipeline", "why is Slack saying X but CI shows Y", "is the pipeline
  actually unblocked", "check if CI escalation caught this", "check the runner fleet / Cloud Build health", "make sure
  nothing is left unresolved".
---

# /ci-reconcile — fleet CI/CD reconciliation and root-cause fix

Answers one question with evidence, then fixes what's actually broken: **is the fleet's CI/CD pipeline really green, and
where exactly is it not — at the root, not the symptom?** Built from the 2026-08-07 incident where a fleet-wide
workflow-template rollout broke `quality-gates-v2` on 8 repos; by the time the Slack wall of alerts was read, 6 of the 8
had already self-recovered, one had a genuine unrelated dependency bug masquerading as a code regression, and the
"resolved" Slack message for the last one was posted while the repo's own gate was still red.

**Always auto-fixes.** This is not a diagnose-and-wait skill (unlike `/data-pipeline-reconciliation`'s read-only
contract) — ship every root-caused fix the same way this workspace's background agents already do
(`quickmerge.sh --agent --files`, `reprovenance_bypass.sh`, a reviewed template rollout), then verify, then report.
Don't stop mid-sweep to ask "should I fix this?" — the findings-triage HARD RULE (in-your-file → fix in same commit;
outside-plan small+clear → ≤30 min) already covers the judgment calls; escalate only a genuinely big/ambiguous finding
per that rule.

## 0. Ground truth first — Slack/ci_status is a claim, GitHub Actions is the fact

**Never act on a Slack alert's stated state.** Before touching anything, re-derive current reality directly:

```bash
# Repo registry — never hardcode a repo list, read the real one
python3 -c "import json; [print(r) for r in json.load(open('unified-trading-pm/workspace-manifest.json'))['repositories']]"

# Per repo, the actual latest conclusion on the trigger branch (usually live-defi-rollout)
gh run list --repo IggyIkenna/<repo> --branch live-defi-rollout --limit 3 --json status,conclusion,name,headSha,createdAt
```

A repo named in an old alert may have already self-recovered (measured: 6/8 repos in the 2026-08-07 incident were green
again within 90 minutes, via a fix commit nobody re-announced). Build the CURRENT red/lagging list from this sweep, not
from the alert text — the alert text tells you where to START looking, not what's still true.

**That starting alert text no longer needs the operator to paste it** —
`python3 scripts/dev/slack-read-channel.py ci-failures <hours>` pulls `#ci-failures` directly (GSM-backed, works
identically on AO — see `/codex/05-infrastructure/agent-slack-read-access.md`). It is still only a starting pointer: the
gh/gcloud sweep above is what decides truth, never the Slack text itself.

## 0b. The completeness contract — sweep EVERY standing monitor via the generated catalog, not a hand-picked list

**This section exists because of a real failure**: an earlier run of this skill hand-curated a short list of "other
alert sources" (glue-runner health, Cloud Build) after encountering them, declared the pipeline "unblocked," and was
wrong — a `release-tag-stall` alert (from a monitor never even considered) and a recurrence of the SAME glue-runner 403
(wrongly written off as "transient" from a handful of green runs, with no understood mechanism) surfaced within hours.
**A hand-picked list of "other alert sources I happened to notice" is exactly the whack-a-mole pattern this skill exists
to replace.** Do not repeat it — the population of standing monitors is enumerable, so enumerate it, every time:

```bash
cd unified-trading-pm && python3 scripts/generate-workflow-catalog.py   # regenerate fresh, don't trust a stale copy
```

This writes `docs/repo-management/CICD-WORKFLOW-CATALOG.md` — every workflow in the PM repo (the fleet's shared CI/CD
brain), grouped by stage, with its trigger type. **The standing-monitor population is every row whose Trigger column has
a `schedule(...)` and whose Mutates column includes `Slack`** — as of 2026-08-07 that's ~23 workflows
(`cloud-build-failure-watcher`, `reconcile-release-tags`, `cassette-drift-check`, `ldr-ci-monitor`,
`removed-symbols-workspace-sweep`, `ruleset-drift-alert`, `secret-health-check`, `build-smoke-all-repos`,
`cold-storage-cleanup`, `fix-approval-timeout`, `overnight-agent-orchestrator`, `overnight-dead-man-switch`,
`branch-health`, `ci-health`, `digest-drift-sweep`, `glue-pool-starvation-monitor`, `glue-runner-health-monitor`,
`ldr-docs-gate`, `ldr-to-main-promote-fleet`, `promote-fleet-startup-failure-monitor`, `sit-gate-stuck-detector`,
`stale-build-watcher`, `version-coherence-check` — **do not hardcode this list going forward; re-derive it from the
catalog every run**, since workflows get added/removed and a stale hardcoded list silently drifts out of sync the same
way a hand-picked one does).

Most of these are already covered by name in earlier sections (`branch-health`/`ci-health` → § 4/§5,
`ldr-to-main-promote-fleet` → § 4). For every one that ISN'T already covered by an earlier section's specific recipe:
don't wait for its next scheduled tick or trust its last Slack post — get its current truth directly, right now:

```bash
gh run list --workflow=<name>.yml --limit 3 --json conclusion,createdAt   # is its last run recent + green?
gh workflow run <name>.yml   # if its last run predates its own schedule interval by >2x, trigger a fresh one
```

**A `success` conclusion is necessary but not sufficient for a DECISION-making monitor.** `reconcile-release-tags` and
`semver-agent` are the concrete lesson: `semver-agent` ran `success` on every trigger for 41 days straight while
silently minting zero tags — the workflow "succeeding" only proves the job didn't error, not that it did its actual job.
For any monitor whose purpose is a decision/action (mint a tag, detect a stall, promote a PR — as opposed to a pure
read-only health check), verify the OUTCOME, not just the run conclusion: did a new tag actually appear
(`git tag -l --sort=-creatordate | head -3` on the target repo), did the stall count the detector itself reports
actually go to zero, did the PR it was supposed to merge actually merge. Read the underlying script the workflow invokes
if the outcome doesn't match a green conclusion — that mismatch (green run, wrong/no outcome) is a bug class of its own,
not a lower-priority one.

**A `success` conclusion that DID post is still not proof the condition is quiet — check whether it posted the SAME
verdict it computed, or a dedup/cooldown suppressed the post.** Found live 2026-08-08: `sit-gate-stuck-detector.yml` ran
`success` at its scheduled tick and its own log showed the correct internal verdict (`unified-api-contracts` 8 straight
blocked ticks, `market-tick-data-service` climbing 4→6) — but the `notify/send-notification` step logged
`Dedup decision: should_post=false (key 'sit_gate_stuck' last posted 56m ago < 60m cooldown — suppressed)`, so nothing
reached Slack even though the condition was measurably WORSENING, not just repeating. A monitor's own last-posted Slack
message is therefore not ground truth for "is this still happening" either — when a monitor's job is to detect a
streak/count that can climb, re-run the underlying detector script directly (most standing monitors have one under
`scripts/cicd/` or `scripts/self-hosted-runners/` — check the workflow's own `run:` step for what it invokes) rather
than trusting silence in the channel.
`plans/active/issues/sit_gate_treadmill_recurs_under_high_ldr_velocity_2026_08_08.md` has the full incident and a queued
fix for the dedup key itself.

## 0c. Host/VM-dispatched monitors — invisible to the GH Actions catalog, enumerate them separately

**This section exists because of a real failure**: a sweep declared "30 minutes quiet" using only §0b's catalog-derived
check, while a real, correctly-firing `glue-runner-crash-loop-watchdog` alert had been paging the whole time. §0b's
catalog only sees GitHub Actions workflows with a `schedule(...)` trigger — it is structurally blind to monitors that
run as a **systemd timer on the EC2 host itself** and dispatch INTO GitHub Actions via `repository_dispatch` (e.g.
`ci-health.yml`'s `glue-runner-alert` job receives the page; the systemd timer that decided to fire it never appears as
a row in `CICD-WORKFLOW-CATALOG.md` at all, because nothing about it lives in `.github/workflows/`). "I checked every
`schedule(...)`-triggered workflow" is not the same claim as "I checked every standing monitor" — these are a
structurally different, non-overlapping population and both must be swept.

Enumerate this population the same non-hand-picked way as §0b — don't hardcode the list below, re-derive it:

```bash
grep -rl "dispatch_alert\|repository_dispatch\|/dispatches\"" scripts/self-hosted-runners/*.sh
```

As of 2026-08-08 this finds `glue-runner-crash-loop-watchdog.sh` and `ci-vm-resource-watchdog.sh` (NOT
`classify-glue-workflows.sh` — that one's a manual advisory tool, no timer, not a standing alert source; confirm each
hit actually has its own `.timer` unit before counting it). For each, get LIVE state directly from the host via SSM —
never trust its last Slack post's timestamp as "still current":

```bash
aws ssm send-command --instance-ids <host> --document-name AWS-RunShellScript \
  --parameters 'commands=["systemctl status <name>.timer --no-pager", "journalctl -u <name>.service --no-pager -n 20"]' \
  --region <region>
```

Known host running these as of 2026-08-08: `i-042a6332509482556` (`ap-northeast-1`, the glue-runner pool). If a new CI
host is ever provisioned, re-check there too — don't assume this is the only box that can run one of these.

**Don't trust a monitor's own internal reasoning without independently checking the ground-truth data it claims to
describe** — this is the second half of the 2026-08-08 failure above. When `glue-runner-crash-loop-watchdog` paged, its
own code correctly asked GitHub's busy API first (its documented "primary signal," added specifically to close an
earlier false-positive class) and got `busy: true` — reading that code and seeing the corroboration step present is not
the same as verifying it actually measured the right thing. It didn't: the alert reported `unit_active_seconds` (the
systemd PROCESS's uptime) as the job's duration, silently assuming a busy process and a long-running job are the same
thing. They weren't — pulling the ACTUAL job history (`gh api repos/<owner>/<repo>/actions/runs?status=in_progress` →
`.../jobs`, matching `runner_name`, reading each job's own `started_at`) showed a ~3-hour IDLE gap immediately before a
fresh, minutes-old job; the process had been alive 3.2h, the job had not. Before accepting "the tool checked X so its
verdict is correct," independently confirm what X actually measures against the real system state — this applies
especially to any TIME-DURATION claim (process uptime, job age, and queue age are three different things a script can
easily conflate). Root-cause fixed in `scripts/self-hosted-runners/glue-runner-crash-loop-watchdog.sh`
(`current_job_started_epoch()` now resolves the real job start time via the Actions API instead of trusting process
uptime) — read that function's comment for the full incident if this recurs in a different script.

A recovery/informational post (e.g. `glue-runner-crash-loop-watchdog` "recovered") is not an open finding by itself —
but if the SAME condition (same runner, same monitor) recurs across the sweep window, that crosses from "an existing
watchdog handling a flake" into "a real host-level problem," and gets its own finding. An alert that references an
existing dated issue doc (`plans/active/issues/`, including `plans/archive/issues/` for closed ones) is
separately-tracked — confirm its CURRENT state briefly rather than assuming the doc's last status still holds, and
report it in § 7 without a full from-scratch re-diagnosis unless it's now genuinely different from what the doc says.

## 0d. Self-healing claims need Slack-corroborated evidence, not just inferred from current-green (2026-08-11)

Declaring an item "self-healed" on the strength of "current CI state is green now" alone conflates two different claims:
_this specific incident resolved_ vs. _something else fixed it later and we never saw how, or the underlying condition
was never actually broken the way the alert said_. Before writing "self-healed" in § 7, pull the actual alert channel
for the window (`python3 scripts/dev/slack-read-channel.py ci-failures <hours>`, or the specific monitor's own channel)
and look for a matching RECOVERED/GREEN/INFO post for that repo + commit. Most of this skill's monitors
(`ldr-ci-monitor`, `cloud-build-failure-watcher`, `sit-gate-stuck-detector`) post an explicit recovery message, not just
a red one — cite that post (timestamp + message text) as the evidence in § 7, not just a `gh run list` success.

If NO recovery post exists in the channel for something you're about to call self-healed: the self-heal claim can still
stand (current CI state is real ground truth per § 0), but say so explicitly — cite CI state alone, don't imply Slack
confirmed it. And treat the missing recovery post as its own small finding: a monitor that pages on RED but never pages
the matching GREEN return is an asymmetric-alerting gap (the reader has no way to know from Slack alone whether a paged
incident ever cleared) — worth a one-line mention in § 7 even when it isn't the main incident, since it's the same
"silence isn't evidence" principle § 6 already applies to monitor health, now applied to individual incident resolution.

## 0e. Expect a concurrent `/ci-reconcile` session — reconcile with it, don't silently duplicate or trust it blindly

This skill is invoked from many places (a scheduled AO job, an operator-triggered laptop session, another slot's own
firefighting) and nothing prevents two runs overlapping on the same fleet at once. A single 2026-08-11 run found BOTH: a
same-day `plans/active/issues/ci_reconcile_overnight_batch_2026_08_11.md` doc already covering 3 of 4 threads it was
about to investigate from scratch, AND a live peer session actively running its own `quality-gates.sh` on the exact same
repo checkout at the same time (visible via `ps aux` — multiple `bash scripts/quality-gates.sh` processes with different
session-scratchpad log paths under `/tmp/claude-*/`). Neither is a problem BY ITSELF (the QG governor's per-repo
concurrency cap correctly queues concurrent runs; a prior session's issue doc is exactly where findings should live) —
the risk is wasted duplicate work or, worse, stepping on a peer's uncommitted tree. Before deep-diving any thread:
`grep`/`ls` `plans/active/issues/` for a same-day `ci_reconcile*`/matching-topic doc and read it — independently
RE-VERIFY its claims against live `gh`/`gcloud` state per § 0 rather than trusting them, since a prior pass can itself
be stale or wrong (see (h)'s ibkr-gateway-infra correction — the exact doc this note is about), but don't re-derive from
zero what's already been correctly diagnosed. If `ps aux | grep quality-gates.sh` shows another session's process
already running against your target repo, that's normal governor-queued contention, not a bug — don't kill it (banned:
"never bulk-kill another slot's pytest/QG") and don't spawn a redundant second run against the same tree; wait for the
existing one or check its log file for the live result before starting your own.

## 1. Classify each still-red item before touching it

For every repo whose current `quality-gates-v2` conclusion is `failure`, pull the real log
(`gh run view <id> --log-failed`) and classify:

- **(a) Fleet template-rollout breakage** — the triggering commit is a `rollout-workflow-templates.sh`-generated
  `chore(ci): roll out …` commit that touched only `.github/workflows/*.yml`, and the failure is a workflow-YAML
  parse/step error. Root fix is in the SOURCE template (`unified-trading-pm/scripts/workflow-templates/`), never a
  hand-edit of the per-repo copy — see § 3.
- **(b) Genuine code regression** — the failing selector (`tests`/`typecheck`/`lint-codex`) traces to an actual
  application-code change. Fix the code, ship via `quickmerge.sh --agent --files`.
- **(c) Dependency phantom-clone** — **a CI-only commit (no app code touched) that still fails `typecheck`/`lint-codex`/
  `tests`** is the tell. The QG workflow clones sibling repos (UTL/UAC/etc.) at a resolved version to typecheck/test
  against; a version-tag-resolution race can silently clone the WRONG version, producing spurious `reportUnknown*`/
  `reportAny` typecheck floods or unrelated test failures that are not real bugs in the repo under test. Confirm by
  diffing the failing repo's `.github/workflows/quality-gates-v2.yml` clone/version-resolution logic against a
  currently-green repo's copy, and by reading the actual error content (not just the aggregate `qg_red_reason`, which
  can itself be wrong — cross-check against which QG slice artifacts actually uploaded `qg-slice-failed-*`).
- **(d) Transient self-hosted-runner flake** (cache race, `uv sync --frozen` cache contention) — only re-run after you
  understand why; a blind retry that happens to pass is not a root-cause fix and will recur.
- **(e) Alert-accuracy bug** — `ci_status` (Firestore-SSOT, written by `ci-status-update.yml`) declared a "resolved"
  state (e.g. `SIT_VALIDATED`) for a sha whose OWN `quality-gates-v2` run is still `failure`. Before calling this a bug:
  check whether `SIT_VALIDATED` is legitimately a decoupled signal (system-integration-tests against a different
  snapshot) vs the repo's own unit-level gate — read `scripts/self-hosted-runners/hosted-baseline/ci-status-update.yml`
  for the actual state-machine transition logic. If it's a real inconsistency (a "resolved" status posted while the
  same-sha gate is still red), that's a template bug — see § 3. If it's a real but confusingly-worded distinct signal,
  fix the message wording, same path.
- **(f) Precommit/fast-path blind to a full-gate-only check** — the failing selector is a corpus-wide validator (a
  ratchet, a link check, a frontmatter/todo-format rule) that exists ONLY in the full `quality-gates.sh` / full
  hygiene-sweep path, with no equivalent in whatever FAST path most commits for that repo actually take (a docs-only
  fast-path like `safe-doc-push.sh`, a `--precommit` prek hook). A violation introduced by an earlier fast-path commit
  sails through clean and only surfaces hours/days later on an unrelated commit's full CI run — CI correctly names the
  triggering SHA, but that SHA usually didn't cause the violation. Tell: `git blame`/`git log -p` on the violating
  line(s) points at an EARLIER commit than the one CI flagged, and that earlier commit shipped via the fast path. Root
  fix: give the checker an `--only <staged-files>` (or `--diff-base <ref>`) mode that validates ONLY the commit's own
  diff, no corpus-wide baseline math, and wire it into the fast path's checklist — same pattern as
  `check_terminal_status_archived.py --only` / `check_finalize_plan_coverage.py --only` / the 6 checks migrated
  2026-08-09 (`check_plan_operator_ruling_evidence.py`, `check_archive_candidates.sh`, `check_reference_paths.py`,
  `check_effort_signal_ratchet.py`, `check_todo_regression.sh`). **Migrate every NEW instance you find the same way, as
  part of the same fix — don't just re-baseline/file-it-and-move-on** (operator ruling 2026-08-09, after this skill
  missed this class the first several times it recurred in one night — `unified-trading-pm` PR #2670). This is the
  single highest-value thing this skill can do beyond firefighting the reported alert: every instance closed here is one
  fewer future 2-6AM page.
- **(g) Promote-batch snapshot race on a whole-corpus SCALAR ratchet** — the failing check compares a repo-wide TOTAL
  count (not per-file, not diff-scoped) against a single hardcoded/frozen baseline, and the repo ships via
  `quickmerge.sh` at high commit velocity (batches of dozens to 100+ LDR commits can land in one promote-PR). Each
  commit's local `quality-gates.sh` run only ever sees a SNAPSHOT of the corpus at that developer's pull time, so
  individually-legitimate additions from DIFFERENT concurrent commits accumulate past the frozen ceiling with no single
  local run ever seeing a violation — the promote-PR's aggregate CI run is the first point anything crosses the line,
  and it blocks whichever unrelated commit happens to be in that batch. Tell:
  `git log -S '<baseline var>=' \ --format="%h %ad %s" -- <the QG script>` shows a recurring history of "re-measure and
  bump" commits, each citing "N unrelated commits since the last catch-up" (measured on `market-tick-data-service` STEP
  5.94/5.95 type:ignore/pyright-suppression ratchets: 3 separate re-measure commits in under 2 weeks, PR #885
  2026-08-09). **Before manually re-bumping the baseline: `git pull --ff-only` the target repo and re-check** — another
  concurrent session may already have landed the same catch-up bump on LDR, in which case the failing promote-PR is just
  a stale pre-bump snapshot that clears on its own next scheduled cycle (`*/15`) and needs no action beyond confirming
  that. If it genuinely hasn't been fixed, the in-the-moment unblock is the repo's own established "re-measure, cite the
  drift count, never silently hand-raise" pattern — but log the RECURRENCE itself as a structural finding: converting
  the check to diff-scoped/attributed (only fail if files the commit/batch actually touches show MORE occurrences than
  at the diff base) stops it recurring, same philosophy as (f)'s `--only` mode applied to a scalar-count check. That
  conversion is careful surgery on a script every commit depends on — dispatch it as its own scoped task, don't rush it
  inline while firefighting the active block.
- **(h) False alarm — the monitor fired but there genuinely wasn't a problem.** Tell: after ground-truth verification (§
  0), the underlying condition the monitor claims exists doesn't. **Don't just log "false alarm, no action" and move
  on** — an uncorrected false-positive mode erodes trust in every future page from that monitor exactly as much as a
  monitor that misses a real problem, and it will keep re-paging on the same non-issue. Diagnose WHY it fired: does its
  detection logic conflate two different signals (commit count vs. release-worthy commit count; process uptime vs. job
  age — see § 0c's `unit_active_seconds` incident for the same conflation pattern in a different monitor), or is the
  threshold simply miscalibrated for this repo's real cadence? Fix the detector at the root — same routing as (f)/(g): a
  per-repo script fix ships via § 2, a shared template/workflow fix ships via § 3. Only skip the structural fix when the
  false trigger was a genuinely one-off external cause that won't recur (e.g. a transient API outage) — state that
  reasoning explicitly in § 7 rather than silently letting a recurring false-alarm pattern stand unaddressed. **A "false
  alarm" verdict is itself a claim that needs verification, not just a plausible-sounding excuse** — an earlier version
  of this exact bullet cited `ibkr-gateway-infra`'s `reconcile-release-tags` stall as "correctly minting nothing,
  unreleased commits were all non-source" and declared no action needed. A later `/ci-reconcile` run (2026-08-11)
  checked the actual `source_dir` `semver-agent.yml` was scoped to and found it pointed at a package directory
  (`ibkr_gateway_infra`) that had **never existed** in the repo (the real package is `ibkr_gateway_client`) — so the
  diff-scope was permanently empty and the bump would silently never fire even on a genuine source change. The earlier
  "false alarm" checked whether recent commits LOOKED non-source; it never checked whether the detector's own configured
  scope was even pointed at real code. Before writing off a stall/false-alarm as "nothing to see here," verify the
  detector's own config target actually resolves to something real, not just that the current diff sample looks benign.

- **(i) A regex/text-based ratchet checker counts a comment/docstring mention, and a pure prose-condensing commit (no
  behavior change) drops the count** (2026-08-11). Tell: the failing selector is a per-file/per-repo ratchet whose
  scanner explicitly does NOT AST-filter comments/docstrings out (check the scanner's own docstring — this is often a
  documented, deliberate simplification, e.g. `check_adapter_contract_regression.py`'s "comments and docstrings are
  intentionally NOT filtered out... If false-positive rate becomes a problem later, switch to AST-walk"), and the
  triggering commit's diff on that exact line is a comment/docstring edit, not a code change. Confirm by reading the
  git-blame'd original text at the baseline's seed point — if the only historical match was inside a docstring
  explaining _why_ something doesn't do X (not code doing X), the baseline entry was always a false-positive risk, not a
  real enforcement point. Fix: drop the specific stale baseline entry (or run the checker's own
  `--regenerate-baseline`/equivalent and diff the result against git HEAD line-by-line before shipping — see (j) for why
  an ungated regenerate is dangerous). Never hand-edit a `DO NOT manually edit — auto-generated` baseline file's content
  by guessing the format; either use the tool's own regenerate path or make the minimal targeted edit that matches
  exactly what a regenerate would produce for that one entry.
- **(j) `--regenerate-baseline` (or an equivalent full-corpus-walk mode) picks up leftover history-rewrite checkout
  directories as if they were live sibling repos** (2026-08-11). Tell: this workspace's local dev tree keeps
  `<repo>.stale-pre-history-rewrite-<timestamp>Z` directories alongside the real repos (leftover artifacts from a past
  `git filter-repo`-style operation) — they still have a real `.git`, so any scanner that tests
  `(child / ".git").exists()` to decide "is this a present repo" will treat them as legitimate. Running a full-corpus
  baseline regeneration in this tree without filtering them out silently adds hundreds of spurious entries for dead code
  no CI checkout will ever contain. **Before shipping ANY `--regenerate-baseline`-class output, diff it against the
  pre-regenerate file and manually account for every new/changed entry** — if any belong to a
  `.stale-pre-history-rewrite-` (or similarly-named leftover) directory, abort, harden the scanner's directory-exclusion
  list to skip that naming pattern, and re-run. This is a workspace-hygiene hazard specific to any local multi-repo tool
  that walks siblings by directory name rather than a registry (`workspace-manifest.json`'s `repositories` list is the
  trustworthy source; a bare `.git`-exists check on the filesystem is not).
- **(k) A 3-way manifest/JSON reconciler's field-classification allowlist is incomplete, so a genuinely
  mechanically-resolvable conflict escalates as "GENUINE NON-CI CONFLICT"** (2026-08-11). Tell: the reconciler (e.g.
  `reconcile_manifest_backmerge.py`, used by `main-backmerge-to-ldr` and the LDR→main promote bots' dirty-state
  handling) has an explicit, documented resolution rule for one field shape (e.g. "both-bumped monotonic version scalar
  → semver-max") but the path-matcher implementing that rule (e.g. `_is_version_field`) only recognizes a HARDCODED set
  of field paths — a structurally-identical field living under a different top-level key (e.g.
  `published_packages. <name>.version` alongside the covered `versions.<repo>` / `repositories.<name>.version`) falls
  through to the conflict escalation even though it's exactly the case the rule exists to handle. Before accepting a
  "genuine conflict" escalation as ground truth: read the reconciler's OWN docstring for what class of field it claims
  to auto-resolve, then check whether the actually-conflicting path matches that description in substance even if it
  doesn't match the literal path list. If it does, extend the classifier (don't hand-resolve the individual conflict
  once — the same gap will refire on every future divergence of that field) — write a test reproducing the real conflict
  via the actual `--base`/`--ours`/`--theirs` triple before and after the fix, run the existing test suite to confirm no
  regression, and if the field pairs a version with a dependent sibling (e.g. `published_at` alongside `version`),
  resolve the WHOLE record atomically from whichever side wins — never split a winning version from a losing timestamp.
  A promote bot's `ahead_by`/PR-dirty state climbing over hours despite "successful" scheduled ticks is the live symptom
  — the bot's own per-tick "success" conclusion just means the workflow didn't crash while failing to actually merge
  anything.
- **(l) A poller's cron interval was throttled down without widening its lookback/dedup window to match, silently
  reopening the exact detection gap the window exists to close** (2026-08-12). Tell: a `schedule:` workflow computes
  `alertable` from a time-bounded query (`createTime >= now - LOOKBACK_MINUTES`, or equivalent) and its own header
  comment states an overlap invariant (e.g. "we look back 20 minutes on a 30-minute cron — overlap so a build created
  right at a tick boundary is never missed") — check whether the LIVE cron still matches the interval that invariant
  assumes. `cloud-build-failure-watcher.yml` was throttled `*/30 -> */15... -> hourly` (2026-07-17, "Phase-3 ci-cost")
  but `LOOKBACK_MINUTES` stayed `20` — on an hourly cron, only `[tick-20, tick]` is ever queried, leaving
  `[tick, tick+40)` (roughly 40 of every 60 minutes) covered by NEITHER the tick that just ran nor the next one. Cloud
  Build failures are invisible to every GH-Actions-based watcher (this file's own header comment: "GCB image builds run
  OUTSIDE GitHub Actions"), so this watcher was the ONLY line of defense for that class — a live, unnoticed ~67% blind
  spot since the throttle landed, caught only because a real failure happened to land in the lucky window. **Before ever
  throttling a poller's schedule for cost: confirm the cost premise is real first** —
  `gh api repos/<owner>/<repo> --jq '.visibility'`; GitHub Actions minutes on `ubuntu-latest` (or any GH-hosted runner)
  are FREE AND UNLIMITED for public repos regardless of frequency, so a throttle on a public-repo workflow saves nothing
  and only costs detection latency. `cloud-build-failure-watcher.yml` lives in `unified-trading-pm`, which went public
  2026-08-06 — the 2026-07-17 throttle's cost rationale had been moot for over a month. If a genuine cost-motivated
  interval change is still warranted on an actually-private repo, widen the lookback/dedup window in the SAME change so
  the overlap invariant keeps holding — never change one side of that pair alone. Self-hosting is not a substitute fix
  for a public repo either: a comment in `ldr-to-main-promote.yml` (dated 2026-08-07) explicitly warns against it —
  self-hosted runners on a public repo are a fork-PR security exposure, on top of buying nothing over the already-free
  `ubuntu-latest` minutes.
- **(m) A stale/superseded promote PR that had posted a CRITICAL alert gets auto-closed with no matching Slack
  resolution — the closing bot recorded it as a GitHub PR comment only** (2026-08-12). Tell: a promote/drain bot
  (`ldr-to-main-promote.yml`, `ldr-to-main-promote-fleet.yml`) closes an old promote PR when a newer LDR tip supersedes
  it — completely normal, correct behaviour (the branch was cut before a later LDR commit landed; merging the stale PR
  would have regressed the target relative to current LDR) — but if that PR's own `quality-gates-v2` run had FAILED, it
  already triggered a CRITICAL "QG slice(s) FAILED" post via the per-repo QG workflow's own notifier. The close step's
  `gh pr close ... --comment "..."` only reaches GitHub, never Slack, so a reader of `#ci-failures` sees the CRITICAL
  and nothing else — exactly the § 0d asymmetric-alerting gap, but here the fix is mechanical rather than just a
  reporting caveat: **the closing bot already has everything it needs (the stale PR number, the reason) to post the
  missing bookend itself.** Root fix (ported into `ldr-to-main-promote.yml`): before closing, check
  `gh pr view <stale_num> --json statusCheckRollup` for a `FAILURE`/`TIMED_OUT` conclusion; if found, accumulate the PR
  number and fire a `recovery: true` INFO post via `notify-slack.yml` naming the closed PR(s) and the fresh replacement
  — skipped entirely for the common case of closing a PR that was never red (that's routine promote-cadence churn, not
  something `#ci-failures` ever alerted on, and posting there too would just be noise). Generalizes: any bot that
  CLOSES/SUPERSEDES an artifact which may have triggered a standing-channel alert should check for that alert's
  precondition before closing and post the matching resolution — don't assume "closing it" is self-evidently visible to
  whoever is watching the alert channel.

## 2. Fix (b), (c), (d) directly in the target repo

Standard single-repo fix path: root-cause, fix, `bash scripts/quality-gates.sh --no-fix`,
`quickmerge.sh "fix: …" --agent --files '<paths>'`, then re-poll `gh run list` until the sha is green. No template/fleet
blast radius here — ship it the moment you're sure of the root cause, per findings-triage.

## 3. Fix (a) and (e) via the template, never a per-repo hand-edit

**Never hand-edit a per-repo `.github/workflows/*.yml` copy** — it will be silently overwritten by the next rollout and
the fix is invisible to every OTHER repo carrying the same bug. The correct path:

1. Find the source template in `unified-trading-pm/scripts/workflow-templates/` (the `.yml.tmpl` the broken per-repo
   file was generated from).
2. Fix the template. Prepare the exact diff.
3. Because this fans out to every repo in `workspace-manifest.json`'s registry (~25 repos) in one shot, do this
   deliberately once: dry-read the rollout script's diff/plan output if it has one, apply, then immediately verify
   across the fleet (§ 5) rather than assuming success. This is still an auto-fix (per this skill's contract) — it is
   not a "propose and wait," but a fleet-wide push earns one clean, careful pass instead of a blind re-run if something
   looks off.
4. Run `bash scripts/workflow-templates/rollout-workflow-templates.sh` per its own usage (read `--help` first — flags
   like scoping to affected repos only, or dry-run, may exist and are cheaper than a full fleet push when only a handful
   of repos actually need the fix).

## 4. Promotion-lag and provenance-gate blocks are in scope

"Unblocked pipeline" includes branches actually propagating, not just the trigger-branch gate being green. Sweep lag:

```bash
gh api repos/IggyIkenna/<repo>/compare/main...live-defi-rollout --jq '.ahead_by'   # LDR ahead of main
gh api repos/IggyIkenna/<repo>/compare/live-defi-rollout...main --jq '.ahead_by'   # main ahead of LDR
```

Or read `scripts/cicd/promotion_lag_monitor.py`'s own output — it's the source of the Slack `branch-health` alert, so
its live state is more current than the alert text.

- **Provenance-gate BLOCKED** (non-quickmerge/bypass commit on LDR, flagged by `check_strict_quickmerge.py`): find the
  real bypass list via `check_strict_quickmerge.py --range origin/main..origin/live-defi-rollout --block` — **not** a
  raw `git log main..live-defi-rollout` count, which mixes in every normally-quickmerged commit and can overstate the
  real number by 10-50x. If it's the current LDR **tip** → `quickmerge.sh --agent --files` it properly through the gate.
  If it's **mid-history** (something landed on top since) → `scripts/cicd/reprovenance_bypass.sh <sha> --push` (read its
  `--help`/source first). **Never hand-arm auto-merge** to route around this. **Size/authorship gate before auto-fixing
  this one**: a small number of commits (roughly ≤5), single-author, diff-reviewed, self-contained → reprovenance
  directly, no need to stop. A larger, foreign, multi-subsystem, multi-agent backlog → this is the one case in this
  skill where auto-fix stops and asks first (structured options: bulk-bless-after-review / re-ship each individually /
  show the list and wait) — bulk-blessing code you can't independently verify as promote-ready is a judgment call, not a
  mechanical fix, per this workspace's own established precedent
  (`plans/archive/issues/utl_ldr_main_blocked_34_foreign_quickmerge_bypasses_2026_07_21.md` and
  `plans/active/issues/provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md`). If the operator
  authorizes the bulk path, still diff-review every commit for anything destructive/secret-leaking/production-credential
  -touching before sweeping it in, and flag-not-sweep anything that fails that screen.
- **Just lagging past the promote cadence, not blocked**: verify the fleet promote cron
  (`scripts/cicd/ldr_to_main_fleet_promote.sh` / the `ldr-to-main-promote-fleet.yml` workflow, `*/15`) is actually
  firing and succeeding (`gh run list --workflow=<it> --limit 5`). If it's healthy and just hasn't ticked yet, don't
  force anything — report expected clear time. If a run is failing, root-cause that same as any other CI failure.

## 5. Cross-check the AO escalation system — don't let a real gap go unfixed silently

For any repo that was still red for a meaningful window (say, >30-60 min) before being fixed: did
`scripts/repo-management/ci_failure_watcher.py`'s auto-recovery actually engage, or did the fix land from a human /
interactive push instead (check the fix commit's author string — `[background-agent]` vs a plain slot/host or
`[unknown]` tag)? A repo that stayed red until an interactive session happened to notice it is an escalation-coverage
gap, not a one-off. If you find a small, clear, obviously-correct bug in the watcher's detection logic, fix it the same
way as any other code fix (§ 2). If the gap is structural (a whole failure class it was never designed to catch, or it
isn't running on the cadence it's supposed to), that's a finding for `plans/active/issues/<slug>_<date>.md` and an
operator notification per the findings-triage HARD RULE — don't quietly patch around agent-orchestrator's own logic
without understanding the design intent first.

## 6. Verify — full-fleet sweep AND full-monitor sweep, not just the repos/monitors that were named

Three separate sweeps, all required before the word "unblocked"/"quiet window"/"no new issues" is allowed in § 7's
report:

1. Re-run § 0's sweep across every repo in `workspace-manifest.json`'s registry, not just the ones the original alert
   named. Every repo should show `quality-gates-v2` conclusion `success` on its trigger branch, and every branch-pair
   from § 4 should be either caught up or genuinely just waiting on its next scheduled tick with a healthy cron behind
   it.
2. Re-run § 0b's catalog-derived monitor sweep, fresh (not reused from earlier in the same session — a monitor you
   checked at the start of a long session may have re-fired since). Every standing monitor gets an explicit verdict.
3. Re-run § 0c's host/VM-dispatched monitor sweep, fresh, via live SSM state — **a `gh run list` scan of PM's own
   Actions runs does NOT cover this population; skipping it is exactly the 2026-08-08 "30-min quiet window" failure** (a
   genuinely-firing host-dispatched alert went unchecked the whole window because the sweep only ever looked at
   GitHub-Actions-native run conclusions). Sweeps 2 and 3 are DIFFERENT populations found by DIFFERENT commands —
   completing one is never evidence the other was covered.
4. **For every repo you SHIPPED a fix to this pass, check its open promote PR(s) too, not just its
   `--branch live-defi-rollout` push CI** (2026-08-11 — a real live miss). Tell:
   `gh run list --repo <r> --branch live-defi-rollout --limit 1` showing `success` is NOT the same claim as "this
   content is mergeable into main" — a promote PR runs its OWN check-suite, sometimes against a different diff base (so
   a diff-scoped ratchet like class (f)/(g)/(k) can fire there even though it stayed silent on the plain LDR push), and
   a failure isolated to the promote-PR check-suite never shows up in a branch-scoped `gh run list`.
   `gh pr list --repo <r> --search "promote" --state open --json number,mergeable,mergeStateStatus` on every repo you
   touched, then `gh pr view <n> --json statusCheckRollup` on anything not `MERGEABLE`/clean — a run still `IN_PROGRESS`
   is fine, a `FAILURE` conclusion is a live miss waiting to be caught by whoever reads Slack next instead of you.

**The bar for saying "unblocked": every repo from sweep 1, every monitor from sweep 2, every monitor from sweep 3, AND
every promote PR from sweep 4 has an explicit, current, verified-clean status in this run — not "I didn't see anything
more in Slack" and not "no new Actions-run failures."** Silence is not evidence of health; several of this skill's own
real findings were monitors that were failing/stale while posting nothing new (a dedup/cooldown suppressing a repeat
page, or a monitor that's simply not running on its expected cadence). If a monitor's coverage genuinely can't be
verified this pass (no direct query path, credentials unavailable), say so explicitly as a coverage gap in § 7 — never
silently drop it from the count.

**Re-poll `#ci-failures` before declaring done, not just once at session start** (2026-08-11 — a real live miss). A
single Slack pull at the top of a long session is a snapshot, not a standing feed — 4 real, unrelated alerts (a
different repo's push failure, a promote-PR-only failure, and a provenance bypass that fired TWICE) landed over the
following ~70 minutes of active fixing and none were caught until the operator pasted them in, because every subsequent
check in that session was a direct `gh`/`gcloud` sweep, never a second Slack read. Direct ground-truth checks answer "is
the specific thing I'm looking at green" — they do not tell you about a DIFFERENT repo/PR/gate that just went red while
you were heads-down on something else, which is exactly what a channel-wide Slack pull is for. Re-pull `#ci-failures`
for the session's elapsed window immediately before writing the § 7 report, even if (especially if) the session has been
running for a while. Separately: the GSM-backed read access (`scripts/dev/slack-read-channel.py`, § 0) is pinned
(2026-08-11 hardening) to the `unified-trading-sa` service-account identity first — a real, non-expiring local
credential on every migrated host (AO's `ubuntu` worker user; the operator's laptop, since 2026-08-11 — see
`/codex/05-infrastructure/agent-slack-read-access.md`) — precisely so it is NOT subject to a human's org-enforced reauth
window. If a re-poll attempt still fails with a `gcloud`/reauth error, that means the pinned account isn't locally
activated on THIS host (or its key is missing/revoked) — that is itself a coverage gap to report explicitly (not
silently skip), since it means the rest of the session's "nothing more in Slack" claim was actually "I couldn't check,"
a materially different claim. Self-heal path:
`gcloud auth activate-service-account --key-file=~/.config/gcloud/keys/unified-trading-sa.json` if the key exists on
this host already; only escalate to the operator if it doesn't (provisioning a new key is a real security decision, not
a routine self-service action) — this is a materially smaller ask than the old "you must interactively
`gcloud auth login`" gap.

## 7. Report

For each item found: root-cause classification (§ 1's letter), evidence (log excerpt / commit sha / diff), what was
shipped (repo + sha, or template diff + rollout confirmation), and post-fix verification (green run id). Explicitly call
out: (1) any alert that was already stale/self-resolved by the time you looked (don't re-fix what's already fixed), (2)
any alert-accuracy issue found and its fix, (3) the AO-escalation verdict from § 5, (4) anything that could NOT be
resolved this pass — file it per findings-triage, never leave it as an unlogged "still broken."

**Close every report with the § 6 checklist made visible**: a table or list of every repo swept (sweep 1), every
GH-Actions-native standing monitor swept (sweep 2, from the regenerated catalog), AND every host/VM-dispatched monitor
swept (sweep 3, from the `scripts/self-hosted-runners/*.sh` grep + live SSM check) — with each item's verified status,
not a prose summary that asks the reader to trust the sweep happened. This is the concrete fix for the failure mode that
motivated § 0b/§ 0c: the reader should be able to look at the list and see for themselves that nothing was skipped,
rather than taking "unblocked" on faith.

## Under `/autonomous` — poll, don't wait to be pasted an alert

**Operator correction (2026-08-09)**: earlier wording here said "re-sweep once more, then stop — continuous monitoring
is `ci_failure_watcher.py`'s job." That undersold this skill's own value: `ci_failure_watcher.py` has automated recovery
for classes (a)-(e); it has NO detector for (f) or (g) above, because those require reading the actual violating content
and its shipping-path history, not just a QG conclusion. Relying on being handed a pasted Slack alert to trigger this
skill means (f)/(g) instances sit undiscovered until they happen to block someone — which is exactly what happened
repeatedly in one night before this skill's classification list even named them.

**When invoked under `/autonomous` or any standing/looping context, don't do one pass and stop**: after a clean sweep,
wait on a bounded interval (10-20 min is reasonable — matches the `*/15` promote cadence § 4 already polls) and re-run §
0's ground-truth sweep fresh, watching every repo's full-gate failures for classes (f)/(g) specifically, not just
whatever the current Slack channel happens to show. Exit the loop only on an explicit stop condition (operator says
stop, or the session/dispatch itself ends) — a quiet window is a reason to widen the poll interval, never a reason to
stop polling.

## What this skill does NOT do

Does not rewrite `agent-orchestrator`'s escalation logic beyond a trivial, obviously-correct fix (§ 5) — a real
design-level gap is a filed finding, not a same-session rewrite. Does not force-push, does not hand-arm auto-merge, does
not bypass the provenance gate other than via the documented `reprovenance_bypass.sh` recovery path, and does not
hand-edit a per-repo workflow copy outside the template source. Codex SSOTs this skill leans on:
`/codex/08-workflows/ci-cd-flow.md`, `/codex/04-architecture/ci-alerting.md`,
`/codex/04-architecture/agent-orchestrator-alerting.md`.
