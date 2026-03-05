# Dependency Alignment Scripts

Scripts to check and validate dependency alignment between pyproject.toml, workspace-manifest.json, and workspace-constraints.toml.

## Workflow

```
1. generate-derived-manifest.py   → derived-dependency-manifest.json (from pyproject.toml)
2. check-dependency-alignment.py  → compare derived vs manifest + canonical
3. validate-dependency-conflicts.py → verify constraints resolve (uv pip compile)
```

## Scripts

| Script                                 | Purpose                                                                                            |
| -------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `generate-derived-manifest.py`         | Extract internal + external deps from all pyproject.toml; output derived-dependency-manifest.json  |
| `check-dependency-alignment.py`        | Compare derived vs workspace-manifest (internal) and canonical-dependency-manifest (external)      |
| `fix-internal-dependency-alignment.py` | Code-use scan: add deps where code imports; remove where not used. Use `--apply` to write changes. |
| `validate-dependency-conflicts.py`     | Run uv pip compile to detect transitive conflicts in workspace-constraints.toml                    |

## Usage

```bash
# Generate derived manifest (run first)
python scripts/manifest/generate-derived-manifest.py

# Check alignment (internal deps vs manifest, external vs canonical)
python scripts/manifest/check-dependency-alignment.py
python scripts/manifest/check-dependency-alignment.py --repo instruments-service
python scripts/manifest/check-dependency-alignment.py --json

# Fix internal alignment (code uses -> add; else remove)
python scripts/manifest/fix-internal-dependency-alignment.py         # dry run
python scripts/manifest/fix-internal-dependency-alignment.py --apply  # apply changes

# Validate constraints resolve (no conflicts)
python scripts/manifest/validate-dependency-conflicts.py
python scripts/manifest/validate-dependency-conflicts.py --regenerate  # regenerate constraints first
```

## Related Scripts

- `scripts/workspace/resolve-canonical-versions.py` — generates workspace-constraints.toml from pyproject.toml
- `scripts/workspace/validate-workspace-constraints.py` — uv pip compile validation
- `scripts/manifest/generate_canonical_dependency_manifest.py` — generates canonical-dependency-manifest.json from workspace-constraints.toml
- `scripts/check_external_dependency_alignment.py` — checks repo pyproject vs canonical-dependency-manifest (external only)
