# Agent Prompt — Phase 2: Library Tier Hardening

> Paste this entire prompt into a new agent session to execute Phase 2. REQUIRES Phase 1 fully complete. Verify
> preconditions before starting.

---

Follow all workspace cursor rules in .cursorrules. No summary docs (no-summary-docs.mdc). uv not pip. quickmerge not git
push. basedpyright <dir>/ not basedpyright. Delete deprecated code; no parallel code paths. Search unified libraries
before implementing anything new.

WORKSPACE_ROOT=${UNIFIED_TRADING_WORKSPACE_ROOT}/unified-trading-system-repos All Python/pytest/ruff/basedpyright/QG
commands: cd $WORKSPACE_ROOT
&& source .venv-workspace/bin/activate first.

---

## Standard of Work — Citadel Audit-Worthy

> **When in doubt, assume a senior quant engineer at a top-tier fund (Citadel, Two Sigma, DE Shaw) is reviewing every
> PR. Build accordingly.**

This means — no exceptions, no shortcuts:

- **No silent errors** — every `except` block must reraise, raise a typed error, or log at ERROR + reraise. `pass` is a
  build failure.
- **No empty fallbacks** — `os.getenv(KEY, '')` silently fails in production; forbidden. Use `UnifiedCloudConfig` or
  `os.environ[KEY]` (raises on missing).
- **No untyped code** — every function parameter, return type, and class field has a type annotation. `Any` is forbidden
  unless documented in `QUALITY_GATE_BYPASS_AUDIT.md`.
- **No TODO comments** in production code — open a GitHub issue with a link instead.
- **No magic numbers/strings** — use constants from UCI or AC.
- **No skipped tests** — every skip must have a linked issue and an `xfail` marker.
- **Every public function/class** has a docstring.
- **Every secret** through Secret Manager. Every config through `UnifiedCloudConfig`.
- If it would fail a Citadel code review, it is not done.

---

## Preconditions (verify ALL before starting)

```bash
# 1. All repos have quickmerge template (Phase 1 A1)
ls unified-trading-services/scripts/quickmerge.sh  # spot check

# 2. No old names anywhere
rg 'market-tick-data-handler|client-reporting-api|alerting-service' --type py  # must be zero

# 3. CI/CD live (Phase 1 A3)
# verify version-bump.yml exists in at least 3 repos

# 4. Import smoke test passes for all T0 libraries
cd unified-api-contracts && python -c "import unified_api_contracts"
cd unified-config-interface && python -c "import unified_config_interface"
```

If any check fails: STOP. Complete Phase 1 first.

---

## SSOT

| Source                 | Path                                                                                                                           |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Workspace manifest DAG | `unified-trading-pm/WORKSPACE_MANIFEST_DAG.svg` — 63 repos, 13 levels (L0-L12, AUTHORITATIVE). L0=PM, L1=codex, L2+=code repos |
| Manifest JSON          | `unified-trading-pm/workspace-manifest.json`                                                                                   |
| Tier architecture      | `unified-trading-/codex/04-architecture/TIER-ARCHITECTURE.md`                                                                  |
| Library matrix         | `unified-trading-/codex/05-infrastructure/unified-libraries/LIBRARY-DEPENDENCY-MATRIX.md`                                      |

**Library tier map:**

| Abbrev  | Repo                               | Tier |
| ------- | ---------------------------------- | ---- |
| AC      | unified-api-contracts              | T0   |
| UIC_INT | unified-internal-contracts         | T0   |
| UCI     | unified-config-interface           | T0   |
| UEI     | unified-trading-library            | T0   |
| UCLI    | unified-cloud-interface            | T0   |
| URDI    | unified-reference-data-interface   | T0   |
| EAL     | execution-algo-library             | T0   |
| MEL     | matching-engine-library            | T0   |
| UTS     | unified-trading-services           | T1   |
| UMI     | unified-market-interface           | T2   |
| UTEI    | unified-trade-execution-interface  | T2   |
| UML     | unified-ml-interface               | T2   |
| UFC     | unified-feature-calculator-library | T2   |
| UPI     | unified-position-interface         | T2   |
| UDEI    | unified-defi-execution-interface   | T2   |
| USEI    | unified-sports-execution-interface | T2   |
| UDC     | unified-domain-client              | T3   |

