---
doc_type: issue
title: Fail-hard canonical enforcement — staged contract, quarantine model, and the sequencing answer
summary: >
  Verified design for the operator directive "make the SSOT canonical, migrate others, and FAIL HARD in manifest and
  code reads and writes." Answers the sequencing question (enable now vs gate on the catalogue gap), defines the staged
  rollout + the quarantine model, and records three adversarially-CONFIRMED gaps that must be closed before
  write-enforce ships.
status: open
nature: design
asset_group: cefi
stage: data
repos: [unified-api-contracts, market-tick-data-service, unified-trading-library]
scope: engineer
tags: [canonical, fail-hard, quarantine, shard-isolation, batch-live-determinism]
related:
  - plans/active/cefi_consolidated_closeout_2026_07_18.md
  - plans/active/issues/canonical_path_oracle_blind_to_filename_stem_2026_07_20.md
  - plans/archive/issues/batch_live_filename_divergence_sanitize_symbol_2026_07_20.md
created: 2026-07-20
author: unknown
# was: cefi_master (epic-assignment audit 2026-08-19) -- canonical/quarantine ID-form governance (UAC oracle + registry + ResolutionEvidence) is schema/contract-governance infra enforced at every write/manifest/read site system-wide, not cefi-specific
parent_epic: uac_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: design
assigned_role: data-pipeline
drift_direction: none
source: workflow wf_3785e859-c1f (map → design → adversarial verify; 7 agents, 0 errors)
depends_on: []
locked_by:
locked_since:
context_scope:
  [
    /codex/04-architecture/shard-level-failure-isolation.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/canonical_path_oracle_blind_to_filename_stem_2026_07_20.md,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/tradfi/tardis_cefi_shards.py,
    unified-api-contracts/unified_api_contracts/canonical/quarantine.py,
  ]
resolved_by:
---

# Fail-hard canonical enforcement — design of record

> Produced + adversarially verified by workflow `wf_3785e859-c1f`. The full 47k design + both verdicts live in the run
> transcript; this doc is the durable, actionable distillation. **The design is APPROVED-IN-PRINCIPLE but NOT ready to
> implement as-is** — §5 lists three adversarially-CONFIRMED gaps that must be closed first.

## 1. The operator's question, answered

Question posed: _"enable fail-hard now with the ~82,000 quarantined, or gate on closing the catalogue gap first?"_

**Answer: neither — it is a false binary. There are THREE independently-gateable flips, not one:**

1. **Ship fail-hard WRITES now (Stages 0 → 1). Do NOT gate writes on the catalogue gap.**
2. **Gate fail-hard READS (Stage 3) on manifest classification being populated (Stage 2) — NOT on the catalogue gap.**
3. **Gate any manifest marker-aware gate on the v2 dedup `--apply` landing + an operator ruling.**

Evidence, strongest first:

- **E1 — writes cannot break the ~82,000, because the ~82,000 are already written.** They are a READ and MANIFEST
  problem; a write gate acts only on NEW writes. This decouples the two halves of the question entirely.
- **E2 — the measured write firing rate is 0% today, ~0.6% when Tardis backfill resumes** (5,413 / ~893,221 on the 6
  healthy venues, each a retryable `attempted_failed`). The only actively-writing lane on 2026-07-20 was
  `batch_hyperliquid` (167/167 canonical, deterministic catalogue-free resolution — cannot miss). Not an outage; a
  worklist.
- **E4 — the READ gate is the only one that must wait, and its dependency is Stage 2 (our own backfill), not the
  catalogue.** Gating reads on `instrument_id_form` before it is populated makes every unclassified row unreadable — the
  naive switch-on the concern warned about. Stage 3 must not precede Stage 2; both are satisfiable independent of the
  catalogue.

## 2. The staged rollout

