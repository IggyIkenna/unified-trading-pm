---
doc_type: plan
title: Artifact pipeline observability — Shipped History part 2 (forked from the artifact pipeline observability plan)
summary:
  Archive-bound Progress Log + Lessons history extracted verbatim from artifact_pipeline_observability_2026_07_17.md's
  2026-07-27 line-cap remediation. Covers the 2026-07-23 dated Progress Log entries (Deploy timeline vertical, the help
  dialog, the remaining three views + per-column sort/filter, the two layout passes) plus the full "Lessons this
  session" section (push-verification-by-content, stat-tile computation, the RepeatedComposite proto gotcha, the
  collision-check discipline, and others). Every item in this file is already pure narrative describing already-shipped
  work — zero open todos. Record-only; not intended for further action.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui, deployment-api, unified-trading-pm]
scope: [engineer, admin]
tags:
  [deployment-observability, artifact-pipeline, image-builds, tarballs, cloud-build, history, plan-split, archive-bound]
related:
  [
    /plans/active/artifact_pipeline_observability_2026_07_17.md,
    /plans/archive/artifact_pipeline_observability_history_2026_07_24.md,
  ]
created: "2026-07-27"
last_updated: "2026-07-27"
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: docs_reconciler
drift_direction: advance-code
supersedes:
superseded_by:
depends_on:
source:
  [
    "Forked 2026-07-27 from artifact_pipeline_observability_2026_07_17.md's Progress Log + Lessons sections during the
    line-cap trim (parent was 981 lines against the 1000-line cap, with more Phase 3b/3c/3d completion notes still to
    add).",
  ]
locked_by:
locked_since:
---

> **🟢 2026-07-27 history extraction** — this file holds Progress Log + Lessons content moved VERBATIM out of
> `artifact_pipeline_observability_2026_07_17.md` (the 2026-07-23 dated entries + the entire "Lessons this session"
> section) to bring that plan back under its 1000-line cap. Every line below already existed in the parent unchanged —
> no content was altered, only relocated. All items here are shipped/narrative; there are no open todos in this file.
> See the parent plan (or `artifact_pipeline_observability_history_2026_07_24.md` for the earlier 2026-07-17→07-21
> narrative) for current status and the still-open items.

# Artifact pipeline observability — Shipped History part 2

## Progress log (2026-07-23 entries)

