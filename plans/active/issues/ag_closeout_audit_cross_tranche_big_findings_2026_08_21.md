---
doc_type: issue
title: ag-closeout-audit 2026-08-21 — cross-tranche big findings requiring operator attention
summary: >-
  Consolidated escalation-worthy findings surfaced during the 2026-08-21 full /ag-closeout-audit sweep (all 10
  tranches, 777 candidate docs, 30 Phase-1 batches). These are the findings that crossed a real severity/escalation
  threshold — either P0 live-capital-safety, a mechanism re-confirmed broken by 5+ independent audit passes, or a
  live operational incident actively wasting compute/pages. Each item below also lives in its own source doc and
  will be re-listed in its owning tranche's ag_closeout_audit_<tranche>_parked_2026_08_21.md doc; this doc exists
  so a single read surfaces everything that needs a human decision or a dedicated fix session, without requiring
  someone to read all 10 tranche docs first.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator, execution-service, deployment-service, unified-trading-library]
scope: [engineer, admin]
tags: [ag-closeout-audit, escalation, big-findings, live-capital-safety]
related: [/plans/active/cross_cutting_consolidated_closeout_2026_07_25.md]
created: 2026-08-21
last_updated: 2026-08-21
author: claude-session-2026-08-21
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: research
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: NA
drift_direction: NA
resolved_by:
locked_by:
source:
  [
    "2026-08-21 — /ag-closeout-audit all-tranche sweep, 30 Phase-1 batches, 10 tranches, 777 candidate docs classified",
  ]
depends_on: []
context_scope: [/plans/active/issues/ag_closeout_audit_cross_tranche_big_findings_2026_08_21.md]
---

# ag-closeout-audit 2026-08-21 — cross-tranche big findings

Full sweep: all 10 tranches (cefi, defi, tradfi, prediction, sports, cross-cutting, ao, ci, infra, ui), 777 AG-primary
candidate docs, 30 Phase-1 read-only classification batches. This doc collects only the findings that crossed a real
severity bar — P0 live-capital-safety, a mechanism independently re-confirmed broken across 5+ separate audit passes,
or a live incident actively burning compute/paging capacity right now. Ordinary orphan findings (a doc with no active
covering plan) live in the 10 per-tranche `ag_closeout_audit_<tranche>_parked_2026_08_21.md` docs instead.

## Live-capital-safety P0s (execution-service / cross-cutting tranche)

1. **W15 venue-adaptor security audit — dozens of unfixed HIGH/CRITICAL findings, zero coverage.**
   `plans/active/w15_execution_service_venue_adaptor_security_audit_2026_08_20.md`. A completed security audit found:
   unbounded/unvalidated on-chain write amounts, missing slippage/deadline bounds (sandwich-attack exposure),
   unsynchronized nonces (replay risk), and — most seriously — several DeFi connectors (`aave.py`, `idle.py`) that
   **fall through to simulated-success when live credentials/executor are absent**, i.e. can silently report a fake
   fill instead of a real failure. Every triage todo across bridge/CCTP, Aave/Morpho/Kamino/Idle lending,
   Lido/EtherFi/RocketPool/Marinade staking, CCXT + native-REST CeFi order boundaries, and perp/CLOB adapters is
   still unchecked. Zero fixes landed, zero AO-dispatch coverage.
2. **OMS order-recovery persistence — almost entirely unbuilt, explicitly blocks safe recovery wiring.**
   `plans/active/w_execution_orchestrator_oms_persistence_impl_2026_08_21.md` +
   `plans/active/w_state_recovery_real_wiring_2026_08_20.md`. `PostgreSQLOrderPersistence` still has stub methods;
   `oms.create_order()`/`update_order_status()` are not wired into the live order-submission hot path; no shared OMS
   instance threads from startup. The sibling recovery-wiring doc explicitly states wiring `OrderRecoveryEngine`
   before this lands would be **actively unsafe** — it would cancel legitimate open orders on every restart, since
   the in-memory `OrderBook` is structurally guaranteed empty with nothing durably persisting order state today.
   Fourth confirmed instance this session of the "declared-but-unwired" architectural pattern (see below).
3. **`execution_state_does_not_survive_restart_2026_08_20.md` — 5 of 8 P0 remediation todos unclaimed.**
   Durable order/position persistence, `OrderRecoveryEngine` wiring, `--skip-recovery`, `AccountHistoryClient`, and
   epoch fencing (no protection against two live instances both submitting orders) remain fully orphaned; only 3
   investigation-only sub-items reached active AO-dispatch coverage.
