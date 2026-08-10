---
doc_type: plan
title:
  "Remove the Kaiko provider scaffold fleet-wide (operator ruling 2026-08-10: Kaiko is banned outright, not
  execution-only) — 7 files across MTDS, UAC and PM, plus close the credential ask"
summary: >-
  On 2026-08-09 a session scaffolded a NEW Kaiko on-chain-analytics adapter in market-tick-data-service
  (`adapters/onchain/kaiko.py` + test + `PLANNED_VENUES` entry + a UAC `SourceCapability`) and filed
  `glassnode_kaiko_credential_ask_2026_08_09.md` asking the operator to provision `kaiko-api-key`. CLAUDE.md's
  removed-providers line already names Kaiko as "do NOT reference", but that line sits under the "Working on DeFi
  EXECUTION?" heading, so the scaffolding session could read it as execution-scoped and not applicable to MTDS
  analytics. Raised to the operator 2026-08-10, who ruled the ban is **workspace-wide, not execution-only**: the ask is
  stale, and the scaffold is deleted per the no-shims rule rather than left parked. This plan removes every live
  reference (7 files, ~70 occurrences) in one change per the entity-rename/split consumer-migration rule, and closes the
  Kaiko half of the credential ask while preserving the Glassnode half, which is unaffected.
status: complete
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags: [kaiko, removed-provider, adapter-removal, credential-ask, no-shims, operator-ruling]
related:
  [
    /plans/active/issues/glassnode_kaiko_credential_ask_2026_08_09.md,
    /plans/archive/2026_08/kaiko_provider_removal_2026_08_10_finalize.md,
    /codex/02-data/external-data-always-available-rule.md,
    /codex/04-architecture/defi-execution-overview.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
effort: medium
drift_direction: none
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/glassnode_kaiko_credential_ask_2026_08_09.md,
    /codex/02-data/entity-rename-and-split-consumer-migration-rule.md,
    /codex/04-architecture/defi-execution-overview.md,
  ]
source: >-
  Operator ruling 2026-08-10 (interactive session, slot 1), in answer to a flagged SSOT ambiguity: CLAUDE.md bans Kaiko
  but under a DeFi-EXECUTION-scoped heading, while the 2026-08-09 ask scaffolds it for MTDS analytics. Operator ruled
  the ban is outright. Consumer set enumerated live in the same session via `rg -il kaiko` across all repos excluding
  `.venv`/`build`/archives.
---

# Remove the Kaiko provider scaffold fleet-wide

> **🟢 ARCHIVED 2026-08-10.** All 4 todos done and verified on origin: the UAC `SourceCapability` + `KAIKO_BASE_URL`
> removal (`unified-api-contracts@c48238266b`, QG ALL PASSED 655s), the MTDS adapter/test/ `PLANNED_VENUES` deletion
> (`market-tick-data-service@da86db197e`, QG ALL PASSED 1177s), the `_RETRY_SAFE_DEFAULT_BASELINE` 3→2 ratchet and the
> CLAUDE.md ban relocation (`unified-trading-pm@026ed5ab52`). The durable rule this plan established — **the
> removed-vendor ban is FLEET-WIDE, not DeFi-execution-only** — lives in
> `/codex/04-architecture/defi-execution-overview.md` § "Removed vendors" and in `cursor-configs/CLAUDE.md`'s always-on
> coding-standards section, NOT here; this plan is provenance only. Verification is recorded in
> [[kaiko_provider_removal_2026_08_10_finalize]].

## The ambiguity that caused this, and why it is worth fixing at the source

`cursor-configs/CLAUDE.md` lists Kaiko among removed providers — but inside the conditional bullet **"Working on DeFi
EXECUTION?"**. A worker scaffolding an on-chain **analytics** adapter in MTDS is not "working on DeFi execution", so the
ban did not obviously apply, and the scaffold was written in good faith. The operator ruled 2026-08-10 that the ban is
workspace-wide. Todo 4 below fixes the wording so the next worker cannot make the same correct-looking mistake.

