# Quality Gate Bypass Audit

<!-- e2e version-bump flow test -->

## 1. PM Repo — Non-Standard Structure (Audited Exception)

**unified-trading-pm** is not a deployable package. It is the project management, docs, and scripts canonical repo.
Quality gates apply PM-specific handling:

| Check               | Standard (deployable package)           | PM Exception                                           |
| ------------------- | --------------------------------------- | ------------------------------------------------------ |
| **basedpyright**    | `REPO_MODULE/` (e.g. `my_service/`)     | `scripts/ github-integration/` — no Python package dir |
| **cloudbuild.yaml** | Required                                | Skipped — PM is not deployed                           |
| **coverage**        | `--cov=REPO_MODULE --cov-fail-under=70` | `--cov=scripts/manifest --cov-fail-under=0`            |
| **SOURCE_DIRS**     | `REPO_MODULE/ tests/`                   | `scripts/ github-integration/ tests/`                  |

**Rationale:** PM hosts automation scripts, cursor rules, workspace manifest, and plans — not a Cloud Run service or
installable library. Documented in `.cursor/rules/pm-repo-context.mdc`.

---

## Version Policy Exemption

file: pyproject.toml field: version value: "1.2.0" justification: PM is internal devops infrastructure, never published
to PyPI. Version tracks internal CI/CD evolution independently of library semver policy. Pre-stable policy applies only
to published libraries. owner: platform-team status: PERMANENT_EXEMPTION

---

## 1.1 Version Policy Exception — `unified-trading-pm` at `1.0.0`

**Repo:** `unified-trading-pm` **Version in manifest:** `1.0.0`

**Justification:** `unified-trading-pm` is a documentation and orchestration repo — it is NOT a deployable Python
package (no Cloud Run service, no installable library). The `versions_policy` rule (all versions `<1.0.0` until first
stable quickmerge CI pass) applies exclusively to deployable service and library packages. `unified-trading-pm` version
`1.0.0` denotes stable SSOT status — it is the single source of truth for workspace manifest, cursor rules, plans, and
PM scripts. Version `1.0.0` here signals maturity of the SSOT role, not a Python package release milestone. This is
exempt from the pre-1.0.0 policy.

**Audit trail:** Added 2026-03-04 per PM-F2 audit finding.

---

## 2. Excluded Paths — Legacy and Tooling Directories

The following directories are excluded from the file-size and function-size quality gate checks. They are PM tooling and
archive files, not deployable code.

| Path                  | Reason                                                                                                                                                                                                                                                                                                |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `docs/archive/`       | Historical documentation archive. `models.py` (3621L) is a snapshot of a deprecated sports-features domain model kept for reference only. Not deployed, not imported.                                                                                                                                 |
| `github-integration/` | One-time and ongoing PM automation scripts for GitHub Projects/Issues workflows. These are long single-file scripts by design (no shared module), and they are not deployed or imported as Python packages. Max file `04-create-service-epics.py` (1167L) is a single-script GitHub API orchestrator. |
| `rd-tax-credits/`     | R&D tax credit export utilities. `export-script.py` `main()` is 168L (exceeds 100L function limit) — it is a one-time reporting tool with a large argparse block followed by a reporting loop. Not deployed, not imported as a package.                                                               |

**Audit trail:** Added 2026-03-04. File/function size exclusions for `docs/archive/`, `github-integration/`,
`rd-tax-credits/` confirmed 2026-03-06.

---

## 2.1 File Size Exceptions — Explicitly Excluded Paths

See §2 above for `docs/archive/`, `github-integration/`, and `rd-tax-credits/` exclusions. Confirmed 2026-03-06.

## 2.2 Ruff Exceptions

None.

---

## 2.5 Bandit `#nosec` Suppressions