- **2026-07-23 — Deploy timeline vertical (2nd view) shipped end-to-end, plus a live production bugfix caught building
  it.** Operator: "continue with the remaining pages … work in worktrees tabs 2" (confirmed the per-slot clone model IS
  the workspace's "worktree" isolation — no separate mechanism). Synced all 3 repos first; discovered a DIFFERENT
  operator (`harshkantariya`, host `harsh_pc`) is independently working this same plan on their own slot-2 clone —
  `deployment-api@0a920c2` (a 30s RPC-deadline fix for the exact "keeps loading" hang the operator had just reported)
  and `deployment-ui@038038e` (the frontend counterpart: a 45s `AbortController` timeout on `getArtifactBuilds`) both
  landed mid-session. Neither touched the Deploys view — confirmed via full history grep before starting, no collision.
  - **Backend — `deployment-api@72a0108`.** `gcp_cloud_run_revisions()` provider: reuses `list_cloud_run_services()` (no
    extra RPC) to enumerate workloads + resolve the live revision, lists each service's revisions (`RevisionsClient`,
    same `_gcp_sdk` boundary), classifies each into new/config/rollback/failed by walking the digest sequence
    chronologically, and computes "held for" via ONE-STEP-LOOKAHEAD to the revision that replaced it.
    `service.deploys()` mirrors `builds()`'s window/stats shape, with one deliberate exception: `live_now` is a
    POINT-IN-TIME count over ALL facts, never the windowed subset — a narrow date range must not undercount what's
    actually serving. `GET /api/artifacts/deploys` + 12 new `--block-network` tests (21 total). MEASURED live: 690
    revisions / 16 services, ~9-11s cold scan (comparable to builds' ~5s, same 300s cache).
  - **Live bug found + fixed in the SAME file (findings-triage: same-file → same commit).** Google-cloud repeated fields
    (`Build.steps`, `Build.images`, `Revision.containers`, `Revision.conditions`) are runtime instances of
    `proto.marshal.collections.repeated.Repeated`/`RepeatedComposite` — NOT `list`/`tuple` — so the
    `isinstance(x, (list, tuple))` gate used throughout `providers.py` silently dropped every real field. The
    ALREADY-SHIPPED Pipeline view's step-timeline drawer and "Produced" column have been silently empty for every real
    build since `8eda1f8`. Root-caused via static introspection (no live RPC needed — built a synthetic proto message,
    no network flakiness in the way) before confirming live. Fixed with one shared `_as_item_list()` helper (any
    iterable, not just list/tuple); verified against live Cloud Build + Cloud Run data both before and after. Also
    found + fixed a `held_for` sign-error (subtraction direction backwards, always computed negative → always empty) via
    the SAME live-verification pass — caught because the numbers looked wrong, not because a test failed.
  - **A genuine finding, not a bug: `deployment-service` has ZERO working Cloud Run revisions, ever.** Its one-ever
    revision's `Ready` condition is `CONDITION_FAILED` ("container failed to start and listen on PORT=8080"); since it
    never went ready, `list_cloud_run_services()`'s `latest_created_revision` fallback still reports it as the service's
    newest state — so the page correctly shows `live=true, change_type=failed` for it. Left as-is (verified via the real
    condition message, not assumed) — exactly the kind of defect this page exists to surface.
  - **UI — `deployment-ui@797180c`.** `DeployTimelineView` mirrors `PipelineView`'s shape (data-derived stat band,
    filter chips, flat table — no drawer, `DeployRow` has no nested detail to expand); `DEPLOY_FILTERS` (all / code /
    live / fail) match the frozen mock's semantics exactly, filtered CLIENT-SIDE like Pipeline (one full-window fetch,
    no round-trip per filter click). Both live views now fetch eagerly + concurrently on mount/window-change, each with
    its own request-id guard (mirrors `CostObservability`'s `loadCore` pattern). **Operator ask, same turn:** default
    window 7d (was 14d) + a real date-range picker on BOTH live views — ported `CostObservability`'s `DateRangePicker`
    verbatim (native `<input type="date">`, `min`/`max` wired to the API's 366-day cap, a hand-picked range deselects
    the day-preset pills and vice versa). Factored the peer's ad hoc 45s abort-timeout into a shared
    `fetchArtifactApi()` helper reused by the new `getArtifactDeploys` (same hang protection, one implementation, not
    two copies to drift). 9 Vitest + 4 `pw:L2` tests; full deployment-ui gate green (101 tests). **Remaining UI:** the 3
    placeholder tabs' real views (running / artifacts / health), each gated on its per-view backend.
- **2026-07-23 (later) — a help/tooltip dialog shipped for the page** (operator ask, out-of-plan-scope but small):
  `deployment-ui@cdcd3df` — a `HelpCircle` button opening a `CostHelpDialog`-style dialog explaining the page's controls
  and, at the time, the two live tabs' columns. Superseded by the later help-dialog update below once all five tabs
  shipped.
- **2026-07-23 (later still) — the remaining three views (Artifacts, What's running, Health) all shipped in one session,
  plus per-column sort/filter/multi-select across all five tables** (operator: "continue with the remaining 3 pages"
  then "make sure they also have these sort and filter and select capabilities").
  - **Backend — `deployment-api@a13c667`.** Added `RegistryImageFact` (a new per-image internal fact type, distinct from
    the existing per-repo `ImageFact` roll-up) and `gcp_artifact_registry_images()`: one `list_docker_images` RPC over
    the single canonical `unified-trading-system` AR repository returns every service's every pushed image in one shot
    (MEASURED live: 3365 images across 20 repos, ~4s cold with `page_size=1000`) — no per-service repo enumeration
    needed, and no scan cap was actually load-bearing (5000 is a generous runaway-safety net). `service.images()`
    aggregates that list per `(cloud, registry, repo)` into the `ImageRow` roll-up (tags of the newest image, summed
    size, a `running_on` cross-ref against live Deploy-timeline digests, and a `state` derived from
    running/age-since-last-push — `STATE_LEGACY` at >30 days idle with nothing running it). `service.running()` is the
    plan's headline runtime join: joins each live `DeployFact`'s digest against the AR image list (digest→image), picks
    a SHA-shaped tag off the matched image (→ the git commit), and joins that `(repo, sha)` to the already-cached
    `BuildFact` list for the trigger/branch. `service.health()` makes ZERO new cloud calls — every condition is derived
    from the builds/deploys/images/running facts the other three view-methods already fetched (AWS-deferred is always
    emitted; live-but-never-ready deploys → high; recent build failures / dup builds → med/low; floating-tag or
    hand-deployed live workloads → med; the VM-tarball-lane gap → med, always; AR registry sprawl ≥500 images/repo →
    low). 12 new `--block-network` unit tests (33 total); full deployment-api gate green.
  - **A real design choice, not a bug: `DRIFT_PINNED` never fires — everything traceable reads `DRIFT_OK`.** Cloud Run's
    API exposes only the RESOLVED digest on a revision, never the tag the operator originally deployed with — so a
    genuine `@sha256`-pin deploy and a `:<sha>`-tag deploy that happens to still resolve to the same digest are
    OBSERVATIONALLY IDENTICAL from this join. Claiming the stronger `pinned` verdict would be a fabricated precision
    this data can't support, so both collapse to the one honest `ok` ("traceable to a commit, however it got there").
    Recorded here so a future session doesn't "fix" `DRIFT_PINNED` into firing without re-deriving why it doesn't.
  - **A ruff gotcha, workspace-relevant beyond this file: `# noqa: <fake-code>` is a soft warning,
    `# noqa: <real-but- disabled-code>` is a hard RUF100 error.** The existing `# noqa: cloud-sdk-direct` convention
    (`routes/builds.py`) uses a made-up string as the noqa "code" — ruff can't parse it as a real code, so it degrades
    to a non-blocking "invalid noqa directive" WARNING and the diagnostic underneath (the `TID251` banned-import) stays
    genuinely unsuppressed. That's fine for the LINT step (which doesn't select TID251) but means the STEP-5.95 ratchet
    script (which runs an ISOLATED `ruff --select TID251` pass) counts it as a real, uncounted-by-noqa violation — so a
    new `from google.cloud import ...` site with only that fake-code comment silently pushes the ratchet's ONE global
    ceiling past baseline, even though it "looked" suppressed. The fix already exists in this codebase
    (`_ci_status_firestore_store.py`): use the REAL code, `# noqa: TID251`, which the ratchet's isolated pass properly
    honors — but that then makes the PLAIN `ruff check` (LINT step, which never selects TID251) flag the noqa itself as
    unused (`RUF100`, since TID251 isn't in the selected set there), which IS a hard blocking error under this repo's
    default `select = [...]` (RUF is in it). Resolved via `pyproject.toml`'s existing escape hatch: a
    `[tool.ruff.lint.per-file-ignores]` entry silencing `RUF100` for the one file — added
    `"deployment_api/services/artifact_pipeline/providers.py" = ["RUF100"]` alongside the pre-existing
    `_ci_status_firestore_store.py` entry. Two separate ruff invocations, two different rule sets, same line — always
    check both when adding a new `# noqa: TID251` site.
  - **UI — `deployment-ui@3210bb5`.** `ArtifactsView`/`RunningView`/`HealthView` replace the three `ComingSoon`
    placeholders, matching Pipeline/Deploy timeline's established shape (data-derived stat tiles, filter-pill bar,
    client-side table). `RunningView` flattens `RunningGroup.versions` to one row per live version (today always length
    1 per service — Cloud Run traffic-split isn't detected by this join, so `fragmented` reads 0 fleet-wide; the shape
    supports a future multi-version row without a contract change) and reuses the Pipeline drawer pattern (click a row
    to expand the full `why` + host list). `images`/`running`/`health` are NOT windowed by date — they load once on
    mount and only refetch on an explicit Refresh, unlike Pipeline/Deploy timeline's window-driven fetch.
  - **The same-turn operator ask — per-column sort + filter + multi-select — landed in two ships, not duplicated
    logic.** `@3126b1b` built the shared primitives (`ColumnHeader`, `MultiSelectFilter`, `TextFilterInput`,
    `toggleColumnSort`/`compareSortValues`) for Pipeline + Deploy timeline; `@3210bb5` reused them verbatim for the
    three new views, adding only each view's own column-key `switch` (`imageSortValue`/`runningSortValue`/
    `healthSortValue`) and column-filter shape. Every table's identity column (Repo / Workload / Service / Area) is
    explicitly multi-select per the operator's ask; other bounded columns (Cloud, State, Change, Drift, Severity) got
    the same multi-select for consistency rather than a narrower text box.
  - Coverage: 19 Vitest (page total) + 10 `pw:L2` (spec total); full deployment-ui gate green (1097 tests workspace-
    wide). Both live dev servers (tmux-hosted, `:5183` UI / `:8004` API) picked up every change via Vite HMR — verified
    healthy post-ship, no restart needed.
