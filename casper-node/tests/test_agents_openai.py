from __future__ import annotations

from agents.openai_agent import OpenAIAgent


def test_missing_api_key_returns_error_dict(clean_env, mock_post) -> None:
    agent = OpenAIAgent()
    result = agent.generate("hello")
    assert result == {
        "status": "error",
        "provider": "openai",
        "message": "OPENAI_API_KEY is not set",
    }


def test_success_parses_choice_content(clean_env, monkeypatch, mock_post) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    json_data = {"choices": [{"message": {"content": "the answer"}}]}
    mock_post(status_code=200, json_data=json_data)

    agent = OpenAIAgent()
    result = agent.generate("prompt", model="gpt-4o-mini")

    assert result["status"] == "ok"
    assert result["provider"] == "openai"
    assert result["model"] == "gpt-4o-mini"
    assert result["content"] == "the answer"
    assert result["raw"] == json_data


def test_http_error_returns_error_shape(clean_env, monkeypatch, mock_post) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    mock_post(status_code=503, text="upstream down")

    result = OpenAIAgent().generate("prompt")

    assert result == {
        "status": "error",
        "provider": "openai",
        "message": "HTTP 503",
        "details": "upstream down",
    }


def test_payload_includes_temperature_and_auth_header(clean_env, monkeypatch, mock_post) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    post = mock_post(status_code=200, json_data={"choices": [{"message": {"content": "x"}}]})

    OpenAIAgent().generate("prompt")

    sent_payload = post.call_args.kwargs["json"]
    sent_headers = post.call_args.kwargs["headers"]
    assert sent_payload["temperature"] == 0.2
    assert sent_headers["Authorization"] == "Bearer sk-test"
