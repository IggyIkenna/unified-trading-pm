---
doc_type: issue
title:
  "deployment-ui's bundled capability-manifest.json / capability-verdict-matrix.json still show DRIFT (Solana) as a
  live, supported venue — bundle predates the 2026-07-16 Solana-perp-DEX cull by 934 UAC commits"
summary:
  'Operator ruling 2026-07-16 killed DRIFT-SOLANA + PACIFICA-SOLANA workspace-wide (UAC, UTL, instruments-service, MTDS,
  deployment-service, execution-service, unified-trading-system-ui, strategy-service, e2e-testing, PM — 11 repos). A
  follow-up fleet grep caught deployment-ui''s user-facing TreasuryTab dropdown (fixed same session, see Progress Log)
  but the sweep also surfaced two large committed data files that were OUT OF SCOPE for a hand-edit:
  `deployment-ui/src/data/capability-manifest.json` (574 nodes / 2433 edges, 21 touching `venue:drift` /
  `collateral:drift`) and `deployment-ui/src/data/capability-verdict-matrix.json` (66 `"venue": "drift"` rows across
  archetypes/verdicts). Both carry a `generated_from_commit` provenance field pointing at UAC commit `9b03b3bf` —
  verified via `git merge-base --is-ancestor` to be an ANCESTOR of (i.e. 934 commits behind) the DRIFT cull commit
  `7628dd30`, so the bundle is provably stale, not just suspicious. These files are consumed by
  `src/components/CapabilityTab.tsx` (a real UI surface, static-loaded, no network) — an operator viewing the Capability
  tab today sees DRIFT offered as a `live-proven` / `available` venue for strategies, and Solana LST collateral
  (JitoSOL/SOL/USDC/mSOL) shown as accepted BY drift, none of which is true post-cull. No dedicated sync/generator
  script for these two bundled files exists inside deployment-ui itself — prior updates landed as `chore(capability):
  re-sync bundled manifest to UAC <node>/<edge> (...)` commits, implying an out-of-repo or ad-hoc regeneration process
  this session did not have access to. Given the size (92k lines combined) and the risk of silently breaking referential
  integrity (edges pointing at a deleted node) from a manual JSON patch without the actual generator, this was triaged
  as a big cross-repo finding to flag rather than hand-edit blind.'
