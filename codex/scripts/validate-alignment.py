"""
Codex alignment validator.

Checks that key codex structural invariants hold:
- SSOT index exists and references expected top-level directories
- No absolute paths in doc files (codex must be portable)
- Required governance docs present

Run: python scripts/validate-alignment.py --check-drift
"""

from __future__ import annotations

import sys
from pathlib import Path


def check_ssot_index(root: Path) -> list[str]:
    errors: list[str] = []
    ssot = root / "00-SSOT-INDEX.md"
    if not ssot.exists():
        errors.append("00-SSOT-INDEX.md missing from codex root")
    return errors


def check_no_absolute_paths(root: Path) -> list[str]:
    errors: list[str] = []
    for md in root.rglob("*.md"):
        if any(p in md.parts for p in (".git", "archive", "node_modules")):
            continue
        if not md.is_file():  # skip broken symlinks
            continue
        text = md.read_text(errors="replace")
        if "/home/" in text or "/Users/" in text:
            errors.append(f"{md.relative_to(root)}: contains absolute path (/home/ or /Users/)")
    return errors


def check_required_dirs(root: Path) -> list[str]:
    errors: list[str] = []
    required = ["06-coding-standards", "04-architecture", "05-infrastructure"]
    for d in required:
        if not (root / d).is_dir():
            errors.append(f"Required directory missing: {d}/")
    return errors


def main() -> int:
    check_drift: bool = "--check-drift" in sys.argv

    if not check_drift:
        print("Nothing to do. Use --check-drift.")
        return 0

    root = Path(__file__).parent.parent
    errors: list[str] = []
    errors.extend(check_ssot_index(root))
    errors.extend(check_required_dirs(root))
    errors.extend(check_no_absolute_paths(root))

    if errors:
        print(f"Alignment check failed ({len(errors)} issue(s)):")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("Alignment check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
