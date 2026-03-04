# GitHub Projects Directory

This directory contains organized scripts and documentation for each GitHub Project.

## Structure

Each project has its own subdirectory with a complete set of scripts:

```
projects/
├── unified-libraries-refactor/    # Project #3
│   ├── 01-create-project.sh
│   ├── 02-create-issues.py
│   ├── 03-link-issues-to-project.sh
│   ├── 04-copy-workflows.sh
│   ├── 05-verify-setup.sh
│   ├── 06-generate-project-readme.sh
│   └── README.md
│
├── initial-cleanup/                # Project #5
│   ├── utilities/
│   │   └── check-codex-violations.py  # Violation checker (from core/02-run-diff-checker.py)
│   ├── 01-create-project.sh
│   ├── 02-create-issues.sh
│   ├── 03-link-issues-to-project.sh
│   ├── 04-run-batch-fix.sh
│   ├── 05-verify-completion.sh
│   ├── 06-generate-manifests.py       # Manifest generator (from one-time/)
│   ├── AGENT_PROMPT.md
│   ├── WORKFLOW.md
│   └── README.md
│
└── README.md                       # This file
```

## Benefits

1. **Organization**: All project scripts in one place
2. **Isolation**: Project-specific logic doesn't conflict
3. **Discovery**: Easy to find relevant scripts for a project
4. **Templates**: Copy structure for new projects
5. **Agent-friendly**: Clear prompts + workflows per project

## Active Projects

### Project #3: Unified Libraries Refactor

**Goal:** Extract shared code into unified libraries
**Status:** Planning
**Directory:** `unified-libraries-refactor/`

### Project #5: Initial Cleanup

**Goal:** Fix all codex violations across 13 repos
**Status:** In Progress (11 open, 2 closed)
**Directory:** `initial-cleanup/`

## Creating New Projects

Follow the structure:

1. Create directory: `mkdir -p projects/[project-name]/`
2. Add scripts:
   - `01-create-project.sh` - Create GitHub Project
   - `02-create-issues.sh` - Create issues
   - `03-link-issues-to-project.sh` - Link issues
   - `04-run-*.sh` - Execution script
   - `05-verify-*.sh` - Verification script
   - `AGENT_PROMPT.md` - Quick prompt for agents
   - `WORKFLOW.md` - Detailed workflow
   - `README.md` - Project overview
3. Reference core scripts in `../automation/` for reusable logic

## Core Automation Scripts

Reusable scripts used by multiple projects:

- `automation/batch-fix-v2.sh` - Core batch automation engine
- `automation/run-cleanup-batch-fix.sh` - Cleanup-specific wrapper
- `utilities/copy-project-workflows.sh` - Copy workflows between projects
- `core/01-manage-cods.sh` - COD management utilities
- `core/02-run-diff-checker.py` - Codex violation scanner

## Related Directories

- `../automation/` - Reusable batch automation scripts
- `../utilities/` - General utilities
- `../core/` - Core GitHub integration scripts (being phased out - scripts moving to projects)
  - `05-check-file-size-cods.py` - Will move to COD-SIZE project when created
- `../one-time/` - One-time migration scripts (being phased out - scripts moved to projects)
