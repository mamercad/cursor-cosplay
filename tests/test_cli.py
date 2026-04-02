from cursor_cosplay import cli


def test_build_parser_uses_environment_defaults(monkeypatch):
    monkeypatch.setenv("CURSOR_COSPLAY_HOST", "0.0.0.0")
    monkeypatch.setenv("CURSOR_COSPLAY_PORT", "9999")

    parser = cli.build_parser()
    args = parser.parse_args([])

    assert args.host == "0.0.0.0"
    assert args.port == 9999


def test_main_starts_uvicorn_with_factory_app(monkeypatch):
    captured = {}

    def fake_run(app, **kwargs):
        captured["app"] = app
        captured["kwargs"] = kwargs

    monkeypatch.setattr("cursor_cosplay.cli.run", fake_run)
    monkeypatch.setattr("sys.argv", ["cursor-cosplay", "--host", "127.0.0.2", "--port", "8766"])

    cli.main()

    assert captured["app"] == "cursor_cosplay.app:create_app"
    assert captured["kwargs"] == {"factory": True, "host": "127.0.0.2", "port": 8766}
