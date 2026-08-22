#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""
One-time script: extract API key env vars from .env / .env.local across the workspace
and write them to api_keys at the workspace root for validation before Secret Manager.

Usage: from workspace root:
  python unified-trading-pm/scripts/extract_api_keys.py
  or: uv run unified-trading-pm/scripts/extract_api_keys.py

Output: api_keys at workspace root. Do not commit this file; add api_keys to .gitignore if the root is ever a repo.
"""

import re
from pathlib import Path

# Workspace root = parent of unified-trading-pm
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_FILE = WORKSPACE_ROOT / "api_keys"

# Relative paths to .env and .env.local under workspace (all KEY=value pairs are extracted, no allowlist)
ENV_PATHS = [
    "deployment-service/.env",
    "deployment-service/.env.local",
    "deployment-api/.env",
    "deployment-api/.env.local",
    "execution-analytics-ui/.env",
    "execution-analytics-ui/.env.local",
    "market-data-processing-service/.env",
    "execution-service/.env",
    "unified-trading-services/.env",
    "instruments-service/.env",
    "market-tick-data-service/.env",
    "features-volatility-service/.env",
    "features-delta-one-service/.env",
    "features-calendar-service/.env",
    "features-onchain-service/.env",
    "ml-inference-service/.env",
    "ml-training-service/.env",
    "strategy-service/.env",
    "trading-analytics-ui/.env",
    "features-sports-service/.env",
]


def parse_env_file(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return out
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"([A-Za-z_][A-Za-z0-9_]*)=(.*)$", line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1].replace('\\"', '"')
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1].replace("\\'", "'")
        if value:
            out[key] = value
    return out


def main() -> None:
    collected: dict[str, str] = {}
    read_files: list[str] = []
    for rel in ENV_PATHS:
        path = WORKSPACE_ROOT / rel
        if not path.exists():
            continue
        read_files.append(rel)
        for k, v in parse_env_file(path).items():
            if k not in collected or v:
                collected[k] = v
    lines = [f"{k}={v}" for k, v in sorted(collected.items())]
    OUTPUT_FILE.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    print(f"Extracted {len(collected)} keys from {len(read_files)} env files -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
