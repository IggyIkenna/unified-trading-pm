---
doc_type: issue
title:
  Data-pipeline audit scripts write commit-intended escalation artifacts into the PM tree but never commit them — local
  runs strand RED findings as dirty untracked files
summary:
  "`manifest_hygiene_daily.py` (and the shared `_dp_common.py` writers) emit an escalation issue doc under
  `plans/active/issues/` plus candidate CSVs under `plans/audit/results/` — both of which the design intends to be
  COMMITTED (the issue doc so the orchestrator PlanRegenLoop ingests it; the CSVs are force-un-ignored in `.gitignore`).
  But the writers have ZERO git commit/push logic, so a LOCAL run just drops the files into the working tree and exits.
  On 2026-07-03 a local `--mode full` run left three such files (a cefi RED issue doc + a 1.4KB candidate CSV + an 18MB
  divergence dump) sitting DIRTY and untracked in the root PM clone for 3 days; the escalation never reached the
  orchestrator and the files were later wiped by a tree-clean before anyone acted on the cefi finding. The Cloud Run
  cron path masks the bug (its output dir is ephemeral container FS, discarded on job exit), so the gap only bites on
  operator/agent-driven local runs."
status: resolved
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [e2e-testing, unified-trading-pm]
scope: [engineer, admin]
tags: [data-pipeline, observability, self-healing, escalation, audit, ci-cd, git-hygiene]
related:
  [../data_pipeline_hardening_self_monitoring_2026_06_22.md, manifest_hygiene_red_2026_07_06.md] # (was: manifest_hygiene_red_2026_07_03.md — dangling; that file was WIPED by a tree-clean before ever being
  # committed (this is literally the bug this doc describes, see "Background" below) so it never existed in git
  # history. manifest_hygiene_red_2026_07_06.md is the actual re-filed successor escalation for the same stranded
  # cefi finding (see Todos item 3 below). Sync 2026-07-12, finding 391, §A2 B-queue ruling.
created: 2026-07-06
parent_epic: observability_master
priority: P2
source:
  [
    "operator-reported dirty root-repo files 2026-07-06",
    "e2e-testing/scripts/audit/manifest_hygiene_daily.py",
    "e2e-testing/scripts/audit/_dp_common.py (write_candidate_csv / file_escalation_issue)",
    "deployment-service/terraform/gcp/data_pipeline_audit_scheduler.tf",
  ]
assigned_vm: planning
resolved_by: "unified-trading-pm@ad1fa6bc2 — see terminal VERIFY todo below"
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-12
---

> **(2026-07-12, finding 212, §A2 B-queue ruling)**: frontmatter `status` synced `open` → `resolved` (was: `open`) — all
> 4 todos are checked `[x]` including the terminal VERIFY step, which cites a live re-run confirming clean `git status`
> and successful PlanRegenLoop ingestion at `unified-trading-pm@ad1fa6bc2`.

# Audit escalation artifacts are written into the PM tree but never committed → local runs strand RED findings

> **TL;DR for the worker:** The data-pipeline self-monitoring audit writes files it _intends_ to be committed (an
> escalation issue doc + candidate CSVs), but the code that writes them contains **no `git add`/`commit`/`push`**. When
> the audit runs **locally** (operator or agent, not the Cloud Run cron), the artifacts land as **dirty untracked files
> in the root PM clone** and just sit there — the orchestrator never ingests the escalation, and the next
> `git clean`/tree-reset wipes them. Fix the loop so a produced escalation is either committed by the sanctioned path or
> is not written to a commit-intended location in the first place. Full context below.

## Background — how this was discovered (2026-07-06)

An operator noticed 5 dirty files in the root `unified-trading-pm` clone and asked who wrote them and why they were
uncommitted. Investigation split them into two unrelated groups:

- **Group 1 (already reverted by the operator):** two modified tracked scripts —
  [scripts/dev/slot-cron-ff-pull.sh](../../../scripts/dev/slot-cron-ff-pull.sh) and
  [scripts/verify-slot-host-symmetry.sh](../../../scripts/verify-slot-host-symmetry.sh) — uncommitted agent WIP from a
  2026-07-06 incident. **Not this issue.** Reverted, no action needed.