| Stage                     | Content                                                                                                           | When                 | Depends on                                                                          |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------- | -------------------- | ----------------------------------------------------------------------------------- |
| **0 — OBSERVE**           | Classify at every write/manifest/read site. Count + log only, **zero behaviour change**.                          | NOW                  | nothing                                                                             |
| **P — PREREQUISITES**     | A-iso (per-shard isolation, §4); explicit `violation_classes` at the 3 oracle callsites; the `None`-map latch fix | NOW, parallel with 0 | nothing                                                                             |
| **1 — WRITE ENFORCE**     | Lanes raise; registry-gated quarantine; `record_failed(NON_CANONICAL_INSTRUMENT_ID)`                              | after 0 + P          | Stage 0 clean + P complete. **NOT the catalogue gap.**                              |
| **2 — MANIFEST CLASSIFY** | Schema v11 `instrument_id_form` on new writes; backfill classifies existing rows                                  | after 1              | Stage 1 + the v2 dedup `--apply` (else it rejects rows the cleanup is about to fix) |
| **3 — READ ENFORCE**      | Read gate raises on non-canonical / unregistered-quarantine                                                       | after 2              | **Stage 2 populated — NOT the catalogue**                                           |

## 3. The quarantine model (for genuinely-unresolvable instruments)

- **NOT a fifth `capture_status`.** A NEW ORTHOGONAL axis: a three-valued id-form verdict
  `canonical / quarantined / non_canonical`, where **`non_canonical > 0` is the ONLY FAIL condition**. A reconciliation
  can then read _"6,795 canonical, N quarantined (registered, expiring), 0 non-canonical" = PASS_.
- **A positive `UNRESOLVED:` token**, never a bare wire stem — a bare stem is ambiguous between "quarantined" and "the
  migration front hasn't reached this yet". Present on all four surfaces (stem + parquet column + manifest key +
  registry) or the write fails.
- **Registry-gated, with mandatory falsifiable `ResolutionEvidence` + an expiry.** Unregistered misses fail from
  Stage 1. Only PACIFICA-SOLANA (265, culled) + the DERIBIT off-by-one-expiry ambiguities are genuine seed members; the
  ~5,413 healthy-venue residue classifies `NON_CANONICAL` and must fail (it is a real catalogue gap, not a quarantine
  case).
- **Objects do NOT move.** Surface D already measured PASS — reads are correct; this is consistency debt, not broken
  access. Moving ~82,000 good objects under a `_quarantine/` prefix (the tradfi corrupt-object mechanism) would break
  every `pipeline_mode=`-prefix-matching reader and convert a reporting gap into a real outage. **Two quarantine kinds,
  one word — keep them distinct.**

## 4. The prerequisite that is ALSO a standalone bug fix — A-iso (D-2)

`market-tick-data-service/.../adapters/tradfi/tardis_cefi_shards.py:144` iterates the cefi shard atom via `groupby`, and
its only `except` (`:241-244`) is `logger.warning(...); writer.close(); raise` — a cleanup handler that **re-raises out
of the whole function**. So today **a raise anywhere in that loop aborts the entire (venue, data_type, day) fetch —
every remaining symbol.** This is already a latent violation of
`/codex/04-architecture/shard-level-failure-isolation.md`, and it is the same class as the measured 2026-07-17 loss of
27 DERIBIT shards (`tardis_cefi_shards.py:296-305`).

**Rebuild that loop as genuinely per-shard isolated** (wrap each iteration; on exception classify via UAC
`classify_venue_error()` → append to `failed_shards` → `continue`; return `(written_paths, failed_shards)`; orchestrator
converts each to `record_failed`). **This is a correctness fix on its own merits and ships alone with zero happy-path
behaviour change** — and it is the hard prerequisite that makes every later write-side raise a one-shard event instead
of a venue-day outage.

## 5. Adversarially-CONFIRMED gaps — CLOSE BEFORE WRITE-ENFORCE SHIPS

1. **Derivative / chain-bundle lane defeats all three write gates (CONFIRMED end-to-end).** A DERIBIT `options_chain`
   strike that misses the catalogue builds a non-canonical id (`tardis_shared.py:519`), attaches it to the column
   (`finalise_rows_and_path:848-856`), but the STEM is `ticks.parquet`/underlying (exempt) → object lands on a canonical
   `underlying=BTC/.../ticks.parquet` path, manifest keyed on underlying with `instrument_id=""`. **Readable object +
   captured row + non-canonical column value, past every gate.** The `build_quarantined_instrument_id` machinery works
   at the id level, which is never the bundle's stem or manifest key — so **quarantine cannot see the objects it is
   provisioned for**. Requires a real column-value gate on the multi-id bundle + a per-instrument manifest disposition
   for derivatives.
