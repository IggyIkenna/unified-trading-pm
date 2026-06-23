#!/usr/bin/env bash
# Epic: sports_master
# Lifecycle: oneoff
# Delete-when: after prod-run + orphan-sweep=0
# migrate_sports_gcs_paths.sh — Audit and migrate sports data GCS paths.
#
# Validates (and optionally migrates) sports reference data in GCS from any
# old path conventions to the canonical paths used by features-sports-service.
#
# Usage:
#   bash migrate_sports_gcs_paths.sh [--apply] [--bucket BUCKET] [--project PROJECT]
#
# Options:
#   --apply           Perform the migration (default: dry-run, list only)
#   --bucket BUCKET   GCS bucket name (default: ${GCP_PROJECT_ID}-sports-data)
#   --project PROJECT GCS project ID (default: reads GCP_PROJECT_ID env var)
#
# Canonical path conventions (SSOT):
#   sports/team_mappings.parquet         — TeamMapping records (UAC TeamMapping schema)
#   sports/league_classifications.parquet — LeagueClassification records
#   sports/fixtures/{season}/{league_id}/{date}.parquet
#
# Old path conventions that may exist from instruments-service era:
#   team_mapping_data/*.parquet
#   league_data/*.parquet
#   sports_data/fixtures/*.parquet

set -euo pipefail

APPLY=false
BUCKET=""
PROJECT="${GCP_PROJECT_ID:-}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --apply)   APPLY=true; shift ;;
        --bucket)  BUCKET="$2"; shift 2 ;;
        --project) PROJECT="$2"; shift 2 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

if [[ -z "$PROJECT" ]]; then
    echo "ERROR: GCP_PROJECT_ID is not set. Pass --project or export GCP_PROJECT_ID."
    exit 1
fi

if [[ -z "$BUCKET" ]]; then
    BUCKET="${PROJECT}-sports-data"
fi

echo "=== Sports GCS Path Migration ==="
echo "Project : $PROJECT"
echo "Bucket  : gs://${BUCKET}"
echo "Mode    : $([ "$APPLY" = true ] && echo 'APPLY' || echo 'DRY-RUN')"
echo

# ---------------------------------------------------------------------------
# Step 1: Check whether the bucket exists
# ---------------------------------------------------------------------------
if ! gsutil ls "gs://${BUCKET}/" &>/dev/null; then
    echo "INFO: Bucket gs://${BUCKET}/ does not exist or is empty."
    echo "      No GCS data to migrate from the old system — path convention validated."
    echo
    echo "Canonical paths for new data:"
    echo "  gs://${BUCKET}/sports/team_mappings.parquet"
    echo "  gs://${BUCKET}/sports/league_classifications.parquet"
    echo "  gs://${BUCKET}/sports/fixtures/{season}/{league_id}/{date}.parquet"
    exit 0
fi

# ---------------------------------------------------------------------------
# Step 2: List existing objects
# ---------------------------------------------------------------------------
echo "--- Existing objects in gs://${BUCKET}/ ---"
gsutil ls -r "gs://${BUCKET}/**" 2>/dev/null || echo "(bucket is empty)"
echo

# ---------------------------------------------------------------------------
# Step 3: Define old → new path mappings
# ---------------------------------------------------------------------------
declare -A PATH_MIGRATIONS=(
    ["team_mapping_data/"]="sports/"
    ["league_data/"]="sports/"
    ["sports_data/fixtures/"]="sports/fixtures/"
)

FOUND=0
for old_prefix in "${!PATH_MIGRATIONS[@]}"; do
    new_prefix="${PATH_MIGRATIONS[$old_prefix]}"
    objects=$(gsutil ls "gs://${BUCKET}/${old_prefix}**" 2>/dev/null || true)
    if [[ -n "$objects" ]]; then
        FOUND=$((FOUND + 1))
        echo "Found objects under old path: gs://${BUCKET}/${old_prefix}"
        echo "$objects" | head -20
        echo
        if [[ "$APPLY" = true ]]; then
            echo "Migrating gs://${BUCKET}/${old_prefix} → gs://${BUCKET}/${new_prefix} ..."
            gsutil -m cp -r "gs://${BUCKET}/${old_prefix}**" "gs://${BUCKET}/${new_prefix}"
            echo "Migration complete. Old paths preserved (delete manually after verification)."
        else
            echo "DRY-RUN: Would migrate → gs://${BUCKET}/${new_prefix}"
        fi
        echo
    fi
done

if [[ $FOUND -eq 0 ]]; then
    echo "No objects found under old path conventions. Nothing to migrate."
    echo
    # Validate canonical paths exist
    echo "--- Checking canonical paths ---"
    for path in \
        "sports/team_mappings.parquet" \
        "sports/league_classifications.parquet"; do
        if gsutil ls "gs://${BUCKET}/${path}" &>/dev/null; then
            echo "  ✅ gs://${BUCKET}/${path}"
        else
            echo "  ⚠️  gs://${BUCKET}/${path} (not present — will be written on first run)"
        fi
    done
fi

echo
echo "=== Done ==="
