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
      - [x] [AGENT] P0. Phase 0 — Pre-audit manifest (read-only). Produce a single artifact under
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

        **SHIPPED 2026-05-08** — artifact at `plans/active/issues/features_repo_consolidation_preaudit_2026_05_08.md`
        (1286 lines / 152 KB). 503 py source files; **only 11 external Python import lines to rewrite** (Phase 4.1
        footprint much smaller than plan body assumed); 51 string references (test-params + openapi catalogues +
        .gitignore) for case-by-case manual fixup; 6 lift candidates + 4 NOT-implemented-anywhere helpers documented.
        Big findings folded into Phase 4/5 sub-todos below + audit-findings section after risk register.
    status: completed
    note: "general-purpose sub-agent shipped artifact 2026-05-08; read-only audit, no code commits."

  - id: phase-1a-uac-feature-family-schema
    content: |
      - [x] [AGENT] P0. Phase 1A — Add `feature_family` to UAC v5 manifest schema. PARALLEL with 1B.

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

      **SHIPPED 2026-05-08 — UAC@`7f63ca3`.** Site decision: placed in `canonical/domain/features/registry.py`
      (alongside `EXPECTED_FEATURE_GROUPS_BY_SERVICE` dependency) rather than `crosscutting/honest_coverage.py` —
      natural locality + plan body says "or the equivalent v5 manifest schema SSOT". Files: registry.py (+139),
      features/__init__.py (+10 facade re-export), tests/unit/test_feature_family.py (+160, 9 tests). Mapped 83
      feature_groups across 5 services (onchain=12, delta_one=36, sports=35; volatility/cross_instrument empty
      stubs; calendar/commodity/multi_timeframe families have 0 mapped today — registry will populate as those
      services declare). **No cross-family collisions detected.** QG: foreign-code lint failure on
      `_instrument_enums.py:52` E501 (parallel agent's uncommitted; not mine); my files clean (0 ruff, 0 basedpyright);
      9 new tests pass + 18 existing test_feature_dag_ssot.py tests still pass.
    status: completed
    note: "Sub-agent shipped UAC@7f63ca3, pushed clean (0 0 vs origin)."

  - id: phase-1b-utl-manifestwriter-feature-family-param
    content: |
      - [x] [AGENT] P0. Phase 1B — `ManifestWriter.record_captured` / `record_empty` / `record_failed` /
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

      **SHIPPED 2026-05-08 — UTL@`c16cef3`.** Files: manifest_writer.py (+217), __init__.py (+2 — export
      MissingFeatureFamilyError), tests/unit/test_manifest_writer_feature_family.py (+260, 10 tests).
      **Design choice — enforcement gate**: implemented `feature_group is set ⇒ feature_family required` shape (NOT
      CLI-detection). Specifically `if effective_feature_group and not feature_family: raise` where "effective"
      considers both row_key.feature_group AND the direct kwarg. Cleaner than CLI introspection;
      ManifestWriter doesn't need to know about service CLIs. Documented in `MissingFeatureFamilyError` docstring.
      **Production-safety verified**: the 8 features-* services use `writer.add(...)` not `record_captured(...)` —
      the new gate fires on the four record_* methods only. `add()` unchanged. **No in-flight VMs break.**
      QG: pre-existing failures only (verified via git-stash ablation: 7 E501s in manifest_writer.py:145-160 /
      1441 / 1449 attribute to commit 68b3804a 2026-05-07 semver-bot; 12 pre-existing basedpyright errors;
      11 pre-existing test failures in test_manifest_writer_capture_status/v6/v7/normalising/record_empty_reason —
      all foreign, all from 2026-05-07 LegacyBlankErrorReasonError hardening). My new test file: 0 ruff, 0 basedpyright,
      10/10 tests pass. Phase 4 follow-ups documented below: add() migration, validate_df kwarg, NormalisingManifestWriter cleanup.
    status: completed
    note: "Sub-agent shipped UTL@c16cef3, pushed clean (0 0 vs origin)."

  - id: phase-2-create-features-service-repo
    content: |
      - [ ] [HUMAN+AGENT] P0. Phase 2 — Create the `features-service` repo with skeleton + ONE flat `pyproject.toml`
        + ONE Dockerfile + ONE quality-gates.sh + ONE buildspec.aws.yaml + ONE cloudbuild.yaml.

        `git init` + `git remote add origin git@github.com:CosmicTrader/features-service.git`. Workspace rules
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

        **PARTIAL 2026-05-08 — local skeleton ready at `${WORKSPACE_ROOT}/features-service` (commit `1f2bc16`).**
        31 files / 5,425 insertions. 46 unique deps unioned across 8 source repos (pin-conflict resolutions:
        `unified-trading-library>=0.3.0,<1.0.0` upward-intersected; `fastapi>=0.115.0,<1.0.0` added explicitly per
        "no fallback imports / direct usage = direct dep" rule — was transitive in source repos via UTL).
        Smoke green: `python -m features_service --version` → `features-service 0.0.1` exit 0. Tests: 2/2 pass
        (`tests/unit/test_smoke.py`). basedpyright: 0 errors, 0 warnings, 0 notes on full `features_service/`.
        Pass 1 QG: green for ENVIRONMENT/AUTO-FIX/LINT/TESTS; only blocker is the expected operator-gate
        `test_repo_in_manifest` (PM `workspace-manifest.json` registration).

        **Remote status update (later 2026-05-08 by operator)**: empty GitHub remote created at
        `git@github.com:CosmicTrader/features-service.git` and configured as `origin` on the local repo. **Note**:
        deviates from the IggyIkenna org convention used by every other workspace repo per
        `unified-trading-pm/workspace-manifest.json` — captured as finding F9 below; operator decision.

        **Phase 2 unblocking checklist for operator** (status 2026-05-08 EOD):
        1. ✅ `gh repo create CosmicTrader/features-service --private --confirm` — DONE; remote configured as
           `origin` on the local skeleton.
        2. ⏸ Add `features-service` entry to `unified-trading-pm/workspace-manifest.json` — PENDING. Use
           `https://github.com/CosmicTrader/features-service` (NOT IggyIkenna) until the org-convention deviation
           (F9) is resolved by the operator.
        3. ⏸ `git push -u origin live-defi-rollout` from `${WORKSPACE_ROOT}/features-service` — PENDING. Pushes
           local commit `1f2bc16` (the skeleton) to the empty remote. After push, flip this checkbox to `- [x]`
           and proceed to Phase 3 subtree merges.

        Items 2 + 3 are operator-driven (main agent will handle the push timing per the workspace conditional-push
        protocol). Tab 2 sub-agent stops after this evidence committed; resumes on operator ack to start Phase 3.

    status: blocked
    note: "PARTIAL: local features-service@1f2bc16 with origin set to CosmicTrader/features-service; pending workspace-manifest entry + push."

  - id: phase-3-migrate-source-repos-with-history
    content: |
      - [ ] [AGENT] P0. Phase 3 — Migrate the 8 source repos into sub-packages, preserving git history.

        Use `git subtree merge` per source repo (NOT `git filter-branch` — it rewrites SHAs). For each source
        family `<f>` ∈ {calendar, commodity, cross_instrument, delta_one, multi_timeframe, onchain, sports,
        volatility}:

        **Branch correction (2026-05-08)**: pull from `live-defi-rollout` (the workspace `active_feature_branch`),
        NOT `main`. Verified during Phase 3 pre-flight — `main` is severely stale vs `live-defi-rollout` for every
        features-\* repo (onchain 67 commits behind, sports 85, delta-one 36). Subtree-merging from `main` would
        import stale source code that fails Phase 6 parity. The original plan-body said `main`; correction lands
        in this same edit.

        **`--squash=false` syntax correction (2026-05-08, F10)**: `git subtree add` only accepts `--squash` as a
        boolean flag (presence = squash, absence = no squash). `--squash=false` is invalid syntax and errors out.
        The correct command is just `git subtree add --prefix=... <repo> <branch>` (no `--squash`). Phase 3
        sub-agent caught this on first invocation and recovered by omitting the flag.

        1. `git subtree add --prefix=features_service/<f> ../features-<f>-service live-defi-rollout`.
           Even without `--squash`, the subtree-add produces a single squash-style commit referencing the source
           SHA in its message ("Add 'features_service/<f>/' from commit '<sha>'"). Source per-commit history is
           PRESERVED but `git log --follow` does NOT traverse the boundary — to see source-side history use
           `git log <source-sha> -- <path-in-source>`. This is canonical git-subtree behavior (F11).
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

        **PARTIAL 2026-05-08 — 25 commits added on top of `1f2bc16` (working tree clean, NOT pushed).**
        Per-family commit shape was 3 commits (not 2): stub-removal (Phase 2 `__init__.py` placeholder blocked
        `git subtree add --prefix=...` on existing prefix) + subtree-add merge + restructure. Final `git log`
        ladder: `b144552d` (sports restructure) → `1f2bc164` (Phase 2 skeleton baseline). Order processed
        smallest-to-largest per F5 (sports last for partial-failure recovery): commodity (80 files moved) →
        multi_timeframe (87) → calendar (108) → cross_instrument (124) → volatility (142) → onchain (169) →
        delta_one (216) → sports (207).

        **Phase 4 import-rewrite scope (well-defined per Phase 3 grep)**:
        - `features_service/`: 752 same-family `from features_<f>_service` occurrences (commodity=31,
          multi_timeframe=51, calendar=63, cross_instrument=100, volatility=77, onchain=114, delta_one=154,
          sports=154).
        - `tests/`: 1607 same-family + 1 cross-family (delta_one tests/ imports features_calendar_service —
          matches F4 audit exactly).
        - Total: 2360 occurrences. Mass sed pattern: `s/from features_<f>_service\b/from features_service.<f>/g`
          per family, plus 1 cross-family rewrite.

        **Special-case handling captured in Phase 3 (forwarded to Phase 4 if redo needed)**:
        - Sports had TWO scripts/ directories — top-level `scripts/` (16 files) AND intra-package
          `features_sports_service/scripts/` (3 files). Resolved by renaming intra-package to `_intra_scripts/`
          first to break the destination-already-exists collision on `git mv features_sports_service/* .`, then
          merging both into `scripts/sports/` (19 files combined).
        - Per-family doc retention was inconsistent (kept README/docs/CHANGELOG/CONTRIBUTING/LICENSE for some
          families, not others). Captured as F11 — Phase 4 should make a deliberate uniform per-family-doc
          decision (retain README only? retain none? retain all?).

        **Push pending (Phase 3 local-only)**: 25 local commits sit at HEAD on `live-defi-rollout`. Main agent
        owns push timing — same workspace-conditional-push protocol as Phase 2 push (also pending).

    status: blocked
    note: "PARTIAL: 25 local commits in features-service on top of 1f2bc16; push pending main agent (along with Phase 2 push); Phase 4 import-rewrite scope mapped + ready."

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

             **SHIPPED 2026-05-08 (Tab B — Wave-2 Phase 4.4 in work-split terminology)**: features-service@726af91d.
             Aggregator wires 8-family `_data_freshness` probes via lazy importlib resolution; aggregate shape is
             `{"families": {...}, "loaded_families": [...], "healthy": bool}` (the `healthy` flag flips False if any
             family probe raises but stays True for cold-start `stale=True, last_processed_date=None` per docstring).
             Per CLAUDE.md "No double SSOT in data-saving methodology": no per-family `health.py` stubs were created —
             each family's existing `_data_freshness` in `<family>/api/main.py` (subtree-merged from source repos) is
             the SSOT; the aggregator imports those at runtime. delta_one's pre-existing `api/health.py` (full-health
             shape, distinct from freshness) was left untouched. 11 tests in `tests/api/test_health_router.py` pass:
             registry shape, cold-start aggregate, partial-progress, exception propagation, /health 200,
             all-families-present, single-family-failure resilience, create_app routes, /readiness 200.

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
      - [x] [AGENT] P0. Phase 8A — Migrate any existing features-*-service VM launchers to the consolidated
        layout. Per workspace VM launcher SSOT rule
        (`codex/05-infrastructure/launcher-script-ssot.md` + `CLAUDE.md`), every launcher MUST live in
        `deployment-service/scripts/vm/`.

        Shipped 2026-05-08 PM (Tab 8A):

        - **deployment-service@2942815** — new `scripts/vm/launch-features-vm.sh` parameterised by
          `--feature-family <name>` + `--asset-group <name>` + `--start-date` + `--end-date` + `--mode` +
          `--launch-mode {dry,full}`. VM-name pattern `features-{family-dashed}-{asset_group_lower}-{ts}`.
          Per-VM shard isolation (`MANIFEST_PER_VM_SHARDS=true` + `VM_NAME=<unique-tag>`) +
          `VM_SHUTDOWN_ON_COMPLETION=true` + opt-in `FEATURE_GROUP` / `SKIP_DEPENDENCY_CHECK` / `FORCE` env
          overrides per legacy launcher conventions. Viability-matrix guard preserved (8 family × 5
          asset_group cells; calendar treats `GLOBAL` as the special no-asset_group case).
        - **deployment-service@2942815** — `vm_zombie_watchdog.py` `features-` heartbeat-only entry comment
          updated to enumerate the 8 consolidated families + cite Phase 8A. The catch-all prefix already
          covered all `features-{family}-{asset_group}-{ts}` VM names; no new dict entry required.
        - **deployment-service@2942815** — `launch-features-backfill-vm.sh` +
          `launch-features-onchain-backfill-vm.sh` deprecated with banner-only redirect note (callers
          continue to work — they delegate to the same code shape; new callers should use the consolidated
          launcher directly). 4 specialty launchers (`launch-features-sports-backfill-vm.sh`,
          `launch-features-sports-parallel-backfill-vm.sh`, `launch-prediction-features-vm.sh`,
          `launch-sfi-progressive-features-backfill-vm.sh`) retain their unique semantics
          (singleton-lock / chunk-split / specialty entry-point) until Phase 7 archives the source repos
          + the specialty scripts migrate into `features_service`.
        - **deployment-api@b91bca2d** — `_SERVICE_LAUNCHER_SCRIPTS` in
          `deployment_api/services/deploy_missing.py` updated: every legacy `features-<family>-service` slug
          + the new `features-service` slug + two previously-missing slugs
          (`features-commodity-service`, `features-multi-timeframe-service`) all point at the consolidated
          `launch-features-vm.sh`. The Deploy-Missing UI button now generates the parameterised launcher
          CLI for all 8 family slugs.

        Bash-syntax check (`bash -n`) clean on all 7 modified launchers + new launcher; Python AST parse
        clean on `vm_zombie_watchdog.py` + `deploy_missing.py`. `--help` smoke verified the new launcher
        prints the standardised flag set.

        **DEFERRED (operator-driven)**: relaunching `vm-zombie-watchdog` (the running watchdog only fetches
        the Python at boot — dict change doesn't propagate live). Since the comment-only update in
        `VM_PREFIX_TO_BUCKET` doesn't change watchdog behaviour (the `features-` heartbeat-only entry was
        already present), the relaunch is non-urgent — operator may include it in the next routine
        watchdog rotation rather than a dedicated bounce. Per workspace rule the relaunch command is:
        `gcloud compute instances delete vm-zombie-watchdog-* --zone=asia-northeast1-c --quiet && bash
        deployment-service/scripts/vm/launch-vm-zombie-watchdog.sh`.

        **Coordination**: `launcher_scripts_consolidation_into_deployment_service_2026_05_07.plan.md`'s
        features-* migration items become a no-op once Phase 7 archives the source repos. The launcher
        consolidation plan was NOT banner-edited this cycle (parallel-agent surface); the
        cross-reference is captured here for read-back.
    status: done
    note: "shipped 2026-05-08 PM Tab 8A; deployment-service@2942815 + deployment-api@b91bca2d. Watchdog relaunch deferred to next routine rotation."

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
      - [x] [AGENT] P0. Phase 9 — Codex SSOT updates. PARALLEL with Phase 8.

        Per the workspace "Post-Plan-Phase Codex Audit" rule (CLAUDE.md, codified 2026-05-08), this phase
        creates the consolidation architecture doc + updates 5 existing docs.

        New + updated docs (all shipped 2026-05-08 PM by Wave-3 Tab PM-CODEX):
        1. **NEW** `codex/04-architecture/features-service-architecture.md` — PM@2e5ca4e7. Replaces 4.5KB
           stub with full SSOT: 8 family sub-package layout, CLI dispatch contract, Health-API aggregator,
           UAC FeatureFamily enum + manifest column, 7 UTL Phase 5 lifts table, deployment topology
           (asset-scoped colocated + cross-cutting flavors), migration history, anti-patterns table.
        2. **UPDATE** `codex/06-coding-standards/feature-service-pattern.md` — PM@9edb649c. Updated "5-6
           separate" → "8 separate" predecessor repos enumerated by name; added cross-link to architecture
           SSOT; new 7-step "Adding a new feature_family" recipe (UAC enum first, sub-package shim, calculator
           class, Health-API freshness callback, ManifestWriter, tests, no new launcher).
        3. **UPDATE** `codex/06-coding-standards/cli-convention.md` — PM@e0121b42. Added --feature-family row
           to optional axes table (UAC FeatureFamily enum 8 members); new "--feature-family for the
           consolidated features-service (2026-05-08)" section with full dispatcher contract.
        4. **UPDATE** `codex/02-data/data-status-drilldown-hierarchy.md` — PM@f5be06ce. Replaced 5 per-repo
           features rows with 9-row block (1 consolidated header + 8 per-family sub-rows showing
           feature_family as outermost axis); new blockquote callout introducing feature_family axis.
        5. **UPDATE** `codex/00-SSOT-INDEX.md` — PM@1d0ee16e. Registered features-service-architecture.md
           under Architecture section with full row body summary.
        6. **UPDATE** `codex/05-infrastructure/launcher-script-ssot.md` — PM@f128e8c9. New "features-service
           consolidation (2026-05-08)" section enumerating 8-to-1 launcher collapse (single
           launch-features-vm.sh parameterised by --feature-family + --asset-group); single `features-`
           prefix in VM_PREFIX_TO_BUCKET; tarball impact callout.

        Bonus update (helpful cross-link, not in original 6-item list):
        7. **UPDATE** `codex/05-infrastructure/vm-tarball-deployment.md` — PM@20a4910a. New paragraph block
           noting tarball-side implications of the 8-to-1 features-* repo consolidation:
           --asset-group flag includes single features-service/ (not 8 per-family repos); VM boot:
           python -m features_service --feature-family X (replaces 8 distinct entry-points).

        QG: `unified-trading-pm` quality-gates.sh clean. Plan-health agent picks up the SSOT additions on the
        next run.
    status: done
    note: "shipped 2026-05-08 PM Wave-3 Tab PM-CODEX; 7 commits PM@2e5ca4e7 / 9edb649c / e0121b42 / f5be06ce / f128e8c9 / 20a4910a / 1d0ee16e"

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

