#!/usr/bin/env bash
# Epic: ci_master
# Lifecycle: temporary
# Delete-when: fleet-wide git-tag rollout complete
#
# Corrective: the git-tag migration re-rolled the whole cloudbuild from the generic template,
# clobbering per-repo custom steps (stage-siblings / operability-probe / pm-configs). Restore the
# PRE-migration cloudbuild (its parent commit) and surgically patch ONLY extract-version to
# git-describe — preserving the custom steps. Commit the corrected cloudbuild.
#
# Usage: fix_clobbered_cloudbuild.sh <repo-name>
set -uo pipefail
REPO="${1:?usage: fix_clobbered_cloudbuild.sh <repo>}"
PM="/Users/ikennaigboaka/Code/unified-trading-system-repos/.tabs/3/unified-trading-pm"
WS="$(cd "$PM/.." && pwd)"
cd "$WS/$REPO" || { echo "❌ $REPO: cannot cd"; exit 2; }
git checkout HEAD -- cursor-configs/settings.json 2>/dev/null || true

MC=$(git log --grep="migrate to version_source=git-tag" --format=%H -1 2>/dev/null)
[ -z "$MC" ] && { echo "❌ $REPO: no migration commit found"; exit 1; }
if ! git show "$MC^:cloudbuild.yaml" > cloudbuild.yaml 2>/dev/null; then
  echo "❌ $REPO: cannot restore pre-migration cloudbuild from $MC^"; exit 1
fi
python3 "$PM/scripts/cicd/patch_cloudbuild_version.py" cloudbuild.yaml || { echo "❌ $REPO: patch failed"; exit 1; }
if git diff --quiet cloudbuild.yaml; then echo "✅ $REPO: cloudbuild already correct (no change)"; exit 0; fi
echo "── $REPO: restored custom cloudbuild + git-describe; running QG ──"
if ! bash scripts/quality-gates.sh > "/tmp/qgfix_${REPO//\//_}.log" 2>&1; then
  echo "❌ $REPO: QG FAILED — see /tmp/qgfix_${REPO//\//_}.log"; tail -15 "/tmp/qgfix_${REPO//\//_}.log"; exit 2
fi
bash scripts/quickmerge.sh "fix(cicd): restore custom cloudbuild steps clobbered by the git-tag migration

The git-tag migration re-rolled the whole cloudbuild from the generic template, dropping per-repo
custom steps (stage-siblings cloning sibling repos into the GCP build context for the Dockerfile
COPY / operability-probe / pm-configs). Restore the pre-migration cloudbuild and surgically patch
ONLY the version-extraction to git-describe (Phase-2/D13), preserving the custom steps. Corrective." \
  --agent --no-fix --files cloudbuild.yaml
echo "── fix rc=$? for $REPO ──"