| File                                                                   | Rule | Suppression    | Justification                                                                                                                                                                                       |
| ---------------------------------------------------------------------- | ---- | -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `scripts/manifest/generate_canonical_dependency_manifest.py:172`       | B314 | `# nosec B314` | `ET.fromstring()` is called on SVG content generated entirely by our own `generate_svg()` function — not on untrusted external input. Used only to validate well-formedness before writing to disk. |
| `scripts/manifest/generate_workspace_dag.py:394`                       | B314 | `# nosec B314` | Same as above — SVG is generated internally and validated before disk write.                                                                                                                        |
| `scripts/repo-management/create-github-repos-and-collaborators.py:103` | B310 | `# nosec B310` | `urllib.request.urlopen` is called with a hardcoded `https://api.github.com/` URL via a `Request` object. No user-controlled URL schemes possible.                                                  |
| `scripts/repo-management/ensure-repo-collaborators.py:104`             | B310 | `# nosec B310` | Same as above — hardcoded GitHub API https endpoint only.                                                                                                                                           |
| `scripts/validate-manifest-dag.py:112`                                 | B310 | `# nosec B310` | `urllib.request.urlopen` to hardcoded `https://api.telegram.org/` — Telegram alert on cycle detection. No user-controlled URL.                                                                      |

**Audit trail:** Added 2026-03-04. validate-manifest-dag.py B310 added 2026-03-13.

## 2.3 Basedpyright Exceptions

| File                                                    | Line | Code                                                   | Justification                                                                                                               |
| ------------------------------------------------------- | ---- | ------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| `scripts/manifest/fix-internal-dependency-alignment.py` | 23   | `import tomli_w  # type: ignore[reportMissingImports]` | `tomli-w` is in PM dependencies; Act/CI type-check env may not resolve it. Runtime works; type ignore documents the bypass. |

**Audit trail:** Added 2026-03-04 (dependency governance S4). reportAny errors fixed 2026-03-06 (312 → 0).

---

## 2.6 Quality Gate Check — `grep -v` Exclusions

Some checks produce false positives against files whose content is pattern-search code (not violations). These
exclusions are applied in `scripts/quality-gates.sh`:

| Check                          | Excluded File                                        | Reason                                                                                                                                                                                         |
| ------------------------------ | ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Bare `except:`                 | `scripts/validation/find-coding-violations.py`       | This script searches for `except:` as a string literal in its rg command arguments. The rg match is on the script source text of the search pattern, not on a real bare except.                |
| Deep unified lib imports       | `scripts/validation/find-coding-violations.py`       | This script contains example import strings like `"from unified_trading_services.core.config import"` as search pattern literals, not as actual imports.                                       |
| Naive datetime                 | `scripts/validation/find-coding-violations.py`       | This script searches for `datetime.now()` / `datetime.utcnow()` as string literals in its rg command arguments. The match is on the search pattern, not on actual naive datetime usage.        |
| TypedDict / `Any`              | `scripts/validation/find-coding-violations.py`       | This script defines `CheckResult` as an internal validation struct (TypedDict) for its own output format. Not a cross-repo contract; the script validates code patterns, not schema placement. |
| `GCP_PROJECT_ID`               | `scripts/propagation/rollout-quality-gate-checks.py` | This migration script contains `GCP_PROJECT_ID` as a sentinel string for the checks it REMOVES from target repos. It is the script that eliminates the violation, not a source of it.          |
| `GCP_PROJECT_ID` (BACK_COMPAT) | `scripts/propagation/rollout-quality-gate-checks.py` | Same script references `GCP_PROJECT_ID` (backward-compat alias) as a migration target string — the script removes this pattern from downstream repos.                                          |
| `pip install`                  | `scripts/agents/llm-agent-wrapper.sh`                | This shell script contains an `echo` statement displaying install instructions for users. It is documentation output, not an actual pip install invocation.                                    |
| `pip install` (self-match)     | `scripts/quality-gates.sh` itself                    | The rg command pattern `pip install` matches the line in the quality-gates.sh that runs the check. Excluded to prevent self-referential false positive.                                        |

**Audit trail:** Added 2026-03-04. find-coding-violations.py (naive datetime, TypedDict) and
rollout-quality-gate-checks.py (BACK_COMPAT) added 2026-03-06.

---

## 2.4 os.getenv() Exceptions — github-integration/ CI/CD Scripts

