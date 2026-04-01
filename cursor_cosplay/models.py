from pydantic import BaseModel, Field


class CursorAgentResult(BaseModel):
    ok: bool
    result: str
    session_id: str | None = None
    request_id: str | None = None
    usage: dict = Field(default_factory=dict)
    raw: dict = Field(default_factory=dict)
