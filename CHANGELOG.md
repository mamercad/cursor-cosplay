# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog,
and this project adheres to Semantic Versioning.

## [Unreleased]

### Added
- Initial FastAPI proxy with `/health`, `/v1/models`, and `/v1/chat/completions`
- Translation from OpenAI-style chat messages to one-shot `cursor agent` prompts
- Optional bearer-token protection via `CURSOR_COSPLAY_API_KEY`
- uv/pytest/ruff project setup and smoke-tested Cursor integration