---

## Naming — Zero Tolerance

Any rename must be complete at ALL levels: pyproject.toml, Python package dir, all imports (rg all 57 repos), Artifact
Registry package, cloudbuild.yaml image tags, Cloud Build trigger name, workspace-manifest.json (4 fields),
runtime-topology.yaml, cursor rules, codex docs.

**NEVER:** old name as alias, re-export, `_deprecated.py`, or `try/except ImportError` fallback.

---

## Bottom-Up Development Rule — No Exceptions

> If a code change requires new functionality that does not exist in a library, add it to the correct library FIRST.
> Never define schemas, error types, event names, or contracts inline in a higher-tier repo.

| If you need...                       | Add to first                              | Tier |
| ------------------------------------ | ----------------------------------------- | ---- |
| New error schema / typed exception   | `unified-api-contracts` (AC)              | T0   |
| New internal event / domain contract | `unified-internal-contracts` (UIC_INT)    | T0   |
| New lifecycle event name             | `unified-trading-library` (UEI)           | T0   |
| New config field                     | `unified-config-interface` (UCI)          | T0   |
| New cloud primitive                  | `unified-cloud-interface` (UCLI)          | T0   |
| New reference data protocol          | `unified-reference-data-interface` (URDI) | T0   |
| New market schema / adapter protocol | `unified-market-interface` (UMI)          | T2   |
| New domain entity                    | `unified-domain-client` (UDC)             | T3   |

**Workflow:** Add to library → run D5 → bump version → cascade `--dep-branch` to all consumers → use in higher tier.
Never skip a step. Never add a workaround in the consuming repo.

---

## Testing Progression — Fastest Feedback First

Every repo follows this ladder. Fix each step before running the next.

| Step         | Command                                        | ~Time   | Catches                                                           |
| ------------ | ---------------------------------------------- | ------- | ----------------------------------------------------------------- |
| Import smoke | `python -c "import <pkg>"`                     | 2s      | Broken `__init__`, circular imports, missing installed deps       |
| D1           | `bash scripts/quickmerge.sh "msg" --lint-only` | 30s     | Syntax, import ordering, line length, formatting                  |
| D2           | `bash scripts/quickmerge.sh "msg" --unit-only` | ~2 min  | Type errors, unit test failures, import-time errors               |
| D3           | `bash scripts/quickmerge.sh "msg" --qg-only`   | ~5 min  | Integration failures, coverage gaps — no git ops, safe to retry   |
| D4           | `bash scripts/quickmerge.sh "msg" --quick`     | ~8 min  | Full QG + git branch ops, no act simulation                       |
| D5           | `bash scripts/quickmerge.sh "msg"`             | ~15 min | Full pipeline with act simulation — **the only gate that counts** |

**Invariant:** Never declare a tier green until D5 passes. `--quick` alone is not sufficient.

---

## Execution Order

### Step 0A — Import Smoke Test (global, all 57 repos, run first)

10 parallel agents (5–6 repos each):

```bash
cd <repo> && source WORKSPACE_ROOT/.venv-workspace/bin/activate
python -c "import <package_name>" 2>&1
```

Record every failure before touching anything else. These are P0 issues — fix them before any other work. Broken imports
cascade: they make every other test fail.

If fixing an import failure requires a new feature in a lower-tier library → apply the bottom-up rule: add to library
first, run D5, then fix the import.

### Step 0B — Global Violation Sweep (all 57 repos, after 0A)

10 parallel agents (5–6 repos each). Three rounds per repo:

**Round 0 — Setup.sh deduplication (before code changes):**

- Verify `scripts/setup.sh` exists (Phase 1 rollout). If ad-hoc version remains, replace with canonical template from
  `unified-trading-pm/scripts/setup.sh`