status: open
nature: notes
asset_group: [defi]
stage: [meta]
repos: [deployment-ui, unified-api-contracts]
scope: [engineer]
tags: [drift, pacifica, solana, capability-manifest, stale-bundle, data-correctness, ui]
related:
  [
    /codex/04-architecture/solana-defi-coverage.md,
    /codex/06-coding-standards/ui-testing-layers.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-07-16
author: unknown
parent_epic: defi_master
priority: P2
source:
  'Operator ruling 2026-07-16: "kill drift entirely from our whole system... kill all other solana perp dex''s. uac,
  code, adaptors, manifest, gcs, everything." Discovered as a side-finding while fixing the TreasuryTab
  SUB_ACCOUNT_DRIFT dropdown bug in deployment-ui (the 12th repo the operator''s fleet grep caught).'
assigned_vm: planning
resolved_by:
locked_by:
context_scope:
  [
    scripts/openapi/generate_strategy_prospectus.py,
    unified-api-contracts/openapi/prospectus,
    /codex/06-coding-standards/script-homes.md,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch3_2026_07_26.md,
  ]
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: refactor
estimate_baseline_ai_days: 0.5
drift_direction: advance-code
depends_on: []
---

# deployment-ui capability bundle still shows DRIFT as a live venue

## What's wrong

`deployment-ui/src/data/capability-manifest.json` and `deployment-ui/src/data/capability-verdict-matrix.json` are
committed, static, generated snapshots consumed by `src/components/CapabilityTab.tsx` (lazy-loaded, no network —
`capability-verdict-matrix.json` is ~2.2 MB per that component's own doc comment). Both carry a `generated_from_commit`
field:

```
$ python3 -c "import json; print(json.load(open('src/data/capability-manifest.json'))['generated_from_commit'])"
9b03b3bfdda77361313b0286863a0122d4a99630
```

Verified against the UAC repo:

```
$ git -C unified-api-contracts merge-base --is-ancestor 9b03b3bf 7628dd30 && echo "ancestor: YES"
ancestor: YES
$ git -C unified-api-contracts log --oneline 9b03b3bf..7628dd30 | wc -l
934
```

So the bundle was generated 934 UAC commits before `7628dd30`, one of the three UAC commits (`7628dd30`, `cb486e42`,
`c5867215`) that shipped the operator's 2026-07-16 Solana-perp-DEX cull. It still contains:

- `capability-manifest.json`: a `venue:drift` node (`"label": "Drift"`, `"asset_group": "DEFI"`) with 17 edges (mostly
  `relation: "supports"`, `status: "available"`, `readiness: "live-proven"` from various archetypes), plus a
  `collateral:drift` node with 4 edges describing JitoSOL/SOL/USDC/mSOL haircuts accepted by Drift.
- `capability-verdict-matrix.json`: 66 rows with `"venue": "drift"` across the `archetypes`/`verdicts` sections.

An operator opening the Capability tab today sees DRIFT presented as a supported, `live-proven` venue — the same class
of user-facing bug as the TreasuryTab dropdown (fixed this session), except in a generated data file instead of
hand-authored JSX.

## Why this wasn't fixed in the same pass

- The files are large (29,170 + 63,122 lines) and machine-generated — prior updates to them landed via
  `chore(capability): re-sync bundled manifest to UAC <n>/<n> (...)` commits (e.g. `7962511`, `99a5f51`, `c1ba2aa` in
  `git log -- src/data/capability-manifest.json`), which implies a real regeneration process exists, but no script
  producing these two specific bundled files was found inside `deployment-ui/` itself (checked `scripts/`,
  `tests/unit/capability-verdict-matrix-loader.test.ts`, `tests/unit/capability-helpers.test.ts`,
  `src/lib/capability-helpers.ts` — all consumers/loaders, not generators).
- UAC's own generator (`unified-api-contracts/scripts/generate_archetype_capability_manifest.py`) writes UAC's _own_
  `archetype_capability_manifest.json` (already current — UAC's cull already ran), not deployment-ui's bundle; the
  deployment-ui bundle appears to be a separate downstream artifact, possibly re-synced by an agent with cross-repo read
  access to UAC's `capability-readiness-report.md` / `capability-unlock-report.md` plus some transform this session did
  not locate.
- A blind manual deletion of the `venue:drift` / `collateral:drift` nodes + their 21 edges (manifest) and 66 rows
  (verdict-matrix) risks silent referential-integrity breaks (e.g. a `relation` edge whose `to_node_id` no longer
  resolves to any node) across two 90k-line files with no test asserting "every edge resolves to a real node" that this
  session could find in the time available — exactly the kind of blast-radius a solo hand-edit is a bad way to close.

## Recommended fix

1. Find/rebuild whatever process produced the `chore(capability): re-sync bundled manifest to UAC ...` commits (check
   `agent-orchestrator` dispatch history / prior session transcripts for the actual regen command — it is very likely a
   short script an agent ran ad hoc against a checked-out UAC, not something committed anywhere).
2. Re-run it against current UAC (`live-defi-rollout` HEAD, post-cull) to regenerate both bundled files.
3. If no such tooling is recoverable, write one: mirror
   `unified-api-contracts/scripts/generate_archetype_capability_manifest.py`'s approach (serialize the live UAC registry
   deterministically) but targeting deployment-ui's manifest/verdict-matrix shape, and commit it under
   `deployment-ui/scripts/` with the standard `# Epic:` / `# Lifecycle:` / `# Delete-when:` lifecycle marker per
   `/codex/06-coding-standards/script-homes.md`.
4. After regeneration, run `tests/unit/capability-verdict-matrix-loader.test.ts` +
   `tests/unit/capability-helpers.test.ts` + the `CapabilityTab` smoke spec (if one exists under `tests/smoke/`) to
   confirm the tab still renders, then quickmerge scoped to the two data files + any new script.

## Verification once fixed

```
rg -n '"venue:drift"|"collateral:drift"|"venue": "drift"' deployment-ui/src/data/capability-manifest.json \
  deployment-ui/src/data/capability-verdict-matrix.json
# should return zero matches
```

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid - the prospectus generator has drifted from the committed files on
  multiple unrelated axes so a blind regen is unsafe; which side is authoritative is undecided and the item is unowned

- 2026-07-16: Discovered during the deployment-ui DRIFT/PACIFICA venue sweep (TreasuryTab SUB_ACCOUNT_DRIFT dropdown fix
  session). TreasuryTab dropdown + mocks + specs fixed and shipped separately
  (`deployment-ui@<sha-filled-in-by-quickmerge>`); this capability-bundle finding filed as its own issue per the
  findings-triage HARD RULE (cross-repo, data-correctness-adjacent, too large to hand-fix in the same pass).

## Second instance — `unified-trading-system-ui/lib/registry/ui-reference-data.json` (coordinator, 2026-07-16)

Same class, different repo/file. Found by the fleet-wide closing grep AFTER two surgical enum fixes to this very file
had already shipped — a caution that "I fixed that file" != "that file is clean".

- **na-eligibility-audit 2026-08-04** (tranche=defi, dispatch agt-62865a): KEEP-NA valid (prior verdict re-affirmed) —
  the sole remaining open item (resync the prospectus generator) is still genuinely judgment-gated: the generator has
  drifted from committed files on multiple unrelated axes and no worker can determine a done-state without a human
  design decision on which side is authoritative. Doc stays `assigned_vm: NA`.

**Fixed + shipped (safe, surgical — enum MIRRORS of UAC, verified against the live enums):**

- `unified-trading-system-ui@70ca4b8c` — dropped `KILL_PER_TREASURY_SUB_ACCOUNT_DRIFT` from the mirrored `KillSwitchId`
  list. Verified: zero UI kill-switch ids missing from UAC's enum.
- `unified-trading-system-ui@15270ed6` — dropped `SUB_ACCOUNT_DRIFT` from the mirrored `TreasurySource` list. Verified
  against UAC's live enum `[COPPER, CEFFU, DEFI_HOT_WALLET, SUB_ACCOUNT_HYPERLIQUID, SUB_ACCOUNT_DYDX]` — exact match.
  (Same bug class as the operator-facing `deployment-ui` TreasuryTab dropdown, fixed at `deployment-ui@26b7159`.)

**NOT fixed — the generated-bundle class this issue is about (needs the resync tooling, do NOT hand-patch):**

`lib/registry/ui-reference-data.json` still carries **~40 lines** of lowercase `drift` inside GENERATED archetype /
capability data — e.g. `"venue_ids": ["drift", "gmx_v2", "hyperliquid"]`,
`"venue_ids": ["drift", "gmx_v2", "hyperliquid", "lido", "uniswap_v3"]`, the archetype id
`CARRY_STAKED_BASIS@jito-kamino-drift-sol-usdc-prod`, and free-text `notes` describing a Solana Jito/Marinade + Kamino +
**Drift** hedge leg. No generator/sync script for this file exists inside the repo (only docs reference it), exactly as
for `deployment-ui`'s `capability-manifest.json` / `capability-verdict-matrix.json`. Hand-editing archetype-graph
nodes/edges blind risks corrupting a generated bundle, so this was deliberately left for the resync tooling this issue
already calls for.

**Grep lesson worth keeping:** the cull's closing greps were UPPERCASE-biased (`DRIFT-SOLANA`, `SUB_ACCOUNT_DRIFT`) and
therefore blind to lowercase venue ids (`"drift"`) in generated JSON. Any future venue cull should grep
case-insensitively AND sweep whole files, not just the matched pattern.

## Third instance — `unified-api-contracts/openapi/*.json` (2026-07-16)

Same class, third repo/location — found during a venue-context (not blanket `drift_|_drift`) case-insensitive sweep of
`unified-api-contracts` + `unified-trading-library` dispatched after the operator flagged that the cull's closing greps
were uppercase-biased. All the LIVE-CODE `"drift"` residue in UAC's own
`unified_api_contracts/internal/architecture_v2/` subsystem (the strategy-archetype leg-spec / capability / collateral /
jurisdiction / order-semantics registries — 7 Python source files: `collateral_registry.py`,
`simulation_assumptions.py`, `jurisdiction_overlay.py`, `order_semantics.py`, `venue_tokens.py`,
`archetype_leg_spec.py`, `archetype_leg_spec_seeds.py` — plus 2 test files, `test_collateral_registry_backfill.py` and
`test_jurisdiction_overlay_backfill.py`) was hand-fixed + shipped this session (UAC commit — see this repo's own
Progress Log / the dispatching session's final report for the exact sha). UAC's own
`unified_api_contracts/internal/architecture_v2/archetype_capability_manifest.json` — which HAS an in-repo generator
(`scripts/generate_archetype_capability_manifest.py`, round-trip parity checker) — was hand-edited (venue_ids +
representative_slot_labels + notes) and verified round-trip clean via
`python scripts/generate_archetype_capability_manifest.py` (`archetype_capability_manifest.json is up-to-date`).

That leaves exactly the SAME stale-bundle class as the `deployment-ui` / `unified-trading-system-ui` instances above,
this time inside UAC's own `openapi/` directory — **no in-repo generator found for any of the three**, so none were
hand-patched:

- `unified_api_contracts/openapi/capability-manifest.json` — `generated_from_commit: f0b66b26...` — verified via
  `git merge-base --is-ancestor f0b66b26 <cull-commit>` to be an ANCESTOR, **821 commits behind current UAC HEAD**.
  Carries a `venue:drift` node (`"label": "Drift"`) + a `collateral:drift` node, 22 edges touching them.
- `unified_api_contracts/openapi/capability-verdict-matrix.json` — `generated_from_commit: 61ba5239...` — also a
  verified ancestor, **100 commits behind current UAC HEAD**. ~70 `"venue": "drift"` rows across
  `archetypes`/`verdicts`.
- `unified_api_contracts/openapi/capability-unlock-report.json` — `manifest_commit: fd87026a...`, downstream of the same
  stale `capability-manifest.json` — 3 `"to_node_id": "venue:drift"` edge references in its `impossible`/`roadmap`
  sections.

`grep -rln 'capability-manifest.json\|capability-verdict-matrix.json\|capability-unlock-report.json' scripts/` inside
`unified-api-contracts` returns nothing — same "prior updates landed via an out-of-repo/ad-hoc regen process" situation
as `deployment-ui`, not the same generator as UAC's OWN `archetype_capability_manifest.json` (that generator only
serialises `ARCHETYPE_CAPABILITY_REGISTRY` back to UAC's own committed file — it does not touch `openapi/`). Filed here
rather than hand-patched per the same blast-radius reasoning as the first two instances (referential-integrity risk
across large generated files with no "every edge resolves to a node" test found in UAC either).

**Also NOT fixed (downstream of UAC, out of this session's UAC/UTL-scoped dispatch, flagged for the operator):**
`unified-trading-system-ui/lib/registry/ui-reference-data.json` `venue_set_variants` / `archetype_capability_registry`
sections and `unified-trading-system-ui/tests/e2e/_shared/strategy-registry.ts` (`CARRY_STAKED_BASIS.instanceIds` still
lists `CARRY_STAKED_BASIS@jito-kamino-drift-sol-usdc-prod`) — both downstream mirrors of the UAC
`archetype_capability_manifest.json` slot label this session just removed from the UAC source. Already independently
discovered and documented in this session's sibling issue doc
`architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md` (UAC-source portion now resolved by this dispatch;
the UI-mirror portion remains open there).

**Fourth instance found, NOT applied — `unified-api-contracts/openapi/prospectus/*.md` (57 files)**: these carry a
`[MACHINE-DERIVED]`/`[CODEX-DERIVED]` header and a real in-repo(-adjacent) generator —
`unified-trading-pm/scripts/openapi/generate_strategy_prospectus.py` — unlike the three JSON bundles above. Ran it dry
(`--uac-root <UAC> --output-dir <scratch>`) to check whether regenerating would cleanly drop the `DRIFT` residue
(`CARRY_STAKED_BASIS.md`, `CARRY_STAKED_BASIS_DATED.md`, `CARRY_BASIS_PERP.md`, `CARRY_RECURSIVE_STAKED.md`,
`YIELD_STAKING_SIMPLE.md` all still list DRIFT in venue-universe tables/mermaid diagrams post the UAC source fix). The
dry-run diff shows the generator has drifted (no pun intended) from the committed files on MANY unrelated axes too —
different venue-category classification (CEFI+DEFI vs DEFI-only), different execution-algorithm lists (including literal
`Selector contradiction: ...` diagnostic strings not present in the committed copies), different markdown fence/table
formatting, a different `generated_from_commit` baseline, and 2 archetypes (`CARRY_FUNDING_DISPERSION.md`,
`TSMOM_BTC_CTA.md`) that don't exist in the committed set at all. This is the same "blind full regen risks silently
changing more than the one thing you meant to fix" situation as the JSON bundles — NOT applied. Non-blocking for
shipping (no `unified-api-contracts` quality-gate reads `openapi/prospectus/`), so left for whoever owns the
prospectus-generator/committed-copy resync.

## Progress log

- **2026-07-21 (slot-4, Track 6 `defi_consolidated_closeout_2026_07_18.md`) — the FIRST instance
  (`deployment-ui/src/data/capability-manifest.json` + `capability-verdict-matrix.json`) is now PRUNED, not fully
  regenerated.** Confirmed the recommended-fix's step 1/2 (recover or rebuild the real generator) is not achievable in
  scope: no committed generator exists anywhere searched (deployment-ui `scripts/`, UAC `scripts/`), and
  `capability-verdict-matrix.json`'s own `reason` strings cite a `config_space_fuzzer` module that does not exist either
  — this is a genuinely lost, bespoke, ad-hoc-run tool, not a case of "we didn't look hard enough." Given that, did a
  **formula-verified, referential-integrity-checked surgical prune** instead of a blind full rewrite (the exact risk
  this doc already flagged): removed the `venue:drift`/`collateral:drift` nodes + their 21 edges from the manifest
  (574→572 nodes, 2433→2412 edges — confirmed zero NEW dangling edge references vs. the pre-existing baseline, which
  already had one unrelated dangling `venue:ibkr` ref and one unrelated duplicate `EVENT_DRIVEN` node, both left
  untouched/out of scope), fixed one stale free-text "Jito/Marinade + Kamino + Drift" mention in a `CARRY_STAKED_BASIS`
  edge's `reason` field, and removed the 66 `venue=drift` cells from the verdict-matrix with correctly recomputed
  per-archetype + top-level summary counts (formula verified byte-for-byte against every OTHER archetype in the file
  before editing: `available_count=Σlen(available_algos)`, `blocked_count=Σlen(blocked_algos)`, `cell_count`=their sum;
  new summary total=20,544, available=12,122, blocked=7,974, not_registered=448 unchanged). Both files' custom
  pretty-printing (dicts always expand, scalar-only lists inline up to a 111-char line width) was reverse-engineered and
  round-trip-verified byte-for-byte BEFORE editing, so the diff is minimal and reviewable rather than a full-file
  reformat. `generated_from_commit` left UNCHANGED (still ~1000+ commits stale) — this is a documented delta on the
  stale base, not a claim of freshness; recovering/building the real generator (this doc's step 1-3) remains the actual
  durable fix and stays open. Also updated the 2 Playwright assertions in `tests/smoke/capability_tab.spec.ts` that
  hardcoded the old (bug-including) counts; `tsc`/`eslint`/`vitest` (1038 tests) + `pw:L2` (all 9
  `capability_tab.spec.ts` cases, incl. a real browser render confirming DRIFT no longer shown) all green. Shipped:
  `deployment-ui@83ec561`. The second/third/fourth instances in this doc (unified-trading-system-ui, UAC `openapi/`,
  prospectus generator) are UNCHANGED by this pass — out of this dispatch's deployment-api/deployment-ui scope.

- **2026-07-26 (slot-2) — SECOND + THIRD instances CLOSED** (`defi_satellite_ao_dispatch_batch2_2026_07_26.md` P2
  `[ENGINEER]` todo). Same class, same formula-verified surgical-prune playbook as the first instance.
  - **Second instance** (`unified-trading-system-ui/lib/registry/ui-reference-data.json`): 24 changes — 7 `venue_ids`
    array elements, 1 free-text `notes` mention, 1 `representative_slot_labels` entry, 1 `strategy_registry.families`
    entry, 1 whole `strategy_registry.strategies` object, and 13 `venue_set_variants` entries with their
    `"(N venues)"`/`"(N DEFI)"` labels formula-recomputed. Zero dangling refs to the removed strategy id (verified via a
    full-tree walk). Custom pretty-printer (dicts expand; scalar lists inline under a 120-col-incl.-prefix width budget)
    round-trip-verified byte-identical against the whole 15,726-line file before editing. `vitest` 286 files/3286 tests
    green, `tsc` clean. Shipped `unified-trading-system-ui@80bb6a9c`.
  - **Third instance** (UAC `openapi/{capability-manifest,capability-verdict-matrix,capability-unlock-report}.json`):
    checked whether `unified-trading-pm/scripts/openapi/generate_capability_*.py` (real generators exist — this doc's
    "no generator found" only checked inside UAC's own `scripts/`, not the sibling PM repo) could just be re-run
    instead; a live test regen showed UAC has drifted enough since the last full regen that blind re-run pulls in a
    large unrelated diff (capability-manifest 576→583 nodes / 2449→2763 edges from unrelated changes) — same
    blast-radius risk already flagged for the prospectus generator (fourth instance below). Formula-verified surgical
    prune stayed the right call: removed `venue:drift`/`collateral:drift` (2 nodes, 21 edges) from
    `capability-manifest.json` (zero NEW dangling refs — the only dangling refs left are the pre-existing unrelated
    `venue:ibkr` gap, confirmed present in the baseline before this edit too; `check_capability_regression.py` PASS);
    removed 69 `(archetype, venue=drift)` cells across 9 archetypes from `capability-verdict-matrix.json` with
    `available_count`/`blocked_count`/`cell_count` + top-level `summary` formula-recomputed and re-verified
    (`cell_count = available_count + blocked_count`); removed 3 `venue:drift` roadmap entries from
    `capability-unlock-report.json` with `missing_piece_counts`/`unlock_distance_histogram`/`roadmap_edges`/
    `blocked_edges_total` recomputed. A concurrent slot-7 commit (`13266bf8`, unrelated D3 CARRY_BASIS_PERP scope work)
    regenerated `capability-manifest.json`/`capability-verdict-matrix.json` for real mid-flight and, as a side effect,
    already dropped the drift residue from those two (plus legitimate additions my hand-prune didn't have) — resolved
    via rebase by keeping their fresher regen for those two files and landing only the `capability-unlock-report.json`
    prune (untouched by their regen) on top. Shipped `unified-api-contracts@6af1b966`. Also discovered + fixed two
    UNDOCUMENTED byte-identical "md5-parity with UAC" copies in `unified-trading-system-ui`
    (`lib/registry/capability-manifest.json`, `public/capability-verdict-matrix.json`) that this doc's original audit
    never found (it only checked UAC's own `scripts/`, not this repo) — re-synced from the fixed UAC originals + fixed 8
    hardcoded node/edge/cell/venue-count assertions in `tests/unit/wizard/{graph,parity-gates}.test.ts` that had baked
    in the stale (drift-including) totals. Shipped `unified-trading-system-ui@a0105d9f`.
  - Net across both instances: zero remaining `venue:drift`/`collateral:drift`/`"drift"`-venue references anywhere
    checked this pass. The fourth instance (`openapi/prospectus/*.md`, 57 files) remains explicitly open — same
    generator-drift blast-radius risk, unowned, per this doc's existing note above.

## Fifth pass — same instances, GMX venue this time (interactive session, 2026-08-04, `/autonomous`)

The 2026-07-25 GMX venue removal (`/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`) hand-fixed UAC's live
Python registries and ran its own definition-of-done grep, but — exactly like the DRIFT case this doc tracks — that grep
was word-boundary (`\bgmx\b`), which cannot match `gmx_v2`/`gmx-arbitrum` (the actual live token forms), and the
generated-bundle class of file this doc exists for was never in scope. An operator report ("GMX coming up as a venue")
led to a live audit finding gmx_v2 residue across the SAME three instance locations this doc already tracks, plus one
this doc doesn't cover (UAC's own internal `archetype_capability_manifest.json`, which is genuinely hand-authored
source-of-truth, not generated from Python — the round-trip generator only proves internal consistency, never proved
GMX-freedom). All fixed and shipped this session, live-verified (tests green, `check_capability_regression.py` PASS):

- **UAC internal source** — `unified_api_contracts/internal/architecture_v2/archetype_capability_manifest.json`: hand-
  edited 9 cells (removed `gmx_v2` from `venue_ids`, dropped gmx-specific `representative_slot_labels`, flipped
  `LIQUIDATION_CAPTURE`/DEFI/perp from PARTIAL→BLOCKED since gmx_v2 was its sole venue — added a new `BL-12` block-list
  entry, mirrored into `/codex/09-strategy/architecture-v2/block-list.md` + `unified-trading-system-ui`'s
  `block-list.ts`), regenerated clean via `generate_archetype_capability_manifest.py --write`.
  `unified-api-contracts@5474716e`.
- **Third instance** (UAC `openapi/capability-manifest.json` + reports) — full regen via
  `unified-trading-pm/scripts/openapi/generate_capability_manifest.py` was safe this time (unlike the 2026-07-26 DRIFT
  pass, which hit a large unrelated diff and fell back to surgical prune) — 0 regressions on
  `check_capability_regression.py`, same commit as above.
- **First instance** (`deployment-ui/src/data/capability-manifest.json` + `capability-verdict-matrix.json`) — same
  formula-verified surgical-prune playbook as the DRIFT pass (this doc's 2026-07-21 entry): 4 nodes / 26 edges removed
  from the manifest (572→568 / 2412→2386, zero new dangling refs vs. baseline), 66 `venue=gmx_v2` cells removed from the
  verdict-matrix across 8 archetypes with `available_count`/`blocked_count`/`cell_count`/top-level `summary`
  formula-recomputed (total_cells 20544→19488, blocked 7974→6918, available/not_registered unchanged) — both files'
  custom pretty-printer (dicts expand, scalar-only lists inline ≤120-char width, verified byte-for-byte round-trip
  before editing). Updated the 2 hardcoded Playwright count assertions in `tests/smoke/capability_tab.spec.ts`. `vitest`
  (1096 tests) + `tsc` + full `quality-gates.sh` green. `deployment-ui@24d06ac`.
- **Second instance** (`unified-trading-system-ui/lib/registry/ui-reference-data.json`) — surgical prune across all 3
  sub-structures this doc's DRIFT pass already established as the pattern: `archetype_capability_registry.per_archetype`
  (9 cells), `strategy_registry.strategies` (4 gmx-only instances removed) + `.families` (4 string refs removed),
  `venue_set_variants` (18 entries, venue removed + `(N ...)` count recomputed). Also re-synced
  `lib/registry/capability-manifest.json` (byte-copy from the freshly-regenerated UAC original, matching this doc's
  established "re-sync from UAC" convention) and `public/capability-verdict-matrix.json` (its own automated sha256
  parity gate in `tests/unit/wizard/parity-gates.test.ts` was independently failing on unrelated drift — fixed via the
  gate's own prescribed `cp` fix). `lib/architecture-v2/coverage.ts` (the UAC-generated TS mirror) hit the SAME
  unrelated-drift-from-a-blind-regen risk this doc's "Fourth instance" section already warns about (new archetypes in
  UAC's registry not yet in this repo's `StrategyArchetype` enum) — reverted the full regen, did a targeted 9-cell
  surgical edit instead, same playbook as the JSON files. Fixed 3 hardcoded test-count assertions (venue count 225→224,
  BLOCK_LIST 10→11 entries) + added the `BL-12` codex/TS mirror entries this fix required. `vitest` (3300 tests) +
  `tsc` + full `quality-gates.sh` green. `unified-trading-system-ui@3c2efb2c`.
- **Orphan GCS objects** (new finding, not a "bundle" instance): 4 pre-existing `venue=GMX` liquidations parquets
  (`day=2020-12-01`, `_migrated_gmx_{ARBITRUM,AVALANCHE}_*` filenames — artifacts of an unrelated 2026-06-21/22
  migration/fold script, never registered in the manifest, so the 2026-07-25 purge's manifest-driven day-loop never
  visited them) found + deleted via the sanctioned `unified_trading_library.cloud_interface.gcs_delete_object` SDK path
  (bucket soft-delete retention = 604800s, qualifying the reversibility-verified self-service carve-out); verified gone
  via a fresh `gcs_describe_object` read post-delete.
- **Live-writer resurrection check** (the operator's specific worry, given a long-running defi backfill VM booted
  2026-07-23, two days before the removal): read both currently-running `mtds-dex-swaps-backfill-*` VMs' own per-VM
  manifest shards directly from GCS (`_index/per_vm/*.parquet`) — 4527 + 400 rows, zero GMX venue rows, 100% canonical
  `dex_pool_swaps` data_type. The removal genuinely holds live; the residue was entirely in stale generated snapshots +
  the 4 orphan objects above, never an active resurrection.

Net: zero remaining live `gmx`/`gmx_v2` references found in the surfaces this pass actually checked (source registries,
all 3 generated-bundle instances, the 4 orphan objects' specific GCS cell). The prospectus-generator fourth instance
below is untouched (out of scope — DRIFT-specific, unrelated to this GMX pass).

> **CORRECTION (same session, immediately after posting the above):** the "zero remaining" claim did not extend to a
> live manifest-skeleton check — the operator directly asked "did you purge the manifest" and a follow-up targeted read
> of the defi `availability_index.parquet` found 4 DIFFERENT `venue=GMX` rows (dated today,
> `capture_status= expected_unattempted`, unrelated to the 4 orphan objects above), meaning some enumerator still treats
> GMX as a valid venue. Filed as its own issue rather than folded in here since it's a genuinely different, unresolved
> root cause (a catalogue-level artifact, not the generated-bundle/source-registry class this doc tracks):
> `/plans/archive/issues/defi_gmx_expected_skeleton_rows_still_enumerated_2026_08_04.md`.

## Todos

- [ ] [SCRIPT] P2. **Run `generate_strategy_prospectus.py` against current `unified-api-contracts` HEAD, review the diff
      (expected large: many unrelated-axis differences plus 2 wholly missing archetypes, `CARRY_FUNDING_DISPERSION` and
      `TSMOM_BTC_CTA`), confirm the 2 missing archetypes land correctly and nothing else looks structurally wrong (a
      `[MACHINE-DERIVED]`/`[CODEX-DERIVED]` header on every file, no truncated sections), then commit all 57 (or 59,
      with the 2 new ones) regenerated files as one `unified-api-contracts` change.** **CORRECTED 2026-08-12
      (/plan-reconcile)**: moved the actionable instruction to this todo's first physical line (was buried after ~250
      words of history/justification, per task_template.md's ao-readiness convention) — no change to scope or intent.
      **RECLASSIFIED 2026-08-08 — "source wins, full regen is correct" is the ruling, not an open design question.**
      Original text (kept for context): "Resync the fourth instance (`unified-api-contracts/openapi/prospectus/*.md`, 57
      files) — the prospectus generator (`unified-trading-pm/scripts/openapi/generate_strategy_prospectus.py`) has
      drifted from the committed files on multiple unrelated axes (venue-category classification, execution-algorithm
      lists, formatting, `generated_from_commit` baseline, 2 missing archetypes), so a blind regen isn't safe yet."
      Re-verified 2026-08-08: the generator is a PURE regenerate-from-source tool by construction — its own docstring
      states "Output: deterministic (sorted, no timestamps). Run twice = byte-identical," and the only file write in the
      whole script is a single unconditional `with open(out_path, "w", encoding="utf-8") as f: f.write(doc)` inside the
      per-archetype loop (line 663) — no read-existing-file, no diff-against-committed, no merge, no preserve-hand-edit
      logic anywhere in the file. This means there is no mechanism by which a committed `.md` could carry authoritative
      content the generator doesn't already derive from source — any divergence is drift, not intentional hand-authored
      content the generator would destroy. Confirmed by git history in `unified-api-contracts`: commits `f8d266ab`
      (2026-07-30, "correct stale gap#3 notes on ARBITRAGE_PRICE_DISPERSION") and `f8515eb7` (2026-07-30, "correct stale
      gap#10 notes on CARRY_BASIS_DATED CME cell") both land the same fix simultaneously in
      `internal/architecture_v2/archetype_capability_manifest.json` (the source registry) AND
      `openapi/prospectus/<archetype>.md` (the generated artifact this todo covers) AND
      `openapi/capability-manifest.json`/`openapi/capability-unlock-report.json` in one commit each — i.e. the
      established, repeated workflow for fixing this content is "edit the source registry, propagate everywhere," never
      "hand-edit the prospectus `.md` independently." The source registry is authoritative by construction. **Remaining
      work is now purely mechanical**: run `generate_strategy_prospectus.py` against current `unified-api-contracts`
      HEAD, review the diff — expected to be large (the doc's own dry-run above found many unrelated-axis differences
      plus 2 wholly missing archetypes, `CARRY_FUNDING_DISPERSION` and `TSMOM_BTC_CTA`) — confirm the 2 missing
      archetypes land correctly and nothing else looks structurally wrong (e.g. a `[MACHINE-DERIVED]`/`[CODEX-DERIVED]`
      header on every file, no truncated sections), then commit all 57 (or 59, with the 2 new ones) regenerated files as
      one `unified-api-contracts` change.

## Progress Log addendum

- **na-eligibility-audit 2026-08-03**: KEEP-NA valid — re-confirmed, and independently cross-confirmed by
  `defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s own Phase-1 classification (its Deferred/non-batchable list):
  "regenerating/reconciling the 57 `unified-api-contracts/openapi/prospectus/*.md` generator outputs spans many axes
  unrelated to DRIFT removal — needs a human design decision on how to reconcile generator vs committed copies before
  any worker todo is determinable." No stale/reclassify-eligible content found. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-03**: refreshed context_scope (4 entries) — instances 1-3 are now resolved, so retargeted the
  list at the sole remaining open item (the 4th instance, the drifted `openapi/prospectus/*.md` generator), replacing
  the stale first-instance-era entries.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **na-eligibility-audit 2026-08-06** (tranche=defi, dispatch agt-e00d37): KEEP-NA valid — one of the best-evidenced
  KEEP-NA cases in the corpus: prior audit passes (07-30/08-03/08-04) plus independent Deferred/non-batchable
  classifications in 3 separate AO-dispatch-batch plans (batch2, batch3, batch6) all carve out the sole open item
  (4th-instance `openapi/prospectus/*.md` generator resync) as human-design-gated, never dispatched. Independently
  re-verified live today: grepped `unified-api-contracts` directly, confirmed the identical 5-file DRIFT list the doc
  names is still affected, generator script unchanged since 2026-06-11. "Edited since" trigger was a metadata-only touch
  (author-field backfill + context-scout refresh). Incidental, not actioned: 1 untracked prose-only item (build
  deployment-ui's own capability-manifest generator) — likely moot-by-precedent given the surgical-prune workaround now
  proven twice (DRIFT 07-21, GMX 08-04). Doc stays `assigned_vm: NA`.
- **2026-08-08**: prior audits treated "which side is authoritative" as an open human design call. Re-read of the
  generator itself (`generate_strategy_prospectus.py`) shows it's a pure regenerate-from-source tool with no
  read-existing/merge/preserve logic — nothing for a hand-edit to have authoritatively diverged INTO — and
  `unified-api-contracts` history (`f8d266ab`, `f8515eb7`, both 2026-07-30) shows the established fix pattern already is
  "edit the source registry, the downstream `.md`/`.json` regenerate/get hand-propagated together," never the reverse.
  Ruled: source wins, full regen is correct — no design decision actually remains, just running the tool and reviewing
  the (expected-large) diff. Reclassified the sole open todo `[ENGINEER]` -> `[SCRIPT]` P2. Flipped `assigned_vm: NA` ->
  `assigned_vm: planning` — this was the doc's only open todo. Also considered retagging `asset_group` from `[defi]` to
  `[cross-cutting]` (the prospectus genuinely spans CEFI/DEFI/TRADFI/SPORTS/PREDICTION) — **decided against it**,
  leaving `asset_group: [defi]` as-is. Reasons: (1) `check_ag_closeout_linkage.py`'s own docstring states a
  multi-value/`cross-cutting`-tagged doc is "EXEMPT by construction" from the AG-closeout-linkage check — retagging
  would silently drop this doc out of the mechanism that keeps a doc from becoming an orphan nothing tracks, right as
  it's being flipped to AO-dispatched. (2) Unlike `phantom_captures_tradfi_2026_06_28.md` (retagged `[cross-cutting]` ->
  `[tradfi]` 2026-08-07 because its content was "100% tradfi-specific"), this doc is majority DEFI content by volume
  (created for a DEFI DRIFT/PACIFICA cull; 4 of its 5 documented "instances" are DEFI-repo fixes already shipped) with
  only the sole _remaining_ todo being genuinely cross-cutting-scoped — not a clean "the whole doc is mistagged" case.
  (3) This doc has an established `na-eligibility-audit`/`context-scout` tracking history under the `defi` tranche (7+
  prior passes above) that a mid-stream retag would fragment. Flagging the mistag here for a dedicated retag pass
  instead, per the task's own fallback: a worker picking up the reclassified todo should register the completed
  `unified-api-contracts` commit under BOTH this doc and whichever cross-cutting tracking surface exists, rather than
  this doc's tag being silently wrong in the meantime.

- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (4 entries), still accurate.
