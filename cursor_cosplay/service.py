from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from cursor_cosplay.models import CursorAgentResult


def build_prompt_from_messages(messages: list[dict[str, Any]]) -> str:
    role_names = {
        "system": "System",
        "user": "User",
        "assistant": "Assistant",
        "tool": "Tool",
    }
    parts: list[str] = []
    for message in messages:
        role = role_names.get(message.get("role", "user"), str(message.get("role", "user")).title())
        content = message.get("content", "")
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(str(item.get("text", "")))
            content = "\n".join(text_parts)
        parts.append(f"{role}: {content}".strip())
    return "\n\n".join(parts)


def to_openai_chat_response(result: CursorAgentResult, model: str) -> dict[str, Any]:
    usage = result.usage or {}
    prompt_tokens = usage.get("inputTokens", 0)
    completion_tokens = usage.get("outputTokens", 0)
    return {
        "id": result.request_id or "cursor-cosplay-chatcmpl",
        "object": "chat.completion",
        "created": 0,
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": result.result},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }


def run_cursor_agent(
    *,
    messages: list[dict[str, Any]],
    model: str,
    workspace: str,
    mode: str | None,
    extra_args: list[str] | None = None,
) -> CursorAgentResult:
    prompt = build_prompt_from_messages(messages)
    resolved_workspace = str(Path(workspace).expanduser().resolve())
    cmd = [
        "cursor",
        "agent",
        "--print",
        "--output-format",
        "json",
        "--trust",
        "--workspace",
        resolved_workspace,
    ]
    if mode:
        cmd += ["--mode", mode]
    if model and model != "cursor-agent":
        cmd += ["--model", model]
    if extra_args:
        cmd += extra_args
    cmd.append(prompt)

    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()
    if not stdout:
        raise RuntimeError(f"cursor agent produced no stdout (stderr: {stderr})")

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"cursor agent returned non-JSON output: {stdout}") from exc

    return CursorAgentResult(
        ok=proc.returncode == 0 and not payload.get("is_error", False),
        result=str(payload.get("result", "")).strip(),
        session_id=payload.get("session_id"),
        request_id=payload.get("request_id"),
        usage=payload.get("usage") or {},
        raw={**payload, "stderr": stderr, "exit_code": proc.returncode},
    )
