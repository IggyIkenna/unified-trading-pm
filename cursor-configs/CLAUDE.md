# Unified Trading System — Claude Code Instructions

> **Lean index** of workspace rules. Each rule has a 1-line essence + a pointer to its full SSOT.
> When a rule applies, **read the SSOT pointer** — don't act from memory.
>
> Trim 2026-05-14: was ~999 lines / ~58KB; now ~400 lines. Per context-fill optimization plan.
>
> **Size budget**: target ≤400 lines / 25KB. Hard cap 1500 / 90KB (review-blocking past that). When budget breached, push to codex SSOT + leave 1-line pointer here.

---

## Model Tier Selection — Sonnet 4.6 (default) vs Opus 4.7 (escalation only)

**Default: Sonnet 4.6 / thinking: medium.** Escalate deliberately — not by default.

Three axes declared per slot and per spawn prompt:

- `model_tier: sonnet-doable | opus-required` — Opus only for main orchestrator, cross-repo architecture, >200k context
- `thinking: medium | high | max` — max always requires Opus; medium on Opus is always wrong
- Sub-agent Agent tool calls MUST set `model="sonnet"|"opus"` explicitly — never inherit

**Self-check at every task start (MANDATORY)**: read running model + declared tier + thinking. Sonnet on opus-required → STOP. Opus on sonnet-doable → flag + proceed. Thinking mismatch → HARD STOP.

SSOT: `codex/06-coding-standards/model-tier-selection.md`.

---

## Environment: Venv Split (SSOT: `cursor-rules/venv-usage-ssot.mdc`)

| Use case                  | Venv                        | Command                                                      |
| ------------------------- | --------------------------- | ------------------------------------------------------------ |
| **Quality gates / tests** | Repo `.venv`                | `cd <repo> && bash scripts/quality-gates.sh` — no activation |
| **IDE / general Python**  | Workspace `.venv-workspace` | `source ${WORKSPACE_ROOT}/.venv-workspace/bin/activate`      |

**Never** run `pytest` directly — wrong venv. Always `quality-gates.sh`.

---

## Master Plan — Live DeFi Trading by 2026-05-23

Two DeFi archetypes (`carry_staked_basis` + `arbitrage_price_dispersion`) live on a real wallet ≥7 days by 2026-05-23.

- **Working plan**: `plans/active/master_to_live_defi_2026_05_23.md`
- **Codex SSOT**: `codex/10-audit/MASTER_READINESS_LIVE_DEFI_2026_05_23.md`
- **Principle**: doc → plan → code. Drift between any pair is review-blocking. Readiness: 7 groups / 23 items (A-G).
- **Parallel workstreams ACTIVE**: TradFi (`epics/tradfi_master_2026_05_07.md`), Sports (`epics/sports_master_2026_05_07.md`), Predictions (`epics/predictions_master_2026_05_07.md`) — separate codepaths, not blocked by DeFi gate. Allocate agent slots to these tracks.

---

## Rules: Read Before Coding

1. `.cursorrules` — workspace standards (uv not pip, quickmerge not git push, etc.)
2. `.cursor/rules/no-empty-fallbacks.mdc` — no try/except fallback imports
3. `.cursor/rules/no-type-any-use-specific.mdc` — no Any types
4. `unified-trading-pm/codex/06-coding-standards/README.md` — coding standards
5. `unified-trading-pm/plans/PLAN_FORMAT.md` — plan format; Cursor checkboxes (`- [x]` / `- [ ]`) required
6. **Asset-group vocabulary**: `asset_group` (not `category`). CLI `--asset-group`, envs `VM_ASSET_GROUP`/`MDPS_ASSET_GROUP`. Keys lowercase: `cefi`/`defi`/`tradfi`/`sports`/`prediction`. GCS hive-key: `asset_group=` canonical. Plan: `plans/active/venue_axis_asset_group_vocabulary_2026_04_25.md`.

---

## Key Rules (Quick Reference)

### Dependencies + builds

