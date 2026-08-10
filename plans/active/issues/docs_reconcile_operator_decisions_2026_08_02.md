---
doc_type: issue
title:
  "docs-reconcile 2026-08-02 — 4 genuine operator-decision parks (cursor-rules/ purpose; locked docs' broken frontmatter
  fields; Fireblocks rotation-cadence SSOT contradiction)"
summary: >-
  Four findings across three docs-reconcile autonomous sweeps that the skill's own contract requires parking for the
  operator rather than auto-fixing: (1) what the 25-file `cursor-rules/` tree is actually FOR today, now that it's
  confirmed NOT synced to the real canonical `.cursor/rules/` tree (150 files, 0 overlap) -- an authority call about
  intent, not a correctness call; (2) `plans/active/issues/macro_micro_econ_data_capture_audit_2026_06_05.md` carries
  `locked_by: live-defi-rollout`, so its broken `source:` frontmatter entry (a brace-expansion path with a redundant
  `unified-trading-pm/` prefix) cannot be auto-fixed per the HARD RULE against editing a locked doc's frontmatter
  without sign-off; (3) added 2026-08-06 -- 14 `plans/active/issues/*.md` docs (incl. the same
  `macro_micro_econ_data_capture_audit_2026_06_05.md` from item 2) all carry a `locked_by`-gated, mechanically truncated
  `summary:` field (12 of 14 cut at exactly 200 chars mid-word/mid-link), pre-drafted replacements ready to apply on
  sign-off; (4) added 2026-08-08 -- credentials-matrix.md and credential-rotation-runbook.md, both `authoritative_for`
  credential rotation cadence, assert DIFFERENT numbers for Fireblocks custody creds (quarterly vs 60d) -- a real
  content contradiction on a security-relevant credential class, not just an ownership overlap.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    docs-reconcile,
    operator-decision,
    cursor-rules,
    locked-doc,
    retrieval-layer,
    credentials,
    authoritative-for-collision,
  ]
related: []
created: 2026-08-02
author: unknown
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days:
estimate_calibrated_ai_days:
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /codex/05-infrastructure/credentials-matrix.md,
    /codex/15-runbooks/credential-rotation-runbook.md,
    /plans/active/issues/macro_micro_econ_data_capture_audit_2026_06_05.md,
    /plans/active/issues/docs_reconcile_remaining_broken_links_2026_08_02.md,
    /plans/active/issues/doc_body_link_checker_blind_to_backtick_citations_2026_08_02.md,
    scripts/workspace/setup-cursor-rules-symlink.sh,
  ]
supersedes:
superseded_by:
depends_on:
source: [docs-reconcile autonomous sweep, dispatch agt-0b4ee1, 2026-08-02]
assigned_role: infra
drift_direction: advance-docs
---

# docs-reconcile 2026-08-02 — 2 operator-decision parks

Both items below were found during the 2026-08-02 autonomous `/docs-reconcile` sweep. Per the skill's own
autonomous-mode contract, a genuine authority call is parked here rather than decided unilaterally. Everything else the
sweep found was either auto-fixed (4 commits shipped, see Progress Log) or filed as a separate report-only issue doc
(see `related` analogues: `doc_body_link_checker_blind_to_backtick_citations_2026_08_02.md`,
`docs_reconcile_remaining_broken_links_2026_08_02.md`).

## 🚧 BLOCKED-OPERATOR-DECISION 1 — what is `cursor-rules/` for?

