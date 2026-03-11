---
name: repo-readiness-semver-hardening-2026-03-11
overview: |
  Consolidate duplicate readiness checklist implementations (deployment-service/configs, codex/10-audit,
  pm/docs) into ONE canonical location in codex/10-audit. Propagate via symlinks to PM, deployment-service
  (sibling-clone for GHA), and system-integration-tests. Harden per-repo semver bump rules, add agent
  major-bump gate in quickmerge.sh, and propagate all rules to AGENTS.md, SUB_AGENT_MANDATORY_RULES, and
  GHA autonomous agent prompts.
type: infra
epic: epic-infra
status: active

completion_gates:
  code: C5
  deployment: none
  business: none

repo_gates:
  - repo: unified-trading-pm
    code: C0
    deployment: none
    business: none
    readiness_note:
      "PM: AGENTS.md, SUB_AGENT_MANDATORY_RULES, quickmerge.sh, GHA workflows, per-repo-semver-rules.yaml. Symlinks to
      codex."
  - repo: unified-trading-codex
    code: C0
    deployment: none
    business: none
    readiness_note: "Codex: 10-audit becomes the SSOT for readiness checklist templates. New files added to 10-audit/."
  - repo: deployment-service
    code: C0
    deployment: none
    business: none
    readiness_note:
      "deployment-service: checklist.*.yaml files become references to codex template. Sibling-clone setup for GHA."
  - repo: system-integration-tests
    code: C0
    deployment: none
    business: none
    readiness_note: "SIT: symlink to codex/10-audit so SIT workflows know which repos are ready for DR4 testing."

depends_on:
  - plan-readiness-gates-overhaul
  - code-readiness-master-plan