- Flat deps only — one `[project.dependencies]` per `pyproject.toml`. No extras.
- `uv pip install` not `pip install`.
- Dockerfiles: `ARG PROJECT_ID` + `FROM --platform=linux/amd64 asia-northeast1-docker.pkg.dev/${PROJECT_ID}/unified-trading-library/unified-trading-library:latest`

### Git discipline

- `bash scripts/quickmerge.sh "msg" --agent` not `git push` for promotion-to-main. Always `--agent` in Claude Code.
- Dirty deps → commit + push directly to `live-defi-rollout`. DO NOT quickmerge when dep repos dirty.
- Two-pass: Pass 1 = `bash scripts/quality-gates.sh`. Pass 2 = `quickmerge --agent` (lint/format/typecheck/codex, no tests).
- `--dep-branch` is human-only.

### Imports + types

- `from unified_trading_library.events import setup_events, log_event` — no fallbacks.
- `basedpyright` not `pyright`; always `run_timeout 120 basedpyright <source_dir>/`.
- No `os.getenv()` — use `UnifiedCloudConfig`. No `# type: ignore`. No `try/except ImportError`.
- `logger.warning("%s", _err.message)` not `logger.warning(_err.message)`.
- No hardcoded `"/tmp"` — use `tempfile.gettempdir()`. SSOT: `codex/06-coding-standards/quality-gates.md`.

### Service architecture

- **instruments-service** for reference data, not MTDS. MTDS is market data only.
- Shard-level failure isolation — no `raise` inside per-venue/per-shard loops. SSOT: `codex/04-architecture/shard-level-failure-isolation.md`.
- Every adapter MUST classify errors via UAC `classify_venue_error()` + emit `ADAPTER_FETCH_FAILED`.
- Service CLIs: `--operation` (what) `--mode` (batch/live) `--asset-group` (domain). SSOT: `codex/06-coding-standards/cli-convention.md`.

### Manifest + honest absence

Manifest v5+: 4-state `capture_status` (`captured`/`empty_confirmed`/`attempted_failed`/`expected_unattempted`). Three categories of "missing": (1) expected gap → `record_empty(reason=<typed>)`, (2) unexpected gap → `DependencyError(fail_fast=True)`, (3) schema-drift bug → RAISE LOUD. Never emit silent placeholders.

- 17 `EXPECTED_*` reasons + `SOURCE_RETURNED_ZERO` in UAC `EMPTY_CONFIRMED_REASONS`. Blank reason → `LegacyBlankErrorReasonError`. Enum: `unified_api_contracts.canonical.crosscutting.honest_coverage.EmptyConfirmedReason`.
- Cluster validation MANDATORY at `record_captured()` for bundled data_types. QG STEP 5.64 enforces. UTL raises `MissingClusterValidationError` if kwargs absent.
- `available_at` is per-row write-time. UTL `record_captured` asserts presence internally.
- Service-output emission: every publish path through `_resolve_policy_output_data_type` + `_publish_emission_check`. SSOT: `codex/02-data/service-output-emission-semantics.md`.

SSOT: `codex/02-data/availability-manifest-and-data-status.md` + `codex/02-data/honest-absence-downstream-handling.md`.

### Shard-granularity SSOT (CRITICAL)

Shard atom MUST be identical across writer atomicity, manifest row key, data-status display, downstream pre-flight gate, deployment-UI drilldown. Drift = silent correctness bug. 4-pillar validation: row count > 0 OR `record_empty`; NaN ratio < threshold; schema matches contract; cluster coverage ≥ expected. SSOT: `plans/epics/infrastructure_master_2026_05_07.md`.

### Live = batch (CRITICAL)

Live and batch are operational modes of the SAME pipeline. Identical schemas, data_types, fields. Banned: separate live-only data_types; distinct field sets; deriving `available_at` at read-time. SSOT: `plans/active/writegate_honest_coverage_endtoend_2026_05_06.md`.

### Bucket-name SSOT

Every bucket lookup via `unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(...)` — never inline `gs://` f-string. `deployment-service/configs/cloud-providers.yaml` is canonical. QG STEP 5.69 enforces. SSOT: `plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md`.

### Other key rules

