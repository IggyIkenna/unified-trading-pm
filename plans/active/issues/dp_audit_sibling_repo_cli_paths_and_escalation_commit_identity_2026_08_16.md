---
doc_type: issue
title: >-
  dp-audit sibling-repo CLI subprocess paths do not resolve inside e2e-audit:latest (DP_DIVERGENT_EMPTY has never
  fired) + the container's escalation-issue auto-commit silently fails (no git identity) — both surfaced while
  verifying the DP-WATCHER-006 manifest-hygiene OOM fix
summary: >-
  While root-causing + verifying the DP_CLOUD_RUN_JOB_FAILED (DP-WATCHER-006) OOM recurrence on
  `uts-prod-dp-manifest-hygiene-changed` (escalation agt-fc531b), two SEPARATE, unrelated bugs surfaced via direct
  image-filesystem inspection and live execution logs, neither masking nor caused by the OOM fix itself: (1)
  `manifest_hygiene_daily.py`'s `_DIVERGENCE_CLI` and `_PHANTOM_CLI` paths are computed as
  `WORKSPACE_ROOT / "<sibling-repo-name>" / "scripts" / "<file>.py"`, which is correct for local multi-repo dev
  (`.tabs/<N>/<repo>/`) but WRONG inside the `e2e-audit:latest` container — `unified-trading-library`'s own Dockerfile
  COPies its repo content directly to `/app` (not `/app/unified-trading-library`), and `instruments-service` is not
  copied into this image AT ALL. Confirmed live: `_check_divergence` and `_check_missing_expected` log
  `SKIPPED (divergence_cli_absent)` on EVERY asset_group, every run — `DP_DIVERGENT_EMPTY` has silently never fired in
  production. `_check_phantom` (full-mode only, not exercised by the `changed`-mode job this escalation was about) is
  very likely broken the same way — not confirmed live this session, flagging as the same root cause. (2) When a
  hygiene run IS red (confirmed live: `cefi` had a genuine `schema_version_not_v9: count=1`), the auto-escalation path
  tries to `git commit` the filed issue doc from inside the Cloud Run container and fails
  (`fatal: unable to auto-detect email address (got 'root@localhost.(none)')`) — the finding is computed correctly but
  the issue doc is never persisted (lost when the ephemeral container exits), so a real RED finding silently produces
  no lasting record. Neither of these blocks the Cloud Run job from exiting 0 (DP-WATCHER-006's own job-failure signal
  is unaffected), which is why they were invisible to that alert and only surfaced via a manual deep-dive.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [e2e-testing, unified-trading-library, instruments-service, unified-trading-pm]
scope: [engineer]
tags:
  [
    e2e-testing,
    data-pipeline,
    dp-audit,
    divergence,
    dp-divergent-empty,
    cloud-run-jobs,
    escalation,
    git-identity,
    silent-failure,
  ]
related:
  [
    /plans/active/data_pipeline_self_healing_completion_residual_2026_07_24.md,
    /plans/archive/2026_08/issues/dp_daily_digest_oom_32gi_ceiling_and_duckdb_migration_followup_2026_08_15.md,
    /plans/archive/2026_08/issues/dp_reprobe_empty_oom_regression_unbounded_manifest_read_2026_08_09.md,
    e2e-testing/scripts/audit/manifest_hygiene_daily.py,
    e2e-testing/Dockerfile,
    unified-trading-library/Dockerfile,
    unified-trading-library/scripts/detect_manifest_divergence.py,
  ]
created: "2026-08-16"
author: data_pipeline_failure escalation agent (agt-fc531b, slot-3)
parent_epic: infrastructure_master
priority: P1
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: infra
assigned_role:
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
last_updated: "2026-08-17"
locked_since:
context_scope: [e2e-testing/scripts/audit/manifest_hygiene_daily.py, e2e-testing/scripts/audit/_dp_common.py, e2e-testing/Dockerfile, unified-trading-library/Dockerfile, /codex/05-infrastructure/data-pipeline-alerts.md, /plans/active/data_pipeline_self_healing_completion_residual_2026_07_24.md]
source: >-
  Surfaced directly by the data_pipeline_failure escalation agent (agt-fc531b) while diagnosing + verifying the
  DP-WATCHER-006 / DP_CLOUD_RUN_JOB_FAILED OOM fix for uts-prod-dp-manifest-hygiene-changed — not itself a filed
  audit finding (the alert that dispatched agt-fc531b only concerned the OOM; this doc covers two DISTINCT bugs found
  along the way).