- **2026-07-23 (later) — two operator-driven layout passes over the page header/toolbar, both shipped same day.** (1)
  `deployment-ui@ed49dbe` — dropped the page's icon+title+subtitle header block and the standalone GCP-active/
  AWS-parked banner; both pieces of copy now live only in the help dialog (a new "GCP / AWS" `HelpTerm` carries the
  banner's full text verbatim). The tab bar moved up to occupy the header's old position (left side), with the window
  presets / date-range picker / refresh / help button unchanged on the right — one row instead of three stacked blocks
  (header, banner, tabs). (2) `deployment-ui@de8271a` — restructured every view's stat-tile-grid + filter-pill-bar
  (previously two full-width blocks stacked, stats on top) into one row via a new shared `ViewToolbar` component: filter
  pills left (bigger — `px-2.5 py-1 text-xs` → `px-3 py-1.5 text-[13px]`), stat tiles right (smaller — `StatTile`'s
  `text-2xl`/`p-3` → `text-lg`/`px-2.5 py-1.5`, wrapped in `flex flex-wrap` instead of a `grid` so they cluster instead
  of stretching full-width), and the pill row's explanation text moved from beside the pills to its own line below them.
  Applied identically to all 5 views via the one shared component — a single edit point instead of 5 independent ones,
  so the layout can't drift between tabs. Visually verified via Playwright screenshots (Pipeline + What's running)
  before shipping, not just eyeballed in code. No test asserted on visual layout/DOM order, so both ships were zero-risk
  to the existing 19 Vitest + 10 `pw:L2` suite (all still pass unchanged) — a reminder that a pure-layout change needs a
  screenshot check precisely because the test suite can't catch it.

