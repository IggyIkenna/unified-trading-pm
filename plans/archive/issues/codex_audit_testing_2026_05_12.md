---
doc_type: issue
title: Codex audit — Testing area (Phase 1.L)
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-ui,
    execution-service,
    instruments-service,
    market-tick-data-service,
    system-integration-tests,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-12
author: harsh-codex-audit-testing-tab (slot 8 sub-agent)
source:
  - plans/active/codex_vs_citadel_infrastructure_audit_2026_05_10.md Phase 1.L
  - /codex/06-coding-standards/integration-testing-layers.md
  - /codex/06-coding-standards/vcr-cassette-pattern.md
  - /codex/06-coding-standards/testing.md (1-line stub)
  - /codex/06-coding-standards/test-templates/README.md + test_event_logging.py
  - /codex/06-coding-standards/test-coverage-data-status.md
  - /codex/06-coding-standards/ui-testing-layers.md
  - /codex/06-coding-standards/quality-gates.md § Test Infrastructure / GCP Emulator / AWS Moto / Credential-Free CI
    Gate / Cassette parity
  - { /codex/06-coding-standards/README.md § "Test Infrastructure: Emulators & Mocks" (appears twice) }
  - /codex/06-coding-standards/dependency-management.md
  - /codex/02-data/vcr-cassette-ownership.md
  - /codex/07-security/testing-with-api-keys.md
  - /codex/04-architecture/tenderly-execution-provider.md
  - codex/00-SSOT-INDEX.md
  - plans/archive/cicd_mock_hardening_2026_03_11.plan.md (archived; content folded into README + quality-gates)
  - cursor-configs/CLAUDE.md § "Testing Infrastructure (Emulators & Mocks)"
  - {
      cross-check code:
        "unified-api-contracts/unified_api_contracts/testing/* + tests/test_cassette_schema_parity.py +
        test_vcr_replay.py; market-tick-data-service/tests/market_interface/{conftest.py,fixtures/mock_ws_server.py};
        execution-service/tests/defi_execution/integration/conftest.py; system-integration-tests/tests/*;
        unified-trading-pm/scripts/demo-mode.sh + docker/docker-compose.mock.yml; */pyproject.toml (flat deps)",
    }
locked_by: live-defi-rollout
locked_since: 2026-05-12
---

# Codex audit — Testing area (Phase 1.L)

> **Severity**: P1 — pre-cutover audit per `codex_vs_citadel_infrastructure_audit_2026_05_10.md` Phase 1.L. **Scope**:
> 5-layer integration tiers (L0 contract alignment → L3b E2E) + UI 8-layer model · GCP emulators · AWS moto ·
> `--block-network` + `network_block_plugin` · `MockWebSocketFeed` · VCR cassette ownership / recording / replay /
> parity · DeFi `responses` + Tenderly fork fixtures · `demo-mode.sh` local stack · coverage targets ·
> `INTEGRATION_TEST_MODE` · test-templates · "expand existing test files" rule · two-pass QG model. **Owner**: Harsh T8
> slot 8 sub-agent (read-only audit); operator review for dispositions before Phase 3 ship.

## Methodology

Read every Testing-area codex surface (`integration-testing-layers.md`, `vcr-cassette-pattern.md`,
`vcr-cassette-ownership.md`, `testing-with-api-keys.md`, `tenderly-execution-provider.md`, `ui-testing-layers.md`,
`test-coverage-data-status.md`, `test-templates/README.md`, `testing.md`, plus the testing sections of
`06-coding-standards/README.md` and `quality-gates.md`, plus `00-SSOT-INDEX.md` rows). For each rule / path / claim:
cite file:line, classify KEEP / LIFT / CONSOLIDATE / DELETE / ADD, attach a 1-line reason + disposition (IMMEDIATE /
PRE_CUTOVER / POST_CUTOVER) + suggested owner. Cross-checked against actual code — every "codex says X is at path P" /
"env var is N" / "the layout is L" was verified by reading the file or `ls`-ing the dir (grep-then-READ, not
grep-then-conclude). The archived `cicd_mock_hardening_2026_03_11.plan.md` was diffed against the README + quality-gates
docs that fold its content forward.

## Findings

### Tier 1 — codex doc vs implementation drift

