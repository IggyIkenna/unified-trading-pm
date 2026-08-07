---
doc_type: issue
title: "plan_reconciler daily deep reconciliation — defi tranche run findings (2026-08-07)"
summary:
  "Run-findings doc + progress journal for plan_reconciler dispatch agt-a2268a, sharded to the defi tranche per the
  2026-08-06 operator ruling on sharded/weekly cadence. Scope: 107 docs under plans/active + plans/active/issues +
  plans/epics carrying asset_group or parent_epic containing 'defi' (Phase-0 inventory: 3.87MB, 45/107 in the 12h grace
  window). Fans out read-only hunter batches, adversarially verifies every candidate, auto-fixes the verified-easy,
  routes the hard ones. Updated incrementally as the run progresses."
status: open
nature: issue
asset_group: [defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [role, plan_reconciler, reconciliation, plan-hygiene, defi, sharded-run]
related: []
created: 2026-08-07
author: plan_reconciler
source: agt-a2268a
locked_by: plan_reconciler-agt-a2268a
parent_epic: plan_hygiene_master
priority: P1
assigned_vm: NA
resolved_by:
---

# plan_reconciler — defi tranche run findings (2026-08-07, dispatch agt-a2268a)

> Persistent-until-resolved run doc. `TRANCHE=defi`. Sections below are appended as the run progresses; see Coverage for
> hunter/batch/doc counts and Plans not reached for anything the run could not get to.

## Phase-0 inventory summary

- Corpus scope: `plans/active/**` + `plans/active/issues/**` + `plans/epics/**` where `asset_group` or `parent_epic`
  contains `defi` (line-based frontmatter parse, scratch/audit subdirs excluded).
- 107 docs, 3,873,041 bytes total, avg 36.2 KB/doc.
- 45/107 (42%) inside the 12h grace window (newest git change <12h old) — READ-ONLY context this run, never written.
- Corpus-wide mechanical hygiene sweep (`run_hygiene_sweep.sh --ci`, whole corpus, not defi-filtered): 4 hard failures —
  reference-path-convention (83 format/92 existence, both over ratchet baseline), AG-closeout-linkage (77 orphans,
  baseline 69), terminal-status-archived (4, baseline 0 — none defi-tagged), archive-candidates (10, baseline 0 — 1
  defi-tagged: `defi_catalog_dp_catalog_001_shrink_blocked_2026_08_02.md`).
- Defi-tranche subset of the AG-closeout-linkage orphans: 9 issue docs (see Coverage / hunter batch assignments below)
  with `asset_group=[defi]` but no graph/mention path to `defi_consolidated_closeout_2026_07_18.md` or a satellite
  dispatch batch.

## Flips verified

HARD-evidence missed-flips, independently re-verified by me (not just trusting the hunter) before applying:

1. `defi_pipeline_mode_source_desync_yearn_v3_2026_07_21.md` todo 5 (F10-register) — `unified-trading-pm@0c4172c31`
   verified reachable on `origin/live-defi-rollout` + F10 row confirmed present at
   `codex/02-data/canonical-cutover-register.md:136`. — `12e2aee10`
2. `lst_rate_honest_coverage_2026_07_21.md` — 3 checkboxes (A2 staking leg, recursive-staking borrow leg, Phase-3
   sample-download) — `strategy-service@e93902d8` + `@23bd8b76` both verified reachable; Phase-3 superseded-by-Phase-5
   claim corroborated against the doc's own in-body Progress Log entry (line ~829). — `d461fd594`
3. `defi_legacy_precanonical_composite_venue_objects_2026_07_24.md` — the hunter-reported missed-flip was **already
   fixed** by the time I checked (checkbox already `[x]` with full evidence) — no action needed, not double-counted.

## Contradictions

Confirmed + resolved this run (evidence-provable, per the skill's Calibration bar — not authority calls):

1. **Barchart delete-todo vs. a later, opposite operator ruling.**
   `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`'s open `[REFACTOR] P2` "DEPRECATE + REMOVE all
   Barchart" todo was superseded by a 2026-07-20 ruling (reconfirmed 2026-07-30, now recorded in
   `/codex/02-data/tradfi-databento-sourcing-ssot.md`): disposition is **KEEP, no purge**. Struck with a citation. —
   `7c03744ca`
2. **`autonomous_session_operator_decisions_2026_07_25.md` entry 12's Status block was a verbatim copy of entry 11's
   text** (wrong topic — locked-plan-deletion-gate instead of the prediction-plan fold decision). Independently
   confirmed the REAL underlying action (option A, the fold) did execute
   (`prediction_perps_kalshi_polymarket_parked_2026_07_24.md` archived, folded into
   `prediction_phase_ab_residuals_2026_07_24.md` § A3) and rewrote the Status block to match. — `677ca807b`
3. **`defi_turbo_api_hides_real_captured_data_2026_07_07.md`'s sole open todo directed work opposite to an
   already-executed, later ruling.** The todo asked to declare HYPERLIQUID/ASTER in UAC's `ALL_DEFI_VENUES` — but the
   2026-08-02 `hyperliquid_aster_defi_to_cefi_asset_group_migration_2026_08_02.md` (closed 2026-08-06) already migrated
   all 7,599 `asset_group=defi` objects for these venues to `cefi` and deleted the defi-bucket originals. Closed as
   moot. — `9e745a8aa`. **This flip made the doc's open-todo count hit 0** — see Archive candidates below.
4. **7 of 8 `related:` refs in `instruments_docs_audit_outstanding_items_2026_07_08.md` pointed at archived docs by
   their stale pre-archival (`plans/active/...`) path.** Repointed to their real `plans/archive/...` locations +
   canonicalized to leading-slash form. — `9c5b24f42`
5. **`backfill_smoke_write_path_canonical_audit_2026_07_20.md`** cited
   `cefi_chain_tail_v6_canonicalisation_2026_07_21.md` at its stale pre-archival path. Repointed. — `574cd2969`
6. **`plans/epics/defi_master.md`'s routing table cited 3 plans** (`defi_governance_params_refresh_2026_06_20`,
   `defi_manifest_canonicalisation_2026_06_01`, `data_source_provenance_all_asset_groups_2026_06_01`) **at their stale
   `../active/...` path** (5 occurrences) — all 3 are archived. Repointed to their real archive locations. — `36a4e854f`