2. **"column == manifest by construction" is TARDIS-ONLY (CONFIRMED).** The live/on-chain lane derives the COLUMN via
   `get_cefi_wire_map().canonical_for()` (`partitioned_writer.py:413-428`) and the MANIFEST via
   `resolve_cefi_instrument_id()` (`venue_fetch.py:381`) — two independent front-ends with independent `None`-latches
   and different miss-behaviours. A HYPERLIQUID shard with a canonical column but a manifest-resolver miss would raise
   `NonCanonicalManifestKeyError` and route a **genuinely-canonical, readable object to `record_failed`** — a coverage
   lie in the opposite direction and a `paper(W)==batch-rerun(W)` divergence. The design must reconcile the two
   derivations, not treat them as one.
3. **Read-gate three-valued classification assumes a positive on-disk marker the current corpus lacks (CONFIRMED
   under-specification).** The read path needs a disposition for a bare-wire stem that is neither registered-quarantine
   nor yet-migrated.

## 5b. Design resolutions for the three §5 gaps (2026-08-11, operator-requested design pass)

**Gap 1 — derivative/chain-bundle column gate.** The structural problem is that §3's "all four surfaces or the write
fails" rule assumes one object = one instrument; a bundle object (stem = underlying, e.g. `ticks.parquet`) legitimately
shares its stem and manifest key across every strike/leg it contains, so no per-leg marker can ever land on those two
surfaces. Resolution: for bundle-shaped writers only (chain-bundle / `options_chain` lanes), add a row-level gate that
validates the embedded instrument_id COLUMN value per row (not the stem, not the manifest key) against the canonical/
quarantine registry, immediately before write. A row whose column value is `NON_CANONICAL` is dropped from the write and
routed to `record_failed(NON_CANONICAL_INSTRUMENT_ID, granularity=row)` — matching Stage 1's existing STRUCTURAL per-row
enforcement philosophy rather than inventing a new column-only quarantine marker (deferred as a later-stage nicety, out
of scope for closing this gap). The manifest keeps its existing underlying-keyed row, plus a new
`quarantined_legs: [...]` field so reconciliation can count dropped legs without needing per-leg manifest rows.

**Gap 2 — TARDIS-only "column == manifest by construction."** The live/on-chain lane's two independent front-ends
(`get_cefi_wire_map().canonical_for()` for the column, `resolve_cefi_instrument_id()` for the manifest key) can disagree
because they're independent computations, not because the underlying data disagrees. Resolution: make the manifest key a
deterministic function of the ALREADY-COMPUTED column value — derive it by parsing that value, not by an independent
second resolution — since the column is written first in `partitioned_writer.py`, it's available before the manifest key
is needed. `resolve_cefi_instrument_id()`'s independent path becomes a fallback ONLY for the case where no column value
exists yet (should not occur at write time on this lane). This closes the divergence structurally instead of reconciling
two answers after the fact.

**Gap 3 — read-gate lacks a positive marker for "not yet migrated."** The three-valued verdict
(`canonical`/`quarantined`/`non_canonical`) has no way to distinguish a legitimately-not-yet-backfilled row from a
genuinely non-canonical one. Resolution: add a temporal `unclassified` state (not a new `capture_status`, consistent
with §3) — any manifest row that predates Stage 2 and simply lacks the `instrument_id_form` field is `unclassified`, not
`non_canonical`. The Stage 3 read gate checks field-presence before checking the verdict: `unclassified` rows
PASS-WITH-WARNING (logged + counted, never failed) until Stage 2's backfill is verified complete (100% of manifest rows
carry `instrument_id_form`), at which point a config flag flips `unclassified` to fail like `non_canonical` — closing
the loophole once there is nothing left to legitimately be unclassified.

These are design resolutions, not implementations — see the new `[WRITER]`/`[UAC]` todos in §7 for the actual code
changes, each now a bounded, independently-dispatchable task. Flagging for a quick operator/engineering sanity check
given this governs a live production correctness gate (options-chain/derivative data) — not blocking dispatch of the new
implementation todos on that check, since they're each independently reviewable in their own PRs.

## 6. Stale premises corrected by verification (do not re-introduce)

- **D-5 / Lane C colon-strip is ALREADY FIXED and committed** (`market-tick-data-service@953679de` —
  `sanitize_file_stem` preserves `:`). Verified live: `HYPERLIQUID:PERPETUAL:BTC-USD@LIN` → guard PASS, no crash on
  resume.
