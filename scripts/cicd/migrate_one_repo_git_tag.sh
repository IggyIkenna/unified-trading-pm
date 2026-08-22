#!/usr/bin/env bash
# Epic: ci_master
# Lifecycle: temporary
# Delete-when: fleet-wide git-tag rollout complete
#
# Migrate ONE repo to version_source=git-tag (Phase-2/D13), end to end, then quickmerge.
# Encapsulates the validated pilot sequence (client-reporting-api):
#   1. pyproject → dynamic hatch-vcs        (migrate_repo_to_git_tag.py --apply)
#   2. roll semver-agent[git-tag] + version-registry-notify  (scoped --template; manifest must already
#      be flipped to version_source=git-tag so __VERSION_SOURCE__ substitutes git-tag)
#   3. re-roll cloudbuild.yaml (git-describe VERSION, F3)     (rollout-cloudbuild.py --repo)
#   4. scope the commit to version files (revert unrelated benign template refreshes)
#   5. quickmerge --agent --files the version set
#
# PRECONDITION: the PM workspace-manifest.json already has repositories[<repo>].version_source=git-tag
# (flipped + committed centrally before this runs, so the template rollout substitutes git-tag).
#
# Usage: migrate_one_repo_git_tag.sh <repo-name>
set -uo pipefail

REPO="${1:?usage: migrate_one_repo_git_tag.sh <repo-name>}"
PM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"     # unified-trading-pm
WS_DIR="$(cd "$PM_DIR/.." && pwd)"                                 # workspace root
REPO_DIR="$WS_DIR/$REPO"

echo "═══════════════════════════════════════════════════════════════════"
echo "MIGRATE $REPO → version_source=git-tag"
echo "═══════════════════════════════════════════════════════════════════"

if [ ! -f "$REPO_DIR/pyproject.toml" ]; then
  echo "❌ $REPO: no pyproject.toml — UI/npm repo, excluded. Skipping."
  exit 3
fi

# Guard: the manifest must already say git-tag for this repo (else the rollout substitutes pyproject).
VS=$(python3 -c "import json;print(json.load(open('$PM_DIR/workspace-manifest.json'))['repositories'].get('$REPO',{}).get('version_source',''))" 2>/dev/null || echo "")
if [ "$VS" != "git-tag" ]; then
  echo "❌ $REPO: manifest version_source='$VS' (not git-tag) — flip + commit the manifest centrally first. Aborting."
  exit 2
fi

# 0b. Baseline-tag backfill: if pyproject declares X.Y.Z but the nearest reachable tag is BEHIND it
# (a release bump whose vX.Y.Z tag wasn't backfilled — e.g. a recent semver bump), mint vX.Y.Z at HEAD
# + push so dynamic versioning resolves the declared version (never regresses). No-op if already tagged.
DECLARED=$(grep -m1 -oE '^version[[:space:]]*=[[:space:]]*"[0-9]+\.[0-9]+\.[0-9]+"' "$REPO_DIR/pyproject.toml" 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "")
if [ -n "$DECLARED" ]; then
  NEAREST=$(git -C "$REPO_DIR" describe --tags --abbrev=0 --match 'v*' 2>/dev/null | sed 's/^v//' || echo "")
  HIGHEST=$(printf '%s\n%s\n' "${NEAREST:-0.0.0}" "$DECLARED" | sort -V | tail -1)
  if [ "$HIGHEST" = "$DECLARED" ] && [ "$NEAREST" != "$DECLARED" ]; then
    if git -C "$REPO_DIR" rev-parse "v$DECLARED" >/dev/null 2>&1; then
      echo "  ⚠️  $REPO: v$DECLARED exists but is not reachable from HEAD — audit will re-check (may need manual tag move)"
    else
      git -C "$REPO_DIR" tag -a "v$DECLARED" -m "baseline release tag for git-tag migration (pyproject declared $DECLARED; backfill)" 2>/dev/null \
        && git -C "$REPO_DIR" push origin "v$DECLARED" 2>/dev/null \
        && echo "  ✅ $REPO: minted baseline tag v$DECLARED at HEAD (pyproject was ahead of nearest tag v${NEAREST:-none})" \
        || echo "  ⚠️  $REPO: baseline tag v$DECLARED mint/push issue (may already exist remotely)"
    fi
  fi
fi

# 1. pyproject → dynamic (safety-audited; refuses on regression / 1.0.0 crossing).
python3 "$PM_DIR/scripts/cicd/migrate_repo_to_git_tag.py" --repo "$REPO" --apply || { echo "❌ $REPO: pyproject migration UNSAFE/failed"; exit 2; }

