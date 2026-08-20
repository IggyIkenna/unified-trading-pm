---
doc_type: plan
title: AssetClass → AssetGroup rename — domain enum only, cross-repo coordinated landing
summary: >-
  Rename the DOMAIN-level unified_api_contracts.AssetClass (crypto/equity/fx/commodity/fixed_income) to AssetGroup
  across UAC + 7 downstream consumer repos + the UI, in one coordinated atomic landing per repo (no backward-compat
  shims allowed). The ledger-scoped LedgerAssetClass (spot_token/perp/lst/…, a different taxonomy, already disambiguated
  in code) is explicitly OUT OF SCOPE and must never be touched by this rename. Supersedes todo C in
  /plans/archive/issues/dart_ui_capability_manifest_and_catalogue_formatting_gaps_2026_07_21.md.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    unified-api-contracts,
    unified-trading-system-ui,
    client-reporting-api,
    execution-service,
    greeks-service,
    instruments-service,
    strategy-service,
    unified-trading-library,
  ]
scope: [engineer]
tags: [asset-class-rename, cross-repo, schema, terminology, plan-discipline]
related:
  [
    plans/archive/issues/asset_class_to_asset_group_rename_scope_underestimated_2026_07_21.md,
    /plans/archive/issues/dart_ui_capability_manifest_and_catalogue_formatting_gaps_2026_07_21.md,
  ]
created: "2026-07-21"
last_updated: "2026-07-21"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.2
assigned_role: backend_engineer
drift_direction: advance-code
sequential: true
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: plans/archive/issues/asset_class_to_asset_group_rename_scope_underestimated_2026_07_21.md
context_scope:
  [
    /codex/04-architecture/tier-and-import-architecture.md,
    /plans/archive/issues/asset_class_to_asset_group_rename_scope_underestimated_2026_07_21.md,
    unified-api-contracts/unified_api_contracts/_instrument_enums.py,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/ledger/_enums.py,
  ]
---

# AssetClass → AssetGroup rename (domain enum only)

> **Destination ruling (BLK-87fc93e4, main, 2026-07-21)**: this is a LOCAL/human plan (`assigned_vm: NA`) by deliberate
> operator-protective default — a 9+-repo atomic breaking rename is exactly the risk class the ask-before-AO-dispatch
> HARD RULE exists for. The operator may flip `assigned_vm: planning` later to dispatch it; do not do that unilaterally.

## The two-enum hazard (read this before touching any file)

`unified_api_contracts` has **two distinct types both literally named `AssetClass`**, and only one of them is what
"AssetGroup" means:

1. **Domain `AssetClass`** (`unified_api_contracts/_instrument_enums.py:122`) —
   `CRYPTO / EQUITY / FX / COMMODITY / FIXED_INCOME`. Market-domain category for position grouping / strategy routing.
   **This is the rename target.**
2. **Ledger `AssetClass`** (`unified_api_contracts/canonical/crosscutting/ledger/_enums.py`) — fine-grained instrument
   buckets (`spot_token / option / perp / lst / …`), a different taxonomy entirely. Already disambiguated in the public
   API: `unified_api_contracts/__init__.py` re-exports it as **`LedgerAssetClass`** specifically "to avoid name
   collision with the domain AssetClass" (see the comment directly above that import). **OUT OF SCOPE — never rename
   this one, never rename its `LedgerAssetClass` alias.**

A blind text-sweep of the literal string `AssetClass` WILL touch both. Every file-level change in every phase below must
confirm which one it's editing by checking the import line, not by pattern-matching the identifier.

## Corrective finding vs. the originating issue doc

