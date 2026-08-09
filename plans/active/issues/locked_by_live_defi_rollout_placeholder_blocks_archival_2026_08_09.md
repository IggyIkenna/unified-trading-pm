---
doc_type: issue
title:
  "22 active docs share the identical locked_by: live-defi-rollout / locked_since: 2026-05-21 pair — looks like a
  placeholder value, not a genuine human lock, and is blocking at least 2 confirmed-done docs from archival"
summary: >-
  Found while auditing an archival candidate in the cefi tranche (`cefi_coinbase_cde_urdi_zero_records_2026_07_28.md`):
  its `locked_by: live-defi-rollout` / `locked_since: 2026-05-21` looked anomalous (a branch name, not a
  person/slot/session identifier, predating the doc's own `created: 2026-07-28` by over 2 months). Corpus-wide grep
  found the IDENTICAL pair on 22 active docs total (5 cefi-tagged, 17 other tranches) — same value, same date, verbatim.
  This is not one doc's stale lock; it reads as a systemic placeholder (a migration/setup-script default, or a
  copy-paste seed value) that was never meant to function as a real archival-blocking lock, but the corpus's tooling
  (`check-locked-plan-deletion.sh` and this skill's own archival gate) can't distinguish it from a genuine one. At least
  2 of the 22 (`cefi_coinbase_cde_urdi_zero_records_2026_07_28.md`,
  `features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md`) are otherwise fully-done,
  unlocked-in-substance archival candidates (0 open todos each, verified) currently blocked from the standard archival
  ritual purely by this lock.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, locked_by, archival, false-lock, corpus-wide, governance]
related:
  [
    /plans/active/issues/cefi_coinbase_cde_urdi_zero_records_2026_07_28.md,
    /plans/active/issues/features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-09"
author: plan_reconciler (agt-51e4bd, slot 9, cefi tranche run)
source: "plan_reconciler cefi tranche run, agt-51e4bd, slot 9, 2026-08-09 — found while auditing an archival candidate"
priority: P2
parent_epic: plan_hygiene_master
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.2
assigned_role: review
assigned_vm: NA
execution_scope: local-only
drift_direction: none
depends_on: []
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    unified-trading-pm/scripts/plan-hygiene/check-locked-plan-deletion.sh,
  ]
---

# `locked_by: live-defi-rollout` / `locked_since: 2026-05-21` — a corpus-wide placeholder value blocking archival

## What I found

Auditing `cefi_coinbase_cde_urdi_zero_records_2026_07_28.md` as an archival candidate (all 3 todos `[x]` done, most
recent 2026-07-30), its frontmatter carries:

```yaml
locked_by: live-defi-rollout
locked_since: 2026-05-21
```

Two things are wrong with this as a genuine lock:

1. `locked_by` values elsewhere in the corpus are person/slot/session identifiers (e.g. `plan_reconciler`, a slot
   number, an operator name) — `live-defi-rollout` is the **integration branch name**, not an identity.
2. `locked_since: 2026-05-21` predates the doc's own `created: "2026-07-28"` by over two months — a doc cannot have been
   locked before it existed.

A corpus-wide grep for the exact same pair found **22 active docs** carrying this identical `locked_by`/`locked_since`
combination verbatim:

```
plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md
plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md
plans/active/issues/ag_closeout_audit_ui_parked_2026_08_09.md
plans/active/issues/cefi_coinbase_cde_urdi_zero_records_2026_07_28.md
plans/active/issues/backfill_vm_slack_alert_e2e_verification_2026_06_23.md
plans/active/issues/bybit_futures_chain_write_shape_2026_07_13.md
plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md
plans/active/issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md
plans/active/issues/deribit_options_chain_af_g4_blocker_2026_07_03.md
plans/active/issues/features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md
plans/active/issues/quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md
plans/active/ui_satellite_ao_dispatch_batch1_2026_08_06.md
plans/active/issues/ao_park_disposition_blocked_answer_no_follow_through_2026_07_31.md
plans/active/issues/defi_bridge_events_historical_backfill_gap_2026_07_28.md
plans/active/issues/defi_lst_oracle_timestamp_glued_instrument_id_2026_07_20.md
plans/active/issues/instruments_service_sports_footystats_uac_overlap_qg_red_2026_07_30.md
plans/active/issues/long_lived_vm_logs_not_backed_up_2026_07_02.md
plans/active/issues/live_pipeline_persistence_hot_path_decoupling_2026_06_24.md
plans/active/issues/macro_micro_econ_data_capture_audit_2026_06_05.md
plans/active/issues/tradfi_canonical_path_migration_design_2026_07_19.md
plans/active/issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md
plans/active/issues/tradfi_recovery_quarantine_registration_gap_2026_07_27.md
```