- **Sports GCS paths**: `unified_api_contracts.sports.candidate_parquet_paths()` in `unified_api_contracts/canonical/domain/sports/gcs_paths.py`. Coverage: `clip_dates_to_source_coverage()` + `is_in_known_gap()`.
- **VIX 15m**: Barchart preload + Yahoo rolling 60d + honest gap. UAC constants in `registry/data_source_continuity.py`.
- **Manifest phantom audit**: `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group X --dry-run`. Do NOT write empty parquets to mask phantoms.
- **VM tarball**: `bash deployment-service/scripts/vm/create-code-tarballs.sh`. SSOT: `codex/05-infrastructure/vm-tarball-deployment.md`.
- **VM launchers**: every `gcloud compute instances create` in `deployment-service/scripts/vm/`. VM naming: first segment must be in `VM_PREFIX_TO_BUCKET` in `vm_zombie_watchdog.py`.
- **No fire-and-forget VM launches (CRITICAL)**: STARTED within 60s + ≥1 progress/hour + STOPPED/FAILED at exit.
- **Per-VM shard isolation**: `VM_NAME=<unique-tag>` + `MANIFEST_PER_VM_SHARDS=true`. QG STEP 5.66 enforces.
- **Temporary state must have a named successor plan** in `## Temporary states + their canonical follow-up plans`.

### Two teammates × multiple parallel agents (CRITICAL)

Harsh AND Ikenna both run parallel agents. Untracked files / dirty mid-edit / recent remote commits = someone else's in-flight work. **Do not touch files outside your clear context.**

- Never `git checkout origin/<branch> -- .` (dumps remote work) or `git checkout -- <file>` on foreign-owned dirty files (UNRECOVERABLE).
- Right recovery: (a) scope tool to YOUR files; (b) stash foreign files before tool runs; (c) accept you can't auto-fix foreign code.
- **Untracked file in a dep repo = NOT YOURS.**
- QG fails on file you don't own → tell the user.

### Clear context = implement, don't ask

When plan / SSOT name the canonical approach, **ship it**. Don't apply when destructive, foreign files involved, or plan says "AWAITING USER DIRECTION."

---

## Service Infrastructure Requirements (QG-Enforced as ERRORS)

- **STEP 5.61** `ServiceBootstrap(...)` must appear in service source — handles STARTED/STOPPED/FAILED.
- **STEP 5.62** `api/main.py` with `make_health_router` from UTL + `data_freshness` callback.
- **STEP 5.34** `config_reloaders.py` uses typed config class — never `object` or `getattr(service_config, ...)`.
- **Schema provenance** — domain types from UAC (or `unified_api_contracts.internal`) — no local definitions.
- **API key hot-reload** — `ApiKeyReloader` from UTL, not one-shot `validate_api_keys_for_venues()`. SSOT:
  `codex/06-coding-standards/config-reloader-pattern.md`.

---

## DeFi Execution Architecture

Pointer chain. Full specs in codex:

- **Credential convention**: `codex/04-architecture/interface-credential-convention.md`. Trade: `get_order_adapter(venue, ...)`. DeFi: `connector.connect(config={...})`. Sports: `adapter(credentials={...})`.
- **RPC URL templates**: `CHAIN_RPC_TEMPLATES` in UAC `registry/capability_declarations/_defi.py`.
- **Flash loan receiver**: `deployment-service/contracts/FlashLoanReceiver.sol`. SSOT: `codex/04-architecture/flash-loan-receiver.md`.
- **Contract registry**: `unified_trading_library/config_interface/testnet_contracts.py` `TestnetContractRegistry` — validates `config/testnet_contracts.yaml` at load.
- **Uniswap live swap**: `UniswapConnector.swap_exact_input()` via SwapRouter02 `0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45`.
- **DeFi error classification**: 13 codes in UAC `unified_api_contracts.canonical.crosscutting.errors.defi.DefiErrorCode`. Routes on FAIL/RETRY/SKIP prefix.
- **DeFi pipeline**: instruments-service → MTDS → features-onchain → strategy → execution.
- **Removed providers** (do NOT reference): Elysium, Arkham, Bloxroute, Infura.
- **Pyth UNBANNED 2026-05-06** for Solana on-chain price feeds. Solana-only; other chains use Chainlink.
- **DeFi + CeFi hybrid (CRITICAL)**: DeFi = long/stake/lend leg (on-chain); hedge/short leg runs on CeFi perp venues. SSOT: `codex/09-strategy/architecture-v2/archetypes/`.
- **Custody**: Copper + CEFFU are June-1. May-23 ships on `CLOUD_KMS_ENCRYPTED`. SSOT: `codex/04-architecture/custody-providers.md`.

