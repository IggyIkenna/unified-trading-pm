#!/usr/bin/env python3
"""docspec — the machine SSOT for documentation frontmatter.

Implements: codex/11-project-management/doc-frontmatter-schema.md (the human SSOT).
Mirrors it in lockstep — the closed-vocab enums, the universal core + per-doc_type
FieldSpecs, and validate_frontmatter() with the THREE-state required/empty/missing logic
that makes the gateless "soak" work:

    missing key            -> required: HARD   | optional: SOFT (add present-but-empty)
    present but empty       -> required: SOFT "needs-content" | optional: OK
    present with a value    -> validate type / enum / registry (bad value: HARD)

`assigned_vm` is the one field whose valid domain includes the `NA` sentinel; a plan's
`assigned_vm` is NEVER cross-checked against its parent_epic's (plan supersedes epic — by design).

# Epic: agent_operating_framework_master
# Lifecycle: permanent
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import yaml

# ----------------------------------------------------------------------------- enums (§5 of the SSOT)
DOC_TYPES = frozenset(
    {
        "plan",
        "epic",
        "issue",
        "audit-result",
        "audit-instruction",
        "codex-ssot",
        "codex-runbook",
        "agent-role",
        "cursor-rule",
    }
)
NATURE = frozenset({"ssot", "guideline", "process", "design", "spec", "record", "notes"})
ASSET_GROUP = frozenset({"cefi", "defi", "tradfi", "sports", "prediction", "cross-cutting", "infrastructure", "meta"})
STAGE = frozenset({"data", "features", "strategy", "backtest", "paper", "live", "execution", "reporting", "meta"})
SCOPE = frozenset({"engineer", "admin", "sales", "prospect", "investor"})
PRIORITY = frozenset({"P0", "P1", "P2", "P3"})
TIER = frozenset({"L0", "L1", "L2", "L3", "L4", "L5"})
ESTIMATE_CLASS = frozenset({"refactor", "design", "infra", "brand-new", "research"})
EXECUTION_SCOPE = frozenset({"orchestrator-agent", "local-only"})
SEVERITY_P = PRIORITY  # audit-result severity is a P0..P3

STATUS_BY_TYPE: dict[str, frozenset[str] | None] = {
    "plan": frozenset({"draft", "active", "blocked", "paused", "complete", "superseded", "cancelled"}),
    "epic": frozenset({"active", "complete", "superseded"}),
    "issue": frozenset({"open", "blocked", "resolved", "false-positive", "superseded"}),
    "audit-result": frozenset({"pass", "partial", "fail"}),
    "audit-instruction": frozenset({"active", "retired"}),
    "codex-ssot": frozenset({"current", "superseded", "stale", "draft"}),
    "codex-runbook": frozenset({"current", "superseded", "stale"}),
    "agent-role": frozenset({"draft", "active", "retired"}),
    "cursor-rule": None,  # Cursor-governed
}


# ----------------------------------------------------------------------------- field specs
class Req(Enum):
    R = "required"
    O = "optional"  # noqa: E741 (enum member name, not a loop variable)
    C = "conditional"


class Sev(Enum):
    HARD = "hard"
    SOFT = "soft"


@dataclass(frozen=True)
class FieldSpec:
    name: str
    req: Req
    kind: str  # scalar|enum|enum_list|free_list|date|registry|registry_or_na|status
    enum: frozenset[str] | None = None
    registry: str | None = None  # vm|epic|repos
    conditional_on: tuple[str, str] | None = None  # (field, value) -> required iff fm[field]==value


# universal core — on every non-exempt doc (cursor-rule excepted, handled specially)
UNIVERSAL_CORE: list[FieldSpec] = [
    FieldSpec("doc_type", Req.R, "enum", DOC_TYPES),
    FieldSpec("title", Req.R, "scalar"),
    FieldSpec("summary", Req.R, "scalar"),
    FieldSpec("status", Req.R, "status"),
    FieldSpec("nature", Req.R, "enum", NATURE),
    FieldSpec("asset_group", Req.R, "enum_list", ASSET_GROUP),
    FieldSpec("stage", Req.R, "enum_list", STAGE),
    FieldSpec("repos", Req.R, "registry", registry="repos"),
    FieldSpec("scope", Req.R, "enum_list", SCOPE),
    FieldSpec("tags", Req.R, "free_list"),
    FieldSpec("related", Req.R, "free_list"),
    FieldSpec("created", Req.R, "date"),
]

PER_TYPE: dict[str, list[FieldSpec]] = {
    "plan": [
        FieldSpec("parent_epic", Req.R, "registry", registry="epic"),
        FieldSpec("assigned_vm", Req.R, "registry_or_na", registry="vm"),
        FieldSpec("execution_scope", Req.R, "enum", EXECUTION_SCOPE),
        FieldSpec("priority", Req.R, "enum", PRIORITY),
        FieldSpec("estimate_class", Req.R, "enum", ESTIMATE_CLASS),
        FieldSpec("estimate_baseline_ai_days", Req.R, "scalar"),
        FieldSpec("estimate_calibrated_ai_days", Req.R, "scalar"),
        FieldSpec("last_updated", Req.O, "date"),
        FieldSpec("locked_by", Req.O, "scalar"),
        FieldSpec("locked_since", Req.O, "scalar"),
        FieldSpec("supersedes", Req.O, "free_list"),
        FieldSpec("superseded_by", Req.O, "free_list"),
        FieldSpec("depends_on", Req.O, "free_list"),
        FieldSpec("source", Req.O, "scalar"),
    ],
    "epic": [
        FieldSpec("name", Req.R, "scalar"),
        FieldSpec("tier", Req.R, "enum", TIER),
        FieldSpec("priority", Req.R, "enum", PRIORITY),
        FieldSpec("assigned_vm", Req.R, "registry_or_na", registry="vm"),
        FieldSpec("parent", Req.R, "scalar"),
        FieldSpec("co_operators", Req.O, "free_list"),
        FieldSpec("codex_ssots", Req.O, "free_list"),
        FieldSpec("related_plans", Req.O, "free_list"),
    ],
    "issue": [
        FieldSpec("parent_epic", Req.R, "registry", registry="epic"),
        FieldSpec("priority", Req.R, "enum", PRIORITY),
        FieldSpec("source", Req.R, "free_list"),
        FieldSpec("assigned_vm", Req.O, "registry_or_na", registry="vm"),
        FieldSpec("resolved_by", Req.C, "scalar", conditional_on=("status", "resolved")),
        FieldSpec("locked_by", Req.O, "scalar"),
    ],
    "audit-result": [
        FieldSpec("audited_scope", Req.R, "scalar"),
        FieldSpec("date", Req.R, "date"),
        FieldSpec("auditor", Req.R, "scalar"),
        FieldSpec("parent_epic", Req.R, "registry", registry="epic"),
        FieldSpec("severity", Req.R, "enum", SEVERITY_P),
        FieldSpec("resulting_plan", Req.O, "scalar"),
        FieldSpec("lib_version", Req.O, "scalar"),
        FieldSpec("doc_versions_checked", Req.O, "free_list"),
    ],
    "audit-instruction": [
        FieldSpec("tier", Req.R, "enum", TIER),
        FieldSpec("parent_epic", Req.R, "registry", registry="epic"),
        FieldSpec("cadence", Req.R, "scalar"),
        FieldSpec("verifier", Req.O, "scalar"),
        FieldSpec("lifespan", Req.O, "scalar"),
    ],
    "codex-ssot": [
        FieldSpec("authoritative_for", Req.R, "free_list"),
        FieldSpec("referenced_by", Req.O, "free_list"),
        FieldSpec("owner", Req.O, "scalar"),
        FieldSpec("last_reviewed", Req.O, "date"),
        FieldSpec("code_refs", Req.O, "free_list"),
    ],
    "codex-runbook": [
        FieldSpec("owner", Req.R, "scalar"),
        FieldSpec("cadence", Req.R, "scalar"),
        FieldSpec("verifier", Req.R, "scalar"),
        FieldSpec("last_executed", Req.O, "scalar"),
        FieldSpec("code_refs", Req.O, "free_list"),
    ],
    "agent-role": [
        FieldSpec("role", Req.R, "scalar"),
        FieldSpec("does", Req.R, "free_list"),
        FieldSpec("does_not", Req.R, "free_list"),
        FieldSpec("triggers", Req.R, "free_list"),
        FieldSpec("scope_tools", Req.O, "free_list"),
        FieldSpec("reports_to", Req.O, "scalar"),
    ],
    "cursor-rule": [],  # special-cased in validate_frontmatter
}


@dataclass(frozen=True)
class Violation:
    field: str
    severity: Sev
    message: str


# ----------------------------------------------------------------------------- registries
@dataclass
class Registries:
    vms: frozenset[str]
    epics: frozenset[str]
    repos: frozenset[str]
    epic_vms: dict[str, str] = field(default_factory=dict)  # epic slug -> its assigned_vm (for plan inheritance)


def load_registries(pm_root: Path) -> Registries:
    """Load the live registries the validator checks against (vm ids, epic slugs+vms, repo names)."""
    vms: set[str] = {"NA"}
    reg = pm_root / "orchestrator_vm_registry.yaml"
    if reg.exists():
        data = yaml.safe_load(reg.read_text()) or {}
        for vm in data.get("vms") or []:
            if isinstance(vm, dict) and vm.get("id"):
                vms.add(str(vm["id"]))
    epics: set[str] = set()
    epic_vms: dict[str, str] = {}
    epics_dir = pm_root / "plans" / "epics"
    if epics_dir.is_dir():
        for p in epics_dir.glob("*.md"):
            if p.name == "README.md":
                continue
            epics.add(p.stem)
            efm, _ = parse_frontmatter(p.read_text())
            if efm and efm.get("assigned_vm"):
                epic_vms[p.stem] = str(efm["assigned_vm"])
    repos: set[str] = set()
    manifest = pm_root / "workspace-manifest.json"
    if manifest.exists():
        m = json.loads(manifest.read_text())
        repos_obj = m.get("repositories") or {}
        repos.update(repos_obj.keys() if isinstance(repos_obj, dict) else repos_obj)
    return Registries(frozenset(vms), frozenset(epics), frozenset(repos), epic_vms)


# ----------------------------------------------------------------------------- helpers
def _is_empty(v: object) -> bool:
    if v is None or v == [] or v == {}:
        return True
    return isinstance(v, str) and v.strip() == ""


def _as_list(v: object) -> list:
    return v if isinstance(v, list) else [v]


# Files whitelisted as data — they carry no frontmatter (§9 of the schema SSOT).
EXEMPT_BASENAMES = frozenset({"README.md", "INDEX.md", "ROADMAP.md", "roadmap.md", "PLAN_FORMAT.md"})


def is_exempt(path: str) -> bool:
    name = Path(path).name
    return (
        name in EXEMPT_BASENAMES
        or name.startswith("_")  # ledgers / pings (e.g. _agent_pings.md) — data, not docs
        or name.upper().endswith("INDEX.MD")  # navigational index docs (INDEX.md, 00-SSOT-INDEX.md)
    )


def doc_type_for_path(path: str) -> str | None:
    """Derive doc_type from a doc's location (the keystone discriminator). Accepts relative or absolute."""
    p = str(Path(path).resolve()).replace("\\", "/")
    if "/plans/epics/" in p:
        return "epic"
    if "/plans/active/issues/" in p:
        return "issue"
    if "/plans/active/" in p:
        return "plan"
    if "/plans/audit/results/" in p:
        return "audit-result"
    if "/plans/audit/instructions/" in p:
        return "audit-instruction"
    if "agent-orchestrator/agents/" in p:
        return "agent-role"
    if p.endswith(".mdc") or "/.cursor/rules/" in p:
        return "cursor-rule"
    if "/codex/15-runbooks/" in p:
        return "codex-runbook"
    if "/codex/" in p:
        return "codex-ssot"
    return None


