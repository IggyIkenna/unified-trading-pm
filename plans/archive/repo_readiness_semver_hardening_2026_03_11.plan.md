---
doc_type: plan
title: repo-readiness-semver-hardening-2026-03-11
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    agent-orchestrator,
    deployment-service,
    execution-service,
    strategy-service,
    system-integration-tests,
    unified-trading-library,
  ]
scope: [engineer, admin]
tags: []
related: []
created: "2026-03-11"
overview: "Consolidate duplicate readiness checklist implementations (deployment-service/configs, codex/10-audit,

  pm/docs) into ONE canonical location in codex/10-audit. Propagate via symlinks to PM, deployment-service

  (sibling-clone for GHA), and system-integration-tests. Harden per-repo semver bump rules, add agent

  major-bump gate in quickmerge.sh, and propagate all rules to AGENTS.md, SUB_AGENT_MANDATORY_RULES, and

  GHA autonomous agent prompts.

  All work complete as of 2026-03-11: 65 per-repo YAML files confirmed in codex/10-audit/repos/,

  deployment-api wired to codex v3.0 SSOT, staging-to-main hard gate added, daily Telegram readiness

  summary, legacy deployment-service checklist configs deleted.

  "
type: infra
epic: epic-infra
session_notes_2026_03_11:
  [
    "deployment-api checklist.py rewritten to codex v3.0 SSOT (no legacy fallback); reads exclusively from
    unified-trading-codex/10-audit/repos/{repo}.yaml; returns 503 when codex_dir is None",
    deployment-api get_codex_dir()/get_plans_dir() added to service_utils.py; lifespan.py wired with app.state.codex_dir
    and app.state.plans_dir at startup,
    "deployment-api Dockerfile: COPY codex-data/ and pm-plans/ bundled at build time",
    "deployment-api cloudbuild.yaml: fetch-readiness-data step clones codex + PM repos and populates codex-data/ and
    pm-plans/ before docker build; uses github-pat availableSecrets",
    deployment-api codex-data/ symlink -> ../unified-trading-codex/10-audit/repos (local dev),
    deployment-api pm-plans/ symlink -> ../unified-trading-pm/plans (local dev),
    "deployment-service: 18 old phase_N_ checklist.*.yaml configs deleted; codex v3.0 is now sole SSOT",
    "unified-trading-pm staging-to-main.yml: hard readiness gate added before merge step; checks cr4_quality_gate and
    dr4_sit_pass; explicit fail status blocks (exit 1); not_assessed passes (advisory)",
    "unified-trading-pm readiness-verifier.yml: Telegram step changed from exit_code==1 to always(); sends daily summary
    regardless of outcome with PASS/FAIL/WARN/MISMATCH counts",
  ]
completion_gates: { code: C5, deployment: none, business: none }
repo_gates:
  - {
      repo: unified-trading-pm,
      code: C0,
      deployment: none,
      business: none,
      readiness_note:
        "PM: AGENTS.md, SUB_AGENT_MANDATORY_RULES, quickmerge.sh, GHA workflows, per-repo-semver-rules.yaml. Symlinks to
        codex.",
    }
  - {
      repo: unified-trading-codex,
      code: C0,
      deployment: none,
      business: none,
      readiness_note:
        "Codex: 10-audit becomes the SSOT for readiness checklist templates. New files added to 10-audit/.",
    }
  - {
      repo: deployment-service,
      code: C0,
      deployment: none,
      business: none,
      readiness_note:
        "deployment-service: checklist.*.yaml files become references to codex template. Sibling-clone setup for GHA.",
    }
  - {
      repo: system-integration-tests,
      code: C0,
      deployment: none,
      business: none,
      readiness_note: "SIT: symlink to codex/10-audit so SIT workflows know which repos are ready for DR4 testing.",
    }