4. **`producer_silence_flatten_protocol_2026_08_14.md` — real-money auto-flatten protocol not built at all.**
   23 open P0/P1 items (spread-preservation, kill-switch bus wiring, liveness/reconciliation-health branch), zero
   AO-dispatch coverage. Not "declared but unwired" — genuinely unimplemented.
5. **`market_data_timestamp_semantics_collapsed_to_one_field_2026_08_20.md` — P0 correctness gap.**
   Live MTDS ticks carry one overloaded timestamp field whose semantics (exchange-time vs. arrival-time) vary
   silently by adapter — blocks per-region replay and makes lookahead-prevention unverifiable on the live path. Only
   2 of 6 todos (pure investigation) reached active coverage; the 4 actual schema/code fixes remain `assigned_vm: NA`.

### The "declared-but-unwired" pattern — now confirmed 5+ times this session, worth its own architectural-integrity review

A recurring shape found independently across cross-cutting batches 3, 4, 5, 6: a safety/correctness mechanism exists
in code (often with docstrings/CLI flags asserting it runs) but has **zero real production call sites**. Confirmed
instances: `TransferCoordinator`, `HealthFactorMonitor` (defi liquidation protection — see below),
`OrderRecoveryEngine`, `dependency_health_policy` actuator (live-path kill-switch-adjacent), and the ml-service
`--run-tag` CLI flag referenced by the recon-bucket finding below. This is systemic enough to warrant a standalone
audit of "every safety mechanism with a docstring claiming production use — does it have a real caller?" rather than
finding the 6th instance one doc at a time.

## Funds-safety P0 (defi tranche)

6. **`health_factor_monitor_no_production_entrypoint_liquidation_unprotected_2026_08_19.md`.** `HealthFactorMonitor`
   (the liquidation-trigger monitor for leveraged DeFi carry positions) has zero measured production
   instantiations; `DeleverageExecutor` has exactly one module-level singleton with no confirmed publisher. If
   genuinely unwired, leveraged DeFi positions have no event-triggered liquidation protection at runtime. 5 open
   investigation/wiring todos, uncovered by any active plan.

## Operational incidents actively burning resources right now

7. **Databento CME billing block — 8+ days stale, burning real SPOT compute daily, unanswered decision. RESOLVED
   2026-08-21 (operator ruling D5): operator pays the invoice directly; the fleet wave mechanism is paused.**
   `plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md`. Billing-blocked since
   2026-08-12, zero recovery through 2026-08-21 (measured 8.0+ days live-capture staleness and still growing). A
   fleet-wide `tradfi-bf-cme-ohlcv-1m-` relaunch wave burns real SPOT compute daily (114+ distinct VM launches/day
   per the 2026-08-20 alert sweep) against a wall that cannot succeed. **Root cause of the daily wave found +
   fixed same-day**: NOT the Terraform-managed `uts-prod-tradfi-wave-launcher-cron` Cloud Scheduler job (confirmed
   `state: PAUSED` since 2026-06-24, unchanged) but a separate, undocumented crontab entry on the AO orchestrator
   VM's `ubuntu` user running `scripts/wave_launcher.py` directly every 3h — paused at the source, 2 currently-running
   zero-progress CME VMs stopped (confirmed via `run.log`/`PROGRESS.json` — both stuck on 402
   `account_delinquent_invoice` every attempted date), and a live GLBX.MDP3 billing-probe gate shipped into
   `wave_launcher.py` as defense-in-depth for whenever the mechanism is re-enabled.
8. **Nightly BLRS determinism reconciliation — failed 55 of 56 scheduled runs since mid-May, escalation stuck 8+
   days, AND a separate dedup bug caused 10 duplicate escalation-worker dispatches in ~30 hours.**
   `plans/active/issues/recon_bucket_missing_nightly_recon_failing_2026_07_13.md`. Root cause fully diagnosed
   2026-07-14: two producer Cloud Run Jobs were never provisioned. An operator escalation (`BLK-8bb28da4`, opened
   2026-08-10) sat unanswered 8+ days. Separately, DP-WATCHER-006's escalation dispatcher failed to suppress
   re-dispatch against an already-open blocked question, causing 10 near-identical escalation-worker dispatches in
   ~30 hours (one instance recorded `"attempts":108`), each re-deriving the identical root cause at real token cost.
   Entirely uncovered by any active dispatch.