## Lessons this session (2026-07-17 through 2026-07-23, so they are not re-learned the hard way)

- **Verify a push landed by CONTENT on origin, not by a push exit code or an is-ancestor check.** A retry loop reported
  "landed" falsely: `git pull --rebase --autostash` popped a _staged_ edit back as _unstaged_, the loop's conditional
  `git commit` then had nothing staged, and the `merge-base --is-ancestor HEAD origin` check passed anyway (HEAD was the
  pulled tip). Fix: after an autostash pop, **re-stage by name before committing**, and gate success on
  `git show origin/<branch>:<file> | grep <expected-content>`. Every ship in this session's later half uses that
  content-gated loop.
- **Compute UI stat tiles from the data; never hand-write them.** A consistency check caught the running-tab tiles
  (claimed 3 fragmented / 11 floating / 3 hand) disagreeing with the rendered rows (real: 4 / 19 / 2), and caught a row
  silently dropped in a rebuild. The real page must derive these server-side.
- **Do not fabricate data to fill a cell.** GCP `gcloud` auth expired mid-session (measured: "Reauthentication failed …
  cannot prompt"); AWS still worked. Two image build-dates I could not re-pull render `n/a — re-auth` rather than a
  made-up date. A `gcloud auth login` on the operator side refills them; the real backend holds live creds so this is a
  mock-only gap.
- **Three earlier claims I made were wrong and are corrected above** — do not let the stale versions survive: memory
  ceiling is **16 GiB** not 4 (I quoted a stale plan decision over the deployed `cloudbuild.yaml`); the AWS tarball
  uploader/setup-script **agree** on the bucket (the breakage is an empty prefix + a different nonexistent bucket); and
  the `0.99.0` `dep_versions` value is an **honest** constant (`SETUPTOOLS_SCM_PRETEND_VERSION`), not the BoM lying.
- **The tarball-audit agent's completion record was lost across a compaction** — its findings had already been folded
  into the plan, but I re-verified every load-bearing Lane-B claim with a fresh live probe rather than trusting them.
  Treat any pre-compaction agent finding as unverified until re-probed.
- **An audit finding decays — re-verify against CURRENT code before filing or acting, especially in a hot area
  (2026-07-21).** The 2026-07-17 pipeline-bug list was ~4 days old and the CI area is the workspace's hottest (Ikenna
  pushed to PM 9 min before I checked; `setup-data-pipeline-vm.sh` 7h, `freeze-deferred-build-replay.yml` 24h). On
  re-check: **#5 was already FIXED 2026-07-20**, **#2 was not-a-bug** (never reproduced), **#6 had partially landed**
  (SHA now measured at boot). Had I filed the list as-was, ~half would have been stale/duplicate. The discipline that
  caught it: grep the 444 issue docs for existing coverage → **READ** the candidates (not grep-then-conclude) → verify
  each bug against the live file + a live probe (the AWS bucket 404, the `deferred-aws-build-` vs `deferred-build-`
  filter) → file only what survives, and record the "verified NOT open" set so nobody re-investigates.