- The both-classes DEFAULT at the `canonical_path_violations` callsites means ID_FORM enforcement went live **the moment
  the oracle committed (`unified-api-contracts@d40c5d7d`)**, not "when live WS capture resumes." Latent only because no
  live/consolidated cefi writes happen today (capture stopped 2026-06-29). The remedy — pass `violation_classes`
  explicitly at every write callsite so writes enforce STRUCTURAL now and ID_FORM only when staged — is a Stage-P item.
- Stages 0-3 require **zero edits to fenced files**: `is_canonical_instrument_id` is already exported; a new UAC
  `is_quarantined_instrument_id` composes with it. The oracle's third verdict is a Stage-4 reporting nicety, not a
  blocker.

## 7. Todos

- [x] ✅ [WRITER] P1. A-iso — rebuild the `tardis_cefi_shards.py:144` groupby loop as per-shard isolated (§4). Ships
      alone. — **SHIPPED `market-tick-data-service@e49e1395`** ("write-guard + A-iso per-shard write isolation",
      confirmed in the 2026-07-22 ~19:50Z DELTA per `cefi_4surface_migration_execution_log_2026_07_24.md`). Stale
      checkbox flip per `cefi_satellite_ao_dispatch_batch2_2026_07_26.md`'s Deferred-item re-check
      (`cefi_satellite_ao_dispatch_batch2_2026_07_26_finalize.md` item -002) — commit verified to exist.
- [x] ✅ [DESIGN] P1. Close the three §5 gaps (derivative-bundle column gate; live-lane dual-resolver reconciliation;
      read marker disposition) before write-enforce. — **DONE 2026-08-11** (operator-requested design pass, via main):
      see §5b for the three resolutions. Flagged for an operator/engineering sanity check given the correctness stakes,
      but not gating dispatch of the three implementation todos below — each is independently reviewable in its own PR.
      Implementation split into the 3 new todos below, one per gap.
- [x] ✅ [WRITER] P2. **RECONCILED 2026-08-16 (cefi_satellite_ao_dispatch_batch19_2026_08_13_finalize.md, slot 21) —
      corrects a stale na-eligibility-audit 2026-08-16 note that missed batch19's prior-day shipment.** **Implement
      Gap 1's resolution (§5b)**: add a row-level column-value gate for bundle-shaped writers (chain-bundle /
      `options_chain` lanes) that validates each row's embedded instrument_id against the canonical/quarantine
      registry before write; drop non-canonical rows to `record_failed(NON_CANONICAL_INSTRUMENT_ID, granularity=row)`;
      add `quarantined_legs: [...]` to the manifest row. Repo: market-tick-data-service. — **SHIPPED
      market-tick-data-service@c1626c5dbd** (+ prerequisite UAC ID_FORM-oracle widening
      `unified-api-contracts@8b81dd78bb`), 2026-08-15, via `cefi_satellite_ao_dispatch_batch19_2026_08_13.md` — see
      that plan's own entry for full detail. The na-eligibility-audit 2026-08-16 extraction to
      `fail_hard_canonical_enforcement_ao_dispatch_2026_08_15.md` (+finalize) duplicated this already-shipped work
      one day later; both cancelled-superseded and archived in this same reconciliation pass.