9. **`ao_tmp_tmpfs_full_sqlite_disk_full_errors_2026_08_21.md` — same-day P0, immediate crisis fixed, 4 hardening
   items unclaimed.** Real production `sqlite3.OperationalError: database or disk is full` caused live 500s on the
   agent-orchestrator host. Fixed same-day, but undersized-cap-vs-leak decision, committing the new systemd reaper
   units to a repo, investigating a correlated 93% I/O wait, and SQLite tmpdir hardening remain open and unclaimed.

## Mechanism-reliability findings re-confirmed by 5+ independent audit passes (crosses this skill's own carried-finding threshold)

10. **AO's own Slack alerting webhook — broken 3+ weeks, 8+ audit rounds, zero paging capability this entire time.**
    `plans/active/issues/ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md`. `AGENT_ORCHESTRATOR_SLACK_WEBHOOK`
    genuinely un-locatable across 2026-08-02 through 2026-08-21 (8+ rounds); a live 2026-08-19 attempt confirmed both
    documented secret names resolve to nothing in the expected GCP project. `ao-self-pull.sh` wedge/drift alerts have
    had zero paging capability this entire window.
11. **`safe-doc-push.sh` (the mandated workspace doc-shipping tool) — 8+ independently observed content-loss/corruption
    incidents, several hit live during THIS audit run.** Silently drops renamed content, resurrects stale content from
    unrelated stash entries over already-correct data, loses unrelated dirty files across quarantine cycles. Multiple
    root causes found+fixed but new variants keep surfacing (most recently 2026-08-18). Given this is CLAUDE.md's
    mandated path for every plan archival workspace-wide, this is a standing reliability risk, not a closed bug class.
    Tracked across `issues/safe_doc_push_extreme_stash_quarantine_drops_renamed_file_content_2026_08_15.md`,
    `issues/safe_doc_push_prek_patch_orphaned_recurrence_2026_08_15.md`,
    `issues/safe_doc_push_stash_pileup_quarantine_drops_renamed_path_2026_08_15.md`,
    `issues/safe_doc_push_unrecognized_flag_silently_becomes_branch_name_2026_08_18.md`.
12. **Shared-checkout `git pull --rebase --autostash` data-loss hazard — 6+ independent repros, 3 of 4 recommended
    fixes still unimplemented.** `issues/autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md`.
    Reproduced deliberately, reproduced live 4 times in the originating session, reproduced a 5th time via plain
    `--ff-only`, and a 6th time on 2026-08-19 in a narrower shape (a top-level session and its own forked sub-agent
    sharing one `.git`). One mitigation shipped (`wip_guard_report`) and verified; 3 of 4 recommended fixes remain
    unimplemented. **This session independently hit variants of this exact hazard multiple times** during Phase-1
    dispatch (see this session's own /pre-compact history — several wave-1/wave-2 na-eligibility-audit and
    ag-closeout-audit sub-agents self-recovered from partial pushes and stash-interleaving content loss).
13. **`na_docs_validity_and_ao_eligibility_audit_2026_07_26.md` — the na-eligibility-audit skill's own origin plan,
    re-confirmed KEEP-NA 9 separate times (2026-07-30 through 2026-08-21) without ever advancing its own tracked
    Phase 1-3 checkboxes.** Self-referential: the skill that keeps re-verifying this plan has moved past what the
    plan itself describes (it now runs incrementally per-tranche), but the plan's literal checkboxes have sat open
    26+ days. Needs an operator ruling: either formally supersede Phase 1-3 with "the skill now IS this plan's
    execution, close it out," or genuinely schedule the sweep it still describes.
14. **`deployment_api_inventory_alert_gate_ondemand_only_2026_07_27.md` (ui tranche) — 6 consecutive audit/reconcile
    passes reaching the same verdict, architecture question unresolved 3+ weeks.** Also itself a "declared-but-unwired"
    instance: `_alert_on_health_transition()`/`_ALERT_HEALTH_STATES` is real, unit-tested alerting code with zero
    independent production trigger (no Cloud Scheduler cron) — only fires as a side effect of a dashboard tab being
    open or the once-daily digest cron. A newly-alertable state can silently go unpaged for up to a day.
15. **`deployment_registry_firestore_p3_cutover_2026_07_14.md` (ui tranche) — 7 dated re-confirmations since
    2026-07-30, root cause diagnosed 2026-08-08, still unfixed.** The GCS-registry cutover HALT condition (the
    reaper never touches Firestore) remains blocked.