## Phase 0 audit findings — discoveries to fold into later phases

Discovered during Phase 0 read-only audit (artifact at
[`plans/active/issues/features_repo_consolidation_preaudit_2026_05_08.md`](issues/features_repo_consolidation_preaudit_2026_05_08.md))

- Phase 1B implementation surprises. All findings adjacent-to-this-plan per Findings Triage Discipline; folded in here
  rather than punted to issues folder. Plan-body Phase 4/5 todos reference these sub-todos.

### F1 — LookaheadBiasError silently underprotected in 6 of 8 families ⚠️ data-correctness

**Severity**: P0 / data-correctness / contradicts CLAUDE.md "Shard-granularity SSOT" rule ("`LookaheadBiasError` raised
loud at every features-\* + MDPS compute, not warn-mode").

**Status today** (per Phase 0 audit § 9.3):

- `features-onchain-service` ✅ enforces production-side
- `features-sports-service` ✅ enforces production-side
- `features-calendar-service` ❌ references only in tests
- `features-cross-instrument-service` ❌ references only in tests
- `features-multi-timeframe-service` ❌ references only in tests
- `features-volatility-service` ❌ references only in tests
- `features-commodity-service` ❌ **zero references**
- `features-delta-one-service` ❌ **zero references**

**Action — add Phase 5 sub-todo**: while lifting `LookaheadBiasError` per the existing Phase 5 todo, ALSO extend the
gate to fire production-side in all 8 families. Each family's compute entry-point gets an
`assert_no_lookahead_for_feature_group(...)` call before processing inputs. Per-family unit tests asserting raise on
stale input. Lands as part of the same logical unit as the helper lift to UTL (avoids two churn cycles).

### F2 — `features-onchain-service/config.py` does not import `UnifiedCloudConfig` ⚠️ SSOT-violation

**Severity**: P1 / workspace SSOT violation per CLAUDE.md Key Rules ("`UnifiedCloudConfig` / `config.key_name` — never
`os.getenv('KEY', '')`"). Other 7 features-\* repos all import it.

**Action — add Phase 4 sub-todo (4.7)**: during the import-rewrite + config-consolidation sweep, audit
`features_service/onchain/config.py` (post-Phase 3 location) for bare `os.getenv` calls; replace with
`UnifiedCloudConfig` access. One-shot fix, lands with the rest of Phase 4.

### F3 — High-leverage lifts beyond plan-body's 4 helpers — extend Phase 5 lift list

**Severity**: P1 / scope expansion — saves duplicated maintenance across consolidated repo.

Per Phase 0 audit § 9, the following NOT-LIFTED dups were discovered in addition to the plan-body's 4 helpers:

- **`BuilderEntry`** — 7-way duplicate (7 of 8 repos copy-paste same dataclass). UTL already has `feature_calculator/`
  - `feature_service_base/` modules — natural home. Single highest-leverage lift.
- **`BroadcastSink` / `LiveDataSource`** — 4-way duplicate (calendar / delta_one / onchain / volatility).
- **`BaseFeatureCalculator`** — 3-way duplicate (cross_instrument / delta_one / multi_timeframe).
- **`FeatureBatchHandler`** — NOT IMPLEMENTED anywhere; every family has copy-paste batch_handler. Coordinate with
  `ml_and_features_master_2026_05_07` Phase 2.UTL-LIFT (which lifts FeatureBatchHandler for the 4 features-\* repos that
  have it) — that work overlaps; banner mutually.
- **`ManifestFreshnessCache`** — NOT IMPLEMENTED in UTL or any features-\* repo (per `ml_and_features_master` Phase
  1A.UTL-CACHE-ADOPT).
- **`WatermarkAlignmentFanin`** — NOT IMPLEMENTED anywhere — greenfield in UTL (already in plan-body Phase 5 list).

**Action — extend Phase 5 todo** to cover these (BuilderEntry + BroadcastSink/LiveDataSource + BaseFeatureCalculator in
addition to plan-body's 4). Total Phase 5 scope: 7 lifts + the LookaheadBiasError extension to 6 families + the optional
FeatureBatchHandler / ManifestFreshnessCache greenfields if not landed by `ml_and_features_master` first.

### F4 — Phase 4.1 cross-family import rewrite footprint is much smaller than assumed

**Severity**: P2 / scope-shrink (good news).

Plan-body Phase 4.1 talked about `features_<f1>` importing from `features_<f2>` as a routine concern (cross-instrument
depending on delta-one outputs, etc.). **Phase 0 audit found ZERO production cross-family imports.** Only ONE
cross-family Python dep exists workspace-wide: `features-delta-one-service/tests/unit/.../test_temporal.py` imports
`features_calendar_service`. Phase 4.1's grep+sed pass is essentially trivial — one test-file rewrite + the 11 external
import lines documented in Phase 0 § (b).

**Action — none required.** Phase 4.1 is shorter than scoped; no plan change. Documented for future agent so they don't
expect to find dozens of cross-family imports.

### F5 — `features-sports-service` is the largest family by every dimension

**Severity**: P2 / Phase 3 sequencing.

Sports = 111 files / 56 tests / 15 scripts / 20 sub-packages (3× the median repo). Has its own intra-package
`features_sports_service/scripts/` alongside top-level `scripts/`. Phase 3 step ordering: do sports LAST among the 8
subtree merges so a partial-failure recovery can still ship the other 7 cleanly. Or split sports into a checkpoint
(separate per-family commit per existing plan, but observe wall-clock there).

### F6 — Phase 1B production-safety: `add()` legacy method requires Phase 4 migration

**Severity**: P0 / dependency for Phase 4.

Phase 1B's enforcement gate (`feature_group is set ⇒ feature_family required`) fires on `record_captured` /
`record_empty` / `record_failed` / `record_expected_empty`. The 8 features-\* services CURRENTLY call `writer.add(...)`
which is the legacy public API path. `add()` was deliberately NOT modified by Phase 1B — it writes `feature_family=""`
rows for features services as a back-compat shape, so existing VMs are unaffected. **Phase 4 MUST migrate features-\*
call sites from `writer.add(...)` to `writer.record_captured(...)` with `feature_family` passed**, otherwise the
consolidated `features-service` repo writes manifest rows with `feature_family=""` and the deployment-UI's Phase 8B
drilldown column renders empty. Add as Phase 4 sub-todo (4.8).

**🟡 BLOCKED 2026-05-08 — Tab C F6 migration agent surfaced architectural gap.** `record_captured()` requires a
`df: pd.DataFrame` kwarg (mandatory `assert_available_at_present(df)` + schema validation against UAC contract
registry; row count derived from `len(df)`). All 18 features-service `writer.add()` callsites — across 8 families,
precise audit complete — happen at manifest-flush time AFTER the per-shard parquet has been written via helpers
like `_write_per_league` / `write_sports_table` / `save_features_to_gcs`. **The df is not in scope at the
callsite**; only `row_count` (from `table_row_counts: dict[str, int]`) is.

Three options for resolution — issue doc with full analysis + recommended-decision matrix:
[`plans/active/issues/f6_record_captured_requires_df_features_consolidation_2026_05_08.md`](issues/f6_record_captured_requires_df_features_consolidation_2026_05_08.md).
Summary of options:

- **Option A** (~1 day): extend `ManifestWriter.add()` with `feature_family: str = ""` kwarg + sed-migrate 18
  callsites. Satisfies F6's user-visible acceptance criterion (deployment-UI Phase 8B drilldown column
  populated) without the deeper contract migration. Leaves `record_captured()` migration for a future plan.
- **Option B** (~3-5 days): refactor df-flow per family so the captured df reaches the manifest write site,
  enabling true `record_captured()` migration with full schema validation. Architectural target but multi-day
  upstream refactor.
- **Option C** (hybrid): Option A this cycle (closes F6 user-visible benefit) + Option B as a named follow-up
  in Phase 5 or a new sub-plan.

**Tab C did NOT ship migrations** — naive substitution would break at runtime on every call (LookaheadBiasError
from `assert_available_at_present(df)` with no df). Awaiting operator triage A / B / C before re-spawning.

**Precise 18-site audit** (preserved here so future agent doesn't re-grep):

| Family            | File:Line                                                  | feature_group target           |
| ----------------- | ---------------------------------------------------------- | ------------------------------ |
| calendar          | calendar/engine/calendar_orchestrator.py:373               | per-`feature_group` arg        |
| onchain           | onchain/engine/orchestrator.py:182                         | per-`feature_group` arg        |
| volatility        | volatility/engine/orchestrator.py:192,198                  | options_volatility (per-tf + agg) |
| volatility        | volatility/engine/orchestrator.py:262,268                  | futures_term_structure (per-tf + agg) |
| volatility        | volatility/engine/orchestrator.py:635,641                  | per-`feature_group` arg (per-tf + agg) |
| commodity         | commodity/cli/handlers/batch_handler.py:269                | per-`feature_group` arg        |
| sports            | sports/cli/handlers/batch_handler.py:797,805               | base_table (with/without league) |
| delta_one         | delta_one/engine/orchestrator.py:316,322                   | per-`feature_group` arg (per-tf + agg) |
| cross_instrument  | cross_instrument/cli/handlers/batch_handler.py:472,479     | per-`feature_group` arg        |
| multi_timeframe   | multi_timeframe/engine/orchestrator.py:254,261             | per-`feature_group` arg        |

### F8 — PM `coverage-floor-guard` MIN_COVERAGE path bug (workspace-wide, cosmetic)

**Severity**: P3 / cosmetic / out-of-scope for this plan.

`unified-trading-pm/scripts/qg-helpers/base-service.sh:194` computes
`_REPO_QG_SCRIPT="$(dirname ${BASH_SOURCE[0]})/../../scripts/quality-gates.sh"` which resolves to PM's own QG
(since `BASH_SOURCE[0]` is the PM-hosted base-service.sh), not the calling repo's QG. So `MIN_COVERAGE` is read
from PM's `MIN_COVERAGE=70` regardless of the consumer setting. Surfaces as spurious
`MISMATCH: MIN_COVERAGE=70 but pyproject.toml fail_under=0` warning during every consumer-repo QG run.

**Action**: not in scope for `features_repo_consolidation_2026_05_08`. Discovered during Phase 2 features-service
QG run. Affects every Python consumer repo running `bash scripts/quality-gates.sh`. Tag: out-of-plan finding;
suggested owner: whoever maintains PM's `qg-helpers/base-service.sh` (Ikenna's side per work-split rule on
"Governance / ratchet thinking"). If the cosmetic warning is annoying, fix should compute the consumer-repo path
via `$PWD` or a passed-in env var, not via `BASH_SOURCE` math.

### F7 — Phase 1B follow-ups: `validate_df` + `NormalisingManifestWriter` need Phase 4/5 attention

**Severity**: P2 / Phase 4-5 scope.

- `validate_df` (UTL public) doesn't accept `feature_family` kwarg today. Strict-mode schema-mismatch paths via this
  function that have `feature_group` set in row_key would trigger the gate. Add as Phase 4 sub-todo (4.9).
- `manifest_writer_normalising.py` (`NormalisingManifestWriter` wrapper) doesn't accept `feature_family` either; only
  test callers exercise it; broken anyway today (calls `record_empty` with no reason → `LegacyBlankErrorReasonError`).
  Phase 5 sub-todo (lift or delete).

### F10 — Plan-body `git subtree add --squash=false` syntax invalid; corrected in-place

**Severity**: P3 / plan-body bug / corrected.

`git subtree` only accepts `--squash` as a boolean flag (presence = squash, absence = no squash). The original
plan-body Phase 3 step 1 specified `--squash=false`, which errors out. Phase 3 sub-agent caught the failure on
first invocation and recovered by omitting the flag entirely. Plan body has been updated in-place.

**Action**: none required — corrected. Future agents reading the plan see the right syntax.

### F11 — `git subtree add` produces squash-style merge commit even without `--squash` (canonical behavior)

**Severity**: P2 / expectation calibration / no fix needed.

Plan body claimed the absence of `--squash` would preserve per-commit history queryable via
`git log --follow`. **Reality**: even without `--squash`, when the prefix is brand-new, `git subtree add` produces
a single squash-style commit ("Add 'features_service/<f>/' from commit '<sha>'") rather than a true non-squashed
merge with all source commits replayed. Source SHAs ARE preserved (in commit messages); to see source-side
history use `git log <source-sha> -- <path-in-source>`. `git log --follow` does NOT traverse the squash boundary.

**Action**: accept this — it's the documented git-subtree behavior. Phase 6 parity test isn't impacted (test
operates on parquet outputs, not git history). Decision recorded for future agents who go looking for per-file
history and find a single import commit.

### F12 — Stray `=0.3.0` file in `features-cross-instrument-service` source repo

**Severity**: P3 / out-of-plan finding / file as separate issue.

Phase 3 sub-agent discovered a literal file named `=0.3.0` (140 bytes, contents = stdout of an `uv pip install`
run that got redirected via shell-glob bug `>= 0.3.0`) in the `features-cross-instrument-service` source repo.
Stripped during Phase 3 restructure. **Out-of-scope for this plan** — but worth filing as an issue against the
source repo before Phase 7 archives it (otherwise the bug history is preserved in the consolidation merge but
the source-repo commit is not addressable as a regression).

**Action**: file separately under `unified-trading-pm/plans/active/issues/features_cross_instrument_stray_file_2026_05_08.md`
when the operator has cycles. NOT this plan's responsibility. Captured here so the finding doesn't evaporate.

### F9 — `features-service` GitHub remote deviates from workspace IggyIkenna org convention ⚠️ org-naming

**Severity**: P2 / org-convention drift / requires operator decision.

The empty GitHub remote for the new `features-service` repo was created at
`git@github.com:CosmicTrader/features-service.git` (operator action, late 2026-05-08). Every other repo in
`unified-trading-pm/workspace-manifest.json` uses `https://github.com/IggyIkenna/<repo>` (verified workspace-wide;
all sibling features-\* / unified-\* / market-\* / instruments-\* / deployment-\* / etc. live under `IggyIkenna`).

**Possible explanations**: (a) deliberate operator choice to start the consolidated repo under a different
organisation (e.g. for billing / IP / collaboration reasons); (b) the workspace is in the middle of an
`IggyIkenna → CosmicTrader` org migration we don't yet know about; (c) typo / transient choice that the operator
intends to correct.

**Action required**: operator confirms which org should own the long-term `features-service` repo. If
`CosmicTrader` is correct, the workspace-manifest entry must use the matching URL + the workspace-wide convention
note in `unified-trading-pm/codex/` should document the new pattern (otherwise subsequent agents will assume
`IggyIkenna` per the current manifest pattern and clone the wrong remote). If the intended org is `IggyIkenna`,
the operator can `gh repo rename` or recreate. Tab 2 honours whichever decision lands but until then defaults
plan-body references to the actually-configured `CosmicTrader/features-service` (the local repo's `origin`).

This finding is **out-of-scope for the consolidation plan itself** but inside scope for the Phase 2 hand-off —
flagged here so subsequent agents reading this plan body don't trip on the convention mismatch.

---

## DONE-2026-05-08

Phase 0 + Phase 1A + Phase 1B shipped today by the `features-consolidation-tab` (Tab 2 of
[`plans/active/work_split_2026_05_08_harsh.md`](work_split_2026_05_08_harsh.md)). Phase 2 LOCAL skeleton committed
locally. Empty GitHub remote at `git@github.com:CosmicTrader/features-service.git` created by operator + configured
as `origin` on the local skeleton (later 2026-05-08). **Phase 2 push pending** — main agent handles the push timing
per the workspace conditional-push protocol; workspace-manifest.json entry registration also pending.

| Phase                                                                    | Repo                    | Commit                | Push                   | Notes                                                                                                                                                                                        |
| ------------------------------------------------------------------------ | ----------------------- | --------------------- | ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0 — pre-audit manifest                                                   | unified-trading-pm      | PM@`1de574b4`         | ✅ pushed              | 1286 lines, 152 KB; 503 py source files; 11 ext imports + 51 string refs                                                                                                                     |
| 1A — UAC FeatureFamily enum + FEATURE_GROUP_TO_FAMILY registry           | unified-api-contracts   | UAC@`7f63ca3`         | ✅ pushed              | 83 feature_groups mapped, no cross-family collisions, 9 unit tests                                                                                                                           |
| 1B — UTL ManifestWriter feature_family kwarg + MissingFeatureFamilyError | unified-trading-library | UTL@`c16cef3`         | ✅ pushed              | gate: feature*group ⇒ feature_family required; 4 record*\* methods; 10 unit tests; production-safe (`add()` unchanged)                                                                       |
| 2A — Phase 2 PARTIAL evidence + F8 audit finding (PM)                    | unified-trading-pm      | PM@`0c8800b8`         | ✅ pushed              | Captured Phase 2 PARTIAL state; `0c8800b8` is the rebased equivalent of original local commit `6eba7e4a` after operator integrated parallel-agent commits.                                   |
| 2B — features-service LOCAL skeleton (push pending)                      | features-service (NEW)  | features-svc@`1f2bc16` | ⏸ remote ready, push pending | 31 files / 5425 lines; 46 deps unioned; smoke + 2/2 tests + basedpyright clean; Pass 1 QG green except expected operator-gate (workspace-manifest registration). Origin set to `CosmicTrader/features-service`; awaiting workspace-manifest entry + operator-driven push. |
| 3 — 8 subtree merges + per-family restructure                            | features-service        | features-svc@`b144552d` (25 commits stacked over `1f2bc16`)                          | ✅ pushed (with Phase 2)              | 8 families subtree-merged in size order (commodity → sports). Per-family commit shape = 3 (stub-removal + subtree-add + restructure). Stripped duplicated top-level config per family; moved tests + scripts to consolidated tree. Working tree clean.                                                  |
| 2+3 PUSH — features-service initial push                                 | features-service        | HEAD `b144552d` to remote                                                            | ✅ pushed                             | `git push -u origin live-defi-rollout` to `git@github.com:CosmicTrader/features-service.git`; 26 commits landed (Phase 2 skeleton + 25 Phase 3 subtree/restructure); divergence `0 0` post-push.                                                                                                          |
| 4.1+4.3+4.5 — mass import rewrites + root-config verify + QG             | features-service        | features-svc@`d8136d72` (9 commits stacked over `b144552d`)                          | ✅ pushed                             | 754 files rewritten across 8 families: per-family `from features_<f>_service` → `features_service.<f>` + 1 cross-family fix (tests/delta_one → calendar). Zero surviving import refs. Phase 2 root config (pyproject/Dockerfile/etc) verified intact. Smoke + tests green; QG inherits 410 foreign lints. |
| 4.2 — CLI lift (dispatching cli/main.py + per-family run() exports)      | features-service        | features-svc@`9135f6c4`                                                              | ✅ pushed                             | **SHIPPED 2026-05-08 PM (Wave-2 Tab A on Ikenna's machine)**: redo from scratch (Harsh's stash didn't cross machines per "Carry-over reality check" above). features-svc@`9135f6c4` (11 files / +562 −45): top-level `features_service/cli/main.py` rewrites the Phase 2 stub into a dispatch parser (--version + --feature-family + --dispatcher-help; `--help` bubbles to family) that forwards remaining argv verbatim to `features_service.<family>.run(argv)` via `importlib.import_module + getattr`. All 8 family `__init__.py` files (calendar / commodity / cross_instrument / delta_one / multi_timeframe / onchain / sports / volatility) now expose a thin `run(argv) -> int` that delegates through new shared helper `features_service/cli/_shim.py::run_via_sys_argv` (sys.argv-patch for legacy ServiceBootstrap mains; native argv pass-through for commodity which already accepts argv per its commodity-specific direct-invocation contract). Tests: `tests/unit/test_cli_dispatch.py` 19/19 PASS in 14.34s — coverage = `_FAMILIES` shape, --version subprocess exit-clean, missing/unknown family rejection (exit 2), parametrised dispatch routing per family, --operation/--mode/--asset-group flag forwarding, --feature-group forwarding, exit-code propagation, sys.argv fallback when argv=None, --dispatcher-help subprocess. Manual smokes: `python -m features_service --version` → 0; `python -m features_service --dispatcher-help` → 0; `python -m features_service --feature-family calendar --help` boots calendar's ServiceBootstrap argparse usage (proves shim forwards correctly through to legacy main_service_cli); `python -m features_service --feature-family commodity --help` shows commodity's parser (proves accepts_argv=True path). Pre-commit pathspec form (`git commit --only -- <files>`) used to avoid bundling Tab B's parallel Phase 4.4 unstaged plan-body edits. Pushed `9135f6c4` directly to `live-defi-rollout` with zero incoming commits at fetch-time. |

**Audit findings folded into plan**: F1-F12 above (LookaheadBiasError underprotection, UnifiedCloudConfig violation, 4
additional lift candidates, Phase 4.1 scope-shrink, sports-as-largest, `add()` migration dependency, validate_df +
NormalisingManifestWriter follow-ups, PM coverage-floor-guard MIN_COVERAGE path bug, **CosmicTrader vs IggyIkenna
GitHub-org convention deviation**, plan-body `--squash=false` syntax bug corrected in-place,
git-subtree squash-style behavior calibration, stray `=0.3.0` file in features-cross-instrument-service source).

## Phase 2 hand-off — operator action items (status late 2026-05-08)

The local `features-service` skeleton at `${WORKSPACE_ROOT}/features-service` is ready to push. **Three steps
unblock the rest of Phase 2-3**; current state below.

1. ✅ **Create the empty GitHub remote** (shared-state action, **DONE by operator late 2026-05-08**) — created at
   `git@github.com:CosmicTrader/features-service.git` and configured as `origin` on the local repo.
   Note: operator picked the `CosmicTrader` org rather than the `IggyIkenna` convention used by every other
   workspace repo — captured as F9 above; awaits operator confirmation that `CosmicTrader` is the long-term
   intended home (vs. typo / migration / etc.).

2. ⏸ **Register `features-service` in PM `workspace-manifest.json`** — PENDING. Use the
   `https://github.com/CosmicTrader/features-service` URL until F9 is resolved (or `IggyIkenna` if F9 resolves
   that direction). The existing 8 features-* entries are templates; copy one and adjust the name + git URL.
   Tier-classify as a service (not a library). Commit + push to PM via the main agent's normal flow.

3. ⏸ **Push the local skeleton** — PENDING (main-agent driven). Mechanics:
   ```bash
   cd ${WORKSPACE_ROOT}/features-service
   # origin is already set; verify with: git remote -v
   git push -u origin live-defi-rollout
   ```
   This pushes commit `1f2bc16` (the local skeleton) to the empty remote. After push lands cleanly:
   - Flip the `phase-2-create-features-service-repo` checkbox in this plan from `[ ]` to `[x]`.
   - Update the todo's `status` field from `blocked` to `completed`.
   - Update the DONE-2026-05-08 table's row 2B Push column from `⏸ remote ready, push pending` to `✅ pushed`.
   - Tab 2 (or fresh spawn) starts Phase 3 — 8 × `git subtree merge --squash=false ../features-<family>-service main`.

**Why steps 2 + 3 are not Tab 2's to do autonomously**: per CLAUDE.md "Conditional push (multi-agent safety
valve)", the main agent owns push timing during high-churn windows like today (Tab 2 + Tab 3 + Tab 4 + Tab 5 +
Ikenna's side all pushing concurrently). Tab 2 commits locally per shippable unit but defers the actual `git push`
to main agent so the workspace stays linear. The local commit is durable; it survives via the shared `.git/`
working tree across agent sessions until the main agent integrates + pushes.

**Cross-side handshake status (per work-split § "Cross-side handshakes")**:

- Harsh Tab 2 (features_repo_consolidation Phase 1-4) → Ikenna Tab 2 (live-pipeline Phase 4-7): **Phase 1 land announced
  here**; Ikenna Tab 2 unblocked from continuing past their Phase-1-dependent work.

- Harsh Tab 2 (ml-features-phase2a wires) → Ikenna Tab 2 (live-pipeline Phase 11 ServiceEmissionPolicy slice b): not yet
  — wires happen in Phase 4 (Tab 12 Q1 absorption) which is after Phase 2 gate.

**Hard gate state (end of 2026-05-08 session, Tab 2 stopping)**:

- ✅ Phase 2 — local skeleton (`1f2bc16`) + remote at `git@github.com:CosmicTrader/features-service.git` (F9
  CosmicTrader-vs-IggyIkenna convention deviation still pending operator confirmation).
- ✅ Phase 3 — 25 local commits subtree-merging + restructuring 8 families; HEAD at `b144552d`.
- ✅ Phase 2+3 PUSHED to `origin/live-defi-rollout` (operator-authorised mid-session, divergence `0 0` post-push).
- ✅ Phase 4.1+4.3+4.5 — mass import rewrites (754 files / 8 families + 1 cross-family fix) + Phase 2 root-config
  verify + smoke + tests + QG. 9 commits stacked, HEAD at `d8136d72`, pushed (divergence `0 0`).
- 🛑 Phase 4.2 — CLI lift was sub-agent-shipped through "all tests pass" stage but **operator-killed before
  commit/push**. WIP saved as `stash@{0}` in features-service local repo. Resume: `git stash pop` in next session.
- ⏸ Workspace-manifest entry registration in PM `workspace-manifest.json` for `features-service` — still pending.

**Remaining-in-this-plan but DEFERRED out of session scope (operator end-of-shift)**:

- Phase 4.2 final (commit/push the stashed CLI lift, or amend if shape needs adjustment).
- Phase 4.4 (Health-API per-family freshness wires).
- F2 (`features-onchain` `UnifiedCloudConfig` fix in `features_service/onchain/config.py`).
- F6 (`add()` → `record_captured` migration in 8 families' code).
- Phase 5 (helper lifts to UTL — F1 LookaheadBiasError extension + 4 plan-listed helpers + F7
  NormalisingManifestWriter + BuilderEntry/BroadcastSink/LiveDataSource/BaseFeatureCalculator dups).
- Phase 6 (parity test, gated by Phase 5).
- Phase 7 (HUMAN+AGENT — archive 8 source repos via `gh repo archive`).
- Phase 8A/8B/9 (multi-repo: launcher migration + deployment-api/ui wiring + codex SSOT updates).
- Phase 10 (workspace-wide QG sweep).
- ml_and_features_master Phase 3 (parquet column-pruning quick-win) — independent, ml-training-service.

**Resume protocol for next Tab 2 session**:

1. Read this plan body's DONE-2026-05-08 block (states what's shipped + what's stashed).
2. `cd ${WORKSPACE_ROOT}/features-service && git status` — should show clean working tree at `d8136d72`.
3. `git stash list` — should show `stash@{0}: On live-defi-rollout: Phase 4.2 mid-flight kill 2026-05-08 ...`.
4. `git stash pop` — restores 9 family `__init__.py` + `cli/main.py` rewrite + new `tests/unit/test_cli_dispatch.py`.
5. Sub-agent's last reported state was "All 15 tests pass" before the QG step. Verify smoke + tests still green
   (`python -m features_service --version` + `pytest tests/unit/test_cli_dispatch.py`), run QG, commit + push.
6. Continue with Phase 4.4 / F2 / F6 per plan + work-split scope.

## Continuation 2026-05-08 PM (Ikenna's main agent, parallel-tab session)

Operator directive: complete the full codebase-wide consolidation in this session (deployment-ui, VM scripts, codex
docs in canonical features-service style, full functional migration, quality gates, workspace manifest, deployment
topology DAG SSOT, internal+external dependency integration, plus residuals from active plans + `plans/epics/`).
Operator confirmed: (a) Phase 7 archival fires AFTER Phase 6 parity-green; (b) ml_and_features residuals (Phase
2A/2B + Phase 3) FOLD INTO this session; (c) up to 5 parallel sub-agents authorised. Picking up where Harsh's Tab 2
stopped on 2026-05-08 evening.

### Carry-over reality check (verified on Ikenna's machine, 2026-05-08 PM)

- **Harsh's Phase 4.2 stash is NOT here.** Stashes don't cross machines. `git stash list` in features-service =
  empty; local HEAD = `d8136d72`, divergence vs `origin/live-defi-rollout` = `0 0`. Decision: redo Phase 4.2 from
  scratch on Ikenna's side. cli/main.py is still the Phase 2 stub (`STUB — Phase 2 skeleton`).
- **F2 is a NO-OP.** `features_service/onchain/config.py` already imports `UnifiedCloudConfig` and extends it
  (subtree merge brought modern shape). Audit was reading pre-merge legacy state. Mark resolved with no code change.
- **F6 is real.** 2 `manifest.add(` call sites in `features_service/sports/cli/handlers/batch_handler.py`
  L797, L805; precise audit during F6 fix wave confirms the exact set across 8 families.
- **Workspace-manifest registration**: shipped now in this Wave 1.

### Wave-decomposed execution plan (5-parallel-agent cap)

Shared `.git/` working tree on Ikenna's machine forces wave structure: agents touching the same repo must work on
disjoint files OR run serially.

| Wave | Owner | Scope | Parallelism |
| ---- | ----- | ----- | ----------- |
| 1 | main (this agent) | Continuation header + workspace-manifest registration + F2 no-op flip | serial, ~30 min |
| 2 | 3 sub-agents | Phase 4.2 (cli/) ‖ Phase 4.4 (api/) ‖ F6 (manifest add→record_captured) | 3-way parallel; disjoint dirs |
| 3 | main + 1 sub-agent | Phase 5 — UTL helper lifts | 2 agents serially per helper |
| 4 | main | Phase 6 parity test → Phase 7 archive (gated on parity-green) | serial |
| 5 | 5 sub-agents | Phase 8A (deployment-service) ‖ Phase 8B-api (deployment-api) ‖ Phase 8B-ui (deployment-ui) ‖ Phase 9 (PM codex) ‖ ml_and_features Phase 3 (ml-training-service) | 5-way parallel; different repos |
| 6 | main | Phase 10 workspace QG sweep + session-end scoreboard + plan flips | serial |

Cross-cutting discipline: per-shippable-unit commit+push, stage-by-name OR pathspec form, bundle Edit→commit→push,
plan-flip in same logical unit, conditional push, deferred-work scoreboard at session-end.

### Cross-plan residuals folded in this session (per operator answer)

- **ml_and_features Phase 2A/2B** (8-service `assert_no_lookahead_for_feature_group` adoption) → Wave 3 Phase 5.
- **ml_and_features Phase 3** (parquet column-pruning, ml-training-service) → Wave 5 parallel sub-agent.


## Continuation 2026-05-08 PM (Ikenna's main agent, parallel-tab session)

Operator directive: complete the full codebase-wide consolidation in this session (deployment-ui, VM scripts, codex
docs in canonical features-service style, full functional migration, quality gates, workspace manifest, deployment
topology DAG SSOT, internal+external dependency integration, plus residuals from active plans + `plans/epics/`).
Operator confirmed: (a) Phase 7 archival fires AFTER Phase 6 parity-green; (b) ml_and_features residuals (Phase
2A/2B + Phase 3) FOLD INTO this session; (c) up to 5 parallel sub-agents authorised. Picking up where Harsh's Tab 2
stopped on 2026-05-08 evening.

### Carry-over reality check (verified on Ikenna's machine, 2026-05-08 PM)

- **Harsh's Phase 4.2 stash is NOT here.** Stashes don't cross machines — Harsh's `stash@{0}` lives on his working
  tree. Ikenna's `features-service/.git` shows `git stash list` = empty. Local HEAD = `d8136d72`, divergence vs
  `origin/live-defi-rollout` = `0 0`. **Decision**: redo Phase 4.2 from scratch on Ikenna's side (cli/main.py is
  still the Phase 2 stub per inspection — `STUB — Phase 2 skeleton`. Family `run()` entry-points to be added
  to each `features_service/<family>/__init__.py`; new `tests/unit/test_cli_dispatch.py` to be written.
- **F2 is a NO-OP.** `features_service/onchain/config.py` already imports `UnifiedCloudConfig` (line 13) and
  extends it (line 17) — the subtree merge brought the modern shape. Audit was reading the legacy
  `features-onchain-service` repo state pre-merge. Mark F2 resolved with no code change.
- **F6 is real.** `grep` finds 2 `manifest.add(` call sites in
  `features_service/sports/cli/handlers/batch_handler.py` lines 797, 805. Other families' `.add(` calls in the
  loose grep are dict/list/set call false-positives but a precise audit during the F6 fix wave confirms the
  exact set.
- **Workspace-manifest registration**: pending (Phase 2 hand-off step 2 above) — being shipped now in this Wave 1.

### Wave-decomposed execution plan (5-parallel-agent cap)

Shared `.git/` working tree on Ikenna's machine forces wave structure: agents touching the same repo must work on
disjoint files OR run serially. Wave plan:

| Wave | Owner | Scope | Parallelism |
| ---- | ----- | ----- | ----------- |
| 1 | main (this agent) | Continuation header + workspace-manifest.json registration + F2 no-op flip | serial, ~30 min |
| 2 | 3 sub-agents | Phase 4.2 (`features_service/cli/`) ‖ Phase 4.4 (`features_service/api/`) ‖ F6 (`<family>/calculator.py` + manifest call sites) | 3-way parallel; disjoint dirs |
| 3 | main + 1 sub-agent | Phase 5 — UTL helper lifts (UTL repo + 8-way de-dup across families) | 2 agents on UTL/features-service serially per helper |
| 4 | main | Phase 6 parity test → Phase 7 archive (gated on parity-green) | serial |
| 5 | 5 sub-agents | Phase 8A (deployment-service) ‖ Phase 8B-api (deployment-api) ‖ Phase 8B-ui (deployment-ui) ‖ Phase 9 (PM codex) ‖ ml_and_features Phase 3 (ml-training-service) | 5-way parallel; different repos |
| 6 | main | Phase 10 workspace QG sweep + session-end scoreboard + plan flips | serial |

Cross-cutting discipline (every wave):
- **Per-shippable-unit commit + push** — no batching. Wave-2 agents commit each shippable unit before main
  fans out Wave 3.
- **Stage by name** — no `git add -A`; pre-commit `git status` + `git diff --cached --stat` (no path arg) check.
- **Bundle Edit→add→commit→push into ONE Bash call** per Foot-gun #4 mitigation — prek-restore race guard.
- **Plan-flip in same logical unit as code commit** — plan checkbox flips ride with the work, not at session end.
- **Conditional push** — every push fetches first, zero incoming → push, any incoming → STOP + flag.
- **Deferred-work scoreboard at session-end** per HARD RULE Half 3 if any item lands non-final.

### Cross-plan residuals folded in this session (per operator answer)

- **ml_and_features Phase 2A/2B** (8-service `assert_no_lookahead_for_feature_group` strict-mode adoption) —
  folded into Wave 3 Phase 5 (LookaheadBiasError strict-mode adoption is the same surface).
- **ml_and_features Phase 3** (parquet column-pruning quick-win in ml-training-service) — folded into Wave 5 as a
  parallel sub-agent against ml-training-service. Independent of consolidation; same wave for parallelism only.
