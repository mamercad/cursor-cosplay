from fastapi.testclient import TestClient

from cursor_cosplay.app import create_app
from cursor_cosplay.models import CursorAgentResult
from cursor_cosplay.service import build_prompt_from_messages, to_openai_chat_response


def test_build_prompt_from_messages_includes_roles_and_content():
    prompt = build_prompt_from_messages(
        [
            {"role": "system", "content": "You are terse."},
            {"role": "user", "content": "Say hello."},
        ]
    )

    assert "System:" in prompt
    assert "You are terse." in prompt
    assert "User:" in prompt
    assert "Say hello." in prompt


def test_to_openai_chat_response_wraps_cursor_result():
    result = CursorAgentResult(
        ok=True,
        result="Hello from Cursor",
        session_id="sess-123",
        request_id="req-456",
        usage={"inputTokens": 10, "outputTokens": 4},
        raw={"type": "result"},
    )

    response = to_openai_chat_response(result, model="cursor-agent")

    assert response["object"] == "chat.completion"
    assert response["model"] == "cursor-agent"
    assert response["choices"][0]["message"]["content"] == "Hello from Cursor"
    assert response["usage"]["prompt_tokens"] == 10
    assert response["usage"]["completion_tokens"] == 4


def test_health_endpoint():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_auth_is_enforced_when_proxy_key_is_set(monkeypatch):
    monkeypatch.setenv("CURSOR_COSPLAY_API_KEY", "secret-key")
    client = TestClient(create_app())

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "cursor-agent",
            "messages": [{"role": "user", "content": "Say hi"}],
        },
    )

    assert response.status_code == 401
    monkeypatch.delenv("CURSOR_COSPLAY_API_KEY", raising=False)


def test_models_endpoint():
    client = TestClient(create_app())

    response = client.get("/v1/models")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"][0]["id"] == "cursor-agent"


def test_models_endpoint_requires_auth_when_proxy_key_is_set(monkeypatch):
    monkeypatch.setenv("CURSOR_COSPLAY_API_KEY", "secret-key")
    client = TestClient(create_app())

    response = client.get("/v1/models")

    assert response.status_code == 401
    monkeypatch.delenv("CURSOR_COSPLAY_API_KEY", raising=False)


def test_chat_completions_endpoint_calls_cursor_runner(monkeypatch):
    client = TestClient(create_app())

    captured = {}

    def fake_run_cursor_agent(*, messages, model, workspace, mode, extra_args=None):
        captured["messages"] = messages
        captured["model"] = model
        captured["workspace"] = workspace
        captured["mode"] = mode
        captured["extra_args"] = extra_args
        return CursorAgentResult(
            ok=True,
            result="Proxy says hi",
            session_id="sess-1",
            request_id="req-1",
            usage={"inputTokens": 7, "outputTokens": 3},
            raw={"type": "result"},
        )

    monkeypatch.setattr("cursor_cosplay.app.run_cursor_agent", fake_run_cursor_agent)

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "cursor-agent",
            "messages": [{"role": "user", "content": "Say hi"}],
        },
    )

    assert response.status_code == 200
    assert captured["model"] == "cursor-agent"
    assert captured["workspace"].endswith("/Code/GH/mamercad/cursor-cosplay")
    assert captured["mode"] is None
    assert response.json()["choices"][0]["message"]["content"] == "Proxy says hi"


def test_chat_completions_rejects_workspace_outside_configured_root(monkeypatch, tmp_path):
    monkeypatch.setenv("CURSOR_COSPLAY_WORKSPACE_ROOT", str(tmp_path))
    client = TestClient(create_app())

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "cursor-agent",
            "messages": [{"role": "user", "content": "Say hi"}],
            "metadata": {"workspace": "/tmp/not-allowed"},
        },
    )

    assert response.status_code == 403
    monkeypatch.delenv("CURSOR_COSPLAY_WORKSPACE_ROOT", raising=False)


def test_chat_completions_supports_plan_mode_via_metadata(monkeypatch):
    client = TestClient(create_app())

    captured = {}

    def fake_run_cursor_agent(*, messages, model, workspace, mode, extra_args=None):
        captured["mode"] = mode
        return CursorAgentResult(
            ok=True,
            result="Plan output",
            session_id="sess-2",
            request_id="req-2",
            usage={"inputTokens": 2, "outputTokens": 2},
            raw={"type": "result"},
        )

    monkeypatch.setattr("cursor_cosplay.app.run_cursor_agent", fake_run_cursor_agent)

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "cursor-agent",
            "messages": [{"role": "user", "content": "Plan it"}],
            "metadata": {"cursor_mode": "plan"},
        },
    )

    assert response.status_code == 200
    assert captured["mode"] == "plan"


def test_chat_completions_returns_502_when_cursor_runner_raises(monkeypatch):
    client = TestClient(create_app())

    def fake_run_cursor_agent(*, messages, model, workspace, mode, extra_args=None):
        raise RuntimeError("cursor exploded")

    monkeypatch.setattr("cursor_cosplay.app.run_cursor_agent", fake_run_cursor_agent)

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "cursor-agent",
            "messages": [{"role": "user", "content": "Say hi"}],
        },
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "cursor exploded"