- Remove duplicated bootstrap logic from `quality-gates.sh`: venv creation, uv bootstrap, `uv lock`, dep install →
  replace with `source scripts/setup.sh` or guard with `[ -f .setup-stamp ]` check
- Verify `bash scripts/setup.sh --check` passes before any code changes

**Round 1 — Mechanical replacements (no structural changes):**

- `os.getenv(KEY, '')` or `os.getenv(KEY)` → `UnifiedCloudConfig` field or `os.environ[KEY]` (empty-string fallback =
  silent failure = forbidden)
- `bare except:` → specific typed exception + log + reraise
- `except Exception: pass` → log with full context (message, traceback, correlation_id) + reraise
- `except <AnyType>: pass` — any silent swallow → log at ERROR + reraise (no exception may be silently discarded)
- `print()` in production source → `logger.info()` with structured fields
- `datetime.now()` / `datetime.utcnow()` → `datetime.now(timezone.utc)`
- `List[x]` / `Dict[x,y]` / `Tuple[x]` → `list[x]` / `dict[x,y]` / `tuple[x]`
- `except ImportError` fallbacks → delete entirely; fail loud (no conditional imports)

**Round 2 — Error handling completeness:** Every `except` block must do one of: (a) reraise, (b) raise a typed
replacement error, (c) log at ERROR with full context + reraise. If the correct typed error class doesn't exist in AC or
UIC_INT → add it there first (bottom-up rule), then use it.

**Round 3 — File and function size:**

```bash
# Files > 900 lines — must be split by SRP:
find . -name "*.py" ! -path "./.venv*" ! -path "*/tests/*" | xargs wc -l 2>/dev/null | sort -rn | awk '$1 > 900 {print}'
# Complexity check (functions > 10 cyclomatic = candidate for split):
timeout 60 ruff check --select C901 . 2>/dev/null
```

Files >900 lines: split by Single Responsibility Principle. Each split is its own commit with a clear message explaining
what was extracted and why. Functions >50 lines: extract named sub-functions for each logical step.

Commit Round 0: `'chore: deduplicate setup logic — quality-gates.sh sources setup.sh'` Commit Round 1+2:
`'fix: global violation sweep — error handling + mechanical QG fixes'` Commit Round 3:
`'refactor: split large files by SRP — file size enforcement'`

### Tier 0 — T0 (8 repos in parallel, after global sweep)

Each repo: A → B → C → D1 → D2 → D3 → D4 → D5.

**Step A** — Deploy structure: verify `cloudbuild.yaml`, `quality-gates.sh`, `setup.sh`, `pyproject.toml`,
`workspace-manifest.json` present and correct. Run `bash scripts/setup.sh --check`. No old names anywhere.

**Step B** — Tests first (write/fix tests before any code rewrite):

- Integration Layer 0: `test_contract_alignment.py` + `test_ac_uic_alignment.py` in AC; `test_uic_ac_alignment.py` in
  UIC_INT — must pass before any T1 work
- All schema todos (ic-greeks-position-schema, ic-pnl-breakdown-schema, ic-circuit-breaker-schema, etc.)
- Coverage floor: every module ≥60%; critical modules ≥80%

**Step C** — Code rewrite:

- URDI: REST adapters, `get_secret_client` via UCLI, rate limiting, `@with_retry`
- MEL: zero inter-library deps (remove any UTS/UCI imports)
- Fix MEL tier in DAG SVG (must show T0)
- AC: split large files (`aws_schemas.py` 1424L, `venue_manifest.py` 1058L, `binance/schemas.py` 1033L)

**D1 → D5:** Run quickmerge ladder. Fix each step before proceeding. D5 = T0 green gate.

**Do NOT start T1 until ALL 8 T0 repos pass D5.**

### Tier 1 — UTS (after all T0 green)

Same A → B → C → D1–D5:

**Step C key tasks:**

- Remove `create_instruments_client`, `create_market_candle_data_client`, `StandardizedDomainCloudService` re-exports
  from `__init__.py`
