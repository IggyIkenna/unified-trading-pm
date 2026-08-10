#!/usr/bin/env python3
"""Filter `codex_rg "except Exception:"` grep hits down to real ExceptHandler
AST nodes, dropping matches that only occur inside a string/comment (e.g. a
generated-code template literal). Reads ripgrep `file:line:content` lines on
stdin, writes the surviving lines to stdout, one per input file parsed once.
"""

import ast
import sys
from pathlib import Path


def real_except_lines(path: str) -> set[int] | None:
    try:
        tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None  # unparsable — fall back to keeping all grep hits for this file
    lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and isinstance(node.type, ast.Name) and node.type.id == "Exception":
            lines.add(node.lineno)
    return lines


def main() -> int:
    cache: dict[str, set[int] | None] = {}
    for raw in sys.stdin:
        line = raw.rstrip("\n")
        parts = line.split(":", 2)
        if len(parts) < 2:
            print(line)
            continue
        path, lineno_str = parts[0], parts[1]
        if path not in cache:
            cache[path] = real_except_lines(path)
        real_lines = cache[path]
        if real_lines is None or int(lineno_str) in real_lines:
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
