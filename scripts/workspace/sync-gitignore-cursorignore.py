#!/usr/bin/env python3.13
"""
Sync .gitignore and .cursorignore from PM central templates to all workspace repos.
Preserves repo-specific exceptions (e.g. !tests/fixtures/*.csv, !.env.example).
Preserves the "Repo-specific exceptions" block in each .gitignore so manual additions persist.
Run from workspace root: python3 unified-trading-pm/scripts/sync-gitignore-cursorignore.py
"""

import subprocess
import sys
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
    # Uncomment Terraform block only for deployment-v3
    if repo_name == "unified-trading-deployment-v3":
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


def main():
    repo_filter: str | None = None
    argv = sys.argv[1:]
    i = 0
    while i < len(argv):
        if argv[i] == "--repo" and i + 1 < len(argv):
            repo_filter = argv[i + 1]
            i += 2
        elif argv[i].startswith("--repo="):
            repo_filter = argv[i].split("=", 1)[1]
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

        gitignore_path.write_text(git_content)
        cursorignore_path.write_text(cursor_content)
        print(f"Updated {name}/ (.gitignore, .cursorignore)")

    print(f"Done. Synced {len(repos)} repos.")

    # Now untrack any files that are now matched by the updated .gitignore rules.
    untrack_script = Path(__file__).parent / "untrack-ignored-files.py"
    untrack_cmd = [sys.executable, str(untrack_script), "--untrack"]
    if repo_filter:
        untrack_cmd += ["--repo", repo_filter]
    sys.stdout.flush()
    print("\nRunning untrack-ignored-files.py --untrack ...")
    sys.stdout.flush()
    result = subprocess.run(untrack_cmd, check=False)
    if result.returncode != 0:
        print("untrack-ignored-files.py exited with errors (see above).", file=sys.stderr)


if __name__ == "__main__":
    main()
