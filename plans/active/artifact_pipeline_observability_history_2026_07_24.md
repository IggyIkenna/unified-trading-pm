---
doc_type: plan
title: Artifact pipeline observability — Shipped History (forked from the artifact pipeline observability plan)
summary:
  Archive-bound Progress Log history extracted verbatim from artifact_pipeline_observability_2026_07_17.md's 2026-07-24
  line-cap remediation. Covers the earliest dated Progress Log narrative from "2026-07-17 — Audit + mock complete"
  through "2026-07-21 (later still) — UI vertical slice 1 shipped" — the mock-first design phase, the shape lock, the
  tarball blast-radius + Deployments-filter audits, the AWS-deferred reframe, build kickoff, and the backend Phase 1/2
  first vertical (Pipeline view) plus its first live UI tab. Every item in this file is already pure narrative
  describing already-shipped work — zero open todos. Record-only; not intended for further action.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui, deployment-api, unified-trading-pm]
scope: [engineer, admin]
tags:
  [deployment-observability, artifact-pipeline, image-builds, tarballs, cloud-build, history, plan-split, archive-bound]
related: [/plans/active/artifact_pipeline_observability_2026_07_17.md]
created: "2026-07-24"
last_updated: "2026-07-24"
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
    "Forked 2026-07-24 from artifact_pipeline_observability_2026_07_17.md's Progress Log entries during the line-cap
    trim (parent was 1045 lines against the 1000-line cap).",
  ]
locked_by:
locked_since:
---

> **🟢 2026-07-24 history extraction** — this file holds Progress Log content moved VERBATIM out of
> `artifact_pipeline_observability_2026_07_17.md` (the "2026-07-17 — Audit + mock complete" entry through the final
> "2026-07-21 (later still) — UI vertical slice 1 shipped" entry) to bring that plan back under its 1000-line cap. Every
> line below already existed in the parent unchanged — no content was altered, only relocated. All items here are
> shipped/narrative; there are no open todos in this file. See the parent plan for current status and the still-open
> items.

# Artifact pipeline observability — Shipped History

- **2026-07-17** — Audit + mock complete. Both clouds probed live; 4 code audits done. Operator decisions captured:
  scope = images + tarballs (artifact pipeline); absorb+retire CloudBuildsTab; page-first (bugs → issue doc); human
  plan. Mock shipped to `deployment-ui/public/design-mocks/artifact-pipeline.html` (deployment-ui@479f8c2, viewable at
  `/design-mocks/artifact-pipeline.html`; temporary, delete-when the real page ships) — real probed data; 2 fabricated
  attributions caught + fixed; bug #2 demoted to UNVERIFIED. Deploy-timeline view + churn/rollback/failed-deploy signals
  added after the feasibility grill confirmed Cloud Run revisions are a free 72-day per-deploy history. Feasibility
  verdict: producible + cheap (cents/yr) + ~60–72d already retained.
- **2026-07-17 (later)** — **Shape LOCKED**: top-level `/ops/artifacts`, all 5 views in v1, default = What's running.
  Operator review of the running tab surfaced a **real design defect**: the row unit was per-workload, collapsing the
  whole VM fleet into one row — misleading at fleet scale (measured: 13 live VMs, incl. 4 `features-sports` in two
  cohorts ~7h apart, i.e. two code versions live in one service). Row unit changed to **service × artifact version with
  an expandable host list**, plus a `fragmented` flag; rationale is data-correctness (a VM never self-updates, so a fix
  shipped today never reaches VMs launched before it). Operator added: deep-link a version row into **Deployments with a
  pre-loaded filter** (needs additive Deployments-side work — Phase 3b) and out to the **GCP/AWS console + build logs**
  for verification. Tarball commit tracking moved **into scope**: (A) measured stamp going forward + (B) inferred from
  the manifest timeline for historic only — **gated on a blast-radius audit** (Phase 3c) under the operator's hard
  constraint that the working latest-tarball CD flow must not break. Two read-only audits dispatched (tarball
  blast-radius; Deployments filter support).