def parse_frontmatter(text: str) -> tuple[dict | None, str]:
    """Return (frontmatter_dict, body). frontmatter_dict is None when there is no `---` block."""
    if not text.startswith("---"):
        return None, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, text
    fm = yaml.safe_load(parts[1])
    if not isinstance(fm, dict):
        fm = {}
    return fm, parts[2]


# ----------------------------------------------------------------------------- value validation
def _validate_value(spec: FieldSpec, v: object, reg: Registries, doc_type: str) -> list[Violation]:
    out: list[Violation] = []
    # the `NA` literal is meaningful ONLY for assigned_vm; elsewhere it is the retired sentinel
    if spec.kind != "registry_or_na" and isinstance(v, str) and v.strip() == "NA":
        out.append(Violation(spec.name, Sev.SOFT, "literal 'NA' — normalize to null / [] (empty convention)"))
        return out
    if spec.kind == "enum":
        if v not in (spec.enum or frozenset()):
            out.append(Violation(spec.name, Sev.HARD, f"'{v}' not in {sorted(spec.enum or [])}"))
    elif spec.kind == "status":
        # status is a closed enum but the existing corpus uses many ad-hoc values; normalizing is a
        # CONTENT decision (deferred content pass), so a mismatch is SOFT during the soak, not HARD.
        allowed = STATUS_BY_TYPE.get(doc_type)
        if allowed is not None and v not in allowed:
            out.append(Violation(spec.name, Sev.SOFT, f"'{v}' not in {doc_type} status {sorted(allowed)} — normalize"))
    elif spec.kind == "enum_list":
        for el in _as_list(v):
            if el not in (spec.enum or frozenset()):
                out.append(Violation(spec.name, Sev.HARD, f"'{el}' not in {sorted(spec.enum or [])}"))
    elif spec.kind == "registry_or_na":
        if v not in reg.vms:
            out.append(Violation(spec.name, Sev.HARD, f"'{v}' not a registry vm-id or NA"))
    elif spec.kind == "registry" and spec.registry == "epic":
        if v not in reg.epics:
            out.append(Violation(spec.name, Sev.HARD, f"parent_epic '{v}' not an epic slug"))
    elif spec.kind == "registry" and spec.registry == "repos":
        for el in _as_list(v):
            if el not in reg.repos:
                out.append(Violation(spec.name, Sev.SOFT, f"repo '{el}' not in workspace-manifest"))
    elif spec.kind == "date":
        s = str(v)
        if not (len(s) >= 10 and s[4] == "-" and s[7] == "-" and s[:4].isdigit()):
            out.append(Violation(spec.name, Sev.SOFT, f"'{v}' not YYYY-MM-DD"))
    return out


