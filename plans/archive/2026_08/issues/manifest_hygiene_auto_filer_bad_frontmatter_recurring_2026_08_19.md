---
doc_type: issue
title: "manifest_hygiene_daily.py / reprobe_new_empty_confirmed.py auto-file issue docs with plan-shaped frontmatter — recurring daily QG break"
created: 2026-08-19
parent_epic: observability_master
assigned_vm: planning
resolved_by: >-
  unified-trading-pm@e56e311cbd (boot-prompt fix) + e2e-audit image rebuild/redeploy (build
  127018f4-e3f4-4937-b466-421d0970c106, digest sha256:cf2eb741..., all 3 Cloud Run Jobs updated) —
  see "Second correction" below for why BOTH were needed (the boot prompt fix alone never took
  effect until the stale container running it was replaced).
source:
  - e2e-testing/scripts/audit/manifest_hygiene_daily.py
  - e2e-testing/scripts/audit/reprobe_new_empty_confirmed.py
locked_by:
summary: >-
  The two daily data-pipeline auto-filers write their findings docs into
  unified-trading-pm/plans/active/issues/ with `doc_type: plan`, `status: active`, and
  `asset_group: cross-asset` (not a valid frontmatter enum value) instead of the required
  `doc_type: issue` / `status: open` / `asset_group: [cross-cutting]` shape — every fresh
  doc they file trips `check_frontmatter_schema` and reds the next quality-gates-v2 run
  until a human/agent manually patches the frontmatter after the fact.
status: resolved
nature: issue
asset_group: [cross-cutting, ci]
stage: [data, meta]
repos: [e2e-testing, unified-trading-pm]
scope: [engineer, admin]
tags: [frontmatter, doc-governance, quality-gates, manifest-hygiene, auto-filer, recurring]
related: [manifest_hygiene_red_all_2026_08_19, empty_reprobe_disagreement_all_2026_08_19]
priority: P2
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

