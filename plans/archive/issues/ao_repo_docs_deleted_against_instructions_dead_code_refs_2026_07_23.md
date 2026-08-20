---
doc_type: issue
title:
  "agent-orchestrator repo-docs cleanup deleted 3 files its own instructions said to KEEP/banner/repoint — leaving 5
  dead doc-references live in shipped code, and a tracker Progress Log claiming '0 dead links' that was never true for
  this batch"
summary:
  ao_docs_reconciliation Tier-6 gave explicit per-file instructions — AUDIT_FINDINGS_2026_05_18.md was to be bannered
  NOT deleted (cited as a live spec), PLAN.md was to have 3 docstrings repointed FIRST then be split, and
  MAIN_AGENT_CUTOVER_REVIEW.md was to be kept with no action. agent-orchestrator@19766e7 deleted all three anyway. Five
  references in shipped server code still point at the deleted files (bootstrap.py, db.py, orm.py, models/__init__.py,
  routes/slots_worker.py). The consolidated tracker's 2026-07-18 Progress Log asserts a final state of zero dead links
  and zero refs to any of the 12 deleted AO docs — untrue for this batch, since the sweep commits it cites (ao@3d2c0e6
  and ao@63d8284) landed about 10 hours later and covered OPERATIONS.md and ENV_VARS instead. Two more repo docs remain
  stale — README.md's directory tree still lists the deleted agents/ dir plus 7 nonexistent files, and
  REPO_PROVENANCE.md still describes the retired tab to LDR to staging to main flow.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [agent-orchestrator, docs, dead-links, conservation-failure, plan-reconcile, false-progress-claim]
related:
  [
    /plans/archive/2026_08/ao_docs_reconciliation_2026_07_15.md,
    /plans/archive/2026_08/ao_open_issues_consolidated_close_out_2026_07_17.md,
  ]
created: 2026-07-23
last_updated: 2026-07-23
priority: P2
parent_epic: orchestrator_master
source: "/plan-reconcile run 2026-07-23 (AO scope), Phase-1 consolidated-docs hunter; every claim re-verified by main"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
resolved_by: all 4 todos shipped with commit SHAs; gate re-measured 2026-07-26 (/plan-reconcile ao) -- zero hits
locked_by:
depends_on: []
---

> **🟢 RESOLVED 2026-07-23 (re-verified 2026-07-26) -- all 4 fixes shipped and independently re-measured 2 days later,
> confirmed clean. Archived per issue-doc-lifecycle.**

## What happened

