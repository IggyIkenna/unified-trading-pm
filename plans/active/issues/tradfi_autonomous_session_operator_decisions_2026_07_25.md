---
doc_type: issue
title: "TradFi /autonomous session (2026-07-25) — queued operator decisions"
summary: >-
  Operator dispatched an 8-hour /autonomous session to resume tradfi_consolidated_closeout_2026_07_18.md and its 3
  children, with explicit instruction to queue genuine operator-decision items in writing rather than block on them
  (operator was leaving the desk). This doc is that queue. Each item below is something this session found that is
  either an explicit pre-existing BLOCKED-OPERATOR-DECISION in the source plans, or a new judgment call this session
  surfaced but did not decide unilaterally. Everything else the session COULD decide from documented intent, it did —
  see the 3 tradfi plan docs' Progress Log sections for the executed work.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, instruments-service, deployment-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: [tradfi, operator-decision, autonomous-session, canonicalisation, ice, chain-bundle]
related:
  [
    tradfi_consolidated_closeout_2026_07_18,
    tradfi_manifest_content_recovery_completion_2026_07_24,
    tradfi_backfill_throughput_followups_2026_07_24,
    tradfi_phase_d_terminal_gate_2026_07_24,
    tradfi_chain_bundle_sampler_root_mismatch_2026_07_23,
  ]
created: 2026-07-25
parent_epic: tradfi_master
priority: P1
source:
  "Operator, 2026-07-25 — dispatched /autonomous with an explicit instruction to keep working for up to 8 hours and
  queue any genuinely operator-owned decisions in writing (structured, answerable async) rather than block waiting for a
  synchronous answer, since the operator was stepping away from the desk."
assigned_vm: NA
execution_scope: local-only
locked_by:
resolved_by:
drift_direction: none
depends_on: []
---

# TradFi /autonomous session (2026-07-25) — queued operator decisions