Spanning 6+ different asset_groups/tranches (cefi, defi, tradfi, ui, meta, plus unlabeled), created dates from
2026-06-05 through 2026-08-09 (i.e. it isn't confined to one authoring session/batch either — new docs keep getting the
same value). This pattern is corpus-wide, not tranche-specific — flagged here rather than fixed inline in the cefi run,
per the "findings outside your scope get filed, not silently fixed" triage rule.

## Why this matters (concrete, not hypothetical)

Verified 2 of the 22 are otherwise genuine, fully-done archival candidates blocked ONLY by this lock:

- `cefi_coinbase_cde_urdi_zero_records_2026_07_28.md` — 0 open todos (all 3 `[x]`, most recent 2026-07-30),
  `status: open` (should be terminal).
- `features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md` — 0 open todos (all 5 `[x]`),
  `status: open`.

Per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` and this workspace's HARD RULE, `locked_by:`
blocks auto-archival without an explicit `[unlock-plan]` — correctly so for a REAL lock, but this value doesn't read as
one, and mechanically clearing it without confirming that is exactly the kind of authority-only action a plan_reconciler
run should route to the operator, not silently override.

I have not surveyed all 22 for archival-readiness (17 are outside the cefi tranche this run is scoped to) — the 2 above
are cefi-tranche-confirmed; the remaining 20 need the same 0-open-todos check before assuming they're also
archival-ready once unlocked.

## What I did NOT do

- Did not clear `locked_by` on any of the 22 docs (including the 2 cefi ones) — this is an explicit human-signal field
  per the HARD RULE, and I cannot rule out that some subset of these locks are genuine despite the suspicious shared
  value (e.g. a bulk `[lock-plan]` operation that happened to run on 2026-05-21 against a since-expanded set of docs — I
  have no evidence for this, but I also can't rule it out from the documented record alone).
- Did not investigate the root cause (which script/process wrote this value, and whether it's still writing it today —
  new docs as recent as `ag_closeout_audit_ui_parked_2026_08_09.md`, created the same day as this finding, already carry
  it, so if this is a live bug it is still actively firing).

## Todos

- [ ] [OPERATOR] P2. Confirm whether `locked_by: live-defi-rollout` / `locked_since: 2026-05-21` on these 22 docs (list
      above) represents a genuine lock or a placeholder/bug artifact. If placeholder: `[unlock-plan]` at least the 2
      cefi-tranche-confirmed archival-ready docs (`cefi_coinbase_cde_urdi_zero_records_2026_07_28.md`,
      `features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md`) so they can go through the
      standard archival ritual; a wider corpus sweep of the remaining 20 for the same 0-open-todos check is a natural
      follow-up once the root cause is known.
- [ ] [SCRIPT] P3. If confirmed a bug (not a genuine bulk-lock event): grep the doc-authoring tooling / templates for
      where `locked_by: live-defi-rollout` could originate as a default/seed value (it is NOT `task_template.md`'s own
      template default, which leaves `locked_by:` blank — confirmed by reading that file) and fix at the root so new
      docs stop acquiring it (`ag_closeout_audit_ui_parked_2026_08_09.md` shows it is still happening as of this doc's
      own creation date).

## Progress Log

- **2026-08-09** (plan_reconciler, agt-51e4bd, slot 9, cefi tranche run): filed after finding the pattern while
  verifying an archival candidate. Corpus-wide grep confirmed scope (22 docs); did not investigate root cause or clear
  any locks (operator-gated).
