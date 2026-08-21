---
doc_type: plan
title: cefi satellite AO dispatch batch 23 — 2026-08-21
summary: >-
  Extraction batch from the cefi tranche's 2026-08-21 /na-eligibility-audit run — 1 conflict-cleared,
  bounded/deterministic todo pulled from 1 source doc (RECLASSIFY_SPLIT). The source doc
  (`pacifica_solana_perp_reintegration_2026_08_14.md`) has 2 open items: this one (a registry-declaration task,
  mirroring an established pattern) and a separate `[OPERATOR]` wallet-key/live-capital decision (CLAUDE.md's
  human-only hard-stop) — the source doc stays `assigned_vm: NA` for that item, unaffected by this extraction.
  Conflict-checked against every existing active cefi batch/finalize plan (through batch22) and a corpus-wide grep
  for `POSITION_READ_MODE_CAPABILITIES`/`pacifica` position-reader — zero hits claiming this exact ground.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [strategy-service, unified-api-contracts]
scope: [engineer]
tags: [cefi, ao-dispatch, satellite-batch, na-eligibility-audit, pacifica, position-read-mode]
related:
  [
    /plans/active/pacifica_solana_perp_reintegration_2026_08_14.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.3
assigned_role: backend_engineer
effort: low
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/pacifica_solana_perp_reintegration_2026_08_14.md,
    strategy-service/strategy_service/position_interface/capabilities.py,
    unified-api-contracts/tests/data/strategy_position_read_mode_baseline.json,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
source: >-
  Drafted by the 2026-08-21 cefi-tranche /na-eligibility-audit run (autonomous worker, dispatch batch parallel
  slot). `status: active` from the start (not draft) per the skill's no-double-gate ruling — na-eligibility-audit's
  own RECLASSIFY_SPLIT verdict + conflict-check IS the authorization to dispatch (unlike /ag-closeout-audit's
  batches, which stay draft pending separate operator approval).
---

# cefi satellite AO dispatch batch 23 — 2026-08-21

> Extracted from `pacifica_solana_perp_reintegration_2026_08_14.md`'s §F follow-up (surfaced 2026-08-20, never
> triaged for dispatch). The item is bounded — mirror an already-established registry-population pattern for
> another venue, no open design/judgment call — unlike the doc's OTHER remaining item (provision a Solana
> `wallet_private_key` to flip `supports_live`), which is CLAUDE.md's explicit human-only wallet-keys hard-stop and
> stays exactly where it is.

## Todos

- [ ] [BACKEND] P2. Give `PACIFICA-SOLANA` a real strategy-service position reader. Add a `pacifica` entry to
      `strategy-service/strategy_service/position_interface/capabilities.py::POSITION_READ_MODE_CAPABILITIES` with
      genuine batch/live/paper coverage — mirror how an existing USDC-margined, no-LST-fallback CeFi perp venue
      (e.g. ASTER) is registered there today, since Pacifica shares that exact margin shape (USDC-only, cross +
      isolated, confirmed live 2026-08-14 — no LST accepted as margin, so the existing LST-address fallback path
      cannot rescue it either). Once the real reader lands, remove `PACIFICA-SOLANA` from the known-gap list in
      `unified-api-contracts/tests/data/strategy_position_read_mode_baseline.json` (the SIT invariant-2 ratchet
      baseline) in the SAME change — ratchets only shrink, never grow back. Source:
      `plans/active/pacifica_solana_perp_reintegration_2026_08_14.md` §F (line ~240, "New follow-up (surfaced
      2026-08-20)"). Repo: strategy-service (+ unified-api-contracts for the baseline-JSON edit). Done when:
      `position_read_mode_availability("pacifica")` returns a real (non-"none") mode on batch/live/paper,
      `PACIFICA-SOLANA` no longer appears in `strategy_position_read_mode_baseline.json`'s known-gap array, a new
      regression test asserts the pacifica entry resolves correctly, and `quality-gates.sh` is green on both
      touched repos.

## Progress Log

- **na-eligibility-audit 2026-08-21 (cefi tranche)**: drafted this batch from the sole bounded-ao-eligible item
  found on `pacifica_solana_perp_reintegration_2026_08_14.md` during a full end-to-end re-read (the doc's OTHER
  open item, the wallet-key/live-signing decision, is a genuine human-only hard-stop and stays put). Conflict-
  checked against every cefi batch/finalize plan through batch22 plus a corpus-wide grep for
  `POSITION_READ_MODE_CAPABILITIES` and any existing pacifica-position-reader work — the one other file that
  references the same registry (`cefi_live_venue_string_dispatch_broken_2026_08_16.md`) does not mention Pacifica
  at all, confirming no overlap. Source doc's checkbox flipped at authoring time to cite this batch.
