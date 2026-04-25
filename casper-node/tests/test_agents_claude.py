from __future__ import annotations


from agents.claude_agent import ClaudeAgent


def test_missing_api_key_returns_error_dict(clean_env, mock_post) -> None:
    agent = ClaudeAgent()
    result = agent.generate("hello")
    assert result == {
        "status": "error",
        "provider": "claude",
        "message": "ANTHROPIC_API_KEY is not set",
    }


def test_success_parses_text_blocks(clean_env, monkeypatch, mock_post) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "key-123")
    json_data = {
        "content": [
            {"type": "text", "text": "hello"},
            {"type": "tool_use", "text": "ignored"},
            {"type": "text", "text": "world"},
        ]
    }
    post = mock_post(status_code=200, json_data=json_data)

    agent = ClaudeAgent()
    result = agent.generate("prompt", model="claude-3-5-sonnet-20241022")

    assert result["status"] == "ok"
    assert result["provider"] == "claude"
    assert result["model"] == "claude-3-5-sonnet-20241022"
    assert result["content"] == "hello\nworld"
    assert result["raw"] == json_data
    post.assert_called_once()


def test_http_error_returns_error_shape(clean_env, monkeypatch, mock_post) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "key-123")
    mock_post(status_code=429, text="rate limited")
    agent = ClaudeAgent()
    result = agent.generate("prompt")

    assert result == {
        "status": "error",
        "provider": "claude",
        "message": "HTTP 429",
        "details": "rate limited",
    }


def test_payload_uses_default_model_when_no_override(clean_env, monkeypatch, mock_post) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "key-123")
    monkeypatch.setenv("ANTHROPIC_MODEL", "custom-model")
    post = mock_post(status_code=200, json_data={"content": []})

    ClaudeAgent().generate("prompt")

    sent_payload = post.call_args.kwargs["json"]
    assert sent_payload["model"] == "custom-model"
    assert sent_payload["messages"] == [{"role": "user", "content": "prompt"}]
    assert sent_payload["max_tokens"] == 800
