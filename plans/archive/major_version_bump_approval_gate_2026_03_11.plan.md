---
doc_type: plan
title: major-version-bump-approval-gate-2026-03-11
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: "2026-03-11"
overview:
  "Any MAJOR version bump — including the initial release to 1.0.0 — for ANY repo MUST go through\na human-approval
  gate: GitHub Issue created automatically, Telegram alert sent with the issue URL,\nuser comments /approve on the
  issue, GHA then bumps pyproject.toml on the staging branch and updates\nworkspace-manifest.json staging_versions in
  unified-trading-pm. Applies equally to:\n  - Autonomous semver-agent.yml detecting a post-1.0.0 MAJOR bump\n  - Any
  human or agent requesting the initial 0.x.x → 1.0.0 promotion\nNO agent (GHA autonomous, overnight orchestrator,
  interactive Claude, Cursor) may directly set a\nMAJOR version without this approval loop. This rule propagates to
  AGENTS.md, SUB_AGENT_MANDATORY_RULES,\ncursor rules, overnight-orchestrator tier prompts, and GHA agent prompt
  injections.\n"
type: infra
epic: epic-infra
completion_gates: { code: C5, deployment: D1, business: none }
repo_gates:
  - { repo: unified-trading-pm, code: C5, deployment: D1, business: none, readiness_note: "GHA templates
        updated/created, cursor rules written, AGENTS.md + SUB_AGENT_MANDATORY_RULES updated,

        overnight-orchestrator and rules-alignment injected. Propagation script rolls templates to all repos.

        " }
  - {
      repo: unified-trading-codex,
      code: C5,
      deployment: none,
      business: none,
      readiness_note: semver.md updated with MAJOR bump approval requirement.,
    }
todos:
  - { id: s1a-update-semver-agent-telegram, content: "Update
        `unified-trading-pm/scripts/propagation/templates/semver-agent.yml`:\n1. When MAJOR bump detected (both
        pre-1.0.0 → 1.0.0 case AND post-1.0.0 MAJOR case):\n   - Create GitHub Issue using `gh issue create`
        with:\n     * Title: \"[MAJOR BUMP PENDING] {repo}: {current_version} → {proposed_version}\"\n     * Label:
        \"major-bump-pending\" (consistent — handler checks this label)\n     * Body must include a <!--
        major-bump-metadata {...} --> HTML comment block with JSON:\n       { \"repo\": \"...\", \"proposed_version\":
        \"...\", \"current_version\": \"...\",\n         \"staging_branch\": \"staging\", \"staging_commit\": \"...\",
        \"reason\": \"...\" }\n       This is machine-parseable by major-bump-issue-handler.yml\n   - Send Telegram
        alert after issue creation:\n     MSG=\"\U0001F534 Major version bump requires approval\\nRepo:
        {repo}\\n{current} → {proposed}\\n{issue_url}\"\n     Use: curl to Telegram bot API with ${{
        secrets.TELEGRAM_BOT_TOKEN\
        \ }} and ${{ secrets.TELEGRAM_CHAT_ID }}\n     Use `|| true` to not fail if Telegram is unavailable\n2. The step
        for 0.x.x → 1.0.0 is currently the \"pre-1.0.0 override\" (feat!: → MINOR on 0.x.x).\n   Keep that override
        (autonomous agents cannot auto-cross to 1.0.0), BUT if the compute step\n   would produce 1.0.0 via MINOR
        overflow (0.9.x + MINOR = 1.0.0), special-case this: cap at\n   0.10.0 instead of 1.0.0. The 1.0.0 cross ALWAYS
        requires human approval via the issue flow.\n3. Current label used by semver-agent is \"major-bump-approval\" —
        change to \"major-bump-pending\"\n   for consistency with the new handler.\n", status: done, note: "Done
        2026-03-11 — commit b99a826. Label fixed to major-bump-pending, Telegram alert added,

        metadata JSON block embedded in issue body. MINOR overflow cap comment added.

        " }
  - { id: s1b-create-request-major-bump-workflow, content: "Create
        `unified-trading-pm/scripts/propagation/templates/request-major-bump.yml`:\nThis is for HUMAN-INITIATED major
        bump requests (including the initial 0.x.x → 1.0.0 promotion).\n\nTRIGGER: workflow_dispatch with inputs:\n  -
        proposed_version: the new MAJOR version (e.g. \"1.0.0\" or \"2.0.0\")\n  - reason: human-readable reason
        (required)\n  - approver: GitHub handle of requester (defaults to GITHUB_ACTOR)\n\nLOGIC:\n1. Read current
        version from pyproject.toml\n2. Validate proposed_version is MAJOR bump (proposed_major >= 1, proposed >
        current)\n3. Create GitHub Issue with label \"major-bump-pending\" + metadata JSON block (same format as
        s1a)\n4. Send Telegram: \"\U0001F534 Major bump REQUESTED: {repo} {current} → {proposed}\\nApprove:
        {issue_url}\"\n5. Output issue URL to GitHub Step Summary\n6. EXIT 0 — the actual bump happens ONLY when user
        approves the issue via major-bump-issue-handler.yml\n\nThis replaces the existing major-bump-approval.yml's\
        \ \"immediately dispatch\" pattern.\nThe old major-bump-approval.yml becomes a deprecated alias (add header:
        DEPRECATED — use request-major-bump.yml).\n", status: done, note: Done 2026-03-11 — commit b99a826.
        request-major-bump.yml created with workflow_dispatch + issue + Telegram. }
  - { id: s1c-create-major-bump-issue-handler, content: "Create
        `unified-trading-pm/scripts/propagation/templates/major-bump-issue-handler.yml`:\n\nTRIGGER: issue_comment with
        types: [created]\nCONDITION: github.event.issue.labels.*.name contains \"major-bump-pending\"\nPERMISSIONS:
        contents: write, issues: write\n\nON /approve comment (case-insensitive, trimmed):\n1. Verify commenter has
        write/maintain/admin access to the repo via GH API\n   (GET
        /repos/{org}/{repo}/collaborators/{commenter}/permission → permission must be write/maintain/admin)\n   If not:
        reply with error comment, do NOT bump\n2. Parse metadata from issue body: <!-- major-bump-metadata { ... } -->
        block\n   Extract: repo, proposed_version, current_version, staging_branch, staging_commit, reason\n3. Checkout
        target repo at staging branch (sparse clone is fine: depth=1)\n   Use: git clone --depth=1 --branch staging
        https://{GH_TOKEN}@github.com/{org}/{repo}.git /tmp/target\n4. Bump pyproject.toml version on staging:\n   -
        Use\
        \ python3 re.sub to replace version = \"current_version\" → \"proposed_version\"\n   - git commit: \"chore: bump
        version to {proposed_version} [major-bump approved by {approver}]\"\n   - git push origin staging\n   CRITICAL:
        this ONLY happens on staging. Never touches main.\n5. Dispatch version-bump to unified-trading-pm:\n   POST
        /repos/IggyIkenna/unified-trading-pm/dispatches\n   event_type: version-bump\n   client_payload: { repo,
        version: proposed_version, branch: staging, commit_sha: \"major-bump-approved\", approved_by: approver }\n6.
        Send Telegram: \"✅ Major bump APPROVED: {repo} → v{proposed_version} on staging (by
        @{approver})\\n{issue_url}\"\n7. Add comment to issue: \"✅ APPROVED by @{approver} on {date}\\nVersion
        {proposed_version} bumped in pyproject.toml on staging.\"\n8. Remove label \"major-bump-pending\", add label
        \"major-bump-approved\"\n9. Close issue with state_reason: \"completed\"\n\nON /reject comment
        (case-insensitive, trimmed):\n1. Same write-access check\n2.\
        \ Send Telegram: \"❌ Major bump REJECTED: {repo} → v{proposed_version} (by @{approver})\\n{issue_url}\"\n3. Add
        comment: \"❌ REJECTED by @{approver} on {date}. No version change.\"\n4. Remove label \"major-bump-pending\",
        add label \"major-bump-rejected\"\n5. Close issue with state_reason: \"not_planned\"\n\nIMPORTANT: Use `|| true`
        on Telegram curl so workflow never fails due to Telegram unavailability.\nIMPORTANT: The step that bumps
        pyproject.toml must run ONLY on /approve (not /reject or unrecognized).\n", status: done, blocked_by: s1a-update-semver-agent-telegram, note: Done
        2026-03-11 — commit b99a826. major-bump-issue-handler.yml created with full /approve and /reject flows. }
  - {
      id: s1d-update-approve-major-bump-script,
      content:
        "Update `unified-trading-pm/scripts/approve-major-bump.sh`:\nChange from: triggers major-bump-approval.yml
        (workflow_dispatch → immediately bumps)\nChange to: triggers request-major-bump.yml (workflow_dispatch → creates
        issue + Telegram)\n\nUpdate the script header comment:\n  \"This script REQUESTS a major bump by triggering
        request-major-bump.yml.\n   The actual version bump ONLY happens when a human approves the GitHub Issue\n   that
        the workflow creates (by commenting /approve on the issue).\"\n\nUpdate the INPUTS_JSON to match
        request-major-bump.yml inputs (proposed_version, reason, approver).\nUpdate the workflow URL from
        major-bump-approval.yml to request-major-bump.yml.\n",
      status: done,
      blocked_by: s1b-create-request-major-bump-workflow,
      note: Done 2026-03-11 — commit b99a826. approve-major-bump.sh updated to use request-major-bump.yml.,
    }
  - {
      id: s1e-propagate-issue-handler-to-all-repos,
      content:
        "Roll out major-bump-issue-handler.yml to all repos via the propagation script:\n1. Add
        \"major-bump-issue-handler.yml\" to the list of templates
        in:\n   `unified-trading-pm/scripts/propagation/rollout-gha-template.sh` (or equivalent)\n2. Run the rollout for
        all 65 repos in workspace-manifest.json\n   (or document the rollout command so CI can do it)\n3. Ensure
        \"major-bump-pending\" and \"major-bump-approved\" and \"major-bump-rejected\" labels\n   exist in each repo.
        Add a label-creation step to the propagation script if missing.\n4. Deprecate major-bump-approval.yml in each
        repo:\n   Add DEPRECATED header comment pointing to request-major-bump.yml.\n",
      status: done,
      blocked_by: s1c-create-major-bump-issue-handler,
      note: "Done 2026-03-11. 63 repos processed (all manifest repos excl. pm + codex).

        Workflow files copied + labels created in all 63. ~32 pushed to main directly;

        ~24 have open PRs on branch chore/major-bump-workflows-plan64.

        Labels: major-bump-pending (D93F0B), major-bump-approved (0E8A16), major-bump-rejected (B60205).

        ",
    }
  - { id: s2a-cursor-rule-major-bump-prohibition, content: "Create
        `unified-trading-pm/cursor-rules/core/major-bump-approval-required.mdc`:

        " }
---

      description: "ANY major version bump (including initial 0.x.x → 1.0.0) REQUIRES a human-approved GitHub Issue — no agent may set a MAJOR version autonomously"
      alwaysApply: true
      priority: 99
      tags: [semver, critical, security]
      ---

      # MAJOR Version Bump Approval Gate — ABSOLUTE RULE

      ## THE RULE (NO EXCEPTIONS)

      NO agent — Claude Code, Cursor, overnight GHA orchestrator, or any autonomous system — may:
      - Edit pyproject.toml to set a version with MAJOR >= 1 that is higher than the current MAJOR
      - Dispatch a version-bump event to unified-trading-pm with a proposed MAJOR version increase
      - Manually create a commit that bumps MAJOR version
      - Comment /approve on a major-bump-pending issue (agents cannot self-approve)

      This applies equally to:
        - Post-1.0.0 MAJOR bumps (e.g. 1.3.2 → 2.0.0)
        - Initial 1.0.0 promotion from any 0.x.x version
        - Infra repos (PM, codex, deployment-service) — no exceptions

      ## HOW MAJOR BUMPS HAPPEN (ONLY path)

      1. semver-agent.yml detects MAJOR needed → creates GitHub Issue with label "major-bump-pending"
         + sends Telegram alert with issue URL
      2. Human reviews the issue and comments `/approve` (or `/reject`)
      3. major-bump-issue-handler.yml fires → bumps pyproject.toml on staging branch ONLY
         + dispatches version-bump to unified-trading-pm staging_versions
      4. The staged version then flows through the normal QG → SIT → main cascade

      OR human-initiated:
      1. bash scripts/approve-major-bump.sh {repo} {version} --reason "..." --admin-pat $GH_PAT
         → triggers request-major-bump.yml → creates issue + Telegram
      2. Same approval step as above

      ## AGENT RESPONSE TO MAJOR BUMP NEED

      When you detect that changes require a MAJOR bump:
      1. DO NOT modify pyproject.toml version
      2. DO NOT dispatch version-bump with a MAJOR version
      3. DO report to the user: "This change requires a MAJOR version bump for {repo}.
         To initiate approval: bash scripts/approve-major-bump.sh {repo} X.0.0 --reason '...' --admin-pat $GH_PAT
         OR: run the request-major-bump.yml workflow from the GitHub Actions UI."
      4. Proceed with the code change without version bumping

      ## PRE-1.0.0 OVERRIDE (unchanged)

      On 0.x.x repos: feat!: bumps MINOR (0.x.y → 0.x+1.0), NOT MAJOR.
      Semver-agent.yml enforces this. No agent should auto-generate 1.0.0.
      MINOR overflow cap: 0.9.x + MINOR → 0.10.0 (NOT 1.0.0). Hard cap.
    status: done
    note:
      "Done 2026-03-11 — commit dd02598. major-bump-approval-required.mdc created (alwaysApply: true, priority: 99)."

- id: s2b-agents-md-strengthen-major-bump content: | Update `unified-trading-pm/AGENTS.md` §10 "Repo Readiness Checklist
  & Semver Rules": Strengthen the MAJOR bump section. Current text says "request user approval" — make it explicit:

  Add after the existing v1.0.0 Gate paragraph:

  ### MAJOR Bump Approval Gate (ABSOLUTE — applies to ALL repos including infra)

  NO agent may bump MAJOR version autonomously. The ONLY approved path is: 1. semver-agent.yml or request-major-bump.yml
  creates GitHub Issue (label: major-bump-pending) 2. Telegram alert sent to user with issue URL 3. User comments
  /approve on the issue → major-bump-issue-handler.yml bumps staging pyproject.toml + dispatches version-bump to PM
  manifest To REQUEST a major bump from CLI: bash unified-trading-pm/scripts/approve-major-bump.sh {repo} {X.0.0}
  --reason "..." --admin-pat $GH_PAT Agents must NEVER: - Edit pyproject.toml to increase MAJOR version - Dispatch
  version-bump events with MAJOR version increase - Comment /approve on major-bump-pending issues (agents cannot
  self-approve) status: done note: "Done 2026-03-11 — commit dd02598. AGENTS.md §10 MAJOR Bump Approval Gate subsection
  added."

- id: s2c-sub-agent-rules-major-bump content: | Update `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
  §10: Add a new subsection after the existing semver rules:

  ### ABSOLUTE PROHIBITION: MAJOR Version Bumps

  You (a sub-agent) are PROHIBITED from:
  - Editing any pyproject.toml to increase the MAJOR version component
  - Dispatching any version-bump event where the proposed version is a MAJOR increase
  - Writing any commit that bumps a repo's MAJOR version
  - Commenting /approve on any GitHub issue (you cannot self-approve)

  If your task would logically require a MAJOR bump:
  1. Complete the CODE changes (normal quickmerge flow)
  2. Do NOT bump the version
  3. Report to the orchestrator: "MAJOR bump required for {repo}: current={X}, proposed={X+1}. Requires human approval.
     Run: bash scripts/approve-major-bump.sh {repo} {X+1}.0.0 --reason '...' --admin-pat $GH_PAT"

  This rule has NO exceptions — not for infra repos, not for 0.x.x → 1.0.0, not for "obvious" cases. status: done note:
  "Done 2026-03-11 — commit dd02598. ABSOLUTE PROHIBITION subsection added to SUB_AGENT_MANDATORY_RULES.md §10."

- id: s2d-overnight-orchestrator-inject-prohibition content: | Update
  `unified-trading-pm/.github/workflows/overnight-agent-orchestrator.yml`: In every tier job (T0, T1, T2, T3, T4a, T4b,
  T4c, T5, T6, infra), inject the following text at the TOP of the Claude Haiku agent prompt (before any repo-specific
  instructions):

  "ABSOLUTE RULE — MAJOR VERSION BUMP PROHIBITION: You are NOT permitted to bump any repo's MAJOR version (including
  0.x.x → 1.0.0). Do NOT edit pyproject.toml to increase the MAJOR component. Do NOT dispatch version-bump events with a
  higher MAJOR version. If MAJOR bump is needed: report it to the user and stop. Do not proceed. Only semver-agent.yml
  can trigger the MAJOR bump approval issue flow. Any attempt to bypass this rule will be detected by
  rules-alignment-agent.yml."

  This injection must appear BEFORE the existing prompt text in each tier. status: done note: "Done 2026-03-11 — commit
  dd02598. MAJOR BUMP PROHIBITION block injected at top of all 4 tier heredocs (T0–T3)."

- id: s2e-rules-alignment-check-major-bump content: | Update
  `unified-trading-pm/.github/workflows/rules-alignment-agent.yml`: Add a step that checks for compliance with the
  major-bump approval gate:

  1. Scan all pyproject.toml changes in the last 24h of commits across all repos (via PM manifest) Look for: version
     field MAJOR increase without a corresponding "major-bump approved by" commit message
  2. Scan for any direct edits to staging_versions in workspace-manifest.json where MAJOR was incremented without a
     corresponding version-bump dispatch with "approved_by" field
  3. If violations found: send Telegram alert + create PM issue: "MAJOR bump policy violation detected"
  4. Always advisory (warn, not fail) — but Telegram alert is mandatory

  This gives an audit trail and catches any policy bypasses. status: done note: "Done 2026-03-11 — commit dd02598.
  Compliance audit step added to rules-alignment-agent.yml (advisory, exit 0)."

# ─── STREAM 3: CODEX STANDARDS UPDATE ───

- id: s3a-codex-semver-standards-update content: | Update `unified-trading-/codex/06-coding-standards/semver.md` (create
  if it doesn't exist): Add section: "MAJOR Version Bump Approval Gate" Contents mirror cursor rule s2a but written as
  standards prose:
  - Who triggers: any agent or human detecting a MAJOR bump is needed
  - How: GitHub Issue → Telegram → /approve comment → GHA bumps staging only
  - What is forbidden: direct pyproject.toml edits, direct version-bump dispatches with MAJOR increase
  - Monitoring: rules-alignment-agent.yml audits compliance daily
  - Reference: unified-trading-pm/scripts/propagation/templates/major-bump-issue-handler.yml
  - Reference: unified-trading-pm/scripts/approve-major-bump.sh status: done note: "Done 2026-03-11 — commit 9e51dcf
    (codex feat/v1.0.0-release branch). semver.md created with full gate spec."

isProject: false
---

# Major Version Bump Approval Gate

## Problem

Currently:

1. **`semver-agent.yml`** creates a GitHub Issue for post-1.0.0 MAJOR bumps — but **no Telegram alert**, **no structured
   metadata** for auto-parsing, and inconsistent label (`major-bump-approval` vs `major-bump-pending`)
2. **`major-bump-approval.yml`** (workflow_dispatch) immediately bumps version without an Issue creation step — the
   human trigger IS the approval but there is no issue trail or Telegram notification
3. **Rules**: AGENTS.md and SUB_AGENT_MANDATORY_RULES say "stop and request user approval" but don't explain the exact
   mechanism (issue + Telegram + /approve flow)
4. **No handler** exists to act on issue approval comments — the loop is broken

## Target State

```
Any MAJOR bump needed (agent-detected OR human-requested)
         │
         ▼
  GitHub Issue created
  label: "major-bump-pending"
  body includes <!-- major-bump-metadata {...} --> JSON
         │
         ▼
  Telegram alert: "🔴 Major bump pending: {repo} {ver} — {issue_url}"
         │
         ▼
  Human reviews + comments /approve (or /reject)
         │
         ▼ (major-bump-issue-handler.yml fires on issue_comment)
  ┌── Verify commenter write access ────────────────────────┐
  │   Parse metadata from issue body                        │
  │   Bump pyproject.toml on staging branch ONLY            │
  │   Dispatch version-bump to PM (staging_versions)        │
  │   Telegram: "✅ Approved: {repo} → v{ver} on staging"   │
  │   Close issue as completed                              │
  └─────────────────────────────────────────────────────────┘
```

## Key Constraints

- **Staging only**: Version bumps (of any kind) only happen on the `staging` branch. Never main.
- **No self-approval**: Agents cannot comment /approve. Only humans with write access.
- **Infra repos included**: PM, codex, deployment-service all subject to the same gate.
- **MINOR overflow cap**: 0.9.x + MINOR bump → 0.10.0 (NOT 1.0.0). Hard cap in semver-agent.yml.
- **Backward compat**: `major-bump-approval.yml` kept as deprecated alias. `approve-major-bump.sh` updated to use
  `request-major-bump.yml`.

## Files Changed

| File                                                         | Repo  | Change                                                         |
| ------------------------------------------------------------ | ----- | -------------------------------------------------------------- |
| `scripts/propagation/templates/semver-agent.yml`             | pm    | Add Telegram + metadata JSON in issue body + label fix         |
| `scripts/propagation/templates/request-major-bump.yml`       | pm    | NEW — workflow_dispatch → issue + Telegram (no immediate bump) |
| `scripts/propagation/templates/major-bump-issue-handler.yml` | pm    | NEW — issue_comment /approve → bump staging + dispatch         |
| `scripts/approve-major-bump.sh`                              | pm    | Update to trigger request-major-bump.yml                       |
| `cursor-rules/core/major-bump-approval-required.mdc`         | pm    | NEW — alwaysApply priority 99                                  |
| `AGENTS.md` §10                                              | pm    | Strengthen MAJOR bump section                                  |
| `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` §10            | pm    | Add ABSOLUTE PROHIBITION subsection                            |
| `.github/workflows/overnight-agent-orchestrator.yml`         | pm    | Inject prohibition at top of all tier prompts                  |
| `.github/workflows/rules-alignment-agent.yml`                | pm    | Add compliance audit step                                      |
| `06-coding-standards/semver.md`                              | codex | Add MAJOR bump gate section                                    |
| All 65 repos (via propagation)                               | all   | major-bump-issue-handler.yml rolled out                        |
