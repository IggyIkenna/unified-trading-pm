# Plan Dependency Map

This document tracks dependencies between active plans. Use `check-plan-gate.sh` to verify that prerequisite phases are
complete before starting dependent work.

## Dependency Graph

```
live-defi-rollout
  └── depends_on: contract-adoption (phase1- items)
  └── depends_on: coverage-remediation (phase1- items)

coverage-remediation
  └── depends_on: (none — standalone)

contract-adoption
  └── depends_on: (none — standalone)

overnight-hardening (this task)
  └── depends_on: (none — standalone)
```

## Gate Check Commands

```bash
# Check if phase1 of a plan is complete before starting phase2 work
bash scripts/agents/check-plan-gate.sh plans/active/some-plan.md "phase1-"

# Check all items in a plan
bash scripts/agents/check-plan-gate.sh plans/active/some-plan.md ""
```

## Adding Dependencies

When a plan has a `depends_on` field in its YAML frontmatter, the depended-upon plan's relevant gate prefix must pass
`check-plan-gate.sh` before the dependent plan can begin that phase.

Workflows can enforce this by adding a step:

```yaml
- name: Check prerequisite plan gate
  run: |
    bash scripts/agents/check-plan-gate.sh \
      plans/active/prerequisite-plan.md \
      "phase1-"
```
