# Casper

**AI Agent Orchestration Platform**

Casper is a modular, cloud-agnostic platform for deploying and managing AI agents. It provides a Python backend with a Next.js frontend, Docker containerization, and multi-cloud deployment support (AWS, Azure, GCP).

## Features

- Multi-Agent Workflows: Orchestrate complex tasks across multiple AI models and providers.
- Cloud-Agnostic Deployment: Deploy to AWS, Azure, or GCP with standardized configurations.
- Dockerized Architecture: Containerized backend and frontend for easy deployment.
- Extensible Design: Add new agents, skills, and integrations via modular architecture.
- Monitoring Ready: Built-in support for health checks and observability.

## Architecture

graph TD
    A[Web Frontend] -->|HTTP/HTTPS| B[Python Backend]
    B -->|API Calls| C[OpenAI]
    B -->|API Calls| D[Anthropic]
    B --> E[Database]
    B --> F[Redis Cache]
    G[GitHub Actions] --> B

## Prerequisites

- Docker (v20.10+) and Docker Compose (v2.0+)
- Python 3.12+ (for local development)
- Node.js 18+ (for frontend development)
- Git

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/BIOHac9D3/Casper.git
cd Casper
```

### 2. Configure Environment
```bash
cp casper-node/.env.example .env
nano .env
```

Required environment variables:
- OPENAI_API_KEY: Your OpenAI API key
- ANTHROPIC_API_KEY: Your Anthropic API key

### 3. Run with Docker
```bash
docker-compose up -d
docker-compose logs -f
```

### 4. Access the Application
- Backend: http://localhost:8000
- Frontend: http://localhost:3000

## Project Structure

Casper/
├── casper-node/          # Python backend
│   ├── cli.py             # Main CLI entry point
│   ├── agents/            # AI agent implementations
│   ├── core/              # Core utilities
│   ├── integrations/      # Third-party integrations
│   ├── pipelines/         # Workflow pipelines
│   └── requirements.txt   # Python dependencies
├── web/                  # Next.js frontend
│   ├── app/               # Application pages
│   ├── package.json      # Node.js dependencies
│   └── tsconfig.json      # TypeScript configuration
├── deploy/               # Deployment configurations
│   ├── aws/               # AWS deployment scripts
│   ├── azure/             # Azure deployment scripts
│   └── gcp/               # GCP deployment scripts
├── Dockerfile             # Backend Docker configuration
├── docker-compose.yml     # Multi-container orchestration
├── .dockerignore          # Docker ignore rules
└── README.md