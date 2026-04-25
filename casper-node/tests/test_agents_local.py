from __future__ import annotations

from agents.local_agent import LocalAgent


def test_ensure_model_success(clean_env, monkeypatch, mock_post) -> None:
    monkeypatch.setenv("OLLAMA_HOST", "http://example:11434")
    mock_post(status_code=200, json_data={"status": "ready"})

    result = LocalAgent().ensure_model("llama3.2:3b")

    assert result["status"] == "ok"
    assert result["provider"] == "local"
    assert result["model"] == "llama3.2:3b"
    assert result["message"] == "ready"


def test_ensure_model_http_error_includes_model(clean_env, mock_post) -> None:
    mock_post(status_code=500, text="boom")

    result = LocalAgent().ensure_model("llama3.2:3b")

    assert result == {
        "status": "error",
        "provider": "local",
        "model": "llama3.2:3b",
        "message": "HTTP 500",
        "details": "boom",
    }


def test_generate_success(clean_env, mock_post) -> None:
    mock_post(status_code=200, json_data={"response": "hi from llama"})

    result = LocalAgent().generate("prompt", model="qwen2.5:3b")

    assert result["status"] == "ok"
    assert result["provider"] == "local"
    assert result["model"] == "qwen2.5:3b"
    assert result["content"] == "hi from llama"


def test_generate_http_error_includes_model(clean_env, mock_post) -> None:
    mock_post(status_code=400, text="bad")

    result = LocalAgent().generate("prompt", model="qwen2.5:3b")

    assert result == {
        "status": "error",
        "provider": "local",
        "model": "qwen2.5:3b",
        "message": "HTTP 400",
        "details": "bad",
    }


def test_host_strips_trailing_slash(clean_env, monkeypatch, mock_post) -> None:
    monkeypatch.setenv("OLLAMA_HOST", "http://example:11434/")
    post = mock_post(status_code=200, json_data={"response": ""})

    LocalAgent().generate("prompt")

    assert post.call_args.args[0] == "http://example:11434/api/generate"