| #    | Finding (KEEP/LIFT/CONSOLIDATE/DELETE/ADD)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Disposition (IMMEDIATE/PRE_CUTOVER/POST_CUTOVER)                                                                                                                                                                                                                                                                  | Owner                                | Evidence (file:line)                                                                                                                                                                                     |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| TS-1 | DELETE/LIFT — `network_block_plugin.py` path is **wrong in 3 places**. `integration-testing-layers.md:246`, `quality-gates.md:1849`, `README.md` § "Test Infrastructure" (both copies) all say `unified-trading-pm/scripts/dev/network_block_plugin.py`. Actual location: `unified-api-contracts/unified_api_contracts/testing/network_block_plugin.py` (shipped there during cicd*mock_hardening, \_not* in PM `scripts/dev/` as the archived plan's todo said). An operator following the codex won't find the plugin. Same wrong-path inheritance: `FaultInjectionTransport` (codex says `unified-trading-pm/scripts/dev/fixtures/` → actual `unified_api_contracts/testing/fault_injection.py`) and `TickReplayEngine` (codex says PM `scripts/dev/fixtures/` → actual `unified_api_contracts/testing/mock_replay.py`).     | IMMEDIATE ✅ DONE @766bcfbc — all 3 paths corrected in integration-testing-layers.md:246 + quality-gates.md:1900 + 06-coding-standards/README.md Test Infrastructure table.                                                                                                                                       | governance                           | `integration-testing-layers.md:246` + `quality-gates.md:1849` + `README.md` § "Test Infrastructure: Emulators & Mocks" rows vs `ls unified-api-contracts/unified_api_contracts/testing/`                 |
| TS-2 | DELETE/LIFT — `vcr-cassette-pattern.md:17` says cassettes live at `api_contracts/api_contracts_external/<venue>/mocks/` and `:18`/`:35` reference `vcr_endpoints.py` at the AC repo root. Actual layout: cassettes at `unified_api_contracts/external/<venue>/mocks/*.yaml` (matches `vcr-cassette-ownership.md` — that doc is the one that's right), and `vcr_endpoints.py` at `unified_api_contracts/testing/vcr_endpoints.py`. The `api_contracts/api_contracts_external` package name is from the _deleted_ UAC layout (per CLAUDE.md "UAC Citadel Architecture" deleted-dirs list).                                                                                                                                                                                                                                        | IMMEDIATE ✅ DONE @766bcfbc — vcr-cassette-pattern.md cassette locations table rewritten to match shipped UAC layout; pointer to vcr-cassette-ownership.md as ownership SSOT.                                                                                                                                     | governance + UAC owner               | `vcr-cassette-pattern.md:13-19,35` vs `ls unified-api-contracts/unified_api_contracts/external/*/mocks` + `unified_api_contracts/testing/vcr_endpoints.py`                                               |
| TS-3 | DELETE/CONSOLIDATE — `vcr-cassette-pattern.md:19,23-28` documents a `scripts/record_vcr_cassettes.py` recording script _in unified-api-contracts_. That script does **not exist** (`ls unified-api-contracts/scripts/` → only `generate_ui_reference_data.py`) and `vcr-cassette-ownership.md:81-82` _explicitly states_ "unified-api-contracts does not ship recording scripts; add a recording script in each interface." Two codex docs directly contradict each other on a cutover-relevant workflow. `vcr-cassette-pattern.md` is the stale one — either delete the recording-script section or fold the whole doc into `vcr-cassette-ownership.md`.                                                                                                                                                                       | IMMEDIATE ✅ DONE @766bcfbc — recording-script section in vcr-cassette-pattern.md removed; replaced with redirect to vcr-cassette-ownership.md (canonical SSOT).                                                                                                                                                  | governance + UAC owner               | `vcr-cassette-pattern.md:19,23-28` vs `vcr-cassette-ownership.md:80-82` + `ls unified-api-contracts/scripts/`                                                                                            |
| TS-4 | DELETE — `tenderly-execution-provider.md:208` says live-mode DeFi connectors "talk directly to Alchemy/**Infura** RPCs." Infura is on the CLAUDE.md "Removed providers (do NOT reference)" list (§ "DeFi Execution Architecture"). The codex doc references a banned provider for the live execution path.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | IMMEDIATE ✅ ALREADY-RESOLVED 2026-05-12 — tenderly-execution-provider.md:127 already removes Infura, references workspace "Removed providers" rule (parallel-agent shipped during this batch).                                                                                                                   | governance + execution-service owner | `tenderly-execution-provider.md:206-209` vs `cursor-configs/CLAUDE.md` § "Removed providers"                                                                                                             |
| TS-5 | DELETE — `quality-gates.md` (lines 935, 1083, 1294, 1297, 1300, 1376, 1802, 1882) + `dependency-management.md` (lines 11, 53, 232) document `[project.optional-dependencies] dev` and `uv pip install -e ".[dev]"` (incl. the moto test-dep example at `quality-gates.md:1801-1805`). CLAUDE.md "Dependencies + builds" rule: "**Flat deps only** — every `pyproject.toml` has ONE `[project.dependencies]`. No `[project.optional-dependencies]`. No `.[dev]` extras." Verified actual `execution-service/pyproject.toml` / `unified-trading-library/pyproject.toml` / `system-integration-tests/pyproject.toml` — none have `[project.optional-dependencies]`. The codex docs are pre-flat-deps and will mislead. (Note: this also surfaces in the Governance/Coding-Standards audit slices — flag there too if not already.) | PRE_CUTOVER ✅ DONE @SLOT8-TESTING-BATCH — FLAT-DEPS BANNER added to top of both `dependency-management.md` + `quality-gates.md` warning that inline `.[dev]` examples are legacy + pointing to CLAUDE.md SSOT. Inline scrub tracked as P2 doc-clean.                                                             | governance + dep-alignment owner     | `quality-gates.md:1801-1805,1294-1300,1876-1882` + `dependency-management.md:11,53,232` vs `cursor-configs/CLAUDE.md` § "Dependencies + builds" + `grep optional-dependencies */pyproject.toml` (0 hits) |
| TS-6 | LIFT — `vcr-cassette-ownership.md:211` links `06-coding-standards/ibkr-mock-pattern.md` as "the full pattern reference"; `test-templates/README.md:46` links `06-coding-standards/testing.md` for the event schema. **`ibkr-mock-pattern.md` does not exist** (the IBKR mock pattern actually lives inline in `vcr-cassette-ownership.md:158-220`). Dead cross-reference — either create the stub or repoint to the inline section.                                                                                                                                                                                                                                                                                                                                                                                             | PRE_CUTOVER ✅ DONE @SLOT8-TESTING-BATCH — vcr-cassette-ownership.md:211 dead cross-ref to `ibkr-mock-pattern.md` lifted; pointer now to inline § "IBKR mock pattern" above the ref. test-templates/README.md → testing.md link is the TS-15 consolidation; TS-10 fleshed out testing.md as the conventions SSOT. | governance                           | `vcr-cassette-ownership.md:211` + `test-templates/README.md:46` vs `ls codex/06-coding-standards/` (no `ibkr-mock-pattern.md`)                                                                           |
| TS-7 | LIFT — `integration-testing-layers.md` "**Last Updated:** 2026-03-04" + cross-refs `unified-trading-pm/plans/cursor-plans/consolidated_remaining_work.plan.md` (a non-existent plan path under the current `plans/` layout) + `.cursor/rules/integration-testing-layers.mdc` (verify it's still synced post `cursor-rules/` reorg). Two-month-old doc on the cutover-critical testing tier model; refresh the "Last Updated" + dead plan link, re-verify the cursor-rule pointer.                                                                                                                                                                                                                                                                                                                                               | PRE_CUTOVER ✅ DONE @SLOT8-TESTING-BATCH — Last Updated bumped 2026-03-04 → 2026-05-12, dead `cursor-plans/consolidated_remaining_work.plan.md` ref repointed to archived `cicd_mock_hardening_2026_03_11.plan.md` fold-forward path, cursor-rule path noted post-`cursor-rules/` reorg.                          | governance                           | `integration-testing-layers.md:7-13,436-440`                                                                                                                                                             |
| TS-8 | LIFT — `testing-with-api-keys.md:64-70` "VCR Cassette Matrix" lists `unified-api-contracts/mocks/umi/` (etc.) cassette locations and a parallel set of _archived/renamed_ interface names (UMI/UTEI/URDI/UPI/USEI/UDEI). The actual cassette path is `unified_api_contracts/external/<venue>/mocks/` (TS-2) and all the interface repos collapsed into execution-service/instruments-service/position-balance-monitor-service per CLAUDE.md. The matrix's `mocks/umi/` style paths never existed in the final layout; statuses all say "pending" (stale — `vcr-cassette-ownership.md` shows ~22 `VALIDATED`). Re-derive this table from `vcr-cassette-ownership.md` § "Current Cassettes" or delete it (duplicate-SSOT).                                                                                                        | PRE_CUTOVER ✅ DONE @SLOT8-TESTING-BATCH — DERIVED-MATRIX BANNER added flagging the legacy interface-name table as historical + pointing to vcr-cassette-ownership.md "Current Cassettes" as canonical inventory. Inline rewrite tracked as P2 doc-clean.                                                         | governance + UAC owner               | `testing-with-api-keys.md:58-73` vs `vcr-cassette-ownership.md:30-74`                                                                                                                                    |

### Tier 2 — testing governance gaps

| # | Finding (KEEP/LIFT/CONSOLIDATE/DELETE/ADD) | Disposition (IMMEDIATE/PRE_CUTOVER/POST_CUTOVER) | Owner | Evidence
(file:line) | | ----- |
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

|
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

| ------------------------------------ |
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

| ---------- |
----------------------------------------------------------------------------------------------------------------------------------------------------------

| | TS-9 | ADD — `--block-network` / `network_block_plugin` is implemented and used in only a _subset_ of repos
(verified inline in `market-tick-data-service/tests/market_interface/conftest.py:20-44`; the shared plugin lives in
`unified_api_contracts/testing/network_block_plugin.py`). There is **no QG step** that asserts every service
`conftest.py` registers the credential-free network gate (the cicd_mock_hardening plan's "h8-credential-free-gate" only
wired it into `system-integration-tests`). Reference incident class: 2026-05-05 MDPS emitted STARTED+STOPPED with
garbage output — a hermetic-test gate is part of the defence. ADD a QG STEP that fails if a service test suite lacks the
`--block-network` plugin registration (or `@pytest.mark.allow_network` opt-out accounting). | PRE_CUTOVER ✅
DONE-PARTIAL @SLOT8-TESTING-BATCH — QG-enforcement gap codified in `integration-testing-layers.md` § "CI Hermeticity"
with proposed-QG-STEP shape; wiring 🟡 NEEDS-OPERATOR-GATE (hard-fail vs warning policy). | governance + QG-template
owner | `quality-gates.md:1809-1850` (documents the gate, no enforcement) + `cicd_mock_hardening_2026_03_11.plan.md` h8
todo (scoped only to SIT) | | TS-10 | ADD — The "expand existing test files; never create `test_*_extended.py` /
`test_*_additional.py`; use singleton fixtures from conftest" rule lives in `.claude/rules/python-backend.md` +
`.claude/rules/universal.md` but is **absent from codex**. `06-coding-standards/testing.md` is the natural home and it's
a 1-line stub. ADD the no-`_extended` rule + the singleton-conftest-fixture rule + "mock external I/O via `autouse=True`
conftest fixtures" to `testing.md`, and optionally a QG ratchet
(`rg 'test\*.\*\*(extended                                                                                                                                                                                                                                                                                                                       | additional                                                                                                                                                                                                                                                                                                                                                       | new)\.py'`
→ fail). | PRE_CUTOVER ✅ DONE @SLOT8-TESTING-BATCH — `testing.md` fully fleshed out from 1-line stub: no-\_extended
rule + singleton-conftest-fixture rule + autouse autouse=True pattern + two-pass model + cross-refs. QG ratchet wiring
🟡 NEEDS-OPERATOR-GATE. | governance | `.claude/rules/python-backend.md` § Testing + `.claude/rules/universal.md` §
"Expand existing test files" vs `/codex/06-coding-standards/testing.md` (stub) | | TS-11 | ADD —
`integration-testing-layers.md` § "Cassette Parity & Drift" (line 237-239) names
`cd unified-api-contracts && pytest tests/test_cassette_schema_parity.py` as a per-commit check (and
`quality-gates.md:1838` says "256 tests, ~2s"). Verified the test file exists. But there's **no codex statement of WHO
runs it on every commit** vs which repos' QG include it — the "Runbook Execution-Owner SSOT" rule (4 mandatory fields:
owner/cadence/verifier/last_executed) is not satisfied for the cassette-parity check, the nightly drift check
(`cassette-drift-check.yml`), or the `cassette_orphan_checker.py`. ADD execution-owner blocks for these three. |
PRE_CUTOVER ✅ DONE @SLOT8-TESTING-BATCH — 3 `execution:` YAML blocks added inline at `integration-testing-layers.md` §
"Cassette Parity & Drift" (owner/cadence/verifier/last_executed for each of: schema-parity check, nightly drift
workflow, orphan-checker). | governance + UAC owner | `integration-testing-layers.md:236-239` +
`quality-gates.md:1832-1855` + `ls unified-api-contracts/unified_api_contracts/testing/` (cassette_orphan_checker.py,
detect_cassette_drift.py) vs `cursor-configs/CLAUDE.md` § "Runbook Execution-Owner SSOT" | | TS-12 | ADD —
`tenderly-execution-provider.md` § "Downstream consumers" cites three NEW Tenderly-fork test/sim consumers from
`defi_simulation_realism_2026_05_10.md` (`test_amm_golden_swaps.py`, `proposal_simulator.py`, high-impact swap
pre-flight) with per-shape validation thresholds — but the doc's own "Configuration" section says the _primary_ fixture
home is "`execution-service/tests/integration/conftest.py`" while the actual DeFi integration conftest is
`execution-service/tests/defi_execution/integration/conftest.py` (verified — it has the Tenderly fork fixtures).
CLAUDE.md "Testing Infrastructure" § also says `execution-service/tests/integration/conftest.py`. Fix the conftest path
in both the codex doc and CLAUDE.md, and confirm the three NEW consumers actually reference the shared fixture (not
duplicate fork-creation). | PRE_CUTOVER ✅ DONE-PARTIAL @SLOT8-TESTING-BATCH — tenderly-execution-provider.md
test_amm_golden_swaps.py path corrected to `tests/defi_execution/integration/` (was `tests/integration/`). CLAUDE.md
mirror fix ✅ DONE @SLOT8-CLAUDE-MD-BUNDLE (line 380 path corrected). Three NEW consumer share-fixture verification 🟡
ROUTED-TO-EXECUTION-SERVICE-OWNER. | governance + execution-service owner | `tenderly-execution-provider.md:300-318` +
`cursor-configs/CLAUDE.md:354` vs `ls execution-service/tests/defi_execution/integration/conftest.py` | | TS-13 | ADD —
`test-coverage-data-status.md` § "Audit + ratchet" says "every (service, asset_group, venue, data_type) row in the audit
is tested in the playwright matrix" and "any flip from WORKING → STOPS_AT_INTERMEDIATE_LEVEL is a failing test" — but
doesn't name the QG step / CI job that enforces it, nor a `last_executed` date for the playwright drilldown matrix. The
doc reads as a contract with no enforcement hook. ADD the enforcing job name + execution-owner block, or downgrade the
"is a failing test" language to "SHOULD be". | PRE_CUTOVER ✅ DONE @SLOT8-TESTING-BATCH — `execution:` YAML block added
inline at `test-coverage-data-status.md` § "Audit + ratchet" (owner=deployment-ui playwright suite /
cadence=per-PR+nightly / verifier=playwright job status). "is a failing test" language clarified as aspirational with
per-PR-pairing fallback. | governance + deployment-ui owner | `test-coverage-data-status.md:36-49` (no QG/job reference)
|

### Tier 3 — stale / superseded / currency

| # | Finding (KEEP/LIFT/CONSOLIDATE/DELETE/ADD) | Disposition (IMMEDIATE/PRE_CUTOVER/POST_CUTOVER) | Owner | Evidence
(file:line) | | ----- |
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

|
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

| ---------- |
-----------------------------------------------------------------------------------------------------------------------------------------

| ----------------- | ------------------------------------ | | TS-14 | DELETE — `06-coding-standards/README.md` contains
the **entire "Test Infrastructure: Emulators & Mocks" section TWICE, verbatim** (once near the QG-config block ~line
824, once again near the error-handling block ~line 860; `grep -c "Test Infrastructure: Emulators"` → 2). Same 11-row
table, same wrong paths (TS-1), same "Full details: cicd_mock_hardening (Plan #60)" footer. Delete one copy; keep a
single canonical instance (and ideally LIFT it into `testing.md` and have README link out — see TS-15). | IMMEDIATE ✅
DONE @766bcfbc — second copy deleted; HTML breadcrumb comment points to canonical first copy. | governance |
`/codex/06-coding-standards/README.md` — duplicated `## Test Infrastructure: Emulators & Mocks` (2 occurrences) | |
TS-15 | CONSOLIDATE — `06-coding-standards/testing.md` is a **1-line stub** ("See README.md and
integration-testing-layers.md") yet `00-SSOT-INDEX.md:188` lists it as the SSOT for "Test standards (structure,
patterns, coverage targets)". The actual content is scattered: emulator/mock table in `README.md` (×2), tier model in
`integration-testing-layers.md`, VCR in two docs, API-key mode in `07-security/`, coverage formula in
`quality-gates.md` + a `.mdc` cursor rule + `unified-trading-pm/docs/testing/testing-requirements.md`. CONSOLIDATE into
`testing.md` as the real testing-infrastructure SSOT (emulator hosts, moto, network gate, mock-WS, VCR pointers,
coverage formula, `INTEGRATION_TEST_MODE`, test-templates, no-`_extended` rule, two-pass model) with the others linking
to it. Triple-SSOT for coverage targets (codex narrative + `.mdc` cursor rule + PM `docs/testing/`) is the worst
offender — pick one. | PRE_CUTOVER ✅ DONE-PARTIAL @SLOT8-TESTING-BATCH — `testing.md` now ships as the conventions SSOT
(no-\_extended + singleton-conftest + two-pass model + cross-refs). Full coverage-target consolidation
(codex+mdc+PM-docs collapse) still tracked as P2; this batch addresses the most-impactful gap (the testing-conventions
surface). | governance | `/codex/06-coding-standards/testing.md` (stub) + `00-SSOT-INDEX.md:188,53,65` (3 different
"testing requirements/standards" SSOT pointers) | | TS-16 | LIFT — `00-SSOT-INDEX.md` does **not** index
`vcr-cassette-pattern.md`, `ui-testing-layers.md`, or `test-coverage-data-status.md` (greps return 0).
`ui-testing-layers.md` ("Last Updated 2026-04-24", 8-layer model) and `test-coverage-data-status.md` are both active
SSOT-grade docs. Add SSOT-INDEX rows. (Mirrors the SSOT-INDEX-completeness pattern from the Ops audit finding O-15 /
Governance G-11.) | IMMEDIATE ✅ DONE @766bcfbc — 3 new SSOT-INDEX rows added after "Integration testing layers (0–3)"
row. | governance | `codex/00-SSOT-INDEX.md` (grep
`vcr-cassette-pattern                                                                                      | ui-testing-layers | test-coverage-data-status`
→ 0 hits) | | TS-17 | LIFT — `cicd_mock_hardening_2026_03_11.plan.md` is archived; its content is "folded forward" into
`README.md` § "Test Infrastructure" and `quality-gates.md` § GCP Emulator / Moto / Credential-Free Gate / Cassette
Parity / Cassette Drift. **But the fold-forward inherited the plan's todo-text paths, not the as-shipped paths** (TS-1).
Also several "h\*" todos still marked `done`/`completed` should be operationally re-verified per "Plans Run To Actual
Completion" (e.g. is `cassette-drift-check.yml` actually scheduled and running? Is the moto suite at 26 tests?). Add an
"as-shipped reconciliation" note to the archived plan banner OR (better) finish the consolidation in TS-15 so the codex
no longer points at the archived plan for "full details". | PRE_CUTOVER 🟡 ROUTED-TO-FOLLOW-UP — as-shipped
reconciliation of the archived cicd_mock plan against the current README/quality-gates fold-forward is a >2hr-audit
task; defer to a dedicated archive-plan audit cycle. TS-15 conventions consolidation already addresses the
most-impactful drift surface. | governance | `cicd_mock_hardening_2026_03_11.plan.md` todos vs
`README.md`/`quality-gates.md` fold-forward + TS-1 path mismatch | | TS-18 | LIFT — `integration-testing-layers.md`
Layer 0 section + `vcr-cassette-ownership.md` § "VCR-based integration test execution" describe replay running "from
within owning interface repos (unified-cloud-interface, `market_tick_data_service/market_interface`,
instruments-service)" — but the post-collapse reality also includes execution-service / position-balance-monitor-service
(per `testing-with-api-keys.md`'s own matrix and `vcr-cassette-ownership.md:11-12`'s "UTEI/USEI/UDEI→execution-service"
note). The Layer-0 doc undercounts the cassette-replay-owning repos. Reconcile the owning-repo list across all three
docs. | PRE_CUTOVER ✅ DONE @SLOT8-TESTING-BATCH — `integration-testing-layers.md` Layer 0 §
VCR-based-integration-test-execution rewritten with 5-repo owning list (unified-cloud-interface / MTDS /
instruments-service / execution-service / position-balance-monitor-service); pointer now to vcr-cassette-ownership.md as
canonical (the deprecated `vcr-cassette-pattern.md` ref removed). | governance | `integration-testing-layers.md:62-79`
vs `vcr-cassette-ownership.md:10-13,242` vs `testing-with-api-keys.md:62-70` |

### Tier 4 — additions worth shipping

| #                                                                                                     | Finding (KEEP/LIFT/CONSOLIDATE/DELETE/ADD)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Disposition (IMMEDIATE/PRE_CUTOVER/POST_CUTOVER) | Owner                                | Evidence (file:line)                                                                                                                                                                |
| ----------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ | ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| TS-19 ✅ FILED @ `plans/active/alerting_runbook_and_operator_ux_post_cutover_2026_05_12.md` (Group E) | ADD — No codex doc states the **two-pass QG model for agents** in a testing context (Pass 1 = full `quality-gates.sh` incl. tests; Pass 2 = `quickmerge --agent` skips tests). It's in CLAUDE.md "Git discipline" + `.claude/rules/python-backend.md` but not in `quality-gates.md`/`testing.md`. ADD a 3-line "Two-pass model — when tests run" subsection to `quality-gates.md` so the "Pass 2 doesn't re-run tests" contract is discoverable from the testing SSOT (avoids "I ran quickmerge --agent so tests passed" misreads).                                                                                                                                                                                                          | POST_CUTOVER                                     | governance                           | `cursor-configs/CLAUDE.md` § "Git discipline" / `.claude/rules/python-backend.md` § "Two-pass model" vs `/codex/06-coding-standards/quality-gates.md` (no two-pass-test subsection) |
| TS-20 ✅ FILED @ `plans/active/alerting_runbook_and_operator_ux_post_cutover_2026_05_12.md` (Group F) | ADD — `integration-testing-layers.md` § "Emulator vs Mock Fixture Decision Matrix" row "DeFi on-chain protocols → Sim mode + `responses passthrough=False`" does not mention the **Tenderly fork fixture path** (the actual DeFi _integration_-layer choice per `tenderly-execution-provider.md` + `execution-service/tests/defi_execution/integration/conftest.py`). The matrix conflates DeFi-unit (sim/responses) with DeFi-integration (Tenderly fork). ADD a distinct row: "DeFi on-chain integration (real swap/AMM fidelity) → Tenderly VNet fork fixture (`tests/defi_execution/integration/conftest.py`)". Also add a row for IBKR (`MagicMock(spec=IB)` — currently only in `vcr-cassette-ownership.md`, not the decision matrix). | POST_CUTOVER                                     | governance + execution-service owner | `integration-testing-layers.md:219-234` (matrix) vs `tenderly-execution-provider.md` + `vcr-cassette-ownership.md:158-220`                                                          |

## Disposition counts

- **IMMEDIATE**: 6 — TS-1, TS-2, TS-3, TS-4, TS-14, TS-16 (codex paths/claims that misdirect operators on
  cutover-relevant testing surfaces; one verbatim-duplicated section).
- **PRE_CUTOVER**: 12 — TS-5, TS-6, TS-7, TS-8, TS-9, TS-10, TS-11, TS-12, TS-13, TS-15, TS-17, TS-18 (doc
  reconciliations, the testing-infra SSOT consolidation, and three new QG/enforcement adds).
- **POST_CUTOVER**: 2 — TS-19, TS-20 (non-blocking decision-matrix + two-pass-model additions).
- **Total**: 20 findings.

## Recommended next steps

1. **Operator triage** — confirm dispositions. **CRITICAL operator-attention**:
   - **TS-3 + TS-1 + TS-2**: VCR docs are internally contradictory and point at deleted/wrong paths —
     `vcr-cassette-pattern.md` says "run the recording script in AC" while `vcr-cassette-ownership.md` says "AC ships no
     recording script", and the cassette dir / `vcr_endpoints.py` / `network_block_plugin.py` paths are all stale. A
     pre-cutover engineer trying to record or block-network from the codex will hit dead ends. Pick
     `vcr-cassette-ownership.md` as the survivor; gut or fold `vcr-cassette-pattern.md`.
   - **TS-5**: `quality-gates.md` + `dependency-management.md` still teach `[project.optional-dependencies] dev` /
     `uv pip install -e ".[dev]"` — directly contradicts the workspace "Flat deps only" rule and the actual pyprojects.
     Risk: an agent re-introduces `[dev]` extras following the codex.
   - **TS-15 + TS-14**: there is no real testing-infrastructure codex SSOT (`testing.md` is a 1-line stub; the
     emulator/mock table is duplicated verbatim in README; coverage targets have 3 competing SSOTs). Consolidating into
     `testing.md` is the highest-leverage fix.
2. **Phase 3 ship (IMMEDIATE, ~0.5 AI-day):** TS-1 (fix 3+ network_block_plugin / fault_injection / mock_replay paths),
   TS-2 (fix VCR cassette + vcr_endpoints paths in `vcr-cassette-pattern.md`), TS-3 (delete the AC-recording-script
   section), TS-4 (drop "Infura" from tenderly doc), TS-14 (delete the duplicated README section), TS-16 (add 3
   SSOT-INDEX rows).
3. **Phase 4 ship (PRE_CUTOVER, ~3 AI-days):** TS-5 (sweep `.[dev]` → flat-deps in 2 codex docs), TS-6 (create
   `ibkr-mock-pattern.md` stub or repoint), TS-7 (refresh `integration-testing-layers.md` header + dead plan link), TS-8
   (re-derive the API-key cassette matrix from `vcr-cassette-ownership.md`), TS-9 (QG step: every service conftest
   registers the network gate), TS-10 (add no-`_extended` + singleton-fixture rules to `testing.md` + optional ratchet),
   TS-11 (execution-owner blocks for cassette-parity / drift / orphan-checker), TS-12 (fix DeFi conftest path in codex +
   CLAUDE.md), TS-13 (name the enforcing job for the data-status playwright matrix), TS-15 (consolidate the
   testing-infra SSOT into `testing.md`), TS-17 (as-shipped reconciliation of the archived cicd_mock plan or finish
   TS-15), TS-18 (reconcile owning-repo lists across the 3 VCR docs).
4. **Phase 5 file (POST_CUTOVER backlog):** TS-19 (two-pass-model subsection in `quality-gates.md`), TS-20
   (Tenderly-fork + IBKR rows in the emulator/mock decision matrix).

## Composes with

- `plans/active/codex_vs_citadel_infrastructure_audit_2026_05_10.md` Phase 1.L (this audit slice).
- `plans/active/issues/codex_audit_ops_2026_05_12.md` Phase 1.I — finding O-15 (SSOT-INDEX completeness) mirrored in
  TS-16.
- `plans/archive/cicd_mock_hardening_2026_03_11.plan.md` — the archived plan whose fold-forward inherited stale paths
  (TS-1, TS-17).
- `cursor-configs/CLAUDE.md` § "Testing Infrastructure (Emulators & Mocks)" + "Dependencies + builds" + "Git discipline"
  (the workspace rules being audited; TS-5, TS-12, TS-19).
- `unified-trading-pm/docs/testing/testing-requirements.md` + `cursor-rules/testing/test-coverage-targets.mdc` — the
  competing coverage-target SSOTs flagged in TS-15.
