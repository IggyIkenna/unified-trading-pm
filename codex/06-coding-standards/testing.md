---
scope: [engineer]
last_updated: 2026-05-12
---

# Testing Standards

> **SSOT for test-file conventions + the no-`_extended` rule + singleton-conftest-fixture rule (codified 2026-05-12
> per TS-10 audit).** For the 5-layer integration testing tier model, see
> [integration-testing-layers.md](integration-testing-layers.md). For the emulator/moto/cassette infrastructure table,
> see [README.md § "Test Infrastructure: Emulators & Mocks"](README.md). For the credential-free QG gate, see
> [quality-gates.md § "Test Infrastructure"](quality-gates.md). TS-15 (consolidate the testing-infra SSOT into this
> doc) is the next planned extension — today this doc is the conventions surface; the cross-refs above remain authoritative
> for their respective layers.

## No `test_*_extended.py` / `test_*_additional.py` / `test_*_new.py` files

**Rule**: when a test file grows beyond what a single class / pytest module can hold, **split by behaviour**, not by
"part 2". Files named `test_foo_extended.py` / `test_foo_additional.py` / `test_foo_new.py` are forbidden — they
silently hide the fact that the original `test_foo.py` couldn't be extended (which usually means the file lacked a
clear behavioural axis).

Workspace evidence: `.claude/rules/python-backend.md` + `.claude/rules/universal.md` § "Expand existing test files".
The codex SSOT is this doc (2026-05-12 codification).

**Proposed QG ratchet** (PRE_CUTOVER backlog per TS-10 audit): `rg 'test_.*_(extended|additional|new)\.py'` → fail in
QG. Today reviewer-discipline-only; ratchet wiring 🟡 NEEDS-OPERATOR-GATE (auto-fail vs warning).

## Singleton conftest fixtures

**Rule**: every per-test-module fixture that mocks an external I/O surface (HTTP client, S3/GCS client, Pub/Sub
publisher, Web3 RPC) MUST live in the nearest `conftest.py` as an `@pytest.fixture(autouse=True)` singleton —
NOT instantiated per-test inside individual test functions. Reasons:

1. Per-test instantiation triples test runtime when the mock has heavy setup (cassette load, Tenderly fork creation).
2. Cross-test state leaks if the mock isn't reset; the `autouse=True` fixture's teardown is the single canonical
   reset point.
3. Two tests in the same module mocking the same surface differently is a smell — usually means the surface needs
   to be parameterised, not duplicated.

Reference impls:
- `unified-api-contracts/unified_api_contracts/testing/*` — autouse network_block_plugin / fault_injection /
  mock_replay fixtures.
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

## Two-pass model — when tests run

Per CLAUDE.md "Git discipline" + `.claude/rules/python-backend.md` § "Two-pass model":

- **Pass 1**: `bash scripts/quality-gates.sh` (full local QG — lint + format + typecheck + **tests**).
- **Pass 2**: `bash scripts/quickmerge.sh "msg" --agent` (lint/format/typecheck/codex — **no tests; Pass 1 already
  ran them**).

A common misread: "I ran `quickmerge --agent` and it passed, so tests passed too" — **wrong**. Pass 2 deliberately
skips tests; Pass 1 is the test gate. SSOT pointer added 2026-05-12 per TS-19 audit (POST_CUTOVER backlog) is here
as well — agents should not interpret a green Pass 2 as test coverage.

## Cross-references

- [integration-testing-layers.md](integration-testing-layers.md) — 5-layer tier model + cassette parity/drift +
  credential-free gate.
- [README.md](README.md) § "Test Infrastructure: Emulators & Mocks" — emulator hosts + moto + mock-WS + VCR pointers.
- [quality-gates.md](quality-gates.md) — coverage formula + ratchet thresholds + QG step inventory.
- [vcr-cassette-pattern.md](../02-data/vcr-cassette-pattern.md) → redirected to
  [vcr-cassette-ownership.md](../02-data/vcr-cassette-ownership.md) (canonical SSOT post-TS-3).
- [test-templates/README.md](test-templates/README.md) — copy-paste boilerplate for events / pytest-asyncio fixtures.
