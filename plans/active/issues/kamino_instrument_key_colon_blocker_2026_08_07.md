---
doc_type: issue
title: kamino.py SOLANA_VAULT compound symbol ':' incompatible with build_instrument_id colon guard
summary: >-
  UAC canonical_id_builder.py (colon-guard added 2026-07-20) hard-rejects any non-sports symbol containing ':'.
  kamino.py:199 builds its SOLANA_VAULT key with symbol '{sym_a}-{sym_b}:{address[:8]}' which embeds ':', blocking the
  build_instrument_id passthrough retrofit prescribed by the 2026-07-08 checklist (which predates the guard). Format
  change requires an operator ruling (changes instrument_key = GCS path segment; migration needed).
status: open
asset_group: [defi]
stage: [data]
repos: [instruments-service, unified-api-contracts]
created: "2026-08-07"
assigned_vm: NA
execution_scope: local-only
priority: P2
assigned_role: data_engineering
tags: [defi, canonical-id, kamino, blocker]
related:
  [
    /plans/archive/2026_08/canonical_id_builder_retrofit_checklist_2026_07_08.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
nature: issue
scope: [engineer]
parent_epic: defi_master
source: >-
  Discovered during defi_satellite_ao_dispatch_batch9_2026_08_06.md todo 1 (task defi_satellite_ao_dispatch_batch9-001,
  slot 2, 2026-08-07) — UAC colon-guard (added 2026-07-20) post-dates the 2026-07-08 retrofit checklist.
resolved_by: ""
locked_by: ""
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/archive/2026_08/canonical_id_builder_retrofit_checklist_2026_07_08.md,
    /plans/active/issues/canonical_path_oracle_blind_to_filename_stem_2026_07_20.md,
    unified-api-contracts/unified_api_contracts/internal/reference/canonical_id_builder.py,
    instruments-service/instruments_service/reference_data/adapters/defi/kamino.py,
  ]
---

## Finding

`canonical_id_builder.py` (UAC) hard-rejects any non-sports/prediction symbol containing `":"` (lines 851–862, added
2026-07-20, per `canonical_path_oracle_blind_to_filename_stem_2026_07_20.md §7` — prevents double-wrapped ids from raw
wire symbols).

`instruments_service/reference_data/adapters/defi/kamino.py:199` builds its `SOLANA_VAULT` instrument key as:

```
instrument_key = f"{venue_tag}:SOLANA_VAULT:{sym_a}-{sym_b}:{address[:8]}"
```

The compound symbol `{sym_a}-{sym_b}:{address[:8]}` (e.g. `SOL-USDC:AbCd1234`) contains an embedded `:`, which the colon
guard hard-rejects with `ValueError` regardless of `passthrough=True`, because the colon check runs before the
passthrough dispatch (line 851 check precedes line 879 passthrough call).

The 2026-07-08 checklist prescribed
`build_instrument_id(venue_tag, InstrumentType.SOLANA_VAULT, f"{sym_a}-{sym_b}:{address[:8]}", passthrough=True)`, but
the colon guard was added 2026-07-20 — after the checklist was authored — making that call a runtime `ValueError`.

## Current state

f-string retained at `kamino.py:199`. Key format unchanged from prior commits; output is byte-identical to before this
batch.

## Options (operator ruling required — changing symbol changes GCS key)

- **(a) Change separator**: replace `:` before the address prefix with `-` → `{sym_a}-{sym_b}-{address[:8]}`. Instrument
  key changes (`SOLANA_VAULT:SOL-USDC:AbCd1234` → `SOLANA_VAULT:SOL-USDC-AbCd1234`). Requires manifest migration for
  existing rows.
- **(b) Use `@` as separator**: `{sym_a}-{sym_b}@{address[:8]}`. Same scope as (a).
- **(c) Leave f-string as-is** (current state). No migration; kamino stays off the builder path.

Discovered during `defi_satellite_ao_dispatch_batch9_2026_08_06.md` todo 1 (batch9-001, slot 2, 2026-08-07).

## Todos

- [ ] [OPERATOR] P2. **Rule on the SOLANA_VAULT compound-symbol format for `kamino.py:199`** — needs a decision among
      options (a) `-` separator, (b) `@` separator, or (c) leave the f-string as-is (kamino stays off the
      `build_instrument_id` passthrough path). (a)/(b) change the instrument_key = GCS path segment and require a
      manifest migration for existing rows; (c) needs no migration but leaves kamino permanently un-retrofitted.
      Genuinely a judgment call, not worker-determinable — no options were dismissed as clearly wrong in the Finding
      above. Not tracked as a todo anywhere else in the corpus (verified via grep); `defi_satellite_ao_dispatch_batch9_
      2026_08_06.md` only cites this doc as the reason kamino.py:199 was retained unfixed, it does not itself carry a
      resolution todo.

## Progress Log

- **na-eligibility-audit 2026-08-07** (tranche=defi): KEEP-NA valid — first audit pass, doc filed today. The doc carries
  no tracked checkboxes at all — it is a pure findings-plus-options write-up awaiting a real operator ruling on a
  GCS-path-changing instrument-key format decision (options (a)/(b)/(c) above, each with different migration
  implications for existing manifest rows) — a textbook OPERATOR_QUESTION, not a worker-determinable outcome. Doc stays
  `assigned_vm: NA`.

- **context-scout 2026-08-09**: populated/refreshed context_scope (4 entries).
- **na-eligibility-audit 2026-08-09** (tranche=defi): KEEP-NA valid -- Pure findings-plus-options doc, zero tracked
  checkboxes but 1 real prose-only open item (this corpus's confirmed trap): UAC's colon-guard hard-rejects kamino.py's
  SOLANA_VAULT compound symbol. 3 explicit options laid out, each with different GCS-path/manifest-migration
  implications -- doc's own text: "operator ruling required" before any implementation. Doc stays `assigned_vm: NA`.
- **2026-08-10 (prose-findings formalization sweep)**: converted 1 prose finding into 1 formal todo (0 already
  resolved). The options (a)/(b)/(c) ruling flagged by every prior na-eligibility-audit pass as "1 real prose-only
  open item" had never actually been formalized as a `- [ ]` checkbox — added a `[OPERATOR] P2` todo under a new
  `## Todos` section.
- **na-eligibility-audit 2026-08-10 (formalized-docs follow-up, group 1 of 2)**: KEEP-NA, valid — the sole todo is
  explicitly `[OPERATOR]`-tagged and self-describes as "Genuinely a judgment call, not worker-determinable" (a
  GCS-path-changing instrument-key format ruling with manifest-migration implications, 3 undismissed options). Never
  re-litigating: the same disposition was independently reached by the 2026-08-07 and 2026-08-09 na-eligibility-audit
  passes on this exact doc. Doc stays `assigned_vm: NA`.
