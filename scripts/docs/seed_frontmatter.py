#!/usr/bin/env python3
"""seed_frontmatter — mechanical auto-seed of documentation frontmatter (W3 backfill, cheap step).

Fills only the DERIVABLE universal-core + per-type fields, preserving existing values, and leaves the
expensive content fields (`summary`, `tags`) PRESENT-BUT-EMPTY (deferred to the later content pass).
Mirrors codex/11-project-management/doc-frontmatter-schema.md; uses docspec for the enums/specs/registries.

Modes:
  --sample [--n 5] [--out DIR]   seed 5 docs per doc_type into DIR (default scratchpad) — NON-destructive review
  --apply PATH...                seed the given docs IN PLACE
  --check-out DIR                run docspec over a seeded output dir and print the validation summary

# Epic: agent_operating_framework_master
# Lifecycle: permanent
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import docspec
import yaml
from docspec import (
    PER_TYPE,
    Sev,
    doc_type_for_path,
    is_exempt,
    load_registries,
    parse_frontmatter,
    validate_frontmatter,
)

# --------------------------------------------------------------------------- mechanical defaults
NATURE_DEFAULT = {
    "plan": "process",
    "epic": "process",
    "issue": "notes",
    "audit-result": "record",
    "audit-instruction": "process",
    "codex-ssot": "ssot",
    "codex-runbook": "process",
    "agent-role": "guideline",
}


def _git_created(path: Path) -> str | None:
    try:
        out = (
            subprocess.run(
                ["git", "log", "--diff-filter=A", "--follow", "--format=%as", "--", str(path)],
                cwd=path.parent,
                capture_output=True,
                text=True,
                timeout=15,
            )
            .stdout.strip()
            .splitlines()
        )
        return out[-1] if out else None
    except (OSError, subprocess.SubprocessError):
        return None


def _derive_title(fm: dict, body: str, path: Path) -> str:
    if fm.get("title"):
        return str(fm["title"])
    if fm.get("name"):
        return str(fm["name"])
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def _derive_asset_group(parent_epic: object, doc_type: str) -> list[str]:
    if not parent_epic:
        return ["meta"] if doc_type in ("codex-ssot", "codex-runbook", "agent-role") else ["cross-cutting"]
    pe = str(parent_epic).lower()
    table: list[tuple[str, tuple[str, ...]]] = [
        ("defi", ("defi",)),
        ("cefi", ("cefi",)),
        ("tradfi", ("tradfi",)),
        ("sports", ("sport",)),
        ("prediction", ("predict",)),
        (
            "infrastructure",
            ("infra", "orchestrator", "deployment", "observ", "cicd", "manifest", "mtds", "instrument", "plan_hygiene"),
        ),
    ]
    for ag, keys in table:
        if any(k in pe for k in keys):
            return [ag]
    return ["cross-cutting"]


def _derive_repos(body: str, repos: frozenset[str]) -> list[str]:
    found = sorted({r for r in repos if r and r in body})
    return found[:6]


def _normalize_status(status: object, doc_type: str) -> object:
    if doc_type == "issue" and status == "active":
        return "open"  # operator 2026-06-24: issues use open, not active
    return status


def seed_fields(path: Path, fm: dict, body: str, reg: docspec.Registries) -> dict:
    """Build the canonical, mechanically-seeded frontmatter dict (insertion-ordered)."""
    dt = doc_type_for_path(str(path))
    out: dict[str, object] = {}
    if dt == "cursor-rule":
        out["doc_type"] = "cursor-rule"
        for k, v in fm.items():
            if k != "doc_type":
                out[k] = v
        return out
    out["doc_type"] = dt
    out["title"] = _derive_title(fm, body, path)
    out["summary"] = fm.get("summary")  # present-but-empty (deferred)
    out["status"] = _normalize_status(fm.get("status"), dt or "")
    out["nature"] = fm.get("nature") or NATURE_DEFAULT.get(dt or "")
    out["asset_group"] = fm.get("asset_group") or _derive_asset_group(
        fm.get("parent_epic") or fm.get("parent"), dt or ""
    )
    out["stage"] = fm.get("stage") or ["meta"]
    out["repos"] = fm.get("repos") or _derive_repos(body, reg.repos)
    # `scope` is the AUDIENCE axis (a list); a PROSE scope is legacy audit-coverage text -> audited_scope, not audience
    legacy_prose_scope = fm.get("scope") if isinstance(fm.get("scope"), str) else None
    out["scope"] = (None if legacy_prose_scope else fm.get("scope")) or ["engineer", "admin"]
    out["tags"] = fm.get("tags") or []  # present-but-empty (deferred)
    out["related"] = fm.get("related") or fm.get("related_plans") or []
    out["created"] = fm.get("created") or _git_created(path)
    # per-type fields: keep existing value (or present-but-empty)
    for spec in PER_TYPE.get(dt or "", []):
        if spec.name not in out:
            out[spec.name] = fm.get(spec.name)
    # derive a plan's assigned_vm from its parent_epic when missing (operator overrides per D2 precedence);
    # an epic (or a plan with no resolvable epic) defaults to NA = "not dispatched until set".
    if dt in ("plan", "epic") and not out.get("assigned_vm"):
        pe = fm.get("parent_epic")
        out["assigned_vm"] = reg.epic_vms.get(str(pe), "NA") if pe else "NA"
    # rehome a legacy prose `scope` (audit coverage) onto audited_scope
    if legacy_prose_scope and not out.get("audited_scope"):
        out["audited_scope"] = legacy_prose_scope
    # preserve any other existing keys (non-destructive); retire `name` on non-epics + fold related_plans
    handled = set(out.keys()) | {"name", "related_plans"}
    for k, v in fm.items():
        if k not in handled:
            out[k] = v
    return out


def emit_frontmatter(fields: dict) -> str:
    dumped = yaml.safe_dump(fields, sort_keys=False, default_flow_style=None, allow_unicode=True, width=1000)
    lines = []
    for ln in dumped.splitlines():
        if ln.endswith(": null"):
            ln = ln[: -len(" null")]
        lines.append(ln)
    return "---\n" + "\n".join(lines) + "\n---\n"


def seed_text(path: Path, reg: docspec.Registries) -> str:
    text = path.read_text()
    fm, body = parse_frontmatter(text)
    fm = fm or {}
    fields = seed_fields(path, fm, body, reg)
    return emit_frontmatter(fields) + "\n" + body.lstrip("\n")


# --------------------------------------------------------------------------- sample selection
def _spread(items: list[Path], n: int) -> list[Path]:
    items = sorted(items)
    if len(items) <= n:
        return items
    step = len(items) / n
    return [items[int(i * step)] for i in range(n)]


def sample_paths(pm_root: Path, n: int) -> dict[str, list[Path]]:
    ws = pm_root.parent

    def pick(globbed) -> list[Path]:
        return _spread([p for p in globbed if not is_exempt(str(p))], n)

    return {
        "plan": pick((pm_root / "plans/active").glob("*.md")),
        "epic": pick((pm_root / "plans/epics").glob("*.md")),
        "issue": pick((pm_root / "plans/active/issues").glob("*.md")),
        "audit-result": pick((pm_root / "plans/audit/results").rglob("*.md")),
        "audit-instruction": pick((pm_root / "plans/audit/instructions").rglob("*.md")),
        "codex-ssot": pick(p for p in (pm_root / "codex").rglob("*.md") if "15-runbooks" not in str(p)),
        "codex-runbook": pick((pm_root / "codex/15-runbooks").rglob("*.md")),
        "agent-role": pick((ws / "agent-orchestrator/agents").glob("*.md")),
    }


# --------------------------------------------------------------------------- CLI
def _dirty_paths(pm_root: Path) -> set[str]:
    """Repo-relative paths with uncommitted changes (so we never stomp a concurrent session's WIP)."""
    out = subprocess.run(
        ["git", "status", "--porcelain"], cwd=pm_root, capture_output=True, text=True, timeout=30
    ).stdout
    return {line[3:].strip() for line in out.splitlines() if line.strip()}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", action="store_true", help="seed 5 docs per doc_type into --out (non-destructive)")
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--out", help="output dir for --sample (default: a scratchpad temp dir)")
    ap.add_argument("--apply", nargs="+", help="seed the given docs IN PLACE")
    ap.add_argument(
        "--apply-sample", action="store_true", help="seed the 5-per-doc_type sample IN PLACE (mtime-guarded)"
    )
    args = ap.parse_args(argv)
    pm_root = docspec._pm_root()
    reg = load_registries(pm_root)

    if args.apply or args.apply_sample:
        if args.apply_sample:
            apply_paths = [str(p) for ps in sample_paths(pm_root, args.n).values() for p in ps]
        else:
            apply_paths = list(args.apply)
        dirty = _dirty_paths(pm_root)  # protect foreign WIP: skip any doc with uncommitted changes
        for p in apply_paths:
            ap_path = Path(p).resolve()
            if is_exempt(p):
                print(f"skipped (exempt):        {p}")
                continue
            try:
                rel = str(ap_path.relative_to(pm_root))
            except ValueError:
                print(f"skipped (cross-repo):    {p}")  # agent-role lives in agent-orchestrator, a separate repo
                continue
            if rel in dirty:
                print(f"skipped (foreign-dirty): {p}")
                continue
            ap_path.write_text(seed_text(ap_path, reg))
            print(f"seeded (in place):       {p}")
        return 0

    out_dir = Path(args.out) if args.out else Path(tempfile.mkdtemp(prefix="fm-sample-"))
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"=== frontmatter sample → {out_dir} ===\n")
    total_hard = 0
    for dt, paths in sample_paths(pm_root, args.n).items():
        print(f"## {dt}  ({len(paths)} docs)")
        for path in paths:
            seeded = seed_text(path, reg)
            dest = out_dir / dt / path.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(seeded)
            fm, _ = parse_frontmatter(seeded)
            vs = validate_frontmatter(dt, fm or {}, reg)
            hard = [v for v in vs if v.severity == Sev.HARD]
            soft = [v for v in vs if v.severity == Sev.SOFT]
            total_hard += len(hard)
            mark = "✓" if not hard else "✗"
            print(
                f"  {mark} {path.name}  hard={len(hard)} soft={len(soft)}"
                + (f"  HARD: {[v.field for v in hard]}" if hard else "")
            )
        print()
    print(f"=== total HARD violations across sample: {total_hard} (target 0) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
