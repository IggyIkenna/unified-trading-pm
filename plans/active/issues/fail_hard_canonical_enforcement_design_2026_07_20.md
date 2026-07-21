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
  - plans/active/issues/batch_live_filename_divergence_sanitize_symbol_2026_07_20.md
created: 2026-07-20
parent_epic: cefi_master
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
| **2 — MANIFEST CLASSIFY** | Schema v10 `instrument_id_form` on new writes; backfill classifies existing rows                                  | after 1              | Stage 1 + the v2 dedup `--apply` (else it rejects rows the cleanup is about to fix) |
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
`codex/04-architecture/shard-level-failure-isolation.md`, and it is the same class as the measured 2026-07-17 loss of 27
DERIBIT shards (`tardis_cefi_shards.py:296-305`).

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

- [ ] [WRITER] P1. A-iso — rebuild the `tardis_cefi_shards.py:144` groupby loop as per-shard isolated (§4). Ships alone.
- [ ] [DESIGN] P1. Close the three §5 gaps (derivative-bundle column gate; live-lane dual-resolver reconciliation; read
      marker disposition) before write-enforce.
- [ ] [WRITER] P2. Pass `violation_classes={STRUCTURAL}` explicitly at the 3 `canonical_path_violations` write
      callsites.
- [ ] [DATA] P2. Stage 0 — classify-and-log at every write/manifest/read site, zero behaviour change.
- [ ] [UAC] P2. `is_quarantined_instrument_id` + `ResolutionEvidence` + the registry (composes, no fenced-file edit).
- [ ] [DATA] P3. Schema v10 `instrument_id_form` + backfill classification (Stage 2), after the v2 dedup `--apply`.
