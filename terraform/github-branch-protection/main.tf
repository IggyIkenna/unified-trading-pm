# GitHub branch-protection RULESETS — IaC codification of the two managed rulesets
# per UTS repo (require-quality-gates on main, require-staging-lock-check on staging).
#
# This is the IaC ALTERNATIVE to scripts/repo-management/pin_branch_protection_rulesets.py.
# Adopt EITHER the script OR this Terraform as the single source of truth — NEVER both
# (dual management guarantees drift). See README.md for adoption + import steps.
#
# Scope note: these are GitHub *rulesets* (repos/{repo}/rulesets), distinct from the
# legacy *classic* branch protection managed by scripts/propagation/apply-branch-protection.sh
# and scripts/repo-management/set-branch-protection.sh.
#
# Required-check contexts follow the rule: a reusable-workflow job records its check-run
# as "<job display name> / <reusable job id>", and the job display name is
# "Quality Gates (<repo>)", so the QG context is:
#   "Quality Gates (<repo>) / <suffix>"
# where <suffix> is "quality-gates-v2" for repos on quality-gates-v2.yml and
# "quality-gates" for repos still on workspace-qg.yml. Flip a repo's suffix here when
# it migrates workflows (the script derives this automatically; in TF it is explicit).

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    github = {
      source  = "integrations/github"
      version = ">= 6.0"
    }
  }
}

# Token via GITHUB_TOKEN env var (needs admin on the org repos).
provider "github" {
  owner = var.github_owner
}

locals {
  # repo => QG reusable-job suffix. ALL repos are on quality-gates-v2.yml now (workspace-qg
  # retired 2026-05-29), so EVERY suffix is "quality-gates-v2" — verified 2026-06-07 against the
  # live `require-quality-gates` rulesets (context = "Quality Gates (<repo>) / quality-gates-v2"
  # fleet-wide). The prior mixed map carried stale "quality-gates" suffixes for 9 repos that, if
  # applied, would set a DEAD context (no run emits it) → dead-lock non-admin merges (M2).
  # As of 2026-05-30 (see plans/active/issues/ci_v2_ruleset_check_name_drift_2026_05_30.md):
  repo_qg_suffix = {
    "alerting-service"                  = "quality-gates-v2"
    "batch-live-reconciliation-service" = "quality-gates-v2"
    "client-reporting-api"              = "quality-gates-v2"
    "deployment-api"                    = "quality-gates-v2"
    "deployment-service"                = "quality-gates-v2"
    "deployment-ui"                     = "quality-gates-v2"
    "execution-service"                 = "quality-gates-v2"
    "ibkr-gateway-infra"                = "quality-gates-v2"
    "instruments-service"               = "quality-gates-v2"
    "market-data-processing-service"    = "quality-gates-v2"
    "market-tick-data-service"          = "quality-gates-v2"
    "strategy-service"                  = "quality-gates-v2"
    "system-integration-tests"          = "quality-gates-v2"
    "trading-agent-service"             = "quality-gates-v2"
    "unified-api-contracts"             = "quality-gates-v2"
    "unified-trading-library"           = "quality-gates-v2"
    "unified-trading-pm"                = "quality-gates-v2"
  }

  qg_context = {
    for repo, suffix in local.repo_qg_suffix :
    repo => "Quality Gates (${repo}) / ${suffix}"
  }

  # Repos that carry a staging ruleset (all except unified-trading-pm, which has none).
  staging_repos = {
    for repo, suffix in local.repo_qg_suffix :
    repo => suffix if repo != "unified-trading-pm"
  }
}

# require-quality-gates — on the default branch (main)
resource "github_repository_ruleset" "require_quality_gates" {
  for_each    = local.repo_qg_suffix
  name        = "require-quality-gates"
  repository  = each.key
  target      = "branch"
  enforcement = "active"

  conditions {
    ref_name {
      include = ["~DEFAULT_BRANCH"]
      exclude = []
    }
  }

  rules {
    required_status_checks {
      required_check {
        context = local.qg_context[each.key]
      }
      strict_required_status_checks_policy = false
    }
  }
}

# require-staging-lock-check — on staging (QG context + the stable check-staging-lock)
resource "github_repository_ruleset" "require_staging_lock_check" {
  for_each    = local.staging_repos
  name        = "require-staging-lock-check"
  repository  = each.key
  target      = "branch"
  enforcement = "active"

  conditions {
    ref_name {
      include = ["refs/heads/staging"]
      exclude = []
    }
  }

  rules {
    required_status_checks {
      required_check {
        context = local.qg_context[each.key]
      }
      required_check {
        context = "check-staging-lock"
      }
      strict_required_status_checks_policy = false
    }
  }
}
