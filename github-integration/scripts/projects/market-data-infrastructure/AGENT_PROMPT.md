tackling # Agent Prompt: Market Data Infrastructure (Quick Copy-Paste)

## Prompt Template

```
Complete subtask for Market Data Infrastructure issue #[ISSUE_NUMBER] in [REPO_NAME].

EPIC CONTEXT (READ FIRST):
- Epic overview: @unified-trading-codex/11-project-management/epics/market-data-infrastructure-epic.md
- Epic breakdown: @unified-trading-codex/11-project-management/epic-breakdowns/epic-market-data-infrastructure.md
- Infrastructure updates: @~/.cursor/plans/infrastructure-updates-for-library-refactor.md
- Backward compatibility: Uses transitive dependencies (services get new libraries automatically)

CRITICAL PRINCIPLES:
- Cloud-agnostic ONLY in unified-trading-services (new libraries use UCS abstractions)
- Backward compatibility via re-exports (6-month window)
- Quality gates must pass in all 3 environments (Local, GitHub Actions, Cloud Build)
- Python 3.13, ruff==0.15.0, uv for all installs
- GCP Artifact Registry for Python packages (NOT GitHub Packages)

WORKFLOW:
1. Pull issue #[ISSUE_NUMBER] from IggyIkenna/[REPO_NAME]
2. Read subtask details from epic breakdown:
   - Description, complexity, priority, risk
   - Files to modify, tests required, blocking tasks
   - Codex references for standards
3. Implement the subtask:
   - Create files/directories as specified
   - Follow codex standards (@unified-trading-codex/06-coding-standards/)
   - Add tests in tests/unit/ or tests/integration/
   - Update dependencies in pyproject.toml (if needed)
   - Run uv lock to update uv.lock (if deps changed)
4. Run quality gates: bash scripts/quality-gates.sh --no-fix
   - If they fail, fix root cause (never skip tests)
   - Ensure three-environment consistency
5. Submit PR: bash scripts/quickmerge.sh "Complete subtask #[ISSUE_NUMBER]: [title]" --files "[changed files]"
   - Include uv.lock if dependencies changed
6. Verify PR passes GitHub Actions quality gates
   - If CI fails but local passed: FIX INFRASTRUCTURE, NOT CODE

SUCCESS CRITERIA:
- Subtask requirements met (per epic breakdown)
- Quality gates pass locally AND in CI
- Tests added/updated and passing
- Documentation updated (if needed)
- PR created with issue number (Closes #[ISSUE_NUMBER])
- Auto-merge enabled
- Issue closes when PR merges

INFRASTRUCTURE NOTES:
- New libraries published to: asia-northeast1-python.pkg.dev/test-project/unified-libraries/
- unified-trading-services lists new libraries as dependencies
- Services get new libraries transitively (no pyproject.toml changes needed)
- Re-exports provide backward compatibility for 6 months

IMPORTANT:
- Use unified-trading-services abstractions for cloud access (never direct GCP/AWS imports in new libraries)
- Maintain cloud-agnosticism (only unified-trading-services touches cloud providers)
- Never skip tests or use --no-verify
- Always use quickmerge (never push directly to main)
- If CI fails but local passed: FIX INFRASTRUCTURE, NOT CODE
- Include uv.lock in PR if dependencies changed
```

## Example Usage

### Example 1: unified-trading-library #3 (Create repo structure)

```
Complete subtask for Market Data Infrastructure issue #3 in unified-trading-library.

WORKFLOW:
1. Pull issue #3 from IggyIkenna/unified-trading-library
2. Read Subtask 1.2.1 from epic breakdown:
   - Create repo structure (src/, tests/, scripts/, pyproject.toml, README.md)
   - Set up Python 3.13, ruff==0.15.0 dev dependencies
   - Add quality-gates.sh and quickmerge.sh scripts
3. Implement repo structure
4. Run quality gates: bash scripts/quality-gates.sh --no-fix
5. Submit PR: bash scripts/quickmerge.sh "Complete subtask #3: Create unified-trading-library repo structure" --files "[all new files]"
6. Verify PR passes GitHub Actions

Follow the workflow in @AGENT_WORKFLOW.md for detailed steps.
```

