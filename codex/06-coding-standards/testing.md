---
doc_type: codex-ssot
title: Testing Standards
summary: >-
  Test-file conventions SSOT — the no-`test_*_extended`/`_additional`/`_new.py` rule (split by behaviour, not "part 2")
  and the singleton-conftest-fixture rule (codified 2026-05-12 per TS-10 audit); defers the 5-layer integration tier
  model to integration-testing-layers.md and the emulator/mock infra table to README.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, market-tick-data-service, unified-api-contracts]
scope: [engineer]
tags: [testing, quality-gates, conventions, refactor]

  [
    /codex/06-coding-standards/integration-testing-layers.md,
    /codex/06-coding-standards/README.md,
    /codex/06-coding-standards/quality-gates.md,
    /codex/06-coding-standards/ui-testing-layers.md,
  ]
created: 2026-03-27
authoritative_for: [test-file conventions (no-_extended rule + singleton-conftest-fixture rule)]
referenced_by:
  [
    /codex/02-data/vcr-cassette-ownership.md,
    /codex/06-coding-standards/README.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
owner:
last_reviewed:
code_refs:
last_updated: 2026-05-12
---

# Testing Standards

> **SSOT for test-file conventions + the no-`_extended` rule + singleton-conftest-fixture rule (codified 2026-05-12 per
> TS-10 audit).** For the 5-layer integration testing tier model, see
> [integration-testing-layers.md](integration-testing-layers.md). For the emulator/moto/cassette infrastructure table,
> see [README.md § "Test Infrastructure: Emulators & Mocks"](README.md). For the credential-free QG gate, see
> [quality-gates.md § "Test Infrastructure"](quality-gates.md). TS-15 (consolidate the testing-infra SSOT into this doc)
> is the next planned extension — today this doc is the conventions surface; the cross-refs above remain authoritative
> for their respective layers.

## No `test_*_extended.py` / `test_*_additional.py` / `test_*_new.py` files

**Rule**: when a test file grows beyond what a single class / pytest module can hold, **split by behaviour**, not by
"part 2". Files named `test_foo_extended.py` / `test_foo_additional.py` / `test_foo_new.py` are forbidden — they
silently hide the fact that the original `test_foo.py` couldn't be extended (which usually means the file lacked a clear
behavioural axis).

Workspace evidence: `.claude/rules/python-backend.md` + `.claude/rules/universal.md` § "Expand existing test files". The
codex SSOT is this doc (2026-05-12 codification).

**Proposed QG ratchet** (post-cutover backlog per TS-10 audit): `rg 'test*.\*\_(extended|additional|new)\.py'` → fail in
QG. Today reviewer-discipline-only; ratchet wiring 🟡 NEEDS-OPERATOR-GATE (auto-fail vs warning).

> **[DELTA 2026-05-22]** **Current state:** Reviewer-discipline only — no automated QG ratchet for `test_*_extended.py`
> / `test_*_additional.py` / `test_*_new.py` filenames. **Planned delta:** `plans/epics/infrastructure_master.md` — STEP
> 5.x ratchet to auto-fail QG on these filename patterns. **Target:** Any new `test_*_extended.py` fails QG immediately;
> zero such files in the workspace.

## Singleton conftest fixtures

**Rule**: every per-test-module fixture that mocks an external I/O surface (HTTP client, S3/GCS client, Pub/Sub
publisher, Web3 RPC) MUST live in the nearest `conftest.py` as an `@pytest.fixture(autouse=True)` singleton — NOT
instantiated per-test inside individual test functions. Reasons:

1. Per-test instantiation triples test runtime when the mock has heavy setup (cassette load, Tenderly fork creation).
2. Cross-test state leaks if the mock isn't reset; the `autouse=True` fixture's teardown is the single canonical reset
   point.
3. Two tests in the same module mocking the same surface differently is a smell — usually means the surface needs to be
   parameterised, not duplicated.

Reference impls:

- `unified-api-contracts/unified_api_contracts/testing/*` — autouse network_block_plugin / fault_injection / mock_replay
  fixtures.
- `market-tick-data-service/tests/market_interface/conftest.py:20-44` — `MockWebSocketFeed` autouse fixture.
- `execution-service/tests/defi_execution/integration/conftest.py` — shared Tenderly fork fixture.

## Test file structure (recap)

Per `.claude/rules/python-backend.md` § Testing + `.claude/rules/universal.md`:

