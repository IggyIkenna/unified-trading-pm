---
doc_type: codex-ssot
title:
  AO-dispatch batch/finalize naming convention, parent_epic grouping, the shared conflict-check protocol, and the
  NA-corpus ratchet
summary:
  "The SSOT for how `/ag-closeout-audit` and `/na-eligibility-audit` name the docs they draft, which frontmatter axis to
  group by, the ONE conflict-check procedure both skills run before dispatching reclassified/batched work, and the
  shrinking-ratchet gate that caps the `assigned_vm: NA` backlog so it cannot grow unattended."
status: current
nature: ssot
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [ao-dispatch, ag-closeout-audit, na-eligibility-audit, naming-convention, conflict-check, ratchet, plan-hygiene]
related:
  [
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /cursor-configs/skills/plan-reconcile/SKILL.md,
    /plans/active/task_template.md,
    /plans/active/na_docs_validity_and_ao_eligibility_audit_2026_07_26.md,
    /codex/11-project-management/doc-frontmatter-schema.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: 2026-07-27
authoritative_for:
  [
    AO-dispatch batch/finalize doc naming convention,
    parent_epic vs asset_group grouping semantics,
    AO-dispatch conflict-check protocol,
    assigned_vm:NA corpus size ratchet,
  ]
referenced_by:
  [
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /cursor-configs/CLAUDE.md,
    /plans/active/task_template.md,
  ]
owner: agent_operating_framework_master
last_reviewed: 2026-07-27
code_refs:
  [
    scripts/plan-hygiene/generate_na_doc_tranche_inventory.py,
    scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py,
    scripts/plan-hygiene/check_na_corpus_ratchet.py,
  ]
---

# AO-dispatch batch naming, grouping, conflict-check, and the NA-corpus ratchet

## 1. Two naming shapes — not one

Every `assigned_vm: planning` doc in the corpus was created one of two ways, and the shape tells you which:

**(a) Fresh carve-out (`/ag-closeout-audit` Phase 3 / `/na-eligibility-audit` Phase 2).** A NEW doc named
`{ag}_satellite_ao_dispatch_batch{N}_{date}.md` (or `_consolidated_native_ao_extract_`, `_closeout_track_{x}_`,
`_track{N}_{topic}_` for the AG-specific variants), always shipped with a paired gated twin — same stem + `_finalize`
(position varies: `{stem}_{date}_finalize.md` or `{stem}_finalize_{date}.md`, both seen live; the ordering is cosmetic)
— carrying `depends_on: [<source-doc-slug>]` + `gate_on_depends: true`, authored `status: active` from the start per the
2026-07-30 no-double-gate ruling — `gate_on_depends` alone machine-holds every task until the source plan's todos are
done (a `status: draft` twin would double-gate).

**(b) Retroactive reclassification (`/na-eligibility-audit` Phase 1).** An EXISTING doc (any name, any age) gets its own
`assigned_vm` flipped `NA → planning` **in place — name unchanged** — and gets a bolt-on
`{original-stem}_finalize_{today}.md` sibling, dated the day of the reclassification pass, tagged
`[ao-dispatch, close-out, reclassification, na-audit]`.

**The filename is not the ground truth for pairing — `depends_on` is.** A (source, finalize) pair can carry different
dates (confirmed live: `infra_capture_and_devops_leftovers_2026_07_06.md`'s finalize twin is dated 19 days later) or a
different finalize-token position. Never infer pairing from string-matching the filename; read `depends_on` on the
candidate finalize doc.

## 2. Grouping — `parent_epic`, not `asset_group`, is the clean axis

`parent_epic` is single-valued and maps 1:1 onto a real `plans/epics/{parent_epic}.md` — use this to bucket docs.
`asset_group` is a multi-value list and, for content that isn't one specific AG, is split three inconsistent ways:
`cross-cutting`, `meta`, and `infrastructure` all mean roughly "spans many ANs or none," with no single canonical value.
`/ag-closeout-audit`'s own tranche-membership rule already had to special-case this (its `ao`/`ci`/`infra` tranches
sweep `asset_group: infrastructure` and `asset_group: meta` in addition to `cross-cutting` — see that skill's own
"Total-coverage gap" note). Any new tooling grouping this corpus should follow the same rule: don't trust `asset_group`
alone for the non-AG bucket; check `infrastructure`/`meta` too, or group by `parent_epic` instead.

## 3. The shared AO-dispatch conflict-check protocol

Both `/ag-closeout-audit` (drafting a new satellite batch out of orphaned docs) and `/na-eligibility-audit`
(reclassifying an `NA` doc's open todos to `planning`) create or activate content that could duplicate work already
queued elsewhere in the live backlog. Before either skill converts a candidate todo into dispatchable
`assigned_vm: planning` content, run this ONE procedure — do not re-derive a parallel version in either skill's own
prose:

1. **Enumerate the candidate's real claim** — what file(s)/mechanism does this todo actually change, not just its
   one-line title (two todos with different titles can still be the same underlying fix).
2. **Check four surfaces for a prior claim on the same ground**: (a) every currently-`status: active`,
   `assigned_vm: planning` plan's own open todos in the same `parent_epic`; (b) any sibling batch/finalize doc already
   drafted or activated in the SAME audit run (a batch1 and a batch2 drafted minutes apart can overlap); (c) the
   tranche's own `{tranche}_consolidated_closeout_*.md` — its "aggregated source docs" section is a digest, not a
   dispatch claim, but its own Track content can still duplicate a candidate; (d) any `status: draft`
   `{ag}_satellite_ao_dispatch_batch{N}_*.md` for the same tranche, from EITHER `/ag-closeout-audit` or
   `/na-eligibility-audit`'s prior runs (not just the current run) — grep its
   `Source:`/`## Deferred`/`## Already covered` citations for the candidate doc's path before finalizing a RECLASSIFY or
   drafting a new extraction.
3. **Verdict**: **zero or milestone-only overlap** → clear, proceed. **Verbatim or near-verbatim duplicate claim** →
   CONFLICT — do NOT draft a competing todo and do NOT silently prefer one side. Preserve the conflicted item in a
   **Deferred** section with both sides cited, and queue it for an explicit operator ruling
   (`plans/active/issues/autonomous_session_operator_decisions_*.md` or the run's own escalation path) — never resolve a
   conflict by guessing which claim should win.
4. **Already-shipped elsewhere, checkbox just never flipped** (a distinct, non-conflicting outcome — the
   `na_docs_validity_and_ao_eligibility_audit_2026_07_26.md` plan's own "KEEP-NA-STALE" bucket) → this is a
   stale-checkbox correction, not a reclassification and not a conflict: cite the extracting doc's commit/sha against
   the stale checkbox, leave `assigned_vm` as-is.

This protocol is what produced the sports-batch3 conflict split (23 of 25 candidates held back over a flagged overlap
with `sports_consolidated_closeout_2026_07_19.md`) and what the NA-audit plan ran ad hoc before every `NA → planning`
flip. Neither skill's own file should restate steps 1-4 — reference this section instead.

## 4. The `assigned_vm: NA` corpus size ratchet

**Why**: `assigned_vm: NA` is the correct home for genuinely operator-gated, investigation-based, or open-judgment work
— most of it is (`na_docs_validity_and_ao_eligibility_audit_2026_07_26.md`'s own sampling: roughly two-thirds of
reviewed NA docs are dated, evidenced KEEP-NA calls, not defaults). The goal is never "drive NA to zero" — that would
misclassify genuine judgment calls as mechanical work. The goal is **the NA backlog must not grow unattended**: new NA
content is fine when it's genuinely NA-worthy, but it should be offset by triaging (reclassifying or archiving) existing
NA content, not just accumulated net over time without anyone ever running the audit that would catch a stale or
mis-defaulted entry.

**Mechanism**: `scripts/plan-hygiene/check_na_corpus_ratchet.py`, baselined against
`scripts/plan-hygiene/na_corpus_baseline.yaml` — a SHRINKING ratchet on two numbers (doc count + total open-todo count
across every `assigned_vm: NA` + `status` ∈ `{active, open}` doc, same population `generate_na_doc_tranche_inventory.py`
already computes). A run that finds either number ABOVE the baseline fails; only `--update-baseline` after a genuine
`/na-eligibility-audit` or manual triage pass (never to launder a run that just found the backlog grew) may lower it.
Wired into `run_hygiene_sweep.sh` alongside the other shrinking ratchets (`doc_reference_baseline.yaml`,
`doc_body_link_baseline.yaml`, line-caps).

**A hand-raised baseline is a real signal, not noise** — if a legitimate spike in new NA work forces a deliberate raise,
that raise should be visible in the commit message with why, same convention as any other ratchet exception in this
corpus.
