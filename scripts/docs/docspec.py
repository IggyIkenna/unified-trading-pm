#!/usr/bin/env python3
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
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
import re
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
NATURE = frozenset({"ssot", "guideline", "process", "design", "spec", "record", "notes", "issue"})
ASSET_GROUP = frozenset(
    {"cefi", "defi", "tradfi", "sports", "prediction", "cross-cutting", "ao", "ci", "infrastructure", "ui", "meta"}
)
STAGE = frozenset({"data", "features", "strategy", "backtest", "paper", "live", "execution", "reporting", "meta"})
SCOPE = frozenset({"engineer", "admin", "sales", "prospect", "investor"})
PRIORITY = frozenset({"P0", "P1", "P2", "P3"})
TIER = frozenset({"L0", "L1", "L2", "L3", "L4", "L5"})
ESTIMATE_CLASS = frozenset({"refactor", "design", "infra", "brand-new", "research"})
EXECUTION_SCOPE = frozenset({"orchestrator-agent", "local-only"})
SEVERITY_P = PRIORITY  # audit-result severity is a P0..P3
# archetype implementation-maturity axis (codex/09-strategy/architecture-v2/**) — restored per operator
# decision 2026-07-06 after enum normalization flattened it out of `status:`; elective, archetype docs only
IMPLEMENTATION_STATUS = frozenset({"design", "code-shipped", "stub", "active", "theoretical-only", "live", "complete"})
# agent-role spawn config — schema SSOT is THIS file (the codex mirror was removed 2026-07-15; live per-role data is
# the dashboard Registry tab / GET /api/roles). Enums mirror the AO runtime (models/_types.ModelTier +
# role_registry._VALID_LIFECYCLES): validated here at PM authoring time, consumed there at spawn time.
AGENT_MODEL = frozenset({"opus", "sonnet", "haiku", "fable"})
AGENT_THINKING = frozenset({"max", "high", "medium", "off", "none", "mechanical"})
AGENT_LIFECYCLE = frozenset({"persistent", "one_shot", "scheduled"})
# Sub-tier within model: sonnet ONLY (operator ruling 2026-08-04, mirrors
# model_tier.SONNET_LIGHT_MODEL/SONNET_DEFAULT_MODEL) -- "light" (sonnet-4.6) is the
# default for routine/specified work (target >=80% of AO dispatch); "default"
# (sonnet-5) is for harder/judgment-heavy roles, escalation, and CI. Absent on a
# sonnet role == "light". Meaningless (and left unvalidated) on opus/haiku/fable roles.
AGENT_SONNET_VARIANT = frozenset({"light", "default"})
# Plan-level reasoning-effort override — mirrors agent-orchestrator's
# server/model_tier.py EFFORT_LADDER verbatim (ground truth per this workspace's
# CLAUDE.md § Model tier). `thinking_tier` on a plan reuses AGENT_THINKING above —
# same vocabulary as an agent-role's thinking field, and
# regen_backlog_from_plan._parse_frontmatter_thinking_tier accepts exactly that set
# (max/high/medium/mechanical/off/none) for a plan's `thinking_tier:` too.
PLAN_EFFORT = frozenset({"low", "medium", "high", "xhigh", "max"})