- **"Parked" ≠ "broken" — do not frame an intentional-off state as a defect (operator 2026-07-21).** I first rendered
  the AWS App Runner PAUSED / ECR-idle states as high-severity red defects ("orphaned · GC"). They are **deliberate**:
  AWS is deferred (no credits), GCP is the sole active production path. Fixing code is free; only creating/deploying AWS
  images costs credits — so AWS-side code bugs are _deferred-with-AWS_, not urgent, and the parked estate is _kept_, not
  a GC candidate. When a resource is off, establish WHY (intentional vs failure) before labelling it.
- **Editing a teammate's actively-hot files is a collision risk, not just a cost question.** When the operator green-lit
  fixing the bugs, the real blocker surfaced as collision (Ikenna is live in every file these bugs live in), not cost.
  Surfaced it and parked the fixes in the issue doc with "loop Ikenna in first" rather than barging into fleet-critical
  CI/boot files. Recurring: the multi-agent-safety "never edit recently-pushed files" rule is about blast radius.
- **A new `deployment_api.services.*` submodule is INVISIBLE to the unit suite until registered in
  `tests/unit/conftest.py` (2026-07-21).** That conftest replaces `deployment_api.services` with a stub package whose
  `__path__ = []`, then hand-injects a curated list of real submodules into `sys.modules` (`cost_observability` is one).
  A new service dotted-imports fine under plain `python` and passes basedpyright, but pytest collection dies with
  `ModuleNotFoundError: No module named 'deployment_api.services.<new>'` — and because `main.py` imports the new route,
  it CASCADES to break every test that imports the app. Fix: register the new service exactly like `cost_observability`
  (pre-import + `sys.modules["deployment_api.services.<new>"] = real_<svc>`). Plain-import / basedpyright / ruff all
  hide it because only pytest loads that conftest — only the FULL gate catches it. Cost one gate cycle; now fixed once
  for the whole `artifact_pipeline` package (the remaining 4 views won't re-hit it).
- **`isinstance(x, (list, tuple))` is the WRONG check for any google-cloud protobuf repeated field — workspace-wide, not
  just here (2026-07-23).** Repeated fields (`Build.steps`, `Build.images`, `Revision.containers`,
  `Revision.conditions`, and presumably more across the codebase) are `proto.marshal.collections.repeated.Repeated` /
  `RepeatedComposite` at runtime — neither is a `list` or `tuple` subclass, so that isinstance gate silently returns
  "empty" for real data while a hand-built test double using a plain list sails through every unit test. This shipped
  silently in `8eda1f8` and was only caught because a NEW call site (`Revision.containers`) hit the identical pattern
  and produced an empty digest that looked wrong on inspection — the ORIGINAL bug (`Build.steps`/`images`) would still
  be unnoticed today without that coincidence. Grep `isinstance(.*\(list, tuple\))` against any file that reads a
  `google.cloud.*` proto response before trusting its "empty" case. Fix pattern: normalize via
  `list(cast("Iterable[object]", value))` in a try/except TypeError, not an isinstance gate.
- **Static introspection beats a live RPC for a data-shape question, and sidesteps live-service flakiness.** Diagnosing
  the `RepeatedComposite` bug needed to know a proto field's RUNTIME type, not its live VALUE — a synthetic
  `cb.Build()` + `.steps.append(...)` answered it with zero network calls, in the same window where live Cloud Build
  RPCs were intermittently hanging (a transient, unexplained blip — ADC/network were independently confirmed healthy).
  When the question is "what type is this," construct the object; don't fight a flaky network for it.
- **A collision check is grep-before-build, not grep-after-symptom.** Before starting the Deploys vertical, checked
  `git log --oneline --all --grep=deploy -- <the exact files about to be touched>` and the plan's `locked_by:` — both
  clear — BEFORE writing a line of provider/service/route code, not after noticing a conflict. Caught mid-session that a
  different operator (`harshkantariya`, host `harsh_pc`) is independently active on this exact plan, on their own slot-2
  clone; their one real-code commit that turn was a narrow, reactive fix to the SAME symptom this session had just
  diagnosed for the operator (the builds hang) — not a race on unclaimed scope. Multi-agent plans need this check before
  every new vertical, not just before a risky one.
- **A registry's byte-size sprawl and its image COUNT are independent signals — the plan's own "~1.5 TB" figure primed
  an assumption that didn't hold.** Before probing live, ~1.5 TB suggested a registry too large to fully list. MEASURED:
  the whole `unified-trading-system` AR repo is only 3365 images (20 repos), listed cold in ~4s — the byte figure is
  dominated by average image SIZE (ML/data-heavy services), not image COUNT. A scan cap sized for "1.5 TB of data" would
  have been massively over-provisioned for what's actually a cheap, fully-listable metadata call. Measure the actual
  axis you're worried about (count vs. bytes) before sizing a safety cap around the wrong one.
- **Two ruff invocations, two different rule sets, on the same file — check both, not just the one CI step you're
  staring at.** The plain `ruff check` (LINT step) and the STEP-5.95 ratchet's isolated `--select TID251` pass read the
  SAME `# noqa` comment under DIFFERENT enabled-rule sets, so a fix for one broke the other twice in sequence during
  this session (fake-code noqa → ratchet counts it as unsuppressed; real-code `TID251` noqa → plain lint flags it as
  `RUF100` unused). The existing `_ci_status_firestore_store.py` precedent (a `per-file-ignores: RUF100` entry) was the
  answer, but only visible by reading `pyproject.toml` directly — the two CI step names alone didn't point at it. When a
  `# noqa: TID251` (or any two-differently-configured-invocation rule) won't go green, grep `pyproject.toml` for how the
  ONE prior site that already worked solved it, rather than iterating noqa text blind.