## Enumerated consumer set (verified live 2026-08-10, `rg -ci kaiko`)

| File                                                                         | Refs | Disposition                                                     |
| ---------------------------------------------------------------------------- | ---: | --------------------------------------------------------------- |
| `market-tick-data-service/.../market_interface/adapters/onchain/kaiko.py`    |   28 | DELETE the file                                                 |
| `market-tick-data-service/tests/unit/test_kaiko_adapter.py`                  |   24 | DELETE the file                                                 |
| `market-tick-data-service/.../market_interface/adapters/onchain/__init__.py` |    4 | remove the export                                               |
| `market-tick-data-service/.../market_interface/factory.py`                   |    1 | remove `"kaiko": "analytics"` from `PLANNED_VENUES` (line ~213) |
| `unified-api-contracts/.../capability_declarations/_altdata.py`              |    8 | remove `KAIKO_BASE_URL` + the `_KAIKO` `SourceCapability`       |
| `unified-api-contracts/.../capability_declarations/__init__.py`              |    2 | remove the re-export                                            |
| `unified-trading-pm/scripts/quality-gates-base/base-service.sh`              |    3 | update the QG carve-out comment that names `kaiko.py`           |

**Not in scope**: `unified-trading-system-ui/docs/reference/*` and `public/presentations/*` mention Kaiko as a market
data vendor in narrative/marketing copy, not as a code dependency. Check each before touching — if it is describing the
vendor landscape rather than claiming we integrate Kaiko, leave it. Only fix copy that asserts an integration we do not
have.

## Todos

- [x] ✅ [DATA] P2. **DONE 2026-08-10 — `unified-api-contracts@c48238266b`** (QG ALL PASSED 655s, post-push ancestry
      verified on LDR; `rg -ci kaiko` across the repo = 0). **Remove Kaiko from `unified-api-contracts` first**
      (dependency order: UAC is T2, MTDS depends on it). Delete `KAIKO_BASE_URL` and the `_KAIKO` `SourceCapability`
      from `unified_api_contracts/registry/capability_declarations/_altdata.py` and its re-export from that package's
      `__init__.py`. **Done when**: `rg -ci kaiko` returns 0 across `unified-api-contracts/` (excluding `.venv`), and
      `bash scripts/quality-gates.sh` is green in that repo. Ship via quickmerge.
- [x] ✅ [DATA] P2. **DONE 2026-08-10 — `market-tick-data-service@da86db197e`** (QG ALL PASSED 1177s, sentinel
      36df62e78; post-push ancestry verified on LDR). Deletions confirmed to have actually LANDED on origin —
      `git cat-file -e FETCH_HEAD:...kaiko.py` and the test both absent, `PLANNED_VENUES` kaiko count 0 — rather than
      trusting the ship report, because the same session proved a ship script can land a create-only commit. **Remove
      the MTDS adapter and its wiring.** Delete `market_tick_data_service/market_interface/adapters/onchain/kaiko.py`
      and `tests/unit/test_kaiko_adapter.py` outright (no shim, no deprecation stub — CLAUDE.md's delete-deprecated-code
      rule), remove the export from `adapters/onchain/__init__.py`, and remove the `"kaiko": "analytics"` entry from
      `market_interface/factory.py`'s `PLANNED_VENUES`. Kaiko was parked in `PLANNED_VENUES` and never wired into
      `get_adapter()`, so no runtime resolution path changes — state that explicitly in the commit. **Done when**:
      `rg -ci kaiko` returns 0 across `market-tick-data-service/` (excluding `.venv`), and
      `bash scripts/quality-gates.sh` is green. Ship via quickmerge.
