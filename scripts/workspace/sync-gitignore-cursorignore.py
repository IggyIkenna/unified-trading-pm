#!/usr/bin/env python3.13
"""
Sync .gitignore and .cursorignore from PM central templates to all workspace repos.
Preserves repo-specific exceptions (e.g. !tests/fixtures/*.csv, !.env.example).
Preserves the "Repo-specific exceptions" block in each .gitignore so manual additions persist.
Run from workspace root: python3 unified-trading-pm/scripts/sync-gitignore-cursorignore.py
"""

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
def get_repos():
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
        "!data/mock/ETHUSDT.csv",
        "!data/mock/SOLUSDT.csv",
    ],
    "unified-trading-pm": [
        "",
        "# --- Repo-specific: keep github-integration data on remote ---",
        "!github-integration/data/*.json",
    ],
    "features-sports-service": [
        "",
        "# --- Repo-specific: keep data writer on remote ---",
        "!features_sports_service/data/writer.py",
    ],
    "instruments-service": [
        "",
        "# --- Repo-specific: keep sp500 tickers on remote ---",
        "!instruments_service/data/sp500_tickers.json",
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
    central_git = read_central(CENTRAL_GITIGNORE)
    central_cursor = read_central(CENTRAL_CURSORIGNORE)

    repos = get_repos()
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


if __name__ == "__main__":
    main()
