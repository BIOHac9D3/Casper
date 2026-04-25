# casper-node

A mobile-first orchestration toolkit for Termux-driven workflows, remote AI agents, and GitHub CI/CD deployment.

## Features

- **CLI control layer** with `generate`, `build`, and `deploy` commands.
- **AI agent adapters** for OpenAI and Anthropic Claude APIs.
- **Remote execution config** for multi-target deploy environments.
- **Pipeline modules** for local build checks and git-based deploy pushes.
- **Memory system** for logs and sessions in filesystem storage.
- **GitHub Actions CI/CD** pipeline with SSH key-based deploy strategy.

## Quick Start

```bash
python -m pip install -r requirements.txt
cp .env.example .env
python cli.py --help
```

## Environment Variables

- `OPENAI_API_KEY`
- `OPENAI_MODEL` (default `gpt-4o-mini`)
- `ANTHROPIC_API_KEY`
- `ANTHROPIC_MODEL` (default `claude-3-5-sonnet-20241022`)

## Usage

```bash
python cli.py generate "Create a release checklist"
python cli.py generate "Summarize latest commit" --provider claude
python cli.py build local
python cli.py deploy production -m "Deploy production release"
```

## Target Configuration

Edit `configs/targets.yaml` to define deploy targets:

- `path`: project root or remote path
- `type`: one of `docker`, `node`, `python`

## CI/CD

Workflow file: `.github/workflows/deploy.yml`

- Triggers on push to `main`
- Installs dependencies
- Runs tests
- Deploys over SSH using repository secrets

Required GitHub secrets:

- `DEPLOY_HOST`
- `DEPLOY_USER`
- `DEPLOY_SSH_KEY`
- `DEPLOY_PATH`
