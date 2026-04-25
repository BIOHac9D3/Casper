## Repo context
- Tech stack: Python 3.11+, Typer CLI, Requests, PyYAML, Rich
- Package manager: pip
- Test runner: pytest
- Lint/typecheck: ruff / mypy (optional)

## Commands (source of truth)
- Install: python -m pip install -r requirements.txt
- Lint: python -m ruff check .
- Typecheck: python -m mypy .
- Unit tests: python -m pytest -q
- Full test suite: python -m pytest
- Build: python cli.py build local

## Codebase conventions
- Error handling: return structured dict responses and raise RuntimeError at CLI boundary for fatal flows.
- Logging: filesystem session logs under memory/logs with UTF-8 text output; never persist secrets.
- Config: YAML target config at configs/targets.yaml + env vars from .env.
- API patterns: adapter classes under agents/ implement BaseAgent.generate(prompt).

## Security posture expectations
- AuthN/AuthZ rules: deployment relies on GitHub + SSH key based access; no password auth.
- Input validation: CLI validates target existence and basic prompt presence.
- Secrets management: API keys only from environment/.env; never committed.
- Dependencies: ask before adding new production deps; prefer stdlib or existing libs.

## Definition of Done
- Tests updated + passing
- No secret leakage
- No breaking changes without explicit instruction
- Clear summary + commands executed in final report