STATUS_BY_TYPE: dict[str, frozenset[str] | None] = {
    "plan": frozenset({"draft", "active", "blocked", "paused", "complete", "superseded", "cancelled"}),
    "epic": frozenset({"active", "paused", "complete", "superseded"}),
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
    E = "elective"  # absent is FINE (no present-but-empty convention); value validated only when present


class Sev(Enum):
    HARD = "hard"
    SOFT = "soft"


@dataclass(frozen=True)
class FieldSpec:
    name: str
    req: Req
    kind: str  # scalar|enum|enum_list|free_list|date|registry|registry_or_na|status
    enum: frozenset[str] | None = None
    registry: str | None = None  # vm|epic|repos|role
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
        FieldSpec("assigned_role", Req.E, "registry", registry="role"),
        FieldSpec("context_scope", Req.E, "free_list"),
        # Reasoning-effort override (elective — most plans rely on assigned_role's
        # derived tier, or the todo-count fallback, and declare neither of these).
        # See PLAN_FORMAT.md's frontmatter block for the full derivation order.
        FieldSpec("effort", Req.E, "enum", PLAN_EFFORT),
        FieldSpec("thinking_tier", Req.E, "enum", AGENT_THINKING),
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
        # blank_assigned_vm_dispatch_classification_gap_2026_07_26.md: was Req.O, which let 58
        # active docs (198 open todos) sit with a genuinely blank assigned_vm -- never classified
        # LOCAL vs AO-dispatchable, structurally eligible for AO pickup the moment someone filled
        # the field in, but invisible to this gate the whole time. NA and planning are both valid
        # values (registry_or_na already accepts NA); blank/absent is not.
        FieldSpec("assigned_vm", Req.R, "registry_or_na", registry="vm"),
        FieldSpec("resolved_by", Req.C, "scalar", conditional_on=("status", "resolved")),
        FieldSpec("locked_by", Req.O, "scalar"),
        FieldSpec("context_scope", Req.E, "free_list"),
        # worker.md §4.5 (FINDINGS CLOSURE, HARD RULE 2026-06-10) mandates author on issue docs.
        # Elective (not Required): only 6 of 444 existing issue docs carry author today
        # (2026-08-04); Required would red the tree. Backfill tracked in the reconciling plan.
        FieldSpec("author", Req.E, "scalar"),
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
        FieldSpec("implementation_status", Req.E, "enum", IMPLEMENTATION_STATUS),
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
        FieldSpec("model", Req.R, "enum", AGENT_MODEL),
        FieldSpec("sonnet_variant", Req.E, "enum", AGENT_SONNET_VARIANT),
        FieldSpec("thinking", Req.E, "enum", AGENT_THINKING),
        FieldSpec("lifecycle", Req.R, "enum", AGENT_LIFECYCLE),
        FieldSpec("does", Req.R, "free_list"),
        FieldSpec("does_not", Req.R, "free_list"),
        FieldSpec("triggers", Req.R, "free_list"),
        FieldSpec("escalation_to", Req.E, "scalar"),
        FieldSpec("temperament_base", Req.E, "scalar"),
        FieldSpec("scope_tools", Req.E, "free_list"),
        FieldSpec("reports_to", Req.E, "scalar"),
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
    roles: frozenset[str] = field(default_factory=frozenset)  # agents/*.md `role:` values


def load_registries(pm_root: Path) -> Registries:
    """Load the live registries the validator checks against (vm ids, epic slugs+vms, repo names, agent roles)."""
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
    roles: set[str] = set()
    agents_dir = pm_root / "agents"
    if agents_dir.is_dir():
        for p in agents_dir.glob("*.md"):
            if p.name == "RULES.md":  # shared boot-rules meta, not a role charter (no `role:` field)
                continue
            afm, _ = parse_frontmatter(p.read_text())
            if afm and afm.get("role"):
                roles.add(str(afm["role"]))
    return Registries(frozenset(vms), frozenset(epics), frozenset(repos), epic_vms, frozenset(roles))


# ----------------------------------------------------------------------------- helpers
_SIBLING_REPOS_CACHE: dict[str, frozenset[str]] = {}


def _sibling_repo_names(pm_root: Path) -> frozenset[str]:
    """The workspace's sibling-repo names, from workspace-manifest.json.

    Used to tell an UNVERIFIABLE cross-repo citation (the sibling repo simply is not checked
    out in this job — e.g. ldr-docs-gate.yml clones ONLY PM) apart from a genuinely DEAD one.
    Reading the manifest, rather than treating "any unrecognised first segment" as a repo,
    is what keeps a typo'd PM-internal path (`plns/foo.md`) a real violation.

    Falls back to an empty set if the manifest is missing/unreadable — which restores the old
    strict behaviour rather than silently passing everything, so a broken manifest cannot turn
    this check off.
    """
    key = str(pm_root)
    cached = _SIBLING_REPOS_CACHE.get(key)
    if cached is not None:
        return cached
    names: frozenset[str] = frozenset()
    try:
        data = json.loads((pm_root / "workspace-manifest.json").read_text())
        repos = data.get("repositories")
        # `repositories` is a dict keyed by repo name (each value a per-repo config object).
        # A plain list of names is accepted too, so this keeps working if that shape ever changes.
        if isinstance(repos, dict):
            names = frozenset(str(k) for k in repos)
        elif isinstance(repos, list):
            names = frozenset(str(r) for r in repos if isinstance(r, str))
    except (OSError, ValueError):
        names = frozenset()
    _SIBLING_REPOS_CACHE[key] = names
    return names


def _is_empty(v: object) -> bool:
    if v is None or v == [] or v == {}:
        return True
    return isinstance(v, str) and v.strip() == ""


def _as_list(v: object) -> list:
    return v if isinstance(v, list) else [v]


# Files whitelisted as data — they carry no frontmatter (§9 of the schema SSOT).
EXEMPT_BASENAMES = frozenset(
    {"README.md", "INDEX.md", "ROADMAP.md", "roadmap.md", "PLAN_FORMAT.md", "RULES.md", "task_template.md"}
)  # RULES.md = shared agent boot-rules meta (the agents/ analogue of CLAUDE.md), not a role charter

# Directory-prefix exemptions (relative to PM root) — a whole family of scratch/spec docs whitelisted
# as data, same rationale as EXEMPT_BASENAMES but keyed on location rather than filename. Scenario
# design specs (scratch_scenarios_day1/*.md) are structured tables feeding the scenario-injection
# harness (codex/04-architecture/scenario-injection-architecture.md), not tracked plans with
# priorities/todos — already treated as frontmatter-free by scripts/plan-hygiene/fix_reference_paths.py.
EXEMPT_DIR_PREFIXES = ("plans/active/scratch_scenarios_day1/",)


def is_exempt(path: str) -> bool:
    name = Path(path).name
    rel = str(path).replace("\\", "/")
    return (
        name in EXEMPT_BASENAMES
        or name.startswith("_")  # ledgers / pings (e.g. _agent_pings.md) — data, not docs
        or name.upper().endswith("INDEX.MD")  # navigational index docs (INDEX.md, 00-SSOT-INDEX.md)
        or any(prefix in rel for prefix in EXEMPT_DIR_PREFIXES)
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
    if "unified-trading-pm/agents/" in p:
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


# Schema-sanctioned valid-empties (doc-frontmatter-schema.md §2/§6): `repos`/`related` are "[] if
# none"; a non-current codex doc (superseded/stale/draft) rightly claims no `authoritative_for`; a
# superseded epic's registry-identity fields are retired identity, not missing content.
_NON_CURRENT_STATUSES = frozenset({"superseded", "stale", "draft"})
_SUPERSEDED_EPIC_EXEMPT = frozenset({"name", "tier", "priority", "parent"})


def _valid_empty(name: str, v: object, fm: dict, doc_type: str) -> bool:
    if name in ("repos", "related") and isinstance(v, list):
        return True
    if name == "authoritative_for" and fm.get("status") in _NON_CURRENT_STATUSES:
        return True
    return doc_type == "epic" and fm.get("status") == "superseded" and name in _SUPERSEDED_EPIC_EXEMPT


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
    elif spec.kind == "registry" and spec.registry == "role":
        if v not in reg.roles:
            msg = f"'{v}' not a role: value under agents/*.md — {sorted(reg.roles)}"
            out.append(Violation(spec.name, Sev.HARD, msg))
    elif spec.kind == "date":
        s = str(v)
        # Full-string match, not a prefix check (2026-07-14, fix_2026_07_30_prek_patch_cache_docspec_date_gap):
        # the OLD prefix-only check (len>=10 + dash positions) only inspected the first 10 chars, so a
        # garbled runaway value like `2026-06-27 "2026-07-30"` — the exact corruption signature from
        # plans/archive/issues/prek_patch_cache_replays_stale_diff_onto_unrelated_files_2026_07_29.md —
        # started with something date-shaped and sailed through undetected, landing corrupted content on
        # origin twice. A plain unquoted YAML date auto-parses to datetime.date, whose str() is always a
        # clean 10-char ISO date, so this tightening does not affect any legitimately-dated doc.
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
            out.append(Violation(spec.name, Sev.SOFT, f"'{v}' not YYYY-MM-DD (full match, not just a prefix)"))
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
    # doc_type is PATH-derived (the keystone discriminator); a declared value that contradicts the
    # path is a lie the enum check can't see (recurring authoring instinct: `doc_type: plan` living
    # in plans/active/issues/ — 3 occurrences by 2026-07-06). Fix the field or move the doc.
    declared = fm.get("doc_type")
    if isinstance(declared, str) and declared in DOC_TYPES and declared != doc_type:
        out.append(
            Violation(
                "doc_type",
                Sev.HARD,
                f"declared '{declared}' contradicts path-derived '{doc_type}' — fix the field or move the doc",
            )
        )
    for spec in specs:
        req = spec.req
        if req == Req.C and spec.conditional_on is not None:
            cf, cv = spec.conditional_on
            req = Req.R if fm.get(cf) == cv else Req.O
        if spec.name not in fm:
            if req == Req.E:
                continue  # elective — absence is not a gap
            if req == Req.R:
                out.append(Violation(spec.name, Sev.HARD, "required key missing"))
            else:
                out.append(Violation(spec.name, Sev.SOFT, "optional key absent — add present-but-empty"))
            continue
        v = fm[spec.name]
        if _is_empty(v):
            if spec.name == "assigned_vm" and req == Req.R:
                out.append(Violation(spec.name, Sev.HARD, "empty — set a vm-id or NA"))
            elif req == Req.R and not _valid_empty(spec.name, v, fm, doc_type):
                out.append(Violation(spec.name, Sev.SOFT, "required but empty — needs content"))
            # an empty OPTIONAL field (incl. an optional assigned_vm on an issue) is fine
            continue
        out += _validate_value(spec, v, reg, doc_type)
    return out


def validate_doc_references(path: Path, fm: dict, doc_type: str) -> list[Violation]:
    """Existence-only check for frontmatter fields that reference OTHER docs by relative path
    (`related`, `codex_ssots`, `supersedes`, `superseded_by`, `depends_on`, `related_plans`,
    `referenced_by`, `doc_versions_checked`, ...) — any `free_list` field, scanned generically.

    Deliberately scoped to PATH-SHAPED entries only (contains '/' and ends `.md`/`.mdc`), e.g.
    `related: [../../codex/foo.md]`. A bare slug (`depends_on: [some_plan_2026_07_01]`) or a
    topic string (`authoritative_for: [quickmerge]`) is NOT resolved — that needs a directory
    search across active/archive/epics with real ambiguity, a different (bigger) problem than
    "does the stated path exist". `code_refs` naturally falls outside this (points at `.py`
    modules, often in a sibling repo not checked out here — the `.md`/`.mdc` filter excludes it
    without needing to special-case the field name).

    Tries four resolutions before flagging, most-specific first:

    1. **Leading-slash, PM-repo-root-relative** (the convention, operator ruling 2026-07-23 —
       `/plans/active/foo.md`, `/codex/02-data/bar.md`; see
       `codex/11-project-management/cross-reference-path-convention.md`). MUST strip the leading
       `/` before joining — `Path(base) / "/plans/foo.md"` silently discards `base` entirely
       (pathlib treats an absolute-shaped RHS as a full replacement, not a join), which would
       otherwise check the filesystem root instead of the repo (caught 2026-07-23: this exact bug
       made every migrated `related:` entry read as "does not exist").
    2. Relative to the referencing doc's own directory (the pre-migration form, e.g. `../../codex/...`).
    3. Relative to the PM root, bare (the pre-migration form, e.g. `codex/...`).
    4. — MEASURED 2026-07-22 against the live corpus: 244 of an initial 336 "broken" hits were
       references to a plan that had since been completed and moved to `plans/archive/**` (a
       normal lifecycle event, not breakage) — a basename search under `plans/archive/**`.

    Only a reference that resolves under NONE of the four is flagged; this keeps the check pointed
    at genuine dead links, not routine archival or a path-join footgun.
    """
    out: list[Violation] = []
    specs = UNIVERSAL_CORE + PER_TYPE.get(doc_type, [])
    pm_root = _pm_root()
    doc_dir = path.resolve().parent
    for spec in specs:
        if spec.kind != "free_list":
            continue
        v = fm.get(spec.name)
        if not isinstance(v, list):
            continue
        for entry in v:
            # Whitespace rules out a path — a free-text sentence that happens to MENTION a path
            # (measured: `authoritative_for` occasionally reads as prose, e.g. "redirect stub —
            # CI/CD flow SSOT is codex/08-workflows/ci-cd-flow.md") is not a reference to resolve.
            if not isinstance(entry, str) or " " in entry or "/" not in entry or not entry.endswith((".md", ".mdc")):
                continue
            if entry.startswith("/"):
                if (pm_root / entry.lstrip("/")).is_file():
                    continue
            elif (doc_dir / entry).is_file() or (pm_root / entry).is_file():
                continue
            if any((pm_root / "plans" / "archive").glob(f"**/{Path(entry).name}")):
                continue
            # 5. Sibling-repo path (e.g. `market-tick-data-service/docs/GCS_PATHS.md`) — this
            # multi-repo workspace checks out sibling repos NEXT TO pm_root, not inside it.
            # context_scope (added 2026-07-30) legitimately cites cross-repo source-path docs
            # this way; the four PM-root-only resolutions above can never resolve those, so
            # every genuinely-real cross-repo doc citation was flagging as dead. Only trust this
            # when the first segment is an actual sibling directory, to avoid silently resolving
            # a typo'd PM-internal path against the wrong root.
            first_segment = entry.split("/", 1)[0]
            workspace_root = pm_root.parent
            if (workspace_root / first_segment).is_dir():
                if (workspace_root / entry).is_file():
                    continue
                # The sibling repo IS checked out and the file genuinely is not there — a real
                # dead reference. Fall through and flag it.
            elif first_segment in _sibling_repo_names(pm_root):
                # The sibling repo is NOT checked out (e.g. ldr-docs-gate.yml's job clones ONLY
                # PM), so this citation is UNVERIFIABLE here, not dead. Flagging it is
                # fail-UNSAFE and produces pure false positives — measured 2026-08-10:
                # ldr-docs-gate went red for 14+ hours on SEVEN citations of
                # instruments-service/docs/*.md files that all exist and are tracked in git,
                # and (because of the separate inherited-`-e` bug) emitted nothing while doing
                # it. Same principle as run_hygiene_sweep.sh's DIFF_BASE_REF guard: when the
                # thing you would compare against is not present, fall back to "cannot verify",
                # never to "violation". The full-QG path DOES clone siblings and still checks
                # these for real, so coverage is not lost — only the PM-only path stops lying.
                # Membership is read from workspace-manifest.json rather than "any unknown first
                # segment", so a typo'd PM-internal path (`plns/foo.md`) is still flagged.
                continue
            out.append(Violation(spec.name, Sev.HARD, f"referenced doc '{entry}' does not exist"))
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