---

# dp-audit sibling-repo CLI paths broken in-container + escalation auto-commit has no git identity

## What I found

**(1) `_DIVERGENCE_CLI`/`_PHANTOM_CLI` never resolve inside `e2e-audit:latest`.**

`e2e-testing/scripts/audit/manifest_hygiene_daily.py`:

```python
_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
_PHANTOM_CLI = _WORKSPACE_ROOT / "instruments-service" / "scripts" / "reconcile_phantom_manifest_rows_all.py"
_DIVERGENCE_CLI = _WORKSPACE_ROOT / "unified-trading-library" / "scripts" / "detect_manifest_divergence.py"
_4PILLAR_CLI = _WORKSPACE_ROOT / "e2e-testing" / "scripts" / "validation" / "validate_shards_4pillar.py"
```

`_WORKSPACE_ROOT` resolves to `/app` inside the container (the file lives at
`/app/e2e-testing/scripts/audit/manifest_hygiene_daily.py`, `.parents[3]` = `/app`). This is CORRECT for
`_4PILLAR_CLI` (`e2e-testing`'s own Dockerfile really does `COPY . /app/e2e-testing`), but WRONG for the other two:

- Directly inspected the live `e2e-audit:latest` image filesystem (`docker pull` + `docker run --entrypoint sh -c 'ls
  /app/unified-trading-library'`) — **does not exist**. `unified-trading-library`'s own Dockerfile (`WORKDIR /app` +
  `COPY . .`) lands its repo content directly at `/app/*` (e.g. `/app/scripts/detect_manifest_divergence.py`), since
  the e2e-audit image is built `FROM` the UTL image — there is no `/app/unified-trading-library/` nesting anywhere.
- `instruments-service` is a completely separate repo/service, never copied into this image at all — `_PHANTOM_CLI`
  can never resolve.

Both `_check_divergence` and `_check_missing_expected` have a graceful `if not _CLI.exists(): fc.skipped = "..."`
guard, so this doesn't crash the job — it just silently no-ops. Confirmed via THIS session's own live verification run
(`uts-prod-dp-manifest-hygiene-changed-77k56`, 2026-08-16T18:00-18:06 UTC, all 5 AGs):

```
oracle_expects_but_empty: SKIPPED (divergence_cli_absent)
oracle_expects_no_manifest_row: SKIPPED (divergence_csv_absent)
```

on EVERY asset_group. `_check_phantom` guards the same way (`_PHANTOM_CLI.exists()`) but is `full`-mode only — not
exercised by the `changed`-mode job this escalation covers, so not directly confirmed live this session, but the same
root cause (no `instruments-service` in the image at all) makes it near-certain to be broken identically on the
weekly `uts-prod-dp-manifest-hygiene-full` job.

**(2) The escalation auto-commit has no git identity in the container, so a real RED finding is computed but never
persisted.**