> Read this doc top-to-bottom when you're back. Nothing below blocked the session's other work — everything unblocked
> kept moving in parallel (see the 3 tradfi plan docs' Progress Logs for what shipped). These are the items that are
> genuinely yours to decide.

## 1. ICE qualifier variants — population is much bigger than previously known [RECOMMEND OPTION A]

**Pre-existing decision, not new** — this was already flagged `BLOCKED-OPERATOR-DECISION` in
`tradfi_manifest_content_recovery_completion_2026_07_24.md` before this session started. What's new: this session's live
catalogue + by-day-corpus full-sweep (2026-07-25) measured the REAL scale for the first time, and it is much larger than
the catalogue-only estimate the plan had been citing.

- Catalogue (`prod/catalog.parquet`): 1,063 ICE-qualifier-variant rows.
- Per-day corpus (`instrument_availability/by_date/`, 27,142 files, full sweep): **269,520 ICE-qualifier-variant rows**
  — 254x the catalogue-only figure, and the dominant share (99%) of that surface's entire 272,616-row quarantine
  population.

The defect: the classifier + current writer emit `ICE:FUTURE:BRN_Z-USD@LIN-...` with banned characters (`_`, `!`)
because Databento's ICE symbols carry a qualifier suffix (`BRN_Z`/`BRN!`/`BRN_MD1`) that `EXCHANGE_CODE_TO_NAME` only
maps for the bare root. ICE is NOT in the tradfi MVP universe, so none of this blocks MVP backfill readiness — but
269,520 rows is a real, now-quantified data-quality gap worth a decision rather than indefinite quarantine.

**Options:**

- **A (recommended — matches the existing plan's own recommendation): qualifier-normalize + map the base root.** Strip
  the qualifier suffix, resolve via the existing base-root map, keep the qualifier as separate metadata if needed. Fixes
  the defect at the source; largest population addressed.
- B: Accept `_qualifier` as a permitted id-shape exception for ICE only, relax the canonical-shape gate for this one
  venue.
- C: Leave ICE permanently quarantined (defer indefinitely) — cheapest, but leaves 269,520 rows honestly-absent from
  every canonical read/count for a venue that's a real (if non-MVP) part of the data estate.
- Other: your call.

## 2. Chain-manifest recovery — retire-phase 50,520-row `--apply` still needs your review

**Pre-existing, unchanged since 2026-07-22/23** — `tradfi_manifest_content_recovery_completion_2026_07_24.md`'s
P1-OPERATOR-REVIEW todo. The register phase (1,545 rows) is done and durability-reverified by this session (still
`captured` in a fresh live read). The retire phase — dropping 50,520 now-superseded raw `futures_chain`/ `options_chain`
manifest rows via a single in-place-CAS whole-index REPLACE — was deliberately never `--apply`'d, per direct prior
operator instruction ("do NOT --apply retire without further review").

**This session did NOT re-run the retire dry-run** (out of scope for what was actioned this pass — the session focused
on the casing/catalogue/phantom items instead). The plan's own text already warns the candidate list goes stale after "a
day or two" — **whoever applies this must re-run the `--retire` dry-run first** to get a fresh candidate list before
deciding.

**Options:** A: review + approve as-is once re-dry-run confirms the list is materially unchanged. B: review + request
changes. C: defer further. Other.

## 3. Chain-bundle canonical-root → raw-Databento-symbol reverse translation — `EXCHANGE_CODE_TO_NAME` SSOT contradiction

**Pre-existing, blocking the Phase-D MVP backfill readiness gate** —
`tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md` §4. The chain-bundle sampler passes a now-canonical
`underlying` (e.g. `"AUD"`) to CME/GLBX.MDP3, whose curated symbol list expects the raw exchange code (`"6A"`) — fixing
this needs resolving a contradiction between two UAC files over what `EXCHANGE_CODE_TO_NAME` should say. This session
did not touch it (not re-investigated this pass; no new information beyond what's already in that issue doc). It remains
the sole named blocker on `tradfi_phase_d_terminal_gate_2026_07_24.md`'s P0 MVP backfill readiness todo — until it's
resolved (or you explicitly accept current evidence as sufficient), that gate stays blocked.

**Options:** A: resolve the SSOT contradiction (read the issue doc §4 for the two conflicting files, pick one). B:
explicitly accept the current Phase-D evidence as sufficient and unblock the MVP backfill gate without fixing this.
Other.

## 4. Legacy-twin bucket deletes — still a hard stop, not re-raised, just confirming it's still parked correctly

`tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md` — `BLOCKED-OPERATOR-DECISION`, Ikenna's migration sign-off
gates this. Untouched this session, correctly (never autonomous per the workspace HARD RULE). No action needed from you
unless you want to move on it; just confirming this session didn't touch it.

## What this session DID decide from documented intent (informational, not asking)

- The manifest `instrument_type` casing residual (45,681 rows re-drifted post-2026-07-22 CAS run) was fixed per the
  already-RULED D1/casing-directive UPPERCASE target — no new decision needed, just execution.
- The catalogue Surface-A re-sweep (both `prod/catalog.parquet` and the by-day corpus) was executed per the
  already-decided `-USD@LIN` target shape from the 2026-07-18 operator ruling.
- The CF-11 phantom `attempted_failed` retirement routed rows to `EXPECTED_INSTRUMENT_NOT_LISTED` /
  `EXPECTED_SOURCE_DELIVERY_LAG` per the already-fixed live emitter's own convention (BLK-d385496b answer B, 2026-06-28)
  — no new taxonomy decision, just applying the existing one to historical residue.

---

# Appended 2026-07-26 — `/plan-reconcile` (tradfi tranche, autonomous) parked decisions

> Added by an autonomous `/plan-reconcile` run scoped to the tradfi tranche (68 tradfi-tagged docs; 37 tradfi-PRIMARY,
> `asset_group: [tradfi]`). Everything that run could prove from git / gcloud / grep it fixed directly (see
> `unified-trading-pm@c78e4a596`). The 5 items below are the ones evidence genuinely cannot settle — they are authority,
> preference, or blast-radius calls, exactly the class the skill's Phase-4 routing table reserves for a ruling. Same
> format as items 1-4 above: options with the recommendation marked.

## 5. Eight tradfi AO plans (49 open todos) are `status: draft` while batch3 is `active` — flip, or keep staged? [RECOMMEND OPTION B]

**The two sides.** `plans/active/tradfi_satellite_ao_dispatch_batch3_2026_07_26.md:16` is `status: active` +
`assigned_vm: planning` (dispatched). But every earlier tradfi AO plan is still `status: draft` — therefore NOT
ingested, NOT dispatched, nothing working them: `tradfi_satellite_ao_dispatch_batch1_2026_07_25.md:15` (5 todos),
`…batch1_finalize_2026_07_25.md:10` (3), `…batch2_2026_07_25.md:16` (11), `…batch2_finalize_2026_07_25.md:12` (3),
`tradfi_registry_coverage_and_ao_readiness_2026_07_25.md:20` (11), `…_finalize.md:18` (3),
`tradfi_consolidated_native_ao_extract_2026_07_25.md:19` (10), `…_finalize.md:12` (3) = **49 open todos, zero
dispatched.**

**Why it matters (not cosmetic).** batch3's own Deferred section defers
`tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md` on the grounds that batch2_finalize "already owns the job of
re-checking" it. That is only true if batch2_finalize is live. It is draft — so that deferral currently has **no live
owner** (this run corrected the "(active)" mislabel in batch3 itself; the ownership gap is the residue).

**Options:**

- A: Flip all 8 (batch1/batch1_finalize/batch2/batch2_finalize + the 4 forked children) to `status: active` now — the
  fastest drain, but 49 todos land on the fleet at once alongside batch3's 9.
- **B [WORKER REC]: Flip only `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md` + its finalize to `active`** (batch2
  is the one batch3 structurally depends on for the mvp_mode re-check ownership), leave batch1 and the 4 forked children
  draft until batch2+batch3 drain. Restores the broken ownership chain with the smallest blast radius.
- C: Keep all 8 draft deliberately (they are a staged backlog, not a queue) — but then batch3's mvp_mode deferral needs
  a different owner named explicitly.
- Other: your call.

## 6. `phantom_captures_tradfi_2026_06_28.md` — tagged `cross-cutting`, content is 100% tradfi [RECOMMEND OPTION A]

**The two sides.** `plans/active/issues/phantom_captures_tradfi_2026_06_28.md:7` declares
`asset_group: [cross-cutting]`, yet every fact in the doc is tradfi-only — its own summary names
`gcp://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet`, its provenance line is
`reconcile_phantom_manifest_rows_all.py --asset-group tradfi --dry-run`, and its venue table is CBOE/NYSE/CME/ICE/
NASDAQ/FX. Against that, `plans/active/cross_cutting_consolidated_closeout_2026_07_25.md:561` deliberately claims it as
a Track-22 source: "— both from the G3 phantom-manifest audit (`reconcile_phantom_manifest_rows_all.py`)", grouped with
`phantom_captures_prediction_2026_06_28.md`.

**Why it needs you.** Both classifications are dated and deliberate, so this is ownership, not a typo. It is also the
exact mistag class `/ag-closeout-audit` warns creates an invisible orphan. Retagging has a mechanical side effect:
`check_ag_closeout_linkage.py` is at **0 orphans (baseline 0)** and must stay there, so any retag must land together
with its linkage line. (Tradfi's side already holds — `tradfi_consolidated_closeout_2026_07_18.md:380` links it.)

**Options:**

- **A [WORKER REC]: Retag `asset_group: [tradfi]`** and convert the cross-cutting Track-22 bullet into a cross-reference
  ("tradfi-owned; listed here because it shares the G3 monitor with the prediction instance"), then re-run
  `check_ag_closeout_linkage.py` and confirm 0 orphans before shipping.
- B: Keep `[cross-cutting]` — Track 22 is "outputs of the standing G3 phantom monitor", a genuinely cross-AG grouping,
  and the per-AG instances are just its rows.
- C: Dual-tag `[tradfi, cross-cutting]` — rejected by the orthogonality rule (falls out of BOTH audits), listed only so
  the option is explicitly ruled out.
- Other: your call.

## 7. An AO todo that launches a billed VM with neither `[OPERATOR]` nor a stated justification [RECOMMEND OPTION A]

**The two sides.** `plans/active/tradfi_satellite_ao_dispatch_batch2_2026_07_25.md:141-147` (`assigned_vm: planning`)
reads: "(1) Verify instruments-service CME (GLBX.MDP3) instrument-definition catalog manifest coverage … **launch a
backfill shard for any real gap** (never copy definitions between dates — CME futures expire daily)." Against that,
`cursor-configs/CLAUDE.md` § Plans: "**every AO todo with a GCS delete/`--apply` or VM launch needs
`[OPERATOR]`+delete-safety-cite OR a stated safe-idempotent justification**". The todo is tagged `[REVIEW] P1` and
carries neither. (The mechanical pre-filter `check_delete_vm_launch_gating.sh` DID flag this doc — adjudicating it is
this skill's job, and the adjudication is: real, not a false positive. The other two tradfi flags in that run ARE false
positives: batch1's `[DOC] P1` launcher-naming todo is self-declared "doc-only scoping addition", and batch2's
`[DATA] P1` consolidator-SSOT todo matched only on a historical narrative's `--apply`.)

**Options:**

- **A [WORKER REC]: Add the stated safe-idempotent justification** rather than an operator gate — cite
  `/codex/05-infrastructure/spot-vms-for-backfill.md` (SPOT default, idempotent shards re-run on preemption) and name
  the launcher + a shard-count bound. Routine backfill shards are the established autonomous pattern; requiring sign-off
  per shard would stall the AG.
- B: Re-tag the sub-item `[OPERATOR]` and require explicit approval before any launch.
- C: Split sub-item (1) out of the 7-item bundle into its own todo so the gate applies only to the launching half.
- Other: your call.

## 8. `tradfi_consolidated_closeout_2026_07_18.md` is near-complete (1 open todo) — fold + archive, or keep as the index? [RECOMMEND OPTION B]

**The two sides.** The plan is `status: active`, `locked_by:` empty, and has exactly **1** open todo —
`plans/active/tradfi_consolidated_closeout_2026_07_18.md:234`: "[DATA] P2. Determine, per MVP cell in the table above,
whether it has actually been proven wired through backfill=paper=live…". An AO-dispatchable derivative of that same todo
already exists at `plans/active/tradfi_consolidated_native_ao_extract_2026_07_25.md:104`. Against archiving: the doc's
own frontmatter calls it a "Coordination index (umbrella) that AGGREGATES (references, does not duplicate) every open
tradfi + tradfi-touching" plan, it is the linkage anchor for the whole tranche, and it `depends_on` two still-active
children. Per the skill's Phase 4, where a near-complete remnant folds is operator-gated and never autonomous.

**Options:**

- A: Fold the remnant into `tradfi_consolidated_native_ao_extract_2026_07_25.md` (where its derivative already lives)
  and archive the shell via the 6-step ritual.
- **B [WORKER REC]: Keep it as the tranche coordination index** — it is explicitly an umbrella, its aggregated-source
  list is what `check_ag_closeout_linkage.py` resolves against, and archiving it would orphan that. Instead mark the one
  open todo as tracked-elsewhere (pointing at the native-extract derivative) so the doc reads as an index, not a
  work-holder.
- C: Archive now and re-home the linkage anchor onto a new `tradfi_consolidated_closeout_aggregated_sources_*.md` (the
  pattern cefi/defi already use).
- Other: your call.

## 9. Three Deferred entries in the ACTIVE batch3 plan are truncated mid-sentence [RECOMMEND OPTION A]

**The two sides.** `plans/active/tradfi_satellite_ao_dispatch_batch3_2026_07_26.md` lines 208, 215 and 232 each end in a
literal `...` mid-sentence — e.g. line 208: "…which is STILL OPEN (verified live:
`status:...", line 232 (the file's last line): "…features-service@34a5d4ff + mdps@7d630a3, per the now-archived...". Against that, the `/ag-closeout-audit`
methodology this doc was produced by states that the NEXT batch re-reads exactly these entries first: "Before fresh
Phase-1 triage, re-check the PRIOR batch's own Deferred section first. Every conflict-gated item there names the
specific competing claim it collided with." A truncated entry cannot be re-checked — the competing claim is the part cut
off.

**Why it needs you.** The truncation is provable; the missing text is not derivable — only the authoring session knows
what each sentence was going to say, and rewriting another session's just-committed reasoning is not a mechanical fix.

**Options:**

- **A [WORKER REC]: Have the batch3 authoring session (or a fresh `/ag-closeout-audit tradfi` pass) re-emit the 3
  Deferred entries in full**, before batch3_finalize's deferred-re-check todo runs against them.
- B: Accept as-is and let batch3_finalize's re-check todo re-derive each conflict from scratch (costs a full re-triage
  of those 3 docs).
- C: Delete the 3 truncated entries and re-triage those docs into batch4 as if never deferred.
- Other: your call.

## Open todo

- [ ] [PM] P2. Once you've answered items 1-3 above, record the decision inline in this doc (flip to resolved) and
      propagate into the relevant plan doc(s)' todos per the standing "plan references, doesn't duplicate" rule.
- [ ] [PM] P2. Same for items 5-9 (appended 2026-07-26 by `/plan-reconcile`, tradfi tranche): record each decision
      inline here and propagate into the named plan doc(s). Items 5 and 7 additionally need their target plans'
      frontmatter / todo tags edited to match the ruling; item 6 must re-run
      `scripts/plan-hygiene/check_ag_closeout_linkage.py` and confirm 0 orphans in the SAME commit as any retag.

## 10. TIME-CRITICAL — the legacy-bucket delete was 2026-07-14, not 2026-07-06; your soft-delete check is more likely to succeed than the doc says [RECOMMEND OPTION A]

**Appended 2026-07-26 by `/ag-closeout-audit` (tradfi tranche, autonomous pass). This is not a design question — it is
one read-only command only you can run, plus a measured correction that changes its urgency.**

`plans/active/issues/tradfi_legacy_bucket_deleted_without_also_legacy_migration_2026_07_26.md` (P0, data-loss) says the
legacy `market-data-tick-tradfi-central-element-323112` bucket was "permanently deleted 2026-07-06", and computes its
TIME-CRITICAL recovery-window item as "20 days ago". **A Cloud Audit Log read this session shows exactly ONE
`storage.buckets.delete` for that bucket over a 120-day window: `2026-07-14T11:03:03.648128088Z`, principal
`ikenna@odum-research.com`.** So it is **12 days ago, not 20** — and it happened 3 minutes before that day's ICE-purge
consolidator pause, i.e. during your 2026-07-14 session, not as part of the 2026-07-06 v9 apply. Full evidence is
appended as a dated addendum to that issue doc (append-only; nothing above it was edited).

Why it needs you specifically: the audit probed and confirmed the gate is real, not a false block —
`gcloud alpha storage buckets list --soft-deleted --project=central-element-323112` returns
`HTTPError 403: unified-trading-sa@... does not have storage.buckets.list access`, while
`gcloud alpha storage buckets describe gs://market-data-tick-tradfi-central-element-323112 --soft-deleted` returns
`HTTPError 400: Bucket generation is required` (a 400, not a 403 — the only missing input is the generation, and only
the 403-denied list call yields it). No available worker credential can close this loop; one command from you can.

- **A [WORKER REC]: run `gcloud alpha storage buckets list --soft-deleted --project=central-element-323112` first
  thing.** At the GCS default 7-day retention the window is closed either way, but any configured retention of 14+ days
  (the range is 7-90) leaves it OPEN at 12 days — and the census evidence already in that doc found a real structural
  uncovered slice (pre-2023 tradfi `trades`/`tbbo` + options/futures chain snapshots) that canonical's Databento source
  cannot retroactively capture. If a generation comes back, the restore decision is yours; if nothing comes back, the
  window is provably closed and the doc's remaining `[OPERATOR]` P0 collapses to "accept the loss with the census
  evidence".
- **B: grant `storage.buckets.list` on `central-element-323112` to `unified-trading-sa` and let a worker run it.**
  Slower to set up, but makes this class of check autonomous next time.
- **C: skip the check and rule on the census evidence alone** — accept the loss now, on the basis that 12 days almost
  certainly exceeds whatever retention is configured. Cheapest, but it closes the only remaining path to actually
  confirming or recovering the missing granularity.
- Other: operator can type a custom answer.

**Recommendation: A.** It is a single read-only command, it is the only step that can still change the outcome, and
every day narrows or closes it permanently.
