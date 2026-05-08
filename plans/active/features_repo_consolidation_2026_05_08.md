---
name: features-repo-consolidation-2026-05-08
overview:
  Merge the 8 separate `features-*-service` repos (calendar / commodity / cross-instrument / delta-one / multi-timeframe
  / onchain / sports / volatility) into a single `features-service` repo with sub-packages per family, ONE Docker image
  parameterised by a CLI `--feature-family` flag, ONE flat `pyproject.toml`, ONE Health-API endpoint exposing per-family
  freshness, and a NEW UAC schema column `feature_family` (additive sibling-or-prefix of `feature_group` in the v5
  manifest). Pre-requisite for `live_pipeline_mtds_mdps_features_2026_05_08` because the live topology assumes a single
  deployable image with per-family deployment flavors. Mirrors the UMI→MTDS and UCI→UTL precedents —
  packages-within-packages, no behavioural change to calculator logic, lift duplicated cross-family helpers
  (watermark+grace fan-in, available_at stamping, LookaheadBiasError gate, NaN write-gate) into UTL. Naming explicitly
  disambiguated from `ml_and_features_master` Phase 2's "feature-store consolidation sidecar" which is feature-DATA
  consolidation (pre-joined wide parquet for ml-training reads) — this plan is REPO consolidation.
type: code
epic: epic-code-completion
status: active

asset_group: cross-cutting
priority: P0
deadline: 2026-05-13
parent: master_to_live_defi_2026_05_23
locked_by: live-defi-rollout
locked_since: 2026-05-08
last_updated: 2026-05-08

completion_gates:
  code: C5
  deployment: D2
  business: none

repo_gates:
  - repo: features-service
    code: C0
    deployment: none
    business: none
  - repo: features-calendar-service
    code: C0
    deployment: none
    business: none
  - repo: features-commodity-service
    code: C0
    deployment: none
    business: none
  - repo: features-cross-instrument-service
    code: C0
    deployment: none
    business: none
  - repo: features-delta-one-service
    code: C0
    deployment: none
    business: none
  - repo: features-multi-timeframe-service
    code: C0
    deployment: none
    business: none
  - repo: features-onchain-service
    code: C0
    deployment: none
    business: none
  - repo: features-sports-service
    code: C0
    deployment: none
    business: none
  - repo: features-volatility-service
    code: C0
    deployment: none
    business: none
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-library
    code: C0
    deployment: none
    business: none
  - repo: deployment-api
    code: C0
    deployment: none
    business: none
  - repo: deployment-ui
    code: C0
    deployment: none
    business: none
  - repo: deployment-service
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-pm
    code: C0
    deployment: none
    business: none

depends_on: []

