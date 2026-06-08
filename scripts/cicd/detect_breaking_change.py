#!/usr/bin/env python3
"""Content-based breaking-change detector for the CI/CD breaking-gate.

Replaces the version-phase heuristic (`bump_type == minor on a 0.x repo`) and the
crude `git diff __init__.py | grep '^-'` text-diff that flagged ANY removed line —
including reformatting, import reordering, and docstring edits — as "breaking".

A change is BREAKING only if the **public API / schema surface** changed in a way
that can break a consumer's import or call:

  * a public exported name (in ``__all__`` or a public top-level def/class) was
    removed or renamed;
  * a public function/method signature changed incompatibly (a required parameter
    added, a parameter removed/renamed, positional order changed, ``*args``/``**kwargs``
    dropped);
  * a public class was removed, or a public method on it was removed;
  * a Pydantic/dataclass FIELD (annotated class attribute) was removed, renamed, or
    its type annotation changed (schema/contract surface — the UAC case);
  * an HTTP route (``@app.get`` / ``@router.post`` …) was removed.

NOT breaking: added names, added *optional* (defaulted) parameters, added methods,
added fields, docstring/comment/body changes, reformatting, reordering.

Stdlib-only (``ast`` + ``subprocess`` + ``git``) — no external dependency so it can
run inside any repo's semver-agent job without a fleet-wide pin.

Usage (inside a checked-out repo):
    detect_breaking_change.py --source-dir <pkg_dir> --base-ref <sha> --head-ref HEAD [--json]

Exit code is always 0 (the verdict is the payload). Prints ``is_breaking=true|false``
on the last stdout line so a shell can ``tail -1``; with ``--json`` prints a full report.
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from dataclasses import dataclass, field
from typing import cast


def _git_show(ref: str, path: str) -> str | None:
    """Return file content at ``ref:path`` or None if it does not exist there."""
    try:
        return subprocess.check_output(
            ["git", "show", f"{ref}:{path}"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except subprocess.CalledProcessError:
        return None


def _git_changed_py(base_ref: str, head_ref: str, source_dir: str) -> list[str]:
    """List .py files under ``source_dir`` that DIFFER between base and head.

    A public-surface change can only originate in a file whose content changed (or was
    added/removed) — so we only need to parse the changed set, not the whole repo. This
    keeps the differ fast (a handful of files per promotion) instead of forking ``git
    show`` over thousands of unchanged files.
    """
    try:
        out = subprocess.check_output(
            ["git", "diff", "--name-only", f"{base_ref}..{head_ref}", "--", source_dir],
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except subprocess.CalledProcessError:
        return []
    return sorted({ln for ln in out.splitlines() if ln.endswith(".py")})


@dataclass
class Signature:
    """A back-compat-relevant view of a callable signature."""

    posonly: list[str] = field(default_factory=list)
    args: list[str] = field(default_factory=list)
    required: list[str] = field(default_factory=list)  # params with NO default
    kwonly_required: list[str] = field(default_factory=list)
    has_vararg: bool = False
    has_kwarg: bool = False

    @classmethod
    def from_node(cls, node: ast.FunctionDef | ast.AsyncFunctionDef) -> Signature:
        a = node.args
        posonly = [p.arg for p in a.posonlyargs]
        args = [p.arg for p in a.args]
        ndef = len(a.defaults)
        positional = posonly + args
        required = positional[: len(positional) - ndef] if ndef else positional
        # drop conventional self/cls for methods
        required = [r for r in required if r not in ("self", "cls")]
        kwonly_required = [
            p.arg for p, d in zip(a.kwonlyargs, a.kw_defaults, strict=False) if d is None
        ]
        return cls(
            posonly=posonly,
            args=[x for x in args if x not in ("self", "cls")],
            required=required,
            kwonly_required=kwonly_required,
            has_vararg=a.vararg is not None,
            has_kwarg=a.kwarg is not None,
        )

    def breaks_from(self, old: Signature) -> str | None:
        """Return a reason string if going old->self is backward-incompatible."""
        # a new REQUIRED positional/keyword param breaks existing callers
        new_required = [r for r in self.required if r not in old.required]
        # filter: a genuinely new required positional is breaking; but if the param
        # merely moved from optional->required keep it; both are breaking.
        added_required = [r for r in self.required if r not in old.args and r not in old.required]
        if added_required:
            return f"added required parameter(s) {added_required}"
        new_kwonly_req = [r for r in self.kwonly_required if r not in old.kwonly_required]
        if new_kwonly_req:
            return f"added required keyword-only parameter(s) {new_kwonly_req}"
        # a removed param that callers may pass positionally/by-keyword
        removed = [a for a in (old.required + old.args) if a not in (self.required + self.args)]
        if removed and not self.has_kwarg:
            return f"removed parameter(s) {removed}"
        # positional order change of the shared required prefix
        shared = [r for r in old.required if r in self.required]
        if shared != [r for r in self.required if r in old.required]:
            return "reordered required positional parameters"
        # dropping **kwargs / *args that old accepted
        if old.has_kwarg and not self.has_kwarg:
            return "dropped **kwargs"
        if old.has_vararg and not self.has_vararg:
            return "dropped *args"
        _ = new_required  # kept for clarity; subsumed by added_required
        return None


@dataclass
class PublicSurface:
    exports: set[str] = field(default_factory=set)  # __all__ / public top-level names
    functions: dict[str, Signature] = field(default_factory=dict)  # qualname -> sig
    classes: set[str] = field(default_factory=set)
    methods: dict[str, Signature] = field(default_factory=dict)  # Class.method -> sig
    fields: dict[str, str] = field(default_factory=dict)  # Class.field -> annotation
    routes: set[str] = field(default_factory=set)  # "GET /path" decorators


def _annotation_str(node: ast.AST | None) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:
        return "?"


def _route_decorators(node: ast.AST) -> set[str]:
    routes: set[str] = set()
    decorators: list[ast.expr] = cast(
        "list[ast.expr]", getattr(node, "decorator_list", [])
    )
    for dec in decorators:
        if (
            isinstance(dec, ast.Call)
            and isinstance(dec.func, ast.Attribute)
            and dec.func.attr in ("get", "post", "put", "delete", "patch")
        ):
            val = dec.func.value
            base = getattr(val, "id", getattr(val, "attr", ""))
            if base in ("app", "router"):
                path = ""
                if dec.args and isinstance(dec.args[0], ast.Constant):
                    path = str(dec.args[0].value)
                routes.add(f"{dec.func.attr.upper()} {path}")
    return routes


def extract_surface(source: str, module: str) -> PublicSurface:
    """Extract the public API surface of one module's source text."""
    surf = PublicSurface()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return surf

    # __all__ if declared
    declared_all: set[str] | None = None
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for tgt in node.targets:
            if (
                isinstance(tgt, ast.Name)
                and tgt.id == "__all__"
                and isinstance(node.value, (ast.List, ast.Tuple, ast.Set))
            ):
                declared_all = {
                    e.value
                    for e in node.value.elts
                    if isinstance(e, ast.Constant) and isinstance(e.value, str)
                }

    # Keyed by BARE name (not module-qualified) so a symbol MOVED between internal
    # modules — while staying exported — is not mistaken for a removal (it has the same
    # bare key in both refs). Collisions across modules are rare for public symbols and,
    # for a breaking GATE, err harmlessly toward "run SIT".
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                surf.functions[node.name] = Signature.from_node(node)
                surf.exports.add(node.name)
            surf.routes |= _route_decorators(node)
        elif isinstance(node, ast.ClassDef):
            if node.name.startswith("_"):
                continue
            surf.classes.add(node.name)
            surf.exports.add(node.name)
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not item.name.startswith("_") or item.name in ("__init__",):
                        surf.methods[f"{node.name}.{item.name}"] = Signature.from_node(item)
                    surf.routes |= _route_decorators(item)
                elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    fname = item.target.id
                    if not fname.startswith("_"):
                        surf.fields[f"{node.name}.{fname}"] = _annotation_str(item.annotation)
        elif isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and not tgt.id.startswith("_") and tgt.id != "__all__":
                    surf.exports.add(tgt.id)

    # If __all__ is declared, the export surface is exactly it (the intentional public API)
    if declared_all is not None:
        surf.exports = declared_all
    return surf