- **2026-07-17 — BOTH AUDITS LANDED.** Tarball verdict **YES-WITH-CONDITIONS**: blast radius measured zero, the change
  is 2 shell lines + 0 Python, no naming/path change, and the commit is _already_ parsed at boot and thrown away. The
  single real risk is a `set -e` regression in `setup-data-pipeline-vm.sh` — which **no CI gate covers** (bash uploaded
  straight to GCS, never executed in CI), so the verification gate is a live `EPHEMERAL_BATCH` launch, not a test run.
  Option (B) came back **weaker than assumed** (±30-min window, wrong-side timestamp, per-repo vector, 30-day archive
  expiry) and may not be worth building now that (A) is cheap. Deployments audit: the cross-link is **cheaper than
  assumed** — provenance is already in hand in `_vm_item()` (~2 lines, zero new I/O), the page is already fully
  URL-param-backed by design, and `consoleUrl()` already exists to reuse.
- **2026-07-17 — three corrections to earlier claims in this plan** (all fixed above): (1) the memory ceiling is **16
  GiB**, not 4 — I had quoted a stale decision from the OOM plan instead of the deployed `cloudbuild.yaml`; (2) the AWS
  tarball lane's uploader and setup script **agree** on the bucket — the real breakage is an empty `code/` prefix plus a
  _different_ nonexistent bucket in the EC2 launcher; (3) manifest/tarball counts corrected to **4064 / 163**. Also: the
  `0.99.0` `dep_versions` value is an **honest** report of a deliberately-pinned `SETUPTOOLS_SCM_PRETEND_VERSION`
  constant (`setup-data-pipeline-vm.sh:703`, because tarballs ship without `.git`) — it carries zero provenance, but the
  BoM is not lying; the mock's wording must reflect that distinction.
- **2026-07-17 — operator DROPPED option (B) entirely.** Only (A), the measured stamp, gets built. Pre-(A) VMs render as
  ⚪ unknown-with-reason rather than carrying a falsely-precise inferred commit, and age out as the fleet recycles.
- **2026-07-20/21 — Tab 1 iterated + signed-off-pending.** Rebuilt to service × version with expandable hosts, made
  service groups collapsible + an expand/collapse-all control (verified in jsdom), and added the "Built from · when"
  build-datetime column (operator ask). Interactions and stat tiles verified against the data, not eyeballed. All tab-1
  review findings folded into the per-tab gate item above. **No page code started — still mock-only, per the working
  mode banner.**
- **2026-07-21 — Tabs 2–5 correctness+usefulness pass, AWS-deferred reframe, issue doc filed (3 ships).** (1)
  `ui@e01e5fc` — Deploy timeline made estate-wide (Cloud Run + GCE VM launches as tarball-lane deploys + real AWS
  storm), live-now badges, held-for intervals, human-vs-CI deployer, filter chips, console links; Pipeline gained filter
  chips + the ⇄-both-lanes xlane badge; Artifacts rebuilt to one-row-per-repo from a **live ECR inventory** (20 repos,
  real counts); Health folded in deploy-lane findings + severity filter + cross-links. All verified in jsdom (0 script
  errors). AWS data probed live 2026-07-21; GCP stayed the 2026-07-17 sample (auth still expired). (2) `ui@fa38eaa` +
  `pm@f25f10911` — reframed AWS from red/defect to **intentionally parked** (operator: no AWS credits, GCP is sole
  active path): top banner, Deploy/Artifacts/Health states → parked/deferred, Health `deferred` tier. (3) `pm@6f52496a4`
  — filed `issues/build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md` after re-verifying every audit
  finding against current code (see the new lesson below). **Still mock-only; no page code started.**
- **2026-07-21 (later) — build-kickoff prep + mock stale-fact corrections (`ui@57785a3`).** Operator signalled readiness
  to build the image tab and to include the tarball SHA stamp **now** ("do it now" — Phase 3c Option A folds into the
  first build). Before starting, re-read Tabs 2–5 against current verified facts and shipped `ui@57785a3` fixing 3 stale
  spots: the Tab-3 + Tab-5 failure-watcher note (that watcher was **fixed 2026-07-20** — right repo + notify-slack
  dedup) and the Tab-5 AWS-tarball "`code/` 0 objects" claim (now **populated**; real defect = the launcher's 404
  bucket). Kept the AWS-lane bugs as real defects tagged `AWS-deferred`, distinct from the blue "parked · not a defect"
  tier — flagged for operator confirmation. Mapped the full build blueprint from the two reference services
  (`cost_observability` backend service + `CostObservability.tsx` page — providers/`_safe` isolation, snapshot worker,
  DuckDB-over-parquet, `_resolve_range`, reqId ordering guard, mock-handler ordering, NAV_GROUPS/route seams). Captured
  two real-page requirements as gate-item notes (Tab-4 per-repo size + GC-candidate flag; Tab-2 date cursor). Verified
  in jsdom (all 5 tabs render, 0 errors); content-verified on origin (ahead=0). **Still mock-only; awaiting operator
  sign-off on Tabs 2–5 before any page code.**
