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
related: [../../codex/04-architecture/solana-defi-coverage.md, ../../codex/06-coding-standards/ui-testing-layers.md]
created: 2026-07-16
parent_epic: defi_master
priority: P2
source:
  'Operator ruling 2026-07-16: "kill drift entirely from our whole system... kill all other solana perp dex''s. uac,
  code, adaptors, manifest, gcs, everything." Discovered as a side-finding while fixing the TreasuryTab
  SUB_ACCOUNT_DRIFT dropdown bug in deployment-ui (the 12th repo the operator''s fleet grep caught).'
assigned_vm: NA
resolved_by:
locked_by:
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
   `codex/06-coding-standards/script-homes.md`.
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

- 2026-07-16: Discovered during the deployment-ui DRIFT/PACIFICA venue sweep (TreasuryTab SUB_ACCOUNT_DRIFT dropdown fix
  session). TreasuryTab dropdown + mocks + specs fixed and shipped separately
  (`deployment-ui@<sha-filled-in-by-quickmerge>`); this capability-bundle finding filed as its own issue per the
  findings-triage HARD RULE (cross-repo, data-correctness-adjacent, too large to hand-fix in the same pass).

## Second instance — `unified-trading-system-ui/lib/registry/ui-reference-data.json` (coordinator, 2026-07-16)

Same class, different repo/file. Found by the fleet-wide closing grep AFTER two surgical enum fixes to this very file
had already shipped — a caution that "I fixed that file" != "that file is clean".

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

## Progress log
