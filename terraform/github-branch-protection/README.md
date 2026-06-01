# GitHub branch-protection rulesets — IaC

Codifies the two managed **rulesets** per UTS repo so they stop drifting when Quality Gates workflows are renamed:

- `require-quality-gates` → main (`~DEFAULT_BRANCH`), requires `Quality Gates (<repo>) / <suffix>`
- `require-staging-lock-check` → `staging`, requires that same QG context **plus** `check-staging-lock`

`<suffix>` is `quality-gates-v2` (repos on `quality-gates-v2.yml`) or `quality-gates` (repos still on
`workspace-qg.yml`). When a repo migrates workflows, flip its entry in `local.repo_qg_suffix` in `main.tf` and
`terraform apply`.

Scope: these are GitHub **rulesets**, distinct from the legacy _classic_ branch protection
(`scripts/propagation/apply-branch-protection.sh`, `scripts/repo-management/set-branch-protection.sh`).

History / contract: `../../plans/active/issues/ci_v2_ruleset_check_name_drift_2026_05_30.md`.

## ⚠️ One SSOT only

Two ways to manage these rulesets — pick exactly one:

1. **Script (in use as of 2026-05-30):** `scripts/repo-management/pin_branch_protection_rulesets.py`. Derives the QG
   context from each repo's live workflow file automatically — no manual suffix map. Run it post-migration to re-pin.
2. **This Terraform.** Declarative + reviewable, but the suffix map is manual.

**Do not run both** against the same rulesets — they will fight and drift. This module is the IaC option; adopting it
means retiring the script as SSOT (and vice-versa).

## Adopting this module (one-time)

The rulesets already exist (created via API). Import them first so `apply` does not recreate them (recreation briefly
removes branch protection):

```bash
cd terraform/github-branch-protection
export GITHUB_TOKEN=...      # admin on the org repos
export GITHUB_OWNER=IggyIkenna
terraform init
bash import.sh | sh          # import all existing rulesets into state
terraform plan               # expect NO creates/destroys — only intended diffs
terraform apply
```

## Verifying (works regardless of which SSOT you use)

```bash
python3 ../../scripts/repo-management/verify_branch_protection_check_names.py
# -> ALL RULESETS CONSISTENT: True
```

## Status

Authored 2026-05-30 to the `integrations/github` v6 provider schema. **Not** run through `terraform validate` on the
authoring host (no terraform binary available) — run `terraform init && terraform validate` before adopting.
