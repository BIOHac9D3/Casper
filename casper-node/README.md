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
node index.js --help
```


## Termux / Node Entry Point

If you prefer invoking from Node in Termux:

```bash
node index.js --help
node index.js generate "Draft release notes"
node index.js build local
```

`index.js` forwards all arguments to `python3 cli.py` and keeps output streaming to your shell.

## Full Termux Install + Run

### 1) One-shot installer script

```bash
bash scripts/termux_install_run.sh <repo_url> <install_dir>
```

Examples:

```bash
bash scripts/termux_install_run.sh https://github.com/your-org/casper-node.git ~/Casper/casper-node
bash scripts/termux_install_run.sh
```

### 2) Manual install in Termux

```bash
pkg update -y
pkg upgrade -y
pkg install -y git python nodejs openssh

git clone https://github.com/your-org/casper-node.git ~/Casper/casper-node
cd ~/Casper/casper-node

python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
npm install --no-audit --no-fund

cp .env.example .env
# edit .env and add API keys
```

### 3) Run in Termux

```bash
cd ~/Casper/casper-node
source .venv/bin/activate

python cli.py --help
node index.js --help

python cli.py generate "Create a release checklist" --provider openai
python cli.py build local
python cli.py deploy production -m "Deploy from Termux"
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