The SAME verification run genuinely found `cefi hygiene: RED` (`schema_version_not_v9: count=1` — a real, correctly-
detected non-v9 row, proof the OOM fix's classification logic works). The hygiene orchestrator tried to file +
commit an escalation issue:

```
2026-08-16 18:05:25,902 INFO escalation issue filed: <container-workspace>/unified-trading-pm/plans . active . issues/manifest_hygiene_red_all_2026_08_16.md (never committed — see below)
Author identity unknown
*** Please tell me who you are.
fatal: unable to auto-detect email address (got 'root@localhost.(none)')
2026-08-16 18:06:03,424 WARNING commit-and-push failed (CalledProcessError); artifacts left in tree: ...
```

The container has no `git config user.name`/`user.email` set anywhere (no `~/.gitconfig`, no per-repo `.git/config`
identity — nothing in `e2e-testing/Dockerfile` or the base UTL Dockerfile sets one). `write_candidate_csv`/
`file_escalation_issue` (`_dp_common.py`) correctly WRITE the issue doc to the local `unified-trading-pm` worktree
inside the container, but the subsequent `git commit` step fails immediately, and since the container is ephemeral
(Cloud Run Job, ends when the process exits), the written-but-uncommitted file is lost with it. I could not find a
`manifest_hygiene_red_all_2026_08_16.md` doc anywhere in my own slot's `unified-trading-pm` checkout — confirming it
never actually landed (this doc does not link it as a real cross-reference — it never existed on any branch).

## Why it matters

- **(1)** is a genuine, silent data-correctness gap: `DP_DIVERGENT_EMPTY` (DP-COVERAGE-class, "oracle expects data but
  manifest shows empty_confirmed") is one of the SSOT-documented failure modes in
  `/codex/05-infrastructure/data-pipeline-alerts.md` — and it has apparently never actually fired from THIS job,
  which is its primary detector. Per CLAUDE.md's data-pipeline-correctness HARD RULE, a detector that has silently
  never run is exactly the class of finding that should not sit un-triaged.
- **(2)** means the hygiene job's own self-healing escalation tier (the `file_issue` half of the emit→route→escalate
  spine) is currently NON-FUNCTIONAL for THIS job specifically — any future genuine RED finding (like today's real
  cefi non-v9 row) computes correctly but is silently dropped before it becomes a tracked, actionable plan/issue doc.
  This is the SAME "computed correctly but never lands" shape the alerting SSOT's own anti-inertness section already
  warns about for a different mechanism (identity-emitted-but-never-registered) — this is identity-computed-but-
  never-committed.

## Recommended decision

**(1)** — two viable directions, needs a decision before implementing (not guessing which the operator/architecture
prefers):

- **A. Fix the image**: have `unified-trading-library`'s own Dockerfile (or the `e2e-audit` Dockerfile as a build
  step) additionally place a copy/symlink of its own repo at `/app/unified-trading-library/`, and vendor
  `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py` (+ its dependency closure) into the image the
  same way `e2e-testing`'s own scripts already are. Preserves the "dispatch to a real sibling-repo CLI as a
  subprocess" architecture as-is.
