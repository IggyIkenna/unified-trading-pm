---
name: cicd-audit-remediation-2026-03-13
overview: >
  Remediates all P0/P1/P2 issues identified in the 2026-03-13 CI/CD pipeline audit. Adds diagram auto-regeneration to PM
  quickmerge so the YAML remains the SSOT and the SVG/HTML are always current. Extends the diagram and CI-CD-FLOW.md to
  show the active-plan-driven agent context cascade: plan → codex → cursor rules → agent context → implementation → dual
  TG approval gates (plan sign-off + merge sign-off). Adds E2E tests for every fix, exercised via admin sync scripts
  where GHA trigger is needed. Hardens race conditions (manifest concurrency, heredoc exits, dispatch retries, conflict
  retry-promotion, SIT debounce starvation). Ensures human-readable semver is the headline at every layer — manifest
  history, Telegram alerts, deployment UI, Docker tags — with SHAs as metadata only.
type: infra
epic: epic-infra
status: active

completion_gates:
  code: C4
  deployment: none
  business: none

repo_gates:
  - repo: unified-trading-pm
    code: C4
    deployment: none
    business: none
    readiness_note: "DR N/A: infra-only. BR N/A: internal tooling."
  - repo: system-integration-tests
    code: C3
    deployment: none
    business: none
    readiness_note: "P0 rollback + SHA-pinning tests live here."
  - repo: deployment-ui
    code: C3
    deployment: none
    business: none
    readiness_note: "BuildSelector multi-env + human-readable deployment IDs."
  - repo: deployment-service
    code: C3
    deployment: none
    business: none
    readiness_note: "deployed_versions writeback + deployment ID format."

depends_on:
  - cicd_e2e_test_plan_2026_03_13
  - conflict_resolution_agent_2026_03_13
  - full_autonomous_agent_ci