## Doc-drift

Flagged (routed via STEP 6, not fixed — codex edits need an explicit operator ruling):

1. **`/codex/02-data/defi-canonical-naming-ssot.md`'s "On-chain perp CLOBs are CeFi, NOT DeFi" section (venue
   enumeration `HYPERLIQUID, ASTER, EXTENDED, LIGHTER`) is now stale** — a 2026-08-06 operator ruling reclassified
   KALSHI_PERP/POLYMARKET_PERP `perp_funding` data to `asset_group=cefi` too (per
   `defi_kalshi_perp_perp_funding_source_not_registered_2026_07_23.md`, currently in the 12h grace window), but the
   codex venue list was never updated to add them. NOT fixed here (codex edit requires operator ruling per HARD RULE).
   See Filed below.
2. **`agents/plan_reconciler.md`'s own STEP 6(b) instruction is stale**: "append ONE line to BOTH
   `ikenna_orchestrator/_agent_pings.md` + `harsh_orchestrator/_agent_pings.md`" — both files carry an explicit
   `RETIRED 2026-07-04 — Do NOT append pings here` notice (superseded by the agent-orchestrator HTTP server, i.e. the
   `/blocked` POST this run already used for the escalation above). Skipped per the live retirement notice; not fixed
   here (role-file edit outside `plans/**`, and not this run's scope) — flagging for whoever next touches that role
   file.
3. **`agents/plan_reconciler.md`'s STEP 7 result-POST path is wrong**: it says `POST $SERVER_URL/api/plan_health/result`
   (underscore) — the real endpoint is `/api/plan-health/result` (hyphen, matching the dispatch endpoint's own naming).
   `curl` against the underscore path returns a bare `404 Not Found`; the hyphenated path + the `X-Orchestrator-Secret`
   header (present in this session's env — the boot note's "may be EMPTY, that's fine" caveat did not apply here)
   returned `200 {"ok":true,...}`. Not fixed here (role-file edit out of scope) — flagging for whoever next touches that
   role file.

## Hygiene fixes

1. `mtds_pipeline_check_process_killed_during_skip_leg_poll_2026_08_06.md` — zero-checkbox doc (confirmed via
   `grep -c`), 3 concrete "Suggested follow-up" prose bullets converted to tracked `- [ ]` [DIAG]/[INFRA] todos per the
   skill's standing zero-checkbox-sweep responsibility. — `e4d3dd48e`
2. `defi_kamino_lending_venue_drift_live_data_verification_gap_2026_08_04.md` — zero-checkbox doc, entire open question
   ("does the live manifest carry stale rows?") already answered + executed by a sibling doc
   (`defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md` item 7, `market-tick-data-service@bd153821` verified
   reachable) — resolved-by-citation, archived. — `21c9a8757`

## Filed

1. **`plan_hygiene_quoted_empty_locked_by_masks_archive_candidates_2026_08_07.md`** (new issue, P2) — verified by
   reading the actual script code (not inferred): `check_archive_candidates.sh` AND `check-locked-plan-deletion.sh` both
   mis-read a literal `locked_by: ""` (quoted-empty) as a real lock, via naive grep+sed/grep-oP text extraction instead
   of real YAML parsing. Confirmed 4 corpus docs currently affected (1 resolved+archived this run via a 2-commit
   workaround, 1 not-yet-a-candidate, 2 genuine masked candidates outside the defi tranche — left for their own
   tranche). Hit the SAME bug live in the deletion-gate hook while archiving
   `dex_pool_state_build_instrument_id_colon_in_symbol_2026_08_04.md` — worked around via a 2-commit split (content
   edit, then archive), documented in the issue doc so the next agent doesn't have to re-discover it. — `78ea4fe70`
2. **Codex drift (KALSHI_PERP/POLYMARKET_PERP venue enumeration)** — see Doc-drift above. Routed via `/blocked`
   (`BLK-02d1163f`, batched with items below) + this filing (STEP 6); needs an operator ruling before any agent edits
   the codex SSOT.
3. **`plans/epics/defi_master.md`'s 5-6 orphaned P3 backlog items** (AWS SNS/SQS mirroring, cross-cloud WIF, ltv-tuning,
   DeFi-data creds, Firebase SA JSON — CEFFU appears already resolved elsewhere) are named in the epic's own routing
   table prose as "kept as the thin epic's `## P3` list below" but that list is auto-generated (only lists real plan
   docs with matching `parent_epic` frontmatter) and is empty — these 5 items have no tracked form anywhere. NOT fixed
   here: where 5 speculative backlog items should live (a new plan doc? hand-added prose distinct from the
   auto-generated block?) is a placement/authority call, not a provable fact. Routed via `/blocked` (`BLK-02d1163f`).
4. **`defi_turbo_api_hides_real_captured_data_2026_07_07.md` is now a genuine archive candidate** (0 open todos post fix
   #3 above, unlocked) but carries ~20 corpus referrers (6 active non-grace, 3 active grace-protected, 11
   archive/historical). NOT archived this run — the referrer-sweep overhead exceeded this run's remaining budget;
   recommend a dedicated `/archive-candidates-audit` pass.

## Archive candidates (operator review)

| Plan                                                                       | Why ready                                                        | Locked?                                            | Archived this run?                                                     |
| -------------------------------------------------------------------------- | ---------------------------------------------------------------- | -------------------------------------------------- | ---------------------------------------------------------------------- |
| `defi_kamino_lending_venue_drift_live_data_verification_gap_2026_08_04.md` | 0 checkboxes; question answered+executed elsewhere, verified sha | No                                                 | **Yes** — `21c9a8757`                                                  |
| `dex_pool_state_build_instrument_id_colon_in_symbol_2026_08_04.md`         | done=2/open=0, both HARD-verified                                | No (was masked by the `locked_by: ""` tooling bug) | **Yes** — `c6af75f0b`                                                  |
| `defi_turbo_api_hides_real_captured_data_2026_07_07.md`                    | done=10/open=0 after this run's fix                              | No                                                 | **No** — ~20 referrers, flagged for a dedicated sweep                  |
| `defi_catalog_dp_catalog_001_shrink_blocked_2026_08_02.md`                 | done=3/open=0                                                    | No                                                 | **No** — in 12h grace window                                           |
| `defi_code_codex_drift_2026_05_27.md`                                      | 13/13 todos `[x]`, D15 fully resolved                            | **Yes** (`locked_by: live-defi-rollout`)           | **No** — needs `[unlock-plan]`, routed via `/blocked` (`BLK-02d1163f`) |

## Refuted (dropped by verify)

- **`defi_legacy_precanonical_composite_venue_objects_2026_07_24.md` fold-to-canonical todo** — hunter (batch8) reported
  this as an open missed-flip; on independent re-check it was already `[x]` with full evidence. Not a contradiction,
  just a stale hunter read (likely resolved by another agent between the hunter's read and my check) — corpus is under
  very high concurrent write load this run (see Coverage note below).

## Coverage (hunters / batches / docs)

- Phase-0 inventory (initial): 107 docs / 3,873,041 bytes across `plans/active` + `plans/active/issues` + `plans/epics`
  tagged `defi`, partitioned into 8 hunter batches (greedy bin-pack, ~484 KB/batch target).
- **Extremely high concurrent write load observed**: a fresh inventory taken ~90 min later (just before STEP 5) found
  109 docs and 47/109 in the 12h grace window (vs. 45/107 at Phase-0) — dozens of docs were actively touched by OTHER
  agents/slots during this run's ~13-minute hunter fan-out alone. Re-verified grace/lock status fresh, per-file,
  immediately before every edit in STEP 5 rather than trusting the Phase-0 snapshot (caught and corrected a
  batch-assignment transcription error on my own part — see Process note below).
- Hunters dispatched: 8/8 completed, `general-purpose` agent type, `model=sonnet`, full corpus coverage confirmed (each
  hunter reported "Read N/N docs in full"). ~2.6M subagent tokens total, ~600s median runtime.
- STEP-4 verification: performed inline (re-running the exact same shas/greps/codex-reads the hunters cited,
  independently) rather than a separate refuter/confirmer sub-agent pair — justified per the skill's Calibration section
  ("small candidate counts you may verify inline (you are opus/max)") and because every applied fix's evidence was a
  re-runnable, deterministic check (git log/merge-base, grep, wc -l), not a subjective judgment call.
- **Process note**: when constructing each hunter's "GRACE SET" list by hand from the master Phase-0 list, I made a
  transcription error on 5 of 8 batches (told hunters a doc was non-grace when the master list said otherwise). Zero
  actual harm — hunters are read-only and never write; I independently re-verified grace status fresh, per-file, before
  every STEP-5 edit regardless of what any hunter assumed. Filed as a lesson for the next dispatch, not a separate issue
  doc (a one-off authoring mistake in this run, not a repo/tooling defect).
- Findings-doc population: this run applied 12 fixes (4 flips/contradictions-resolved + 2 archives + hygiene + 1
  tooling-bug filing) across 14 commits, out of ~50+ distinct findings surfaced by the 8 hunters. The remainder fall
  into: (a) currently grace-protected (re-check next pass), (b) genuine authority/placement calls (routed via
  `/blocked`, see Filed), (c) lower-priority AO-dispatch-readiness/hedge-pointer/prose-cosmetic findings not
  individually applied this run for lack of remaining budget — see Plans not reached.

## Plans not reached

Findings surfaced by the 8 hunters but not individually verified+applied this run (budget-limited, not blocked):

- **AO-dispatch-readiness gaps** (several): `lighter_tardis_writerless_route_hang_2026_07_28.md`'s `[CODE]` tag on a
  todo whose own text says the fix needs a human design pick among 3 options (should likely be `[DESIGN]`); prose-only
  (not `gate_on_depends`-enforced) prerequisites in `defi_pipeline_e2e_and_coverage_validation_2026_06_20.md` and
  `defi_satellite_ao_dispatch_batch2_2026_07_26.md`'s KALSHI_PERP todo; a missing `[OPERATOR]` tag on a GCS-delete todo
  in `defi_satellite_ao_dispatch_batch6_2026_07_30.md` (has the delete-safety citation, missing the formal tag).
- **Hedge-pointer language**: `mtds_qg_red_uac_capability_declaration_drift_2026_08_05.md` has a malformed
  backtick-mangled checkbox (invisible to `grep -c '^\s*- \[ \]'`) — currently in the 12h grace window.
- **Cosmetic/prose well-formedness**: several docs (`defi_cefi_venue_chain_axis_contamination_2026_07_28.md`,
  `defi_code_codex_drift_2026_05_27.md`, `defi_track01_per_instrument_and_canon_id_2026_07_24.md`, others) carry large
  mid-paragraph whitespace-injection artifacts (P3 cosmetic, likely a copy-paste/editor artifact class worth a dedicated
  sweep, not fixed individually this run).
- **`defi_dex_pool_swaps_733_row_indexer_health_findings_2026_07_27.md`** has a genuinely false-completion checkbox
  (marked `[x]` "SHIPPED" but the MTDS half is confirmed stranded off `live-defi-rollout`, verified by the doc's own
  later context-scout entry) — currently in the 12h grace window, re-check next pass.
- Several more contradictions/stale-drift items reported by hunters against docs that are **currently in the 12h grace
  window** (`defi_cefi_venue_chain_axis_contamination_2026_07_28.md`,
  `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`'s GMX-regression section,
  `defi_kalshi_perp_perp_funding_source_not_registered_2026_07_23.md`'s stale Follow-ups section,
  `defi_staking_yields_lst_rates_handler_gaps_2026_07_24.md`'s self-contradicting audit note,
  `defi_consolidated_closeout_2026_07_18.md`'s stale "13 open" digest-count citing `defi_track01`) — all confirmed by
  hunters with good evidence, none touched (grace), flagged for the next reconcile pass to pick up once grace clears.
