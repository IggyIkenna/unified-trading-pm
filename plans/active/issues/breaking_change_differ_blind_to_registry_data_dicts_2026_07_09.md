---
doc_type: issue
title:
  Breaking-change differ is blind to UAC registry data-dicts (INSTRUMENT_TYPES_BY_VENUE et al.) — a consumer-breaking
  value edit promotes LDR→main with NO cross-repo gate
summary: |
  A UAC change (`unified-api-contracts@23fa3a99`) that removed "SPOT_PAIR" from the set-values of the "OKX"/"BYBIT"
  keys in the `INSTRUMENT_TYPES_BY_VENUE` dict broke instruments-service's `build_expected('cefi')` (75→71 tuples,
  real OKX-SPOT captures made invisible) — yet reached `main` with zero cross-repo gate examining it. Root cause:
  `detect_breaking_change.py` classifies the edit **non-breaking** (proven: `is_breaking: false`, export count
  1153→1153) because it only diffs public exports / Enum members+values / exported-name type-annotations / HTTP
  routes — NOT the literal contents of a plain module-level dict. Under `ldr_main` the cross-repo SIT gate fires
  ONLY on a differ-detected breaking change, so it never triggered; the promote drained on UAC's own per-repo QG
  (green — the change is internally valid to UAC). Backstop also failed: the always-on nightly SIT ran green due to
  a coverage gap (no test re-derives IS's expected-universe from the live UAC registry). The break sat latent ~22.5h
  and was caught only by a human running local `quality-gates.sh` on IS.
status: open
nature: notes
asset_group: [cefi]
stage: [meta]
repos: [unified-trading-pm, system-integration-tests, unified-api-contracts, instruments-service]
scope: [engineer, admin]
tags:
  [
    ci-cd,
    breaking-change-detection,
    contract-surface,
    registry,
    cross-repo-gate,
    sit,
    quality-gates,
    false-negative,
    ship-blocker-class,
  ]
related:
  [
    plans/active/issues/instruments_service_cefi_qg_red_on_ldr_head_2026_07_08.md,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/06-coding-standards/integration-testing-layers.md,
  ]
created: 2026-07-09
parent_epic: infrastructure_master
priority: P1
source:
  interactive session 2026-07-09 — CI-gate false-negative analysis of the
  instruments_service_cefi_qg_red_on_ldr_head_2026_07_08 incident
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-09
---

# Breaking-change differ is blind to UAC registry data-dicts — cross-repo break promotes with no gate

## What happened (incident, 2026-07-07 → 07-08)

A production-verified UAC fix silently broke a downstream consumer and reached `main` with **no cross-repo CI gate
examining it**. It was caught ~22.5h later by a human running local quality gates, not by CI. Full downstream-symptom
analysis + the interim revert are tracked in the companion doc
`instruments_service_cefi_qg_red_on_ldr_head_2026_07_08.md`; **this doc is about the CI-gate false-negative that let it
through**, which is the reusable root cause.

Timeline (UTC; IST = +5:30):

| When (UTC)                | Event                                                                                                                                                                                                               |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 07-07 15:25               | `unified-api-contracts@23fa3a99` (slot-3) removes `"SPOT_PAIR"` from the `"OKX"` and `"BYBIT"` set-values of `INSTRUMENT_TYPES_BY_VENUE`. Quickmerged to UAC LDR.                                                   |
| 07-07 15:37               | UAC LDR→main promote PR runs **UAC's own `quality-gates-v2` → green** (change is internally valid to UAC).                                                                                                          |
| 07-07 ~15:37              | `detect_breaking_change.py` verdict = **non-breaking** → the `ldr_main` cross-repo SIT gate **never fires**. Content promotes to UAC `main`, back-merges into IS LDR (HEAD `be95c76`).                              |
| 07-07 16:35               | Nightly/dispatch `full-workspace-sit` runs **green** (coverage gap; also does not gate promotes).                                                                                                                   |
| 07-07 15:25 → 07-08 14:00 | **~22.5h latent break.** IS `build_expected('cefi')` = 71 (was 75), OKX-SPOT invisible, 3 IS tests red. IS's `quality-gates-v2` runs **0 times** (no IS promote). Nightly SIT (07-08 04:02) green. **No CI catch.** |
| 07-08 (day)               | **Human catch** — slot-7 runs local `bash scripts/quality-gates.sh` on IS while shipping unrelated understat work, hits the 3 red tests, files the companion issue doc.                                             |
| 07-08 14:00               | Interim fix: revert `unified-api-contracts@1771d59a` (restores `SPOT_PAIR`) + `instruments-service@666bca5` (green sentinel). Shipping unblocked.                                                                   |

## Root cause — a two-layer miss (Layer 1 is the reusable defect)

### Layer 1 — the breaking-change differ does not treat registry data-dicts as contract surface (PRIMARY)

`unified-trading-pm/scripts/cicd/detect_breaking_change.py` is the SSOT trigger for the cross-repo SIT gate. Per its own
docstring it flags a change breaking **only** if:

- a public exported name (`__all__` / public top-level def/class) was removed/renamed;
- an exported name's **type annotation** changed;
- an **Enum member or member VALUE** was removed/changed;
- an HTTP route was removed.

The three registry constants that downstream consumers actually treat as contract are plain annotated dicts:

- `unified_api_contracts/registry/venue_constants.py:365` — `INSTRUMENT_TYPES_BY_VENUE: dict[str, set[str]]`
- `unified_api_contracts/registry/market_data_categories.py:226` — `VENUES_BY_ASSET_GROUP: dict[str, list[str]]`
- `unified_api_contracts/registry/market_data_categories.py:1055` —
  `VENUE_DATA_TYPE_CAPABILITIES: dict[str, dict[str, str]]`

`23fa3a99` removed two set-members (`"SPOT_PAIR"`) from inside `INSTRUMENT_TYPES_BY_VENUE`. The name stayed exported and
the annotation stayed `dict[str, set[str]]`, so **the AST differ sees no change to its tracked surface.** Proven
empirically:

```
$ .venv/bin/python scripts/cicd/detect_breaking_change.py \
    --source-dir unified_api_contracts --base-ref 23fa3a99^ --head-ref 23fa3a99 --json
{ "is_breaking": false, "reasons": [], "old_export_count": 1153, "new_export_count": 1153 }
```

But a **key or collection-member removal from these dicts IS a contract change** — downstream code enumerates them:
`build_expected(asset_group)` iterates `VENUES_BY_ASSET_GROUP` and reads `VENUE_DATA_TYPE_CAPABILITIES` /
`INSTRUMENT_TYPES_BY_VENUE` to materialise the expected universe; instruments-service's `_CEFI_VENUE_FOLD` folds
manifest venues into those expected tuples. Removing `(OKX, SPOT_PAIR)` deletes an expected tuple that real captured
data still folds onto → the data becomes invisible to Layer-1/Layer-2 coverage. That is precisely the class of break the
cross-repo gate exists to stop, and it is invisible to an export-only differ.

The CI/CD flow doc already acknowledges an **adjacent** escaped class — manifest `schema_version` is "a real contract
change but does NOT trip the breaking differ" (`/codex/08-workflows/ci-cd-flow.md`, breaking-differ section). Registry
data-dicts are the same category: data-carrying contracts the AST differ cannot see. The principle generalises to **any
data registry — Python dict/set/list constants OR YAML/JSON registry files** — whose contents are a cross-repo contract.

### Layer 2 — even if the gate had fired, SIT would have passed (coverage gap, backstop)

`full-workspace-sit`'s cross-repo tests do not exercise the broken invariant:

- `system-integration-tests/tests/unit/test_registry_alignment.py` checks only `InstrumentType` **enum membership**
  (`SPOT_PAIR` still exists as an enum member → green). It never checks per-venue
  `INSTRUMENT_TYPES_BY_VENUE`/`VENUE_DATA_TYPE_CAPABILITIES`/`VENUES_BY_ASSET_GROUP` consistency.
- The one test touching this exact area — `test_venue_to_tardis_matches_inverted_venue_mapping` — is
  `@pytest.mark.xfail(strict=False)` whose reason describes the very `okex → OKX-SPOT` split inconsistency. Non-strict
  xfail = green regardless. The venue-split area was already a **known, deliberately-tolerated blind spot.**
- `tests/integration/test_instrument_alignment.py` uses a **mock instrument generator**, not IS's real
  `build_expected('cefi')`, so it cannot see expected-universe drift or the fold mismatch.

## Why it matters

There is **no 25-repo-wide QG on CI and no consumer-fanout on a provider promote.** The only cross-repo gate (SIT) is
breaking-gated, so a provider (UAC) can promote a consumer-breaking registry edit to `main` with only its own per-repo
QG having looked at it. The break is then invisible until the consumer independently ships and re-runs its own QG
against the new provider — hours/days later, or (as here) not at all until a human intervenes. This is exactly the
cross-repo data-correctness class that `/codex/02-data/data-pipeline-correctness-hard-rule.md` says must freeze shipping
— but the gate that should enforce it never ran.

## Recommended fix

Close Layer 1 (make the gate fire) AND Layer 2 (give it teeth when it does):

1. **Extend the differ to treat designated registry data-constants as contract surface** — diff the literal
   keys/collection-members of an allowlisted set of module-level registry constants; flag a **removed key or removed
   set/list member** (and, for `VENUE_DATA_TYPE_CAPABILITIES`, a removed inner data_type) as breaking. Start with
   `INSTRUMENT_TYPES_BY_VENUE`, `VENUES_BY_ASSET_GROUP`, `VENUE_DATA_TYPE_CAPABILITIES`; make the allowlist maintainable
   (a `# @contract-surface` marker on the constant, or a small registry in the differ). Additive changes (new
   key/member) stay non-breaking, matching the existing "new Enum member is additive" rule.
2. **Close the SIT coverage gap** so the gate has teeth — add a cross-repo invariant that imports the **live** UAC
   registry and (a) runs IS's real `build_expected('cefi')`, (b) asserts every `VENUE_DATA_TYPE_CAPABILITIES` entry
   resolves to a venue declared in `VENUES_BY_ASSET_GROUP`, and (c) asserts every IS `_CEFI_VENUE_FOLD` target exists in
   the expected universe. Resolve (don't tolerate) the `strict=False` xfail on
   `test_venue_to_tardis_matches_inverted_venue_mapping`.
3. **Decide the provider-promote policy** — whether a differ-flagged registry change should additionally fan out and run
   key consumers' suites (at minimum instruments-service) against the candidate UAC before LDR→main merges. Broader than
   (1)+(2); may be deferred if (1)+(2) are judged sufficient.

## Todos

- [ ] [DESIGN] P1. Specify the contract-surface extension to `detect_breaking_change.py`: the allowlist mechanism
      (marker vs. registry), which mutations are breaking (key removal, set/list member removal, capability-inner-key
      removal) vs. additive-OK, and how it composes with the existing export/enum/route surface. Cite the manifest
      `schema_version` precedent. (repo: unified-trading-pm)
- [ ] [FIX] P1. Implement the extension in `scripts/cicd/detect_breaking_change.py` + tag the three registry constants
      as contract surface in `unified-api-contracts`. Additive stays non-breaking. (repos: unified-trading-pm,
      unified-api-contracts)
- [ ] [TEST] P1. Add cases to `unified-trading-pm/.../tests/unit/test_detect_breaking_change.py`: (a) removing a
      set-member from a tagged dict → breaking; (b) adding one → non-breaking; (c) regression fixture = the exact
      `23fa3a99` shape (`(OKX, SPOT_PAIR)` removal) → must now report `is_breaking: true`. (repo: unified-trading-pm)
- [ ] [FIX] P1. Close the SIT coverage gap: add the `build_expected('cefi')` + capability/fold cross-repo invariant to
      `system-integration-tests` and resolve the `strict=False` xfail on
      `test_venue_to_tardis_matches_inverted_venue_mapping`. (repo: system-integration-tests)
- [ ] [DESIGN] P2. Decide whether provider (UAC) registry-change promotes should fan out consumer QG (≥ IS) as a gate;
      spec it or explicitly defer with rationale. (repo: unified-trading-pm)
- [ ] [DOCS] P2. Once landed, update the breaking-differ section of `/codex/08-workflows/ci-cd-flow.md` to document
      registry-data-constant tracking (remove the implicit "only exports/enums/routes/annotations" mental model). (repo:
      unified-trading-pm)
- [ ] [VERIFY] P1. Reproduce end-to-end: differ on `23fa3a99` returns `is_breaking: true` post-fix; the new SIT
      invariant goes RED when `(OKX, SPOT_PAIR)` is removed. "Run it, don't read it." (repos: unified-trading-pm,
      system-integration-tests)

## Cross-reference

Downstream symptom + interim Option-B revert (and the still-open Option-A DESIGN decision on OKX-SPOT venue declaration)
live in `instruments_service_cefi_qg_red_on_ldr_head_2026_07_08.md`. That doc = "IS is red, unblock shipping"; **this
doc = "the CI gate that should have stopped it didn't, and here's the reusable fix."** Resolve the CI-gate fix here.