---

## Version / Workflow / Plan Governance

- **Version graduation**: `feat!` on 0.x.x = MINOR. **NEVER bump manually** — semver-agent handles all. Graduate: `gh workflow run request-major-bump.yml --repo IggyIkenna/<repo> -f proposed_version="1.0.0"` → comment `/approve`. Post-1.0.0: `feat!` = MAJOR.
- **PM/Codex fast-path**: plans/docs/cursor rules (`*.md`, `*.mdc`) → PR targets **main**. Scripts/workflows → PR targets **staging**.
- **Plan locking**: `locked_by: live-defi-rollout` + `locked_since: <date>` prevents archival without `[unlock-plan]` in commit. Agents may ASK to unlock; never unlock autonomously.
- **Plan archival (HARD RULE)**: scan for DEFERRED items; verify operations ran in production; migrate deferred items to active home with `**MIGRATED FROM:**`; banner archived plan with `## Deferred work — migrated to:`; update CLAUDE.md/codex if workspace contract changed.
- **Workflow templates**: SSOT `unified-trading-pm/scripts/workflow-templates/`. Never edit per-repo copies — edit PM template + run `rollout-workflow-templates.sh`.
- **Force-sync warning**: `admin-force-sync-all-to-main.sh` overwrites remote main — can revert semver-agent bumps. Run `run-version-alignment.sh` first.

---

## Testing + Local Development

**Tests**: credential-free (`CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true`). GCP emulators: PubSub `localhost:8085`, Storage `localhost:4443`, BQ `localhost:9050`. AWS: `@mock_aws` (moto). `pytest --block-network`. DeFi integration: Tenderly fork fixtures in `execution-service/tests/defi_execution/integration/conftest.py`. Cassette parity: `cd unified-api-contracts && pytest tests/test_cassette_schema_parity.py` (every commit).

**Local dev**: deployment-stack (ports 8004/5183): `bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh [--api|--ui|--stop]`. Tier-based: `cd unified-trading-system-ui && bash scripts/dev-tiers.sh --tier 0`. Port registry: `unified-trading-pm/scripts/dev/ui-api-mapping.json`. Full guide: `codex/08-workflows/local-dev.md`.

**Multi-repo**: each subdirectory is independent git repo. Only commit to target repo. Never `basedpyright .` from workspace root — always per-repo with timeout.

---

## Batch = Live (CRITICAL)

Batch + live use SAME code path. Only difference: execution fills. Never build standalone backtest engines; never distinguish live/batch strategies; never build asset-group-specific backtest engines. 99% of code path identical.

---

## System-First Architecture

Look at the existing system before implementing. Key repo map: events → UTL · schemas → UAC · cloud → unified-cloud-interface · market data → MTDS · execution → execution-service · reference data → instruments-service (`URDI` is a phantom name — does NOT exist) · UI → `unified-trading-system-ui` (consolidated) + `deployment-ui` + `user-management-ui`.

**UAC import rule**: `from unified_api_contracts.{domain} import ...` only. Never `canonical.*` or `normalize_utils.*`. SSOT: `imports/uac-import-surface-enforcement.mdc`. Full decision tree: `SUB_AGENT_MANDATORY_RULES.md` §0.

---

## Plan Format + Filename Convention

Every todo: `- [x] [SCRIPT] P0. Description...`. SSOT: `plans/PLAN_FORMAT.md`.

3-layer model: cutover master → epics (`plans/epics/*.epic.md`) → granular sub-plans (`plans/active/*.md`). Extensions: `plans/active/` = `<slug>.md`; `plans/archive/` = keep existing (DO NOT rename); `plans/ai/` = `<slug>.plan.md`. SSOTs: `plans/epics/README.md` + `plans/PLAN_FORMAT.md`.

