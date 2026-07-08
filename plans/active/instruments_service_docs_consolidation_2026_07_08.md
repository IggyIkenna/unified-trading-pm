---
doc_type: plan
title:
  Consolidate instruments-service's 17 docs into 7 — one setup guide, one adapter-architecture guide, one doc per asset
  group
summary:
  "instruments-service/docs/ has 17 markdown files (6,529 lines) with heavy overlap — COMMAND_FLOW_ANALYSIS.md,
  COMMAND_FLOW_DIAGRAM.md, and VENUE_ADAPTERS.md all describe the same adapter architecture; DEFI_GUIDE.md duplicates
  DEFI_INSTRUMENTS.md; CORPORATE_ACTIONS.md is TradFi-only content living outside TRADFI_INSTRUMENTS.md. Operator wants
  this collapsed to 7 docs (1 setup guide, 1 adapter code-structure guide, 5 asset-group docs), each asset-group doc
  carrying an explicit MVP-universe section (MVP universe is NOT all instruments captured — it's the subset actually
  used for market-tick-data download once things are wired end-to-end), and cross-linked to this session's real
  findings: the instruments-definitions drilldown mockup
  (https://claude.ai/code/artifact/e2824e52-3a51-43e0-b4b1-933bee469f9d) and the instrument_id canonicalization decision
  doc. Before writing anything, audit the existing docs against real code, the mockup, and UAC for deviations — several
  are already known to be stale (docs describe a single-margin-type Deribit, a pre-A_TOKEN/ DEBT_TOKEN lending model,
  etc)."
status: active
nature: design
asset_group: [cefi, defi, tradfi, sports, prediction, meta]
stage: [meta]
repos: [instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: [documentation, consolidation, instrument-id, mvp-universe, adapter-architecture, cleanup]
related:
  [
    issues/instrument_id_format_canonicalization_2026_07_08.md,
    issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md,
    issues/defi_lending_atoken_debttoken_instrument_split_2026_07_07.md,
    instruments_completion_tracker_2026_07_06.md,
    ../audit/results/canonical_instrument_id_audit_2026_07_08.md,
  ]
created: 2026-07-08
last_updated: 2026-07-08
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: design
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 3.6
assigned_role: data_engineering
drift_direction: advance-code
depends_on: [../audit/results/canonical_instrument_id_audit_2026_07_08.md]
locked_by:
locked_since:
supersedes:
superseded_by:
model_tier: sonnet-doable
thinking_tier: medium
source:
  'Operator, 2026-07-08: "do we need a new doc one per AG with cross links to general convention specs to replace these
  docs [17 instruments-service docs listed] ... take everything that we have discussed and those existing docs and
  update to max 7 docs ... a basic setup guide, something on the code structure of new adapters, and then just a doc per
  asset group around this instrument convention. In each doc, also include an understanding of what MVP universe looks
  like ... MVP universe isnt necessarily all the instruments we download ... check for deviations for us before we write
  these extra docs." Chose human-driven plan (assigned_vm: NA) over agent-orchestrator when asked.'
---

> **Read-before-write discipline (operator-mandated)**: Phase 1 is a pure audit — no doc gets touched until every claim
> in the 17 existing docs has been checked against real code / the mockup / UAC and every deviation is logged. Phase 2
> is a design checkpoint with the operator before any prose gets written. Phases 3-4 are the actual rewrite + cutover.

## The 5 sources this plan reconciles

1. **The 17 existing docs** (`instruments-service/docs/*.md` + `docs/specs/*.md`) — what's currently documented.
2. **The mockup** (https://claude.ai/code/artifact/e2824e52-3a51-43e0-b4b1-933bee469f9d) — real venues/instrument_ids/
   bugs verified this session, per asset group.
3. **The real code** — instruments-service adapters, `canonical_id_builder.py`, MVP-scope constants.
4. **UAC** — `unified_api_contracts` venue/instrument-type registries (the actual SSOT for venue lists + adapter keys
   per `codex/04-architecture/instruments-service-as-ssot-for-mtds.md`).
5. **This session's 2 PM issue docs** — `instrument_id_format_canonicalization_2026_07_08.md` (the decided
   canonical-format target-state) and `adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md`
   (the 3-layer GCS/manifest/deployment-UI reconciliation gap) — both need to be reflected in the new docs, not just
   left as separate PM tickets nobody reading `instruments-service/docs/` would ever find.

## Target 7-doc structure

| #   | New doc                          | Absorbs                                                                                                                                                                                                                                                    |
| --- | -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `docs/SETUP_GUIDE.md`            | `specs/SETUP_GUIDE.md`, `specs/SECRETS_SETUP.md`, `specs/API_KEYS_STANDARDIZED_PROCESS.md`, `specs/TEST_ALIGNMENT.md`, `specs/CLOUD_OPERATIONS.md`                                                                                                         |
| 2   | `docs/ADAPTER_ARCHITECTURE.md`   | `docs/ARCHITECTURE.md`, `specs/COMMAND_FLOW_ANALYSIS.md`, `specs/COMMAND_FLOW_DIAGRAM.md`, `specs/VENUE_ADAPTERS.md`, general parts of `specs/INSTRUMENT_SPECIFICATION.md` (the canonical_id_builder.py explanation + its real caveats found this session) |
| 3   | `docs/CEFI_INSTRUMENTS.md`       | existing + relevant CeFi slices of `specs/MVP_INSTRUMENTS.md`/`specs/INSTRUMENT_SPECIFICATION.md` + mockup cross-link + canonicalization findings                                                                                                          |
| 4   | `docs/DEFI_INSTRUMENTS.md`       | existing + `specs/DEFI_GUIDE.md` (near-duplicate) + relevant DeFi MVP/spec slices + mockup cross-link + canonicalization findings + the A_TOKEN/DEBT_TOKEN decision                                                                                        |
| 5   | `docs/TRADFI_INSTRUMENTS.md`     | existing + `specs/CORPORATE_ACTIONS.md` (currently orphaned TradFi-only content) + relevant TradFi MVP/spec slices + mockup cross-link                                                                                                                     |
| 6   | `docs/SPORTS_INSTRUMENTS.md`     | existing + relevant Sports MVP/spec slices + mockup cross-link (fixtures-are-the-instrument model, bookmaker=venue)                                                                                                                                        |
| 7   | `docs/PREDICTION_INSTRUMENTS.md` | renamed from `docs/POLYMARKET_PREDICTION.md` + relevant Prediction MVP/spec slices + mockup cross-link                                                                                                                                                     |

10 docs retired: `specs/SETUP_GUIDE.md`, `specs/SECRETS_SETUP.md`, `specs/API_KEYS_STANDARDIZED_PROCESS.md`,
`specs/TEST_ALIGNMENT.md`, `specs/CLOUD_OPERATIONS.md`, `specs/COMMAND_FLOW_ANALYSIS.md`,
`specs/COMMAND_FLOW_DIAGRAM.md`, `specs/VENUE_ADAPTERS.md`, `specs/DEFI_GUIDE.md`, `specs/CORPORATE_ACTIONS.md`,
`specs/INSTRUMENT_SPECIFICATION.md`, `specs/MVP_INSTRUMENTS.md` — wait, that's 12, not 10; the final count depends on
how cleanly `INSTRUMENT_SPECIFICATION.md`/`MVP_INSTRUMENTS.md` split across docs #2-7 — **confirm the exact retirement
list as part of Phase 2's design checkpoint**, this table is a starting hypothesis, not a locked decision.

## Todos

### Phase 1 — Audit (no doc writing yet)

- [ ] [DATA] P0. **Read all 17 existing docs in full** (not just the intros already skimmed) and extract every concrete
      claim: venue lists per AG, instrument_id format examples, MVP-universe scope statements, adapter-count claims.
      Produce a claims inventory (a working scratch file, not a committed doc) — this is the input to every later
      cross-check.
- [ ] [DATA] P0. **Cross-check every instrument_id-format claim against real code** — `canonical_id_builder.py`, the
      per-venue adapters already read this session (yearn.py/beefy.py/karak.py/pendle.py/renzo.py/idle.py and the CeFi
      ones), and a real GCS `prod/catalog.parquet` read per asset group where not already covered this session. Flag
      every doc claim that doesn't match what's actually captured.
- [ ] [DATA] P0. **Cross-check every venue-list claim against UAC's registries** (`venue_mapping.py`,
      `data_type_capability.py`, `venue_constants.py`) — flag venues the docs mention that UAC doesn't declare (or vice
      versa).