> **🗄️ ARCHIVED 2026-08-19** — `status: resolved`, sole todo `[x]`, `locked_by:` empty, no referrers found in
> `plans/active/`. Per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`.

# manifest_hygiene_daily.py / reprobe_new_empty_confirmed.py auto-file issue docs with plan-shaped frontmatter — recurring daily QG break

## What I found

Resolving escalation `agt-064a24` (promote_qg_failure, unified-trading-pm PR #3492, continuously red 51min)
traced the failure to `check_frontmatter_schema` rejecting
`plans/active/issues/manifest_hygiene_red_all_2026_08_19.md`: `doc_type: plan` (path-derived
type is `issue`), `status: active` (not a valid issue status), `asset_group: cross-asset` (not
in the enum), `tags: []`, `resolved_by` absent. The full local `quality-gates.sh` run then
surfaced a second, freshly-filed doc with the exact same defect shape:
`plans/active/issues/empty_reprobe_disagreement_all_2026_08_19.md`. Both are auto-filed by
scripts in `e2e-testing/scripts/audit/` (`manifest_hygiene_daily.py`,
`reprobe_new_empty_confirmed.py`) — "Wave 4b, Phase 5 scripted→LLM escalation hop" per their own
doc preamble.

Checking the equivalent 2026-08-18 docs (`manifest_hygiene_red_all_2026_08_18.md`,
`empty_reprobe_disagreement_all_2026_08_18.md`) shows they now carry correct
`doc_type: issue` / `status: open|resolved` / `asset_group: [cross-cutting]` frontmatter — but
that correction was applied by hand after filing (visible in their status trailing comments),
not by the filer itself. This is a recurring pattern, not a one-off: every day's fresh
auto-filed doc ships broken and needs a human/agent to notice and hand-patch it before the next
promote PR's QG run, and on 2026-08-19 nobody had yet, which is what produced the 51-minute red
wall this escalation was dispatched for.

## Why it matters

This is silent, recurring toil that directly causes fleet-wide promote-PR QG failures — the
exact wall type `quality_gate_resolution` exists to firefight. Fixing the filer template once
(in `e2e-testing/scripts/audit/`) removes the daily manual-patch step and prevents the next
occurrence, rather than firefighting it fresh each day.

## Recommended decision (SUPERSEDED — see Correction)

~~In `e2e-testing/scripts/audit/manifest_hygiene_daily.py` and `reprobe_new_empty_confirmed.py`
(or a shared frontmatter-template helper they both call), fix the emitted frontmatter block to
the issue-doc schema.~~ This premise was wrong — neither script writes frontmatter at all
(confirmed: zero `doc_type` references in either file). See Correction below for the actual fix.

## Correction — found via a 2026-08-19 /ci-reconcile investigating a THIRD occurrence of this alert class

Both filer scripts call `_dp_common.py::file_escalation_issue`, which — per its own docstring and
an explicit 2026-08-18 operator ruling
(`/plans/archive/2026_08/dp_audit_escalation_agent_backed_filing_2026_08_18.md`) — **never writes an issue
doc to disk itself**. It emits a `DP_ESCALATION_DEFERRED` event and dispatches to an agent worker
(`agents/data_pipeline_failure.md`) that is supposed to file the doc from the payload. e2e-testing's
own copy of the frontmatter template was deleted entirely in that same 2026-08-18 change
(`e2e-testing@aa6e8a1498`) — there was nothing left in this repo's scripts to patch.

The REAL bug: `agents/data_pipeline_failure.md`'s boot-prompt instructions told the dispatched
agent to "mirror `e2e-testing/scripts/audit/_dp_common.py::file_escalation_issue`'s template" —
a reference that had already been deleted the same day it was written. Every agent dispatched
into the "no slug, only a finding payload" path between 2026-08-18 and 2026-08-19 10:32 UTC had
no live example to copy and had to guess, which explains the observed plan-shaped frontmatter
(`doc_type: plan`, `status: active`, `asset_group: cross-asset`) — it matches the shape from
BEFORE the 2026-08-18 architecture change, i.e. stale institutional pattern-matching, not random
noise. The instructions were also separately missing `assigned_vm`, itself a required field for
`doc_type: issue`.

**Already fixed**, found already landed when this doc was re-opened for the third occurrence:
`unified-trading-pm@e56e311cbd` (2026-08-19 10:32:57 UTC, a peer session) repointed the boot
prompt to the current, live, test-covered template —
`deployment-service/deployment_service/data_pipeline_monitors/escalation_issue_writer.py::write_issue_doc`
(verified: file exists, has its own prior-incident-driven schema comments and a
`test_escalation_issue_writer.py` test) — and added the missing `assigned_vm: vm-cross-cutting`
instruction. Verified this is genuinely live on current `live-defi-rollout` HEAD, not just
staged.

## Second correction (2026-08-19, later same day) — the deployed container was the ACTUAL root cause, not the boot prompt

Both prior corrections above assumed `dp-audit-bot`'s daily filings came from the dispatched-agent
path (`agents/data_pipeline_failure.md`). They did not. `dp-audit-bot`'s commits carry no
`Quickmerge:` trailer and don't match either bot-exemption pattern
(`check_strict_quickmerge.py`'s `"github-actions"` / `"[bot]"` checks) — they never went through
`safe-doc-push.sh`, quickmerge, or any git hook at all. `git log --author=dp-audit-bot` shows the
identical raw-commit pattern recurring **daily** (2026-08-17 through 2026-08-19, both filings each
day), including on 2026-08-19 — a full day AFTER `e2e-testing@aa6e8a1498` (2026-08-18 11:20:50
UTC) landed the fix that was supposed to stop exactly this ("never raw-commit escalation issue doc
from Cloud Run Job; always dispatch to agent-orchestrator instead").

**Confirmed via `gcloud builds list --project=central-element-323112`**: the `e2e-audit:latest`
Cloud Build image was last built **2026-08-17T02:14:53Z** — a day and a half BEFORE the source
fix. The three Cloud Run Jobs that run these scripts daily
(`uts-prod-dp-manifest-hygiene-changed`, `uts-prod-dp-manifest-hygiene-full`,
`uts-prod-dp-reprobe-empty`) were pinned to that stale image's exact digest
(`sha256:e27b001c...`). **The source fix was real and correct — it was simply never deployed.**
That's why every downstream "fix" (this doc's original recommendation, the boot-prompt repair)
kept failing to actually stop the recurrence: none of them touched the thing that was really
running.

**Fix**: rebuilt via `gcloud builds submit --config=cloudbuild-e2e-audit.yaml
--project=central-element-323112 --region=asia-northeast1 .` (build `127018f4-e3f4-4937-b466-421d0970c106`,
2026-08-19T14:20:11Z, SUCCESS, 1m45s) — new digest `sha256:cf2eb741...`. Explicitly updated all
three Cloud Run Jobs to the new digest via `gcloud run jobs update <name> --image=...@sha256:cf2eb741...`
(verified live via `gcloud run jobs describe` on all three afterward — all three now reference the
new digest, not just the update command's own success message). Did **not** manually execute any
job — next scheduled run picks up the new image on its own.

With this deployed, `dp-audit-bot`'s next daily run will hit the ALREADY-FIXED `file_escalation_issue`
code path (emit event + dispatch to agent, never raw-write+push) — the boot-prompt fix from the
first correction now actually matters, since a dispatched agent will finally be the one filing
these docs going forward, through the gated `safe-doc-push.sh` path.

## Todos

- [x] ✅ [CODE] P2. Root-cause + fix the recurring bad-frontmatter auto-filing. DONE — actual fix
      was a boot-prompt reference repair in `agents/data_pipeline_failure.md`
      (`unified-trading-pm@e56e311cbd`), not a change to the e2e-testing scripts this doc
      originally named; corrected and closed by a later `/ci-reconcile` pass after finding the
      original recommendation pointed at dead code.
- [x] ✅ [INFRA] P1. Rebuild + redeploy the `e2e-audit` Cloud Build image so the boot-prompt fix
      (and the underlying `file_escalation_issue` architecture change) actually takes effect. DONE
      — see "Second correction" above; new digest live on all three Cloud Run Jobs, verified via
      `gcloud run jobs describe`, not executed manually.
- [ ] [OPERATOR] P3. Confirm tomorrow's (2026-08-20) `dp-audit-bot` daily runs stop appearing —
      if `manifest_hygiene_red_all_2026_08_20.md` / `empty_reprobe_disagreement_all_2026_08_20.md`
      still land with bad frontmatter or a `dp-audit-bot` raw-commit signature, the deploy did not
      actually take effect (or a fourth mechanism exists) and this needs reopening.