todos:
  - id: phase-0-pre-audit-manifest
    content: |
      - [ ] [AGENT] P0. Phase 0 — Pre-audit manifest (read-only). Produce a single artifact under
        `unified-trading-pm/plans/active/issues/features_repo_consolidation_preaudit_2026_05_08.md` enumerating, per
        source repo (8 features-* repos):
        (a) every Python module + class + public function and which sub-package it lands in post-merge;
        (b) every callsite OUTSIDE the source repo that imports from `features_<family>_service.*` — grep across
            all sibling repos under `${WORKSPACE_ROOT}` (UAC / UTL / UCI / UEI / UDC / MTDS / MDPS / instruments-service /
            ml-training-service / ml-inference-service / strategy-service / execution-service / position-balance-monitor-service
            / risk-and-exposure-service / unified-trading-pm / deployment-api / deployment-ui / deployment-service /
            e2e-testing) — every hit gets a row: repo, file, line, import statement, post-merge replacement;
        (c) every script under `scripts/` per source repo + its post-merge home (`features-service/scripts/<family>/`);
        (d) every test under `tests/` per source repo + its post-merge home (`features-service/tests/<family>/`);
        (e) every UAC / UTL symbol the source repo redefines locally that should be imported from upstream instead
            (catch self-declared duplicates per Citadel-Grade § 7 SSOT rule);
        (f) every cross-family helper currently duplicated across ≥2 source repos (the "lift to UTL" candidates) —
            specifically watermark+grace fan-in, `available_at` stamping, `LookaheadBiasError` gate, NaN write-gate,
            ManifestFreshnessCache adoption status (per `ml_and_features_master` Phase 1A.UTL-CACHE-ADOPT).
        Output is the input to every later phase; do NOT skip — the entire migration's correctness depends on
        catching every external import. **Foot-gun**: `unified-trading-pm/cursor-configs/` and
        `unified-trading-pm/codex/` may reference module paths in docs (search for `features_<family>_service` as a
        substring, not just `import` lines).
    status: todo
    note: ""

  - id: phase-1a-uac-feature-family-schema
    content: |
      - [ ] [AGENT] P0. Phase 1A — Add `feature_family` to UAC v5 manifest schema. PARALLEL with 1B.

      Site: `unified-api-contracts/unified_api_contracts/canonical/crosscutting/honest_coverage.py` (or the equivalent
      v5 manifest schema SSOT — locate via `grep -rn "feature_group" unified-api-contracts/unified_api_contracts/canonical/`).

      Add the new column as a closed-set `StrEnum`:

      ```python
      class FeatureFamily(StrEnum):
          CALENDAR = "calendar"
          COMMODITY = "commodity"
          CROSS_INSTRUMENT = "cross_instrument"
          DELTA_ONE = "delta_one"
          MULTI_TIMEFRAME = "multi_timeframe"
          ONCHAIN = "onchain"
          SPORTS = "sports"
          VOLATILITY = "volatility"
      ```

      Extend the manifest row schema to include `feature_family: str | None` (sibling of `feature_group`). Existing
      rows have `feature_family=None` — back-compat preserved. Per CLAUDE.md "Manifest migration, NOT fallback" rule:
      add a one-time migration script (Phase 4) that flips legacy rows to the correct family based on the writer
      service that produced them; no runtime fallback path.

      Tests `unified-api-contracts/tests/unit/test_feature_family.py`:
      (1) enum closed-set: `set(FeatureFamily) == 8 expected values` exactly;
      (2) every existing `feature_group` symbol can be mapped to exactly ONE feature_family (build a registry dict
          `FEATURE_GROUP_TO_FAMILY` in UAC and assert no orphans);
      (3) JSON serialization round-trip preserves both columns.

      QG: `cd unified-api-contracts && bash scripts/quality-gates.sh` clean. Push to `live-defi-rollout`.
    status: todo
    note: ""

  - id: phase-1b-utl-manifestwriter-feature-family-param
    content: |
      - [ ] [AGENT] P0. Phase 1B — `ManifestWriter.record_captured` / `record_empty` / `record_failed` /
        `record_expected_empty` accept a new optional `feature_family: str | None = None` kwarg, default None for
        non-features writers (cefi / defi / tradfi / sports / prediction MTDS+MDPS pass nothing, behaviour
        unchanged). PARALLEL with 1A.

      Site: `unified-trading-library/unified_trading_library/manifest_writer.py` (or the equivalent SSOT — locate
      via `grep -rn "def record_captured" unified-trading-library/`).

      Enforcement rule: when `feature_family` is None AND the writer's source CLI was invoked with
      `--operation calculate`, raise `MissingFeatureFamilyError` (mirrors the existing
      `MissingClusterValidationError` enforcement for bundled-shard cluster validation per writegate Phase 1A
      contract).

      Tests `unified-trading-library/tests/unit/test_manifest_writer_feature_family.py`:
      (1) record_captured with feature_family="onchain" writes the column to the parquet;
      (2) record_captured WITHOUT feature_family from a features-CLI source raises MissingFeatureFamilyError;
      (3) record_captured WITHOUT feature_family from a non-features CLI source (MTDS/MDPS) does NOT raise —
          the column is just None;
      (4) the write is row-level: same shard with two feature_families produces two distinct rows, not collisions.

      QG: UTL quality-gates.sh clean.
    status: todo
    note: ""

  - id: phase-2-create-features-service-repo
    content: |
      - [ ] [HUMAN+AGENT] P0. Phase 2 — Create the `features-service` repo with skeleton + ONE flat `pyproject.toml`
        + ONE Dockerfile + ONE quality-gates.sh + ONE buildspec.aws.yaml + ONE cloudbuild.yaml.

        `git init` + `git remote add origin git@github.com:IggyIkenna/features-service.git`. Workspace rules
        (`unified-trading-pm/.cursorrules` + `cursor-configs/SUB_AGENT_MANDATORY_RULES.md`) symlinked from PM exactly
        like every other repo. Sibling-clone path under `${WORKSPACE_ROOT}/features-service` matches the existing
        `workspace-manifest.json` convention.

        Skeleton:
        ```
        features-service/
          features_service/
            __init__.py
            __main__.py             # cli entry: python -m features_service ...
            cli/main.py             # standardised --operation/--mode/--asset-group/--feature-family/--feature-group
            api/main.py             # ONE FastAPI app, ONE Health-API with per-family data_freshness callback registry
            common/                 # cross-family lifts (Phase 5)
            calendar/               # placeholder, populated in Phase 3
            commodity/
            cross_instrument/
            delta_one/
            multi_timeframe/
            onchain/
            sports/
            volatility/
          tests/
            unit/
            integration/
            common/                 # tests for the lifted helpers
          scripts/quality-gates.sh  # workspace-standard
          Dockerfile                # ARG PROJECT_ID + asia-northeast1-docker.pkg.dev/${PROJECT_ID}/unified-trading-library/...
          pyproject.toml            # ONE flat [project.dependencies] — union of the 8 source repos' deps, deduped
          buildspec.aws.yaml
          cloudbuild.yaml
          pyrightconfig.json        # strict basedpyright matching workspace
          .python-version           # 3.13
        ```

        Empty smoke test: `python -m features_service --version` returns the version. QG Pass 1 green on the
        empty skeleton (lint + format + typecheck on a stub `cli/main.py` that only handles `--version`). Push.

        **Repo creation gate**: human approval required to create the GitHub repo (per CLAUDE.md "Executing actions
        with care" — repo creation is a shared-state action). Agent prepares the local git init + skeleton + asks
        the operator to create the empty remote on GitHub.
    status: todo
    note: ""

  - id: phase-3-migrate-source-repos-with-history
    content: |
      - [ ] [AGENT] P0. Phase 3 — Migrate the 8 source repos into sub-packages, preserving git history.

        Use `git subtree merge` per source repo (NOT `git filter-branch` — it rewrites SHAs). For each source
        family `<f>` ∈ {calendar, commodity, cross_instrument, delta_one, multi_timeframe, onchain, sports,
        volatility}:

        1. `git subtree add --prefix=features_service/<f> ../features-<f>-service main --squash=false`. The
           `--squash=false` preserves per-commit history; we want to keep author + timestamp + message attribution
           for `git blame` to work post-migration.
        2. Move source files: `git mv features_service/<f>/features_<f>_service/* features_service/<f>/` then
           remove the now-empty `features_<f>_service/` directory.
        3. Strip duplicated top-level config: `pyproject.toml`, `Dockerfile`, `cloudbuild.yaml`, `buildspec.aws.yaml`,
           `pyrightconfig.json`, `.python-version`, `scripts/quality-gates.sh`, `pip.conf`, `coverage.xml`, `uv.lock`
           — these all live at the consolidated repo root, NOT per family. `README.md` per family kept (renamed to
           `features_service/<f>/README.md`).
        4. Move tests: `git mv features_service/<f>/tests/* tests/<f>/`.
        5. Move scripts: `git mv features_service/<f>/scripts/* scripts/<f>/`. `scripts/quality-gates.sh` lives at
           the consolidated root.
        6. Update internal imports: `grep -rln "features_<f>_service" features_service/<f>/ tests/<f>/ scripts/<f>/`
           and rewrite to `features_service.<f>`. Use `sed -i '' 's/features_<f>_service/features_service.<f>/g'`.
        7. Per-family commit: `feat(<f>): import features-<f>-service into features-service via git subtree`.

        After all 8 subtree merges + per-family commits, push the consolidated repo to origin. Source repos remain
        untouched on disk + on GitHub for now (Phase 7 archives them).

        **Critical**: `git subtree` on macOS may need `brew install git-subtree` (or use the bundled `git-subtree.sh`
        from git-core/contrib if `git subtree` returns "unknown command"). Verify before starting Phase 3.

        Tests: skeleton smoke (`python -m features_service --version`) still green. Per-family unit tests
        (lifted as-is from source repos) RUN but may fail at this stage — Phase 4 fixes the import paths systematically.
    status: todo
    note: ""

  - id: phase-4-fix-internal-imports-cli-and-config
    content: |
      - [ ] [AGENT] P0. Phase 4 — Fix internal imports + lift the 8 per-family CLIs into a single dispatching
        `features_service/cli/main.py`. SEQUENTIAL after Phase 3.

        4.1 — Cross-family import fixes: any file under `features_service/<f1>/` that imported from
             `features_<f2>_service.*` (cross-family imports across the source repos — grep finds these in cross-instrument
             which depends on delta-one outputs, and delta-one has some volatility-feature reuse) gets rewritten to
             `features_service.<f2>.*`. Grep + sed pass per family. Phase 0 pre-audit § (a) lists every cross-family
             reference.

        4.2 — Single dispatching CLI in `features_service/cli/main.py`:

             ```python
             def main() -> None:
                 args = parse_args()  # --operation/--mode/--asset-group/--feature-family/--feature-group/...
                 family_module = importlib.import_module(f"features_service.{args.feature_family}")
                 family_module.run(args)  # each family exposes a `run(args: ParsedArgs) -> None` entry point
             ```

             Each `features_service/<f>/__init__.py` exports `run(args)` that delegates to the lifted-from-source-repo
             CLI logic. Workspace `codex/06-coding-standards/cli-convention.md` is the SSOT for the standardised flag set.

        4.3 — Single `pyproject.toml` deduped: union the 8 source repo deps, pin to the most-recent compatible
             range across all. Workspace rule "ONE list, no [project.optional-dependencies]" applies. Run
             `uv pip install -e .` from the consolidated repo + smoke a venv build. Pin discrepancies (e.g. one source
             pinned `numpy>=2.3,<2.4` and another `numpy>=2.2,<2.4`) get resolved upward — the consolidated repo's tests
             must pass on the unified set.

        4.4 — Single `Dockerfile`: `ARG PROJECT_ID` + base
             `FROM --platform=linux/amd64 asia-northeast1-docker.pkg.dev/${PROJECT_ID}/unified-trading-library/unified-trading-library:latest`
             per CLAUDE.md "Key Rules". COPY in `features_service/`, install via uv pip, expose Health-API on port 8XXX
             (assign next free per `unified-trading-pm/scripts/dev/ui-api-mapping.json`).

        4.5 — Single Health-API in `features_service/api/main.py`: imports `make_health_router` from UTL, registers
             ONE `data_freshness` callback that internally fans out across the loaded families and returns a per-family
             freshness map. Health endpoint reachable at `:PORT/health` and returns
             `{"families": {"onchain": {...}, "delta_one": {...}, ...}, "loaded_families": [...]}`.

        4.6 — Single `scripts/quality-gates.sh` per workspace template; runs ruff + basedpyright + bandit + pytest +
             codex compliance over the WHOLE consolidated repo. Per-family pytest filtering via
             `pytest tests/<f>/` for development; CI runs the whole tree.

        QG: `cd features-service && bash scripts/quality-gates.sh` Pass 1 clean. Push.
    status: todo
    note: ""

  - id: phase-5-lift-cross-family-helpers-to-utl
    content: |
      - [ ] [AGENT] P1. Phase 5 — Lift the 4 duplicated cross-family helpers from per-family code into
        `unified-trading-library/unified_trading_library/feature_service_base/` (or `features/common/` — locate
        via `grep -rn "feature_service_base" unified-trading-library/`). Each helper currently copy-pasted across
        ≥2 of the 8 source repos.

        Helpers to lift (Phase 0 pre-audit § (f) is the authoritative source list — these are the candidates):
        (a) **Watermark + grace fan-in** for cross-instrument-style multi-stream alignment — currently inlined in
            features-cross-instrument and features-multi-timeframe, slight drift between the two. Lifted name:
            `unified_trading_library.streaming.WatermarkAlignmentFanin`.
        (b) **`available_at` stamping** — every features-* family stamps `available_at` per row at write time; the
            stamping logic mirrors UAC `availability_stamping.stamp_available_at_*` but each features-* repo has
            its own thin wrapper. Lift the wrappers into UTL `feature_service_base/available_at_stamping.py` so
            new families pick up the canonical shape.
        (c) **`LookaheadBiasError` strict-mode gate** — per-row enforcement that
            `input.available_at <= target_ts - horizon`. Currently fires in 3 of 8 features-* repos with subtle
            differences in horizon resolution; lift into a single `assert_no_lookahead_for_feature_group(...)`
            helper that reads horizon from the UAC feature-DAG SSOT (per `ml_and_features_master` Phase 1A).
        (d) **NaN write-gate** — per-feature-group threshold check before `record_captured`; rejects writes with
            >threshold% NaN. Currently inlined per-calculator. Lift into a UTL `WriteGateHelper.check_nan_ratio(...)`.

        Tests for each lifted helper under `unified-trading-library/tests/unit/feature_service_base/` (existing
        directory; add helper-specific tests). Each lift is its own commit with the per-family inline removals
        in the same commit — no parallel paths during transition (workspace "no double SSOT" rule).

        QG: UTL quality-gates.sh clean per lift commit; consolidated features-service quality-gates.sh clean
        after all 4 lifts land.

        **Coordination**: `ml_and_features_master` Phase 2.UTL-LIFT lifts the `FeatureBatchHandler` glue from
        the 4 features-* repos that have it. That work overlaps with this Phase 5 — coordinate via the
        Cross-Plan-Coordination-Banners rule. Recommend: `ml_and_features_master` lifts FeatureBatchHandler
        first (or in parallel with this Phase 5 if the agents don't collide); features-service inherits it.
    status: todo
    note: ""

  - id: phase-6-regression-parity-test
    content: |
      - [ ] [AGENT] P0. Phase 6 — Pre-merge vs post-merge feature-output parity test. SEQUENTIAL after Phase 5.

        Goal: prove the migration is byte-for-byte (or numerically identical) for feature outputs on a sample
        backtest window. Workspace doesn't ship a generic "feature output diff" tool today, so this phase ALSO
        creates `unified-trading-pm/scripts/dev/feature_parity_diff.py` as a reusable utility.

        Steps:
        1. Pick a 7-day reference window (e.g. 2026-04-01 → 2026-04-07) covering at least one shard per family
           that has live data on disk.
        2. Pre-merge baseline: each of the 8 features-*-service repos still on disk + git-cleanly-checked-out
           at their last-pre-consolidation commit. Run their per-family CLIs against the reference window with
           output to `${WORKSPACE_ROOT}/.feature_parity_diff/baseline/<f>/`.
        3. Post-merge: run `python -m features_service --feature-family <f> --mode batch --start-date ...
           --end-date ...` for each family with output to `${WORKSPACE_ROOT}/.feature_parity_diff/postmerge/<f>/`.
        4. `feature_parity_diff.py` reads both parquets per family, asserts:
           - Schema match (column names + types identical).
           - Row count identical.
           - For numeric columns: `np.allclose(baseline, postmerge, rtol=1e-9, atol=0)` — strict equality except
             for floating-point edge cases (cross-row aggregates may have minute reorder noise; tolerance covers
             that).
           - For string / categorical columns: exact equality.
           - For `available_at` column: identical timestamps (the available_at lift in Phase 5 must NOT change
             stamping semantics).
        5. Any diff > tolerance fails Phase 6 → diagnose the offending family + back to Phase 4 / 5.

        QG: parity diff zero across all 8 families. Save the diff report under
        `unified-trading-pm/plans/active/issues/features_repo_consolidation_parity_2026_05_08.md` for audit trail.

        **Why this gates Phase 7**: source repos are NOT archived until parity is proven. If parity fails for a
        family, we revert that family's subtree merge + diagnose without losing operational continuity.
    status: todo
    note: ""

  - id: phase-7-archive-source-repos
    content: |
      - [ ] [HUMAN+AGENT] P0. Phase 7 — Archive the 8 source repos. SEQUENTIAL after Phase 6 parity gate green.

        Per source repo `features-<f>-service`:
        1. Add a `README_ARCHIVED.md` at repo root with a banner: "**ARCHIVED 2026-05-XX** — code merged into
           `features-service` via `features_repo_consolidation_2026_05_08.plan.md`. New work + bug fixes go to
           `features-service/features_service/<f>/`."
        2. Replace the existing `README.md` with a 5-line stub pointing to the archive banner.
        3. Final commit: `chore(archive): merged into features-service per features_repo_consolidation_2026_05_08`.
        4. GitHub: `gh repo archive IggyIkenna/features-<f>-service --confirm` (operator runs — repo archive is a
           shared-state action requiring human approval per CLAUDE.md "Executing actions with care").
        5. Remove from `unified-trading-system-repos.code-workspace` `folders` list.
        6. Remove from `workspace-manifest.json` repo registry.
        7. Update `unified-trading-pm/scripts/workspace/setup-workspace-config-symlink.sh` if it enumerates the 8
           features-* repos explicitly.

        QG: `unified-trading-pm` quality-gates.sh clean after the workspace-manifest edit.
    status: todo
    note: ""

  - id: phase-8a-deployment-launcher-migration
    content: |
      - [ ] [AGENT] P0. Phase 8A — Migrate any existing features-*-service VM launchers to the consolidated
        layout. Per workspace VM launcher SSOT rule
        (`codex/05-infrastructure/launcher-script-ssot.md` + `CLAUDE.md`), every launcher MUST live in
        `deployment-service/scripts/vm/`.

        Audit + migration:
        1. `grep -rln "features-<f>" deployment-service/scripts/vm/` per family — record current launchers.
        2. Replace each `launch-features-<f>-*.sh` with one parameterised
           `deployment-service/scripts/vm/launch-features-<flavor>.sh` that takes
           `--feature-family <name>` + `--asset-group <name>` + `--mode {batch,live}` + the standard
           `RUN_TS=$(date +%Y%m%d-%H%M%S)` + `MANIFEST_PER_VM_SHARDS=true` + `VM_NAME=<unique-tag>` per the
           workspace per-VM-shard-isolation rule.
        3. Update `VM_PREFIX_TO_BUCKET` in
           [`deployment-service/scripts/vm/vm_zombie_watchdog.py`](../../deployment-service/scripts/vm/vm_zombie_watchdog.py)
           to register the new `features-<flavor>-` prefix and remove the 8 retired prefixes (one prefix per
           old features-<family>- launcher).
        4. Update `_SERVICE_LAUNCHER_SCRIPTS` in
           `deployment-api/deployment_api/services/deploy_missing.py` so the Deploy-Missing UI button
           continues to work for features deploys.
        5. Relaunch `vm-zombie-watchdog` per workspace rule (the running watchdog only fetches the Python at
           boot — dict change doesn't propagate live). Operator-driven action; agent prepares the relaunch
           command but does not run it.

        QG: `deployment-service` quality-gates.sh clean.

        **Coordination**: `launcher_scripts_consolidation_into_deployment_service_2026_05_07.plan.md` is in
        flight migrating ad-hoc launchers from `e2e-testing/scripts/` + `features-*-service/scripts/` into
        `deployment-service/scripts/vm/`. Coordinate via Cross-Plan-Coordination-Banners — that plan's work
        for features-* repos becomes a no-op once Phase 7 archives the source repos. Banner the launcher
        consolidation plan with `🟡 IN-FLIGHT REFACTOR` pointing here so its agents skip features-* repos.
    status: todo
    note: ""

  - id: phase-8b-deployment-api-ui-wiring
    content: |
      - [ ] [AGENT] P1. Phase 8B — Update `deployment-api` + `deployment-ui` to surface `feature_family` as a
        first-class drilldown axis in the data-status tab, parallel to the existing `feature_group` axis.

        deployment-api:
        1. `_SERVICE_LAUNCHER_SCRIPTS` updated per Phase 8A.
        2. Data-status leaf-stats endpoint (existing — added in writegate Phase 4.A.3) gets a new
           filter parameter `feature_family: str | None` so the UI can slice the manifest by family.
        3. Deploy-Missing endpoint generates the new launcher CLI shape
           (`launch-features-<flavor>.sh --feature-family <name> --asset-group <name>`).

        deployment-ui:
        1. `DataStatusTab` adds a `feature_family` column to the per-shard table when manifest rows have a
           non-null value (mostly features-service rows — non-features rows render `n/a`).
        2. Drilldown hierarchy adjusted in `codex/02-data/data-status-drilldown-hierarchy.md` — feature_family
           sits between asset_group and feature_group.
        3. `LeafSchemaModal` (existing — writegate Phase 4.A.4) renders feature_family alongside feature_group
           for features-service shards.

        Tests: deployment-api unit tests under `tests/unit/test_data_status_feature_family_filter.py`;
        deployment-ui Vitest under `src/components/data-status/__tests__/feature-family-column.test.tsx`. QG
        clean per repo.

        **Coordination**: `deployment_ui_lifecycle_tabs_2026_05_08` may overlap on data-status surface
        edits; banner that plan + this one mutually.
    status: todo
    note: ""

  - id: phase-9-codex-ssot-updates
    content: |
      - [ ] [AGENT] P0. Phase 9 — Codex SSOT updates. PARALLEL with Phase 8.

        Per the workspace "Post-Plan-Phase Codex Audit" rule (CLAUDE.md, codified 2026-05-08), this phase
        creates the consolidation architecture doc + updates 5 existing docs.

        New + updated docs:
        1. **NEW** `codex/04-architecture/features-service-architecture.md` (no plan-draft stub yet — write
           in this phase) — describes the consolidated repo shape, per-family sub-package layout, the
           `feature_family` UAC enum, the cross-family helpers lifted to UTL, the per-family deployment
           flavor matrix (which families colocate with which asset_group's MDPS vs which run as
           cross-cutting). 4-5 paragraphs + a routing table.
        2. **UPDATE** `codex/06-coding-standards/feature-service-pattern.md` — replace per-repo references with
           sub-package references; add a "Adding a new feature_family" recipe pointing at
           `features-service/features_service/<f>/__init__.py` exporting `run(args)`.
        3. **UPDATE** `codex/06-coding-standards/cli-convention.md` — extend the standardised CLI flag
           catalogue with `--feature-family`.
        4. **UPDATE** `codex/02-data/data-status-drilldown-hierarchy.md` — add the feature_family axis to the
           drilldown order.
        5. **UPDATE** `codex/00-SSOT-INDEX.md` — register the new architecture doc under "Architecture".
        6. **UPDATE** `codex/05-infrastructure/launcher-script-ssot.md` — replace the 8 features-* launcher
           rows with the consolidated `launch-features-<flavor>.sh` row.

        QG: `unified-trading-pm` quality-gates.sh clean. Plan-health agent picks up the SSOT additions on the
        next run.
    status: todo
    note: ""

  - id: phase-10-workspace-wide-qg-sweep
    content: |
      - [ ] [AGENT] P0. Phase 10 — Workspace-wide QG sweep across all repos that imported `features_<f>_service`
        symbols (Phase 0 pre-audit § (b) is the authoritative consumer list). Final phase before completion.

        For each consumer repo identified in Phase 0:
        1. Verify all imports rewritten to `features_service.<f>` form. `grep -rln "features_<f>_service"` from
           the consumer repo's source dir returns zero hits.
        2. Run consumer's `bash scripts/quality-gates.sh` Pass 1 — must be clean.
        3. If consumer publishes events / writes to manifest with `feature_family` populated, verify the column
           propagates correctly (manifest reader at `feature_family=<value>` returns the consumer's rows).

        Final gate: `for repo in $(jq -r '.repos[].path' workspace-manifest.json); do (cd "$repo" && bash scripts/quality-gates.sh) || exit 1; done`
        — every workspace repo green simultaneously. Operator runs; agent prepares the sweep command and
        documents every QG-failure-attribution per CLAUDE.md (your-bug vs other-agent's-bug).
    status: todo
    note: ""

isProject: false
---

# features-\* repo consolidation (2026-05-08)

## Why this plan exists

Pre-requisite for `live_pipeline_mtds_mdps_features_2026_05_08.plan.md` — the live pipeline topology assumes a SINGLE
`features-service` Docker image parameterised by `--feature-family` / `--asset-group`, deployed in two flavors
(asset-scoped colocated with MDPS per asset_group; cross-cutting standalone). Maintaining that topology against 8
separate image build + deploy pipelines is operationally infeasible against the 2026-05-23 cutover — every per-family
deploy-flow drift becomes an outage risk.

This plan also pays down standing tech debt: the 8 features-\*-service repos share ~70% of their boilerplate
(pyproject.toml deps, Dockerfile, scripts/quality-gates.sh, CLI shape, Health-API wiring, ServiceBootstrap, manifest
write-gate, available_at stamping, LookaheadBiasError gate). Per CLAUDE.md "No double SSOT in data-saving methodology"

- "Single Source of Truth" rules, that duplication is itself a workspace violation. Consolidation is the canonical fix.

Pattern matches UMI→MTDS (commit history visible in [market-tick-data-service/](../../market-tick-data-service/) —
`git log --oneline | grep "merge umi"`) and UCI→UTL (commit history visible in unified-trading-library —
`git log --oneline | grep "merge unified-config-interface"`). Sub-packages within a parent repo, light internal seams,
ONE Docker image, ONE Health-API, ONE flat pyproject.toml.

## Naming disambiguation

Two unrelated meanings of "features consolidation" coexist in the workspace:

1. **REPO consolidation** (this plan) — 8 features-\*-service repos → 1 features-service repo. SOURCE-side concern.
2. **DATA consolidation** (`ml_and_features_master_2026_05_07` Phase 2) — feature-store sidecar that pre-joins
   per-feature_group parquets into a wide format (one parquet per `(asset_group, day, instrument, timeframe)`) so
   ml-training does ONE GCS GET per day instead of N. OUTPUT-side concern.

These are orthogonal; both ship before May 23. This plan REFERENCES the data-consolidation plan (Phase 5 cross-family
lift coordinates with `ml_and_features_master` Phase 2.UTL-LIFT) but does NOT subsume or modify it.

## Codex SSOTs

Read these BEFORE making code changes — drift between code and these docs is a review-blocking failure per the workspace
`doc → plan → code` discipline:

- [`codex/06-coding-standards/feature-service-pattern.md`](../../codex/06-coding-standards/feature-service-pattern.md) —
  features-\* service pattern (current per-repo shape; this plan's Phase 9 updates this to sub-package shape).
- [`codex/06-coding-standards/cli-convention.md`](../../codex/06-coding-standards/cli-convention.md) — standardised CLI
  axes (`--operation`, `--mode`, `--asset-group`); Phase 9 adds `--feature-family`.
- [`codex/02-data/data-lineage-MTDS-features-ml.md`](../../codex/02-data/data-lineage-MTDS-features-ml.md) — MTDS →
  features-\* → ml-training/ml-inference lineage; Phase 4 / 5 / 6 must preserve this lineage exactly.
- [`codex/02-data/availability-manifest-and-data-status.md`](../../codex/02-data/availability-manifest-and-data-status.md)
  — manifest schema + 4-state taxonomy; Phase 1A adds `feature_family` column; Phase 1B adds the writer kwarg.
- [`codex/05-infrastructure/launcher-script-ssot.md`](../../codex/05-infrastructure/launcher-script-ssot.md) — every
  gcloud / aws ec2 launcher MUST live in `deployment-service/scripts/vm/`. Phase 8A consolidates the 8 per-family
  launchers into one parameterised script.
- [`codex/04-architecture/batch-live-symmetry.md`](../../codex/04-architecture/batch-live-symmetry.md) — batch=live
  code-path symmetry; consolidation must NOT introduce a batch/live divergence in any features family.

## Pre-audit manifest

Phase 0 produces the authoritative pre-audit manifest as
`unified-trading-pm/plans/active/issues/features_repo_consolidation_preaudit_2026_05_08.md`. Subsequent phases reference
that file for: (a) module-by-module destination map; (b) every cross-repo import to rewrite; (c) per-family scripts +
tests to relocate; (d) self-declared duplicates to delete; (e) cross-family helper duplications to lift to UTL.

This plan does NOT pre-emit that manifest content — Phase 0 IS the audit work + producing the artifact. Subsequent
agents read the artifact, not this plan body.

## Phased execution DAG

```
Phase 0 (Pre-audit manifest — SOLO, blocks everything)
   │
   ├─> Phase 1A (UAC feature_family enum)  ─┐
   ├─> Phase 1B (UTL ManifestWriter kwarg) ─┤  PARALLEL within Phase 1
   │                                         ▼
   └─> Phase 2 (Create features-service repo + skeleton — gated by Phase 1 land)
        │
        └─> Phase 3 (Subtree-merge 8 source repos with history — SEQUENTIAL per family)
             │
             └─> Phase 4 (Fix internal imports + lift CLI + dedupe pyproject + Dockerfile + Health-API)
                  │
                  ├─> Phase 5 (Lift 4 cross-family helpers to UTL — PARALLEL with Phase 6)
                  ├─> Phase 6 (Pre-merge vs post-merge parity test — PARALLEL with Phase 5)
                  │
                  └─> Phase 7 (Archive 8 source repos — gated on Phase 6 parity green)
                       │
                       ├─> Phase 8A (Launcher migration in deployment-service)  ┐
                       ├─> Phase 8B (deployment-api + deployment-ui wiring)     ├─ PARALLEL
                       └─> Phase 9 (Codex SSOT updates)                          ┘
                            │
                            └─> Phase 10 (Workspace-wide QG sweep)
```

Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4 SEQUENTIAL. Phase 5/6 PARALLEL. Phase 7 SEQUENTIAL after Phase 6. Phase
8A/8B/9 PARALLEL. Phase 10 SEQUENTIAL final.

Estimated days: Phase 0 (0.5d) + Phase 1 (0.5d parallel) + Phase 2 (0.5d) + Phase 3 (0.5d) + Phase 4 (1d) + Phase 5+6
(1d parallel) + Phase 7 (0.5d) + Phase 8+9 (1d parallel) + Phase 10 (0.5d) = ~5d wall-clock with agent parallelism,
~7-8d sequential.

## Success criteria

- **Phase 0**: pre-audit manifest committed under `plans/active/issues/`; every cross-repo import + every duplicated
  helper enumerated.
- **Phase 1A**: UAC `FeatureFamily` enum + `FEATURE_GROUP_TO_FAMILY` registry merged; 3 unit tests pass; UAC QG clean.
- **Phase 1B**: UTL `ManifestWriter` accepts `feature_family` kwarg; `MissingFeatureFamilyError` raised on features-CLI
  write without it; 4 unit tests pass; UTL QG clean.
- **Phase 2**: features-service repo created with skeleton; smoke `python -m features_service --version` green; Pass 1
  QG clean on stub.
- **Phase 3**: 8 sub-packages populated via `git subtree merge --squash=false`; per-family commits visible in `git log`;
  smoke + per-family pytest RUNS (failures fixed in Phase 4).
- **Phase 4**: per-family pytest GREEN; consolidated pyproject + Dockerfile + Health-API working; QG Pass 1 clean.
- **Phase 5**: 4 cross-family helpers lifted to UTL with per-family inline removals in same commit; UTL QG clean.
- **Phase 6**: parity diff zero across all 8 families; report committed under `plans/active/issues/`.
- **Phase 7**: 8 source repos archived on GitHub; `workspace-manifest.json` + `code-workspace` cleaned; PM QG clean.
- **Phase 8A**: launchers consolidated; `VM_PREFIX_TO_BUCKET` updated; `vm-zombie-watchdog` relaunched.
- **Phase 8B**: deployment-api + deployment-ui surface `feature_family` axis; per-repo QG clean.
- **Phase 9**: 1 new codex doc + 5 updates landed; SSOT index updated.
- **Phase 10**: workspace-wide QG sweep green across every consumer repo.

## Anti-patterns to avoid

- **Do NOT use `git filter-branch`** for the source-repo merge — it rewrites SHAs and destroys `git blame`. Use
  `git subtree merge --squash=false` per Phase 3.
- **Do NOT keep per-family `pyproject.toml`** as a "shim" during transition. Workspace rule "Flat deps only" means ONE
  pyproject at the consolidated repo root, period.
- **Do NOT introduce `[project.optional-dependencies]`** to handle deps that are family-specific. If only
  features-onchain needs `web3.py`, it goes in the consolidated pyproject's `[project.dependencies]` because workspace
  rule "every pyproject has ONE list, no optional groups" is non-negotiable.
- **Do NOT run Phase 7 before Phase 6 parity green.** If parity fails for a family, we revert that family's subtree
  merge cleanly without losing operational continuity. Archiving source repos before parity = irreversible.
- **Do NOT add `# type: ignore` to silence basedpyright errors arising from import path rewrites.** Fix the import path
  properly. Workspace rule "No `# type: ignore` to hide architectural violations".
- **Do NOT use the deployment-UI Deploy-Missing button to launch features VMs during the migration window.** The
  `_SERVICE_LAUNCHER_SCRIPTS` registry will be inconsistent until Phase 8A lands; manual `gcloud` invocations are the
  right escape valve.

## Cross-plan coordination

- **`live_pipeline_mtds_mdps_features_2026_05_08`** — STRICT BLOCKER: this plan must reach Phase 7 before live-pipeline
  Phase 3 (deploy features instances per asset_group). Banner the live-pipeline plan with
  `🔴 BLOCKED — features-repo-consolidation Phase 7 must land first`.
- **`pipeline_mode_partition_migration_2026_05_08`** — independent; no overlap. May run in parallel.
- **`ml_and_features_master_2026_05_07`** — Phase 2.UTL-LIFT (FeatureBatchHandler lift) overlaps with this plan's Phase
  5 (4-helper lift). Coordinate: ml_and_features_master agent owns FeatureBatchHandler; this plan owns the 4 helpers;
  banner each other to avoid double-lift.
- **`launcher_scripts_consolidation_into_deployment_service_2026_05_07`** — Phase 8A here makes that plan's features-_
  migration items a no-op. Banner the launcher plan with `🟡 IN-FLIGHT REFACTOR — features-_ repos archived per
  features_repo_consolidation_2026_05_08; skip those`.
- **`deployment_ui_lifecycle_tabs_2026_05_08`** — Phase 8B here may collide on data-status drilldown surface. Banner
  mutually.
- **`master_to_live_defi_2026_05_23`** — pre-requisite for Group F/G live-only readiness. Add a folded-todo pointer in
  master plan's `### Group F` section: "features-repo consolidation pre-req for live-pipeline (see
  `features_repo_consolidation_2026_05_08.plan.md`)".
- **`infrastructure_master_2026_05_07`** — umbrella; no direct collision.
- **`mdps_streaming_and_backpressure_2026_05_07`** + **`mtds_databento_path_streaming_2026_05_07`** — independent (these
  are MDPS / MTDS internal refactors); no overlap.

## Temporary states + their canonical follow-up plans

This plan does NOT introduce any temporary state — Phase 7 deletes source repos cleanly, Phase 4 deletes per-family
duplicated config files cleanly, Phase 5 deletes per-family helper inlines in the same commit as the UTL lift.

The one transitional state is **between Phase 3 (subtree merges) and Phase 7 (archive source repos)**: during this
window, source repos exist on disk + GitHub but the canonical implementation is the consolidated repo. Operators who
manually launch source-repo VMs during this window will hit stale code; mitigation is the "Cross-Plan Coordination
Banners" rule (banner the source repos' last-pre-archive commits with `🟡 SUPERSEDED`) and Phase 8A's launcher migration
completing before Phase 7 archives the repos.

## Risk register

| Risk                                                                                            | Likelihood | Impact                               | Mitigation                                                                                                          |
| ----------------------------------------------------------------------------------------------- | ---------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| Phase 6 parity fails for a family due to floating-point reorder                                 | Medium     | Migration paused for that family     | Tolerance covers float reorder; if a family genuinely diverges, root-cause via per-calculator diff before reverting |
| Cross-family import rewrite missed in Phase 4                                                   | Medium     | Runtime ImportError on consumer repo | Phase 0 pre-audit § (b) is exhaustive; Phase 10 workspace-wide QG sweep catches any missed reference                |
| `git subtree` not available on agent's machine                                                  | Low        | Phase 3 stalls                       | Document `brew install git-subtree` (or use `git-subtree.sh` from git-core/contrib) at Phase 3 start                |
| Operator launches a source-repo VM during transition window                                     | Low        | Confusing data-status output         | Phase 8A migration + banner discipline; transition window ≤2 days                                                   |
| Workspace-manifest agents (plan-health, conflict-resolution) flag the 8 archived repos as drift | Low        | Noise in agent reports               | Phase 7 step 5+6 removes them from workspace-manifest in the same commit                                            |