- [ ] [DATA] P1. **Cross-check MVP-universe claims against the real MVP-scoping code** (`mvp_scope.py` or equivalent)
      per asset group — confirm or correct each doc's stated MVP scope; this is the section the operator explicitly
      wants added/corrected in every AG doc.
- [ ] [DATA] P1. **Reconcile every doc claim against the mockup + this session's 2 issue docs** — anywhere a doc
      contradicts a real finding already verified this session (e.g. a doc describing Deribit as single-margin-type, or
      describing AAVE_V3/COMPOUND_V3/MORPHO's lending split incorrectly), log it as a required correction.
- [ ] [DATA] P1. **Produce the deviation log** — one consolidated list (doc → claim → real state → source of truth),
      shared with the operator before Phase 2 starts. This is the actual "check for deviations" deliverable requested.

### Phase 2 — Design checkpoint (operator review before writing)

- [ ] [DESIGN] P0. **Finalize the exact 7-doc → source-doc mapping** (the table above is a starting hypothesis) —
      confirm with the operator, especially how `INSTRUMENT_SPECIFICATION.md`/`MVP_INSTRUMENTS.md`'s cross-cutting
      content splits between the adapter-architecture doc (general convention) and the 5 AG docs (per-AG specifics +
      deviations).
- [ ] [OPERATOR] P0. **Review the deviation log + finalized structure with the operator** before any prose is written —
      a checkpoint, not a rubber stamp; several deviations may need an operator decision on which side is correct (doc
      or code) before the new doc can state either.

### Phase 3 — Write (draft-gated on Phase 2 completing — do not start until the checkpoint above is done)

- [ ] [SCRIPT] P1. **Write `docs/SETUP_GUIDE.md`** (merge SETUP_GUIDE + SECRETS_SETUP + API_KEYS_STANDARDIZED_PROCESS +
      TEST_ALIGNMENT + CLOUD_OPERATIONS) — dedupe overlapping content, keep it a single coherent walkthrough.
- [ ] [SCRIPT] P1. **Write `docs/ADAPTER_ARCHITECTURE.md`** (merge ARCHITECTURE + COMMAND_FLOW_ANALYSIS +
      COMMAND_FLOW_DIAGRAM + VENUE_ADAPTERS + the general convention slice of INSTRUMENT_SPECIFICATION) — include the
      real `canonical_id_builder.py`-is-mostly-unused finding from `instrument_id_format_canonicalization_2026_07_08.md`
      so a new adapter author knows there is NOT one enforced builder to call.
- [ ] [SCRIPT] P1. **Rewrite `docs/CEFI_INSTRUMENTS.md`** — corrected per the deviation log, MVP-universe section added,
      cross-link to the mockup's CeFi tab + the canonicalization decision's dated-derivative findings
      (Kraken/Binance/Bybit/Deribit format divergences, the decided `@LIN`/`@INV` + `YYYYMMDD` target).
- [ ] [SCRIPT] P1. **Rewrite `docs/DEFI_INSTRUMENTS.md`** (absorbing DEFI_GUIDE) — corrected per the deviation log,
      MVP-universe section added, cross-link to the mockup's DeFi tab + the A_TOKEN/DEBT_TOKEN decision + the DEX-pool
      bare-address finding.
- [ ] [SCRIPT] P1. **Rewrite `docs/TRADFI_INSTRUMENTS.md`** (absorbing CORPORATE_ACTIONS) — corrected per the deviation
      log, MVP-universe section added, cross-link to the mockup's TradFi tab.
- [ ] [SCRIPT] P1. **Rewrite `docs/SPORTS_INSTRUMENTS.md`** — corrected per the deviation log, MVP-universe section
      added, cross-link to the mockup's Sports tab (fixtures-are-the-instrument model, bookmaker=venue,
      fixture/bookmaker/market_type odds structure).
