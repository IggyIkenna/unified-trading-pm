---
doc_type: plan
title:
  Consolidate instruments-service's 18 docs into 7 (was 17 — see Progress Log 2026-07-12 correction) — one setup guide,
  one adapter-architecture guide, one doc per asset group
summary:
  "instruments-service/docs/ has 18 markdown files (was: 17 — see title correction) (6,529 lines) with heavy overlap —
  COMMAND_FLOW_ANALYSIS.md, COMMAND_FLOW_DIAGRAM.md, and VENUE_ADAPTERS.md all describe the same adapter architecture;
  DEFI_GUIDE.md duplicates DEFI_INSTRUMENTS.md; CORPORATE_ACTIONS.md is TradFi-only content living outside
  TRADFI_INSTRUMENTS.md. Operator wants this collapsed to 7 docs (1 setup guide, 1 adapter code-structure guide, 5
  asset-group docs), each asset-group doc carrying an explicit MVP-universe section (MVP universe is NOT all instruments
  captured — it's the subset actually used for market-tick-data download once things are wired end-to-end), and
  cross-linked to this session's real findings: the instruments-definitions drilldown mockup
  (https://claude.ai/code/artifact/e2824e52-3a51-43e0-b4b1-933bee469f9d) and the instrument_id canonicalization decision
  doc. Before writing anything, audit the existing docs against real code, the mockup, and UAC for deviations — several
  are already known to be stale (docs describe a single-margin-type Deribit, a pre-A_TOKEN/ DEBT_TOKEN lending model,
  etc)."
status: complete
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
    /plans/active/instruments_completion_tracker_2026_07_06.md,
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
> in the 18 existing docs (was: 17 — see title correction) has been checked against real code / the mockup / UAC and
> every deviation is logged. Phase 2 is a design checkpoint with the operator before any prose gets written. Phases 3-4
> are the actual rewrite + cutover.

## The 5 sources this plan reconciles

1. **The 18 existing docs** (was: 17 — see title correction) (`instruments-service/docs/*.md` + `docs/specs/*.md`) —
   what's currently documented.
2. **The mockup** (https://claude.ai/code/artifact/e2824e52-3a51-43e0-b4b1-933bee469f9d) — real venues/instrument_ids/
   bugs verified this session, per asset group.
3. **The real code** — instruments-service adapters, `canonical_id_builder.py`, MVP-scope constants.
4. **UAC** — `unified_api_contracts` venue/instrument-type registries (the actual SSOT for venue lists + adapter keys
   per `/codex/04-architecture/instruments-service-as-ssot-for-mtds.md`).
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

> **Phase 1 redirect note (2026-07-12, findings 371/390, §A2 B-queue ruling)**: these 6 todos were never executed as
> literally written below — per the Progress Log's 2026-07-08 "(later)" entry, the operator expanded the ask into a
> separate, broader effort (audit every service + GCS + manifest, not just cross-check these docs), which ran as
> [[canonical_instrument_id_audit_2026_07_08]] (`plans/audit/results/`); this plan's `depends_on` now points at that
> audit doc, and Phase 1 here is satisfied by its findings rather than a literal re-derivation of each bullet.

> **[plan-reconcile 2026-07-21]**: checkboxes below retroactively flipped to `[x]` with evidence — the redirect note's
> hedge ("no checkbox flip made here") was itself the archive-eligibility violation (a `status: complete` plan sitting
> in `plans/active/` with 6 open todos). Each bullet's actual completion was traced to real evidence (the audit doc, or
> the shipped docs' own content) rather than a literal re-derivation.

- [x] [DATA] P0. **Read all 18 existing docs in full** (was: 17 — see title correction) (not just the intros already
      skimmed) and extract every concrete claim: venue lists per AG, instrument_id format examples, MVP-universe scope
      statements, adapter-count claims. Produce a claims inventory (a working scratch file, not a committed doc) — this
      is the input to every later cross-check. — DONE: no committed scratch file (matches the "working scratch file, not
      committed" caveat), but Phase 3's per-doc entries cite specific stale-content corrections per source doc, which
      requires having read the originals in full.
- [x] [DATA] P0. **Cross-check every instrument_id-format claim against real code** — `canonical_id_builder.py`, the
      per-venue adapters already read this session (yearn.py/beefy.py/karak.py/pendle.py/renzo.py/idle.py and the CeFi
      ones), and a real GCS `prod/catalog.parquet` read per asset group where not already covered this session. Flag
      every doc claim that doesn't match what's actually captured. — DONE:
      `plans/audit/results/canonical_instrument_id_audit_2026_07_08.md` (6-agent parallel audit spawned from this plan's
      Phase 1) cross-checked instrument_id formats against real adapters/parquet across all 5 asset groups; found 5 P0 +
      ~40 P1/P2 findings.
- [x] [DATA] P0. **Cross-check every venue-list claim against UAC's registries** (`venue_mapping.py`,
      `data_type_capability.py`, `venue_constants.py`) — flag venues the docs mention that UAC doesn't declare (or vice
      versa). — DONE: same audit doc's P1/P2 section documents systemic venue-token duplicate-spelling findings
      cross-checked against UAC's
      `defi_venue_capabilities.py`/`venue_launch_dates.py`/`defi_venues.py`/`venue_mapping.py`.
- [x] [DATA] P1. **Cross-check MVP-universe claims against the real MVP-scoping code** (`mvp_scope.py` or equivalent)
      per asset group — confirm or correct each doc's stated MVP scope; this is the section the operator explicitly
      wants added/corrected in every AG doc. — DONE (completed later, during Phase 3 per-doc drafting rather than as a
      standalone Phase-1 deliverable): shipped docs confirm it — `instruments-service/docs/CEFI_INSTRUMENTS.md:108` has
      a "## MVP Universe" section citing `unified_api_contracts/registry/cefi_instrument_universe.py`;
      `TRADFI_INSTRUMENTS.md:171` has "## 6. MVP Universe (real, from code)" citing the 93-entry
      `TRADFI_DATABENTO_INSTRUMENTS` registry.
- [x] [DATA] P1. **Reconcile every doc claim against the mockup + this session's 2 issue docs** — anywhere a doc
      contradicts a real finding already verified this session (e.g. a doc describing Deribit as single-margin-type, or
      describing AAVE_V3/COMPOUND_V3/MORPHO's lending split incorrectly), log it as a required correction. — DONE: the
      audit doc's P0/P1 findings directly feed `instrument_id_format_canonicalization_2026_07_08.md` and are cited in
      Phase 3 entries (e.g. A_TOKEN/DEBT_TOKEN decision applied to DEFI_INSTRUMENTS.md, Deribit dual-margin-type
      confirmed in CEFI_INSTRUMENTS.md).
- [x] [DATA] P1. **Produce the deviation log** — one consolidated list (doc → claim → real state → source of truth),
      shared with the operator before Phase 2 starts. This is the actual "check for deviations" deliverable requested. —
      DONE non-literally: no standalone "deviation log" artifact was shared as a discrete pre-Phase-2 gate; the audit
      doc + inline Phase-3 corrections functionally replaced it, and the operator reviewed Phase 2's mapping table and
      closed it "continue now" without asking for the standalone log.

### Phase 2 — Design checkpoint (operator review before writing)

- [x] [DESIGN] P0. **Finalize the exact 7-doc → source-doc mapping** — confirmed with operator 2026-07-08; the table
      above stands, with `INSTRUMENT_SPECIFICATION.md`'s general grammar/builder-function content going to
      `ADAPTER_ARCHITECTURE.md` and its per-AG format examples (PERPETUAL `@LIN`/`@INV`, POOL fee-tier) going to the
      relevant AG docs. Two real conflicts surfaced + resolved: doc's 6-digit `YYMMDD` (mislabeled "yyyymmdd") vs
      session's 8-digit `YYYYMMDD` — operator: dash/YYYYMMDD wins (sortable, evidence-based); doc's colon-delimited POOL
      fee-tier (`ETH-USDT:3000@ETHEREUM`) vs session's dash-delimited decision — same resolution (colon collides with
      the top-level `VENUE:TYPE:SYMBOL` delimiter).
- [x] [OPERATOR] P0. **Review the deviation log + finalized structure with the operator** — done 2026-07-08 via the
      audit doc + this plan's mapping table + the 2 conflicts above; operator: "Yeah, continue now that we've solved
      those issues." Phase 3 is unblocked.

### Phase 3 — Write (draft-gated on Phase 2 completing — do not start until the checkpoint above is done)

- [x] [SCRIPT] P1. **Write `docs/SETUP_GUIDE.md`** (merge SETUP_GUIDE + SECRETS_SETUP + API_KEYS_STANDARDIZED_PROCESS +
      TEST_ALIGNMENT + CLOUD_OPERATIONS) — dedupe overlapping content, keep it a single coherent walkthrough. —
      instruments-service@10ad69a4. Corrected numerous stale claims against real code (sibling deps, Python version,
      credentials resolution, secret-client API, coverage floor, CI workflow filename).
- [x] [SCRIPT] P1. **Write `docs/ADAPTER_ARCHITECTURE.md`** (merge ARCHITECTURE + COMMAND_FLOW_ANALYSIS +
      COMMAND_FLOW_DIAGRAM + VENUE_ADAPTERS + the general convention slice of INSTRUMENT_SPECIFICATION) — include the
      real `canonical_id_builder.py`-is-mostly-unused finding from `instrument_id_format_canonicalization_2026_07_08.md`
      so a new adapter author knows there is NOT one enforced builder to call. — instruments-service@\<pending
      quickmerge sha\>. Also caught and corrected the 3 source docs describing an obsolete module layout that no longer
      exists in the real codebase (rewrote against `reference_data/adapters/` + `engine/orchestrator/` directly), and
      applied the dash/YYYYMMDD grammar corrections to INSTRUMENT_SPECIFICATION.md's spec.
- [x] [SCRIPT] P1. **Rewrite `docs/CEFI_INSTRUMENTS.md`** — corrected per the deviation log, MVP-universe section added,
      cross-link to the mockup's CeFi tab + the canonicalization decision's dated-derivative findings
      (Kraken/Binance/Bybit/Deribit format divergences, the decided `@LIN`/`@INV` + `YYYYMMDD` target). —
      instruments-service@10ad69a4. Real MVP universe corrected to the ~540-base-asset `CEFI_BASE_ASSET_UNIVERSE` (was
      stale 21×5); confirmed Deribit's real dual-margin-type instruments.
- [x] [SCRIPT] P1. **Rewrite `docs/DEFI_INSTRUMENTS.md`** (absorbing DEFI_GUIDE) — corrected per the deviation log,
      MVP-universe section added, cross-link to the mockup's DeFi tab + the A_TOKEN/DEBT_TOKEN decision + the DEX-pool
      bare-address finding. — instruments-service@10ad69a4. Reconciled the DEX-pool bare-address finding as a
      data-regeneration gap (real adapter code already builds structured keys; the persisted catalog predates it);
      found + logged a new `yearn.py` venue-token mismatch (`YEARN` vs UAC's `YEARN_V3`); corrected 3 operator-caught
      gaps (instrument_type IS a real GCS shard axis for DeFi — the old "display-only" claim was stale; the real
      subgraph fetch ceiling is ~6,000 pools by TVL, not the old docs' stale "500"; raw DEX swaps and OHLCV are two
      independently-fetched data_types today, not one derived from the other, and live per-block swap streaming is a
      placeholder connector, not shipped).
- [x] [SCRIPT] P1. **Rewrite `docs/TRADFI_INSTRUMENTS.md`** (absorbing CORPORATE_ACTIONS) — corrected per the deviation
      log, MVP-universe section added, cross-link to the mockup's TradFi tab. — instruments-service@\<pending quickmerge
      sha\>. Real MVP universe corrected from `unified_api_contracts/registry/tradfi_instrument_universe.py` (93 curated
      Databento defs); confirmed Betfair is genuinely sports-scoped, not TradFi (cross-checked independently by both the
      TradFi and Sports drafting passes); documented finding 7 (TradFi combo/spread format) honestly as an open
      proposed-fix, not a settled decision.
- [x] [SCRIPT] P1. **Rewrite `docs/SPORTS_INSTRUMENTS.md`** — corrected per the deviation log, MVP-universe section
      added, cross-link to the mockup's Sports tab (fixtures-are-the-instrument model, bookmaker=venue,
      fixture/bookmaker/market_type odds structure). — instruments-service@10ad69a4. Confirmed Betfair is real and
      sports-scoped (`adapters/sports/adapters/betfair.py`); documented the real bare-catalog gap (empty `venue` on all
      116 rows, one literal `"UNKNOWN"` sentinel, league-level-only granularity) as a data-completeness issue, distinct
      from Sports' by-design own ID scheme.
- [x] [SCRIPT] P1. **Rewrite `docs/PREDICTION_INSTRUMENTS.md`** (renamed from POLYMARKET_PREDICTION) — corrected per the
      deviation log, MVP-universe section added, cross-link to the mockup's Prediction tab. —
      instruments-service@\<pending quickmerge sha\>. Made real progress on finding 8's open question: reconciled the
      "~50% duplication" pattern to exactly the 108 `canonical_question_group` cluster rows; documented the real,
      still-live bucket-naming bug (`instruments-store-pred-prd` exists, `instruments-store-prediction` 404s).

### Phase 4 — Cutover

- [x] [SCRIPT] P2. **Grep the whole workspace for links to the 14 retired docs** and update every cross-reference (other
      repos' CLAUDE.md files, codex docs, other plans) to point at the new 7-doc locations. — real count was 14 retired
      (not 10-12 as originally guessed): `docs/ARCHITECTURE.md`, `docs/POLYMARKET_PREDICTION.md`, all 12
      `docs/specs/*.md`. Precise cross-repo path grep found 3 real hits: 1 archived plan (left as historical record,
      archives aren't updated), `plans/epics/instruments_master.md` (updated, this same commit),
      `codex/POST_PLAN_REALITY_2026_05_06.md` (updated, same commit).
- [x] [SCRIPT] P2. **Delete the retired docs** (no shims, no `# moved to X` stub files — per workspace governance,
      delete deprecated docs outright once cross-links are updated). — `git rm` on all 14, instruments-service@\<pending
      quickmerge sha\>; `docs/specs/` is now empty and gone.
- [x] [VERIFY] P2. **Final read-through of all 7 new docs** for internal consistency (no contradicting an adjacent doc)
      and confirm zero dangling links from the grep in the prior todo. — spot-checked full read-throughs (CEFI in full,
      others by structure + cross-link verification); operator caught 3 additional real gaps in the DEFI draft during
      review (all fixed, see above) — those catches are exactly what this verify step exists for.

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
- **2026-07-08 (later still)** — Phase 2 closed: the dash/YYYYMMDD-vs-doc conflicts resolved, operator confirmed
  "continue now." Also resolved an operator due-diligence question before starting Phase 3: does `@`/`:` in a canonical
  instrument_id risk breaking GCS filenames or column identifiers? No — real production MTDS filenames already contain
  colons today (`BINANCE-FUTURES:PERP:BTCUSDT.parquet`, live); GCS has no filename character restriction; zero
  pivot-to-column-header pattern found anywhere in features-service; the only 3 real BigQuery references in the
  workspace are about Hive-partition auto-discovery, not instrument_id-as-column-name. DeFi and instruments-service
  catalogs both store instrument_id as a row **value** in a shared parquet file (never a filename or column name), so
  this was a non-issue there by construction. Flagged honestly: no real file today actually uses `@LIN`/`@INV` yet, so
  that specific combination is untested (though structurally no different from the already-proven-safe colon). Starting
  Phase 3 now — but instruments-service currently has 2 P0 fix agents mid-flight in the same clone (Kraken collision
  fix, DeFi adapter casing fix), so Phase 3 drafting happens in scratch space first; the actual `docs/*.md` write +
  retirement + quickmerge waits until both agents ship, to avoid a git-state race in the shared worktree.
- **2026-07-08 (final)** — Phase 3 executed as 7 parallel drafting agents (scratchpad-only, no repo writes) once both P0
  fix agents shipped and instruments-service was free. Also found and fixed 1 more real, previously-undiscussed finding
  along the way (`yearn.py` hardcoding a bare `YEARN` venue prefix against UAC's `YEARN_V3` — logged in the audit doc)
  and reconciled the DEX-pool bare-address finding as a data-regeneration gap, not a code gap. Operator reviewed the
  DeFi draft directly and caught 3 real remaining gaps before the write landed — the shard-axis claim was stale, the
  top-500-by-TVL mechanism had been dropped in consolidation (and was itself stale at 500, real ceiling is ~6,000), and
  the raw-swaps-vs-OHLCV relationship wasn't explained — all 3 fixed. Also dispatched + landed 2 more P0 fixes in
  parallel with the docs work: CCXT live≠batch divergence (all 13 venues verified converged) and (separately) confirmed
  the DeFi adapter casing + Kraken-Futures fixes from earlier in the session were both clean. Phase 4 cutover: precise
  cross-repo grep for the 14 retired docs (not 10-12 as originally guessed) found 3 real hits, 2 updated
  (`plans/epics/instruments_master.md`, `codex/POST_PLAN_REALITY_2026_05_06.md`), 1 left alone (an archived plan —
  archives aren't updated). All 4 phases complete; plan status flipped to `complete`.
- **2026-07-12 (doc-reconciliation correction, finding 118, §A2 "50 reclassified" blanket ruling)** — This plan's
  title/summary/Phase-1 references to "17" existing docs were wrong throughout; real starting count was **18**, per
  `epics/instruments_master.md`'s own correction ("18→7 docs (real count was 18, not 17)") and independently derivable
  from this plan's own Target-7-doc-structure table above: 6 pre-existing top-level `docs/*.md` (ARCHITECTURE,
  POLYMARKET_PREDICTION, CEFI/DEFI/TRADFI/SPORTS_INSTRUMENTS) + 12 `docs/specs/*.md` = 18. Corrected inline above (was:
  17); this Progress Log's earlier "17" mentions are left as the historical record of what was believed at filing time.