- **2026-07-21 (later) — build STARTED (operator signed off all 5 tabs); backend Phase 1/2 first vertical shipped.**
  Operator: "good to start … on all the tabs 1 to 5" + AWS-lane framing confirmed ("what's broken is broken"). Flipped
  the DO-NOT-START banner → 🟢 BUILD STARTED and ticked all 5 tab gates + the final sign-off (`pm@161200196`). Built
  `deployment_api/services/artifact_pipeline/` on the cost-observability shape and shipped the first end-to-end vertical
  — the **Pipeline (builds) view** — as **`deployment-api@8eda1f8`**: the normalized contract for ALL 5 views
  (`models.py` — internal `BuildFact`/`DeployFact`/`ImageFact` + Pydantic response models), the TTL cache, the `safe[T]`
  per-source isolation wrapper, the `gcp_cloud_builds` provider (Cloud Build → `BuildFact`, adding the structured
  `failure_info` + `steps` the old build-history route dropped), `service.builds()` (window resolution, dup + cross-lane
  detection, data-derived stats), `GET /api/artifacts/builds` + the loud `_resolve_range` 400 gate, main.py
  registration, and 13 `--block-network` unit tests. Full deployment-api gate green (basedpyright 0, ruff clean, 4783
  tests). **Remaining backend:** 4 views (images / deploys / running-join+drift / health) + their providers (AR
  versions, Cloud Run revisions, ECR, App Runner/ECS, CodeBuild, tarball manifests) + the snapshot worker + the runtime
  digest→SHA join; then the UI page + Phase 3c tarball stamp.
- **2026-07-21 (later still) — UI vertical slice 1 shipped: the `/ops/artifacts` page with a LIVE Pipeline tab
  (`deployment-ui@47e6379`).** Operator asked for "at least one tab … in the actual UI". Ran the API (:8004, real GCP
  data via ADC/`GCP_PROJECT_ID=central-element-323112`, `DISABLE_AUTH=true`) + the UI (:5183) locally for the operator
  first — verified 400 live builds / 98.2% success / 7 failures / 26 wasted-dups flowing end-to-end. Then built
  `src/pages/ArtifactPipeline.tsx` (self-contained, mirroring `CostObservability`: plain fetch + `useRef` reqId guard +
  inline token-styled primitives): a 5-tab shell (running / deploy / **pipeline** / artifacts / health) where the
  **Pipeline (builds) tab is wired live to `GET /api/artifacts/builds`** — data-derived stat band (total / success-rate
  / failed / median / wasted-dup), client-side lane/cloud/status filters, and a per-build failure + step-timeline
  drawer; the other four tabs render an honest "backend in progress" placeholder. Wired the route (`App.tsx`) + a
  Fleet&Cost `NAV_GROUPS` entry (`NavMenu.tsx` — auto-lights `TopNavBar` + satisfies the orphan-audit),
  `getArtifactBuilds`
  - `BuildsResponse`/`BuildRow`/`BuildStep`/`BuildsStats` types on `deploymentApi.ts`, a `mockArtifactBuilds` handler on
    `mock-api.ts`, **5 Vitest** unit tests + a **2-case `pw:L2`** smoke spec (`tests/smoke/artifact-pipeline.spec.ts`;
    cites this plan). Bumped the two nav-count tests (15→16 canonical entries). Full deployment-ui gate green (tsc +
    eslint
  - orphan-audit + 1047 tests + build + codex checks incl. no-hardcoded-colours). Shipped through two peer-rebase
    sentinel-stale cycles (busy branch) — pull-rebase kept the merged tree, content-verified ahead=0. **Remaining UI:**
    the 4 placeholder tabs' real views + their `pw:L2` coverage + `__mock` race hooks, each gated on its per-view
    backend (deploys next).