def validate_frontmatter(doc_type: str | None, fm: dict, reg: Registries) -> list[Violation]:
    """The three-state validator. Returns all violations (HARD + SOFT)."""
    if doc_type is None:
        return [Violation("doc_type", Sev.HARD, "unknown doc_type (path not recognized)")]
    if doc_type == "cursor-rule":
        if fm.get("doc_type") != "cursor-rule":
            return [Violation("doc_type", Sev.HARD, "cursor-rule must carry doc_type: cursor-rule")]
        return []
    specs = UNIVERSAL_CORE + PER_TYPE.get(doc_type, [])
    out: list[Violation] = []
    for spec in specs:
        req = spec.req
        if req == Req.C and spec.conditional_on is not None:
            cf, cv = spec.conditional_on
            req = Req.R if fm.get(cf) == cv else Req.O
        if spec.name not in fm:
            if req == Req.R:
                out.append(Violation(spec.name, Sev.HARD, "required key missing"))
            else:
                out.append(Violation(spec.name, Sev.SOFT, "optional key absent — add present-but-empty"))
            continue
        v = fm[spec.name]
        if _is_empty(v):
            if spec.name == "assigned_vm" and req == Req.R:
                out.append(Violation(spec.name, Sev.HARD, "empty — set a vm-id or NA"))
            elif req == Req.R:
                out.append(Violation(spec.name, Sev.SOFT, "required but empty — needs content"))
            # an empty OPTIONAL field (incl. an optional assigned_vm on an issue) is fine
            continue
        out += _validate_value(spec, v, reg, doc_type)
    return out