### Example 2: unified-trading-services #5 (Add PubSub abstraction)

```
Complete subtask for Market Data Infrastructure issue #5 in unified-trading-services.

WORKFLOW:
1. Pull issue #5 from IggyIkenna/unified-trading-services
2. Read Subtask 1.1.2 from epic breakdown:
   - Create unified_trading_services/core/pubsub_abstraction.py
   - Define PubSubClient interface (abstract base class)
   - Implement GCPPubSubClient and AWSPubSubClient
   - Add get_pubsub_client() to client_factory.py
3. Implement PubSub abstraction (see epic breakdown for code structure)
4. Run quality gates: bash scripts/quality-gates.sh --no-fix
5. Submit PR: bash scripts/quickmerge.sh "Complete subtask #5: Add PubSub abstraction" --files "unified_trading_services/core/pubsub_abstraction.py unified_trading_services/core/client_factory.py"
6. Verify PR passes GitHub Actions

Follow the workflow in @AGENT_WORKFLOW.md for detailed steps.
```

### Example 3: unified-config-interface #15 (Migrate config code)

```
Complete subtask for Market Data Infrastructure issue #15 in unified-config-interface.

WORKFLOW:
1. Pull issue #15 from IggyIkenna/unified-config-interface
2. Read Subtask 2.1.3 from epic breakdown:
   - Copy unified_trading_services/core/config.py to unified_config_interface/
   - Update imports to use unified_trading_services abstractions
   - Preserve UnifiedCloudServicesConfig base class
   - Add tests
3. Migrate config code
4. Run quality gates: bash scripts/quality-gates.sh --no-fix
5. Submit PR: bash scripts/quickmerge.sh "Complete subtask #15: Migrate config code from unified-trading-services" --files "unified_config_interface/config.py tests/unit/test_config.py"
6. Verify PR passes GitHub Actions

Follow the workflow in @AGENT_WORKFLOW.md for detailed steps.
```

## Infrastructure Setup (Phase 0 Tasks)

### Example 4: Phase 0 #1 (Create Artifact Registry Python repo)

```
Complete subtask for Market Data Infrastructure issue #1 (infrastructure).

WORKFLOW:
1. Pull issue #1 (infrastructure task)
2. Read Subtask 0.1 from epic breakdown:
   - Create GCP Artifact Registry Python repository "unified-libraries"
   - Location: asia-northeast1
   - Format: python
3. Run gcloud command:
   gcloud artifacts repositories create unified-libraries \
       --repository-format=python \
       --location=asia-northeast1 \
       --description="Unified libraries Python packages" \
       --project=test-project
4. Verify repository exists:
   gcloud artifacts repositories describe unified-libraries \
       --location=asia-northeast1
5. Document in epic breakdown (mark task as complete)

No PR needed for infrastructure tasks - document completion in issue.
```

## Batch Equivalent

This local workflow is equivalent to:

```bash
cd unified-trading-codex/11-project-management/github-integration/scripts/projects/market-data-infrastructure

bash run-batch-fix.sh \
  --model auto \
  --repos "[REPO_NAME]" \
  --project 8 \
  --state open
```

But run locally with full control and visibility.

## Related Files

- Detailed workflow: `@AGENT_WORKFLOW.md`
- Epic overview: `@unified-trading-codex/11-project-management/epics/market-data-infrastructure-epic.md`
- Epic breakdown: `@unified-trading-codex/11-project-management/epic-breakdowns/epic-market-data-infrastructure.md`
- Infrastructure plan: `@~/.cursor/plans/infrastructure-updates-for-library-refactor.md`
- Coding standards: `@unified-trading-codex/06-coding-standards/README.md`
- Git workflow: `@unified-trading-codex/.cursor/rules/git-workflow.mdc`