def merge(a: PublicSurface, b: PublicSurface) -> PublicSurface:
    out = PublicSurface()
    out.exports = a.exports | b.exports
    out.functions = {**a.functions, **b.functions}
    out.classes = a.classes | b.classes
    out.methods = {**a.methods, **b.methods}
    out.fields = {**a.fields, **b.fields}
    out.routes = a.routes | b.routes
    return out


def surface_at(ref: str, paths: list[str]) -> PublicSurface:
    """Build the public surface at ``ref`` restricted to the given changed ``paths``."""
    surf = PublicSurface()
    for path in paths:
        content = _git_show(ref, path)
        if content is None:
            continue  # file absent at this ref (added at head / removed at head)
        module = path.replace("/", ".").removesuffix(".py")
        surf = merge(surf, extract_surface(content, module))
    return surf


def diff_surfaces(old: PublicSurface, new: PublicSurface) -> list[str]:
    """Return a list of BREAKING reasons (empty == non-breaking)."""
    reasons: list[str] = []

    # 1) Export-name set is the authoritative public API a consumer imports. A name gone
    #    from the union public surface (was public, now absent everywhere scanned) = breaking.
    removed_exports = sorted(old.exports - new.exports)
    if removed_exports:
        reasons.append(f"removed public export(s): {removed_exports}")

    # 2) A public class that disappeared AND is no longer exported anywhere = removed
    #    (a class merely MOVED between modules keeps its bare key + export → not flagged).
    removed_classes = sorted((old.classes - new.classes) - new.exports)
    if removed_classes:
        reasons.append(f"removed public class(es): {removed_classes}")

    # 3) Signature changes of symbols present in BOTH refs (real incompatible change,
    #    not a move). A function gone but still exported (moved) is ignored here.
    for name, old_sig in sorted(old.functions.items()):
        new_sig = new.functions.get(name)
        if new_sig is None:
            if name in new.exports:
                continue  # moved, still exported
            reasons.append(f"removed public function: {name}")
            continue
        why = new_sig.breaks_from(old_sig)
        if why:
            reasons.append(f"function {name}: {why}")

    for qual, old_sig in sorted(old.methods.items()):
        cls = qual.split(".", 1)[0]
        new_sig = new.methods.get(qual)
        if new_sig is None:
            # only a real removal if the owning class is still public (else class-level move/removal covers it)
            if cls in new.exports or cls in new.classes:
                reasons.append(f"removed public method: {qual}")
            continue
        why = new_sig.breaks_from(old_sig)
        if why:
            reasons.append(f"method {qual}: {why}")

    # 4) Schema/contract fields (the UAC case): a removed/renamed/retyped field on a class
    #    still present is a contract break.
    removed_fields = sorted(set(old.fields) - set(new.fields))
    removed_fields = [f for f in removed_fields if f.split(".", 1)[0] in (new.exports | new.classes)]
    if removed_fields:
        reasons.append(f"removed schema field(s): {removed_fields}")
    for qual in sorted(set(old.fields) & set(new.fields)):
        if old.fields[qual] != new.fields[qual]:
            reasons.append(f"changed field type {qual}: {old.fields[qual]!r} -> {new.fields[qual]!r}")

    removed_routes = sorted(old.routes - new.routes)
    if removed_routes:
        reasons.append(f"removed HTTP route(s): {removed_routes}")

    return reasons


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-dir", required=True, help="package dir, e.g. unified_trading_library")
    ap.add_argument("--base-ref", required=True, help="git ref of the promoted/previous version")
    ap.add_argument("--head-ref", default="HEAD")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()
    source_dir = cast(str, args.source_dir)
    base_ref = cast(str, args.base_ref)
    head_ref = cast(str, args.head_ref)
    as_json = cast(bool, args.as_json)

    changed = _git_changed_py(base_ref, head_ref, source_dir)
    # Always include the package top-level __init__.py — it is the authoritative declared
    # public API (__all__); the export-set diff is the primary breaking signal even when
    # __init__.py itself did not change in this promotion.
    init_py = f"{source_dir.rstrip('/')}/__init__.py"
    scan = sorted(set(changed) | {init_py})
    old = surface_at(base_ref, scan)
    new = surface_at(head_ref, scan)
    reasons = diff_surfaces(old, new)
    is_breaking = bool(reasons)

    if as_json:
        print(
            json.dumps(
                {
                    "is_breaking": is_breaking,
                    "reasons": reasons,
                    "base_ref": base_ref,
                    "head_ref": head_ref,
                    "source_dir": source_dir,
                    "old_export_count": len(old.exports),
                    "new_export_count": len(new.exports),
                },
                indent=2,
            )
        )
    else:
        if reasons:
            print("BREAKING — public-surface changes:")
            for r in reasons:
                print(f"  - {r}")
        else:
            print("non-breaking — no public API/schema surface change detected")
        print(f"is_breaking={'true' if is_breaking else 'false'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
