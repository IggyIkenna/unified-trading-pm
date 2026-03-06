---

name: Citadel Standard Production Readiness — D+ Remediation
status: active
overview: "Remediation plan for the 10-agent Citadel Standard Architecture production readiness audit (Grade D+, 6.2/10).\n\
 \ Addresses all P0 blocking and P1 high-priority violations with clear fix guidelines.\n\n ## Audit Summary (2026-03-06)\n\
 \ - **Grade:** D+ (6.2/10)\n - **Method:** 10 parallel agents across 60+ repos\n - **Scope:** Architecture, security,\
 \ code quality, schema governance, configuration, testing, error handling, data quality, dependencies, anti-patterns\n\n\
 \ ## Non-Contradiction Invariants (MUST NOT violate)\n - Tier DAG: T0→T1→T2→T3→services; no service imports service\n\
 \ - UAC must NOT import UIC or any service (T0 leaf)\n - No os.getenv for secrets; use get_secret_client().get_secret()\n\
 \ - No empty fallbacks (os.getenv('KEY', '')); fail fast\n - Quickmerge always: bash scripts/quickmerge.sh \"message\"\
 \ — never git push directly\n - basedpyright: timeout 120 basedpyright <source_dir>/ — NEVER basedpyright . or basedpyright\
 \ (no args)\n - No backward-compat shims; no git reset --hard in scripts/docs\n - Schema: UAC external venue schemas;\
 \ UIC domain/<service>/ for service output schemas\n\n ## Stream Ordering\n Phase 1 (P0): Streams 1–8 — blocking; run\
 \ in parallel where independent.\n Phase 2 (P1): Streams 9–18 — after P0 merges; parallel where possible.\n All streams\
 \ gate on: bash scripts/quickmerge.sh passes in target repo.\n\n ## Fix Guideline Pattern (every stream)\n SCAN → FIX\
 \ → VERIFY → QG\n - SCAN: ripgrep/command to find violations\n - FIX: exact pattern or code change\n - VERIFY: command\
 \ that returns zero hits when done\n - QG: bash scripts/quickmerge.sh \"message\" passes"
todos:

- id: p0-stream1-tier-dag-uac-instruments
  content: 'P0 Stream 1 — Tier DAG: UAC importing instruments_service

  SCAN: rg ''instruments_service|from instruments_service'' unified-api-contracts/ --type py --glob ''!.venv\*''

  FIX: Move test to unified-internal-contracts/tests/. UAC is T0 leaf.

  VERIFY: rg returns zero hits

  QG: bash scripts/quickmerge.sh "fix(p0-stream1): remove UAC→instruments_service tier violation"'
  status: pending

- id: p0-stream2-ui-service-separation
  content: 'P0 Stream 2 — UI-Service Separation: visualizer-ui in execution-service

  SCAN: ls execution-service/visualizer-ui/

  FIX: Extract to standalone repo. Per ui-service-separation.mdc.

  VERIFY: visualizer-ui/ gone from execution-service

  QG: bash scripts/quickmerge.sh "feat(p0-stream2): extract visualizer-ui"'
  status: pending

- id: p0-stream3-os-getenv-api-keys
  content: 'P0 Stream 3 — Security: os.getenv for API keys in tests

  SCAN: rg "os\.getenv\(.\*API_KEY|API_SECRET" execution-service/tests/

  FIX: get_secret_client().get_secret() or mock. Per instruments-domain-and-api-keys.mdc.

  VERIFY: zero hits

  QG: bash scripts/quickmerge.sh "fix(p0-stream3): replace os.getenv API keys"'
  status: pending

- id: p0-stream4-any-types-reportany
  content: 'P0 Stream 4 — Code Quality: Any / dict[str, Any]

  SCAN: basedpyright execution_service/ | grep Any

  FIX: TypedDict/Pydantic at boundary; cast() for third-party. NEVER type: ignore.

  VERIFY: Any errors 0 or in QUALITY_GATE_BYPASS_AUDIT.md

  QG: bash scripts/quickmerge.sh "fix(p0-stream4): replace Any types"'
  status: pending

