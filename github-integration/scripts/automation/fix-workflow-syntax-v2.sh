#!/usr/bin/env bash
#
# Fix duplicate run: keys in quality-gates.yml workflows
#
# The issue: A step has TWO run: blocks, which is invalid YAML
# Solution: Split into two separate steps
#
# Usage: bash fix-workflow-syntax-v2.sh <repo-path>

set -uo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <repo-path>"
  exit 1
fi

REPO_PATH="$1"
WORKFLOW_FILE="$REPO_PATH/.github/workflows/quality-gates.yml"

if [ ! -f "$WORKFLOW_FILE" ]; then
  echo "❌ No workflow file: $WORKFLOW_FILE"
  exit 1
fi

echo "🔧 Fixing: $(basename "$REPO_PATH")"

# Use Python to properly split the duplicate run: blocks
python3 - "$WORKFLOW_FILE" <<'PYTHON_EOF'
import sys
import re

workflow_file = sys.argv[1]

with open(workflow_file, 'r') as f:
    lines = f.readlines()

fixed_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    fixed_lines.append(line)

    # Check if this line is a step with a run: block
    if line.strip().startswith('- name:') and 'run:' not in line:
        step_name = line.strip()
        i += 1

        # Collect all lines for this step
        step_lines = []
        indent_level = None
        found_first_run = False

        while i < len(lines):
            curr_line = lines[i]

            # Check if we've hit the next step or section
            if curr_line.strip().startswith('- name:') or (curr_line.strip().startswith('#') and not curr_line.startswith('      #')):
                break

            # Detect first run: block
            if curr_line.strip().startswith('run:'):
                if found_first_run:
                    # This is a DUPLICATE run: block - split into new step
                    print(f"  Found duplicate run: at line {i + 1}, splitting into new step")

                    # Add the collected lines (first run: block)
                    fixed_lines.extend(step_lines)
                    step_lines = []

                    # Create a new step for the duplicate run: block
                    fixed_lines.append('\n')
                    fixed_lines.append('      - name: Install dependencies\n')

                    # Add the duplicate run: block and its content
                    while i < len(lines):
                        dup_line = lines[i]
                        if dup_line.strip() and not dup_line.startswith('        ') and not dup_line.strip().startswith('run:'):
                            break
                        fixed_lines.append(dup_line)
                        i += 1

                    found_first_run = False  # Reset for potential next step
                    break
                else:
                    found_first_run = True

            step_lines.append(curr_line)
            i += 1

        # Add remaining step lines if any
        fixed_lines.extend(step_lines)
        continue

    i += 1

with open(workflow_file, 'w') as f:
    f.writelines(fixed_lines)

print(f"  ✅ Fixed")
PYTHON_EOF

echo "  Done!"