- [x] ✅ [DATA] P3. **DONE 2026-08-10 — `unified-trading-pm@026ed5ab52`.** Dropped `kaiko` from the
      `onchain/{glassnode,helius_solana,kaiko}.py` carve-out prose AND lowered `_RETRY_SAFE_DEFAULT_BASELINE` 3 → 2,
      since the 3 existed solely for `kaiko.py` and baselines only ever go DOWN — leaving it would bake in a permanent
      slack whitelist slot. Rule 11(a) blast-radius proof done FIRST: the `_RSD_PATTERN` has exactly 2 CODE sites
      fleet-wide, both MTDS (`glassnode.py:238`, `helius_solana.py:261`); every other repo has 0, so baseline 2 cannot
      fail any repo. **Update the PM QG carve-out comment.** `scripts/quality-gates-base/base-service.sh` (~line 3877)
      documents a 2026-08-09 carve-out naming `onchain/{glassnode,helius_solana,kaiko}.py`. Drop `kaiko` from that list
      and from the surrounding prose so the comment does not describe a file that no longer exists. Do NOT weaken the
      carve-out for the two remaining adapters. **Done when**: the comment names only the surviving adapters and PM QG
      is green. `scripts/**` reaches main via the D16 carve-out, not quickmerge.
- [x] ✅ [DOCS] P2. **DONE 2026-08-10 — `unified-trading-pm@026ed5ab52`.** The removed-vendor ban moved out of the
      conditional "Working on DeFi EXECUTION?" bullet into the **always-on** coding-standards section, worded
      fleet-wide. Size budget honoured throughout: a concurrent peer edit pushed the file 113 B OVER the 40,960 B hard
      cap mid-session; condensed (and reclaimed the now-redundant DeFi-bullet pointer) to land at 40,936 B rather than
      raising the cap. The rationale + the generalisable lesson went to
      `/codex/04-architecture/defi-execution-overview.md` § "Removed vendors", not into CLAUDE.md — SSOT direction.
      **Fix the CLAUDE.md ambiguity that caused this.** The removed-providers list lives under the "Working on DeFi
      EXECUTION?" conditional bullet, which made a workspace-wide ban look execution-scoped. Move or restate it so the
      ban reads as fleet-wide regardless of the touching subsystem, honouring the file's ≤40 KB budget
      (`check_agent_rules_size_cap.py`) — condense elsewhere rather than growing the file, and never raise the cap.
      **Done when**: a worker reading only the always-on section would know not to scaffold a Kaiko adapter, and the
      size cap still passes.

## Codex SSOTs

- `/codex/02-data/entity-rename-and-split-consumer-migration-rule.md` — why every consumer migrates in ONE change
- `/codex/04-architecture/defi-execution-overview.md` — the removed-providers list this ruling widens
- `/codex/02-data/external-data-always-available-rule.md` — why the Glassnode half stays a live credential ask

## Progress Log

- **2026-08-10** — Authored after flagging the CLAUDE.md scope ambiguity to the operator, who ruled Kaiko banned
  outright. Consumer set enumerated live (7 files, ~70 refs). Confirmed Kaiko sits in `PLANNED_VENUES` only and is not
  reachable through `get_adapter()`, so removal carries no runtime behaviour change.

- **2026-08-10 — AO backlog VERIFIED live (not inferred).** Queried the running orchestrator read-only via SSM
  (`check-ao-backlog-status.sh <filter>`; TOTAL_TASKS=3154). All four plans authored/fixed this session are ingested:
  `meta_plan_corpus_hygiene_ao_dispatch_batch1` **22** tasks, `deployment_api_unauthenticated_prod_p0` **9** (one
  already `status=dispatched dispatched_to=9` — a worker is on the unauthenticated-prod P0), `kaiko_provider_removal`
  **6**, `ao_satellite_ao_dispatch_batch19` **5**. batch19 contributing at all is the proof its dispatch-enablement fix
  was needed: at the `assigned_vm: NA` + `execution_scope: local-only` it was authored with, it would have contributed
  zero and the operator's approval would have been silently inert. **Method note for the next agent**: an unfiltered run
  truncates its listing, so absence there is a DISPLAY artifact, not evidence — always re-query with the plan-name
  filter (`$1`) before concluding a plan is missing, and never run it with `2>/dev/null` (a wrong cwd fails silently and
  looks identical to "no matching tasks").