- [x] ✅ [DOCS] P2. **RESOLVED 2026-08-08 (operator ruling, ao round-5 apply item 7 — see
      /plans/active/issues/ao_round5_apply_session_operator_qa_index_2026_08_08.md).** What is the 25-file
      `cursor-rules/` tree's purpose today, and should it be kept, repurposed, or archived?

  Verified fact (not in question): `cursor-rules/` (25 `.mdc` files, top-level dir) and `.cursor/rules/` (150 `.mdc`
  files, dot-dir) have **zero file overlap** — confirmed via basename spot-check across both trees. The real, current
  sync mechanism (`scripts/workspace/setup-cursor-rules-symlink.sh`) treats `.cursor/rules/` as the canonical,
  git-tracked source, symlinked OUT to sibling repos — its own header says "No sync scripts needed." Three docs
  previously claimed `cursor-rules/` syncs to `.cursor/rules/`; that claim was false and has been corrected
  (unified-trading-pm@c9dc2cfb5) to state the true mechanism without asserting what `cursor-rules/` is for, since that
  part is genuinely unknown from the evidence gathered.

  An archived plan (`plans/archive/agent_ci_prototype.plan.md:70`) shows a THIRD, even earlier wiring scheme
  (`.cursor/rules/` <- symlink <- `cursor-rules/`, the reverse direction) — so the mechanism has changed at least twice,
  and `cursor-rules/` may be a leftover from an earlier iteration that was never cleaned up.

  **A: Archive `cursor-rules/`** — if nothing reads from it today (grep confirms no script/CI job references the bare
  `cursor-rules/` path as a live input), it's dead weight from a superseded wiring scheme. [RECOMMENDED — simplest, and
  the evidence gathered so far didn't surface a live consumer, though this wasn't exhaustively proven] B: **Keep it as a
  staging/draft area** — e.g. new rules are authored in `cursor-rules/` first, then promoted into `.cursor/rules/` by a
  manual step not yet automated. If true, this should be documented explicitly (the "no sync scripts needed" comment on
  the symlink script would then need a caveat). C: **Something else** — a genuinely distinct, currently-undocumented
  purpose (e.g. a different tool consumes it, or it's scoped to a specific IDE/agent that isn't Cursor). Other: operator
  can type a custom answer.

  **CORRECTION (round5 ao investigation, 2026-08-08) — the "nothing reads from it" premise behind Option A is FALSE; a
  live CI consumer exists and was missed by all 4 prior read-only passes.**
  `.github/workflows/rules-alignment-agent.yml` ("Rules Alignment Agent") triggers on every push to `main` touching
  `plans/active/**` and its entire job is to search `cursor-rules/` for `.mdc` coverage of new plan constraints and
  auto-create missing ones there
  (`bash scripts/quickmerge.sh "chore: add cursor rules for new plan constraints" --files ...`) — its own header
  comment: "Keeps PM plans and cursor rules in sync automatically." Confirmed this workflow is genuinely LIVE, not
  stale/disabled: `gh run list --workflow=rules-alignment-agent.yml` shows it firing every ~15-20min (matching
  quickmerge promotion cadence) with `completed/success` on EVERY run through 2026-08-08 08:34 UTC, i.e. running today,
  well after the 2026-08-02 archival. Two real prior commits exist from this exact workflow (`92d0db96fa`, `0c52685ee2`,
  author `Rules Alignment Agent <rules-alignment-agent@ci.local>`) — but BOTH predate the archival (2026-06-03/04); zero
  such commits have landed since 2026-08-02 despite the workflow running successfully dozens of times against a target
  directory that no longer exists at its expected path. Spot-checked one recent full run log
  (`gh run view 31248707115 --log`) for errors — found none; the haiku-4-5 sub-agent appears to be gracefully no-op'ing
  (finding nothing worth flagging) rather than crashing, but this is inferred from absence of error output, not proven.
  **This changes the calculus materially**: the archival that already happened (see the docs-reconcile/na-eligibility
  Progress Log entries below) was made on the stated premise that no live consumer existed — that premise was wrong.
  Whether the right fix is (i) restore `cursor-rules/` so this workflow has a real target again, (ii) retarget/retire
  the workflow now that its target moved to `.cursor/rules/`, or (iii) confirm the graceful-no-op is intentional and
  leave both as-is, is a genuine operator call this investigation should NOT make unilaterally — NOT resolving this
  item, re-flagging it with materially new evidence instead of the closer-to-moot framing the 2026-08-03/06 entries left
  it in.

## 🚧 BLOCKED-OPERATOR-DECISION 2 — locked doc's broken `source:` field