- UTS dual-publish rename: add `unified_trading_services/` re-export; cascade to ALL 14 services + 7 T2 libs via
  `--dep-branch`; delete old import path immediately
- Verify all of these exist and are tested: `GCSEventSink`, `PubSubEventSink`, `QueueEventSink`, `ServiceCLI`,
  `BatchOrchestrator`, `@with_retry`, `setup_service`, `StateStore`, `BaseCloudWriter`, `GracefulShutdownHandler`

**D5 = T1 green gate.** Do NOT start T2 until UTS passes D5.

### Tier 2 — T2 (7 repos in parallel, after T0+T1 green)

Same A → B → C → D1–D5:

**Step A critical:** Remove UDC from UMI `pyproject.toml` — T2 imports T0+T1 only. Add tier-boundary CI check to
`quality-gates.sh`.

**Step B:** VCR cassettes for public venues (kalshi, polymarket, thegraph, defillama, fear_greed).

**Step C:** Implement 12 `NotImplementedError` stubs in UMI; USEI Betfair + Pinnacle adapters; UML: define
`ModelArtifactStore` protocol, remove direct UDC imports.

**T2 D5 = all 7 repos green.** Do NOT start T3 until all T2 pass D5.

### Tier 3 — UDC (after T0+T1+T2 green)

Same A → B → C → D1–D5:

**Step A:** Replace `CloudTarget/get_config` imports from UTS with UCLI equivalents; remove `unified-trading-services`
from `pyproject.toml`.

**Step C rename:** Add `unified_domain_client/` re-export; update all 14 services + T2 libs; delete old import path;
rename GitHub repo + AR packages + Cloud Build triggers.

**T3 D5 = Phase 2 complete.** Phase 3 starts only after T3 D5 passes.

---

## Done Criteria

- [ ] `bash scripts/setup.sh --check` passes in all 58 repos
- [ ] Import smoke test passes in all 58 repos (51 Python + 7 TS verified via setup.sh)
- [ ] Setup logic deduplicated: quality-gates.sh no longer duplicates venv/deps bootstrap (Round 0)
- [ ] Global violation sweep committed (Round 1+2) to all 58 repos
- [ ] Large-file SRP splits committed (Round 3) to all affected repos
- [ ] All 8 T0 repos pass D5 full quickmerge
- [ ] Integration Layer 0 tests pass (AC↔UIC schema alignment)
- [ ] UTS (T1) passes D5
- [ ] All 7 T2 repos pass D5
- [ ] UDC (T3) passes D5
- [ ] UDC has zero `unified-trading-services` deps
- [ ] UMI has zero UDC deps
- [ ] MEL has zero inter-library deps
- [ ] UTS rename cascade complete: all 14 services + 7 T2 libs use new import names
- [ ] `rg` for any old names returns zero hits across all 57 repos

---

## Key Files

- `unified-trading-pm/plans/active/phase2_library_tier_hardening.plan.md` — full task list
- `unified-trading-pm/workspace-manifest.json` — repo registry
- `unified-trading-/codex/05-infrastructure/unified-libraries/LIBRARY-DEPENDENCY-MATRIX.md` — tier rules
- `unified-trading-/codex/04-architecture/TIER-ARCHITECTURE.md` — full tier architecture
- `unified-trading-/codex/06-coding-standards/quality-gates.md` — QG template
- `unified-trading-/codex/06-coding-standards/setup-standards.md` — setup.sh documentation (includes isolated mode,
  fresh env, AGENTS.md)
- `unified-trading-pm/scripts/setup.sh` — setup.sh SSOT template (supports `--isolated` for standalone repos)
- `unified-trading-pm/scripts/workspace-bootstrap.sh` — full workspace bootstrap for fresh VMs
- `unified-trading-pm/templates/AGENTS.md` — per-repo caveats template for agents/developers
- `.cursor/rules/delete-deprecated.mdc` — no backward compat, delete old code
- `.cursor/rules/mandatory-setup-sh.mdc` — every repo must have setup.sh