## FINAL REPORT (rule 9) — 2026-08-10 autonomous close-out

**All 4 todos done and shipped.** `unified-api-contracts@c48238266b` → `market-tick-data-service@da86db197e` (UAC first,
dependency order) → `unified-trading-pm@026ed5ab52` (QG carve-out + CLAUDE.md + codex). Zero live Kaiko integration
references remain workspace-wide; the two surviving `.ts` hits name Kaiko as a market COMPETITOR in investor-relations
copy, which this plan's scope note explicitly excludes.

### Forced tradeoffs decided under rule 1 (no operator asked)

1. **Lowered `_RETRY_SAFE_DEFAULT_BASELINE` 3 → 2** rather than leaving slack. The 3 existed solely for `kaiko.py`;
   baselines only ever go DOWN, so leaving it would have permanently widened a whitelist. Lowering it makes the gate
   STRICTER, so rule 11(a) required proving the whole fleet passes first — counted the pattern across every repo:
   exactly 2 code sites, both MTDS. Every other repo has 0.
2. **Condensed CLAUDE.md instead of raising its cap.** A concurrent peer edit pushed it 113 B over the 40,960 B hard cap
   mid-session. The size-budget rule says condense and migrate to codex, never raise — so the rule was tightened to 156
   B and its rationale moved to the codex SSOT. Final 40,936 B.
3. **Filed the `safe-doc-push` defect rather than fixing it inline** —
   `/plans/active/issues/safe_doc_push_isolation_drops_rename_deletions_2026_08_10.md`, P1, 5 todos. It touches a
   fleet-wide ship script every repo and agent depends on; under rule 11 that wants its own regression test and
   blast-radius check, not a patch buried in a docs close-out. This is the ONE thing consciously not completed here.

### Defects introduced by this session and caught before hand-off

- **Create-only archive commit.** `8ac88720e6` landed 17 adds and zero deletes, duplicating every archived doc at its
  old `plans/active/` path where the AO backlog still read it as open. Root cause: isolated-worktree mode syncs by
  COPYING named files, and a deleted file has nothing to copy. Recovered in `1653006e52` via `SDP_ISOLATED=0` after
  confirming all 17 pairs were byte-identical (no divergence). Caught only by diffing origin, not by any exit code.
- **The batch19 approval was inert.** `status: draft → active` was flipped as its source doc instructed, but the doc was
  authored `assigned_vm: NA` + `execution_scope: local-only` — both rejected by `_plan_contributes_briefs`. Corrected to
  match its peers; it now contributes 5 backlog tasks where it would have contributed 0.

### Standing lesson for the next agent

**A ship script's exit code is not evidence of what reached origin.** Three separate times this session a script
returned 0 (or a truncated log implied success) while landing nothing or landing a partial commit. Verify with
`git log`/`git ls-tree`/`git cat-file` against `FETCH_HEAD` every time, and never pipe a ship script through `tail`.

### Verified end-state

| Surface                          | Result                                                                               |
| -------------------------------- | ------------------------------------------------------------------------------------ |
| ag-closeout parked corpus        | 28 → 10 docs · 62 → 17 open todos · 18 → 0 `[OPERATOR]` · 0 duplicates               |
| PM commits on origin             | 9                                                                                    |
| Code shipped                     | UAC `c48238266b`, MTDS `da86db197e` — both QG-green, ancestry-verified               |
| AO backlog (live, SSM read-only) | batch1 **22** tasks · P0 **9** (one `dispatched_to=9`) · kaiko **6** · batch19 **5** |
| Operator residue                 | 6 genuine items + 6 design calls, consolidated onto ONE list, none left scattered    |