- [x] ✅ [DOCS] P3. **RESOLVED (operator ruling 2026-08-08, ao round-5 apply item 8: "Authorize").** Fix (or authorize
      fixing) the broken `source:` frontmatter entry in
      `plans/active/issues/macro_micro_econ_data_capture_audit_2026_06_05.md` -- already applied as a side effect of an
      earlier cleanup commit, re-verified live: all 6 leading-slash entries present, no brace-expansion remains.

  That doc carries `locked_by: live-defi-rollout` in its own frontmatter — per the workspace HARD RULE, any edit
  touching a `locked_by:` doc's frontmatter needs operator sign-off, so this was NOT auto-fixed even though the fix
  itself is mechanical and low-risk.

  The defect: `source:` (line 24) contains
  `"unified-trading-pm/codex/02-data/{mtds-data-source-coverage-matrix,tradfi-data-types-catalog,defi-data-types-catalog,sports-data-source-coverage-matrix,prediction-data-types-catalog,honest_coverage_baseline_2026_05}.md"`
  — a brace-expansion shorthand for 6 files, all of which exist, but the literal string (a) carries a redundant
  `unified-trading-pm/` prefix (the citing doc is already inside that repo) and (b) uses shell brace-expansion syntax no
  path-existence checker can literally resolve, so it's permanently flagged broken regardless of the prefix fix.

  A: **Expand the one brace-syntax string into 6 separate `/codex/02-data/<filename>.md` leading-slash entries** in the
  `source:` list. [RECOMMENDED — matches how every other multi-file citation in this corpus is written, and each of the
  6 targets was independently verified to exist] B: Leave as-is (the baseline already tolerates it as pre-existing debt;
  low real-world cost since `source:` is a provenance field, not a navigation aid). Other: operator can type a custom
  answer.

## 🚧 BLOCKED-OPERATOR-DECISION 3 — 14 locked issue-docs with truncated `summary:` frontmatter (added 2026-08-06)

