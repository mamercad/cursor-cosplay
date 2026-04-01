from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from cursor_cosplay.models import CursorAgentResult
from cursor_cosplay.service import run_cursor_agent, to_openai_chat_response


class ChatCompletionsRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    model: str = "cursor-agent"
    messages: list[dict[str, Any]]
    metadata: dict[str, Any] | None = None


class HealthResponse(BaseModel):
    status: str
    platform: str


class ModelsResponse(BaseModel):
    object: str = "list"
    data: list[dict[str, str]] = Field(
        default_factory=lambda: [
            {"id": "cursor-agent", "object": "model", "owned_by": "cursor-cosplay"}
        ]
    )


def create_app() -> FastAPI:
    app = FastAPI(title="cursor-cosplay")
    api_key = os.getenv("CURSOR_COSPLAY_API_KEY", "")
    workspace_root = os.getenv("CURSOR_COSPLAY_WORKSPACE_ROOT", "")
    workspace_root_path = Path(workspace_root).expanduser().resolve() if workspace_root else None

    def require_auth(authorization: str | None) -> None:
        if not api_key:
            return
        expected = f"Bearer {api_key}"
        if authorization != expected:
            raise HTTPException(status_code=401, detail="Invalid API key")

    def resolve_workspace(metadata: dict[str, Any]) -> str:
        workspace = str(metadata.get("workspace", "."))
        workspace_path = Path(workspace).expanduser().resolve()
        allowed_paths = (workspace_path, *workspace_path.parents)
        if workspace_root_path and workspace_root_path not in allowed_paths:
            raise HTTPException(status_code=403, detail="Workspace outside configured root")
        return str(workspace_path)

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok", platform="cursor-cosplay")

    @app.get("/v1/models", response_model=ModelsResponse)
    def models(authorization: str | None = Header(default=None)) -> ModelsResponse:
        require_auth(authorization)
        return ModelsResponse()

    @app.post("/v1/chat/completions")
    def chat_completions(
        request: ChatCompletionsRequest,
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        require_auth(authorization)
        metadata = request.metadata or {}
        mode = metadata.get("cursor_mode")
        workspace = resolve_workspace(metadata)
        try:
            result: CursorAgentResult = run_cursor_agent(
                messages=request.messages,
                model=request.model,
                workspace=workspace,
                mode=mode,
                extra_args=None,
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        if not result.ok:
            raise HTTPException(status_code=502, detail=result.raw)
        return to_openai_chat_response(result, model=request.model)

    return app