`ao_docs_reconciliation_2026_07_15.md` Tier-6 audited 10 repo docs in `agent-orchestrator/docs/` and gave **per-file**
instructions — deliberately not a blanket delete, because three of them were cited from live code.
`agent-orchestrator@19766e7` (2026-07-18 00:43:10 +0530, _"docs: AO repo docs cleanup — delete 7 historical build
artifacts, fix README + AUTH_INVENTORY"_, confirmed ancestor of `origin/live-defi-rollout`) deleted them anyway.

| File                           | Tier-6 instruction                                                                                          | What happened              |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------- | -------------------------- |
| `AUDIT_FINDINGS_2026_05_18.md` | **"banner (NOT archive — it is cited as a live spec)"**                                                     | DELETED                    |
| `PLAN.md`                      | **"split, do NOT blanket-delete: repoint `server/db.py`, `orm.py`, `models/__init__.py` docstrings FIRST"** | DELETED, nothing repointed |
| `MAIN_AGENT_CUTOVER_REVIEW.md` | **"keep — no action"** (already correctly bannered)                                                         | DELETED                    |

## Verified consequence — 5 dead doc-references live in shipped code

Measured 2026-07-23 (`rg` over `agent-orchestrator/server/**/*.py`; all three target files confirmed absent):

```
server/bootstrap.py:278            # post-cutover spec in docs/MAIN_AGENT_CUTOVER_REVIEW.md.
server/models/__init__.py:1        """... See docs/PLAN.md § API Endpoints.
server/db.py:48                    do not race on dispatch (see docs/PLAN.md § Concurrency Model).
server/orm.py:1                    """... See docs/PLAN.md § SQLite — Runtime State."""
server/routes/slots_worker.py:705  `server/verify.py` + `docs/AUDIT_FINDINGS_2026_05_18.md`):
```

These are docstrings/comments, so nothing breaks at runtime — the cost is that the next person to read `orm.py` or
`db.py` for the concurrency contract follows a pointer to a file that does not exist, on the exact subject (dispatch
race conditions) where guessing is expensive.

## The false-progress claim — read this before trusting the tracker's Progress Log

`ao_open_issues_consolidated_close_out_2026_07_17.md`'s 2026-07-18 Progress Log entry states:

> Final state: 0 dead links, 0 refs to any of the 12 deleted AO docs

**That is not true for this batch, and the timestamps prove the sweep could not have covered it:** the cited sweep
commits are `ao@3d2c0e6` (2026-07-18 10:28:12) and `ao@63d8284` (10:35:40) — about `OPERATIONS.md` and an
`ORCHESTRATOR_VM_ID` example — landing ~10 hours **after** `19766e7` (00:43:10) removed these three files. The sweep was
real; its scope simply never included them, and the summary generalised.

This is the more important half of the finding. A verified-sounding "0 dead links" line is exactly what stops the next
person re-checking.

## Also still stale (same Tier-6 batch, instructions not carried out)

- `agent-orchestrator/README.md:444-449` — the "Files in This Directory" tree still lists `agents/` and 7 files under it
  (`RULES.md`, `main.md`, `review.md`, `backup.md`, `worker.md`, `monitor.md`, `usage_reporter.md`). The `agents/`
  directory **does not exist** (removed separately in `ao@5eaea29`). README.md:365 and :397 also link `agents/main.md` /
  `agents/review.md` inline. Tier-6 asked for "replace with a pointer".
- `agent-orchestrator/docs/REPO_PROVENANCE.md:3` — still says _"Follows the standard
  `tab -> live-defi-rollout -> staging -> main` flow"_. The `tab/<op>/N` model is RETIRED (per-slot clones), and the
  fleet default is now LDR → `main` DIRECT with staging bypassed.

## Todos

- [x] ✅ [BACKEND] P2. **Repoint or remove the 5 dead doc-references in shipped code.** For each of the 5 lines above,
      either point at the surviving SSOT (the concurrency contract and API-endpoint descriptions now live in
      `/codex/04-architecture/agent-orchestrator-overview.md` + the worker-liveness doc — confirm before citing) or
      delete the dangling clause if the docstring stands on its own. **Do NOT resurrect the deleted files.** **Gate**:
      `rg -n 'AUDIT_FINDINGS_2026_05_18|docs/PLAN\.md|MAIN_AGENT_CUTOVER_REVIEW' agent-orchestrator/server/` returns
      zero hits, and each replacement pointer resolves to a file that exists. — **DONE** `agent-orchestrator@367252219`
      (2026-07-24 06:11:16Z, "fix(docs): repoint dead docs/PLAN.md, AUDIT_FINDINGS, and MAIN_AGENT_CUTOVER_REVIEW refs
      in server/"). **Gate re-measured 2026-07-26 (/plan-reconcile ao)**: the exact `rg` command returns **zero hits**
      (exit 1) over `agent-orchestrator/server/`.
- [x] ✅ [DOCS] P3. **Fix `README.md`'s directory tree + the 2 inline `agents/*.md` links.** The `agents/` dir is gone;
      role prompts live in `unified-trading-pm/agents/`. Replace the tree section with a pointer rather than re-listing
      files that will drift again. **Gate**: every path in README.md's tree resolves; no link to a nonexistent `agents/`
      file. — **DONE** `agent-orchestrator@f52b223cd` (2026-07-24 06:19:27Z, "docs: replace README agents/ tree with a
      pointer to unified-trading-pm/agents/"). **Gate re-measured 2026-07-26**: `README.md:447-448` is now a pointer
      reading "no agents/ dir — REMOVED in agent-orchestrator@5eaea29; role boot prompts now live in
      unified-trading-pm/agents/"; the 2 inline links at `:365`/`:397` resolve to `unified-trading-pm/agents/main.md`
      and `…/review.md` (both exist); all 24 remaining tree paths resolve on disk.
- [x] ✅ [DOCS] P3. **Correct `REPO_PROVENANCE.md`'s branch-flow sentence** to the current model (per-slot clones →
      `live-defi-rollout`; LDR → `main` direct, staging bypassed by the per-repo `ldr_main` toggle). SSOT:
      `/codex/08-workflows/ci-cd-flow.md`. **Gate**: no `tab ->` flow description remains in the file. — **DONE**
      `agent-orchestrator@5d8cdc8ee` (2026-07-24 06:12:26Z, "docs: correct REPO_PROVENANCE branch-flow to per-slot
      LDR->main direct model"). **Gate re-measured 2026-07-26**: `rg 'tab ->'` on the file returns zero hits; line 3 now
      reads "no `tab` branch — that model is retired … promotion is `live-defi-rollout -> main` DIRECT, with `staging`
      bypassed via the per-repo `ldr_main` toggle".
- [x] ✅ [REVIEW] P2. **Correct the tracker's "0 dead links" Progress Log claim** in
      `ao_open_issues_consolidated_close_out_2026_07_17.md` to state the sweep's ACTUAL scope, so the line stops reading
      as fleet-wide proof. **Gate**: the entry names which commits swept what, and links this doc for the batch it
      missed. — **DONE (unified-trading-pm, this commit)**: the tracker's 2026-07-18 entry now carries a dated
      CORRECTION naming `ao@19766e7` (the deleting commit) vs `ao@3d2c0e6`/`ao@63d8284` (the different batch the sweep
      actually swept) and links this doc. Duplicate todo in
      `/plans/archive/2026_07/ao_remediation_b_code_chain_2026_07_23.md` flipped alongside (same finding, one fix).

## Lesson

**A per-file instruction list is not a delete list.** Tier-6 distinguished "banner", "repoint-then-split" and "keep — no
action" precisely because three files were load-bearing for code comments; the cleanup collapsed all ten into one
delete. When an audit's output is a per-file disposition table, the executing commit should quote each file's
disposition back — a single "cleanup — delete N artifacts" message cannot be checked against the instruction it is
implementing.

**And a summary line is not a measurement.** "0 dead links" was written from the intent of a sweep, not from re-running
the grep afterwards. The grep takes one second and would have caught all five.
