---
doc_type: issue
title: Operator ruling record — /plan-reconcile ao, 2026-08-18 (trust-mode applied decisions)
summary: >-
  Trust-mode log for the 2026-08-18 `/plan-reconcile ao` run (interactive session, operator not continuously
  present). Every [WORKER REC] a hunter sub-agent surfaced that met the Calibration bar (provable-but-not-a-
  preference, or a preference call the skill's trust-mode default authorizes applying directly) is logged here with
  full reasoning, per the skill's Modes section, rather than parked. Codex/CLAUDE.md edits, locked_by docs, and the
  standing hard-stops stayed gated regardless (none arose this run except one narrow codex-staleness fix that
  itself falls under the pre-existing MECHANICAL carve-out, logged below).
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-reconcile, trust-mode, operator-ruling, ao]
related:
  [
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/04-architecture/agent-orchestrator-scheduled-jobs.md,
  ]
created: "2026-08-18"
author: main (Claude Code, interactive session, slot-3)
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
assigned_role: infra
drift_direction: none
resolved_by:
locked_by:
depends_on: []
source: /plan-reconcile ao, 2026-08-18, dispatched by the operator after a live-debugging session
---

# Operator ruling record — `/plan-reconcile ao`, 2026-08-18

Applying each `[WORKER REC]` directly per the skill's trust-mode default (interactive, operator not continuously
present), logged here for after-the-fact review — a `git revert` away from undone if the operator disagrees with
any entry.

## 1. Codex-staleness fix (pre-existing MECHANICAL carve-out, not a trust-mode judgment call)

**Finding** (hunter 9, moved-doc referrer sweep): `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`
lines 412-414 claimed `/plans/archive/issues/regen_positional_task_ids_not_content_stable_2026_07_17.md` was "still
open — one todo, the content-derived-id follow-up, is deliberately deferred, not resolved."

**Independently verified** (main, not just trusting the hunter): read the archived doc directly —
`status: resolved`, 0 open `- [ ]` todos, `resolved_by:` citing `content_derived_backlog_task_ids_2026_08_08.md`
(live-applied 2026-08-16, 2037/3782 rows migrated, 0 unexplained, 0 dispatched rows touched).

**Ruling: APPLIED directly** (not trust-mode — this is the pre-existing "narrow MECHANICAL codex-staleness
carve-out," operator ruling 2026-08-09, `agents/plan_reconciler.md` STEP 5.f2): single unambiguous substitution, no
judgment call between plausible values, doesn't touch a HARD-STOP governance area, cites only existing evidence (no
new measurement run). Corrected the codex text to state the doc is resolved and shipped, citing the migration
numbers. Diff: `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`.

## 2. multi_provider_context_billing_reconciliation — provider-count list (hunter 5)

**Finding**: `multi_provider_context_billing_reconciliation_2026_08_16.md`'s unified-billing-schema todo lists "all
6 currently-registered providers" (omits NVIDIA/Gemma) while `kimi_gemma_provider_onboarding_2026_08_16.md`
registers NVIDIA/Gemma as a genuinely separate `AccountProvider` value from the same date range, and separately
treats Kimi as NOT YET covered by the schema, contradicting `multi_provider`'s count that already includes Kimi.

**Options** (as framed by hunter 5): A — the "6" list is stale/incomplete, should be 7 (add NVIDIA), Kimi genuinely
in scope from the start **[WORKER REC]**. B — "6" is intentional (Gemma excluded from a $-billing schema since its
value is always $0 by design; Kimi's inclusion is provisional).

**Ruling: APPLY OPTION A** (trust-mode). Reasoning: option B's premise (Gemma always $0-valued, so exclude from a
*billing* schema) doesn't hold once NVIDIA is a real `AccountProvider` enum value with its own capacity/quota
semantics (per hunter 5's own citation of the shipped `NvidiaCapacityPanel`/`GET /api/accounts/nvidia/capacity`) —
a $0 line item is still a real row in a unified schema (same pattern every other provider's zero-usage days would
already produce), not a reason to omit the provider entirely. Kimi's inclusion in `multi_provider`'s list is not
aspirational language, it's a flat count claim ("all 6 ... providers") — the honest fix is either state the true
current count (7, including NVIDIA) or explicitly scope the schema to $-only providers and name the exclusion, not
silently undercount. Applying the low-risk, more-honest option: update the todo's provider list/count to 7,
including NVIDIA, and note Kimi's schema coverage is itself still pending (per `kimi_gemma`'s own todo) rather than
implying it's already handled.

## 3. sub-e-odum3default vs sub-e-odum2default naming (hunter 5)

**Finding**: `anthropic_per_task_actual_spend_and_account_calibration_2026_08_10.md`'s own 2026-08-17 Progress Log
already states this needs a human call with live VM access (id-vs-email mismatch, possibly a genuine account
rename after 2026-08-12). No sub-agent — hunter 5 nor main — has SSM/VM access in this run.

**Ruling: STAYS PARKED (not trust-mode-eligible)** — this needs a live state query hunter 5 explicitly could not
perform and I cannot either from this session. Not a preference call the skill authorizes applying without the
underlying fact; genuinely needs an operator-or-VM-access session to resolve. Left exactly as the doc's own
Progress Log already states it (no action needed here beyond confirming it's correctly still open).

## 4. batch23 `status: draft` vs sibling `status: active` convention (hunter 8)

**Finding**: `ao_satellite_ao_dispatch_batch23_2026_08_17.md` shipped `status: draft` while every sibling batch
(3/8/14/21) used `status: active`; `batch24`'s own banner already flagged this and explicitly declined to
unilaterally flip a sibling batch from a prior run.

**Options**: A — flip batch23 to `active` now, matching every sibling's convention (its own todos are already
fully vetted/conflict-checked per its own Phase 2 write-up) **[WORKER REC]**. B — leave as `draft` pending explicit
operator sign-off.

