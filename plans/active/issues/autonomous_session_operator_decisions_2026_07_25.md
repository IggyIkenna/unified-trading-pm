---
doc_type: issue
title: Autonomous session 2026-07-25 — queued operator decisions
summary: >-
  Single running log of every genuine operator-decision-caliber question surfaced during the 2026-07-25 /autonomous
  session (plan-of-record: ag_closeout_audit_rollout_2026_07_25.md). Per the operator's explicit instruction at session
  start ("you have to ask me operator questions for decisions... so that i can answer when im back"), these are QUEUED —
  never blocked on — and the session keeps working on everything else. Each entry follows the
  SUB_AGENT_MANDATORY_RULES.md escalation format (options + a marked recommendation). Operator: answer inline under each
  entry (or via chat) when back; unanswered entries stay open.
status: open
nature: issue
asset_group: [cefi, defi, tradfi, prediction, sports, cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [autonomous, operator-decision, ag-closeout-audit]
related:
  - /plans/active/ag_closeout_audit_rollout_2026_07_25.md
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: agent_operating_framework_master
assigned_vm:
priority: P1
locked_by:
resolved_by:
source: >-
  Operator instruction 2026-07-25 immediately after /autonomous invocation: queue genuine decisions instead of silently
  deciding or blocking.
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# Autonomous session 2026-07-25 — queued operator decisions

## 1. `git rm` 2 stale-duplicate stub files (2026-07-25, sports archival)

Not a judgment call — a mechanically-safe delete blocked by a hard guardrail
(`agent-orchestrator/scripts/hooks/block_destructive_commands.py`) that forbids `git rm` for autonomous workers,
correctly. A concurrent commit (`9aed72662`, unrelated tradfi work) picked up the ADD half of a `git mv` archival rename
but not the DELETE half, leaving stale full-content duplicates at the OLD paths alongside the correct archived copies.
Both stale files were overwritten with an explicit `⚠️ STALE DUPLICATE` stub + a queued `[OPERATOR]` todo (so they're
self-explanatory and harmless in the meantime) rather than left as confusing full duplicates.

A:
`git rm plans/active/sports_closeout_batch1_finalize_2026_07_24.md plans/active/data_completion_sports_history_2026_07_24.md`
— removes both stub files; the real content already lives at `plans/archive/2026_07/`. [WORKER REC] B: Leave the stubs
in place — they're self-documenting and harmless, just slightly noisy in `plans/active/`. Other: operator can type a
custom answer

**Status**: open

---

## 2. `gas_fees_lst_rates_manifest_bucket_mismatch_2026_07_10.md` — locked doc, audit says resolved (2026-07-25, defi)

The defi orphan-audit classified this doc `archivable_now`: its own latest section (2026-07-12) claims one item still
open (`e2e-testing/staked_basis_funding_scan.py`'s `_lst_bucket()`/`_read_lst_exchange_rate` reader), but that claim
looks stale — sibling plan `defi_dedicated_bucket_shared_migration_2026_07_13.md`'s Todo 3 (checked `[x]`, 2026-07-13)
explicitly fixed that exact function, with a live-verified post-deploy parity todo (2026-07-13/14: "e2e
`_read_lst_exchange_rate` LIDO 1.2333 + JITO 1.2766 ... zero reads left on the dedicated buckets"). I did NOT flip this
doc's frontmatter — it carries `locked_by: live-defi-rollout` (`locked_since: 2026-05-21`), an explicit human "not
yours" signal per CLAUDE.md's plan-locking rule, which I'm treating as applying here even though this is an issue-doc
status flip, not a plan archival — the lock predates this session and I have no context on why it's held.

A: `[unlock-plan]` + flip `status: resolved` with
`resolved_by: <the defi_dedicated_bucket_shared_migration commit that shipped Todo 3>` — the evidence looks solid, this
just needs the lock cleared first. [WORKER REC] B: Leave locked and open — the lock may be protecting something I don't
have context on (e.g. active investigation, pending a different fix). Confirm with whoever set the lock before touching
it. Other: operator can type a custom answer

**Status**: open

---

## 3. Kamino/Solend `lending_indices` `instrument_type` shape — writer code vs live GCS probe disagree (2026-07-25, defi)

`issues/defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md`'s follow-up todo ("does the
dex_pools-class fake-history-snapshot bug also affect Kamino/Solend Solana lending_indices in the `-prd-` bucket")
asserts the CORRECT real path shape to probe is `instrument_type=solana_lending`, citing
`market-tick-data-service/market_tick_data_service/cli/handlers/lending_indices_handler.py::resolve_lending_instrument_type()`
as ground truth (Kamino/Solend resolve to `InstrumentType.SOLANA_LENDING`). But
`defi_consolidated_closeout_2026_07_18.md`'s Track 2 independently reports a 2026-07-20 live GCS probe finding a KAMINO
`lending_indices` canonical twin (47 objects) actually sitting under `instrument_type=solana_amm_pool` at
`day=2026-04-14` — a THIRD, different path shape from both the already-known-wrong `instrument_type=pool` and this
todo's targeted `solana_lending`. Neither doc has cross-checked the discrepancy against the other. The conflict-check
run over the 2026-07-25 defi satellite AO-eligibility triage explicitly flagged this as needing operator sign-off rather
than a silent reconciliation — if a worker probes only `solana_lending` as originally scoped, it risks filing a false
"clean bill" finding while missing the population Track 2 actually found live under `solana_amm_pool`.

A: Widen the todo's scope to ALSO probe `instrument_type=solana_amm_pool` for KAMINO/SOLEND before filing any "clean
bill" finding, explicitly reconciling against Track 2's 2026-07-20 47-object finding. [WORKER REC] B: Dispatch the todo
exactly as scoped (probe only `solana_lending`) and accept the risk that the finding may be incomplete if real
Kamino/Solend `lending_indices` data actually lives under `solana_amm_pool` instead. C: Hold this todo out of any AO
batch entirely and rule directly on which `instrument_type` shape (`solana_lending` vs `solana_amm_pool`) is
authoritative for Kamino/Solend `lending_indices`, since the writer code and the live GCS probe currently disagree.
Other: operator can type a custom answer

**Status**: open

---

No further entries yet. This doc will accumulate entries as genuine judgment calls surface during the
cefi/defi/tradfi/prediction closeout-audit rollout. Format for each entry:

```
## <N>. <short title> (<date>, <AG/doc context>)

<question text — both sides cited as path:line + quote, why they conflict, which side looks authoritative and why>

A: <option — recommendation marked here if applicable> [WORKER REC]
B: <option>
Other: operator can type a custom answer

**Status**: open
```