- [x] ✅ [DOCS] P2. **DONE (operator ruling 2026-08-08, ao round-5 apply item 9 — see
      /plans/active/issues/ao_round5_apply_session_operator_qa_index_2026_08_08.md: "Authorize all 14"; actually APPLIED
      2026-08-10 — see Progress Log, the 2026-08-08 entry's cited SHA `97ce494ecd` was a context-scout sweep commit that
      never touched these `summary:` fields; all 14 were still truncated until today).** Apply (or authorize applying)
      the pre-drafted replacement `summary:` on 14 `locked_by`-gated `plans/active/issues/*.md` docs — re-applied
      2026-08-10, see Progress Log for the real commit SHA.

  All 14 carry a real `locked_by` value (13× `live-defi-rollout`, 1× `harsh-fleet-audit`) — per the same HARD RULE as
  item 2 above, none were auto-fixed. This is a distinct, larger recurrence of the exact same gate, found by today's
  `/docs-reconcile --autonomous` sweep's summary-quality hunter (Phase 1) and independently re-verified programmatically
  (string length + `locked_by` re-check against live frontmatter, not just the hunter's report). 12 of the 14 are
  truncated at EXACTLY 200 characters — strong evidence of a mechanical cap applied at authoring/backfill time, not
  scattered human error; the other 2 are shorter but equally cut off mid-sentence/mid-link. All 14 replacement summaries
  below were derived by reading each doc's full body, not guessed from the title.

  | Doc (under `plans/active/issues/`)                                                    | Current tail (truncation point)         | Proposed replacement `summary:`                                                                                                                                                                                                                                                                                                                                                                                                                |
  | ------------------------------------------------------------------------------------- | --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  | `cve_affected_pinned_deps_remediation_2026_06_18.md`                                  | `...What breaks    ...` (raw table row) | Follow-up to lift the fleet-wide `--ignore-vuln` pip-audit CVE allowlist once each entry's real blocker clears — re-verifies every ignored CVE against current locked versions, drops moot/fixed entries, corrects stale mischaracterizations, and closes newly-found gaps (e.g. a missed fastapi/starlette bump).                                                                                                                             |
  | `backfill_vm_slack_alert_e2e_verification_2026_06_23.md`                              | `...With ~50 running VMs, that...`      | E2E verification of the backfill-VM Slack-alert path found four gaps: the heartbeat-stall watcher was OOM-killed every tick before writing its sentinel (fixed in code, not yet deployed), Python stdout/stderr isn't captured in Cloud Logging for fleet monitors/alerting, Slack delivery isn't end-to-end observable, and delivered alerts were generic because the UTL envelope was never unwrapped.                                       |
  | `batch_live_reconciliation_service_audit_2026_05_27.md`                               | `...what a...`                          | Full repo audit of batch-live-reconciliation-service (BLRS), the T+1 nightly batch-vs-live reconciliation orchestrator: documents its multi-stage DAG, data flow, and CLI/API surface, and catalogues codex↔code drift plus misplaced cross-repo responsibilities as ✅-decided vs ❓-needs-operator items tracked in §7.                                                                                                                      |
  | `capability_wizard_analysis_findings_2026_06_11.md`                                   | `...2026_06_11.m...` (broken mid-link)  | Running log of bugs, gaps-in-understanding, conflicting truths, and dual-but-different implementations found while building the capability wizard/manifest — companion to the gap-discovery tracker (which covers missing capabilities/registries instead); each finding tagged OPEN / FIXED / TRIAGED with evidence.                                                                                                                          |
  | `capability_wizard_gap_discovery_2026_06_11.md`                                       | `...agents only when...`                | Running pool of gaps surfaced while building the capability wizard/manifest — items are UNACKED scope that graduate into todos on the parent plan, taxonomized as missing_registry / missing_extraction / needs_code_scan / logical_dead_end; companion to the analysis-findings doc (which tracks bugs/conflicts).                                                                                                                            |
  | `defi_code_codex_drift_2026_05_27.md`                                                 | `...audit-resu...`                      | Actionable tracker for 13 code↔codex drifts (D1–D13) found re-reading the actual DeFi pipeline Python (MTDS/MDPS/UAC/features-service) against codex SSOTs — stale data-type names, legacy bucket prefixes, an unimported adapter, catalog gaps, banned-provider references, and more; full record in the companion audit-result doc.                                                                                                          |
  | `fleet_audit_triad_deferred_followups_2026_06_01.md`                                  | `...not to be actioned until...`        | Operator-deferred ('let it be') follow-up tail from the three 2026-05-27 fleet-audit plans (canonical_vm_log_archival, cefi_venue_backfill_coverage_remediation, deployment_ui_vm_and_venue_coverage_visibility) after they were archived — captures un-actioned items (e.g. archive crons never `tofu apply`'d) so nothing is silently lost; not to be worked until the operator activates it.                                                |
  | `fleet_data_acquisition_health_2026_06_21.md`                                         | `...(all data_ty...`                    | Operator-requested sweep of every data-acquisition VM lane's run.log (~75 VMs) on 2026-06-21: confirms all lanes running with zero fleet-wide rate-limiting, most lanes actively capturing data, and catalogues fixable code errors found per lane (cefi tick-schema validation, SOURCE_PRIORITY mismatches, mtds version-surface drift) with follow-up todos.                                                                                 |
  | `issue_docs_remediation_sweep_2026_06_02.md`                                          | `...Outcome: a large fraction of "...`  | Consolidated dispatch tracker from a 2026-06-02 code-audit of every plans/active/issues/*.md doc verifying each open claim against current code — a large fraction were already fixed after the docs were written; remaining real gaps are re-tracked here per-repo as canonical dispatchable todos, each source doc archived once its items here are verified complete.                                                                       |
  | `macro_micro_econ_data_capture_audit_2026_06_05.md`                                   | `...a whole tier of _fr...`             | Coverage audit of macro (economic-calendar) vs micro (market-structure) data capture: micro is captured well across nearly every asset group (L3/L4), macro is essentially TradFi-only and thin, and a free-tier vendor category is coded but not backfilled (capacity ≠ backfill) — includes a vendor cost/coverage refresh and an architecture-direction decision log.                                                                       |
  | `perp_funding_data_semantics_and_cadence_2026_06_16.md`                               | `...reads \`data_type=...\``            | Four correctness gaps in how perp funding is annualised and time-stamped, found building a carry_staked_basis analysis: two funding-cadence registries (UAC vs UTL) disagree and one is wrong, `funding_timestamp` is off by one settlement for most venues, the cadence table has no historical tracker, and DERIBIT's timestamp can't be safely derived from scratch — funding is a P0 input to net-carry ranking.                           |
  | `tradfi_backfill_oom_remediation_2026_06_24.md`                                       | `...a fresh tarball alone do...`        | Root-causes the 2026-06-24 `tradfi-bf-*` OHLCV backfill stalls (DP_VM_STALL) as an OOM crash-loop, not the databento chunk-decode hang some earlier fixes targeted — each fresh per-chunk process balloons to ~15GB within minutes on an e2-standard-4; documents the fix and tracks several later, mechanistically-distinct stall findings from follow-up verification.                                                                       |
  | `live_mode_event_sink_topic_missing_2026_06_21.md` (resolved)                         | `...crashed at startup with:`           | RESOLVED — the first-ever live MTDS launch crashed at startup because UTL's sink-factory derives the live lifecycle-event Pub/Sub topic as `{service_name}-events`, which terraform never provisions per-service (only a shared `service-lifecycle-events` topic exists) — a fleet-wide gap since no service had run live mode before; unblocked by creating the missing MTDS topic, same wall awaits every other service's first live launch. |
  | `instruments_service_sports_footystats_uac_overlap_qg_red_2026_07_30.md` (superseded) | `...both pre-existing...:`              | SUPERSEDED — duplicate discovery of the same instruments-service QG-RED blocker (FOOTYSTATS violates the IS/UAC sports-venue disjointness invariant + a golden-fixture drift) already filed, more completely, in the archived `instruments_service_qg_red_uac_sports_venue_overlap_2026_07_30.md`; kept for corpus trail only, do not dispatch its todos.                                                                                      |

  A: **Apply all 14 replacements as-is** (each was derived from the doc's own full body, not guessed). [RECOMMENDED —
  all 14 are pure `summary:` frontmatter swaps, zero body/content changes, lowest-risk field on a locked doc] B:
  **Unlock the 14 docs first** (clear `locked_by`/`locked_since` if the lock is stale — 10 of 14 have no `locked_since`
  at all, and the 4 that do are 2+ months old as of 2026-08-06), then let the next docs-reconcile run auto-fix them
  normally. C: **Leave as-is** — the truncation is cosmetic (L2 retrieval degradation only, not a correctness bug) and
  not worth an exception to the locked-doc rule. Other: operator can type a custom answer.

## 🚧 BLOCKED-OPERATOR-DECISION 4 — Fireblocks custody credential rotation cadence: two SSOTs disagree (added 2026-08-08)

- [ ] [DOCS] P0. **Reconcile the Fireblocks RSA rotation cadence between `credentials-matrix.md` and
      `credential-rotation-runbook.md` — pick the correct number and fix the other doc to match.**

  Found by the 2026-08-08 `/docs-reconcile --autonomous` sweep's `authoritative_for` collision hunter, independently
  re-verified against both live docs (not just the hunter's report) before parking. Both docs declare
  `authoritative_for: [credential rotation cadence...]` and both are `status: current`:

  - `/codex/05-infrastructure/credentials-matrix.md` § 1 (Custody row): **"60d for HMAC creds; quarterly for Fireblocks
    RSA"** — explicitly carves Fireblocks RSA out of the 60d HMAC bucket into its own ~90d cadence.
  - `/codex/15-runbooks/credential-rotation-runbook.md` § 1 (Custody row, labeled "Copper / Fireblocks / CEFFU HMAC +
    JWT"): **"60d"** — no carve-out, Fireblocks lumped into the uniform 60d bucket.

  This is NOT a resolution-logic false positive — I read both tables directly and the numbers genuinely disagree for the
  same named provider/credential (Fireblocks custody creds). One candidate explanation the runbook's own row label
  suggests: it calls the row "HMAC + JWT," but `credential-rotation-runbook.md` §3.2 elsewhere describes Fireblocks as
  using an **RSA PEM**, not HMAC/JWT — so the runbook's Custody row may have been written for Copper/CEFFU specifically
  and Fireblocks may have been swept in under the same row by mistake, rather than the cadence itself being a deliberate
  disagreement. I have no way to confirm that read without knowing which cadence Fireblocks' custodian API actually
  enforces/expects — a security-operational fact, not something derivable from the docs alone. This is exactly the class
  of `authoritative_for` collision this skill's own contract forbids auto-resolving in any mode (evidence can show the
  collision exists but not which side is right).

  A: **`credentials-matrix.md` is correct (quarterly for Fireblocks RSA)** — fix `credential-rotation-runbook.md`'s
  Custody row to carve out Fireblocks separately from Copper/CEFFU HMAC, matching the RSA-vs-HMAC distinction §3.2
  already draws. [Weakly favored — the runbook's own §3.2 describes Fireblocks as RSA-based, and a distinct key-type
  plausibly warrants a distinct cadence, but this is not a confident recommendation.] B:
  **`credential-rotation-runbook.md` is correct (uniform 60d)** — fix `credentials-matrix.md`'s Custody row to drop the
  Fireblocks carve-out. C: **Neither — the real cadence is something else entirely** (e.g. whatever Fireblocks' own
  API/dashboard actually enforces), and both docs need updating to match. Other: operator can type a custom answer.

## 🚧 BLOCKED-OPERATOR-DECISION 5 — `plan-hygiene.md` duplicated verbatim in two dirs, both `authoritative_for` "plan hygiene" (added 2026-08-09)

- [ ] [DOCS] P1. **Decide the disposition of `/codex/12-agent-workflow/plan-hygiene.md` vs
      `/codex/11-project-management/plan-hygiene.md` — merge, split with cross-links, or re-scope one's
      `authoritative_for` claim.**

  Found by the 2026-08-09 `/docs-reconcile --autonomous` sweep's `authoritative_for` collision hunter, independently
  re-verified against both live docs before parking. Both `status: current`, both literally titled "Plan Hygiene":

  - `/codex/12-agent-workflow/plan-hygiene.md` — title `Plan Hygiene — Silent Failure Modes, Tags, Crons, and Severity`,
    `authoritative_for: [plan-hygiene 4 silent-failure modes, hygiene-sweep severity ladder]`.
  - `/codex/11-project-management/plan-hygiene.md` — title `Plan Hygiene — Scripts, Runbook, and Cron`,
    `authoritative_for: [plan-hygiene script suite (structural checks), required/deprecated plan frontmatter field list]`.

  Both describe the same underlying system (`run_hygiene_sweep.sh`, cron cadence, the retired GHA
  `plan-health-agent.yml` job folded into `quality-gates-v2` — the retirement event is described almost verbatim in both
  bodies). Neither doc's `related:` frontmatter cross-references the other — the disambiguation signal present in every
  legitimate parent/child split found elsewhere in this same sweep (e.g. `portfolio-allocator.md`'s two docs mutually
  cross-reference; `mev-protection.md`'s pair has an explicit "canonical SSOT" self-declaration + `referenced_by:`). The
  12-agent-workflow doc DOES cross-reference the 11-project-management one twice inline in prose (§ "Daily deep
  reconciler", § "Plan-health PR gate") — so the author was aware of the overlap but never resolved it structurally.
  `rg -l '^authoritative_for:.*plan-hygiene' codex/` today returns both with no signal for which to open for a generic
  "plan hygiene" query — the exact retrieval-correctness break this field exists to prevent.

  A: **Merge into one doc.** The 11-project-management doc is scripts/runbook/cron-focused (mechanics); the
  12-agent-workflow doc is silent-failure-modes/severity-focused (why it matters + what breaks). Fold one into the other
  (whichever section location fits this corpus's `codex/NN-*` topic convention better) and redirect the other to a thin
  pointer, matching the precedent this same doc used for the `naming-convention.md` → `strategy-identity-versioning.md`
  merge (BLOCKED-OPERATOR-DECISION analog, resolved 2026-07-31). [Not marked RECOMMENDED — both docs are substantial
  (not one clearly a stub) and cover genuinely distinct sub-topics, so a merge may lose useful separation; flagging as
  an option, not the default.] B: **Keep both, add explicit cross-references and narrow each `authoritative_for` claim
  to be unambiguous** (e.g. 12-agent-workflow keeps "silent-failure modes + severity ladder", 11-project-management
  keeps "script suite + frontmatter field list" — genuinely non-overlapping if stated precisely, since the current
  claims already gesture at a split, they're just not cross-linked). [RECOMMENDED — lower-risk than a merge, preserves
  both docs' distinct content, and only requires adding `related:` entries + tightening the `authoritative_for:` wording
  rather than a content migration.] C: **Something else** — e.g. one doc is actually stale/superseded and should be
  archived outright. Other: operator can type a custom answer.

## Progress Log

- 2026-08-02 (docs_reconciler, dispatch agt-0b4ee1): filed. 4 other commits from this same sweep already shipped
  (unified-trading-pm@7de163bf1, @50f2e668b, @c9dc2cfb5, @809a28c97) covering everything that WAS auto-fixable — see the
  sweep's Phase 5 report for the full breakdown.
- **na-eligibility-audit 2026-08-02** (infra tranche, dispatch agt-fe5e17): KEEP-NA, valid — both items are explicit
  `BLOCKED-OPERATOR-DECISION` authority calls (A/B/C options, no evidence-determined single answer) per this doc's own
  title and framing. Textbook KEEP-NA, no re-derivation needed.
- **docs-reconcile 2026-08-03** (dispatch agt-fd4e6d) — NOT resolving BLOCKED-OPERATOR-DECISION 1 myself, but flagging
  strong circumstantial evidence it may already be moot: commits `unified-trading-pm@b45eab084` /`@d4f7fab9d`
  (2026-08-02 23:26-23:27, "apply operator rulings on 2026-08-02 scheduled-audit-batch operator-decision queue") deleted
  the top-level `cursor-rules/` tree entirely and moved all 25 files verbatim into
  `plans/archive/cursor-rules_2026_08_02/` — the exact action Option A here recommended, under a matching archive-date
  slug. Neither commit message names this issue doc explicitly, so this is circumstantial, not proof (hence not
  auto-closing the checkbox) — but if the operator confirms that archival WAS the intended resolution, this item and
  `pm-repo-context.mdc`'s "unresolved — flagged for operator review" note (line 29) both need a one-line update to say
  RESOLVED instead of leaving both artifacts stale.
- **context-scout 2026-08-03**: populated context_scope (4 entries).
- **na-eligibility-audit 2026-08-03** (ao tranche): ARCHIVE-eligible on content, still PARKED — not archiving this run.
  Independently re-verified BOTH items resolved on disk: item 1 — the entire top-level `cursor-rules/` tree is confirmed
  physically absent (`find`), moved verbatim to `plans/archive/cursor-rules_2026_08_02/` by
  `unified-trading-pm@b45eab084`/`@d4f7fab9d`, exactly Option A. Item 2 —
  `macro_micro_econ_data_capture_audit_2026_06_05.md`'s `source:` field brace-expansion string is confirmed expanded
  into 6 separate `/codex/02-data/<filename>.md` leading-slash entries (full diff read, not just `git blame`), exactly
  Option A. BUT went one step further than the 2026-08-03 docs-reconcile entry above and checked
  `plan_reconcile_parked_operator_decisions_2026_08_02.md` — the doc both commits' messages point to as the "2026-08-02
  scheduled-audit-batch operator-decision queue" source of truth — for an explicit ruling entry on either item: **zero
  hits for "cursor-rules", "macro_micro_econ", or this doc's own filename.** Separately, item 2's fix landed as a side
  effect of a BROADER 3-string brace-expansion cleanup in the same commit (2 of the 3 expanded strings — the
  `unified-api-contracts` registry ones — were never even flagged by this issue), not a targeted fix — further weakening
  the "this was a deliberate ruling on THIS item" reading vs. "a general mechanical cleanup pass happened to also
  satisfy it." Three independent read-only passes now (docs-reconcile 2026-08-03, this audit) agree the evidence is
  strong but not traceable to a recorded ruling, and item 2 involves a `locked_by:` doc's frontmatter edit with no
  sign-off record found — staying conservative on a semi-irreversible action (archival = `git mv` + corpus-wide referrer
  rewrites) rather than resolving the ambiguity myself. Leaving `.cursor/rules/pm-repo-context.mdc:29`'s "unresolved"
  note untouched too, for the same reason — let one operator confirmation trigger both updates together, as this doc's
  own 2026-08-03 entry already anticipated. **Escalating for explicit confirmation:**

  Should this doc be archived now, given both BLOCKED-OPERATOR-DECISION items appear resolved on disk but neither traces
  to a recorded ruling?

  A: Confirm both resolutions ARE the intended outcome — archive this doc now (6-step ritual). [Evidence supports this,
  but item 2 touching a locked doc's frontmatter without a traceable sign-off record makes it genuinely the operator's
  call, not a worker inference.] B: The resolutions are coincidental/unrelated to this doc's specific asks — reopen with
  corrected framing reflecting what actually happened. C: Something else — operator has context these three read-only
  passes don't. Other: operator can type a custom answer.

- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **docs-reconcile 2026-08-06** (dispatch agt-cea8ef): independently re-confirmed items 1 and 2's underlying facts a
  4th/3rd time (own `find` + frontmatter re-parse, not a re-read of this doc's prior entries). Made ONE narrow, factual
  edit distinct from resolving BLOCKED-OPERATOR-DECISION 1 itself: `.cursor/rules/pm-repo-context.mdc:26-29` previously
  read as though whether `cursor-rules/` still exists were itself unresolved ("What `cursor-rules/` is for today is
  unresolved — flagged for operator review" with no mention it had already been archived) — that framing is stale and
  actively misleading to a fresh reader four days after the archival, independent of the still-fully-open "what should
  replace it" question. Updated it to state the archival as the now-undisputed fact it is (3 independent audit passes
  agree) and point here for the still-open follow-on question, WITHOUT touching BLOCKED-OPERATOR-DECISION 1's own open
  A/B/C framing above and WITHOUT archiving this issue doc (both stay exactly as prior passes left them, pending the
  explicit confirmation already requested 2026-08-03). Flagging the deviation from "leave `pm-repo-context.mdc`
  untouched too" explicitly here in case the operator disagrees with drawing that line — easy to revert
  (`unified-trading-pm` history has the prior wording). Added BLOCKED-OPERATOR-DECISION 3 (14 locked docs, truncated
  `summary:` frontmatter) — a same-gate recurrence found by this run's Phase 1 summary-quality hunter, independently
  re-verified (string length + live `locked_by` re-check) before parking rather than auto-fixing. Full Phase 5 report in
  this run's `/done` evidence + chat transcript (dispatch agt-cea8ef).

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **docs-reconcile 2026-08-08** (dispatch agt-bb1c67): added BLOCKED-OPERATOR-DECISION 4 (Fireblocks rotation-cadence
  contradiction between `credentials-matrix.md` and `credential-rotation-runbook.md`) — found by this run's Phase 1
  `authoritative_for` collision hunter (4 candidate collisions surfaced corpus-wide; 3 were content-consistent overlaps
  reported separately in this run's Phase 5 chat report, this is the 1 genuine content contradiction). Independently
  re-verified both docs' actual tables + the runbook's §3.2 RSA-vs-HMAC distinction before parking, per this run's own
  standard of not just trusting a sub-agent's report. Bumped this doc's frontmatter `priority` P2→P1 to reflect the new
  item's severity (security-relevant credential class); did not touch items 1-3's own priority framing.
- **docs-reconcile 2026-08-08, re item 3**: this run's OWN Phase 1 summary-quality hunter independently re-swept the
  full corpus (not primed with this doc's existing findings) and surfaced the exact same 14 docs with the exact same
  200-char truncation defect. Cross-checked all 14 `locked_by` fields live before considering any fix — all 14 still
  carry a real lock (13× `live-defi-rollout`, 1× `harsh-fleet-audit`), so none were touched; this is a re-confirmation
  that item 3's park is still current, not a new finding. Also traced the root cause precisely this run:
  `scripts/plan-hygiene/fix_frontmatter.py::get_first_paragraph_after_heading()` hard-truncates at char 197 + "..." with
  no word/sentence-boundary awareness (verified by reading the function directly) — filed as a standalone P2 finding in
  `docs_reconcile_remaining_broken_links_2026_08_02.md` (a script-tooling fix, not a doc-content fix, so out of scope
  for the item-3 sign-off itself) rather than duplicated here.
- **na-eligibility-audit 2026-08-08** (ao tranche): KEEP-NA, valid — `grep -cE '^[[:space:]]*[-*] \[ \]'` = **4**,
  matching. All 4 items are explicit `BLOCKED-OPERATOR-DECISION` A/B/C(/D) authority calls per the doc's own framing
  (items 1-3 unchanged; item 4, added today, is a genuine security-relevant content contradiction the docs-reconcile
  entry above already correctly declined to guess at). Textbook KEEP-NA, no re-derivation needed.

- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (6 entries), still accurate.
- **docs-reconcile 2026-08-09** (one-off `docs_reconciler` boot, slot 27): added BLOCKED-OPERATOR-DECISION 5
  (`plan-hygiene.md` duplicated verbatim across `codex/12-agent-workflow/` and `codex/11-project-management/`) — found
  by this run's `authoritative_for` collision hunter (16 duplicate-basename/fuzzy-topic groups examined corpus-wide, 15
  disqualified as either status-mismatched or legitimate parent/child splits with proper `related:` cross-links; this is
  the 1 genuine collision). Independently re-verified both docs' `status`/`authoritative_for`/`related` frontmatter live
  before parking, not just trusted from the hunter's report.
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 1)**: KEEP-NA, valid — first na-eligibility-audit pass
  since item 5 was added. Both remaining open items (4: Fireblocks rotation-cadence contradiction; 5: plan-hygiene.md
  duplication) are explicit `BLOCKED-OPERATOR-DECISION` A/B/C authority calls per the doc's own framing, no
  evidence-determined single answer for either. Textbook KEEP-NA.