- id: p0-stream5-bare-except-exception
  content: 'P0 Stream 5 — Code Quality: bare except / except Exception

  SCAN: rg ''except\s*:|except Exception.*pass'' --type py --glob ''!**/tests/**''

  FIX: except Exception as e: logger.error(...); raise. Or @handle_api_errors.

  VERIFY: zero bare except

  QG: bash scripts/quickmerge.sh "fix(p0-stream5): replace bare except"'
  status: pending

- id: p0-stream6-validate-timestamp-alignment
  content: 'P0 Stream 6 — Schema: missing validate_timestamp_date_alignment

  SCAN: ml-training, pnl-attribution, position-balance-monitor, features-sports write paths

  FIX: validate_timestamp_date_alignment(df, date=...) before writer.write(). Per schema-service-owned.mdc.

  VERIFY: each write path has validation

  QG: bash scripts/quickmerge.sh "fix(p0-stream6): add validate_timestamp_date_alignment"'
  status: pending

- id: p0-stream7-basedpyright-no-args
  content: 'P0 Stream 7 — Anti-Patterns: basedpyright . or no args

  SCAN: rg ''basedpyright\s+\.|basedpyright\s*$'' --glob ''*.md'' --glob ''\*.sh''

  FIX: timeout 120 basedpyright <source_dir>/. Per basedpyright-safety.mdc.

  VERIFY: zero hits

  QG: bash scripts/quickmerge.sh "fix(p0-stream7): replace basedpyright ."'
  status: pending

- id: p0-stream8-git-reset-hard
  content: 'P0 Stream 8 — Anti-Patterns: git reset --hard in scripts/docs

  SCAN: rg ''git reset --hard'' --glob ''_.md'' --glob ''_.sh''

  FIX: Remove. Use quickmerge --dep-branch. Per never-revert-local-changes.mdc.

  VERIFY: zero hits (exclude rule docs)

  QG: bash scripts/quickmerge.sh "fix(p0-stream8): remove git reset --hard"'
  status: pending

- id: p1-stream9-google-cloud-deployment
  content: 'P1 Stream 9 — Architecture: google.cloud in deployment-api/service

  SCAN: rg ''from google\.cloud'' deployment-api/ deployment-service/

  FIX: get_storage_client() from UCI. Per cloud-agnostic.mdc.

  VERIFY: zero outside UCI providers

  QG: bash scripts/quickmerge.sh "fix(p1-stream9): replace google.cloud"'
  status: pending

- id: p1-stream10-empty-fallbacks
  content: 'P1 Stream 10 — Configuration: empty fallbacks

  SCAN: rg "getenv\([^)]+,\s\*[''\"]{2}\)" --type py --glob ''!**/tests/**''

  FIX: Remove fallback; config required field. Fail fast.

  VERIFY: zero hits

  QG: bash scripts/quickmerge.sh "fix(p1-stream10): remove empty fallbacks"'
  status: pending

- id: p1-stream11-requests-in-async
  content: 'P1 Stream 11 — Code Quality: requests in async

  SCAN: async functions with requests.get/post

  FIX: aiohttp. Per async-http-aiohttp.mdc.

  VERIFY: no requests in async

  QG: bash scripts/quickmerge.sh "fix(p1-stream11): replace requests with aiohttp"'
  status: pending

- id: p1-stream12-naive-datetime
  content: 'P1 Stream 12 — Code Quality: datetime.now()/utcnow()

  SCAN: rg ''datetime\.now\(\)|datetime\.utcnow\(\)'' --type py

  FIX: datetime.now(timezone.utc). Per utc-datetime.mdc.

  VERIFY: zero hits

  QG: bash scripts/quickmerge.sh "fix(p1-stream12): naive datetime to UTC"'
  status: pending

- id: p1-stream13-service-models-to-uic
  content: 'P1 Stream 13 — Schema: domain schemas in service models.py

  SCAN: 9 services with BaseModel in models.py

  FIX: UIC domain/<service>/output.py. Per service-domain-schema-in-uic.mdc.

  VERIFY: no cross-repo schemas in service

  QG: bash scripts/quickmerge.sh "feat(p1-stream13): migrate schemas to UIC"'
  status: pending

- id: p1-stream14-adapter-models-to-uac
  content: 'P1 Stream 14 — Schema: adapter \_\*\_models in interface repos

  SCAN: UMI, sports-execution adapters

  FIX: UAC unified_api_contracts_external/<venue>/schemas.py. Per adapter-models-belong-in-uac.mdc.

  VERIFY: zero \_\*\_models in interfaces

  QG: bash scripts/quickmerge.sh "feat(p1-stream14): migrate adapter models to UAC"'
  status: pending

- id: p1-stream15-os-getenv-production
  content: 'P1 Stream 15 — Configuration: os.getenv in production

  SCAN: rg ''os\.getenv|os\.environ\.get'' --glob ''!**/tests/**'' --glob ''!**/scripts/**'' -l

  FIX: UnifiedCloudConfig or get_secret_client. Document exceptions.

  VERIFY: zero in SOURCE_DIR

  QG: bash scripts/quickmerge.sh "fix(p1-stream15): replace os.getenv"'
  status: pending

- id: p1-stream16-files-over-900-lines
  content: 'P1 Stream 16 — Anti-Patterns: files >900 lines

  SCAN: find . -name ''\*.py'' -exec wc -l {} \; | awk ''$1>900''

  FIX: Split per file-splitting-guide.md. Production first.

  VERIFY: no prod .py >900

  QG: bash scripts/quickmerge.sh "refactor(p1-stream16): split files"'
  status: pending

- id: p1-stream17-todo-fixme-to-issues
  content: 'P1 Stream 17 — Anti-Patterns: TODO/FIXME in production

  SCAN: rg ''TODO|FIXME'' --type py --glob ''!**/tests/**'' -l

  FIX: GitHub issue + # ISSUE-123. Or remove.

  VERIFY: each has ref or removed

  QG: bash scripts/quickmerge.sh "chore(p1-stream17): TODO to issues"'
  status: pending

- id: p1-stream18-summary-status-files
  content: 'P1 Stream 18 — Anti-Patterns: _\_SUMMARY.md / _\_STATUS.md

  SCAN: find . -name ''_\_SUMMARY.md'' -o -name ''_\_STATUS.md''

  FIX: Delete. Per no-summary-docs.mdc.

  VERIFY: zero hits

  QG: bash scripts/quickmerge.sh "chore(p1-stream18): remove summary files"'
  status: pending
