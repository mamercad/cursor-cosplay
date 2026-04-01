from __future__ import annotations

import argparse
import os

from uvicorn import run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the cursor-cosplay OpenAI-compatible proxy")
    parser.add_argument(
        "--host",
        default=os.getenv("CURSOR_COSPLAY_HOST", "127.0.0.1"),
        help="Bind host (default: CURSOR_COSPLAY_HOST or 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("CURSOR_COSPLAY_PORT", "8765")),
        help="Bind port (default: CURSOR_COSPLAY_PORT or 8765)",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    run("cursor_cosplay.app:create_app", factory=True, host=args.host, port=args.port)