---

## Capture Discoveries As Plan Todos Immediately (HARD RULE)

Every side-discovery MUST go into a plan todo at the moment it surfaces. Tag P0-P3 + `**DEFERRED**`/`**NICE-TO-HAVE**` + provenance. **Never auto-memory. Never chat summary.**

End-of-cycle: every deferral in your summary MUST already be a `- [ ]` plan todo. Grep to verify — no match → STOP, add todo first. Reviewers reject summaries with grep-miss deferrals.

---

## Active Plan Inventory + Done-vs-Left Dashboard

Run: `python3 unified-trading-pm/scripts/plans/regenerate_active_plan_inventory.py`. Cadence: morning + EOD + before planning decisions (slot 1 main, both sides). Writes between `<!-- AUTO-INVENTORY-START -->` / `<!-- AUTO-INVENTORY-END -->` in `master_to_live_defi_2026_05_23.md`. Full SSOT: `codex/11-project-management/active-plan-inventory-tracker.md`.

---

## Commit + Push + Flip Plan Checkboxes As You Ship Each Item (HARD RULE)

**Half 1 — Commit + push at every shippable unit.** Pushed = real. Per-shippable-unit cadence, NOT per-hour.

Pre-commit check (MANDATORY — catches accidental bundling):
```bash
git status && git diff --cached --stat   # NO PATH ARGUMENT — see entire index
```
If anything not yours: `git restore --staged <file>` before commit.

**Foot-gun #4** (prek auto-restore): bundle Edit→stage→commit→push into ONE Bash call. `--no-verify` IS authorized when auto-restore symptoms observed (diagnostic: "Restored working tree changes from .../prek/patches/" in output). Stage explicitly by name; never `git add .` / `-A`.

**Half 2 — Flip checkbox in same logical unit.** `- [ ]` → `- [x] (commit-sha + evidence)` AS SOON AS shipped. Don't flip unless work is pushed. Flip commits use `docs(plans):` prefix (NOT `plan(...)` — rejected by hook).

**Half 3 — Session-end deferred-work scoreboard.** Multi-item sessions with non-final state → `## Deferred work after <date> <session-tag>` table in plan body before `## Temporary states`.

---

## Post-Plan-Phase Codex Audit (HARD RULE)

After every major phase: (1) phase changed a codex contract? update the doc. (2) new pattern not in codex? write stub. (3) invalidated codex doc? add SUPERSEDED banner. Codex doc paths MUST be enumerated in plan's "Codex SSOT updates" phase — plans omitting this are review-blocking.

---

## CI Verification After Every Push (HARD RULE)

- Pushes to `main` / PRs → CI runs. **Always verify** via `gh run list --branch <branch> --repo <owner>/<repo> --limit 5`.
- Pushes to `live-defi-rollout` / `feat/*` → NO remote CI. Quality enforced locally via `quality-gates.sh`.
- On CI fail: `gh run view <run-id> --log-failed`. Fix root cause. Push again.
- CI failures are NOT issues to flag — fix in real time.

---

## Grep-Then-Read, Not Grep-Then-Conclude (HARD RULE)

0 grep hits ≠ feature missing. Many features are runtime-resolved (regex dispatch, StrEnum lookups, factory registries, dynamic `getattr`, config-driven wiring). After 0 hits: escalate to READ — open candidate consumer + factory/dispatcher files. When uncertain, ASK rather than CONCLUDE. For >50KB plans, read past executive summary.

---

## Findings Triage Discipline (HARD RULE)

| Where it sits | Action |
| --- | --- |
| In your code / file you own | Fix in same commit |
| Adjacent to your plan | Document + fix in YOUR plan |
| Outside plan, small + clear | Fix if ≤30 min |
| Outside plan, ambiguous | Diagnose first — read both sides (caller + callee). Fix the side that's wrong. If genuinely can't tell → file issue doc. |
| Outside every plan | `plans/active/issues/<name>_<YYYY_MM_DD>.md` |
| **Big finding** | NOTIFY OPERATOR + file issue doc |

