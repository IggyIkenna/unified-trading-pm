# Plans Directory

Project planning, task tracking, and execution plans for the Unified Trading System workspace.

## Plan Format

**Format SSOT:** [PLAN_FORMAT.md](PLAN_FORMAT.md). Every plan MUST use Cursor-friendly checkboxes: `- [x]` (done) or
`- [ ]` (pending) at the start of each todo's content so Cursor Plan Mode shows filled vs hollow circles correctly.

## Directory Structure

| Directory            | Contents                                                                                                 |
| -------------------- | -------------------------------------------------------------------------------------------------------- |
| `active/`            | Canonical plans folder (20 plans). `.cursor/plans` symlinks here. See [active/INDEX.md](active/INDEX.md) |
| `staged/`            | Plans queued for activation                                                                              |
| `cicd/`              | CI/CD infrastructure plans, dependency matrix, and quality gates optimization                            |
| `tasks/cursor/`      | Cursor IDE agent task definitions (sub-agent execution plans)                                            |
| `tasks/claude-code/` | Claude Code orchestration tools, parallel execution guides, and agent scripts                            |

## Active Plans (Day 1–2)

Four plans in progress (2 per person). Full index: [active/INDEX.md](active/INDEX.md).

| Plan                         | Notes                         |
| ---------------------------- | ----------------------------- |
| **plans_to_deployable**      | Canonical four-stage pipeline |
| **phase1**                   | Foundation prep               |
| **AWS_MIGRATION**            | Dual-cloud readiness          |
| **SPORTS_MIGRATION_GAP_FIX** | Sports migration gap fix      |