# 2. roll the two version workflows ONLY (scoped — avoid bundling unrelated template refreshes).
bash "$PM_DIR/scripts/workflow-templates/rollout-workflow-templates.sh" --repo "$REPO" --template semver-agent.yml.tmpl >/dev/null 2>&1 || true
bash "$PM_DIR/scripts/workflow-templates/rollout-workflow-templates.sh" --repo "$REPO" --template version-registry-notify.yml >/dev/null 2>&1 || true

# 3. PATCH the existing cloudbuild's extract-version → git-describe IN PLACE (preserves stage-siblings,
#    pm-configs, and every other per-repo customization). Re-rolling the whole file from the generic
#    template clobbered those custom steps (silent — QG doesn't run the cloudbuild Docker build), so we
#    surgically patch only the one version line instead.
[ -f "$REPO_DIR/cloudbuild.yaml" ] && python3 "$PM_DIR/scripts/cicd/patch_cloudbuild_version.py" "$REPO_DIR/cloudbuild.yaml" || true

cd "$REPO_DIR" || { echo "❌ $REPO: cannot cd"; exit 2; }

# 4. scope to version files: revert anything the rollout touched that is NOT part of the migration.
git checkout HEAD -- cursor-configs/settings.json 2>/dev/null || true
for f in .github/workflows/quality-gates-v2.yml .github/workflows/update-dependency-version.yml \
         .github/workflows/staging-lock-check.yml .github/workflows/request-major-bump.yml \
         .github/workflows/major-bump-issue-handler.yml; do
  [ -f "$f" ] && git checkout HEAD -- "$f" 2>/dev/null || true
done

# Confirm the migration actually applied.
if ! grep -q 'dynamic = \["version"\]' pyproject.toml; then
  echo "❌ $REPO: pyproject not dynamic after transform — aborting before commit"; exit 2
fi

# Build the --files list from what genuinely changed among the version set.
FILES=""
for f in pyproject.toml cloudbuild.yaml .github/workflows/semver-agent.yml .github/workflows/version-registry-notify.yml; do
  if [ -f "$f" ] && ! git diff --quiet -- "$f" 2>/dev/null; then FILES="$FILES $f"; fi
  # untracked (new) files (version-registry-notify.yml on first roll)
  if [ -f "$f" ] && git status --porcelain -- "$f" 2>/dev/null | grep -q '^??'; then FILES="$FILES $f"; fi
done
FILES="$(echo "$FILES" | xargs -n1 2>/dev/null | sort -u | xargs 2>/dev/null)"
if [ -z "$FILES" ]; then echo "⚠️  $REPO: no version-file changes to commit (already migrated?)"; exit 0; fi
echo "  files: $FILES"

# 4b. Full QG FIRST — validates the migrated tree under dynamic versioning AND writes a fresh green
# sentinel at the current HEAD, so quickmerge --no-fix fast-paths (a moved HEAD from a backmerge
# otherwise invalidates the sentinel and quickmerge bails without committing).
echo "── running full QG for $REPO (validates dynamic versioning + writes sentinel) ──"
if ! bash "$REPO_DIR/scripts/quality-gates.sh" >/tmp/qg_${REPO//\//_}.log 2>&1; then
  echo "❌ $REPO: QG FAILED under dynamic versioning — see /tmp/qg_${REPO//\//_}.log (last 20):"
  tail -20 "/tmp/qg_${REPO//\//_}.log"
  exit 2
fi
echo "  ✅ QG green for $REPO"

# 5. quickmerge (fast-paths on the fresh sentinel; lands on LDR).
bash "$REPO_DIR/scripts/quickmerge.sh" "feat(cicd): migrate to version_source=git-tag (Phase-2/D13 fleet rollout)

Switch pyproject to dynamic hatch-vcs versioning (version out of source); the released version
resolves from the git tag (git describe), no committed 'version =' line. Roll retargeted
semver-agent (VERSION_SOURCE=git-tag, mints tags) + version-registry-notify (tag push -> PM
registry); re-roll cloudbuild (VERSION from git describe, F3). version_source=git-tag flipped in
the PM manifest. Backward-compatible: git describe resolves the same version the repo declared.
Operator-mandated fleet-wide git-tag rollout." --agent --files "$FILES"
RC=$?
echo "── quickmerge rc=$RC for $REPO ──"
exit $RC
