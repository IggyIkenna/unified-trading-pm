---
doc_type: issue
title: "Operator ruling record — gcloud WIF-poisoning durable-direction decision, 2026-08-08"
summary: >-
  Durable, citable home for the single operator ruling closing
  `orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md`'s head `[OPERATOR-DECISION]` todo (option (b), a
  non-shared credential file per job). That todo cited only "operator ruling 2026-08-08" with no traceable
  `/plans/…`/`/codex/…`/`.md` pointer — a source nothing in the corpus could resolve, tripping
  `check_plan_operator_ruling_evidence.py` the moment the round-11 sweep touched that file for an unrelated append. The
  ruling text is transcribed VERBATIM from the citing todo; nothing is reconstructed, inferred, or added. This gives the
  citation a traceable home, per the same pattern established by
  `operator_ruling_record_ao_round5_apply_session_2026_08_08.md` — it is NOT a substitute for the operator confirming it
  is accurate.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [admin]
tags: [operator-ruling, evidence, plan-hygiene, quality-gates, findings-triage]
related:
  [
    /plans/active/issues/orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md,
    /plans/active/issues/operator_ruling_record_ao_round5_apply_session_2026_08_08.md,
    /plans/archive/2026_08/issues/tradfi_finding_e1_unsourced_operator_ruling_citation_2026_08_03.md,
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-09
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
assigned_role: admin
drift_direction: advance-docs
resolved_by:
locked_by:
source: >-
  Round-11 ci-tranche RECLASSIFY sweep, 2026-08-09 — filed to unblock a `check_plan_operator_ruling_evidence.py`
  precommit failure hit while adding an unrelated round-11 marker to
  `orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md`, whose head todo cited an untraceable "operator
  ruling 2026-08-08" with no corpus pointer.
depends_on: []
---

# Operator ruling record — gcloud WIF-poisoning durable-direction decision

## Provenance — read this before citing this doc

**This is a transcription, not a transcript.** The ruling below is copied verbatim from the todo that already quoted it
(`orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md`'s head `[OPERATOR-DECISION]` todo); the citing doc and
location are named so the original wording is one `grep` away. Nobody re-derived, guessed at, or extended it.

**What this doc does and does not settle.** It settles _traceability_ only — a reader can now find the ruling and see
exactly which todo claims it. It does **not** settle _authenticity_ — only the operator can confirm it was really issued
as quoted. That distinction is the whole point of the gate this doc exists to satisfy
(`/plans/archive/2026_08/issues/tradfi_finding_e1_unsourced_operator_ruling_citation_2026_08_03.md` is the precedent: an
unsourced ruling citation is ambiguous between a missing-citation bug and a worker overriding an `[OPERATOR]` gate, and
a third party cannot tell which from the outside). The confirmation todo below stays open until the operator answers.

## The ruling, as cited

- **Durable direction for the shared `~/.config/gcloud` active-account poisoning** — _"option (b) — non-shared
  credential file per job."_ Cited by
  `/plans/active/issues/orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md`'s head `[OPERATOR-DECISION] P1`
  todo ("**RESOLVED 2026-08-08 -- operator ruling: option (b), a non-shared credential file per job.**"), which lists
  the 4 candidate directions (a)-(d) it chose among: (a) extend `CLOUDSDK_CONFIG` isolation to workflow job steps, (b)
  move `unified-trading-sa`'s activation to a non-shared `GOOGLE_APPLICATION_CREDENTIALS` file, (c) stop dual-purposing
  the VM as a self-hosted runner pool, (d) a periodic self-heal cron.

## Todos

- [ ] [OPERATOR] P2. **Confirm this ruling is accurate as transcribed, or correct it.** It is quoted verbatim from the
      todo that applied it, but only the operator can confirm it was really issued this way — the two unresolved
      implementation todos it unblocks (Part 1/2 of the credential-file migration, plus the ADC-backed-client extension)
      both rest on this decision being real. **Done when**: this doc records the confirmation (or correction), dated.
      Repo: unified-trading-pm.

## Progress Log

- **2026-08-09 (round-11 ci-tranche RECLASSIFY sweep)** — Created to unblock a `check_plan_operator_ruling_evidence.py`
  precommit failure hit while appending an unrelated round-11 KEEP-NA marker to
  `orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md`. Deliberately scoped to transcription only — the
  ruling is copied verbatim from its citing todo and attributed to that doc, so this adds traceability without adding
  authority. Authenticity confirmation is tracked as the open `[OPERATOR]` todo above, not assumed.

## na-eligibility-audit verdict

**na-eligibility-audit 2026-08-10** (ci tranche, autonomous, dispatch agt-74eff9) [body-hash:6896a5b27835b713]: KEEP-NA,
valid — grep confirms exactly 1 open todo (line 72), matching the phase0 figure. Brand-new doc (created 2026-08-09, no
prior audit marker) whose entire purpose is to hold a transcribed operator ruling ('option (b), a non-shared credential
file per job') and its confirmation. The doc's own text is explicit that it settles traceability only, not authenticity
-- 'only the operator can confirm it was really issued as quoted.' The sole todo is explicitly [OPERATOR]-tagged and
cannot be resolved by a worker. Genuinely operator-gated by design. KEEP_NA_VALID.
