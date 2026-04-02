import json
import subprocess

import pytest

from cursor_cosplay.service import build_prompt_from_messages, run_cursor_agent


class CompletedProcessStub:
    def __init__(self, *, stdout="", stderr="", returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def test_build_prompt_from_messages_extracts_text_parts_from_content_list():
    prompt = build_prompt_from_messages(
        [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "hello"},
                    {"type": "image_url", "image_url": {"url": "https://example.com/test.png"}},
                    {"type": "text", "text": "world"},
                ],
            }
        ]
    )

    assert prompt == "User: hello\nworld"


def test_run_cursor_agent_times_out_with_clear_error(monkeypatch):
    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="cursor agent", timeout=kwargs["timeout"])

    monkeypatch.setattr("cursor_cosplay.service.subprocess.run", fake_run)

    with pytest.raises(RuntimeError, match=r"timed out after 300s"):
        run_cursor_agent(
            messages=[{"role": "user", "content": "hello"}],
            model="cursor-agent",
            workspace=".",
            mode=None,
        )


def test_run_cursor_agent_raises_when_stdout_is_empty(monkeypatch):
    monkeypatch.setattr(
        "cursor_cosplay.service.subprocess.run",
        lambda *args, **kwargs: CompletedProcessStub(stdout="", stderr="boom", returncode=1),
    )

    with pytest.raises(RuntimeError, match=r"produced no stdout"):
        run_cursor_agent(
            messages=[{"role": "user", "content": "hello"}],
            model="cursor-agent",
            workspace=".",
            mode=None,
        )


def test_run_cursor_agent_raises_when_stdout_is_not_json(monkeypatch):
    monkeypatch.setattr(
        "cursor_cosplay.service.subprocess.run",
        lambda *args, **kwargs: CompletedProcessStub(stdout="not json", stderr="", returncode=0),
    )

    with pytest.raises(RuntimeError, match=r"returned non-JSON output"):
        run_cursor_agent(
            messages=[{"role": "user", "content": "hello"}],
            model="cursor-agent",
            workspace=".",
            mode=None,
        )


def test_run_cursor_agent_marks_payload_error_as_not_ok(monkeypatch):
    payload = {"result": "bad", "is_error": True, "request_id": "req-1"}
    monkeypatch.setattr(
        "cursor_cosplay.service.subprocess.run",
        lambda *args, **kwargs: CompletedProcessStub(
            stdout=json.dumps(payload),
            stderr="err",
            returncode=0,
        ),
    )

    result = run_cursor_agent(
        messages=[{"role": "user", "content": "hello"}],
        model="cursor-agent",
        workspace=".",
        mode=None,
    )

    assert result.ok is False
    assert result.raw["stderr"] == "err"
    assert result.raw["exit_code"] == 0


def test_run_cursor_agent_passes_mode_model_and_extra_args(monkeypatch, tmp_path):
    captured = {}
    payload = {
        "result": "ok",
        "request_id": "req-2",
        "usage": {"inputTokens": 1, "outputTokens": 1},
    }

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return CompletedProcessStub(stdout=json.dumps(payload), stderr="", returncode=0)

    monkeypatch.setattr("cursor_cosplay.service.subprocess.run", fake_run)

    result = run_cursor_agent(
        messages=[{"role": "user", "content": "hello"}],
        model="gpt-4.1",
        workspace=str(tmp_path),
        mode="plan",
        extra_args=["--force"],
        timeout=123,
    )

    assert result.ok is True
    command = captured["command"]
    assert "cursor agent" in command
    assert "--mode plan" in command
    assert "--model gpt-4.1" in command
    assert "--force" in command
    assert str(tmp_path.resolve()) in command
    assert captured["kwargs"]["shell"] is True
    assert captured["kwargs"]["timeout"] == 123
