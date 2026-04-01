# cursor-cosplay

cursor-cosplay is a small OpenAI-compatible proxy that makes `cursor agent` usable as a local `/v1/chat/completions` backend.

It intentionally implements a minimal OpenAI-like subset rather than the full OpenAI API surface.

The name is literal: Cursor is cosplaying as an OpenAI-ish API.

## What it does

- exposes `/health`
- exposes `/v1/models`
- exposes `/v1/chat/completions`
- translates OpenAI-style chat messages into a single prompt for `cursor agent`
- returns an OpenAI-style chat completion response
- can require a bearer token via `CURSOR_COSPLAY_API_KEY`
- can restrict workspaces to a configured root via `CURSOR_COSPLAY_WORKSPACE_ROOT`

## Requirements

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/)
- `cursor` CLI installed and authenticated
- `CURSOR_API_KEY` available for the Cursor CLI if needed by your setup

## Install

```bash
uv sync --extra dev
```

## Run

By default the proxy binds to `127.0.0.1:8765`.

```bash
uv run cursor-cosplay
```

Optional environment variables:

```bash
export CURSOR_COSPLAY_HOST=127.0.0.1
export CURSOR_COSPLAY_PORT=8765
export CURSOR_COSPLAY_API_KEY=<your-key>
export CURSOR_COSPLAY_WORKSPACE_ROOT=$HOME/Code/GH
uv run cursor-cosplay
```

CLI options:

```bash
uv run cursor-cosplay --help
uv run cursor-cosplay --host 127.0.0.1 --port 8765
```

## Example request

```bash
curl http://127.0.0.1:8765/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <your-key>' \
  -d '{
    "model": "cursor-agent",
    "messages": [
      {"role": "system", "content": "Be concise."},
      {"role": "user", "content": "Respond with exactly: HELLO"}
    ]
  }'
```

Example response:

```json
{
  "id": "...",
  "object": "chat.completion",
  "created": 0,
  "model": "cursor-agent",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "HELLO"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 0,
    "completion_tokens": 29,
    "total_tokens": 29
  }
}
```

## Cursor-specific metadata

The request body may include `metadata` values for proxy control:

```json
{
  "model": "cursor-agent",
  "messages": [{"role": "user", "content": "Plan the refactor"}],
  "metadata": {
    "cursor_mode": "plan",
    "workspace": "/home/mark/Code/GH/mamercad/some-repo"
  }
}
```

Supported `cursor_mode` values:
- `plan`
- `ask`

## Development

Run tests:

```bash
uv run python -m pytest -q
```

Run lint:

```bash
uv run ruff check .
```

## Status

Intentionally minimal proxy focused on one-shot `chat/completions` calls to `cursor agent`. Streaming is not implemented.

---

Made with :heart: and :coffee: in Michigan. Copyright (2026) [Emtesseract](https://emtesseract.com).