todos:
  # ── Diagram SSOT (do first — unblocked) ──────────────────────────────────

  - id: diagram-regen-in-quickmerge
    content: >
      Make the CI/CD diagram regenerate automatically as part of PM quality gates so it can never drift from the YAML
      SSOT. Steps: (1) In scripts/quality-gates.sh, after the final `source` line, add:
          echo "Regenerating CI/CD pipeline diagram..."
          python3 "${REPO_ROOT}/scripts/generate-cicd-diagram.py"
      (2) Add generate-cicd-diagram.py to all codex EXCLUDE_GLOBS arrays in
          quality-gates.sh so basedpyright/codex checks skip it.
      (3) Verify: run bash scripts/quality-gates.sh, confirm SVG/HTML updated. Acceptance: every PM quickmerge that
      touches cicd-pipeline-definition.yaml or generate-cicd-diagram.py auto-regenerates the outputs.
    status: done

  - id: fix-conflict-node-semantics
    content: >
      The 'conflict detected?' diamond has inverted YES/NO visual semantics: red NO badge goes to staging_to_main
      (proceed), confusing readers. Fix in cicd-pipeline-definition.yaml: (1) Rename node label to "merge\nconflict?"
      (shorter, unambiguous). (2) Connection conflict_detected → staging_to_main: change outcome to
          "yes" (green — "yes, conflict free, proceed") and label "clean".
          Wait — actually flip: rename label to "conflict\nfree?" so:
          YES (green) → staging_to_main (no conflict, proceed)
          NO (red)    → conflict_agent + tg_conflict_detected (conflict exists)
      (3) Update all connection labels and outcomes accordingly. (4) Regenerate diagram. Acceptance: green YES goes to
      staging_to_main, red NO goes to conflict agent.
    status: done

  - id: fix-staging-locked-swimlane
    content: >
      staging_locked_decision is in 'developer' swimlane but the decision is made by GHA (reads staging_status.locked
      from workspace-manifest.json via staging-lock-gate required status check). Move to 'gha_repo' swimlane. Check col
      spacing against gha_repo neighbours after move. Regenerate diagram.
    status: done

  - id: add-missing-connections
    content: >
      Add connections that are real but missing from the diagram: (1) staging_to_main → manifest_sync  (implicit PM push
      triggers it; make
          it explicit so codex sync on SIT path is visible).
      (2) plan_alignment annotation: add to annotations section —
          text "advisory: no merge gate" position below.
      (3) Add 'no SIT path' annotation near breaking_decision for PM/codex. Regenerate.
    status: done

  - id: add-plan-cascade-nodes
    content: >
      Add the plan-driven agent context cascade to the diagram. This is the central governance model: plans are the
      canonical context for all agent decisions. New nodes:

      plan_lifecycle (gha_pm, col 1.5, branch agent):
        "Plan created/updated\nactive plans/\nagent or human"
        actor: "Human or agent writes plan;\nPM main push fires cascade"

      tg_plan_ready (telegram, col 3.5, branch agent):
        "Plan ready\nfor human\nreview"
        tooltip: "Telegram notification on plan creation. Human must sign off
          before agent begins implementation. Only two human gates in the
          system: (1) plan approval, (2) merge approval."

      tg_merge_ready (telegram, col 6.0, branch agent):
        "Agent PR ready\nhuman review\n& TG merge gate"
        tooltip: "Second and final human gate. Agent-opened PRs require
          explicit human approval in TG before auto-merge fires. Ensures
          human oversight on all agent-driven changes."

      tg_cloud_build_fail (telegram, col 4.8, branch both):
        "Build failed\n$REPO $BRANCH\nCloud Build"
        tooltip: "Sent when GCP Cloud Build returns non-zero exit. Currently
          NOT IMPLEMENTED — tracked in add-cloud-build-fail-alert todo.
          Marked pending in diagram."

      New connections:
        plan_lifecycle → rules_alignment   (cascades to cursor rules)
        plan_lifecycle → manifest_sync     (cascades to codex)
        plan_lifecycle → tg_plan_ready     (human review notification)
        conflict_agent → tg_merge_ready   (agent PR → second TG gate)
        build_dev → tg_cloud_build_fail    (dashed, pending impl)
        build_staging → tg_cloud_build_fail (dashed, pending impl)
        build_prod → tg_cloud_build_fail   (dashed, pending impl)

      Add annotation on conflict_agent:
        "Context: active plans + codex\n+ AGENTS.md + cursor rules\n
         Human approves plan first"

      Regenerate diagram.
    status: done

  # ── P0 code fixes (race conditions & correctness) ─────────────────────────
  # Principle: no silent state corruption, no deadlocks, no infinite loops.
  # Every mutation is atomic, every dispatch is retried, every error propagates.

  - id: unify-manifest-concurrency-groups
    content: >
      RACE CONDITION: sit-gate.yml and sit-unlock.yml use concurrency group "manifest-update", but staging-to-main.yml
      uses "staging-to-main". These are DIFFERENT groups — if SIT fails at the same moment staging-to-main fires (race
      between staging-validated and sit-failed dispatches), both workflows mutate staging_status concurrently. One write
      wins, one is silently lost. Fix: (1) ALL workflows that mutate workspace-manifest.json must use a SINGLE
      concurrency group:
          concurrency:
            group: manifest-update
            cancel-in-progress: false
          Affected workflows: sit-gate.yml, sit-unlock.yml, staging-to-main.yml, update-repo-version.yml,
          hotfix-mode.yml, major-bump-approval.yml.
      (2) Within each workflow's manifest mutation step, add a compare-and-swap guard:
          MANIFEST_SHA_BEFORE=$(git rev-parse HEAD -- workspace-manifest.json)
          # ... mutate manifest ...
          MANIFEST_SHA_AFTER=$(git rev-parse HEAD -- workspace-manifest.json)
          if [ "$MANIFEST_SHA_BEFORE" != "$MANIFEST_SHA_AFTER" ]; then
            echo "CONFLICT: manifest changed during mutation — retrying"
            git pull --rebase origin main
            # re-run mutation
          fi
      (3) Add JSON schema validation after every manifest write (see add-manifest-json-validation). Test: run
      sit-gate.yml and staging-to-main.yml concurrently via workflow_dispatch — verify serialization, no lost writes.
      Acceptance: zero possibility of concurrent manifest mutations.
    status: pending

  - id: fix-heredoc-exit-propagation
    content: >
      SILENT CORRUPTION: Multiple workflows (sit-gate.yml, sit-unlock.yml, update-repo-version.yml, staging-to-main.yml,
      hotfix-mode.yml) use python3 heredocs to mutate workspace-manifest.json. If the Python block raises an exception
      (corrupted JSON, disk full, key error), bash continues and commits corrupted or empty manifest. Fix: (1) Every
      python3 heredoc block must have || exit 1 after the PYEOF terminator:
          python3 - <<PYEOF || exit 1
          import json
          ...
          PYEOF
      (2) Add set -eo pipefail at the top of every run: block that mutates manifest. (3) After every manifest write,
      validate JSON:
          python3 -c "import json; d=json.load(open('workspace-manifest.json')); assert 'versions' in d" || {
            git checkout -- workspace-manifest.json
            echo "FATAL: manifest corruption detected — reverted"
            exit 1
          }
      Affected files: sit-gate.yml, sit-unlock.yml, staging-to-main.yml, update-repo-version.yml, hotfix-mode.yml. Test:
      introduce a deliberate KeyError in a test branch heredoc — verify workflow fails immediately, manifest is not
      committed in corrupted state. Acceptance: no silent manifest corruption possible.
    status: pending

  - id: fix-semver-staging-trigger
    content: >
      Blocked on: full_autonomous_agent_ci plan § fix-semver-agent-template-staging-trigger. The semver-agent.yml
      template currently fires on 'main' push. Must be fixed to fire on 'staging' push only. Also: atomically disable
      version-bump.yml (set if: false) when semver-agent rolls out to prevent double-bump. Test: push feat: commit to a
      T2 repo, verify ONLY one version bump fires, verify it fires on staging push not main push.
    status: pending
    blocks: fix-semver-agent-template-staging-trigger (full_autonomous_agent_ci)

  - id: add-sit-rollback
    content: >
      When SIT fails, sit-unlock.yml clears the lock but leaves broken code in staging with no automated recovery
      signal. Add: (1) In sit-unlock.yml, after clearing the lock, create a GH Issue with human-readable title:
          "SIT failed: $REPO v$VERSION needs fix or revert" (semver, not SHA)
          with label 'sit-failure' and assignee the last PR author.
      (2) Optionally: open a revert PR to last_known_good_sha (the SHA before
          the failing commit set). Record last_known_good_sha in
          staging_status when sit-gate.yml fires.
      (3) Update diagram: add sit_rollback_issue node in gha_pm, connection
          from sit_unlock_fail → sit_rollback_issue.
      Test: force a SIT failure via admin sync, verify issue is opened with semver in title. Acceptance: engineers know
      immediately what broke (by version, not SHA) and can act without checking GHA logs manually.
    status: done

  - id: add-cascade-cycle-guard
    content: >
      update-repo-version.yml dispatches dependency-update to all direct dependents per manifest DAG. A cycle (repo A
      depends B depends A) causes infinite dispatch. Fix: (1) Before dispatching in update-repo-version.yml, run a DFS
      cycle check on the dependency subgraph for the triggering repo. (2) If cycle detected: send Telegram alert with
      human-readable context:
          "Dependency cycle detected: $REPO_A v$VER_A -> $REPO_B v$VER_B -> $REPO_A — cascade aborted."
          and exit 1 (do NOT dispatch).
      (3) Add cycle-check to validate-alignment.py or a new
          validate-manifest-dag.py script, run in quality-gates.sh.
      Test: introduce a deliberate cycle in a test manifest branch, verify cascade aborts and Telegram fires.
      Acceptance: no infinite dispatch loops possible.
    status: done

  - id: fix-sha-pinning-toctou
    content: >
      Current flow: staging push → 10-min debounce → sit-gate.yml fires → records staging_commits SHAs. But if a [skip
      ci] constraint commit lands during the debounce, it's in staging but not in the tested SHA set. staging_to_main
      promotes the full current staging (including untested [skip ci] commits), creating a gap between tested and
      deployed state. Fix: (1) Record staging_commits at END of smoke-test-gate.yml debounce
          (immediately before dispatching to SIT), not when sit-gate.yml fires.
          This captures the full staging state at the moment testing begins.
          Record BOTH sha AND version for each repo (see enrich-staging-commits-with-semver).
      (2) In staging-to-main.yml, verify that current staging HEAD is within
          the tested SHA set (or is a [skip ci] descendant of a tested SHA).
          If not, re-trigger SIT before promoting.
      Test: push a [skip ci] commit during SIT run, verify it gets included in the next SIT set or blocked from
      promotion.
    status: done

  - id: wire-conflict-resolution-retry-promotion
    content: >
      DEADLOCK: staging-to-main.yml detects a merge conflict → dispatches merge-conflict-detected → conflict agent opens
      a resolution PR → human approves → PR merges. But then NOBODY retriggers staging-to-main.yml. The promotion is
      stuck — the workflow that detected the conflict already exited, and no workflow re-fires it. Fix: (1) In
      conflict-resolution-agent.yml, after the resolution PR is created, add metadata to the PR body:
          "<!-- AUTO_RETRY_PROMOTION: true -->"
      (2) Create .github/workflows/conflict-resolution-merged.yml:
          trigger: pull_request (closed, merged) on branches matching auto-resolve/*
          Steps: if PR body contains AUTO_RETRY_PROMOTION marker:
            - Wait 30s for GitHub state to settle
            - Re-dispatch staging-validated to PM (retries the promotion)
            - Telegram: "Conflict resolved for $REPO v$VERSION — retrying staging→main promotion"
      (3) Add idempotency: staging-to-main.yml checks if current staging SHAs have already been promoted
          (compare staging_commits to main_commits). If already promoted, exit early — no duplicate promotion.
      Test: create a merge conflict, let agent resolve it, merge resolution PR — verify staging-to-main fires
      automatically. Acceptance: no manual intervention needed after conflict resolution PR merges.
    status: pending

  - id: verify-staging-lock-gate-all-repos
    content: >
      The SHA-pinning TOCTOU fix (fix-sha-pinning-toctou) depends on staging-lock-gate being a REQUIRED status check on
      every repo's staging branch protection rules. If any repo is missing it, commits slip through during SIT. Fix: (1)
      Script: scripts/repo-management/verify-staging-lock-gate.sh
          For each repo in workspace-manifest.json with arch_tier T0-T3:
            gh api repos/$OWNER/$REPO/branches/staging/protection/required_status_checks
            Verify "staging-lock-gate" is in the contexts list.
            If missing: log and optionally add via gh api PUT.
      (2) Add to quality-gates.sh as a manifest validation step. (3) Run in overnight orchestrator as a pre-check.
      Acceptance: 100% of repos with staging branch have staging-lock-gate as required check.
    status: pending

  - id: add-dispatch-retry-with-alerting
    content: >
      SILENT FAILURE: All repository_dispatch calls across the pipeline are fire-and-forget (curl with || echo WARNING).
      If a dispatch fails (archived repo, network blip, GitHub API degradation), the target repo never receives the
      event. Examples: staging-locked dispatch to 65 repos — if 3 fail, those repos never learn staging is locked.
      staging-unlocked — if 5 fail, those repos stay locked forever. dependency-update — if 2 of 10 dependents miss it,
      they build against stale deps. Fix: (1) Create unified-trading-pm/scripts/dispatch-helpers.sh:
          Function dispatch_with_retry(repo, event_type, payload):
            for attempt in 1 2 3; do
              HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
                "https://api.github.com/repos/$OWNER/$repo/dispatches" ...)
              [[ "$HTTP" == "204" ]] && return 0
              sleep $((attempt * 5))
            done
            send_telegram "Dispatch $event_type to $repo failed after 3 attempts"
            return 1
          Function dispatch_to_all(event_type, payload, repo_list):
            FAILED=()
            for repo in $repo_list; do
              dispatch_with_retry "$repo" "$event_type" "$payload" || FAILED+=("$repo")
            done
            if [ ${#FAILED[@]} -gt 0 ]; then
              send_telegram "Dispatch $event_type failed for: ${FAILED[*]}"
            fi
      (2) Source dispatch-helpers.sh in: sit-gate.yml, sit-unlock.yml, staging-to-main.yml, update-repo-version.yml,
          manifest-sync.yml, overnight-agent-orchestrator.yml.
      (3) Replace all bare curl dispatch calls with dispatch_with_retry. Test: temporarily block a test repo's webhook —
      verify 3 retries fire, then Telegram alert. Acceptance: no silent dispatch failures possible.
    status: pending

  - id: add-sit-debounce-starvation-cap
    content: >
      If PRs keep merging to staging every 5 minutes during business hours, the 10-min debounce in smoke-test-gate.yml
      resets each time and SIT NEVER runs. Staging stays locked indefinitely — a liveness failure. Fix: (1) In
      smoke-test-gate.yml, add a max-debounce counter.
          If debounce has been reset more than 3 times consecutively, fire SIT immediately regardless.
          Implementation: use GH Actions cache key "debounce-reset-count" — increment on each cancellation,
          reset to 0 when SIT actually fires.
      (2) Alternative (simpler): use a fixed window instead of rolling debounce.
          "Run SIT at most every 20 min. If staging has new commits since last SIT, fire immediately after 20-min
          cooldown expires."
      (3) Telegram alert when starvation cap triggers: "SIT debounce capped at 3 resets — forcing SIT run for
          staging HEAD $VERSION" (version, not SHA).
      Acceptance: SIT always runs within 30 min of first staging push, regardless of subsequent push frequency.
    status: pending

  - id: add-manifest-json-validation
    content: >
      If a manifest-mutating workflow writes corrupted JSON (partial write, race condition, Python exception), there is
      no automated recovery. The corrupted manifest gets committed to git and breaks all downstream workflows. Fix: (1)
      Create unified-trading-pm/scripts/validate-manifest-json.sh:
          python3 -c "
          import json, sys
          d = json.load(open('workspace-manifest.json'))
          required = ['versions', 'repositories', 'staging_status', 'staging_versions']
          missing = [k for k in required if k not in d]
          if missing:
              print(f'FATAL: manifest missing keys: {missing}', file=sys.stderr)
              sys.exit(1)
          # Validate all versions are valid semver
          import re
          semver = re.compile(r'^\d+\.\d+\.\d+$')
          for repo, ver in d.get('versions', {}).items():
              if not semver.match(ver):
                  print(f'FATAL: {repo} version {ver!r} is not valid semver', file=sys.stderr)
                  sys.exit(1)
          print('Manifest valid')
          " || {
            git checkout -- workspace-manifest.json
            echo "FATAL: manifest corruption detected and auto-reverted"
            # Telegram alert
            exit 1
          }
      (2) Call validate-manifest-json.sh after EVERY manifest write in all mutating workflows. (3) Add to
      quality-gates.sh as a pre-check. Test: write invalid JSON to manifest on a test branch — verify validation catches
      it, reverts, and alerts. Acceptance: corrupted manifest never reaches a committed state.
    status: pending

  # ── P1 silent failure fixes ───────────────────────────────────────────────

  - id: add-cloud-build-fail-alert
    content: >
      Cloud Build failures are currently silent — GHA dispatches fire-and-forget. Fix options (in priority order): (1)
      Configure Cloud Build to publish build results to a GCP Pub/Sub topic.
          Create a GHA workflow cloud-build-status.yml that subscribes via
          Cloud Build webhook (or polls the Cloud Build API) and fires Telegram
          on non-SUCCESS status.
      (2) Alternative (simpler): Add a polling step in cloud-build-router.yml
          after each trigger — poll gcloud builds list --filter="id=$BUILD_ID"
          every 30s until COMPLETE or FAILURE, then send Telegram.
      Preferred: option (2) is simpler, no new GCP infra needed. Poll timeout: max 60 min, max 120 poll iterations. On
      timeout:
          Telegram "Build status unknown after 60 min — check manually: $BUILD_URL"
      Telegram format (human-readable, semver not SHA):
          "Cloud Build FAILED\nRepo: $REPO v$VERSION\nBranch: $BRANCH\nBuild: $BUILD_URL"
      Update diagram: add tg_cloud_build_fail connections from build nodes. Test: introduce a deliberate Docker build
      failure, verify alert fires with version in message.
    status: done

  - id: add-major-bump-approval-handler
    content: >
      MAJOR bump creates a GitHub Issue and fires Telegram but there is no workflow listening for human /approve or
      /reject. This means MAJOR bumps are permanently blocked. Fix: Create .github/workflows/major-bump-approval.yml in
      PM:
        - trigger: issue_comment (created)
        - filter: issue has label 'major-bump-pending'
        - AUTHORIZATION CHECK: verify commenter is in the authorized approvers list:
            if: contains(fromJSON('["IggyIkenna"]'), github.event.comment.user.login)
            Reject with comment "Only authorized maintainers can approve major bumps" if actor is not in list.
            This prevents bots, external contributors, or unauthorized team members from approving breaking changes.
        - if comment body starts with '/approve':
            update manifest.versions[$REPO] to MAJOR version,
            dispatch version-updated to $REPO,
            close issue, Telegram "MAJOR bump approved: $REPO v$OLD_VERSION -> v$NEW_VERSION"
        - if comment body starts with '/reject':
            close issue with 'rejected' label,
            Telegram "MAJOR bump rejected: $REPO — staying at v$CURRENT"
      Test: manually trigger request-major-bump.yml, comment /approve from authorized user, verify version promoted and
      issue closed. Test with unauthorized user — verify rejection. Acceptance: only authorized humans can approve
      breaking version changes.
    status: done

  - id: add-conflict-agent-timeout
    content: >
      conflict-resolution-agent.yml has no timeout. If Claude API is degraded the job hangs indefinitely, team sees
      "working on it..." forever. Fix: (1) Add 'timeout-minutes: 30' to the conflict-resolution-agent job. (2) Add a
      final step with 'if: failure()' that sends Telegram:
          "Conflict agent timed out on $REPO v$VERSION — resolve manually. Branch:
           $BRANCH. Conflicting files: $FILES_LIST."
      (3) Set the Telegram message from step (a) (the "working" message) to
          include an ETA: "agent active, ~10 min, will notify when done."
      Test: mock a long-running agent by adding sleep 2000 in a test workflow, verify timeout fires and Telegram message
      is sent.
    status: done

  - id: add-overnight-t0-escalation
    content: >
      Overnight orchestrator currently sends one Telegram summary at end. If T0 (core libraries) has any failures, the
      whole system may be running against broken interfaces — but this isn't surfaced until someone reads the morning
      message. Fix in overnight-agent-orchestrator.yml: (1) After T0 tier completes, check if any T0 repos failed. (2)
      If any T0 failures: immediately send a PRIORITY Telegram alert
          (separate from morning summary): "T0 FAILURE — overnight audit.
           Core libraries failing: $FAILING_REPOS (with versions). T1-T3 results unreliable.
           Immediate action required."
      (3) Open a GitHub Issue in PM: "Overnight T0 failure: $DATE — $REPOS"
          with label 'critical-audit-failure'.
      (4) Morning summary includes per-repo version info (see enrich-telegram-with-versions). Test: force a T0 repo to
      fail in overnight audit (set exit 1 in test job), verify priority Telegram fires before T1 runs, and message
      includes repo version numbers.
    status: done

  - id: add-staging-to-main-idempotency
    content: >
      If staging-to-main.yml fires twice (GitHub API hiccup, manual re-run, conflict-resolution-merged retrigger), it
      dispatches staging-unlocked to 65 repos twice and attempts to merge staging→main twice. The second merge may
      succeed on already-merged state or create duplicate PRs. Fix: (1) At the start of staging-to-main.yml, before any
      mutation:
          Read staging_commits from manifest.
          Read main_commits.history[0].commits.
          If staging_commits is a subset of main_commits.history[0].commits: exit 0 early.
          "Staging already promoted — skipping duplicate run."
      (2) Before creating the merge PR, check if a staging→main PR already exists:
          EXISTING=$(gh pr list --base main --head staging --json number --jq '.[0].number')
          If exists: reuse it instead of creating a new one.
      Acceptance: running staging-to-main.yml twice with the same staging state produces exactly one promotion.
    status: pending

  - id: add-conflict-agent-dedup
    content: >
      If merge-conflict-detected fires twice for the same conflict (dispatch retry, manual re-trigger), the conflict
      agent opens TWO resolution PRs for the same conflict. Both contain Claude-generated code. Human must close one.
      Fix: (1) In conflict-resolution-agent.yml, before creating a resolution branch:
          Check if branch auto-resolve/$SOURCE-to-$TARGET-* already exists:
            git ls-remote --heads origin "auto-resolve/$SOURCE-to-$TARGET-*" | head -1
          If exists: update the existing branch + PR instead of creating a new one.
      (2) Before opening PR, check if a resolution PR already exists:
          gh pr list --head "auto-resolve/$SOURCE-to-$TARGET" --json number
      Acceptance: duplicate conflict dispatches produce exactly one resolution PR.
    status: pending

  # ── Bot tier isolation & Claude availability ─────────────────────────────
  # Three bot tiers, each with a dedicated API key (separate Anthropic project):
  #   CICD bots      — conflict-resolution, semver, rules-alignment, codex-sync
  #                    (critical path, triggered by human actions, must never be rate-limited)
  #   SysHealth bots — overnight-agent-orchestrator, agent-audit, health-monitor, cassette-drift
  #                    (scheduled/batch, high volume, can be deferred without blocking humans)
  #   Analysis bots  — trading quality, performance, scenario analysis (FUTURE PHASE)
  #                    (separate concern — PnL loss ≠ code quality; deployment decisions manual)

  - id: add-three-tier-bot-api-keys
    content: >
      All agent workflows share a single ANTHROPIC_API_KEY. When overnight audit (65 repos in parallel) exhausts the
      rate limit it blocks conflict-resolution agent — which the team needs immediately to unblock a stuck staging
      merge. Three bot tiers map cleanly to three separate Anthropic project keys:
        ANTHROPIC_API_KEY_CICD      — conflict-resolution-agent.yml,
                                       rules-alignment-agent.yml, codex-sync-agent.yml,
                                       semver-agent.yml. Critical path, low volume,
                                       must never be rate-limited by batch work.
        ANTHROPIC_API_KEY_SYSHEALTH — overnight-agent-orchestrator.yml,
                                       agent-audit.yml (all 65 repos via propagate),
                                       claude-api-health-monitor.yml,
                                       cassette-drift-check.yml. Scheduled/batch.
                                       Rate limits here are deferrable; conflicts are not.
        ANTHROPIC_API_KEY_ANALYSIS  — FUTURE: trading-quality-agent, performance-analysis,
                                       scenario-analysis. Separate Anthropic project so
                                       analysis quota never touches CI/CD or health.
                                       Not wired yet — placeholder secret only.
      Fix: (1) Create and register the three GH secrets (PM repo + propagate SYSHEALTH to
          all 65 service repos via propagate-github-secrets.sh).
      (2) Update each workflow env block with fallback to shared key:
            ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY_CICD
                                  || secrets.ANTHROPIC_API_KEY }}
          Fallback enables gradual rollout without breaking existing workflows.
      (3) Document in docs/repo-management/agent-api-keys.md:
          tier → key → workflows → quota budget → rotation cadence.
      (4) Update diagram annotations (done: overnight=SYSHEALTH, conflict=CICD). (5) POST-ROLLOUT: after confirming all
      tier-specific keys work (verify via
          claude-api-health-monitor.yml for each tier), REMOVE the fallback:
            ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY_CICD }}
          The fallback masks key misconfiguration — if CICD key is wrong, it silently falls back to the shared key,
          defeating isolation. classify_claude_error (add-api-failure-classification) catches 401s explicitly, so
          the fallback is unnecessary once keys are validated. Target: remove within 1 week of rollout.
      Acceptance: overnight audit rate-limit does not affect conflict-resolution or semver agents in the same time
      window. No silent key fallbacks after rollout is confirmed.
    status: done

  - id: add-api-failure-classification
    content: >
      All agent workflows treat any Claude API error identically — job fails, timeout fires, no context. Different error
      modes need different responses:
        401/403 → key invalid/expired: NEVER retry. Open GH Issue
                  "ANTHROPIC_API_KEY_<TIER> invalid — rotate immediately."
                  Telegram "Auth error — {tier} key needs rotation."
        429/529 → rate limited / model overloaded: retry 3x with 15s/60s/300s
                  backoff. If still failing after 3 attempts: graceful skip +
                  Telegram "{tier} rate limited — deferred to next cycle."
        503 / connection refused → Claude infra down: no retry. Telegram
                  "Claude unreachable — check status.anthropic.com. {tier}
                  agents skipped; will retry at next scheduled run." Exit 0.
        Timeout → job exceeded timeout-minutes: Telegram with repo + version + branch
                  + CLAUDE_ERROR_CLASS=timeout. Exit 1.
        Unknown → Telegram with first 200 chars of stderr for triage.
      Fix: (1) Create unified-trading-pm/scripts/claude-helpers.sh:
          Function classify_claude_error(stderr_file, tier, repo, branch):
            - Grep stderr for "401"/"403"/"unauthorized", "429"/"529"/"rate",
              "503"/"unavailable"/"connection refused", to set CLAUDE_ERROR_CLASS.
            - Export CLAUDE_ERROR_CLASS + CLAUDE_ERROR_MSG.
            - Send typed Telegram alert (emoji + class + tier + repo + branch).
            - Return 0 on service_down; 1 on auth_error; 2 on rate_limited.
      (2) Create composite action .github/actions/handle-claude-api-error/action.yml:
          Inputs: stderr_path, tier (cicd|syshealth|analysis), agent_name.
          Calls classify_claude_error; outputs error_type + should_retry + retry_delay_s.
      (3) Source claude-helpers.sh in all CICD and SYSHEALTH agent workflows.
          agent-audit.yml retry loop already exists — just classify before re-dispatch.
      (4) conflict-resolution-agent.yml already has timeout-minutes: 30;
          add 'if: failure()' final step calling classify_claude_error with
          CLAUDE_ERROR_CLASS=timeout.
      Test: run workflow with invalid key (wrong last char) — verify exactly one Telegram "Auth error — cicd key needs
      rotation" fires, job exits, no retry.
    status: done

  - id: add-claude-api-health-preflight
    content: >
      Agents begin cloning repos and installing Claude CLI before discovering the API is unreachable — wasting 3-5 min
      per job and producing uninformative failures. Two-layer fix:

      Layer A — Per-agent pre-flight (first step in every agent workflow):
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY_CICD || secrets.ANTHROPIC_API_KEY }}
        run: |
          timeout 30 claude --print "ping: respond with OK" 2>preflight_err.txt \
            | grep -qi "ok" && echo "Claude API: healthy" \
            || { source unified-trading-pm/scripts/claude-helpers.sh
                 classify_claude_error preflight_err.txt cicd $(basename $PWD) preflight
                 exit $?; }
        On service_down (exit 0): skip gracefully, no pipeline failure.
        On key_invalid (exit 1): alert + fail job so key rotation is visible.
        Overnight orchestrator: runs health check ONCE before dispatching T0
        to prevent 65 agent-audit.yml jobs all failing silently. On failure:
        Telegram "Overnight audit SKIPPED — Claude unreachable at <UTC>.
        Next cron: 01:00 UTC. No T0-T3 runs fired." and exit 0.

      Layer B — Dedicated health monitor cron (state-transition alerts only):
        File: .github/workflows/claude-api-health-monitor.yml
        Schedule: "*/15 * * * *"  (every 15 min, uses ANTHROPIC_API_KEY_SYSHEALTH)
        timeout-minutes: 2
        Logic:
          - Run 30s preflight ping.
          - Read previous state from GH Actions cache key "claude-health-state".
          - If state CHANGED (healthy→degraded or degraded→healthy): send Telegram.
            "Claude API degraded at 14:30 UTC — 429 on SYSHEALTH key." or
            "Claude API recovered at 14:45 UTC."
          - Do NOT send Telegram if state unchanged (no spam every 15 min).
          - Write new state to cache.
        This gives proactive alerting BEFORE the overnight cron fires.
        Also covers: can Claude itself be pinged to check for issues? Yes —
        this workflow IS that check, running independently of all agent work.
      Diagram: api_health_preflight + tg_api_key_failure nodes already added (2026-03-13). Annotations updated to show
      tier key assignments. Acceptance: Anthropic incident → no agent wastes >30s, clear Telegram fires once, all
      SYSHEALTH skips gracefully, CICD agents unaffected.
    status: done

  # ── Plan-driven agent context (new governance model) ─────────────────────
  # Two human gates. Everything else automated. No agent bypasses these gates.
  # Gate 1: /approve-plan — before implementation starts (ENFORCED, not advisory)
  # Gate 2: /approve-merge — before code lands

  - id: add-conflict-plan-context
    content: >
      conflict-resolution-agent.yml currently reads AGENTS.md + plans in its prompt. Strengthen this to ensure plans are
      the PRIMARY context: (1) In the agent prompt, add explicit instruction: "Read ALL files in
          active plans/ directory. The active plans define WHAT should be
          implemented and WHY. When resolving a conflict, determine which
          resolution is consistent with the relevant active plan's intent.
          If the conflict touches a planned feature, preserve the plan's
          design. Reference the plan in your PR description."
      (2) Clone PM repo in agent workflow (already done), ensure
          plans/active/*.plan.md are read in the prompt construction step.
      (3) Add plan context to the PR body template: "Resolution guided by
          plan: [plan-name] §[relevant-todo-id]"
      (4) Before opening a resolution PR, check if a resolution branch already exists (see add-conflict-agent-dedup).
      This is the core of plan-driven conflict resolution — the plan is the tie-breaker when two changes conflict.
    status: done

  - id: add-tg-plan-approval-gate
    content: >
      Currently there is no Telegram notification when a new plan is created or updated in PM active plans/. Human
      review of plans happens out-of-band. Fix: add a new step to rules-alignment-agent.yml or create a separate
      plan-notification.yml that fires when plans/active/*.plan.md changes: (1) Trigger: push to PM main touching
      plans/active/*.plan.md. (2) Read the changed plan file, extract name + overview + first 3 todos. (3) Send
      Telegram: "Plan ready for review: [plan-name]\n
          Overview: [first 200 chars]\nTodos: [count] pending\n
          Review: [link to file on GitHub]\nApprove with: /approve-plan [name]"
      (4) Human replies /approve-plan [name] → plan-approval.yml marks plan
          status: approved in frontmatter. Agents check status: approved before
          implementing plan todos.
      ENFORCEMENT (not advisory): (5) Plans start as status: active (not approved). All agent workflows that implement
          plan todos MUST check plan status before acting:
            grep -q 'status: approved' plan.md || { echo "Plan not approved — skipping"; exit 0; }
          Affected: conflict-resolution-agent.yml, rules-alignment-agent.yml (implementation steps only — notification
          steps still fire on active plans so the human gets the review request).
      (6) Alternative (stronger): plans start as status: draft. The PM push trigger for agent cascades only fires
          if at least one plan has status: approved. Draft plans are invisible to implementation agents.
      This closes the governance loop: no agent starts implementing until human has explicitly reviewed the plan.
    status: done

  - id: add-tg-merge-approval-gate
    content: >
      Second human gate: all agent-opened PRs currently can auto-merge once quality gates pass. For conflict resolution
      PRs, humans must review. But for other agent PRs (codex sync, rules alignment, semver bumps) there is no explicit
      approval gate. Fix: (1) For conflict-resolution PRs: tg_conflict_done already fires with PR
          URL. Explicitly note in the Telegram message: "PR will NOT auto-merge.
          Review and approve in GitHub."
      (2) For other agent PRs (codex-sync-agent, rules-alignment-agent): add a
          Telegram message on PR creation: "Agent PR opened: [title]\n
          [PR URL]\nApprove merge with: /approve-merge [PR#]"
      (3) Implement /approve-merge handler (PR comment workflow) that sets
          auto-merge on the PR when human sends this.
      (4) AUTHORIZATION: /approve-merge handler must validate commenter:
          if: contains(fromJSON('["IggyIkenna"]'), github.event.comment.user.login)
          Same authorized approvers list as add-major-bump-approval-handler.
      Net effect: two mandatory human touchpoints for any agent-driven change:
        Gate 1: /approve-plan [name] — before implementation starts
        Gate 2: review PR in GitHub or /approve-merge [PR#] — before code lands
    status: done

  # ── Human-readable versioning (semver is the headline, SHA is metadata) ──
  # Principle: every human-facing surface — Telegram, deployment UI, manifest
  # history, GH Issues — leads with version + branch context. SHAs are always
  # available one click deeper but never the primary identifier.

  - id: enrich-staging-commits-with-semver
    content: >
      staging_commits and main_commits currently store raw SHAs only — not human-readable. Nobody can glance at the
      manifest and know what version was tested or promoted without cross-referencing staging_versions. Fix: (1) Change
      staging_commits structure from:
          "staging_commits": {"execution-service": "4c0f38a..."}
        to:
          "staging_commits": {
            "execution-service": {
              "version": "0.1.23",
              "sha": "4c0f38adef...",
              "branch": "feat/defi-rollout"
            }
          }
      (2) Change main_commits.history entries from:
          {"promoted_at": "...", "commits": {"repo": "sha"}}
        to:
          {"promoted_at": "...", "promotions": {
            "execution-service": {
              "from": "0.1.22",
              "to": "0.1.23",
              "sha": "4c0f38a...",
              "branch": "feat/defi-rollout"
            }
          }}
        This makes every promotion record immediately readable: "execution-service went from 0.1.22 to 0.1.23 via
        feat/defi-rollout at 08:45 UTC."
      (3) Update all workflows that read/write staging_commits and main_commits:
          sit-gate.yml (writes staging_commits), staging-to-main.yml (reads staging_commits, writes main_commits),
          sit-unlock.yml (clears staging_commits).
      (4) Update validate-manifest-json.sh to validate new structure. Acceptance: git log of workspace-manifest.json is
      human-readable without SHA cross-referencing.
    status: pending

  - id: enrich-telegram-with-versions
    content: >
      Telegram messages currently show tier-level pass/fail (overnight), "SIT running" (lock), or repo+branch
      (conflicts) — but never the VERSION being tested, promoted, or failing. Operators must check GHA logs to know
      which version broke. Fix: (1) Overnight summary — change from:
          "T0 (libraries): success"
        to:
          "T0 (libraries): success
           unified-trading-library v0.2.1
           unified-config-interface v0.1.56"
          Include version for every repo tested, with pass/fail indicator per repo.
      (2) SIT lock alert — change from:
          "SIT locked: staging under test"
        to:
          "SIT locked: testing execution-service v0.1.23 + 2 deps"
      (3) Conflict alert — change from:
          "Conflict detected: $REPO staging→main"
        to:
          "Conflict detected: $REPO v$STAGING_VERSION → main (v$MAIN_VERSION)"
      (4) SIT failure — change from:
          "SIT failed — staging unlocked"
        to:
          "SIT failed: execution-service v0.1.23 — staging unlocked, revert needed"
      (5) Promotion — add new message:
          "Promoted to main: execution-service v0.1.22 → v0.1.23 (feat/defi-rollout)"
      Source version from enriched staging_commits (see enrich-staging-commits-with-semver). Acceptance: every Telegram
      message includes human-readable semver, never raw SHAs.
    status: pending

  - id: populate-deployed-versions
    content: >
      The manifest has deployed_versions: {dev: {}, staging: {}, prod: {}} but it is NEVER populated. Cloud Build pushes
      images but never writes back which version is actually running where. The deployment UI cannot show "what's
      running in prod right now" from the manifest — it has to query Artifact Registry directly. Fix: (1) In
      cloud-build-router.yml, after Cloud Build succeeds (poll returns SUCCESS), write back to manifest:
          "deployed_versions": {
            "$ENV": {
              "$REPO": {
                "version": "$VERSION",
                "image_tag": "$IMAGE_TAG",
                "deployed_at": "2026-03-13T09:00:00Z",
                "build_id": "$BUILD_ID"
              }
            }
          }
          Commit with [skip ci] to avoid triggering cascades.
      (2) In deployment-service/monitor.py: read deployed_versions from manifest as secondary source,
          with Cloud Run / Artifact Registry as primary (for live state).
      (3) In deployment-ui BuildSelector: show deployed_versions per env with visual badges (see
          deployment-ui-multi-env-selector).
      Acceptance: manifest always reflects what is deployed where, with semver tags (not SHAs).
    status: pending

  - id: deployment-ui-multi-env-selector
    content: >
      BuildSelector.tsx currently reads only manifest.versions (main/prod). Operators cannot see or select staging or
      feature branch versions from the deployment UI — they must know the exact image tag. Fix: (1) Extend BuildSelector
      to read from three sources:
          - manifest.versions (main/prod) — green badge
          - manifest.staging_versions (staging) — yellow badge
          - manifest.deployed_versions.dev (feature branches) — blue badge
          Dropdown groups: "Production (main)" | "Staging (under test)" | "Development (feature branches)"
      (2) Each entry shows: "$REPO v$VERSION ($BRANCH)" with environment badge.
          Example: "execution-service v0.1.23-staging (staging)" [yellow]
          Example: "execution-service v0.1.23-feat-defi-rollout (dev)" [blue]
      (3) DeploymentHistory.tsx: add "from_version" column alongside existing "tag" column.
          Show: "v0.1.22 → v0.1.23" instead of just "0.1.23".
      (4) ServiceVersion in deployment-service/monitor.py already has image_tag (semver) + git_commit (SHA).
          Surface both in API response, but UI shows only semver by default with SHA as tooltip/expandable detail.
      Acceptance: operator can see all versions across all environments in one dropdown, select any for deployment, and
      never needs to type or remember a SHA.
    status: pending

  - id: human-readable-deployment-id
    content: >
      DeploymentState.deployment_id is currently a generated UUID — not human-readable. When operators discuss
      deployments ("roll back deploy abc123"), nobody knows what abc123 refers to without looking it up. Fix: (1) Change
      deployment_id format to:
          deploy-{service}-{version}-{env}-{sequence}
          Example: deploy-execution-service-0.1.23-prod-1
          If someone retries: deploy-execution-service-0.1.23-prod-2
          The sequence number makes retries visible and distinguishable without reading UUIDs.
      (2) In deployment-service, update deployment_id generation:
          Generate sequence by counting existing deployments for same service+version+env in GCS.
      (3) In DeploymentHistory.tsx, deployment_id is now directly meaningful — no tooltip or lookup needed. (4) Telegram
      deploy notifications use this ID: "Deployed: deploy-execution-service-0.1.23-prod-1" (5) GCS path becomes:
      gs://{bucket}/deployments/deploy-execution-service-0.1.23-prod-1/state.json
          (still unique, but human-navigable in GCS console).
      Acceptance: every deployment ID is self-describing — service, version, environment, and retry count visible at a
      glance.
    status: pending

  - id: enforce-branch-slug-convention
    content: >
      Cloud Build tags use {semver}-{branch-slug} for Docker images, but branch names are free-form. Long or
      special-character branch names produce unreadable image tags (e.g., 0.1.23-feat-my-cool-thing-that-is-really-
      long-and-has-special-chars). Fix: (1) In quickmerge.sh, validate feature branch names before creating PRs:
          BRANCH_SLUG=$(echo "$BRANCH" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g' | cut -c1-30)
          If original != slug: warn "Branch name will be slugified to: $BRANCH_SLUG"
      (2) Document convention in docs/repo-management/branch-naming.md:
          - Max 30 chars after feat/ or fix/ prefix
          - Lowercase alphanumeric + hyphens only
          - Examples: feat/defi-rollout, fix/auth-timeout, chore/deps-update
      (3) In cloud-build-router.yml, apply the same slugification to IMAGE_TAG construction
          (defensive — even if branch name is long, tag stays readable).
      Acceptance: all Docker image tags are human-readable and under 50 chars total.
    status: pending

  # ── Testing ──────────────────────────────────────────────────────────────
  # Split into fast path (scripted, deterministic, no external deps) and
  # slow path (AI-gated, external services, run in overnight or manual only).

  - id: test-p0-remediation
    content: >
      E2E test each P0 fix using admin sync scripts or workflow_dispatch: (a) Rollback: Force a SIT failure using admin
      script (push known-bad commit to staging). Verify GH Issue opened WITH SEMVER in title. Verify staging unlocked.
      (b) Cascade cycle: Edit workspace-manifest.json on a test branch to add
          a cycle (repo A → B → A). Run validate-manifest-dag.py, verify it
          exits non-zero with cycle description.
      (c) SHA pinning: Push a [skip ci] constraint commit during a running SIT
          (using admin merge script). Verify staging_commits captures the full
          SHA set including the constraint commit, or that promotion is deferred.
      (d) Semver trigger: After fix, push feat: to a T2 staging. Verify version
          bump fires on staging push, not on subsequent main push. Verify only
          one bump (not two).
      (e) Manifest concurrency: Run sit-gate.yml and staging-to-main.yml via workflow_dispatch simultaneously.
          Verify serialization via concurrency group — no lost writes.
      (f) Heredoc exit: On test branch, introduce a deliberate KeyError in sit-gate.yml heredoc.
          Verify workflow fails immediately, manifest is not committed corrupted.
      (g) Dispatch retry: Temporarily disable webhook on a test repo. Verify dispatch_with_retry fires 3x,
          then Telegram alert.
      (h) Conflict retry-promotion: Create merge conflict, let agent resolve, merge resolution PR.
          Verify staging-to-main retriggers automatically.
      Acceptance: all 8 scenarios behave correctly with no manual recovery needed.
    status: pending

  - id: test-plan-cascade
    content: >
      Split into FAST PATH (scripted, deterministic) and SLOW PATH (AI-gated, external deps).

      FAST PATH (run in PR CI — no external deps): (1) Validate plan YAML structure: frontmatter has name, overview,
      status, todos. (2) Validate manifest DAG: no cycles, all repos referenced exist. (3) Validate dispatch payloads:
      mock dispatch_with_retry, verify correct event_type + payload shape. (4) Validate Telegram message format:
      template renders with version, not SHA. (5) Validate staging_commits enriched structure: version + sha + branch
      present. (6) Validate deployment_id format: matches deploy-{service}-{version}-{env}-{seq} pattern.

      SLOW PATH (run in overnight orchestrator or manual workflow_dispatch — requires Claude API + GitHub + Telegram):
      (1) Create a new test plan in plans/active/ (minimal, 1 todo). (2) Verify: push to PM main → manifest-sync fires →
      codex updated. (3) Verify: rules-alignment-agent fires → cursor rule created for the new plan constraint. (4)
      Verify: Telegram plan-ready notification received with correct content. (5) Send /approve-plan [test-plan-name]
      via Telegram → verify plan frontmatter updated to status: approved. (6) Create a deliberate merge conflict in a
      test repo. (7) Verify: conflict-resolution-agent fires, reads active plans, references the test plan in its
      resolution
          PR body.
      (8) Verify: tg_merge_ready notification fires with PR URL. (9) Send /approve-merge [PR#] → verify PR auto-merges.
      Acceptance: fast path runs in <30s with zero external deps. Slow path works end-to-end with exactly two human TG
      actions.
    status: pending

  - id: test-version-readability
    content: >
      Verify human-readable versioning end-to-end: (1) Push a feat: commit to staging → verify staging_commits has
      {version, sha, branch} structure. (2) Trigger SIT → verify Telegram lock message includes "v$VERSION" not raw SHA.
      (3) SIT passes → verify Telegram promotion message shows "v0.1.22 → v0.1.23 (feat/branch)". (4) Cloud Build
      succeeds → verify deployed_versions in manifest is populated with semver. (5) Open deployment UI → verify
      BuildSelector shows all 3 environments with badges. (6) Verify deployment_id format:
      deploy-{service}-{version}-{env}-{seq}. (7) Verify Docker image tag is under 50 chars and human-readable. (8)
      Verify main_commits.history entry has from/to versions, not just SHAs. Acceptance: a non-engineer can read every
      version surface and understand what version is where.
    status: pending

  - id: register-ssot-index
    content: >
      Add this plan to unified-trading-codex/00-SSOT-INDEX.md in the Plans section (after cicd_e2e_test_plan_2026_03_13
      row). Entry format: | cicd_audit_remediation_2026_03_13.plan.md | CI/CD audit P0/P1/P2 remediation + plan-driven
      governance + human-readable versioning | unified-trading-pm/plans/active/ |
    status: done

isProject: false
---

# CI/CD Pipeline Audit Remediation

**Context:** Full audit performed 2026-03-13 against the live pipeline implementation. 22 original issues found across
P0/P1/P2. Secondary audit identified 14 additional race conditions, silent failure vectors, and governance enforcement
gaps. Versioning audit identified 6 human-readability gaps. Total: 42 issues across 35 todos.

## Design Principles

1. **Semver is the headline, SHA is metadata.** Every human-facing surface — Telegram, deployment UI, manifest history,
   GH Issues — leads with version + branch context. SHAs are one click deeper, never the primary identifier.
2. **Two human gates, everything else automated.** Gate 1: /approve-plan (before implementation). Gate 2: /approve-merge
   (before code lands). No agent bypasses these gates. Gates are ENFORCED, not advisory.
3. **No silent failures.** Every dispatch is retried. Every heredoc propagates errors. Every manifest mutation is
   validated. Every timeout fires an alert with version context.
4. **No race conditions.** Single concurrency group for all manifest mutations. Idempotency guards on all retriggerable
   workflows. Debounce starvation cap prevents liveness failures.
5. **Fast path and slow path.** Scripted validation (deterministic, no external deps, <30s) runs in PR CI. AI-gated E2E
   tests (Claude API, GitHub, Telegram) run in overnight orchestrator or manual trigger only.

## Governance Model (the central insight)

The pipeline's correctness depends on agents having the RIGHT context. That context is the **active plans**:

```
Plan created (human or agent)
  → codex-sync-agent updates unified-trading-codex (source of truth)
  → rules-alignment-agent creates cursor rules from plan constraints
  → Telegram: "Plan ready for review: [name] v[version]" [Gate 1: human approves plan]
  → Agent reads: active plans + codex + AGENTS.md + cursor rules
  → Agent implements → opens PR
  → Telegram: "Agent PR ready: [repo] v[version]" [Gate 2: human approves merge]
  → PR merges → staging → SIT → main
  → Telegram: "Promoted: [repo] v0.1.22 → v0.1.23 (feat/branch)"
```

**Only two human actions in the entire flow:** approve plan + approve merge. Everything else is automated, but nothing
agent-driven bypasses these gates.

## Audit Findings Summary

| Priority                           | Count | Status                      |
| ---------------------------------- | ----- | --------------------------- |
| P0 (race conditions & correctness) | 12    | all pending                 |
| P1 (silent failures & idempotency) | 6     | all pending                 |
| P2 (governance enforcement)        | 3     | all pending                 |
| Human-readable versioning          | 6     | all pending                 |
| Diagram SSOT                       | 5     | immediate (unblocked)       |
| Testing                            | 3     | fast path + slow path split |

See full audit in session notes (2026-03-13). Top risk: workspace-manifest.json as a git-committed distributed state
store — concurrent writes create race conditions. Mitigated by: unified concurrency group (unify-manifest-concurrency-
groups), JSON validation after every write (add-manifest-json-validation), and heredoc exit propagation
(fix-heredoc-exit-propagation).

## Version Readability Guarantee

After the versioning todos are complete, the following is guaranteed at every layer:

| Layer                      | Before                         | After                                                               |
| -------------------------- | ------------------------------ | ------------------------------------------------------------------- |
| Manifest staging_commits   | `{"repo": "sha"}`              | `{"repo": {"version": "0.1.23", "sha": "...", "branch": "feat/x"}}` |
| Manifest main_commits      | `{"commits": {"repo": "sha"}}` | `{"promotions": {"repo": {"from": "0.1.22", "to": "0.1.23", ...}}}` |
| Manifest deployed_versions | `{}` (empty)                   | `{"prod": {"repo": {"version": "0.1.22", "deployed_at": "..."}}}`   |
| Telegram alerts            | Tier pass/fail, no version     | Per-repo semver in every message                                    |
| Deployment UI dropdown     | Main versions only             | Main + staging + dev with color badges                              |
| Deployment ID              | UUID                           | `deploy-execution-service-0.1.23-prod-1`                            |
| Docker image tags          | Possibly long/unreadable       | Max 50 chars, slugified branch names                                |

## Diagram Auto-Regeneration

After `diagram-regen-in-quickmerge` is complete, the following is guaranteed:

- `cicd-pipeline-definition.yaml` = canonical SSOT (human-edited)
- `CI-CD-PIPELINE.svg` + `CI-CD-PIPELINE.html` = generated, never hand-edited
- Regeneration happens on every PM `quickmerge` pass that changes `.yaml` or `.py`
- The diagram is therefore always in sync with the documented pipeline

## References

- `plans/active/cicd_e2e_test_plan_2026_03_13.plan.md` — test plan for all fixes
- `plans/active/conflict_resolution_agent_2026_03_13.plan.md` — agent implementation
- `plans/active/full_autonomous_agent_ci.plan.md` — semver-agent fix (dependency)
- `docs/repo-management/cicd-pipeline-definition.yaml` — diagram SSOT
- `scripts/generate-cicd-diagram.py` — diagram generator
- `docs/repo-management/CI-CD-PIPELINE.html` — live interactive diagram