- [x] ✅ [WRITER] P2. **RECONCILED 2026-08-16 (cefi_satellite_ao_dispatch_batch19_2026_08_13_finalize.md, slot 21) —
      corrects a stale na-eligibility-audit 2026-08-16 note that missed batch19's prior-day shipment.** **Implement
      Gap 2's resolution (§5b)**: make the live/on-chain lane's manifest key a deterministic function of the
      already-computed column value (parse it, don't re-resolve independently via `resolve_cefi_instrument_id()`);
      keep the independent resolver only as a fallback for the no-column-yet case. Repo: market-tick-data-service
      (`venue_fetch.py`, `partitioned_writer.py`). — **SHIPPED market-tick-data-service@d518aca80d**, 2026-08-15, via
      `cefi_satellite_ao_dispatch_batch19_2026_08_13.md` — see that plan's own entry for full detail. Same duplicate
      dispatch (`fail_hard_canonical_enforcement_ao_dispatch_2026_08_15.md`) cancelled-superseded and archived
      alongside Gap 1 above.
- [x] ✅ [UAC] P3. **Implement Gap 3's resolution (§5b)**: add the temporal `unclassified` state (manifest row predates
      Stage 2 / lacks `instrument_id_form`) distinct from `non_canonical`; wire the Stage 3 read gate to
      pass-with-warning on `unclassified` until a backfill-complete flag promotes it to enforced-fail. Repo:
      unified-api-contracts + market-tick-data-service (read gate). — **SHIPPED unified-api-contracts@8203b600c0 +
      market-tick-data-service@ecedb15f4e** (2026-08-15, slot-17·backend_engineer, via
      `cefi_satellite_ao_dispatch_batch19_2026_08_13.md` — see that plan's own entry for full detail). PASS-WITH-WARNING
      only today (Stage 2's schema v10 `instrument_id_form` still open, unblocked below); the read gate promotes to
      enforced-fail once that field ships and `_STAGE2_ID_FORM_BACKFILL_COMPLETE` flips.
- [x] ✅ [WRITER] P2. Pass `violation_classes={STRUCTURAL}` explicitly at the 3 `canonical_path_violations` write
      callsites. — **SHIPPED as part of the same `market-tick-data-service@e49e1395` batch**: "mtds fail-hard
      write-guard fix (STRUCTURAL-only enforce + Stage-0 ID_FORM observe-log)" via the shared
      `enforce_structural_and_observe_id_form()` helper wired into all 3 callsites (`partitioned_writer.py`,
      `websocket_runner.py`, `book_microstructure_handler.py`). Stale checkbox flip per the same Deferred-item re-check
      — commit verified to exist.
- [x] ✅ [DATA] P2. Stage 0 — classify-and-log at every write/manifest/read site, zero behaviour change. — Write-side:
      `market-tick-data-service@e49e1395` (wired into `partitioned_writer.py` / `websocket_runner.py` /
      `book_microstructure_handler.py` via `enforce_structural_and_observe_id_form()`). Manifest + read-side:
      `market-tick-data-service@4bd7e87e` (`manifest_recorder._observe_cefi_id_form()` in all 4 `record_*` methods;
      `tardis_cefi_shards._emit_per_symbol_manifest` classify after `_sym` resolves; `reader._cefi_candidate_stems`
      walrus-form classify). Regression test (9 tests) proves zero behaviour change. QG green.
- [x] ✅ [UAC] P2. `is_quarantined_instrument_id` + `ResolutionEvidence` + the registry (composes, no fenced-file edit).
      — **SHIPPED `unified-api-contracts@989e9d16`** (quarantine model + `classify_id_form()`) — standalone module, not
      yet wired into any write/read guard (that's Stage 3, still future work per the `[DESIGN] P1` todo above). Stale
      checkbox flip per the same Deferred-item re-check — commit verified to exist.
- [ ] [DATA] P3. Schema v11 `instrument_id_form` + backfill classification (Stage 2), after the v2 dedup `--apply`.

## Progress Log

- **2026-08-22 (D19 manifest-consolidation session)**: corrected this doc's own stale "v10" claim — a version-number
  collision found while landing an unrelated schema bump. `MANIFEST_SCHEMA_VERSION` (`_schema.py`) was still the live
  `9`; this doc's Stage 2 todo names "v10" but is DEPENDENCY_BLOCKED (reaffirmed across 5+ na-eligibility-audit passes,
  most recently 2026-08-21) on Stage 1 write-enforce + the v2 dedup `--apply`, neither imminent. Meanwhile
  `event_driven_manifest_consolidation_2026_08_22.md`'s manifest-v10 proposal (config_shard_id/config_version/
  code_semver/run_attempt/latency_profile_hash/upstream_gap_class+days+ratio) is ready to ship now and legitimately
  claims the actual next version number in the live constant. Since only one batch can be "v10" in the constant and
  this doc's own Stage 2 has no near-term unblock, retitled this doc's still-open todo (+ the staged-rollout table
  above) to v11 so it doesn't collide when it eventually ships. `quarantined_legs` (`_rows.py`, shipped 2026-08-15,
  self-labeled "v10" in its own comment but never actually bumped the constant) is retroactively folded into the real
  v10 bump alongside the D19 columns — see `unified-trading-library/unified_trading_library/manifest_writer/_schema.py`
  for the authoritative v10 payload. No code changes in this repo from this correction — doc-only, via
  `safe-doc-push.sh`.