## Cross-tranche routing / coverage-attribution gaps (process findings, not correctness bugs)

- The entire `code_readiness` five-agent system (8 docs, ~78 combined open todos across coordinator + T1-T5) sits
  completely outside the AO-dispatch mechanism by design (operator-launched interactive slots, not AO backlog) — not
  neglect, but worth an explicit acknowledgment in future audit scoping so it stops re-surfacing as "orphaned."
- Two cross-cutting satellite batches (`batch19`, `batch20`) have sat `status: draft` since 2026-08-19 with real,
  sometimes P0, work drafted inside them (including the `dependency_health_policy` live-path item and the
  `mdps_fleet_duplicate_relaunch_explosion` P0 cron re-enable) — never promoted to `active`. Their paired `_finalize`
  plans are `status: active` and gated on drafts that were never dispatched, so those finalize plans can structurally
  never complete. This is the "finalize plan permanently stuck" trap found repeatedly this run.
- A doc's real AO-dispatch coverage sometimes comes from a DIFFERENT tranche's batch than the one auditing it
  (multi-tag docs) — several `orphaned` verdicts in a tranche's own report turned out to be covered elsewhere. Not a
  gap, just means the per-tranche orphan counts in the 10 parked docs slightly overstate true orphan totals until
  reconciled cross-tranche.

## Recommended next actions (not yet executed — this doc is the record, not the fix)

- [x] N. ✅ [INFRA] P0. Item 7 (tradfi Databento billing) — RESOLVED 2026-08-21 per D5 ruling: OPERATOR-RULED —
      APPROVED, operator pays the Databento CME invoice; the tradfi-bf-cme-ohlcv-1m fleet wave mechanism is paused
      (autonomous, zero-cost — see item 7 body above for the paused-crontab + billing-probe-gate evidence), relaunch
      only after billing clears. Source: this doc; ledger D5.
- [ ] [OPERATOR] P0. Rule on item 8 above (recon_bucket nightly recon fleet-wide Cloud Run Job provisioning) — still
      live, actively wasting real compute/paging capacity right now, not covered by today's decision ledger.
      Source: this doc.
- [ ] [OPERATOR] P0. Decide disposition for items 1-6 (execution-service/defi live-capital-safety gaps) — at minimum
      confirm whether these are already scheduled for a dedicated engineering pass outside the AO-dispatch system.
      Source: this doc.
- [ ] [INFRA] P1. Locate or re-provision `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` (item 10) — a 3-week silent
      paging-capability gap on the orchestrator's own alerting. Source: this doc.
- [ ] [INFRA] P2. Schedule a dedicated review of `safe-doc-push.sh`'s stash/quarantine reconcile logic (item 11) —
      8+ independent incidents against the workspace's mandated shipping tool. Source: this doc.
- [ ] [DOCS] P3. Per D1 ruling (ADOPTED-REC 2026-08-21, autonomous-dispatch authority: "approve all — repeated
      audits agree these are churn, not live tasks"): formally supersede
      `na_docs_validity_and_ao_eligibility_audit_2026_07_26.md`'s own tracked Phase 1-3 checkboxes — add a closing
      note stating the na-eligibility-audit skill now IS that plan's execution (it runs incrementally per-tranche),
      then archive it. Done-when: the doc is archived with a superseded-by note citing D1. Source: this doc;
      ledger D1.
- [ ] [OPERATOR] P2. Decide whether to promote `cross_cutting_satellite_ao_dispatch_batch19`/`batch20` from draft to
      active, or explicitly abandon them and re-derive their content into fresh batches. Source: this doc.

## Progress Log

- **2026-08-21**: Doc created directly from the 2026-08-21 full `/ag-closeout-audit` sweep (30 Phase-1 batches, all
  10 tranches, 777 candidate docs). This is a synthesis doc — no new investigation performed here; every finding
  cites its own source doc for full detail.
- **2026-08-21 — ruling D1 (Stale meta-doc disposition)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch authority,
  AUTONOMOUS_AGENT_RULES rule 2): Approve all — repeated audits agree these are churn, not live tasks; the two
  keep-open items and the one split are the only exceptions. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md
  ledger.
- **2026-08-21 — ruling D5 (Databento CME billing + relaunch fleet)**: OPERATOR-RULED 2026-08-21 — APPROVED:
  operator pays the Databento CME invoice; agent pauses the tradfi-bf-cme-ohlcv-1m fleet wave mechanism NOW
  (autonomous, zero-cost), relaunch only after billing clears. Source:
  /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
