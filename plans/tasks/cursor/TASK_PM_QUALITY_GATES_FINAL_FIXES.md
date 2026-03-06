# Task: PM Quality Gates — Final Fixes (Agent Instructions)

**Workspace root**: /Users/ikennaigboaka/Code/unified-trading-system-repos

---

## Edit Rules (MANDATORY)

- **Use sed, cat, or python3 -c / python3 << 'PYEOF' for ALL edits.** Inline edit tools do not work.
- **Proper fixes only.** No bypass audit, no relaxing quality gates, no skipping checks.
- **Verify**: Run ruff check and basedpyright on changed files before claiming done.

---

## Already Fixed (do not redo)

| Item                         | File(s)                                                     | Status                                                                  |
| ---------------------------- | ----------------------------------------------------------- | ----------------------------------------------------------------------- | ---------------- | ------------- | --- | --- |
|                              |                                                             | true bypass                                                             | quality-gates.sh | Replaced with |     | :   |
| check-codex-violations split | utilities/lib/codex_violations.py                           | Split from monolithic script                                            |
| E501 line length             | check-codex-violations.py                                   | Docstring, add_argument, results.append, \_write_output_json            |
| F821 undefined names         | 04-create-service-epics.py                                  | 6 _build_\* helpers added                                               |
| Imports                      | 04-create-service-epics.py, epic_loaders.py, epic_models.py | Epic, Task, Subtask, loaders, ServiceDict, **all**                      |
| check-internal-advisories    | imports, empty fallbacks                                    | Fixed                                                                   |
| find-coding-violations       | naive datetime, bare except, deep imports                   | Patterns in JSON                                                        |
| sbom-store                   | GCP_PROJECT_ID, os.environ                                  | argparse                                                                |
| rollout-quality-gate-checks  | GCP literal                                                 | Built at runtime                                                        |
| 02-run-diff-checker          | function size                                               | create_github_issue, main split                                         |
| rd-tax-credits export-script | function size                                               | export_helpers                                                          |
| diff_checkers                | cast, subprocess                                            | Imports added                                                           |
| generate-per-service-specs   | file size 916L                                              | Extracted spec*logging.py (Colors, log*\*) to utilities/spec_logging.py |

| 03-check-service-compliance | function size | main split into _parse_compliance_args, \_resolve_services_to_check, \_print_compliance_summary, \_create_issues_from_gaps |
| track-metrics | function size | format_markdown_report split into 9 helpers |
| 00-setup-cod-project | function size | main split into \_parse_setup_args, \_validate_mode, \_resolve_repos, \_run_setup_steps, \_print_completion |
| 3x 02-create-issues | function size | create_issues split into \_build_issue_specs, \_find_existing_issue, \_create_single_issue_on_github, \_process_single_issue |
| codex_violations | function size | find_coding_standards_violations split into 8 \_check\_\_ helpers |
| generate-simple-violation-manifests | function size | generate*manifest split into 6 \_build*_ helpers |
| parse-agent-logs | function size | parse*stream split into \_parse_stream_header, \_extract_events, \_handle*_, *dispatch_event |
| create-all-projects | function size | main split into \_parse_args, \_validate_args, \_resolve_projects_to_create, \_create_projects_loop, \_print_summary |
| generate-per-service-specs | function size | generate_domain_spec, generate_observability_spec, generate_infrastructure_spec split into \_extract*_ + _build_\* |
| generate-issues-from-classifications | method size | \_create_issue split into \_build_issue_body, \_build_issue_labels |

---

## If Quality Gates Still Fail

1. Run bash scripts/quality-gates.sh --no-fix in unified-trading-pm.
2. Fix only the reported errors (ruff, basedpyright, tests).
3. Use sed/cat/python3 for edits — never inline edit tools.
4. Re-run quality gates to verify.

---

## Quick Verification

cd unified-trading-pm && source ../.venv-workspace/bin/activate
ruff check github-integration/scripts/core/ github-integration/scripts/projects/
basedpyright github-integration/scripts/core/04-create-service-epics.py