1. **Mirror source structure** — `service/foo/bar.py` → `tests/foo/test_bar.py`.
2. **One test class per behavioural axis** — `class TestFooHappyPath:` / `class TestFooErrorPaths:` /
   `class TestFooEdgeCases:`. Not `class TestFoo:` with 200 methods.
3. **Expand existing files** — see "No `_extended`" rule above.
4. **autouse conftest fixtures for I/O mocks** — see "Singleton conftest fixtures" above.
5. **`pool: "forks"` in `vitest.config.ts`** for TS test repos — see CLAUDE.md "Local Development" §.

## BLOCK_CRITICAL emission-policy test pattern

**Added 2026-05-15 — Phase 8 / slot 6 doc-currency audit.**

When a service uses `ServiceEmissionPolicy.BLOCK_CRITICAL` as its write policy, unit tests MUST verify all three routing
outcomes:

1. **Suppression path** — empty / invalid data → `decision.should_publish_row == False`.
2. **Alert path** — same suppression input → `decision.should_alert == True`.
3. **Publish path** — valid data → `decision.should_publish_row == True`, no alert.

Reference implementation: `risk-and-exposure-service/tests/test_emission_policy_risk_state.py` — uses two test classes
(`TestCheckEmissionPolicyRouting` for the 4 routing cases, `TestRiskSnapshotSinkWrite` for the sink integration).

**Done-def for BLOCK_CRITICAL coverage**: risk-and-exposure-service (and any future service adopting `BLOCK_CRITICAL`)
has tests covering suppression + alert + publish routing + deactivation re-arms. QG coverage gate applies (≥70%). SSOT:
`/codex/02-data/service-output-emission-semantics.md` § BLOCK_CRITICAL.

---

## LocalKeyCustodyProvider test pattern (mock-`_w3` seam)

**Added 2026-05-15 — Phase 8 / slot 6 doc-currency audit.**

`LocalKeyCustodyProvider` (dev-only raw-PK signing) has **no constructor injection seam** for the Web3 client — unlike
`CloudKmsCustodyProvider` which accepts `kms_client`/`secrets_client` as params. The correct mock seam is **direct
attribute assignment** after construction:

```python
provider = LocalKeyCustodyProvider(private_key=_TEST_PK)
provider._w3 = _make_mock_web3()   # bypass lazy _get_web3() initialisation
```

`_make_mock_web3()` must stub `eth.account.from_key.return_value.address`,
`eth.account.from_key.return_value.sign_transaction.return_value.raw_transaction`, `eth.get_balance`,
`eth.get_transaction_count`, `eth.gas_price`, `eth.send_raw_transaction`.

**TxParams optional-key access**: `web3`'s `TxParams` TypedDict marks most keys as `NotRequired`. Access via
`.get("key")`, never `["key"]`, to satisfy `basedpyright reportTypedDictNotRequiredAccess`.

**Conftest requirement**: `setup_events(MockEventSink())` must be called in conftest so `log_event()` calls in provider
methods don't raise during test.

Reference implementation: `execution-service/tests/unit/custody/test_local_key_provider.py` (33 tests, 8 classes;
committed `f1dee093` 2026-05-15).

---

## Two-pass model — when tests run

Per CLAUDE.md "Git discipline" + `.claude/rules/python-backend.md` § "Two-pass model":

- **Pass 1**: `bash scripts/quality-gates.sh` (full local QG — lint + format + typecheck + **tests**).
- **Pass 2**: `bash scripts/quickmerge.sh "msg" --agent` (lint/format/typecheck/codex — **no tests; Pass 1 already ran
  them**).

A common misread: "I ran `quickmerge --agent` and it passed, so tests passed too" -- **wrong**. Pass 2 deliberately
skips tests; Pass 1 is the test gate. SSOT pointer added 2026-05-12 per TS-19 audit (post-cutover backlog -- this doc is
the landing) -- agents should not interpret a green Pass 2 as test coverage.

## Cross-references

- [integration-testing-layers.md](integration-testing-layers.md) — 5-layer tier model + cassette parity/drift +
  credential-free gate.
- [README.md](README.md) § "Test Infrastructure: Emulators & Mocks" — emulator hosts + moto + mock-WS + VCR pointers.
- [quality-gates.md](quality-gates.md) — coverage formula + ratchet thresholds + QG step inventory.
- [vcr-cassette-pattern.md](vcr-cassette-pattern.md) → redirected to
  [vcr-cassette-ownership.md](/codex/02-data/vcr-cassette-ownership.md) (canonical SSOT post-TS-3).
- [test-templates/README.md](test-templates/README.md) — copy-paste boilerplate for events / pytest-asyncio fixtures.
