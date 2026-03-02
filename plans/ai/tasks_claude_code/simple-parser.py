#!/usr/bin/env python3
"""
Simple parser for agent stream-json output
Shows only important events in clean format
"""

import json
import sys

# Buffer for thinking text
thinking_buffer = []

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue

    try:
        event = json.loads(line)
        event_type = event.get("type")

        # Accumulate thinking deltas
        if event_type == "thinking":
            subtype = event.get("subtype")
            if subtype == "delta":
                text = event.get("text", "")
                thinking_buffer.append(text)
            elif subtype == "completed":
                # Print accumulated thinking
                if thinking_buffer:
                    full_text = "".join(thinking_buffer).strip()
                    if full_text:
                        # Print as complete paragraphs with proper line breaks
                        lines = full_text.split('\n')
                        for line_text in lines:
                            if line_text.strip():
                                # Wrap long lines at 100 chars
                                words = line_text.split()
                                current_line = ""
                                for word in words:
                                    if len(current_line) + len(word) + 1 > 100:
                                        print(f"💭 {current_line}", flush=True)
                                        current_line = word
                                    else:
                                        current_line = f"{current_line} {word}" if current_line else word
                                if current_line:
                                    print(f"💭 {current_line}", flush=True)
                        print("", flush=True)  # Blank line after thinking
                    thinking_buffer = []

        # Show tool calls
        elif event_type == "tool_call" and event.get("subtype") == "started":
            tool_call = event.get("tool_call", {})

            if "readToolCall" in tool_call:
                path = tool_call["readToolCall"]["args"].get("path", "")
                # Show just filename, not full path
                filename = path.split('/')[-1] if '/' in path else path
                print(f"\n📖 Reading: {filename}", flush=True)

            elif "writeToolCall" in tool_call:
                path = tool_call["writeToolCall"]["args"].get("path", "")
                filename = path.split('/')[-1] if '/' in path else path
                print(f"✏️  Writing: {filename}", flush=True)

            elif "shellToolCall" in tool_call:
                cmd = tool_call["shellToolCall"]["args"].get("command", "")
                if len(cmd) > 60:
                    cmd = cmd[:57] + "..."
                print(f"\n🔧 Running: {cmd}", flush=True)

            elif "grepToolCall" in tool_call:
                pattern = tool_call["grepToolCall"]["args"].get("pattern", "")
                if len(pattern) > 50:
                    pattern = pattern[:47] + "..."
                print(f"🔍 Searching: {pattern}", flush=True)

        # Show completion
        elif event_type == "result":
            is_error = event.get("is_error", False)
            if is_error:
                print("❌ Agent failed", flush=True)
            else:
                print("✅ Agent completed", flush=True)

    except (json.JSONDecodeError, KeyError):
        # Skip malformed JSON
        continue