- **2026-08-16 (na-eligibility-audit follow-up Q&A round 2, operator ruling)**: the Gap 1-3 implementation question —
  **run the §5b sanity check first, then proceed** — extracted to
  `fail_hard_canonical_enforcement_ao_dispatch_2026_08_15.md` (`assigned_vm: planning`). Gap 3 was already shipped
  (checked below); the Stage 2 schema v10 backfill authorization question was not separately ruled this round.
- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): KEEP-NA, valid - `nature: design`,
  APPROVED-IN-PRINCIPLE only; the open `[DESIGN]` todo is closing 3 adversarially-confirmed architecture gaps before
  write-enforce.
- **context-scout 2026-08-03**: re-verified context_scope (5 entries) — all five still directly cited by the doc's own
  body; no change needed.
- **na-eligibility-audit 2026-08-04** (tranche=cefi, autonomous): KEEP-NA, valid — reaffirms the 2026-07-30 verdict;
  `nature: design`, remaining open work is closing 3 adversarially-confirmed architecture gaps before write-enforce, a
  judgment/design call not bounded worker-determinable work.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **na-eligibility-audit 2026-08-06** (tranche=cefi, autonomous): KEEP-NA, valid — reaffirms the 2026-07-30 verdict;
  `nature: design`, the enforcement design is APPROVED-IN-PRINCIPLE but not ready to implement pending 3
  adversarially-confirmed architecture gaps. The closest-to-bounded residual item (Stage-0 classify-and-log) spans 3
  repos and sits inside a design surface the doc's own author has twice declared not-ready — kept bundled under NA
  rather than split out unilaterally.
- **na-eligibility-audit 2026-08-08** (tranche=cefi, autonomous): KEEP-NA, valid — reaffirms the 2026-07-30 verdict. In
  scope this run only because the Stage-0 `[DATA] P2` todo's manifest+read-side half shipped
  (`market-tick-data-service@4bd7e87e`, 2026-08-07) and flipped `[x]` — that closes the "closest-to-bounded residual
  item" the 2026-08-06 marker flagged, it does not open a new one. 2 open todos remain, both correctly NA: `[DESIGN] P1`
  (close the 3 §5 architecture gaps — GENUINE_WORK, a real design/judgment call, not worker-determinable) and
  `[DATA] P3` (Stage 2 schema v10 backfill — DEPENDENCY_BLOCKED on Stage 1 write-enforce, which is itself blocked on the
  same `[DESIGN] P1` gap-closure, plus the separate v2 dedup `--apply` landing). Neither clears the bounded-outcome bar.

- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **na-eligibility-audit 2026-08-09** (tranche=cefi, autonomous): KEEP-NA, valid — design 'APPROVED-IN-PRINCIPLE, not
  ready to implement' pending 3 adversarially-confirmed architecture gaps. Both open items are real design/judgment
  work, not worker-determinable.
- **2026-08-11** (operator-requested design pass, via main, part of an AO-dispatch-visibility gate unblocking pass on
  the downstream `canonical_path_oracle_blind_to_filename_stem_2026_07_20.md` doc, which was gated on this one):
  proposed resolutions to all three §5 gaps (§5b), closed the `[DESIGN] P1` todo, split implementation into 3 new
  bounded todos. Not implemented — design only. Recommend a quick operator/engineering sanity check on §5b before the
  implementation todos ship, given this governs a live production correctness gate for options-chain/derivative data.
- **na-eligibility-audit 2026-08-16** [body-hash:5c31e82a03b5597f]: KEEP-NA, stale-citation fix applied (checkbox(es) corrected to cite where the work actually landed -- see inline citations above). Doc stays assigned_vm: NA.
- **na-eligibility-audit 2026-08-17** [body-hash:2217935cc9688abd]: KEEP-NA, valid — Reaffirmed. Sole open item (Stage 2, schema v10 instrument_id_form) is DEPENDENCY_BLOCKED per the doc's own staged-rollout table ("Depends on: Stage 1 + the v2 dedup --apply"), reaffirmed across 5+ prior audit passes. Doc stays assigned_vm: NA.
- **context-scout 2026-08-17**: re-verified context_scope (5 entries), unchanged.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
- **na-eligibility-audit 2026-08-21**: KEEP-NA, valid — reaffirms prior verdicts; sole open item (Stage 2, schema
  v10 `instrument_id_form`) stays DEPENDENCY_BLOCKED per the doc's own staged-rollout table.