The issue doc that spawned this plan flagged `LedgerRow.asset_class` (`_ledger_row.py:259`) as possible schema-migration
territory ("a persisted field, not just an in-memory identifier"). **Investigation during authoring found this field is
typed with the LEDGER-scoped enum, not the domain one** — `_ledger_row.py:25` imports `AssetClass` from `._enums` (the
local ledger module, the same module `__init__.py` re-exports as `LedgerAssetClass`), not from `_instrument_enums`. So
**`LedgerRow.asset_class` is NOT touched by this rename and no ledger-data schema migration is needed** — provided Phase
1 stays correctly scoped to the domain enum only. **Todo 1 re-verifies this determination independently before anything
else proceeds** (don't inherit this finding on trust — the template's own "verify an ordering note, don't reason from
shape alone" rule applies equally to a scope-safety claim).

## Todos

- [ ] [BACKEND] P1. **Re-verify the two-enum scoping is airtight before touching anything.** Confirm (a) the domain
      `AssetClass` (`_instrument_enums.py`) and the ledger `AssetClass`/`LedgerAssetClass`
      (`canonical/crosscutting/ledger/_enums.py`) are genuinely two separate classes with no shared identity/subclass
      relationship; (b) every current importer of the bare `AssetClass` name resolves to the DOMAIN class specifically
      (`grep -rn "\bAssetClass\b"` per repo, then trace each hit's actual import line — do not trust a prior count
      without re-tracing); (c) `LedgerRow.asset_class`'s type resolves to the ledger enum, confirming no persisted-data
      migration is needed. Write the confirmed per-file consumer list (not just the issue doc's per-repo counts) as this
      todo's evidence — Phase 2 dispatches off this list. (repo: unified-api-contracts)
- [ ] [BACKEND] P1. **Rename in `unified-api-contracts`.** `_instrument_enums.py`'s `AssetClass` class → `AssetGroup`;
      update every domain-enum reference found in todo 1's list (NOT the ledger ones). Update the public `__init__.py`
      export name. Run `bash scripts/quality-gates.sh` — this WILL break every downstream consumer's imports until Phase
      2 lands; that's expected and is why this repo's commit and every Phase-2 repo's commit must land as one
      coordinated set, not sequentially-and-independently-mergeable (no backward-compat re-export shim — CLAUDE.md bans
      shims). (repo: unified-api-contracts)
- [ ] [BACKEND] P1. **Per-repo consumer updates — land together with todo 2, not independently.** Update every import +
      reference of the domain `AssetClass` → `AssetGroup` in `client-reporting-api`, `execution-service`,
      `greeks-service`, `instruments-service`, `strategy-service`, `unified-trading-library` (per-repo file counts from
      the originating issue doc: 5/2/2/10/3/3 respectively — re-derive the exact list from todo 1, don't trust the count
      alone). Each repo's `quality-gates.sh` must go green pinned against the renamed UAC version before this todo is
      considered done. (repo: client-reporting-api, execution-service, greeks-service, instruments-service,
      strategy-service, unified-trading-library)
- [ ] [UI] P1. **UI-side rename — independently shippable** (no cross-repo import dependency on the backend rename, per
      the originating issue doc's point 3). `unified-trading-system-ui`'s ~50 files/identifiers using
      `AssetClass`/`asset_class`/`assetClass` → `AssetGroup`/`asset_group`/`assetGroup`. Cite the actual file list
      (re-grep at execution time — the issue doc's estimate is a lower bound, not a spec) rather than a stale count.
      `quality-gates.sh` green. (repo: unified-trading-system-ui)
- [ ] [REVIEW] P1. **Tests + goldens.** Any test fixture, golden file, or snapshot asserting on the old `AssetClass`
      name/import path (as opposed to its VALUES — `crypto`/`equity`/etc. stay unchanged, this is a class-name rename,
      not a value rename) across all 8 repos above updates in the same coordinated landing. Re-run each repo's full test
      suite, not just the renamed files' own tests — a name rename can break an unrelated test that imports the old
      symbol incidentally. (repo: unified-api-contracts, unified-trading-system-ui, client-reporting-api,
      execution-service, greeks-service, instruments-service, strategy-service, unified-trading-library)
- [ ] [DATA] P2. **Codex terminology sweep** (the P11.1.4 item the originating dart_ui issue doc references) — grep
      `codex/` for prose references to "AssetClass" describing the domain concept and update to "AssetGroup"; leave any
      doc correctly describing `LedgerAssetClass` untouched. Gated on todos 2-4 landing (the terminology should match
      shipped code, not precede it). (repo: unified-trading-pm)
- [x] ✅ [PLANNING] P2. **Supersede todo C** in
      `/plans/archive/issues/dart_ui_capability_manifest_and_catalogue_formatting_gaps_2026_07_21.md` with a pointer to
      this plan (mark it non-dispatchable / point here) so the original P3 mechanical-sweep framing never gets picked up
      and executed under the old, underscoped understanding. (repo: unified-trading-pm) **DONE (na-eligibility-audit
      2026-08-03)** — verified live in the archived doc: its todo C (line ~203) already reads
      `[x] BLOCKED-SUPERSEDED [CODE] P3` with the struck-through original text, "SUPERSEDED 2026-07-21...
      Non-dispatchable — do not execute this line as scoped", and an explicit pointer: "already covered by
      plans/active/asset_class_to_asset_group_rename_2026_07_21.md (see that doc for execution)." This is exactly the
      treatment this todo asks for — already applied, nothing further to do.

## Codex SSOTs

`/codex/04-architecture/tier-and-import-architecture.md` (no service↔service deps; UAC as the shared dependency every
repo above imports from — this is exactly the shape that makes a UAC rename a coordinated-landing problem, not an
independent-PR problem), `/codex/02-data/availability-manifest-and-data-status.md` (persisted-schema-change caution —
cited by the originating issue doc; this plan's Todo 1 finding is that it does NOT apply here, but re-verify before
trusting that).

## Progress Log

- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — reaffirms 2026-08-04 (unchanged, open-todo count still 6):
  explicit dated destination ruling (BLK-87fc93e4, 2026-07-21) governs — LOCAL/human by deliberate operator-protective
  default for a 9+-repo atomic breaking rename; "do not [flip assigned_vm] unilaterally."
- **na-eligibility-audit 2026-08-02** (re-confirms 2026-07-30; only change since = context-scout `context_scope`
  frontmatter, body byte-identical): KEEP-NA, valid — explicit dated destination ruling (BLK-87fc93e4, 2026-07-21):
  LOCAL/human by deliberate operator-protective default for a 9+-repo atomic breaking rename — 'do not do that
  unilaterally'.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (4 entries) — swapped in the two-enum hazard's actual source
  files (`_instrument_enums.py` rename target + the out-of-scope ledger twin `_enums.py`, both explicitly named in the
  doc's own "two-enum hazard" section), dropped the availability-manifest codex ref + the superseded dart_ui issue doc
  (todo 1 already re-confirmed this doesn't apply / already resolved).
- **na-eligibility-audit 2026-08-04**: KEEP-NA, valid — re-confirms the 2026-08-02 pass; the explicit dated destination
  ruling (BLK-87fc93e4, 2026-07-21: "LOCAL/human by deliberate operator-protective default... do not do that
  unilaterally") still governs; open-todo count unchanged at 6.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (4 entries), still accurate.
- **context-scout 2026-08-15**: re-scouted; context_scope unchanged (4 entries), still accurate.
- **T4-execution-settlement client-reporting-api close-out 2026-08-20** [session scope: `client-reporting-api` +
  unified-trading-pm docs only]: verified current code state — the domain `AssetClass`
  (`unified-api-contracts/unified_api_contracts/_instrument_enums.py:122`) is still NOT renamed (no `AssetGroup` class
  exists there; the `AssetGroup` names elsewhere in UAC — `canonical/gcs_paths.py`, `canonical/asset_group_registry.py`,
  `registry/archetype_capability_matrix.py` — are pre-existing, unrelated types, not this rename's target).
  `client-reporting-api` still has 5 files referencing the domain `AssetClass`
  (`client_reporting_api/core/ledger_views.py` + 4 test files). **No code changes made**: todo 3's `client-reporting-api`
  consumer update explicitly must "land together with todo 2, not independently" — doing it now (before UAC's rename
  lands) would break `client-reporting-api`'s import, since `AssetGroup` does not yet exist in UAC's public API for the
  domain enum. Todos 1-2 are scoped to `unified-api-contracts`, outside this session's scope. Open-todo count unchanged
  at 6; destination ruling (BLK-87fc93e4) continues to correctly govern, `assigned_vm: NA` unchanged.
- **context-scout 2026-08-20**: re-scouted; context_scope unchanged (4 entries), all still resolve on disk.