- **Group 2 (this issue):** three **untracked, machine-generated** files from the data-pipeline audit, dirty in the tree
  since 2026-07-03 and later wiped by a tree-clean before triage:
  1. `plans/active/issues/manifest_hygiene_red_2026_07_03.md` — an auto-filed **cefi RED escalation issue doc**
     (`assigned_vm: vm-cross-cutting`, `parent_epic: observability_master`) carrying one `[CODE] P1` todo pointed at
     `market-tick-data-service`. It referenced file (2) by absolute path.
  2. `plans/audit/results/manifest_hygiene_cefi_2026_07_03.csv` — a **1.4 KB, 10-row** candidate list. Despite the
     `.csv` name it is glued-together log lines (some real findings — `349628/5718967 rows non-v9`,
     `4-pillar rc=1 for cefi`, `DIVERGENT_EMPTY 20,282` — and some bare INFO log headers like
     `Phantom distribution by venue (top 15):`). Breadcrumbs, not a clean table; the real phantom data is the 782-record
     triage JSONL written to `gs://central-element-323112-phantom-triage/triage_cefi_20260703_052348.jsonl`.
  3. `plans/audit/results/divergence_2026-07-03.csv` — an **18 MB, 190,846-row** full cell-level divergence dump, **cefi
     only**, spanning **2019-03-30 → 2026-06-29**. Columns:
     `asset_group,venue,data_type,date,expected_state,reason,any_captured,any_empty,any_failed,row_count,classification`.
     Classification distribution: `MISSING_EXPECTED 82,440` · `OK_CAPTURED 48,820` · `OK_OUT_OF_SCOPE 21,310` ·
     `DIVERGENT_EMPTY 20,282` · `OK_NOT_YET_LIVE 14,382` · `ATTEMPTED_FAILED 3,612`. ~84k of 190k rows are `OK_*`
     (nothing wrong). The issue doc (1) does **not** reference this file — it is a raw intermediate diagnostic.

> **Note:** all three files were wiped from the working tree (by a `git clean`/tree-reset, likely the 5-min slot cron)
> **before** the operator could act on them. Their content above was captured during the 2026-07-06 investigation. The
> underlying **cefi RED data finding itself is still unaddressed** and should be re-surfaced (see "Also do" below) —
> this issue is about the _tooling gap that stranded it_, not the cefi finding per se.

## Who created the files (attribution)

- **Machine-written by the audit script**, not a human hand-editing: the issue doc's own frontmatter says
  `author: "manifest_hygiene_daily.py (data-pipeline daily audit)"`; the CSVs are written by
  `_dp_common.write_candidate_csv()` and the divergence dump by the `detect_manifest_divergence` CLI the audit shells
  out to.
- **From a LOCAL `--mode full` run, NOT the Cloud Scheduler cron.** Proof:
  - mtime `2026-07-03 05:15 / 05:53 UTC`, a **Friday**. The crons are `0 8 * * *` (daily `--mode changed`) and
    `0 8 * * 0` (**Sunday** `--mode full`). Neither fires Friday 05:15.
  - The findings include phantom + 4-pillar classes, which only `--mode full` produces — so someone ran the full walk by
    hand in this workspace.
- **No git attribution** (never committed); filesystem owner was `ubuntu`. The exact local actor (which agent/operator
  slot ran it) could not be pinned — that ambiguity is itself a symptom of the gap (a committed artifact would carry
  slot·host authorship).

## Root cause — the actual bug to fix

The design **intends these artifacts to be committed**, but nothing commits them:

1. **Issue doc is ingestion-intended.** `_dp_common.file_escalation_issue()` writes to `plans/active/issues/` precisely
   so the orchestrator's **PlanRegenLoop → backlog → AutoSpawn** picks it up — the in-code comment
   ([\_dp_common.py](../../../../e2e-testing/scripts/audit/_dp_common.py), ~L114-117) says a filed issue "is only
   ingested … when it declares an explicit `assigned_vm`" and must therefore carry one. Ingestion requires the file to
   be **committed and pushed**. It never is.
