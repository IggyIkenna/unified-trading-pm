# Agent Cleanup Prompt (Quick Copy-Paste)

## Prompt Template

```
Fix all codex violations for [REPO_NAME] issue #[ISSUE_NUMBER].

INFRASTRUCTURE CONTEXT (READ FIRST):
- Quality gates: @unified-trading-codex/06-coding-standards/quality-gates.md
- Three environments: @unified-trading-codex/11-project-management/github-integration/docs/QUALITY-GATES-ENVIRONMENTS.md
- Dockerfile standards: @unified-trading-codex/06-coding-standards/dockerfile-standards.md
- Dependencies: @unified-trading-codex/06-coding-standards/dependency-management.md

CRITICAL: Ensure unified infrastructure consistency:
- Local: uv pip install -e ../unified-trading-services
- GitHub Actions: uv pip install --system -e deps/unified-trading-services
- Cloud Build: FROM unified-trading-services:latest (already in base image)
- NEVER add unified-trading-services to pyproject.toml dependencies!

WORKFLOW:
1. Pull issue #[ISSUE_NUMBER] from IggyIkenna/[REPO_NAME]
2. Ensure quality gates script is up-to-date (has Check 5: imports inside functions)
   - Verify GitHub Actions uses: bash scripts/quality-gates.sh --no-fix
   - Verify GitHub Actions installs: uv pip install --system -e ../unified-trading-services
   - Verify Dockerfile uses: FROM unified-trading-services:latest
3. Fix all violations listed in the issue:
   - print() → logger.info() (production code only, exclude tests/)
   - os.getenv() → config class extending UnifiedCloudServicesConfig
   - datetime.now() → datetime.now(timezone.utc)
   - bare except → specific exceptions or @handle_api_errors
   - imports inside functions → move to top of file
   - requests → httpx/aiohttp in async code
   - asyncio.run() in loops → asyncio.gather()
   - time.sleep() in async → asyncio.sleep()
4. Run quality gates: bash scripts/quality-gates.sh --no-fix
   - If they fail, check if quality gates script needs updating
   - Update quality gates AND verify three-environment consistency
   - Then fix remaining violations
5. Submit PR: bash scripts/quickmerge.sh "Fix all COD violations for issue #[ISSUE_NUMBER]" --files "[changed files]"
6. Verify PR passes GitHub Actions quality gates
   - If CI fails, check for infrastructure mismatches
   - Update quality gates/GitHub Actions/Dockerfile if needed
   - Fix any test failures

SUCCESS CRITERIA:
- All violations from issue fixed
- Quality gates pass locally AND in CI
- Three-environment consistency (Local, GitHub Actions, Cloud Build)
- PR created with issue number
- Auto-merge enabled
- Issue closes when PR merges

IMPORTANT:
- Use unified-trading-services quality gates as template
- Maintain three-environment consistency at all times
- Never add unified-trading-services to pyproject.toml
- Check if unified-trading-services already has a dependency before adding to service
- If CI fails but local passed: FIX INFRASTRUCTURE, NOT CODE
- Never skip tests or use --no-verify
- Always use quickmerge (never push directly to main)
- Fix quality gates script FIRST if it's outdated
- CI should be exact copy of local environment
```

## Example Usage

### Example 1: execution-service #147

```
Fix all codex violations for execution-service issue #147.

WORKFLOW:
1. Pull issue #147 from IggyIkenna/execution-service
2. Ensure quality gates script is up-to-date (has Check 5: imports inside functions)
3. Fix all violations listed in the issue
4. Run quality gates: bash scripts/quality-gates.sh --no-fix
5. Submit PR: bash scripts/quickmerge.sh "Fix all COD violations for issue #147" --files "[changed files]"
6. Verify PR passes GitHub Actions

Follow the workflow in @AGENT_CLEANUP_WORKFLOW.md for detailed steps.
```

### Example 2: Handling CI Failure (Infrastructure Problem)

```
Scenario: Local quality gates passed, but GitHub Actions failed.

DIAGNOSIS:
- Local: ✅ bash scripts/quality-gates.sh --no-fix → PASS
- CI: ❌ GitHub Actions → FAIL

This is NOT a code problem. This is an infrastructure mismatch.

ACTION:
1. Check CI logs: gh run view --log
2. Identify mismatch (e.g., "unified_trading_services not found")
3. Fix GitHub Actions workflow:
   - Add: uv pip install --system -e ../unified-trading-services
   - Use: python-version-file: 'pyproject.toml'
   - Call: bash scripts/quality-gates.sh --no-fix
4. Commit infrastructure fix (NOT code changes)
5. Wait for CI to pass with infrastructure fix
6. Then commit code changes

NEVER:
- Change code to work around CI issues
- Skip tests to make CI pass
- Downgrade dependencies to make CI pass
- Add test exclusions for CI

FIX THE INFRASTRUCTURE TO MATCH LOCAL, NOT THE OTHER WAY AROUND.
```

### Example 3: instruments-service #58

```
Fix all codex violations for instruments-service issue #58.

WORKFLOW:
1. Pull issue #58 from IggyIkenna/instruments-service
2. Ensure quality gates script is up-to-date (has Check 5: imports inside functions)
3. Fix all violations listed in the issue
4. Run quality gates: bash scripts/quality-gates.sh --no-fix
5. Submit PR: bash scripts/quickmerge.sh "Fix all COD violations for issue #58" --files "[changed files]"
6. Verify PR passes GitHub Actions

Follow the workflow in @AGENT_CLEANUP_WORKFLOW.md for detailed steps.
```

## Quality Gates Update Prompt (If Needed)

```
Update quality gates script for [REPO_NAME] to match unified-trading-services.

STEPS:
1. cd /path/to/[REPO_NAME]
2. Compare: diff scripts/quality-gates.sh ../unified-trading-services/scripts/quality-gates.sh
3. Key updates needed:
   - Add Check 5: Imports inside functions
   - Update check numbering: requests=6, asyncio=7, time.sleep=8
   - Copy heuristic checks for asyncio.run() and time.sleep()
4. Test: bash scripts/quality-gates.sh --no-fix
5. Commit: bash scripts/quickmerge.sh "Update quality gates to match unified-trading-services" --files "scripts/quality-gates.sh"

After this merges, run the cleanup workflow.
```

## Batch Equivalent

This local workflow is equivalent to:

```bash
cd unified-trading-codex/11-project-management/github-integration/scripts/automation

bash enhanced-cleanup-batch-fix.sh \
  --model auto \
  --repos "[REPO_NAME]" \
  --require-labels "cleanup" \
  --state open
```

But run locally with full control and visibility.

## Related Files

- Detailed workflow: `@AGENT_CLEANUP_WORKFLOW.md`
- Coding standards: `@unified-trading-codex/06-coding-standards/README.md`
- Git workflow: `@unified-trading-codex/.cursor/rules/git-workflow.mdc`
