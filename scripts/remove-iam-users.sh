#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Remove specified user principals from the project IAM policy (security cleanup).
# Use for offboarded/old emails that must no longer have any project access.
#
# Usage:
#   bash unified-trading-pm/scripts/remove-iam-users.sh
#   PROJECT_ID=central-element-323112 bash unified-trading-pm/scripts/remove-iam-users.sh
#
# Optional: --dry-run to print what would be removed without applying.
# Requires: gcloud installed and authenticated as a project owner/admin.

set -e

PROJECT_ID="${PROJECT_ID:-central-element-323112}"
DRY_RUN=""

# Users to remove (all permissions revoked)
USERS_TO_REMOVE=(
  balazs@odum-research.com
  ezgi@odum-research.com
  jack@odum-research.com
  jin.uk.hu95@gmail.com
  laurent@odum-research.com
  sebastjan@odum-research.com
  tim@odum-group.io
)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

if ! command -v gcloud &>/dev/null; then
  echo "Error: gcloud CLI not found."
  exit 1
fi

echo "Project: $PROJECT_ID"
echo "Users to remove from IAM:"
for u in "${USERS_TO_REMOVE[@]}"; do echo "  - $u"; done
echo ""

POLICY_FILE=$(mktemp)
trap 'rm -f "$POLICY_FILE"' EXIT

gcloud projects get-iam-policy "$PROJECT_ID" --format=json >"$POLICY_FILE"

# Remove each user from every binding; write updated policy to new file
python3 <<PY
import json
with open("$POLICY_FILE") as f:
    policy = json.load(f)
removed = set()
for binding in policy.get("bindings", []):
    role = binding.get("role", "")
    members = binding.get("members", [])
    new_members = [m for m in members if not m.startswith("user:") or m.replace("user:", "") not in (
        "balazs@odum-research.com",
        "ezgi@odum-research.com",
        "jack@odum-research.com",
        "jin.uk.hu95@gmail.com",
        "laurent@odum-research.com",
        "sebastjan@odum-research.com",
        "tim@odum-group.io",
    )]
    for m in members:
        if m.startswith("user:") and m.replace("user:", "") in (
            "balazs@odum-research.com", "ezgi@odum-research.com", "jack@odum-research.com",
            "jin.uk.hu95@gmail.com", "laurent@odum-research.com", "sebastjan@odum-research.com",
            "tim@odum-group.io",
        ):
            removed.add((role, m))
    binding["members"] = new_members
# Remove bindings with no members left
policy["bindings"] = [b for b in policy["bindings"] if b.get("members")]
with open("$POLICY_FILE", "w") as f:
    json.dump(policy, f, indent=2)
for r, m in sorted(removed):
    print(f"  Remove: {m} from {r}")
PY

if [[ -n "$DRY_RUN" ]]; then
  echo ""
  echo "[DRY-RUN] No changes applied. Run without --dry-run to apply."
  exit 0
fi

echo ""
read -p "Apply IAM policy change? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 0
fi

gcloud projects set-iam-policy "$PROJECT_ID" "$POLICY_FILE"
echo "Done. Removed users no longer have any project IAM bindings."
echo "Verify: bash unified-trading-pm/scripts/list-gcp-iam-emails.sh"
