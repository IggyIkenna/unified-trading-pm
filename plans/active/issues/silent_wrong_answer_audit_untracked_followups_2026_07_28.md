---
doc_type: issue
title: >-
  e2e-testing's 4-pillar schema/NaN checks are vacuous for 51 of 61 (asset_group, data_type) pairs and need a
  schema-contract decision — the untracked follow-up from silent_wrong_answer_audit_candidates_2026_07_20.md
summary: >-
  While closing silent_wrong_answer_audit_candidates_2026_07_20.md's one remaining todo (the 2 stashed features-service
  fixes — both resolved, see that doc's Progress Log), found its "Recommended handling" section named 2 more
  genuinely-open findings only as prose, never as a tracked `- [ ]` todo anywhere. **The P0 half (strategy-service's
  `pnl_input_builder.py` hardcoding every DeFi fill's gas price to 1 gwei) was EXTRACTED 2026-07-30 by operator ruling
  into its own dispatchable doc, strategy_service_gas_fee_reader_hardcodes_1_gwei_2026_07_30.md** — it was bounded and
  ready to ship, and did not belong behind an undecided design question. What remains here is that design question:
  P1 finding 9 — e2e-testing's `validate_shards_4pillar.py` pillar-2/3 (schema/NaN) checks are vacuous (they degrade to
  `row_count > 0`) for 51 of 61 (asset_group, data_type) pairs because no per-pair schema/NaN-tolerance contract exists
  to check against; the audit doc explicitly said it "needs a schema-contract decision" and left it for a follow-up
  that was never filed.
status: open
nature: issue
asset_group:
  [cross-cutting] # corrected 2026-07-29 (ag-closeout-audit orthogonality fix) -- was [defi, cross-cutting], a genuine
  # mistag: P1 (e2e-testing schema-contract gap, 51/61 asset_group x data_type pairs) is unambiguously cross-AG, and
  # parent_epic is infrastructure_master (cross-cutting's own scoping epic), not defi_master; already cited/covered as
  # cross-cutting content under Track 12 of cross_cutting_consolidated_closeout_2026_07_25.md. The DeFi-specific half
  # (the P0 gas-fee reader fix) left this doc on 2026-07-30, so cross-cutting is now the doc's only content, not just
  # its dominant one.
stage: [data]
repos: [e2e-testing]
scope: [engineer, admin]
tags: [silent-failure, 4-pillar, schema-contract, follow-up]
related:
  [
    /plans/archive/issues/silent_wrong_answer_audit_candidates_2026_07_20.md,
    /plans/active/issues/strategy_service_gas_fee_reader_hardcodes_1_gwei_2026_07_30.md,
    /plans/active/issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md,
  ]
created: 2026-07-28
last_updated: 2026-07-30
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2 # was P1 while this doc still carried the P0 gas-fee fix; the sole remaining todo is the P2 e2e-testing
# schema-contract decision, so the doc-level priority now matches its actual content (2026-07-30 split-out).
estimate_class: research
estimate_baseline_ai_days: 0.3 # was 0.5 — halved 2026-07-30, the gas-fee half of the work left this doc
estimate_calibrated_ai_days: 0.36
assigned_role: backend
drift_direction: neutral
depends_on: []
source: >-
  Surfaced 2026-07-28 while closing silent_wrong_answer_audit_candidates_2026_07_20.md's stashed-fixes todo (the audit
  doc's own "Recommended handling" #2/#4 prose, never converted to todos).
resolved_by:
locked_by:
locked_since:
---

# Silent-wrong-answer audit — the untracked schema-contract follow-up

## Todos

> **EXTRACTED 2026-07-30 — the P0 strategy-service gas-fee reader fix no longer lives here.** Operator ruled it out of
> this doc so a bounded real-money PnL bug is not gated behind the undecided schema-contract question below. It is now
> `/plans/active/issues/strategy_service_gas_fee_reader_hardcodes_1_gwei_2026_07_30.md` (`assigned_vm: planning`, P0,
> immediately dispatchable), re-verified against the current code and expanded with three follow-on defects the
> original one-line todo did not name. **Do not re-add a gas-fee todo here** — that doc is the single place it ships
> from. This doc now tracks ONLY the P2 e2e-testing schema-contract decision.

- [ ] [BACKEND] P2. **e2e-testing** — resolve the schema-contract decision `validate_shards_4pillar.py`'s pillar-2 (NaN)
      / pillar-3 (schema) checks need: they are vacuous (degrade to `row_count > 0`) for 51 of 61
      `(asset_group, data_type)` pairs because no per-pair schema/NaN-tolerance contract exists to check against. This
      is the harness MTDS quality-gates STEP 5.88 runs and the batch+live matrix delegates its batch verdict to, so the
      gap is load-bearing, not cosmetic. Source: silent_wrong_answer_audit_candidates_2026_07_20.md P1 finding 9 (the
      7th "safe survivor" — flagged as needing this decision, never actioned).

## Why this wasn't fixed inline

Both original findings were cross-repo (strategy-service / e2e-testing) — outside the filing session's assigned repo
(features-service) and its narrow mandate (reconcile 2 stashed features-service fixes). Filed per the "every follow-up
is a `- [ ]` todo, never prose" HARD RULE so archiving the parent audit doc doesn't silently drop them.

The remaining item stays `assigned_vm: NA` because it is a genuine design decision, not bounded work: nobody has
decided what the per-pair schema/NaN-tolerance contract should say, and "figure out how X should look" is a human
decision, not an AO todo (`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` §
"Dispatch-scope eligibility"). Once that contract is decided, wiring `validate_shards_4pillar.py` to enforce it is
ordinary dispatchable work and should be filed as its own todo against that decision's outcome.

## Progress Log

- **2026-07-30 (operator-ruled split-out)**: Extracted the P0 strategy-service gas-fee reader fix into
  `/plans/active/issues/strategy_service_gas_fee_reader_hardcodes_1_gwei_2026_07_30.md` (`assigned_vm: planning`, P0)
  so it is dispatchable immediately instead of being trapped behind the undecided schema-contract question that is the
  reason this doc is `assigned_vm: NA`. The new doc re-verified the claim against current code (the 1-gwei fallback,
  the dead `gas_fees/chain_id=…/` prefix, MTDS's real canonical write path) and added three follow-on defects the
  one-line todo here never named. Narrowed this doc's frontmatter to match what it actually still holds: `repos`
  `[strategy-service, e2e-testing]` → `[e2e-testing]`, `stage` `[strategy, data]` → `[data]`, dropped the
  `gas-fees`/`pnl-correctness` tags, `priority` P1 → P2, estimate halved. Docs-only, no code changed.

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — the P2 todo is explicitly a schema-contract DECISION ('no
  per-pair schema/NaN-tolerance contract exists to check against'). NOTE the P0 gas-fee reader fix IS bounded and
  specific — worth an operator call on splitting it out. (That call was made the same day — see the split-out entry
  above.)