todos:
  # ─── PHASE 0: AUDIT EXISTING CHECKLIST CONTENT (prerequisite for all phases) ───

  - id: p0-audit-existing-checklists
    content: |
      Before consolidating, diff the three existing checklist implementations to understand overlap and gaps:
      1. codex/10-audit/_checklist-template-enhanced.yaml (v2.0 — COD-01 through REGULATORY-04 items)
      2. codex/10-audit/batch/ and codex/10-audit/live/ per-service files
      3. deployment-service/configs/checklist.template.service.yaml (52-item, 7-phase operational template)
      4. unified-trading-pm/docs/REPO_READINESS_CHECKLIST.md (CR/DR/BR stage model)
      Output: gap analysis doc identifying:
        - Items in deployment-service not in codex template
        - Items in codex not covered by CR/DR/BR model
        - Batch/live-specific items that need both modes tracked
    status: in_progress
    note: |
      Stream A running — gap analysis + template + 65 per-repo files being created in codex/10-audit/.

  # ─── PHASE 1: CODEX 10-AUDIT AS SSOT ───

  - id: p1a-consolidated-checklist-template
    content: |
      In codex/10-audit/, create the canonical unified readiness checklist template:
      unified-trading-codex/10-audit/REPO_READINESS_CHECKLIST.yaml

      Structure (single checklist per repo, batch/live split for deployment, either/both for business):
      ```yaml
      schema_version: "3.0"
      repo: "{REPO_NAME}"
      repo_type: "library|service|api|ui|infra"   # drives which sections apply
      deployment_modes: ["batch", "live", "both"]  # drives deployment section
      business_modes: ["batch", "live", "both"]    # user-declared per repo

      code_readiness:
        cr1_functionality: { status, evidence, notes }
        cr2_unit_tests: { status, coverage_pct, evidence }
        cr3_integration_tests: { status, manifest_deps_covered, evidence }
        cr4_quality_gate: { status, last_run_date, evidence }
        cr5_quickmerge: { status, branch, ci_url }

      deployment_readiness:
        batch:  # or null if modes excludes batch
          dr1_infra: { status, evidence }
          dr2_ci_smoke: { status, evidence }
          dr3_feature_env: { status, evidence }
          dr4_sit_pass: { status, evidence }
          dr5_load_perf: { status, evidence }
          dr6_prod_ready: { status, evidence }
        live:   # or null if modes excludes live
          dr1_infra: { ... }
          ...

      business_readiness:    # either batch, live, or both sections
        batch:
          br1_acceptance_criteria: { status, evidence }
          br2_circuit_breaker: { status, na_reason }
          br3_event_handling: { status, evidence }
          br4_pnl_targets: { status, kpis_declared, evidence }
          br5_pnl_optimization: { status, na_reason, backtest_artifact_uri }
          br6_batch_vs_live: { status, evidence }    # only if both modes
          br7_staging_parity: { status, evidence }
          br8_user_approved: { status, approved_date }
        live:
          ...
      ```
      Merge the best criteria from all three existing templates into this single schema.
    status: todo
    blocked_by: p0-audit-existing-checklists
    note: |
      Key merge decisions:
      - COD-01 through REGULATORY-04 items from _checklist-template-enhanced.yaml → fold into CR1/CR4
      - 52-item operational template from deployment-service → fold batch/live DR sections
      - CR/DR/BR model from PM → becomes the top-level structure
      - validator_id and automation_status fields from enhanced template → preserve in CR/DR items

  - id: p1b-per-repo-checklist-files
    content: |
      In codex/10-audit/repos/, create per-repo YAML files using the new template:
      - One file per repo: unified-trading-codex/10-audit/repos/{repo-name}.yaml
      - Pre-populate CR/DR/BR state from code_readiness_master_plan_2026_03_11.plan.md
      - MERGE in the 52-item operational status from deployment-service/configs/checklist.{service}.yaml
        into the DR and business sections (operational phases map to DR1/DR2/DR3 criteria)
      - Migrate codex/10-audit/batch/{service}.yaml and live/{service}.yaml into the unified repos/ format
        then move those files to codex/10-audit/_archive/batch/ and _archive/live/
      - Run as parallel agent tasks split by tier: T0/T1, T2/T3, T4-instruments+mtds, T4-features+ml,
        T4-strategy+execution+monitoring, T5-apis, T6-uis, infra
      After each tier agent completes: add a deprecation header comment to the corresponding
      deployment-service/configs/checklist.{service}.yaml files pointing to the new canonical location.
    status: todo
    blocked_by: p1a-consolidated-checklist-template
    note: |
      Output: 65 YAML files in codex/10-audit/repos/ (one per repo in workspace-manifest.json).
      PM/codex: infra template, BR2-BR7 all N/A with reasons; BR8 still required for v1.0.0.
      Libraries: deployment_modes field set appropriately; DR3 = AR wheel published (not Cloud Run).

  - id: p1c-codex-10-audit-readme
    content: |
      Create codex/10-audit/README.md (or update if exists):
      - Declare this dir as the SSOT for all repo readiness checklists
      - Explain the 3-axis model (CR/DR/BR) and batch/live deployment split
      - Document the schema version and upgrade path
      - Reference ssot-reference-mapping.md for where this fits in the broader SSOT hierarchy
      - Add SSOT declaration: "This supersedes deployment-service/configs/checklist.*.yaml for readiness criteria"
      - Note: deployment-service/configs/ remains SSOT for operational data (sharding, venues, data-catalogue)
    status: todo
    blocked_by: p1a-consolidated-checklist-template

  # ─── PHASE 2: SYMLINK AND DISTRIBUTION STRATEGY ───

  - id: p2a-pm-reference-update
    content: |
      Update unified-trading-pm/docs/REPO_READINESS_CHECKLIST.md:
      - Add a banner at top: "CANONICAL CHECKLIST TEMPLATE: unified-trading-codex/10-audit/REPO_READINESS_CHECKLIST.yaml"
      - Replace duplicate stage definitions with references to codex
      - Keep the CR/DR/BR stage NAMES and brief descriptions (the PM doc is the developer-facing summary)
      - Add a note: "Per-repo status: codex/10-audit/repos/{repo-name}.yaml"
      Do NOT delete PM's doc — it's the human-readable summary; codex YAML is machine-readable.
    status: todo
    blocked_by: p1c-codex-10-audit-readme

  - id: p2b-setup-workspace-codex-link
    content: |
      Update unified-trading-pm/scripts/workspace/setup-workspace-from-manifest.sh:
      When setting up a repo, also clone/update unified-trading-codex if not present (as sibling).
      Create a RELATIVE symlink in each repo:
        ln -sfn ../../unified-trading-codex/10-audit/repos/{repo-name}.yaml {repo}/.readiness
      CRITICAL: must be relative (../../...) NOT absolute. Relative symlinks work on GHA where
      workspace root differs from local machine. Absolute paths break across environments.
      Also commit a plain text .readiness-ref file: "../../unified-trading-codex/10-audit/repos/{repo-name}.yaml"
      .readiness-ref is the GHA-safe fallback (text file, no symlink needed, just cat it to get path).
    status: todo
    blocked_by: p1b-per-repo-checklist-files
    note: |
      Symlink: ln -sfn ../../unified-trading-codex/10-audit/repos/{repo}.yaml .readiness  (relative)
      NOT: ln -s /Users/ikennaigboaka/Code/.../unified-trading-codex/10-audit/repos/{repo}.yaml (absolute — WRONG)
      .readiness → gitignore (created fresh by setup-workspace; path varies per machine/GHA runner)
      .readiness-ref → committed (stable relative path string; GHA reads this to resolve checklist)

  - id: p2c-deployment-service-sibling-clone
    content: |
      Update deployment-service/.github/workflows/ (or create a new setup step):
      In GHA workflows that need checklist data, add a setup step:
      ```yaml
      - name: Checkout unified-trading-codex (readiness checklists)
        uses: actions/checkout@v4
        with:
          repository: IggyIkenna/unified-trading-codex
          token: ${{ secrets.GH_PAT }}
          path: ../unified-trading-codex   # sibling clone
      ```
      This makes codex/10-audit/repos/ available to deployment-service GHA workflows.
      Update deployment-service/configs/checklist.*.yaml: add a header comment pointing to codex canonical.
    status: todo
    blocked_by: p1b-per-repo-checklist-files

  - id: p2d-sit-symlink-readiness
    content: |
      In system-integration-tests, add a readiness-check step to smoke-test-gate.yml:
      Before running SIT tests against a repo, check if that repo has reached DR4 prerequisite in
      codex/10-audit/repos/{repo}.yaml. Steps:
      1. Add a sibling-clone step for unified-trading-codex (same pattern as p2c).
      2. Create system-integration-tests/scripts/check-sit-readiness.py:
         Reads codex/10-audit/repos/{repo}.yaml for each repo in the SIT run scope.
         Flags repos where dr3_feature_env.status != "pass" — SIT cannot validate an undeployed service.
         Outputs a markdown table to GitHub Step Summary.
      3. This is ADVISORY (warn, not fail) — SIT may still run even if some repos haven't reached DR3.
    status: todo
    blocked_by: p1b-per-repo-checklist-files

  # ─── PHASE 3: PER-REPO SEMVER RULES ───

  - id: p3a-semver-type-rules-doc
    content: |
      Create unified-trading-pm/docs/per-repo-semver-rules.yaml — centralized YAML declaring, per repo type
      (library/service/api/ui/infra), exactly what changes constitute MAJOR, MINOR, and PATCH bumps.

      Per type rules:
      library: MAJOR=removed public export or breaking type change; MINOR=new export/function/class added;
               PATCH=bug fix/internal refactor/doc update/perf improvement
      service: MAJOR=removed HTTP endpoint/PubSub topic/UEI event type, breaking request schema change;
               MINOR=new endpoint/event type/optional field, new dependency added;
               PATCH=bug fix/perf/config change/new test
      api:     MAJOR=removed HTTP endpoint, breaking response schema change, auth mechanism change;
               MINOR=new endpoint/new optional response field; PATCH=bug fix/perf/config
      ui:      npm semver only; MAJOR=breaking API contract change; MINOR=new feature; PATCH=bug fix
      infra:   no strict semver; MAJOR=breaking change to scripts/workflows used by other repos

      Pre-1.0.0 override: on 0.x.x, feat!: bumps MINOR (never MAJOR). MAJOR only post-1.0.0.
    status: done
    note: "Done 2026-03-11 — commit ae2bace: docs/per-repo-semver-rules.yaml created on feat/semver-rules-centralized"

  - id: p3b-semver-manifest-field
    content: |
      Add `semver_rules_ref` field to each repo entry in workspace-manifest.json:
      Values: "library-t0", "library-t1", "library-t2", "library-t3", "service", "api", "ui", "infra"
      Also add `v100_na_items` dict per-repo for permanently declared N/A items with reasons.
      Example: "execution-service": { "v100_na_items": { "BR5": "N/A — not a revenue-path lib" } }
    status: done
    note: "Done 2026-03-11 — commit fbfde15: semver_rules_ref added to all 65 repos in workspace-manifest.json"

  - id: p3c-per-repo-semver-cursor-rule
    content: |
      Create unified-trading-pm/cursor-rules/core/per-repo-semver-rules.mdc
      RULE: Before proposing any commit message with feat!:, feat:, or fix:, agent must:
      1. Look up repo's semver_rules_ref in workspace-manifest.json
      2. Read the matching rule set from docs/per-repo-semver-rules.yaml
      3. Verify the change matches the declared bump level
      4. For post-1.0.0 repos: if change is MAJOR, stop and request user approval
      alwaysApply: true, priority: 98 (highest among semver rules).
    status: done
    note: "Done 2026-03-11 — commit d359973: cursor-rules/core/per-repo-semver-rules.mdc created"

  # ─── PHASE 4: AGENT MAJOR-BUMP BLOCKER ───

  - id: p4a-quickmerge-advisory-only
    content: |
      Update unified-trading-pm/scripts/quickmerge.sh: REMOVE any version-bump logic entirely.
      quickmerge.sh NEVER bumps versions — it only merges code. Version bumps are GHA-only.
      Add an advisory Stage 0.3 comment/print (NOT an exit 1) that says:
      "NOTE: version bumps are handled autonomously by semver-agent.yml after QG passes on staging.
       No manual version changes are needed. Do NOT edit pyproject.toml version manually."
      This is informational only — quickmerge never reads or writes version numbers.
    status: done
    note: "Done 2026-03-11 — commit ac2e9bf: Stage 0.3 converted from exit-1 gate to advisory-only print"

  - id: p4b-semver-agent-plan-aware
    content: |
      Redesign .github/workflows/semver-agent.yml template:

      TRIGGER: workflow_run on quality-gates.yml completing with conclusion=success AND branch=staging.
      This is a SEPARATE workflow from quality-gates.yml — it observes QG completion, it doesn't run inside it.

      AGENT LOGIC (Claude Haiku monitors work-done vs PM plans):
      1. Read current staging_versions[repo] from PM workspace-manifest.json.
         If not set: baseline = "0.0.0".
      2. Read the git diff (all changed files) since last staging version was set.
      3. Read ALL active PM plans that reference this repo in their repo_gates
         (from unified-trading-pm/plans/active/*.plan.md). Identify which plan todos were completed
         in this batch of changes.
      4. Classify bump magnitude by comparing:
         a. Code diff analysis: removed exports/endpoints → MAJOR; new features → MINOR; fixes → PATCH
         b. Plan todos completed: todos with "feat:" intent → MINOR; "fix:" → PATCH; "feat!:" → MAJOR intent
         c. Use the higher of (a) and (b) as the final bump type
         d. Cross-reference with docs/per-repo-semver-rules.yaml for this repo's semver_rules_ref
      5. Apply pre-1.0.0 override: if current version starts with "0.", MAJOR → MINOR.
      6. Apply 0.0.0 baseline: MAJOR/MINOR from 0.0.0 → 0.1.0; PATCH → 0.0.1.
      7. If bump is MAJOR and version >= 1.0.0:
         - Do NOT bump. Trigger the major-bump-approval.yml workflow via workflow_dispatch.
         - The approval workflow requires a human trigger (or admin script with GH_PAT).
         - Log: "MAJOR bump staged — awaiting approval via GHA workflow_dispatch or admin approval script."
      8. Otherwise: dispatch version-bump to PM → updates staging_versions in manifest.

      NO version bumps happen inside quickmerge.sh or any local script. This workflow is the SOLE authority.
    status: done
    note: "Done 2026-03-11 — commit e68635d: semver-agent.yml redesigned as QG-triggered plan-aware workflow"

  - id: p4c-major-bump-approval-workflow
    content: |
      Create .github/workflows/major-bump-approval.yml in each repo (via rollout template):

      TRIGGER: workflow_dispatch with inputs:
        - repo: repo name
        - proposed_version: the new MAJOR version (e.g. "2.0.0")
        - reason: summary of why this is MAJOR
        - approver: name/GH handle of approver

      Also triggerable by admin script:
        bash unified-trading-pm/scripts/approve-major-bump.sh {repo} {version} --admin-pat $GH_PAT

      LOGIC:
      1. Verify the approver has write access to the repo (via GH API)
      2. Verify the repo's codex/10-audit/repos/{repo}.yaml has all gates met (or N/A declared)
         for the v1.0.0 checklist (CR5, DR3, DR4, BR2, BR3, BR4)
      3. If gates not met: print what's missing; exit 1 (approval denied, not blocked permanently)
      4. If gates met: dispatch version-bump to PM with the approved MAJOR version
      5. Update codex/10-audit/repos/{repo}.yaml: set br8_user_approved.status="pass",
         br8_user_approved.approved_by={approver}, br8_user_approved.approved_date={today}

      Create the approval script: unified-trading-pm/scripts/approve-major-bump.sh
    status: todo
    note: "Admin script uses GH_PAT with admin rights to trigger the GHA approval workflow programmatically."

  # ─── PHASE 5: PROPAGATION TO AGENT CONTEXTS ───

  - id: p5a-agents-md-readiness-section
    content: |
      Update unified-trading-pm/AGENTS.md: add Section 10 "Repo Readiness & Semver Rules".
      Content (brief, authoritative):
      - Readiness SSOT: codex/10-audit/REPO_READINESS_CHECKLIST.yaml + repos/{repo}.yaml
      - CR0-CR5, DR0-DR6, BR0-BR8 — one-line each
      - Deployment modes: batch | live | both (per repo's deployment_modes field)
      - Business modes: either or both (per repo's business_modes field)
      - v1.0.0 gate: CR5(main) + DR3 + DR4 + BR2 + BR3 + BR4 + BR8 (no exceptions)
      - No agent may set BR8 or v1.0.0 autonomously
      - Per-repo semver rules: docs/per-repo-semver-rules.yaml (look up semver_rules_ref in manifest)
    status: done
    note: "Done 2026-03-11 — commit 41d833c: AGENTS.md Section 10 added on feat/agent-propagation-readiness"

  - id: p5b-sub-agent-rules-readiness
    content: |
      Update unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md:
      Add Section 10 "Readiness Checklist & Semver" (mirrors AGENTS.md Section 10 but in mandatory imperative style).
      Critical additions beyond AGENTS.md:
      - "Read {repo}/.readiness-ref to find the codex checklist for this repo before claiming any stage is complete"
      - "To check a repo's readiness state: cat unified-trading-codex/10-audit/repos/{repo}.yaml"
      - "NEVER advance a repo's readiness stage unless all criteria in the checklist item are met"
    status: done
    note: "Done 2026-03-11 — commit 1162e17: SUB_AGENT_MANDATORY_RULES Section 10 added"

  - id: p5c-overnight-orchestrator-readiness
    content: |
      Update unified-trading-pm/.github/workflows/overnight-agent-orchestrator.yml:
      1. Add sibling-clone step for unified-trading-codex (same GH_PAT pattern as other sibling clones)
      2. In each tier's Claude Haiku agent prompt, inject:
         - Current CR/DR/BR state for repos in this tier from codex/10-audit/repos/
         - "Before proposing any semver bump, read docs/per-repo-semver-rules.yaml"
         - "After any quickmerge, update codex/10-audit/repos/{repo}.yaml with new CR stage"
         - "Never set BR8 or v1.0.0 autonomously — present readiness summary to user instead"
    status: done
    note: "Done 2026-03-11 — commit 2cb3d41: overnight-agent-orchestrator.yml readiness context injected"

  - id: p5d-rules-alignment-readiness-check
    content: |
      Update unified-trading-pm/.github/workflows/rules-alignment-agent.yml:
      Add a step: for any plan change that introduces new per-repo readiness criteria, verify
      codex/10-audit/REPO_READINESS_CHECKLIST.yaml is updated to match. If not, create the update.
      Specifically check: new N/A declarations, new BR/DR gates, new repo types added to manifest.
    status: done
    note: "Done 2026-03-11 — commit 1076275: rules-alignment-agent.yml readiness check added"

  # ─── PHASE 6: PM/CODEX FORMAL STATUS ───

  - id: p6a-pm-codex-formal-waiver
    content: |
      Update code_readiness_master_plan_2026_03_11.plan.md repo_gates:
      - unified-trading-pm: CR5=done (v1.2.0); DR N/A (infra tooling, not deployed as service); BR N/A.
      - unified-trading-codex: CR5=done (docs-only, no Python source to quality-gate);
        DR N/A; BR N/A; v1.0.0 eligible per infra exemption.
      Add readiness_note with formal waiver rationale for each.
      Create codex/10-audit/repos/unified-trading-pm.yaml and unified-trading-codex.yaml with infra template.
    status: todo

  - id: p6b-codex-version-bump
    content: |
      Check unified-trading-codex version in pyproject.toml. If <1.0.0:
      1. Create codex/10-audit/repos/unified-trading-codex.yaml with all non-applicable gates marked "na"
         with documented reasons; BR8 marked "pending — awaiting user approval"
      2. Present to user the v1.0.0 readiness summary:
         "CR5: done (docs repo, no Python QG required). DR1-DR6: N/A (no Cloud Run deployment).
          BR2: N/A (no circuit breaker). BR3: N/A (no UEI events). BR4: N/A (no PnL/perf targets).
          BR5-BR7: N/A. BR8: PENDING — awaiting your approval."
      3. Do NOT create the version PR until user gives explicit approval in session.
      4. After approval: commit codex/10-audit/repos/unified-trading-codex.yaml with BR8 status=pass,
         then create the v1.0.0 PR.
    status: todo
    blocked_by: p6a-pm-codex-formal-waiver
    note: "BR8 required even for infra repos — consistent rule, no exceptions."

  # ─── PHASE 7: AUTOMATED READINESS VERIFIER ───

  - id: p7a-readiness-verifier-script
    content: |
      Create unified-trading-pm/scripts/check-repo-readiness.py
      Reads codex/10-audit/repos/{repo}.yaml (declared state), then runs automated checks:
      - CR1: grep NotImplementedError, TODO, FIXME in source (excluding tests/)
      - CR2: read coverage.xml vs declared coverage_pct
      - CR3: parse manifest deps, check tests/integration/ for each dep's test file
      - CR4: check for ruff/basedpyright error files from last QG run
      - DR3 (services): check if .readiness-ref health endpoint is reachable (non-blocking)
      Outputs declared vs verified table. Flags UNVERIFIED mismatches. Does NOT modify checklist files.
    status: todo

  - id: p7b-readiness-verifier-gha
    content: |
      Create unified-trading-pm/.github/workflows/readiness-verifier.yml
      Trigger: workflow_dispatch (tier filter), schedule: "0 3 * * *" daily.
      Clones codex as sibling, runs check-repo-readiness.py for specified tier.
      Output: GitHub Step Summary table + Telegram alert on mismatches.
    status: todo
    blocked_by: p7a-readiness-verifier-script

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
| `codex/10-audit/README.md`                                      | 1c    | SSOT declaration               |
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
| `pm/plans/active/code_readiness_master_plan_2026_03_11.plan.md` | 6a    | PM/Codex N/A waivers           |
| `pm/scripts/check-repo-readiness.py`                            | 7a    | New verifier script            |
| `.github/workflows/readiness-verifier.yml`                      | 7b    | New GHA workflow               |

---

## Verification

1. `cat codex/10-audit/repos/execution-service.yaml` — must show batch + live deployment sections
2. `cat execution-service/.readiness-ref` — must contain `codex/10-audit/repos/execution-service.yaml`
3. On a post-1.0.0 test: `bash scripts/quickmerge.sh "feat!: test" --agent` must exit 1
4. `grep -c "CR1\|cr1_functionality" AGENTS.md` > 0
5. `python scripts/check-repo-readiness.py --repo unified-events-interface` outputs CR/DR/BR table