- [ ] [SCRIPT] P1. **Rewrite `docs/PREDICTION_INSTRUMENTS.md`** (renamed from POLYMARKET_PREDICTION) — corrected per the
      deviation log, MVP-universe section added, cross-link to the mockup's Prediction tab.

### Phase 4 — Cutover

- [ ] [SCRIPT] P2. **Grep the whole workspace for links to the 10-12 retired docs** and update every cross-reference
      (other repos' CLAUDE.md files, codex docs, other plans) to point at the new 7-doc locations.
- [ ] [SCRIPT] P2. **Delete the retired docs** (no shims, no `# moved to X` stub files — per workspace governance,
      delete deprecated docs outright once cross-links are updated).
- [ ] [VERIFY] P2. **Final read-through of all 7 new docs** for internal consistency (no contradicting an adjacent doc)
      and confirm zero dangling links from the grep in the prior todo.

## Progress Log

- **2026-07-08** — Filed after the operator asked whether 17 overlapping instruments-service docs should collapse to 7
  (1 setup guide, 1 adapter-architecture guide, 5 per-asset-group docs with an explicit MVP-universe section each),
  cross-linked to this session's mockup + canonicalization-decision findings. Confirmed via real line-count/intro-skim
  of all 17 docs that the proposed 7-doc structure is achievable (top-level `docs/*.md` are already one-per-AG;
  `docs/specs/*.md` splits cleanly into setup-guide material, adapter-architecture material, and AG-specific material
  currently living outside its AG doc). Operator chose human-driven execution (assigned_vm: NA) over agent-orchestrator
  dispatch. No audit work started yet — Phase 1 is next.
- **2026-07-08 (later)** — Phase 1's audit was split out and run as its own effort per the operator's expanded ask
  (audit every service + GCS + manifest, not just cross-check the 17 docs) — see
  [[canonical_instrument_id_audit_2026_07_08]] (`plans/audit/results/`). That audit is now DONE: found 5 P0 live bugs
  - ~40 P1/P2 findings across instruments-service/MTDS/deployment-api/deployment-ui/GCS/manifest/strategy-service. This
    plan's `depends_on` now points at that audit doc — Phase 1 here is satisfied by its findings rather than a separate
    re-derivation. Phase 2 (design checkpoint) is next, once the 5 P0 bugs' own fix plans are underway.