**"Pre-existing" is NOT a triage criterion** — fix now if you can. **Diagnose before fix** — is the code wrong or the test wrong? Read both sides.

"Big" = data correctness ≥1 asset_group / May-23 critical path / cross-repo / contradicts workspace SSOT. Issue-doc frontmatter: `title`/`created`/`author`/`source[]`/`locked_by`. Body: `## What I found` / `## Why it matters` / `## Recommended decision`.

---

## Plans Run To Actual Completion, Not Smoke-Test Green (HARD RULE)

Code-shipped ≠ operationally-shipped. Backfills/migrations/reconcilers run to completion on real infra with manifest-verified rows + sample-inspected parquets. ADC admin perms on GCP (`central-element-323112`) + AWS (`427895769566`) — do NOT pause for operator approval on infra ops.

Hard-stop list (human-only): wallet keys, kill-switch arming, force-push to main, version 1.0.0 graduation.

Every Tab in daily work-split MUST declare Full-Execution Criterion. SSOT: `plans/PLAN_FORMAT.md` § 8.

---

## Estimate Calibration (HARD RULE)

Apply class multipliers at plan-write time. Claude's estimates run 1.5-3× conservative for this workspace's fan-out pattern:

| Class | Multiplier |
| --- | --- |
| `refactor` | 0.4× |
| `design` | 0.6× |
| `infra` | 0.8× |
| `brand-new` | 1.0× |
| `research` | 1.2× |

Frontmatter (every plan after 2026-05-11): `estimate_class` / `estimate_baseline_ai_days` / `estimate_calibrated_ai_days`. Legacy plans: retrofit on next substantive touch — do NOT mass-sweep. Retrospective ledger: `codex/08-workflows/estimation-retrospective-ledger.md`. Full SSOT: `codex/08-workflows/estimation-calibration.md`.

---

## Citadel-Grade Planning Standards

Every plan MUST: (1) Pre-Audit Before Execution — workspace-wide grep for every removed/renamed symbol; embed manifest. (2) Phased Execution DAG with explicit deps + QG gates between phases. (3) No Technical Debt — clean breaks, no shims. (4) Parallelization — independent items marked PARALLEL. (5) Success Criteria per phase — QG/basedpyright/ruff + test + deployment gates. (6) Downstream Consumer Updates — pre-audit EVERY workspace consumer for removed/renamed public symbols. (7) Single Source of Truth — types in UAC or `unified_api_contracts.internal`.

---

## Runbook Execution-Owner SSOT (HARD RULE)

Every runbook MUST declare 4 fields: `owner` / `cadence` / `verifier` / `last_executed`. No exceptions — missing fields = review-blocking. Closed set of execution paths: (1) Cron VM, (2) Daily Tab assignment, (3) QG-wired smoke, (4) Cron ScheduleWakeup. Reference: `plans/active/issues/runbook_execution_governance_gaps_2026_05_08.md`.

---

## Peripheral Script Directories Under Primary-Consumer QG (HARD RULE)

Every peripheral script directory importing from a service MUST be wired into THAT service's `quality-gates.sh`. Key mapping: `e2e-testing/scripts/defi/` → strategy-service QG; `e2e-testing/scripts/sports/` → features-service QG; `e2e-testing/scripts/prediction/` → mtds QG; `*_service/scripts/migration_*.py` → own service QG.

---

## Master Plan Continuous-Verification Column (HARD RULE)

Every success criterion (Groups A-G, 23 items) MUST declare continuous-verification path. Column: `| Group | Item | Cutover Criterion | Continuous Verification | Last verified |`. PRs without `Last verified` updates are review-blocked.

---

## Per-Tab Worktrees — 3-tier parallel-agent isolation

3 tiers: Operator (separate machines) → Slot (`.tabs/<N>/<repo>/` on `tab/<operator>/<N>`) → Sub-agent (within slot, shares index).

Bootstrap: `bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --init --slots 8` (also: `--add-slot N`, `--reset-slot N`, `--list`). Reconciliation: `bash unified-trading-pm/scripts/dev/slot-master-rebase.sh`.