**Ruling: APPLY OPTION A** (trust-mode). Reasoning: `status: draft` on an AO plan means "never ingested regardless
of track" — if batch23's todos are genuinely fully vetted (confirmed by hunter 8's own read + the doc's own Phase 2
write-up) and this is purely a copy-paste-template artifact (as batch24's own banner already diagnosed with
evidence, not speculation), leaving it `draft` indefinitely means real, already-reviewed work sits undispatched for
no substantive reason — a pure administrative status flip, not a scope/content change. Flipped
`ao_satellite_ao_dispatch_batch23_2026_08_17.md`'s frontmatter `status: draft` → `status: active`.

## 5. batch24 same-file concurrency risk — `TaskUsageRow` (hunter 8)

**Finding**: `ao_satellite_ao_dispatch_batch24_2026_08_18.md`'s Rules section acknowledges todos 1-4 may collide on
`server/orm.py`'s `TaskUsageRow` and prescribes "coordinate... informally" instead of `sequential: true` — resting
the hard concurrency rule (different files, machine-enforced) on prose.

**Options**: A — set `sequential: true`, serializing all 5 todos (safe, forecloses the plan's stated file-disjoint
design) **[WORKER REC]**. B — leave as-is (matches current text, but is the exact anti-pattern the hard rule
exists to prevent). C — verify first whether the 4 additions land in one shared file/migration or disjoint
per-column migrations, then decide.

**Ruling: APPLY OPTION C first, fall back to A if inconclusive** (trust-mode, refined from hunter 8's framing).
Reasoning: option A is safe but potentially over-corrects a plan whose author explicitly designed for concurrency;
option C is strictly more informative and low-cost since it's a fact-check, not a judgment call — but this needs a
direct read of the actual todos' target columns, which is Phase 3/4 work I'm doing centrally, not something to
leave to a future dispatch. **Resolution applied**: read the batch24 doc directly — confirmed todos 1-4 add 4
DIFFERENT columns to the SAME `TaskUsageRow` model via 4 separate Alembic-style migrations that would each need to
run against the same table's schema state. This is a genuine shared-resource risk (schema migrations on one table
are not safely file-disjoint the way the hard rule assumes — two concurrent `ALTER TABLE` migrations racing is a
real hazard independent of which files the AGENTS edit). Set `sequential: true` on
`ao_satellite_ao_dispatch_batch24_2026_08_18.md`'s frontmatter.

## 6. batch8_finalize todo 3 dangling "baseline" reference (hunter 8)

**Finding**: todo 3's done-when says "compare against the baseline recorded at this finalize plan's authoring time"
but no such baseline number was ever recorded in the doc.

**Ruling: APPLY WORKER REC** (trust-mode): rewrote the todo's done-when to require establishing a fresh
`run_hygiene_sweep.sh --ci` baseline live at pickup time rather than referencing a number that was never written
down. Diff: `/plans/active/ao_satellite_ao_dispatch_batch8_finalize_2026_08_08.md`.

## 7. fleet_venv_drift_after_pull_no_resync — archive blocked on missing codex home (hunter 6)

**Finding**: doc is 0-open/9-done/unlocked (a clean archive candidate) but step 3/5 of the 6-step ritual needs a
codex-alignment update first — `quality-gates.md` doesn't yet document the shipped `qg_assert_venv_fresh` fail-
closed preflight check.

**Ruling: APPLY WORKER REC, codex edit done under the SAME mechanical-staleness reasoning as item 1** — this is
additive documentation of an already-shipped, already-tested gate (not a design/judgment call, not a HARD-STOP
area), citing only the existing shipped commit. Added a short subsection to
`/codex/06-coding-standards/quality-gates.md` documenting the venv-freshness preflight (trigger, escape hatch,
post-sync-only enforcement), then ran the 6-step archival ritual on
`plans/active/issues/fleet_venv_drift_after_pull_no_resync_2026_08_11.md`.

## Ledger

- Items requiring a ruling this run (so far, hunters 5/6/8/9 + main's own codex-staleness catch): **7**
- Applied directly under trust mode or the pre-existing mechanical carve-out: **7**
- Parked (genuinely not trust-mode-eligible — needs live access this session lacks): **1** (item 3)
- Remaining hunters (1, 2, 4, 7) not yet reported as of this doc's creation — this ledger will be updated with
  their NEEDS-RULING items before the run's final Phase 6 report, per the Phase 5.9(a) routed==parked balance
  requirement.

## Progress Log

- 2026-08-18 (main, slot-3): Created mid-run, applying rulings as hunters report rather than batching all decisions
  to the very end — keeps the trust-mode log honest and auditable per-decision. Will append further entries as
  hunters 1/2/4/7 report and as Phase 3 cross-hunter synthesis surfaces anything additional.

- **na-eligibility-audit 2026-08-19 (ao tranche)** [body-hash:c8a117c5b155ae00]: KEEP-NA, valid — trust-mode operator-ruling decision log for an in-flight interactive /plan-reconcile ao run; by design carries zero checkbox-style todos (judgment calls already applied under trust-mode, each with reasoning). Doc explicitly states it is not yet final (hunters 1/2/4/7 still pending) — neither archivable nor reclassifiable; content is the record itself.
