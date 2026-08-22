#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Verify every GitHub Actions `uses: owner/repo@ref` pin RESOLVES to a real ref.

The phantom-tag class (incident 2026-06-10): a version bump to `astral-sh/setup-uv@v8`
broke `update-dependency-version.yml` fleet-wide because the v8 series is pin-only
(`@v8.2.0`) — there is NO floating `@v8` tag, so the workflow failed at "Set up job"
with "unable to resolve action ... unable to find version v8". Not every action keeps
floating major tags; assuming one exists is the bug. (Same class as the node24 tag.)

This gate resolves each unique `(owner/repo, ref)` against the GitHub API
(`gh api repos/<owner>/<repo>/commits/<ref>`, which dereferences a tag / branch / SHA
uniformly) and FAILS (exit 1) on any ref that does not resolve — so a phantom pin is
caught BEFORE a workflow-template rollout fans it across the fleet.

Network-graceful: if `gh` is absent or unauthenticated / offline (probe:
`gh api rate_limit`), resolution is SKIPPED with a warning and the gate exits 0. This
keeps it a no-op under `--block-network` local quality-gates while doing real work in
CI and in the `rollout-workflow-templates.sh` pre-flight (which have network + GH_PAT).

Usage:
    python3 check-action-pins.py                 # scan .github/workflows/
    python3 check-action-pins.py --templates     # scan scripts/workflow-templates/ (pre-rollout)
    python3 check-action-pins.py --dir PATH       # scan an explicit dir
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import cast

# `uses:` value capture — first non-whitespace token after `uses:` (trailing `# comment`
# is naturally excluded). The leading `- ` of a step list item is optional.
_USES_RE = re.compile(r"^\s*-?\s*uses:\s*(?P<val>\S+)")

# A pinned external action looks like `owner/repo[/subpath]@ref`. Skip:
#   - local actions / reusable workflows  (`./...`)
#   - docker actions                      (`docker://...`)
#   - dynamic refs                        (`${{ ... }}`)
#   - bare local refs with no `@`


class Pin:
    """One resolvable action pin and where it was seen."""

    __slots__ = ("owner_repo", "ref", "sites")

    def __init__(self, owner_repo: str, ref: str) -> None:
        self.owner_repo = owner_repo
        self.ref = ref
        self.sites: list[str] = []  # "file:lineno" occurrences


def extract_pins(workflow_file: Path) -> list[tuple[str, str, str]]:
    """Return [(owner_repo, ref, "file:lineno"), ...] for resolvable external pins."""
    out: list[tuple[str, str, str]] = []
    try:
        lines = workflow_file.read_text(encoding="utf-8").splitlines()
    except OSError:
        return out
    for i, raw in enumerate(lines, 1):
        m = _USES_RE.match(raw)
        if not m:
            continue
        val = m.group("val").strip().strip("'\"")
        if val.startswith(("./", "docker://")) or "${{" in val or "@" not in val:
            continue
        path, _, ref = val.rpartition("@")
        if not path or not ref:
            continue
        parts = path.split("/")
        if len(parts) < 2:
            continue  # not an owner/repo form
        owner_repo = f"{parts[0]}/{parts[1]}"
        out.append((owner_repo, ref, f"{workflow_file.name}:{i}"))
    return out


def collect_pins(files: list[Path]) -> dict[tuple[str, str], Pin]:
    pins: dict[tuple[str, str], Pin] = {}
    for f in files:
        for owner_repo, ref, site in extract_pins(f):
            key = (owner_repo, ref)
            pin = pins.get(key)
            if pin is None:
                pin = Pin(owner_repo, ref)
                pins[key] = pin
            pin.sites.append(site)
    return pins


def _network_ok() -> bool:
    """True iff `gh` is present and an authenticated API call succeeds (online + authed)."""
    if not shutil.which("gh"):
        return False
    try:
        r = subprocess.run(["gh", "api", "rate_limit"], capture_output=True, text=True, timeout=20, check=False)
    except (OSError, subprocess.SubprocessError):
        return False
    return r.returncode == 0


def ref_resolves(owner_repo: str, ref: str) -> bool:
    """True iff `ref` resolves to a commit on `owner_repo` (tag / branch / SHA)."""
    try:
        r = subprocess.run(
            ["gh", "api", f"repos/{owner_repo}/commits/{ref}", "--jq", ".sha"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return r.returncode == 0 and bool(r.stdout.strip())


def _resolve_dir(args: argparse.Namespace) -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    if cast(bool, args.templates):
        return repo_root / "scripts" / "workflow-templates"
    return Path(cast(str, args.dir))


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify GitHub Actions pins resolve to real refs.")
    parser.add_argument("--dir", default=".github/workflows", help="Workflows dir (default: .github/workflows)")
    parser.add_argument("--templates", action="store_true", help="Scan scripts/workflow-templates/ (pre-rollout gate)")
    args = parser.parse_args()

    scan_dir = _resolve_dir(args)
    if not scan_dir.is_dir():
        print(f"check-action-pins: no such dir {scan_dir} — nothing to check.")
        return 0

    # Include `.tmpl` workflow templates (e.g. quality-gates-v2.yml.tmpl) — they carry
    # `uses:` pins too (setup-uv lives there), so a phantom tag there fans out on rollout.
    files = sorted({p for pat in ("*.yml", "*.yaml", "*.yml.tmpl", "*.tmpl") for p in scan_dir.glob(pat)})
    pins = collect_pins(files)
    if not pins:
        print(f"check-action-pins: no external action pins in {scan_dir}.")
        return 0

    if not _network_ok():
        print(
            f"⚠ check-action-pins: SKIPPED ({len(pins)} unique pin(s)) — gh unavailable / offline / "
            "unauthenticated. Re-run in CI or pre-rollout with network + GH_PAT to verify pins resolve."
        )
        return 0

    unresolved: list[Pin] = []
    for pin in sorted(pins.values(), key=lambda p: (p.owner_repo, p.ref)):
        if not ref_resolves(pin.owner_repo, pin.ref):
            unresolved.append(pin)

    if unresolved:
        print(f"\n❌ {len(unresolved)} action pin(s) do NOT resolve to a real ref:")
        for pin in unresolved:
            print(f"  {pin.owner_repo}@{pin.ref}  — referenced at: {', '.join(pin.sites)}")
        print(
            "\n  A floating major tag may not exist (e.g. astral-sh/setup-uv has no @v8 — use @v8.2.0).\n"
            "  Verify the intended ref: gh api repos/<owner>/<repo>/tags --jq '.[].name' | head"
        )
        return 1

    print(f"✅ check-action-pins: all {len(pins)} unique pin(s) in {scan_dir.name}/ resolve.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
