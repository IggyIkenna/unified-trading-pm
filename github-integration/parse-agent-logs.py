#!/usr/bin/env python3
"""
Parse Cursor Agent stream-json logs into human-readable format
"""

import json
import logging
import sys
from collections.abc import Iterable
from typing import cast

logger = logging.getLogger(__name__)
# ANSI color codes
BLUE = "\033[0;34m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
RED = "\033[0;31m"
GRAY = "\033[0;90m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Type alias for parsed JSON dicts
JsonDict = dict[str, object]


def _get_dict(d: JsonDict, key: str) -> JsonDict:
    """Safely get a nested dict from a dict, returning empty dict if missing."""
    val = d.get(key, {})
    return cast(JsonDict, val) if isinstance(val, dict) else {}


def _get_list(d: JsonDict, key: str) -> list[object]:
    """Safely get a list from a dict, returning empty list if missing."""
    val = d.get(key, [])
    return cast(list[object], val) if isinstance(val, list) else []


def _get_str(d: JsonDict, key: str, default: str = "") -> str:
    """Safely get a string from a dict."""
    val = d.get(key, default)
    return str(val) if val is not None else default


def parse_stream(input_stream: Iterable[str]) -> None:
    """Parse NDJSON stream and output human-readable format"""

    for raw_line in input_stream:
        line = raw_line.strip()
        if not line:
            continue

        try:
            event: JsonDict = cast(JsonDict, json.loads(line))
        except json.JSONDecodeError as e:
            logger.debug("Skipping item due to %s: %s", type(e).__name__, e)
            continue

        event_type = _get_str(event, "type")

        # System init
        if event_type == "system" and _get_str(event, "subtype") == "init":
            model = _get_str(event, "model", "unknown")
            cwd = _get_str(event, "cwd")
            print(f"\n{BLUE}{'=' * 49}{RESET}")
            print(f"{BLUE}Agent Started{RESET}")
            print(f"{GRAY}Model: {model}{RESET}")
            print(f"{GRAY}Working Directory: {cwd}{RESET}")
            print(f"{BLUE}{'=' * 49}{RESET}\n")

        # User message
        elif event_type == "user":
            msg = _get_dict(event, "message")
            content = _get_list(msg, "content")
            if content:
                first = content[0]
                text = _get_str(cast(JsonDict, first), "text") if isinstance(first, dict) else ""
                print(f"{BOLD}User:{RESET}")
                print(f"   {text}\n")

        # Assistant message
        elif event_type == "assistant":
            msg = _get_dict(event, "message")
            content = _get_list(msg, "content")
            if content:
                first = content[0]
                text = _get_str(cast(JsonDict, first), "text") if isinstance(first, dict) else ""
                if text.strip():
                    print(f"{GREEN}Agent:{RESET} {text}")

        # Thinking (reasoning)
        elif event_type == "thinking":
            subtype = _get_str(event, "subtype")
            if subtype == "delta":
                text = _get_str(event, "text")
                if text.strip():
                    print(f"{GRAY}{text.strip()}{RESET}", end="", flush=True)
            elif subtype == "completed":
                print()  # Newline after thinking

        # Tool calls
        elif event_type == "tool_call":
            subtype = _get_str(event, "subtype")
            tool_call = _get_dict(event, "tool_call")

            if subtype == "started":
                # Determine tool type
                if "readToolCall" in tool_call:
                    read_call = _get_dict(tool_call, "readToolCall")
                    read_args = _get_dict(read_call, "args")
                    path = _get_str(read_args, "path")
                    print(f"{YELLOW}Reading: {path}{RESET}")

                elif "writeToolCall" in tool_call:
                    write_call = _get_dict(tool_call, "writeToolCall")
                    write_args = _get_dict(write_call, "args")
                    path = _get_str(write_args, "path")
                    print(f"{YELLOW}Writing: {path}{RESET}")

                elif "shellToolCall" in tool_call:
                    shell_call = _get_dict(tool_call, "shellToolCall")
                    shell_args = _get_dict(shell_call, "args")
                    cmd = _get_str(shell_args, "command")
                    # Truncate long commands
                    if len(cmd) > 80:
                        cmd = cmd[:77] + "..."
                    print(f"{YELLOW}Running: {cmd}{RESET}")

            elif subtype == "completed":
                # Show results for key tools
                if "shellToolCall" in tool_call:
                    shell_call = _get_dict(tool_call, "shellToolCall")
                    result = _get_dict(shell_call, "result")
                    if "success" in result:
                        success = _get_dict(result, "success")
                        stdout = _get_str(success, "stdout")
                        stderr = _get_str(success, "stderr")
                        exit_code_raw = success.get("exitCode", 0)
                        exit_code = int(exit_code_raw) if isinstance(exit_code_raw, (int, float)) else 0

                        if exit_code == 0:
                            print(f"{GREEN}   Success (exit {exit_code}){RESET}")
                        else:
                            print(f"{RED}   Failed (exit {exit_code}){RESET}")

                        # Show important output (quality gates, errors)
                        if "PASSED" in stdout or "FAILED" in stdout:
                            for out_line in stdout.split("\n"):
                                if "PASSED" in out_line or "FAILED" in out_line or "===" in out_line:
                                    print(f"{GRAY}   {out_line}{RESET}")

                        if stderr and stderr.strip():
                            print(f"{RED}   stderr: {stderr[:200]}{RESET}")

                elif "writeToolCall" in tool_call:
                    write_call = _get_dict(tool_call, "writeToolCall")
                    result = _get_dict(write_call, "result")
                    if "success" in result:
                        success = _get_dict(result, "success")
                        lines_raw = success.get("linesCreated", 0)
                        lines_count = int(lines_raw) if isinstance(lines_raw, (int, float)) else 0
                        print(f"{GREEN}   Wrote {lines_count} lines{RESET}")

        # Final result
        elif event_type == "result":
            subtype = _get_str(event, "subtype")
            is_error = bool(event.get("is_error", False))
            duration_raw = event.get("duration_ms", 0)
            duration_ms = float(duration_raw) if isinstance(duration_raw, (int, float)) else 0.0
            duration = duration_ms / 1000

            print(f"\n{BLUE}{'=' * 49}{RESET}")
            if subtype == "success" and not is_error:
                print(f"{GREEN}Agent Completed Successfully{RESET}")
            else:
                print(f"{RED}Agent Failed{RESET}")

            print(f"{GRAY}Duration: {duration:.1f}s{RESET}")
            print(f"{BLUE}{'=' * 49}{RESET}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Read from file
        with open(sys.argv[1]) as f:
            parse_stream(f)
    else:
        # Read from stdin (pipe)
        parse_stream(sys.stdin)