- **B. Fix the path computation**: make `_DIVERGENCE_CLI`/`_PHANTOM_CLI` environment-aware — resolve to the
  container-actual layout (`/app/scripts/...` for UTL) when running in the container, fall back to the current
  multi-repo-relative computation for local dev. Cheaper (no image/Dockerfile change, no instruments-service
  vendoring) but `_PHANTOM_CLI` has no equivalent "already-in-the-base-image" shortcut since `instruments-service`
  isn't UTL — B only closes the divergence half; phantom would still need option A's vendoring (or a scope decision
  that `_check_phantom` moves to a DIFFERENT runner image that already has instruments-service, e.g. IS's own image).
- [WORKER REC]: **B for `_DIVERGENCE_CLI`** (small, safe, closes the higher-value DP_DIVERGENT_EMPTY gap immediately)
  **+ A for `_PHANTOM_CLI`** only if `_check_phantom`'s weekly `full`-mode OOM/breakage is independently confirmed
  live (not yet done this session — check `uts-prod-dp-manifest-hygiene-full`'s recent execution logs first).

**(2)** — mechanical, low-risk: set a container-local git identity before the commit-and-push step (either bake
`git config --global user.name/user.email` into `e2e-testing/Dockerfile` — matching this workspace's own
`ikennaigboaka [slot-N·host]` convention isn't meaningful for an unattended job, so a distinct bot identity like
`dp-audit-bot <dp-audit-bot@noreply>` is more honest — or set it at runtime in `_dp_common.py`'s commit-and-push
helper immediately before the `git commit` subprocess call). Verify by re-triggering a run with a planted non-v9 row
(mirrors this session's own live discovery) and confirming the issue doc actually lands + is visible via `git log`
in the container's `unified-trading-pm` worktree before the container exits.

## Todos

- [x] ✅ [CODE] P1. Fix `_DIVERGENCE_CLI` path resolution (option B above) so `_check_divergence`/`_check_missing_expected`
      actually run inside `e2e-audit:latest`; verify locally against a real AG's manifest that `DP_DIVERGENT_EMPTY`
      classification actually executes (not just `.exists()` returning True) before shipping. Repo: e2e-testing. —
      e2e-testing@c3da78786d
- [x] ✅ [CODE] P2. Confirm live whether `uts-prod-dp-manifest-hygiene-full` (weekly, `--mode full`) has ALSO been
      silently skipping `_check_phantom` via the same `_PHANTOM_CLI` absence (check its recent execution logs first —
      don't assume); if confirmed, decide + implement option A or a scope change for phantom specifically. Repo:
      e2e-testing / instruments-service / deployment-service (image build). — e2e-testing@4ebd52dc27
- [x] ✅ [CODE] P1. Set a container-local git identity before the escalation issue-doc commit-and-push step in
      `_dp_common.py` (or the Dockerfile), so a genuine RED finding's auto-filed issue doc actually persists instead
      of being silently dropped when the ephemeral Cloud Run container exits. Verify with a planted non-v9 row +
      confirm the issue doc lands on `origin/live-defi-rollout`. Repo: e2e-testing. — e2e-testing@7edd1a3d03
- [x] ✅ [CODE] P3. Once (1) is fixed, re-run `uts-prod-dp-manifest-hygiene-changed` and `-full` and confirm
      `DP_DIVERGENT_EMPTY`/`DP-COVERAGE`-class findings, if any exist in the real manifests, now surface for the
      first time — this may itself uncover a backlog of real, previously-invisible divergence findings worth a
      follow-up triage pass. Repo: e2e-testing. — confirmed live 2026-08-17, see Progress Log + new todos (6)/(7)
      below for two DISTINCT bugs surfaced by this re-run.
- [ ] [CODE] P2. `detect_manifest_divergence.py`'s classification CSV (`divergence_<date>.csv`) is never found on disk
      by `manifest_hygiene_daily.py` inside `e2e-audit:latest` in PRODUCTION (confirmed live 2026-08-17, both
      `-changed` and `-full` runs, all 5 AGs: `divergence CSV ... not found (CLI may have failed or been scoped out)`
      immediately after every `invoking divergence: ...` line) — even though the CLI now RESOLVES + RUNS (todo (1)
      fixed that half) and DOES emit `DIVERGENT_EMPTY` log lines the fallback stdout-counting path in
      `_check_divergence` picks up. Root cause not yet diagnosed (candidates: the CLI writes to a path that doesn't
      match `_divergence_csv_path()`'s `<pm-root>/plans/audit/results/divergence_<date>.csv` computation in-container;
      a silent write failure; a working-directory mismatch). Consequence: EVERY `oracle_expects_but_empty` count
      reported in production (5/5/1/5 across cefi/tradfi/sports/prediction on 2026-08-17) is coming from the
      documented-unreliable stdout-substring fallback ("off by 2-3 orders of magnitude on real corpora" per the
      code's own docstring), NOT the accurate CSV-based classification; `oracle_expects_no_manifest_row`
      (MISSING_EXPECTED) has NO fallback at all and is 100% blind in production (`SKIPPED (divergence_csv_absent)`
      on every AG, every run). Diagnose by invoking `detect_manifest_divergence.py --asset-group cefi` directly
      inside a fresh `e2e-audit:latest` container shell and checking where it actually writes vs.
      `_divergence_csv_path()`'s expectation. Repo: e2e-testing / unified-trading-library.
- [ ] [CODE] P2. The escalation auto-commit collides when `-changed` and `-full` run the same UTC day: both call
      `file_escalation_issue(slug="manifest_hygiene_red", ...)`, which derives the SAME date-based filename
      `manifest_hygiene_red_all_<date>.md` (+ same-named per-AG candidate CSVs) regardless of which job wrote it.
      Confirmed live 2026-08-17: `-changed` (11:39-11:49 UTC) committed + pushed successfully
      (`unified-trading-pm@ceff608`); `-full` (11:39-12:45 UTC, ran concurrently) computed its OWN correct findings
      (including full-mode-only `phantom_captured_no_parquet`/`shard_4pillar_fail` counts never captured by the
      changed run) then hit an `add/add` rebase conflict on the identical filenames when it tried to commit ~1h
      later, logged `WARNING commit-and-push failed (CalledProcessError)`, and exited 0 — so the full-mode-only
      findings (cefi/tradfi/sports phantom=1 + shard_4pillar=1 each) were silently dropped, the exact
      "computed correctly but never persisted" failure class todo (3)/(4) above already fixed for the git-identity
      case, now recurring via a git-conflict path instead. Fix: make `file_escalation_issue`'s slug/filename
      mode-aware (e.g. append `--mode` to the slug: `manifest_hygiene_red_changed_<date>.md` /
      `manifest_hygiene_red_full_<date>.md`) so same-day changed+full runs never collide. Repo: e2e-testing
      (`scripts/audit/_dp_common.py` / `manifest_hygiene_daily.py`'s `run()` → `file_escalation_issue` call).
- [x] ✅ [CODE] P2. `_dp_common.py`'s `file_escalation_issue` template has drifted from the current
      `doc-frontmatter-schema.md` — a fresh escalation doc it wrote on 2026-08-16 (RED cefi finding, first real
      escalation since (1) above shipped) was missing `doc_type`/`summary`/`status`/`nature`/`asset_group`/`stage`/
      `repos`/`scope`/`tags`/`related`/`priority`/`resolved_by`, all present in older archived instances (e.g.
      `plans/archive/issues/manifest_hygiene_red_2026_07_14.md`) — so every auto-commit of a genuine RED finding has
      been failing `plan-hygiene`'s frontmatter-schema check (compounding, not caused by, the git-identity issue in
      (3) above). Hand-fixed the one instance in `unified-trading-pm@1c8ceabfb8`; the generator itself is still stale.
      Repo: e2e-testing (`scripts/audit/_dp_common.py`). — e2e-testing@c05ec220ec

## Progress Log

- **2026-08-16 (ui_developer worker, slot-5)**: Shipped todo (3) — `e2e-testing@7edd1a3d03`. Added a
  best-effort identity check immediately before the `git commit` step in
  `_commit_and_push_pm_artifacts` (`scripts/audit/_dp_common.py`): `git config --get user.email` probes
  whether ANY identity resolves (local/global/system); only when it does NOT does the code set a distinct
  `dp-audit-bot <dp-audit-bot@noreply>` identity via `git config user.name`/`user.email` (repo-local, not
  `--global`), so a real local worker/operator PM clone's own per-slot commit identity
  (`ikennaigboaka [slot-N·host]`) is never overwritten. Verification: could not re-trigger a live Cloud Run
  run with a planted non-v9 row from this slot (no container access), so verified via unit tests instead —
  updated `test_commit_and_push_invokes_git_when_dot_git_present` (identity already present → only the probe
  fires, never a bot-identity set, proving local dev is unaffected) and added
  `test_commit_and_push_sets_bot_identity_when_missing` (identity absent → `config user.name`/`user.email`
  fire with the `dp-audit-bot` values BEFORE `add`/`commit`, reproducing the exact fix for the live
  `unable to auto-detect email address (got 'root@localhost.(none)')` failure this doc documents). Full
  `bash scripts/quality-gates.sh` green on the committed SHA (sentinel verified == HEAD) before shipping via
  quickmerge. Did NOT re-verify a live Cloud Run job — that's still open follow-up if the operator wants
  in-container confirmation; the unit coverage is the practical verification available from a worker slot.

- **2026-08-16 (backend_engineer worker, slot-12)**: Shipped todo (1). Re-implemented the environment-aware
  `_DIVERGENCE_CLI` fallback (local-dev sibling path, then container-flat `_WORKSPACE_ROOT/scripts/...` fallback) in
  `e2e-testing@c3da78786d`. Verified LOCALLY, twice, against real production `cefi` data (not `.exists()` alone):
  (a) direct `detect_manifest_divergence.py --asset-group cefi` invocation wrote a real
  `divergence_2026-08-16.csv` (341,215 cells: 58,319 `DIVERGENT_EMPTY`, 58,890 `MISSING_EXPECTED`); (b) the actual
  `manifest_hygiene_daily.py --asset-group cefi --mode changed` wrapper (the real fix target) then reproduced the
  identical counts via `_check_divergence`/`_check_missing_expected` (`oracle_expects_but_empty: count=58319`,
  `oracle_expects_no_manifest_row: count=58890`) — proving the classification genuinely executes, not just that the
  CLI path resolves. Both runs required `run-bounded-analysis.sh --mem-cap` well above the 6-8G tried first (30M-row
  `cefi` manifest read+merge needs ~14-16G here); an unbounded/under-capped run SIGTERMs (`exit 143`) right after the
  manifest load, before classification — worth knowing for whoever re-runs this at scale. This verification run's own
  RED cefi finding auto-filed for real (`manifest_hygiene_red_cefi_2026_08_16.md` + candidate CSV) — landed via
  `unified-trading-pm@1c8ceabfb8` after hand-fixing its frontmatter (see new P2 todo above) and a dangling referrer
  link in `cefi_consolidated_closeout_aggregated_sources_2026_07_24.md` left by an unrelated prior archival. Did NOT
  touch (2)/(3)/(4) — out of scope for this dispatch.

- **2026-08-16 (data_pipeline_failure escalation agent, agt-fc531b, slot-3)**: Filed while wrapping up the
  DP-WATCHER-006 OOM escalation for `uts-prod-dp-manifest-hygiene-changed` (see that escalation's own shipped commits
  `e2e-testing@ed59dbe` + `e2e-testing@a1ce2af` for the actual OOM fix, unrelated to this doc). Confirmed (1) via
  direct `docker pull` + filesystem inspection of the live `e2e-audit:latest` image, cross-checked against the
  `SKIPPED (divergence_cli_absent)` log lines from a live re-execution (`uts-prod-dp-manifest-hygiene-changed-77k56`,
  2026-08-16T18:00-18:06Z, all 5 AGs). Confirmed (2) from the SAME execution's own logs (`cefi` genuinely RED,
  auto-commit failed on missing git identity). Not fixed inline — both are genuinely separate root causes from the
  OOM this escalation was dispatched for, and (1) in particular has a real design decision (A vs B above) that
  shouldn't be guessed by a one-shot alert-triage worker. Filed as `[CODE] P1/P1/P2/P3` todos rather than left as
  prose per the workspace's own findings-triage HARD RULE.

- **2026-08-17 (backend_engineer worker, slot-8)**: Shipped todo (2) — `e2e-testing@4ebd52dc27`. Confirmed live
  first: checked `uts-prod-dp-manifest-hygiene-full`'s MOST RECENT execution
  (`uts-prod-dp-manifest-hygiene-full-dmsxx`, 2026-08-16T20:10-20:22Z, all 5 AGs — itself already AFTER todo (1)'s
  `_DIVERGENCE_CLI` fix landed) via `gcloud logging read` — `phantom_captured_no_parquet: SKIPPED
  (phantom_cli_absent)` fired on every asset_group, confirming (2) exactly as suspected. (Side note, not this todo's
  scope but worth flagging: that SAME execution ALSO still showed `oracle_expects_but_empty: SKIPPED
  (divergence_cli_absent)` for every AG — the deployed image at that point still predated `e2e-testing@c3da78786d`;
  resolved incidentally by this todo's own image rebuild below, see verification.)
  Implemented option A (vendor), not a scope change: audited `reconcile_phantom_manifest_rows_all.py`'s full 1991-line
  import surface and found ZERO instruments-service-internal imports — only `unified_api_contracts` /
  `unified_trading_library` / pandas / stdlib, all already present in the `e2e-audit:latest` base image — so the
  "dependency closure" the issue doc's option-A framing warned about turns out to be empty; only the one file needs
  vendoring. Added a `stage-workspace-deps` step to `cloudbuild-e2e-audit.yaml` (mirrors
  `market-tick-data-service/cloudbuild.yaml`'s own existing sibling-repo-staging pattern — shallow `git clone` of
  instruments-service into `.deps/`, same GH_PAT-from-Secret-Manager auth) + a guarded `RUN` hoist step in the
  Dockerfile that copies the one script to `/app/instruments-service/scripts/...` — the SAME
  `<root>/instruments-service/scripts/<file>` shape local multi-repo dev already has, so `_PHANTOM_CLI`'s EXISTING
  path computation resolves with no code change (unlike `_DIVERGENCE_CLI`'s env-aware-fallback fix, no new path logic
  was needed here at all). Verified in two stages, not `.exists()` alone: (a) LOCALLY — built the image with a
  locally-staged `.deps/instruments-service` copy, confirmed `_PHANTOM_CLI.exists() == True` +
  `_DIVERGENCE_CLI.exists() == True`, ran `manifest_hygiene_daily.py --mode full --smoke` clean, and invoked the
  vendored CLI's `--help` directly inside the container (exercises every import — pandas/UAC/UTL — with no GCS
  network/creds needed) to prove the subprocess mechanism genuinely works, not just that the file is present; (b)
  PRODUCTION — submitted the real `cloudbuild-e2e-audit.yaml` build (`gcloud builds submit`,
  `Evidence: cloudbuild=8575b934-bdab-4e66-a6a8-56e8c2bb45c9` resolves `SUCCESS` — its own smoke step, which runs all
  4 audit scripts' `--smoke` including `--mode full`, gates the push), then `docker pull`ed the FRESHLY-PUSHED
  `e2e-audit:latest` (digest `sha256:1aa54070c643d0696fdbd6c0b3000e82d0a57fb75c70745a27d175829c3ab9f3`) and confirmed
  BOTH `/app/instruments-service/scripts/reconcile_phantom_manifest_rows_all.py` AND
  `/app/scripts/detect_manifest_divergence.py` are present on the real image now live in Artifact Registry — so both
  (1) and (2)'s fixes are confirmed LIVE, not just committed, closing the exact "code fixed but image never rebuilt"
  gap this doc's own history already hit twice (the stale-`ARG`/stale-build incidents on
  `uts-prod-dp-manifest-hygiene-changed`). Did NOT re-trigger a live `uts-prod-dp-manifest-hygiene-full` Cloud Run
  execution against real production data (that's todo (4)/P3's scope, gated on this fix landing) — next Sunday
  08:00 UTC run (or an operator-triggered `gcloud run jobs execute`) will be the first real confirmation that
  `_check_phantom` actually classifies against production manifests, not just that the CLI resolves.
**context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)

- **2026-08-17 (data_engineering worker, slot-24)**: Shipped todo (5) — `e2e-testing@c05ec220ec`. Read
  `doc-frontmatter-schema.md` + `docspec.py`'s `PER_TYPE["issue"]` (ground truth: universal core
  doc_type/title/summary/status/nature/asset_group/stage/repos/scope/tags/related/created + issue-type
  parent_epic/priority/source required, assigned_vm/resolved_by/locked_by optional-present,
  context_scope/author elective) and rewrote `file_escalation_issue`'s frontmatter block in `_dp_common.py`
  to emit every previously-missing field: `doc_type: issue`, a `summary` auto-derived from `what_i_found`
  (whitespace-collapsed, truncated to 200 chars + `...`), `status: open` (a freshly-filed issue's correct
  initial state — `resolved_by` present-but-empty alongside it, since docspec's `Req.C` only requires
  `resolved_by` once `status: resolved`), `nature: process` (matching both real historical instances —
  `manifest_hygiene_red_2026_07_14.md` archived + the `2026_08_16` hand-fix — over the SSOT prose's
  literal "issue" suggestion, since both are valid NATURE enum values and precedent-matching seemed the
  safer restoration target), `asset_group` from the existing `asset_groups` param (falls back to the
  `cross-cutting` enum value when a caller passes none, e.g. a non-AG-partitioned escalation), `stage:
  [meta]`, `repos: [{target_repo}]` (already an existing param), `scope: [engineer, admin]`, `tags`
  (data-pipeline/daily-audit/slug-derived — non-empty, since an empty `tags:` list is NOT in docspec's
  `_valid_empty` sanctioned set the way `repos`/`related` are, so it would SOFT-fail), and `related: []`.
  Also switched `title`/`summary` YAML embedding from raw f-string interpolation to `json.dumps(...)`
  (JSON-string escaping is a valid subset of YAML double-quoted-scalar escaping) — the pre-existing
  `title: "{title}"` pattern would have corrupted the frontmatter block on any title containing a literal
  `"`, a latent bug in the exact code path this fix already touches. Verified against the real validator
  contract: added `test_file_escalation_issue_frontmatter_matches_schema` (parses the generated frontmatter
  with `yaml.safe_load` and asserts every field docspec requires is present + correctly valued, including
  the `>200`-char summary-truncation path and the `resolved_by: null` present-but-empty case) and
  `test_file_escalation_issue_asset_group_defaults_to_cross_cutting` (the `asset_groups=()` fallback).
  Confirmed all 3 real callers (`manifest_hygiene_daily.py`, `drilldown_reconciliation_guard.py`,
  `reprobe_new_empty_confirmed.py`) always pass `asset_groups=` and rely on the `target_repo` default
  (`market-tick-data-service`) or a caller-specific override — neither behavior changed by this fix. Full
  `bash scripts/quality-gates.sh` green on the committed SHA (sentinel re-verified == HEAD after the
  commit-then-QG ordering fix) before shipping via quickmerge; post-push ancestry verified
  (`e2e-testing@c05ec220e` is an ancestor of `origin/live-defi-rollout`). Did NOT re-trigger a live Cloud
  Run hygiene run to observe a real auto-filed doc pass plan-hygiene's `check_frontmatter_schema.py` gate
  end-to-end in production — that's the next `uts-prod-dp-manifest-hygiene-*` execution's own confirmation,
  not reproducible from a worker slot without container access (same limitation the slot-5 git-identity fix
  for todo (3) already noted). Remaining open todo (4)/P3 (re-run + confirm `DP_DIVERGENT_EMPTY` findings
  now surface for real) is unaffected by this fix and still open.

- **2026-08-17 (infra worker, slot-25)**: Shipped todo (4)/P3 — no code, live re-run + confirmation.
  Triggered both `uts-prod-dp-manifest-hygiene-changed` (execution `r6bcv`, 11:39-11:49 UTC) and
  `uts-prod-dp-manifest-hygiene-full` (execution `7pbdm`, 11:39-12:45 UTC — the GCS-walking phantom+4pillar
  checks took ~65min) via `gcloud run jobs execute --region=asia-northeast1`, then read both executions'
  logs via `gcloud logging read`. **Confirmed the core ask**: `oracle_expects_but_empty` (`DP_DIVERGENT_EMPTY`)
  now surfaces real, non-zero counts for the first time — cefi=5, tradfi=5, sports=1, prediction=5, defi=0
  (both runs agree) — a previously-invisible backlog exactly as anticipated, now flowing through the existing
  escalation path (the `-changed` run's finding auto-filed + committed successfully as
  `manifest_hygiene_red_all_2026_08_17.md` → `unified-trading-pm@ceff608`, already triaged/frontmatter-fixed
  by other agents per this file's own git history). **But surfaced two DISTINCT new bugs while confirming**,
  filed as new todos above rather than left as prose (findings-triage HARD RULE): (a) the divergence CLI's
  classification CSV is never actually found on disk in-container in EITHER run/mode (`divergence CSV ...
  not found` immediately after every `invoking divergence:` log line, all 5 AGs, both executions) — so every
  reported `oracle_expects_but_empty` count is coming from the documented-unreliable stdout-substring
  fallback, not the accurate CSV path, and `oracle_expects_no_manifest_row` (MISSING_EXPECTED) is 100% blind
  in production (no fallback exists for it); (b) the `-full` run's OWN escalation commit (its full-mode-only
  phantom/4-pillar findings, computed correctly ~1h after `-changed` had already committed) hit an `add/add`
  git conflict on the identical same-day filename `-changed` had already landed, failed to commit, and was
  silently dropped — recurrence of the exact "computed but never persisted" class todo (3) fixed for the
  git-identity case, now via a filename-collision path instead. Did not fix either — both need a real code
  change in `e2e-testing`, out of a re-run-and-confirm task's own scope; see the two new todos above for the
  concrete fix directions. Fresh-pulled the PM worktree (`git fetch` + `ff-only`) before this edit; no code
  shipped this task (pure plan-flip + Progress Log, PM repo only).