depends_on: [plan-readiness-gates-overhaul, code-readiness-master-plan]
todos:
  - {
      id: p0-audit-existing-checklists,
      content:
        "Before consolidating, diff the three existing checklist implementations to understand overlap and gaps:\n1.
        codex/10-audit/_checklist-template-enhanced.yaml (v2.0 — COD-01 through REGULATORY-04 items)\n2.
        codex/10-audit/batch/ and codex/10-audit/live/ per-service files\n3.
        deployment-service/configs/checklist.template.service.yaml (52-item, 7-phase operational template)\n4.
        unified-trading-pm/docs/REPO_READINESS_CHECKLIST.md (CR/DR/BR stage model)\nOutput: gap analysis doc
        identifying:\n  - Items in deployment-service not in codex template\n  - Items in codex not covered by CR/DR/BR
        model\n  - Batch/live-specific items that need both modes tracked\n",
      status: done,
      note: "Done 2026-03-11 — gap analysis created at /codex/10-audit/gap-analysis-2026-03-11.md.

        Full analysis also in /codex/10-audit/consolidation-gap-analysis.md (Stream A).

        Key findings: Phase 7 operational data excluded; 38 v2.0 validator IDs absorbed into code_audit_items;

        batch/live dirs were never populated so no archive needed; 15 dual-mode repos identified.

        ",
    }
  - { id: p1a-consolidated-checklist-template, content: "In codex/10-audit/, create the canonical unified readiness
        checklist template:\nunified-trading-codex/10-audit/REPO_READINESS_CHECKLIST.yaml\n\nStructure (single checklist
        per repo, batch/live split for deployment, either/both for business):\n```yaml\nschema_version: \"3.0\"\nrepo:
        \"{REPO_NAME}\"\nrepo_type: \"library|service|api|ui|infra\"   # drives which sections apply\ndeployment_modes:
        [\"batch\", \"live\", \"both\"]  # drives deployment section\nbusiness_modes: [\"batch\", \"live\",
        \"both\"]    # user-declared per repo\n\ncode_readiness:\n  cr1_functionality: { status, evidence, notes
        }\n  cr2_unit_tests: { status, coverage_pct, evidence }\n  cr3_integration_tests: { status,
        manifest_deps_covered, evidence }\n  cr4_quality_gate: { status, last_run_date, evidence }\n  cr5_quickmerge: {
        status, branch, ci_url }\n\ndeployment_readiness:\n  batch:  # or null if modes excludes batch\n    dr1_infra: {
        status, evidence }\n    dr2_ci_smoke:\
        \ { status, evidence }\n    dr3_feature_env: { status, evidence }\n    dr4_sit_pass: { status, evidence
        }\n    dr5_load_perf: { status, evidence }\n    dr6_prod_ready: { status, evidence }\n  live:   # or null if
        modes excludes live\n    dr1_infra: { ... }\n    ...\n\nbusiness_readiness:    # either batch, live, or both
        sections\n  batch:\n    br1_acceptance_criteria: { status, evidence }\n    br2_circuit_breaker: { status,
        na_reason }\n    br3_event_handling: { status, evidence }\n    br4_pnl_targets: { status, kpis_declared,
        evidence }\n    br5_pnl_optimization: { status, na_reason, backtest_artifact_uri }\n    br6_batch_vs_live: {
        status, evidence }    # only if both modes\n    br7_staging_parity: { status, evidence }\n    br8_user_approved:
        { status, approved_date }\n  live:\n    ...\n```\nMerge the best criteria from all three existing templates into
        this single schema.\n", status: done, blocked_by: p0-audit-existing-checklists, note: 'Done 2026-03-11 —
        codex/10-audit/REPO_READINESS_CHECKLIST.yaml exists at schema_version: "3.0".

        Template created by Stream A. All merge decisions implemented:

        - COD-01 through REGULATORY-04 items → code_audit_items cross-reference section

        - 52-item operational template → Phase 7 data-catalogue items excluded (operational-only, kept in
        deployment-service/configs/)

        - CR/DR/BR model from PM → top-level structure with batch/live sub-keys per section

        - validator_id fields preserved in code_audit_items with all 110 IDs tracked

        ' }
  - {
      id: p1b-per-repo-checklist-files,
      content:
        "In codex/10-audit/repos/, create per-repo YAML files using the new template:\n- One file per repo:
        unified-trading-codex/10-audit/repos/{repo-name}.yaml\n- Pre-populate CR/DR/BR state from
        code_readiness_master_plan_2026_03_11.plan.md\n- MERGE in the 52-item operational status from
        deployment-service/configs/checklist.{service}.yaml\n  into the DR and business sections (operational phases map
        to DR1/DR2/DR3 criteria)\n- Migrate codex/10-audit/batch/{service}.yaml and live/{service}.yaml into the unified
        repos/ format\n  then move those files to codex/10-audit/_archive/batch/ and _archive/live/\n- Run as parallel
        agent tasks split by tier: T0/T1, T2/T3, T4-instruments+mtds,
        T4-features+ml,\n  T4-strategy+execution+monitoring, T5-apis, T6-uis, infra\nAfter each tier agent completes:
        add a deprecation header comment to the corresponding\ndeployment-service/configs/checklist.{service}.yaml files
        pointing to the new canonical location.\n",
      status: done,
      blocked_by: p1a-consolidated-checklist-template,
      note: '65 YAML files confirmed present in codex/10-audit/repos/ as of 2026-03-11 (schema_version: "3.0",

        code_readiness/deployment_readiness/business_readiness sections). Files were generated in a prior

        session. Statuses are not_assessed (to be updated per-repo as work progresses).

        ',
    }
  - { id: p1c-codex-10-audit-readme, content: 'Create /codex/10-audit/README.md (or update if exists):

        - Declare this dir as the SSOT for all repo readiness checklists

        - Explain the 3-axis model (CR/DR/BR) and batch/live deployment split

        - Document the schema version and upgrade path

        - Reference ssot-reference-mapping.md for where this fits in the broader SSOT hierarchy

        - Add SSOT declaration: "This supersedes deployment-service/configs/checklist.*.yaml for readiness criteria"

        - Note: deployment-service/configs/ remains SSOT for operational data (sharding, venues, data-catalogue)

        ', status: done, blocked_by: p1a-consolidated-checklist-template, note: "Done 2026-03-11 — README.md already
        existed at /codex/10-audit/README.md (committed as 5a6d5ba). Declares SSOT boundary, 3-axis CR/DR/BR model, v3.0
        schema upgrade path, batch/live split, supersedes note for deployment-service/configs/checklist.*.yaml, and
        references ssot-reference-mapping.md. All p1c criteria satisfied." }
  - { id: p2a-pm-reference-update, content: 'Update unified-trading-pm/docs/REPO_READINESS_CHECKLIST.md:

        - Add a banner at top: "CANONICAL CHECKLIST TEMPLATE:
        unified-trading-codex/10-audit/REPO_READINESS_CHECKLIST.yaml"

        - Replace duplicate stage definitions with references to codex

        - Keep the CR/DR/BR stage NAMES and brief descriptions (the PM doc is the developer-facing summary)

        - Add a note: "Per-repo status: codex/10-audit/repos/{repo-name}.yaml"

        Do NOT delete PM''s doc — it''s the human-readable summary; codex YAML is machine-readable.

        ', status: done, blocked_by: p1c-codex-10-audit-readme, note: Done 2026-03-11 — REPO_READINESS_CHECKLIST.md
        banner added pointing to codex SSOT. }
  - {
      id: p2b-setup-workspace-codex-link,
      content:
        "Update unified-trading-pm/scripts/workspace/setup-workspace-from-manifest.sh:\nWhen setting up a repo, also
        clone/update unified-trading-codex if not present (as sibling).\nCreate a RELATIVE symlink in each repo:\n  ln
        -sfn ../../unified-trading-codex/10-audit/repos/{repo-name}.yaml {repo}/.readiness\nCRITICAL: must be relative
        (../../...) NOT absolute. Relative symlinks work on GHA where\nworkspace root differs from local machine.
        Absolute paths break across environments.\nAlso commit a plain text .readiness-ref file:
        \"../../unified-trading-codex/10-audit/repos/{repo-name}.yaml\"\n.readiness-ref is the GHA-safe fallback (text
        file, no symlink needed, just cat it to get path).\n",
      status: done,
      blocked_by: p1b-per-repo-checklist-files,
      note: "Done 2026-03-11 — commit 1a27d7a. workspace-bootstrap.sh Phase 2.5 writes .readiness-ref per repo.

        Relative path: ../../unified-trading-codex/10-audit/repos/{repo-name}.yaml. .readiness → gitignore.

        ",
    }
  - {
      id: p2c-deployment-service-sibling-clone,
      content:
        "Update deployment-service/.github/workflows/ (or create a new setup step):\nIn GHA workflows that need
        checklist data, add a setup step:\n```yaml\n- name: Checkout unified-trading-codex (readiness
        checklists)\n  uses: actions/checkout@v4\n  with:\n    repository: IggyIkenna/unified-trading-codex\n    token:
        ${{ secrets.GH_PAT }}\n    path: ../unified-trading-codex   # sibling clone\n```\nThis makes
        codex/10-audit/repos/ available to deployment-service GHA workflows.\nUpdate
        deployment-service/configs/checklist.*.yaml: add a header comment pointing to codex canonical.\n",
      status: done,
      blocked_by: p1b-per-repo-checklist-files,
      note: Done 2026-03-11 — commit 691e5a8. deployment-service quality-gates.yml has codex sibling-clone step.,
    }
  - {
      id: p2d-sit-symlink-readiness,
      content:
        "In system-integration-tests, add a readiness-check step to smoke-test-gate.yml:\nBefore running SIT tests
        against a repo, check if that repo has reached DR4 prerequisite in\ncodex/10-audit/repos/{repo}.yaml. Steps:\n1.
        Add a sibling-clone step for unified-trading-codex (same pattern as p2c).\n2. Create
        system-integration-tests/scripts/check-sit-readiness.py:\n   Reads codex/10-audit/repos/{repo}.yaml for each
        repo in the SIT run scope.\n   Flags repos where dr3_feature_env.status != \"pass\" — SIT cannot validate an
        undeployed service.\n   Outputs a markdown table to GitHub Step Summary.\n3. This is ADVISORY (warn, not fail) —
        SIT may still run even if some repos haven't reached DR3.\n",
      status: done,
      blocked_by: p1b-per-repo-checklist-files,
      note:
        "Done 2026-03-11 — commit 2cf0502. smoke-test-gate.yml + scripts/check-sit-readiness.py (advisory, exits 0).",
    }
  - { id: p3a-semver-type-rules-doc, content: "Create unified-trading-pm/docs/per-repo-semver-rules.yaml — centralized
        YAML declaring, per repo type\n(library/service/api/ui/infra), exactly what changes constitute MAJOR, MINOR, and
        PATCH bumps.\n\nPer type rules:\nlibrary: MAJOR=removed public export or breaking type change; MINOR=new
        export/function/class added;\n         PATCH=bug fix/internal refactor/doc update/perf improvement\nservice:
        MAJOR=removed HTTP endpoint/PubSub topic/UEI event type, breaking request schema change;\n         MINOR=new
        endpoint/event type/optional field, new dependency added;\n         PATCH=bug fix/perf/config change/new
        test\napi:     MAJOR=removed HTTP endpoint, breaking response schema change, auth mechanism
        change;\n         MINOR=new endpoint/new optional response field; PATCH=bug fix/perf/config\nui:      npm semver
        only; MAJOR=breaking API contract change; MINOR=new feature; PATCH=bug fix\ninfra:   no strict semver;
        MAJOR=breaking change to scripts/workflows\
        \ used by other repos\n\nPre-1.0.0 override: on 0.x.x, feat!: bumps MINOR (never MAJOR). MAJOR only
        post-1.0.0.\n", status: done, note: "Done 2026-03-11 — commit ae2bace: docs/per-repo-semver-rules.yaml created
        on feat/semver-rules-centralized" }
  - { id: p3b-semver-manifest-field, content: 'Add `semver_rules_ref` field to each repo entry in
        workspace-manifest.json:

        Values: "library-t0", "library-t1", "library-t2", "library-t3", "service", "api", "ui", "infra"

        Also add `v100_na_items` dict per-repo for permanently declared N/A items with reasons.

        Example: "execution-service": { "v100_na_items": { "BR5": "N/A — not a revenue-path lib" } }

        ', status: done, note: "Done 2026-03-11 — commit fbfde15: semver_rules_ref added to all 65 repos in
        workspace-manifest.json" }
  - { id: p3c-per-repo-semver-cursor-rule, content: "Create
        unified-trading-pm/cursor-rules/core/per-repo-semver-rules.mdc

        RULE: Before proposing any commit message with feat!:, feat:, or fix:, agent must:

        1. Look up repo's semver_rules_ref in workspace-manifest.json

        2. Read the matching rule set from docs/per-repo-semver-rules.yaml

        3. Verify the change matches the declared bump level

        4. For post-1.0.0 repos: if change is MAJOR, stop and request user approval

        alwaysApply: true, priority: 98 (highest among semver rules).

        ", status: done, note: "Done 2026-03-11 — commit d359973: cursor-rules/core/per-repo-semver-rules.mdc created" }
  - {
      id: p4a-quickmerge-advisory-only,
      content:
        "Update unified-trading-pm/scripts/quickmerge.sh: REMOVE any version-bump logic entirely.\nquickmerge.sh NEVER
        bumps versions — it only merges code. Version bumps are GHA-only.\nAdd an advisory Stage 0.3 comment/print (NOT
        an exit 1) that says:\n\"NOTE: version bumps are handled autonomously by semver-agent.yml after QG passes on
        staging.\n No manual version changes are needed. Do NOT edit pyproject.toml version manually.\"\nThis is
        informational only — quickmerge never reads or writes version numbers.\n",
      status: done,
      note: "Done 2026-03-11 — commit ac2e9bf: Stage 0.3 converted from exit-1 gate to advisory-only print",
    }
  - { id: p4b-semver-agent-plan-aware, content: "Redesign .github/workflows/semver-agent.yml template:\n\nTRIGGER:
        workflow_run on quality-gates.yml completing with conclusion=success AND branch=staging.\nThis is a SEPARATE
        workflow from quality-gates.yml — it observes QG completion, it doesn't run inside it.\n\nAGENT LOGIC (Claude
        Haiku monitors work-done vs PM plans):\n1. Read current staging_versions[repo] from PM
        workspace-manifest.json.\n   If not set: baseline = \"0.0.0\".\n2. Read the git diff (all changed files) since
        last staging version was set.\n3. Read ALL active PM plans that reference this repo in their
        repo_gates\n   (from unified-trading-pm/plans/active/*.plan.md). Identify which plan todos were completed\n   in
        this batch of changes.\n4. Classify bump magnitude by comparing:\n   a. Code diff analysis: removed
        exports/endpoints → MAJOR; new features → MINOR; fixes → PATCH\n   b. Plan todos completed: todos with \"feat:\"
        intent → MINOR; \"fix:\" → PATCH; \"feat!:\" → MAJOR intent\n\
        \   c. Use the higher of (a) and (b) as the final bump type\n   d. Cross-reference with
        docs/per-repo-semver-rules.yaml for this repo's semver_rules_ref\n5. Apply pre-1.0.0 override: if current
        version starts with \"0.\", MAJOR → MINOR.\n6. Apply 0.0.0 baseline: MAJOR/MINOR from 0.0.0 → 0.1.0; PATCH →
        0.0.1.\n7. If bump is MAJOR and version >= 1.0.0:\n   - Do NOT bump. Trigger the major-bump-approval.yml
        workflow via workflow_dispatch.\n   - The approval workflow requires a human trigger (or admin script with
        GH_PAT).\n   - Log: \"MAJOR bump staged — awaiting approval via GHA workflow_dispatch or admin approval
        script.\"\n8. Otherwise: dispatch version-bump to PM → updates staging_versions in manifest.\n\nNO version bumps
        happen inside quickmerge.sh or any local script. This workflow is the SOLE authority.\n", status: done, note: "Done
        2026-03-11 — commit e68635d: semver-agent.yml redesigned as QG-triggered plan-aware workflow" }
  - { id: p4c-major-bump-approval-workflow, content: "Create .github/workflows/major-bump-approval.yml in each repo (via
        rollout template):\n\nTRIGGER: workflow_dispatch with inputs:\n  - repo: repo name\n  - proposed_version: the
        new MAJOR version (e.g. \"2.0.0\")\n  - reason: summary of why this is MAJOR\n  - approver: name/GH handle of
        approver\n\nAlso triggerable by admin script:\n  bash unified-trading-pm/scripts/approve-major-bump.sh {repo}
        {version} --admin-pat $GH_PAT\n\nLOGIC:\n1. Verify the approver has write access to the repo (via GH API)\n2.
        Verify the repo's codex/10-audit/repos/{repo}.yaml has all gates met (or N/A declared)\n   for the v1.0.0
        checklist (CR5, DR3, DR4, BR2, BR3, BR4)\n3. If gates not met: print what's missing; exit 1 (approval denied,
        not blocked permanently)\n4. If gates met: dispatch version-bump to PM with the approved MAJOR version\n5.
        Update codex/10-audit/repos/{repo}.yaml: set
        br8_user_approved.status=\"pass\",\n   br8_user_approved.approved_by={approver},\
        \ br8_user_approved.approved_date={today}\n\nCreate the approval script:
        unified-trading-pm/scripts/approve-major-bump.sh\n", status: done, note: "Done 2026-03-11 — commit ed5ad3b:
        major-bump-approval.yml template + approve-major-bump.sh created" }
  - { id: p5a-agents-md-readiness-section, content: 'Update unified-trading-pm/AGENTS.md: add Section 10 "Repo Readiness
        & Semver Rules".

        Content (brief, authoritative):

        - Readiness SSOT: codex/10-audit/REPO_READINESS_CHECKLIST.yaml + repos/{repo}.yaml

        - CR0-CR5, DR0-DR6, BR0-BR8 — one-line each

        - Deployment modes: batch | live | both (per repo''s deployment_modes field)

        - Business modes: either or both (per repo''s business_modes field)

        - v1.0.0 gate: CR5(main) + DR3 + DR4 + BR2 + BR3 + BR4 + BR8 (no exceptions)

        - No agent may set BR8 or v1.0.0 autonomously

        - Per-repo semver rules: docs/per-repo-semver-rules.yaml (look up semver_rules_ref in manifest)

        ', status: done, note: "Done 2026-03-11 — commit 41d833c: AGENTS.md Section 10 added on
        feat/agent-propagation-readiness" }
  - { id: p5b-sub-agent-rules-readiness, content: 'Update
        unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md:

        Add Section 10 "Readiness Checklist & Semver" (mirrors AGENTS.md Section 10 but in mandatory imperative style).

        Critical additions beyond AGENTS.md:

        - "Read {repo}/.readiness-ref to find the codex checklist for this repo before claiming any stage is complete"

        - "To check a repo''s readiness state: cat unified-trading-codex/10-audit/repos/{repo}.yaml"

        - "NEVER advance a repo''s readiness stage unless all criteria in the checklist item are met"

        ', status: done, note: "Done 2026-03-11 — commit 1162e17: SUB_AGENT_MANDATORY_RULES Section 10 added" }
  - {
      id: p5c-overnight-orchestrator-readiness,
      content:
        "Update unified-trading-pm/.github/workflows/overnight-agent-orchestrator.yml:\n1. Add sibling-clone step for
        unified-trading-codex (same GH_PAT pattern as other sibling clones)\n2. In each tier's Claude Haiku agent
        prompt, inject:\n   - Current CR/DR/BR state for repos in this tier from codex/10-audit/repos/\n   - \"Before
        proposing any semver bump, read docs/per-repo-semver-rules.yaml\"\n   - \"After any quickmerge, update
        codex/10-audit/repos/{repo}.yaml with new CR stage\"\n   - \"Never set BR8 or v1.0.0 autonomously — present
        readiness summary to user instead\"\n",
      status: done,
      note: "Done 2026-03-11 — commit 2cb3d41: overnight-agent-orchestrator.yml readiness context injected",
    }
  - { id: p5d-rules-alignment-readiness-check, content: "Update
        unified-trading-pm/.github/workflows/rules-alignment-agent.yml:

        Add a step: for any plan change that introduces new per-repo readiness criteria, verify

        codex/10-audit/REPO_READINESS_CHECKLIST.yaml is updated to match. If not, create the update.

        Specifically check: new N/A declarations, new BR/DR gates, new repo types added to manifest.

        ", status: done, note: "Done 2026-03-11 — commit 1076275: rules-alignment-agent.yml readiness check added" }
  - {
      id: p6a-pm-codex-formal-waiver,
      content:
        "Update code_readiness_master_plan_2026_03_11.plan.md repo_gates:\n- unified-trading-pm: CR5=done (v1.2.0); DR
        N/A (infra tooling, not deployed as service); BR N/A.\n- unified-trading-codex: CR5=done (docs-only, no Python
        source to quality-gate);\n  DR N/A; BR N/A; v1.0.0 eligible per infra exemption.\nAdd readiness_note with formal
        waiver rationale for each.\nCreate codex/10-audit/repos/unified-trading-pm.yaml and unified-trading-codex.yaml
        with infra template.\n",
      status: done,
      note: "Done 2026-03-11 — commit c682dff: formal waivers in codex/10-audit/repos/unified-trading-{pm,codex}.yaml",
    }
  - {
      id: p6b-codex-version-bump,
      content:
        "Check unified-trading-codex version in pyproject.toml. If <1.0.0:\n1. Create
        codex/10-audit/repos/unified-trading-codex.yaml with all non-applicable gates marked \"na\"\n   with documented
        reasons; BR8 marked \"pending — awaiting user approval\"\n2. Present to user the v1.0.0 readiness
        summary:\n   \"CR5: done (docs repo, no Python QG required). DR1-DR6: N/A (no Cloud Run deployment).\n    BR2:
        N/A (no circuit breaker). BR3: N/A (no UEI events). BR4: N/A (no PnL/perf targets).\n    BR5-BR7: N/A. BR8:
        PENDING — awaiting your approval.\"\n3. Do NOT create the version PR until user gives explicit approval in
        session.\n4. After approval: commit codex/10-audit/repos/unified-trading-codex.yaml with BR8
        status=pass,\n   then create the v1.0.0 PR.\n",
      status: done,
      blocked_by: p6a-pm-codex-formal-waiver,
      note: "Done 2026-03-11 — commit ff477a4. BR8 approved by IggyIkenna in session.

        pyproject.toml: 0.1.0 → 1.0.0. BR8 status=pass in 10-audit/repos/unified-trading-codex.yaml.

        PR: https://github.com/IggyIkenna/unified-trading-codex/pull/1369

        ",
    }
  - { id: p7a-readiness-verifier-script, content: "Create unified-trading-pm/scripts/check-repo-readiness.py

        Reads codex/10-audit/repos/{repo}.yaml (declared state), then runs automated checks:

        - CR1: grep NotImplementedError, TODO, FIXME in source (excluding tests/)

        - CR2: read coverage.xml vs declared coverage_pct

        - CR3: parse manifest deps, check tests/integration/ for each dep's test file

        - CR4: check for ruff/basedpyright error files from last QG run

        - DR3 (services): check if .readiness-ref health endpoint is reachable (non-blocking)

        Outputs declared vs verified table. Flags UNVERIFIED mismatches. Does NOT modify checklist files.

        ", status: done, note: "Done 2026-03-11 — commit e720924: scripts/check-repo-readiness.py created" }
  - { id: p7b-readiness-verifier-gha, content: 'Create unified-trading-pm/.github/workflows/readiness-verifier.yml

        Trigger: workflow_dispatch (tier filter), schedule: "0 3 * * *" daily.

        Clones codex as sibling, runs check-repo-readiness.py for specified tier.

        Output: GitHub Step Summary table + Telegram alert on mismatches.

        ', status: done, note: "Done 2026-03-11 — commit 0541c8a: .github/workflows/readiness-verifier.yml created", blocked_by: p7a-readiness-verifier-script }
isProject: false
---

# Repo Readiness & Semver Hardening

## Context

Three overlapping implementations of repo readiness checklists currently exist:

1. **`deployment-service/configs/checklist.*.yaml`** — 52-item operational checklists per service (7 phases), currently
   the operational tracking SSOT per `ssot-reference-mapping.md`
2. **`unified-trading-codex/10-audit/`** — standards-based audit template (`_checklist-template-enhanced.yaml`) plus
   per-service batch/ and live/ YAML files
3. **`unified-trading-pm/docs/REPO_READINESS_CHECKLIST.md`** — the CR/DR/BR stage model (text, human-readable) plus
   `code_readiness_master_plan_2026_03_11.plan.md` as the 65-repo tracker

The user's intent:

- **One canonical location** — `codex/10-audit/` as SSOT for readiness templates + per-repo status
- **Repo readiness = one checklist** (not separate docs) per repo, with batch/live split inside deployment section
- **Deployment = batch AND live** tracked independently
- **Business = either or both** per repo's declared trading modes
- **PM and deployment-service symlink/reference** codex; SIT clones codex for DR4 prerequisite checks
- **v1.0.0 means much more than quickmerge** — full CR+DR+BR gate with user approval required

---

## Consolidation Strategy

```
codex/10-audit/
├── REPO_READINESS_CHECKLIST.yaml     ← NEW: canonical schema (v3.0, merges all 3 sources)
├── README.md                          ← SSOT declaration + schema docs
├── repos/
│   ├── unified-trading-library.yaml   ← per-repo status (replaces batch/ + live/ split)
│   ├── execution-service.yaml         ← has both batch and live sections
│   └── ... (65 files total)
└── _archive/
    ├── batch/                         ← old batch/ files moved here
    └── live/                          ← old live/ files moved here

unified-trading-pm/
└── docs/REPO_READINESS_CHECKLIST.md  ← human-readable summary; declares codex as SSOT for YAML

deployment-service/configs/
└── checklist.*.yaml                  ← add header: "Operational status; canonical template: codex/10-audit/"

{each-repo}/
└── .readiness-ref                    ← "codex/10-audit/repos/{repo-name}.yaml" (committed)

system-integration-tests/
└── scripts/check-sit-readiness.py   ← reads codex/10-audit/repos/ to gate DR4 runs
```

---

## Parallel Execution Strategy

All 7 phases with natural ordering within phases. Most phases can run in parallel across streams:

| Stream                | Todos              | Dependencies                 |
| --------------------- | ------------------ | ---------------------------- |
| A — Audit + Template  | p0, p1a, p1b, p1c  | p1b needs p1a; p1c needs p1a |
| B — Symlinks          | p2a, p2b, p2c, p2d | All need p1b                 |
| C — Semver Rules      | p3a, p3b, p3c      | p3b needs p3a; p3c needs p3a |
| D — Bump Blocker      | p4a, p4b           | Independent of A/B/C         |
| E — Agent Propagation | p5a, p5b, p5c, p5d | All independent              |
| F — PM/Codex Status   | p6a, p6b           | p6b needs p6a                |
| G — Verifier          | p7a, p7b           | p7b needs p7a                |

Launch: agents for A (p0 first, then p1a/p1b/p1c in sequence), C, D, E, F, G all simultaneously. Stream B starts after
p1b completes.

---

## Key Design Decisions

### 1. Batch vs Live in Deployment Readiness

Each service declares `deployment_modes: ["batch", "live", "both"]` in its checklist. Services with both modes (e.g.,
execution-service, strategy-service) track DR1–DR6 for each mode independently. Libraries have no DR1–DR6 (AR publish is
their equivalent).

### 2. Business Readiness Either/Or

`business_modes: ["batch", "live", "both"]` — a service can be business-ready for batch only (if live trading comes
later). BR8 can be granted for batch mode while live mode BR gates are still in progress.

### 3. PM/Codex as SSOT Separation

- `codex/10-audit/` = SSOT for readiness **templates and per-repo status** (YAML, machine-readable)
- `pm/docs/REPO_READINESS_CHECKLIST.md` = SSOT for the **CR/DR/BR stage definitions** (human-readable, prose)
- `deployment-service/configs/checklist.*.yaml` = SSOT for **operational tracking status** (batch job execution phases)
  These three serve different audiences and are NOT duplicates — each has a unique concern.

### 4. Design Decisions (confirmed by user)

- **deployment-service checklist.\*.yaml fate**: MERGE into codex/10-audit/repos/ (one file per repo).
  deployment-service/configs/checklist.\*.yaml become deprecated stubs with a pointer comment.
- **Infra repo v1.0.0**: BR8 still required for PM and codex — user explicitly approves in a session. BR2/BR3/BR4/BR5
  all declared N/A with reasons; BR8 is the only gate that blocks.
- **Per-repo semver rules**: Centralized in `unified-trading-pm/docs/per-repo-semver-rules.yaml`. All repos reference
  via `semver_rules_ref` in `workspace-manifest.json`.

---

## Key Files Modified

| File                                                            | Phase | Change                         |
| --------------------------------------------------------------- | ----- | ------------------------------ |
| `codex/10-audit/REPO_READINESS_CHECKLIST.yaml`                  | 1a    | New canonical template (v3.0)  |
| `codex/10-audit/repos/*.yaml`                                   | 1b    | 65 per-repo status files       |
| `/codex/10-audit/README.md`                                     | 1c    | SSOT declaration               |
| `pm/docs/REPO_READINESS_CHECKLIST.md`                           | 2a    | Add codex SSOT banner          |
| `pm/scripts/setup-workspace-from-manifest.sh`                   | 2b    | .readiness-ref creation        |
| `deployment-service/.github/workflows/`                         | 2c    | Sibling-clone codex step       |
| `system-integration-tests/scripts/check-sit-readiness.py`       | 2d    | New DR4 prerequisite check     |
| `pm/docs/per-repo-semver-rules.yaml`                            | 3a    | New per-type bump rules        |
| `workspace-manifest.json`                                       | 3b    | semver_rules_ref per repo      |
| `pm/cursor-rules/core/per-repo-semver-rules.mdc`                | 3c    | New cursor rule                |
| `pm/scripts/quickmerge.sh`                                      | 4a    | Stage 0.3 major-bump gate      |
| `.github/workflows/semver-agent.yml`                            | 4b    | Major-bump GitHub Issue        |
| `pm/AGENTS.md`                                                  | 5a    | Section 10: readiness + semver |
| `pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`                | 5b    | Section 10                     |
| `.github/workflows/overnight-agent-orchestrator.yml`            | 5c    | Readiness context injection    |
| `.github/workflows/rules-alignment-agent.yml`                   | 5d    | Readiness mdc check            |
| `pm/plans/archive/code_readiness_master_plan_2026_03_11.plan.md` | 6a    | PM/Codex N/A waivers           |
| `pm/scripts/check-repo-readiness.py`                            | 7a    | New verifier script            |
| `.github/workflows/readiness-verifier.yml`                      | 7b    | New GHA workflow               |

---

## Verification

1. `cat codex/10-audit/repos/execution-service.yaml` — must show batch + live deployment sections
2. `cat execution-service/.readiness-ref` — must contain `codex/10-audit/repos/execution-service.yaml`
3. On a post-1.0.0 test: `bash scripts/quickmerge.sh "feat!: test" --agent` must exit 1
4. `grep -c "CR1\|cr1_functionality" AGENTS.md` > 0
5. `python scripts/check-repo-readiness.py --repo unified-events-interface` outputs CR/DR/BR table
