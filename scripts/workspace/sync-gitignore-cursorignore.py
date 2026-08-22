#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""
Sync .gitignore and .cursorignore from PM central templates to all workspace repos.
Preserves repo-specific exceptions (e.g. !tests/fixtures/*.csv, !.env.example).
Preserves the "Repo-specific exceptions" block in each .gitignore so manual additions persist.
Run from workspace root: python3 unified-trading-pm/scripts/sync-gitignore-cursorignore.py

Flags:
  --repo NAME          Limit to a single repo.
  --dry-run            Preview changes without writing anything.

  --purge-history      DESTRUCTIVE: rewrites git history to remove files matching
                       .gitignore from every past commit. Requires git-filter-repo.
                       Prints force-push instructions — does NOT push automatically.
                       NOT part of the normal sync workflow — explicit flag only.
                       Use --dry-run first to preview what would be removed.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

PM = Path(__file__).resolve().parent.parent.parent
WORKSPACE_ROOT = PM.parent
TEMPLATES = PM / "scripts" / "templates"
CENTRAL_GITIGNORE = TEMPLATES / ".gitignore.central"
CENTRAL_CURSORIGNORE = TEMPLATES / ".cursorignore.central"

# Header for the block that sync preserves; add patterns below this in any repo.
REPO_EXCEPTIONS_HEADER = "# --- Repo-specific exceptions (add below; sync preserves this section) ---"
# Placed at top of every .gitignore for visibility (sync writes this + preserved block first).
KEEP_THESE_LINE = "# --- Keep these (do not ignore): uv.lock, package.json, .env.example, tsconfig.json ---"

# Repos with Terraform — get the active (uncommented) terraform block in .gitignore.
TERRAFORM_REPOS = {"unified-trading-deployment-v3", "ibkr-gateway-infra", "deployment-service"}


# Repos to process (must have .git at root)
def get_repos(repo_filter: str | None = None) -> list[Path]:
    if repo_filter:
        p = WORKSPACE_ROOT / repo_filter
        if not (p / ".git").exists():
            raise SystemExit(f"Repo not found or not a git repo: {repo_filter}")
        return [p]
    repos = []
    for d in WORKSPACE_ROOT.iterdir():
        if d.is_dir() and (d / ".git").exists():
            name = d.name
            if name.startswith(".") or name in (".venv-workspace", ".mypy_cache"):
                continue
            repos.append(d)
    return sorted(repos, key=lambda x: x.name)


# Repo-specific additions for .gitignore (appended after central content)
REPO_GITIGNORE_ADDITIONS = {
    "unified-trading-library": [
        "",
        "# --- Repo-specific: keep test fixtures on remote ---",
        "!tests/fixtures/*.csv",
    ],
    "unified-trading-deployment-v3": [
        "",
        "# --- Repo-specific: keep example env on remote ---",
        "!.env.example",
    ],
    "trading-analytics-ui": [
        "",
        "# --- Repo-specific: keep example env on remote ---",
        "!.env.example",
    ],
    "features-delta-one-service": [
        "",
        "# --- Repo-specific: keep mock data on remote ---",
        "!data/",
        "!data/mock/",
        "!data/mock/ETHUSDT.csv",
        "!data/mock/SOLUSDT.csv",
    ],
    "unified-trading-pm": [
        "",
        "# --- Repo-specific: keep github-integration data on remote ---",
        "!github-integration/",
        "!github-integration/data/",
        "!github-integration/data/*.json",
    ],
    "features-sports-service": [
        "",
        "# --- Repo-specific: keep data writer on remote ---",
        "!features_sports_service/",
        "!features_sports_service/data/",
        "!features_sports_service/data/writer.py",
    ],
    "instruments-service": [
        "",
        "# --- Repo-specific: keep sp500 tickers on remote ---",
        "!instruments_service/",
        "!instruments_service/data/",
        "!instruments_service/data/sp500_tickers.json",
    ],
    "execution-service": [
        "",
        "# --- Repo-specific: keep data module (source code) on remote ---",
        "!execution_service/",
        "!execution_service/data/",
        "!execution_service/data/**",
    ],
}


def read_central(path: Path) -> str:
    return path.read_text().strip()


def extract_preserved_gitignore_block(existing_path: Path) -> str:
    """Extract content under REPO_EXCEPTIONS_HEADER from existing .gitignore (for re-sync).
    Works whether the block is at top (new) or end (old) of file; stops at central header '# ==='.
    """
    if not existing_path.exists():
        return ""
    text = existing_path.read_text()
    if REPO_EXCEPTIONS_HEADER not in text:
        return ""
    start = text.index(REPO_EXCEPTIONS_HEADER)
    after_header = text[start + len(REPO_EXCEPTIONS_HEADER) :].lstrip("\n")
    lines = after_header.splitlines()
    preserved_lines = []
    for line in lines:
        if line.strip().startswith("# ="):
            break
        preserved_lines.append(line)
    return "\n".join(preserved_lines).rstrip()


def gitignore_for_repo(repo_name: str, central: str, preserved_block: str = "") -> str:
    # Top block: keep-these note + repo exceptions header + preserved lines (easy to see and maintain)
    top = KEEP_THESE_LINE + "\n" + REPO_EXCEPTIONS_HEADER + "\n"
    if preserved_block:
        top += preserved_block.rstrip() + "\n"
    top += "\n"

    out = central
    # Uncomment Terraform block for repos that contain Terraform configuration.
    if repo_name in TERRAFORM_REPOS:
        terraform_commented = (
            "# --- Optional: Terraform (uncomment if repo has Terraform) ---\n"
            "# **/.terraform/\n# *.tfstate\n# *.tfstate.*\n# *.tfplan\n"
            "# crash.log\n# crash.*.log\n# override.tf\n# override.tf.json\n"
            "# *_override.tf\n# *_override.tf.json\n# *.auto.tfvars"
        )
        terraform_active = (
            "# --- Terraform (active in this repo) ---\n"
            "**/.terraform/\n*.tfstate\n*.tfstate.*\n*.tfplan\n"
            "crash.log\ncrash.*.log\noverride.tf\noverride.tf.json\n"
            "*_override.tf\n*_override.tf.json\n*.auto.tfvars"
        )
        out = out.replace(terraform_commented, terraform_active)
    additions = REPO_GITIGNORE_ADDITIONS.get(repo_name)
    if additions:
        out += "\n" + "\n".join(additions)

    return top + out + "\n"


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def purge_history_for_repo(repo: Path, dry_run: bool = False) -> bool:
    """Rewrite git history to remove files that should be .gitignored.

    Uses git-filter-repo to excise matching paths from every commit.
    Saves and restores origin remote (filter-repo removes it as a safety measure).
    Does NOT push — prints force-push instructions after rewriting.
    Returns True if paths were found (or would be found in dry-run).
    """
    name = repo.name

    # Collect all file paths ever added across full history.
    r = _run(
        ["git", "log", "--all", "--diff-filter=A", "--name-only", "--pretty=format:"],
        cwd=repo,
    )
    if r.returncode != 0 or not r.stdout.strip():
        print(f"{name}/: no git history or error — skipping purge")
        return False

    historical_paths = sorted({p.strip() for p in r.stdout.splitlines() if p.strip()})

    # Ask git which of those paths match the current .gitignore rules.
    check = subprocess.run(
        ["git", "check-ignore", "--no-index", "--stdin"],
        input="\n".join(historical_paths) + "\n",
        cwd=repo,
        capture_output=True,
        text=True,
    )
    to_purge = sorted({p.strip() for p in check.stdout.splitlines() if p.strip()})

    if not to_purge:
        print(f"{name}/: no history paths match .gitignore — nothing to purge")
        return False

    print(f"{name}/: {len(to_purge)} path(s) to purge from history:")
    for p in to_purge:
        print(f"  {p}")

    if dry_run:
        return True

    # Verify git-filter-repo is available.
    gfr = subprocess.run(["which", "git-filter-repo"], capture_output=True, text=True)
    if gfr.returncode != 0:
        print(
            f"{name}/: git-filter-repo not found — install with: pip install git-filter-repo",
            file=sys.stderr,
        )
        return False

    # Save origin URL before filter-repo removes it.
    origin_r = _run(["git", "remote", "get-url", "origin"], cwd=repo)
    origin_url = origin_r.stdout.strip() if origin_r.returncode == 0 else None

    # Remove filter-repo's "already_ran" marker so re-runs don't prompt interactively.
    already_ran = repo / ".git" / "filter-repo" / "already_ran"
    already_ran.unlink(missing_ok=True)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("\n".join(to_purge) + "\n")
        tmp_path = Path(f.name)

    try:
        r2 = subprocess.run(
            ["git-filter-repo", "--paths-from-file", str(tmp_path), "--invert-paths", "--force"],
            cwd=repo,
        )
        if r2.returncode != 0:
            print(f"{name}/: git-filter-repo failed (exit {r2.returncode})", file=sys.stderr)
            return False
    finally:
        tmp_path.unlink(missing_ok=True)

    # Restore origin (filter-repo always removes it).
    if origin_url:
        subprocess.run(["git", "remote", "add", "origin", origin_url], cwd=repo, capture_output=True)
        print(f"{name}/: history purged, origin restored ({origin_url})")
        print(f"  -> Force-push required: git -C {repo} push --force origin HEAD")
    else:
        print(f"{name}/: history purged (no origin remote to restore)")

    return True


