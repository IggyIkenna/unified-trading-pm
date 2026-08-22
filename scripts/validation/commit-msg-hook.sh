#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# Git commit-msg hook for conventional commits validation
#
# This hook validates that commit messages follow conventional commit format:
# type(scope): description
#
# Valid types:
# - feat: A new feature
# - fix: A bug fix
# - chore: Maintenance, dependencies, build changes
# - docs: Documentation changes
# - refactor: Code change that neither fixes a bug nor adds a feature
# - test: Adding missing tests or correcting existing tests
# - ci: Changes to CI configuration files and scripts
# - BREAKING CHANGE: A breaking API change (can be used as type or body footer)
#
# Scope is optional but when provided should be in parentheses: feat(auth):
# Breaking changes can use ! notation: feat!: or fix!:
#
# Examples of valid commit messages:
# - feat: add user authentication
# - fix(api): handle null response in user endpoint
# - feat!: remove deprecated login method
# - chore(deps): update pytest to 8.0.0
# - docs: update API documentation
# - refactor(core): simplify error handling
# - test: add integration tests for payment flow
# - ci: update GitHub Actions workflow
# - BREAKING CHANGE: remove legacy API endpoints
#
# Usage:
# 1. Copy this script to .git/hooks/commit-msg in your repo
# 2. Make it executable: chmod +x .git/hooks/commit-msg
# 3. The hook will run automatically on each commit
#
set -e

commit_file="$1"
commit_msg=$(cat "$commit_file")
first_line=$(echo "$commit_msg" | head -n 1)

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Allow merge commits (git pull/merge creates these; no conventional format)
if [[ "$first_line" == Merge* ]]; then
  echo -e "${GREEN}✅ Merge commit (allowed)${NC}"
  exit 0
fi

# Valid conventional commit pattern
# Supports:
# - Basic types: feat:, fix:, chore:, docs:, refactor:, test:, ci:
# - Scoped types: feat(scope):, fix(api):
# - Breaking changes: feat!:, fix!:, feat(api)!:
# - BREAKING CHANGE as type: BREAKING CHANGE:
PATTERN='^(feat|fix|chore|docs|refactor|test|ci|BREAKING CHANGE)(\([^)]+\))?!?:[[:space:]].+'

if [[ "$first_line" =~ $PATTERN ]]; then
  echo -e "${GREEN}✅ Commit message follows conventional commit format${NC}"
  exit 0
else
  echo -e "${RED}❌ Invalid commit message format${NC}"
  echo
  echo -e "${YELLOW}Your commit message:${NC}"
  echo "  $first_line"
  echo
  echo -e "${YELLOW}Expected format:${NC}"
  echo "  type(scope): description"
  echo
  echo -e "${YELLOW}Valid types:${NC}"
  echo "  feat:     A new feature"
  echo "  fix:      A bug fix"
  echo "  chore:    Maintenance, dependencies, build changes"
  echo "  docs:     Documentation changes"
  echo "  refactor: Code change that neither fixes a bug nor adds a feature"
  echo "  test:     Adding missing tests or correcting existing tests"
  echo "  ci:       Changes to CI configuration files and scripts"
  echo "  BREAKING CHANGE: A breaking API change"
  echo
  echo -e "${YELLOW}Examples:${NC}"
  echo "  feat: add user authentication"
  echo "  fix(api): handle null response in user endpoint"
  echo "  feat!: remove deprecated login method"
  echo "  chore(deps): update pytest to 8.0.0"
  echo "  docs: update API documentation"
  echo "  BREAKING CHANGE: remove legacy API endpoints"
  echo
  echo -e "${RED}Please fix your commit message and try again.${NC}"
  exit 1
fi