2. **Candidate CSVs are commit-eligible by design.** `.gitignore` line 138 `*.csv` ignores all CSVs, but line 140
   `!plans/audit/results/*.csv` **force-un-ignores** these ("Mega-audit diagnostic outputs are checked-in artefacts
   consumed by downstream phases").
3. **But the writers have no git logic at all.** `grep -n 'git\|commit\|push' manifest_hygiene_daily.py _dp_common.py` →
   nothing. The script computes its output dir as
   `Path(__file__).resolve().parents[3] / "unified-trading-pm" / "plans" / …` and just writes + exits.

**Why the cron path hides it:** in the Cloud Run job the image lays the repo at `/app`, so `parents[3]` resolves to
`/app/unified-trading-pm/plans/…` — **ephemeral container FS discarded on job exit**. The cron's _real_ outputs are the
`DP_*` events → alerting-service → `#data-pipeline-alerts` Slack, plus the triage JSONL to GCS. So the cron never needed
the local files, and the missing-commit bug is invisible there. It only bites when the script is run **locally** (as on
2026-07-03), where `parents[3]` resolves to the real workspace root and the files land in the live PM clone as dirty
untracked cruft that either strands the escalation or gets wiped by a tree-clean.

## What triggers the audit (for reference)

- **Scheduled:** GCP Cloud Scheduler → Cloud Run Jobs, defined in
  [deployment-service/terraform/gcp/data_pipeline_audit_scheduler.tf](../../../../deployment-service/terraform/gcp/data_pipeline_audit_scheduler.tf)
  (plan `data_pipeline_hardening_self_monitoring_2026_06_22.md`, Wave-4b): `dp-manifest-hygiene-changed-cron` daily
  `0 8 * * *` (`--mode changed`) and `dp-manifest-hygiene-full-cron` weekly `0 8 * * 0` (`--mode full`). **Not** a
  plan-health agent and **not** the agent-orchestrator.
- **Ad-hoc / local:** any operator or agent can run the script directly — which is what produced the 2026-07-03 files.

## How to regenerate the artifacts (to reproduce / verify a fix)

The script lives at `e2e-testing/scripts/audit/manifest_hygiene_daily.py`. Run it from that repo's `.venv` with GCP ADC
available (it reads GCS via `StorageClient`):

```bash
cd /home/ubuntu/unified-trading-system-repos/e2e-testing
GCP_PROJECT_ID=central-element-323112 DEPLOYMENT_ENV=prod CLOUD_PROVIDER=gcp \
  .venv/bin/python scripts/audit/manifest_hygiene_daily.py --mode full --asset-group cefi
# --mode changed  → index-only (v9 / divergence / path-canonicality), the fast daily checks
# --mode full     → adds the GCS-walking phantom + 4-pillar checks (slower; what produced the 18MB dump)
# omit --asset-group → all 5 AGs
# --smoke          → imports + arg-parse only, no GCS (mechanism check)
```

A non-empty candidate list re-creates: the issue doc under `plans/active/issues/`, the per-AG candidate CSV under
`plans/audit/results/`, and (in `--mode full`) the `divergence_<date>.csv` dump — landing in whichever
`…/unified-trading-pm/…` the script's `parents[3]` resolves to. **This is the reproduction of the bug**: after the run,
`git status` in the PM clone will show them dirty and untracked, with nothing having committed them.

## Recommended fix (design decision needed — that's why this is a `planning` dispatch)

Pick one coherent approach and implement it end-to-end; do **not** just paper over symptoms:

- **Option A — script owns the commit (sanctioned path).** When a local (non-container) run produces an escalation,
  commit the issue doc + small candidate CSV via the workspace's approved doc path (a `docs(plans):` commit + push to
  LDR — **never a raw `git push` of code**, and this is docs so prek-only applies). Detect "am I in a real clone vs an
  ephemeral container" so the cron stays a no-op writer. This is the most faithful to the current design (issue doc is
  meant to be ingested).
- **Option B — decouple from the working tree.** Stop writing commit-intended artifacts into the live clone at all; have
  the audit publish the escalation through a channel the orchestrator already reads (e.g. the same `DP_*` event spine /
  a dedicated GCS prefix the PlanRegenLoop ingests), so there is nothing to leave dirty. Cleaner long-term but a bigger
  change to the ingestion contract.
- **In either case, fix the artifact-size / gitignore mismatch:** the 18 MB `divergence_*.csv` is a raw, mostly-`OK_*`,
  unreferenced, fully-regenerable dump — it should **not** enter git history. Narrow the `.gitignore` whitelist
  (line 140) so `divergence_*.csv` is excluded while the small candidate CSVs stay commit-eligible, OR write the
  divergence dump under a scratch/GCS path instead of `plans/audit/results/`.

**Verification (definition of done):** run the regeneration command above and confirm the produced escalation is either
(a) committed+pushed by the sanctioned path and ingested by PlanRegenLoop, or (b) delivered via the chosen channel with
**no dirty untracked file left in the PM clone**; and confirm a fresh full run leaves `git status` clean (no 18 MB CSV,
no stranded issue doc).

## Also do (re-surface the stranded cefi finding)