def main() -> None:
    repo_filter: str | None = None
    purge_history = False
    dry_run = False

    argv = sys.argv[1:]
    i = 0
    while i < len(argv):
        if argv[i] == "--repo" and i + 1 < len(argv):
            repo_filter = argv[i + 1]
            i += 2
        elif argv[i].startswith("--repo="):
            repo_filter = argv[i].split("=", 1)[1]
            i += 1
        elif argv[i] == "--purge-history":
            purge_history = True
            i += 1
        elif argv[i] == "--dry-run":
            dry_run = True
            i += 1
        else:
            i += 1

    central_git = read_central(CENTRAL_GITIGNORE)
    central_cursor = read_central(CENTRAL_CURSORIGNORE)

    repos = get_repos(repo_filter)
    for repo in repos:
        name = repo.name
        gitignore_path = repo / ".gitignore"
        cursorignore_path = repo / ".cursorignore"

        preserved = extract_preserved_gitignore_block(gitignore_path)
        git_content = gitignore_for_repo(name, central_git, preserved)
        cursor_content = central_cursor + "\n"

        if dry_run:
            print(f"{name}/: would update (.gitignore, .cursorignore)")
            continue
        gitignore_path.write_text(git_content)
        cursorignore_path.write_text(cursor_content)
        print(f"Updated {name}/ (.gitignore, .cursorignore)")

    if dry_run:
        print(f"Done (dry-run). Would sync {len(repos)} repos.")
    else:
        print(f"Done. Synced {len(repos)} repos.")

    # Purge history before untracking — filter-repo rewrites HEAD so untrack
    # handles any remaining stragglers cleanly.
    #
    # --purge-history is intentionally NOT part of the normal sync/untrack workflow.
    # It rewrites git history and requires a force-push to each affected remote.
    if purge_history:
        print("\n" + "=" * 70)
        print("WARNING: --purge-history rewrites git history.")
        print("  - Commits in affected repos will get new SHAs.")
        print("  - Anyone with a local clone must re-clone after force-push.")
        print("  - A force-push to each affected remote is required.")
        print("  - This does NOT run as part of normal sync — explicit flag only.")
        if dry_run:
            print("  (dry-run: showing what would be purged, no changes made)")
        print("=" * 70)
        sys.stdout.flush()
        mode = " (dry-run)" if dry_run else ""
        print(f"\nPurging history{mode} ...")
        sys.stdout.flush()
        purged_any = False
        for repo in repos:
            if purge_history_for_repo(repo, dry_run=dry_run):
                purged_any = True
        if not purged_any:
            print("No paths to purge across all repos.")

    # Untrack any files currently in the index that are matched by .gitignore.
    # In --dry-run mode, pass --dry-run (not --untrack) so the callee also only reports.
    untrack_script = Path(__file__).parent / "untrack-ignored-files.py"
    untrack_flag = "--dry-run" if dry_run else "--untrack"
    untrack_cmd = [sys.executable, str(untrack_script), untrack_flag]
    if repo_filter:
        untrack_cmd += ["--repo", repo_filter]
    sys.stdout.flush()
    print(f"\nRunning untrack-ignored-files.py {untrack_flag} ...")
    sys.stdout.flush()
    result = subprocess.run(untrack_cmd, check=False)
    if result.returncode != 0:
        print("untrack-ignored-files.py exited with errors (see above).", file=sys.stderr)


if __name__ == "__main__":
    main()