# ----------------------------------------------------------------------------- CLI
def _pm_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate documentation frontmatter against the schema SSOT.")
    ap.add_argument("--check", nargs="+", required=True, help="doc path(s) to validate")
    ap.add_argument("--doc-type", help="override the path-derived doc_type")
    ap.add_argument("--soft", action="store_true", help="also print SOFT (needs-content) violations")
    args = ap.parse_args(argv)
    reg = load_registries(_pm_root())
    hard_total = 0
    for path in args.check:
        if is_exempt(path):
            print(f"-- {path}  EXEMPT (no frontmatter required)")
            continue
        dt = args.doc_type or doc_type_for_path(path)
        text = Path(path).read_text()
        fm, _ = parse_frontmatter(text)
        if fm is None:
            print(f"✗ {path}  [{dt}]  NO FRONTMATTER")
            hard_total += 1
            continue
        vs = validate_frontmatter(dt, fm, reg)
        hard = [v for v in vs if v.severity == Sev.HARD]
        soft = [v for v in vs if v.severity == Sev.SOFT]
        hard_total += len(hard)
        mark = "✓" if not hard else "✗"
        print(f"{mark} {path}  [{dt}]  hard={len(hard)} soft={len(soft)}")
        for v in hard:
            print(f"    HARD  {v.field}: {v.message}")
        if args.soft:
            for v in soft:
                print(f"    soft  {v.field}: {v.message}")
    return 1 if hard_total else 0


if __name__ == "__main__":
    sys.exit(main())