The 2026-07-03 cefi RED finding (20,282 `DIVERGENT_EMPTY` cells — notably `OKX-SWAP trades` around 2026-05-20..22;
349,628 non-v9 rows; phantom rows; `4-pillar rc=1`) was **never triaged** — its issue doc was wiped before pickup. After
(or alongside) fixing the tooling gap, **re-run the audit for cefi** and file/ingest a fresh escalation so the actual
data-correctness signal gets worked. Per the data-pipeline-correctness hard rule a RED audit should not be left
unaddressed.

## Todos

- [x] ✅ [CODE] P2. Fix the escalation-commit loop in
      `e2e-testing/scripts/audit/{manifest_hygiene_daily.py,_dp_common.py}` — chose Option A (script commits via
      sanctioned `docs(plans):` path on local runs, no-op in container). New `_commit_and_push_pm_artifacts()` helper in
      `_dp_common.py` detects a real PM clone via `<pm_root>/.git`, stages the issue doc + candidate CSVs, commits with
      the `docs(plans):` prefix (strict-quickmerge carve-out for plans-only), and pushes to `live-defi-rollout`.
      `file_escalation_issue()` now invokes it (skipped when `issues_dir` is a test override). Ephemeral container FS
      (no `.git` under `/app/unified-trading-pm/`) stays a no-op so the Cloud Run cron path is unchanged. Best-effort —
      a git failure logs a warning but never sinks the audit run. 6 new unit tests cover the no-git, has-git,
      missing-artifact, idempotent-noop, subprocess-error, and test-override paths. — e2e-testing@694ff4c
- [x] ✅ [CODE] P2. Fix the artifact-size/gitignore mismatch — keep the 18 MB `divergence_*.csv` out of git history —
      chose "narrow the whitelist" (Option A): appended `plans/audit/results/divergence_*.csv` after the
      `!plans/audit/results/*.csv` whitelist in `unified-trading-pm/.gitignore`. Verified with `git check-ignore`:
      `divergence_2026-07-06.csv` → ignored (last-match line 146); `manifest_hygiene_cefi_*.csv` → still committable
      (last-match line 140 whitelist). Divergence CLI (`unified-trading-library/scripts/detect_manifest_divergence.py`)
      unchanged — the file still lands at the same path for local inspection, just not in git history. —
      unified-trading-pm@2d6fe63
- [x] ✅ [DATA] P1. Re-run the cefi audit (`--mode full --asset-group cefi`) and file/ingest a fresh escalation so the
      stranded 2026-07-03 RED finding (20,282 DIVERGENT_EMPTY / non-v9 / phantom / 4-pillar) actually gets triaged in
      `market-tick-data-service`. — unified-trading-pm@460682f91 (slot-13, 2026-07-06). Evidence: audit ran 15:07-15:17
      UTC from slot-13, wrote issue doc `plans/active/issues/manifest_hygiene_red_2026_07_06.md` + candidate CSV
      `plans/audit/results/manifest_hygiene_cefi_2026_07_06.csv` (both committed at 460682f91); `assigned_vm`
      hand-edited from the pre-694ff4c script default (`vm-cross-cutting`) to `planning` so PlanRegenLoop actually
      ingests the escalation. Fresh findings: schema_version_not_v9 344,842/7,219,598 rows (dist 9/5/6/4 =
      6.87M/178k/133k/33k — all legacy stragglers); oracle_expects_but_empty 23,451 DIVERGENT_EMPTY (mostly UPBIT
      book_snapshot_5 around 2024-12-28..30); phantom 0; 4-pillar 0 (recovered vs rc=1 on 2026-07-03). The 18MB
      `divergence_2026-07-06.csv` diagnostic was NOT committed — it is regeneratable and item #2 owns the gitignore
      narrowing. Audit ran BEFORE item #1's commit-and-push helper (694ff4c) reached this slot; a repeat run with the
      new helper is covered by item #4 (VERIFY).
- [x] ✅ [VERIFY] P2. Confirm a fresh full run leaves `git status` clean in the PM clone and the escalation is ingested
      by PlanRegenLoop (no dirty untracked artifacts). — unified-trading-pm@ad1fa6bc2. Evidence: ran
      `manifest_hygiene_daily.py --mode changed --asset-group cefi` (slot-3, 2026-07-06 19:35 UTC);
      `_commit_and_push_pm_artifacts()` committed issue doc + candidate CSV at ad1fa6bc2 and pushed to LDR; `git status`
      in PM clone: clean (empty). Gitignore also verified: `divergence_*.csv` → ignored (line 146); candidate CSVs →
      committable. PlanRegenLoop ingestion: `manifest_hygiene_red_2026_07_06.md` at ad1fa6bc2 carries
      `assigned_vm: planning` → will be ingested on next PlanRegenLoop tick.