**Rule bypassed:** No `os.getenv()` — use `UnifiedCloudConfig` (codex §06 / `no-os-getenv` rule).

**Scope:** `github-integration/` scripts only. These are PM orchestration scripts that drive GitHub API workflows and
must authenticate via environment-injected tokens (e.g. `GITHUB_TOKEN`, `GH_TOKEN`). They run outside any cloud context
and cannot use `get_secret_client()`, which requires a live GCP runtime.

| File                                                                                      | Line | Call                                                 | Justification                                                                                            |
| ----------------------------------------------------------------------------------------- | ---- | ---------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `github-integration/scripts/utilities/create-all-projects.py`                             | 345  | `os.getenv("GITHUB_TOKEN")`                          | GitHub API token for project creation — must come from CI environment variable, no GCP runtime available |
| `github-integration/scripts/projects/initial-cleanup/utilities/check-codex-violations.py` | 894  | `os.getenv("GITHUB_REPO", ...)`                      | GitHub repo name for API calls — env var override pattern for local dev vs CI                            |
| `github-integration/scripts/core/02-run-diff-checker.py`                                  | 894  | `os.getenv("GITHUB_REPO", ...)`                      | GitHub repo name for API calls — env var override pattern for local dev vs CI                            |
| `github-integration/scripts/one-time/setup-cod-project-workflows.py`                      | 38   | `os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")` | GitHub API token with `GH_TOKEN`/`GITHUB_TOKEN` dual-fallback — standard GitHub Actions pattern          |

**Rationale:** `github-integration/` scripts are pure CI/CD automation that orchestrate GitHub Projects, issues, and
workflow triggers. They have no access to GCP Secret Manager (no service account, no ADC in the CI environment where
they run). Reading GitHub credentials from environment variables is the correct and intentional approach for this
architecture boundary. `UnifiedCloudConfig` and `get_secret_client()` are for deployed cloud services, not for PM
orchestration scripts.

**Architecture boundary:** This exception applies exclusively to `github-integration/` scripts. All other production
service and library code must use `UnifiedCloudConfig` (config values) or `get_secret_client()` (secrets/API keys).

**Audit trail:** Added 2026-03-04 per quality-gate failure analysis.

---

## 2.9 Broad `except Exception` — Manifest/Workspace Parsing Scripts

**Rule bypassed:** No `except Exception:` — use specific exception types.

**Scope:** The following scripts are excluded from the broad-except check:

- `scripts/check_external_dependency_alignment.py` — parses semver specifiers and pyproject.toml files; broad except
  catches malformed input
- `scripts/fix_external_dependency_alignment.py` — same as above
- `scripts/manifest/fix-internal-dependency-alignment.py` — parses imports from source files; broad except handles
  partial parses

**Rationale:** These are PM tooling scripts that parse external files (pyproject.toml, Python source). Parsing can fail
with many different exception types (syntax errors, encoding errors, malformed TOML). Using `except Exception: pass` or
`except Exception: return fallback` here is appropriate to maintain resilience — the scripts are best-effort tools, not
production services with SLAs. The "specific exception" rule applies to production services where silent failures are
dangerous.

**Additional:** `scripts/validate-manifest-dag.py` — `send_telegram_alert()` catches `Exception` so Telegram API
failures (network, timeout, HTTP errors) never block the DAG validation script. Alert delivery is best-effort.

**Additional:** `scripts/cicd/tier_c_promotion_gate.py` — `_overlay_firestore_ci_status()` catches `Exception` so
Firestore unavailability (SDK missing, no credentials, network error) never blocks the promotion gate. Falling back to
the manifest ci_status values on any error is the intended safe-default behaviour. Added 2026-06-11.

**Additional:** `scripts/cicd/promotion_lag_monitor.py` — `_write_firestore_promotion_lag()` catches `Exception` so a
missing Firestore SDK or absent credentials never blocks the lag monitor from running and alerting. The write is
explicitly best-effort; the monitor's core function (lag detection + alerting) is independent. Added 2026-06-11.

**Additional:** `scripts/repo-management/ci_failure_watcher.py` — `_write_firestore_ci_watcher()` catches `Exception` so
Firestore unavailability never blocks the CI watcher from scanning and paging. The write is explicitly best-effort.
Added 2026-06-11.