SSOTs: `codex/05-infrastructure/per-tab-worktrees.md` + `plans/active/per_agent_worktrees_2026_05_10.md`.

---

## Daily Work-Split Process (Ikenna ↔ Harsh, AI-paralleled)

**Main orchestrator bootstrap**: read your side's LEDGER first (`ikenna_orchestrator/LEDGER.md` or `harsh_orchestrator/LEDGER.md`). Boot: `git status` + `git fetch` + ledger read + ack state.

**Sizing**: ~250-400 cal AI-days per side per 4-day cycle. **Ikenna**: cross-cutting design (3+ repos), trading-judgment, governance, large migrations. **Harsh**: implement-from-spec, run-script-and-verify, single-repo edits, test execution.

**Models**: A = fixed 5-tab clustering. B = 1-main + dynamic spawned tabs.

**Universal mechanics**:
- **Conditional push**: `git fetch` first → 0 incoming → push freely; any incoming → STOP, document 🟡 BLOCKED in plan-of-record, append ping.
- **Ping ledger bifurcation**: workspace-shared `plans/active/_agent_pings.md` (cross-side only) + per-side `<side>_orchestrator/pings/slot_<N>.md` (intra-side). Per-slot files reset on re-theme via `--reset-slot <N>`. Cross-side commit-sha entries persist until both sides ack.
- **Slot precedence**: slot 1 main owns master-plan refresh + daily inventory regenerator. Other slots do NOT edit `master_to_live_defi_2026_05_23.md` directly.
- Sub-agent fan-out: send all `Task` calls in SINGLE message. Paste `SUB_AGENT_MANDATORY_RULES.md` at top.

Full SSOT: `codex/12-agent-workflow/` + `ikenna_orchestrator/LEDGER.md`.

---

## Cross-Plan Coordination Banners

When launching VM or starting in-flight refactor, add `> **🟢 VM RUNNING — ...**` / `> **🟡 IN-FLIGHT REFACTOR — ...**` banner to every affected active plan. Scan banners before touching affected surface. Banner-remove owned by launcher at completion.

---

## Sub-Agents & Autonomous Agents: Full Rules Required (MANDATORY)

Sub-agents start FRESH. Paste `SUB_AGENT_MANDATORY_RULES.md` (10KB lean file) at TOP of every Task spawn.
- Local: `RULES=$(bash unified-trading-pm/scripts/agents/inject-mandatory-rules.sh "$WORKSPACE_ROOT" "$REPO")`.
- GHA: load via `GITHUB_ENV` heredoc.
- If paste impractical: include "Before any action, read SUB_AGENT_MANDATORY_RULES.md and follow ALL rules strictly."
- **If rules injection fails, agent MUST NOT proceed.**

SSOTs: `unified-trading-pm/scripts/agents/inject-mandatory-rules.sh` + `cursor-configs/SUB_AGENT_MANDATORY_RULES.md`.

---

## Analysis Rules

EXCLUDE `.venv*`, `node_modules/`, `build/`, `dist/`. FOCUS Python source in service dirs.
```bash
rg "pattern" --type py --glob '!.venv*' --glob '!build' --glob '!tests'
```

---

## Workspace Configs (Canonical in PM)

Canonical: `unified-trading-pm/cursor-configs/`. Setup: `bash unified-trading-pm/scripts/workspace/setup-workspace-config-symlink.sh`. Strict basedpyright (`reportAny`/`reportUnknownMemberType`/`reportUnknownVariableType` = error).

---

## UAC Citadel Architecture

Layout: `canonical/domain/` · `canonical/crosscutting/` · `external/{source}/` (80+ dirs) · `normalize_utils/` · `registry/` · root facades.

**Deleted dirs** (do NOT reference): `canonical/normalize/` · `external/sports/` · `external/cloud_sdks/` · `external/onchain/` · `external/macro/` · `schemas/` · `shared/`.

Import: `from unified_api_contracts import X` or `from unified_api_contracts.{domain} import X`. Deep paths are UAC-internal. SSOT: `codex/02-data/contracts-scope-and-layout.md`.
