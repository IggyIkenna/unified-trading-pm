---
doc_type: plan
title: CeFi misc audits + hygiene — UAC fallback decision, reconciliation spot-check, archival
summary: >-
  3 independent, ungated todos on different files/repos forked from cefi_consolidated_closeout_2026_07_18.md's "Operator
  dispositions" section (2026-07-25 split): the `[OPERATOR]`-gated UAC per-venue seed fallback removal decision, a
  bounded spot-check slice of the GCS/manifest/UI reconciliation-gap doc, and archival of the one cefi issue doc still
  genuinely awaiting it (`cefi_layer1_denominator_gaps_2026_07_03.md` — its sibling
  `betfair_instrument_id_delimiter_cross_repo_2026_07_08.md` is already archived, confirmed during this split). Every
  other candidate originally considered for this plan (the ccxt/native adapter audit, the non-Tardis VM sweep, the
  UAC-fallback blast-radius audit, the data-status axis-value-census quickmerge, the UPBIT wiring check) is already
  drafted in cefi_consolidated_native_ao_extract_2026_07_25.md — deliberately NOT duplicated here.
status: draft
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-api-contracts, instruments-service, unified-trading-pm]
scope: [engineer]
tags: [cefi, close-out, hygiene, audit, archival]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md,
    /plans/archive/issues/cefi_layer1_denominator_gaps_2026_07_03.md,
    /plans/active/cefi_misc_audits_and_hygiene_finalize_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.5
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Forked from cefi_consolidated_closeout_2026_07_18.md's "Operator dispositions" section, 2026-07-25 split — path 4 of
  that parent's 4 reachability paths, the misc-audit path. Deliberately smaller than the design pass's initial ~8-todo
  estimate: cross-checking against cefi_consolidated_native_ao_extract_2026_07_25.md (a parallel sibling triage of this
  same parent's native todos) found 5 of the originally-considered candidates already drafted there — excluded here to
  avoid duplication, per the explicit cross-check requirement for this split.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# CeFi misc audits + hygiene

> **Ungated, independent todos on different files/repos** — the default per `task_template.md` §4, safe to dispatch
> concurrently. **Why only 3 todos (deliberate, not an oversight).** The original design pass estimated ~8 todos for
> this plan; cross-checking against `cefi_consolidated_native_ao_extract_2026_07_25.md` (drafted by a parallel sibling
> triage of this same parent's native todos) found 5 already covered there: the `*_ccxt.py`/`*_native.py` adapter audit
> (Track 5), the non-Tardis VM sweep (Track 6), the UAC per-venue-seed-fallback blast-radius audit, the data-status
> axis-value-census quickmerge (Track 8), and the UPBIT wiring check (MVP universe). Re-drafting any of them here would
> duplicate dispatchable work. Companion gated finalize: `cefi_misc_audits_and_hygiene_finalize_2026_07_25.md`.

## Todos

- [ ] [OPERATOR] P1. **Decide whether to remove the UAC per-venue seed fallback**
      (`unified_api_contracts.registry.market_data_categories.get_expected_instruments_for_venue`'s fallback to the
      per-venue MVP seed when a present catalogue lacks a venue), using the blast-radius caller list produced by
      `cefi_consolidated_native_ao_extract_2026_07_25.md`'s own UAC-fallback-audit candidate (once it ships). The
      operator's "catalogues should be the sole source" ruling (already applied to the wholesale MTDS fallback removal)
      points toward removal, but this is a UAC change with fleet-wide blast radius — an operator/interactive call on
      acceptable risk, not a background-dispatchable decision. Non-dispatchable (`[OPERATOR]`, per `task_template.md`
      §3) — stays visible for the operator to act on directly. Repo: unified-api-contracts. **Done when**: the ruling is
      recorded in this plan's Progress Log, then executed as a follow-up todo if the ruling is "remove."
- [ ] [VERIFY] P2. **Spot-check the next 3 unverified findings in
      `issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md` across GCS/manifest/UI**
      (the bounded half only — re-scoped from the source todo's open-ended "decide the reconciliation cadence" half,
      which stays a human/policy decision recorded in that issue doc, not dispatched here). Reuse the doc's own
      established spot-check methodology. Repo: instruments-service. **Done when**: each of the 3 findings has a
      recorded PASS/FAIL consistency verdict (GCS vs manifest vs UI) cited in the issue doc's Progress Log, and the doc
      explicitly still flags the cadence-decision half as open/human.
- [x] ✅ [PM] P1. **Archive `issues/cefi_layer1_denominator_gaps_2026_07_03.md`** (confirmed during this split: 0
      checkbox-syntax open todos of its own — a 1000-line narrative/findings doc whose actionable items were already
      forked into other docs, still carrying `status: open`) via the standard 6-step archival ritual. **Scope note**:
      its sibling `issues/betfair_instrument_id_delimiter_cross_repo_2026_07_08.md` is ALREADY archived (verified during
      this split, `plans/archive/issues/`) — no action needed there, do not re-archive. Also re-scoped from the source
      todo's broader "pull forked-elsewhere todos into THIS plan" + "any other otherwise-complete cefi plans" asks, both
      open-ended with no defined target list — those stay a human/PM judgment call in
      `cefi_consolidated_closeout_2026_07_18.md`, not dispatched here. Repo: unified-trading-pm. **Done when**:
      `cefi_layer1_denominator_gaps_2026_07_03.md` is confirmed 0-open-todos, `status` flipped to `resolved`, moved to
      `plans/archive/issues/`, every corpus referrer's path fixed, and this plan's Progress Log cites the commit. ✅ —
      unified-trading-pm@(this commit). A deeper cross-doc investigation (dispatched agent, full 1000-line read + every
      prose-described residual gap traced to a sibling doc) confirmed safe: OKX-SPOT Option-A/B decision lives in
      `instruments_service_cefi_qg_red_on_ldr_head_2026_07_08.md`; DERIBIT-COMBO real-row capture is gated on
      `tardis_concurrent_ip_lockout_2026_07_12.md`; v1-enumerator retirement + DERIBIT-COMBO catalogue backfill are
      fully shipped. Moved to `plans/archive/issues/`, `status: resolved`, 20 corpus referrers fixed (3 archived
      "plan_reconciliation_operator_decisions_history_part*" docs intentionally left citing the OLD active-path — they
      are frozen historical records of findings at the time, not live pointers). **Separate finding surfaced, NOT this
      todo's scope — flagged to the operator instead**: `bybit_spot_manifest_stray_captures_2026_07_07.md` was flipped
      `resolved` 2026-07-14 on checkbox-only evidence, but a 2026-07-10 live-manifest read
      (`instruments_remaining_work_audit_2026_07_10.md` item 7) found the actual `--apply` relabel/delete was never run
      against production (135,444 anomalous BYBIT-SPOT rows unchanged) — likely needs its status corrected + the
      remediation actually re-run, independent of this archival. **CLOSED 2026-07-26**:
      `cefi_bybit_spot_manifest_remediation_2026_07_25.md` re-verified, ran the real `--apply` (53,934 spot-nonsense
      rows deleted, verified via `by_data_type` + `measure_honest_coverage.py` -- 0 remaining BYBIT-SPOT stray tuples),
      and added a closure addendum to the archived issue doc confirming its `status: resolved` is now genuinely accurate
      to live production state, not just to checkbox history. No further action needed on this finding.

## Reconciliation

Once this plan's todos ship, flip the 3 corresponding checkboxes in `cefi_consolidated_closeout_2026_07_18.md` (Operator
dispositions' UAC-fallback-decision item, the reconciliation-gap `[VERIFY]` item, the consolidate+archive `[PM]` item),
citing evidence. Gated via the companion `cefi_misc_audits_and_hygiene_finalize_2026_07_25.md`
(`depends_on: [cefi_misc_audits_and_hygiene_2026_07_25]` — `gate_on_depends: true`).

## Codex SSOTs

No new durable contract is created by this plan — every todo executes an already-decided spec from the parent doc, or is
a bounded audit feeding a still-open human decision recorded there.