**Additional:** `scripts/cicd/reconcile_release_tags.py` — `_write_firestore_release_tags()` catches `Exception` so a
missing Firestore SDK or absent credentials never blocks the release-tag reconciler from creating tags. The write
(latest tag per repo → `repo_state/{repo}/release_tag`, so tag-readers query Firestore instead of the GitHub tags API)
is explicitly best-effort. Added 2026-06-11.

**Audit trail:** Added 2026-03-04. validate-manifest-dag.py added 2026-03-13.

---

## 2.7 Empty Dict/List Fallback — Manifest and Workspace Parsing Scripts

**Rule bypassed:** No `.get("key", {})` / `.get("key", [])` empty fallbacks.

**Scope:** The following script directories are excluded from the empty dict/list fallback check:

- `scripts/manifest/` — JSON manifest parsing (optional sections may be absent)
- `scripts/workspace/` — workspace manifest traversal
- `scripts/migration/` — migration scripts parsing structured JSON output
- `scripts/propagation/` — rollout scripts parsing quality gate result JSON
- `scripts/repo-management/` — repo management scripts parsing manifest JSON
- `scripts/check_external_dependency_alignment.py`, `scripts/fix_external_dependency_alignment.py`

**Rationale:** These scripts parse JSON manifest files where certain sections (`dependencies`, `repositories`,
`sources`) are genuinely optional. `.get("key", [])` returning an empty list when a key is absent is correct and
intentional — a missing section means "no items", not an error. The "fail fast" rule applies to API response fields and
config values in production services, not to manifest file traversal in PM tooling scripts.

**Audit trail:** Added 2026-03-04. ED/EL exclusions for scripts/manifest, workspace, migration, propagation,
repo-management confirmed 2026-03-06.

---

## 2.8 Import Inside Function — `scripts/manifest/sbom-store.py` (RESOLVED 2026-03-06)

**Rule bypassed:** No imports inside functions.

**Status:** RESOLVED. Import moved to top level with `try/except ImportError`; `get_storage_client is None` check
replaces `importlib.util.find_spec`. No bypass needed.

**Audit trail:** Added 2026-03-04. Resolved 2026-03-06.

---

## 2. Dependency Governance Audit — Known uv.lock / Path Dep Issues (S4.6)

**Audit:** dependency_governance.plan.md (2026-03-05)

| Repo                                       | Issue                                                        | Resolution                                                                    |
| ------------------------------------------ | ------------------------------------------------------------ | ----------------------------------------------------------------------------- |
| unified-trading-library                    | uv lock fails: `unified-cloud-services[aws]` not in registry | Dep references external package; add to workspace-constraints or use path dep |
| features-cross-instrument-service          | uv lock fails: `unified-cloud-interface` path dep            | Run `uv lock` from workspace root with path deps installed                    |
| system-integration-tests                   | `.venv` invalid (no Python executable)                       | Remove `.venv` and run `uv sync` from workspace                               |
| 20 internal manifest↔pyproject mismatches | fix-internal-dependency-alignment.py needs tomli_w           | `uv pip install tomli-w` then run fix script                                  |

**Rationale:** Path deps and workspace-local packages require workspace context for resolution. Documented for S4 audit
traceability.

## basedpyright-baseline: `.basedpyright-baseline.json` (33 pre-existing errors)

**Added:** 2026-03-10 — typecheck fix pass **Status:** JUSTIFIED — untyped third-party dependencies; target is zero when
stubs become available **Errors suppressed:** 33

**Reason:** Script automation tools: json.loads()/yaml.safe_load() return Any by design (dynamic data); argparse
namespace attrs typed as Any; subprocess results Any. Root cause: these scripts parse dynamic external data where Any is
inherent.

**Scope:** All errors in `.basedpyright-baseline.json` are from untyped third-party libraries or unresolvable import
chains in workspace venv context — NOT architectural violations. No `reportAny` errors in first-party code are
suppressed.

**Target:** Remove baseline when upstream type stubs are available.
