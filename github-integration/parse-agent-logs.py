#!/usr/bin/env python3
"""
Parse Cursor Agent stream-json logs into human-readable format
"""

import json
import logging
import sys

logger = logging.getLogger(__name__)
# ANSI color codes
BLUE = "\033[0;34m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
RED = "\033[0;31m"
GRAY = "\033[0;90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def parse_stream(input_stream):
    """Parse NDJSON stream and output human-readable format"""

    for line in input_stream:
        line = line.strip()
        if not line:
            continue

        try:
            event = json.loads(line)
        except json.JSONDecodeError as e:
            logger.debug("Skipping item due to %s: %s", type(e).__name__, e)
            continue

        event_type = event.get("type")

        # System init
        if event_type == "system" and event.get("subtype") == "init":
            model = event.get("model", "unknown")
            cwd = event.get("cwd", "")
            print(f"\n{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
            print(f"{BLUE}🤖 Agent Started{RESET}")
            print(f"{GRAY}Model: {model}{RESET}")
            print(f"{GRAY}Working Directory: {cwd}{RESET}")
            print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n")

        # User message
        elif event_type == "user":
            content = event.get("message", {}).get("content", [])
            if content:
                text = content[0].get("text", "")
                print(f"{BOLD}👤 User:{RESET}")
                print(f"   {text}\n")

        # Assistant message
        elif event_type == "assistant":
            content = event.get("message", {}).get("content", [])
            if content:
                text = content[0].get("text", "")
                if text.strip():
                    print(f"{GREEN}🤖 Agent:{RESET} {text}")

        # Thinking (reasoning)
        elif event_type == "thinking":
            subtype = event.get("subtype")
            if subtype == "delta":
                text = event.get("text", "")
                if text.strip():
                    print(f"{GRAY}💭 {text.strip()}{RESET}", end="", flush=True)
            elif subtype == "completed":
                print()  # Newline after thinking

        # Tool calls
        elif event_type == "tool_call":
            subtype = event.get("subtype")
            tool_call = event.get("tool_call", {})

            if subtype == "started":
                # Determine tool type
                if "readToolCall" in tool_call:
                    path = tool_call["readToolCall"]["args"]["path"]
                    print(f"{YELLOW}📖 Reading: {path}{RESET}")

                elif "writeToolCall" in tool_call:
                    path = tool_call["writeToolCall"]["args"]["path"]
                    print(f"{YELLOW}✏️  Writing: {path}{RESET}")

                elif "shellToolCall" in tool_call:
                    cmd = tool_call["shellToolCall"]["args"].get("command", "")
                    # Truncate long commands
                    if len(cmd) > 80:
                        cmd = cmd[:77] + "..."
                    print(f"{YELLOW}🔧 Running: {cmd}{RESET}")

            elif subtype == "completed":
                # Show results for key tools
                if "shellToolCall" in tool_call:
                    result = tool_call["shellToolCall"].get("result", {})
                    if "success" in result:
                        stdout = result["success"].get("stdout", "")
                        stderr = result["success"].get("stderr", "")
                        exit_code = result["success"].get("exitCode", 0)

                        if exit_code == 0:
                            print(f"{GREEN}   ✅ Success (exit {exit_code}){RESET}")
                        else:
                            print(f"{RED}   ❌ Failed (exit {exit_code}){RESET}")

                        # Show important output (quality gates, errors)
                        if "PASSED" in stdout or "FAILED" in stdout:
                            for line in stdout.split("\n"):
                                if "PASSED" in line or "FAILED" in line or "===" in line:
                                    print(f"{GRAY}   {line}{RESET}")

                        if stderr and stderr.strip():
                            print(f"{RED}   stderr: {stderr[:200]}{RESET}")

                elif "writeToolCall" in tool_call:
                    result = tool_call["writeToolCall"].get("result", {})
                    if "success" in result:
                        lines = result["success"].get("linesCreated", 0)
                        print(f"{GREEN}   ✅ Wrote {lines} lines{RESET}")

        # Final result
        elif event_type == "result":
            subtype = event.get("subtype")
            is_error = event.get("is_error", False)
            duration = event.get("duration_ms", 0) / 1000

            print(f"\n{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
            if subtype == "success" and not is_error:
                print(f"{GREEN}✅ Agent Completed Successfully{RESET}")
            else:
                print(f"{RED}❌ Agent Failed{RESET}")

            print(f"{GRAY}Duration: {duration:.1f}s{RESET}")
            print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Read from file
        with open(sys.argv[1], "r") as f:
            parse_stream(f)
    else:
        # Read from stdin (pipe)
        parse_stream(sys.stdin)
