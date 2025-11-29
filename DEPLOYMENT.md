# OMHC Deployment Guide

Quick setup and deployment guide for the Open Mental Health Collective (OMHC) system.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Deployment to Vertex AI](#deployment-to-vertex-ai)
4. [MCP Server Setup](#mcp-server-setup)
5. [Testing & Validation](#testing--validation)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

- **Python 3.13+** ([Download](https://www.python.org/downloads/))
- **Google Cloud SDK** ([Install gcloud](https://cloud.google.com/sdk/docs/install))
- **Git** (for version control)
- **uv** (Python package manager - recommended) or **pip**

### Google Cloud Platform

1. **GCP Project** with billing enabled
2. **APIs Enabled**:
   - Vertex AI API
   - Cloud Run API (if deploying MCP server)
   - Cloud Logging API
3. **IAM Permissions**:
   - `Vertex AI Admin` or `Agent Engines Admin`
   - `Cloud Run Admin` (if deploying MCP)
   - `Service Account User`

---

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/OMHC.git
cd OMHC
```

### 2. Set Up Python Environment

**Using uv (recommended):**
```bash
# Create virtual environment
python -m venv .venv

# Activate environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
pip install -e ".[dev]"
```

### 3. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

**Required variables in `.env`:**
```bash
# Google API Key (for local development)
GOOGLE_API_KEY=your_google_api_key_here

# GCP Configuration (for deployment)
OMC_GCP_PROJECT_ID=your-gcp-project-id
OMC_GCP_LOCATION=us-central1

# Model Configuration
OMHC_MODEL_NAME=gemini-2.0-flash
```

### 4. Authenticate with Google Cloud

```bash
# Login to Google Cloud
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Set application default credentials
gcloud auth application-default login
```

### 5. Run Tests Locally

```bash
# Run all tests
pytest

# Run only unit tests
pytest tests/unit -v

# Run E2E tests (requires MCP server)
pytest -m e2e -v
```

### 6. Test Locally with ADK

```bash
# Start ADK web interface
adk web --agent-module agents.orchestrator_agent.agent

# Or use the runner directly
python -c "
from agents import root_agent
from google.adk.runners import Runner

runner = Runner(agent=root_agent)
response = runner.run('I need help managing stress')
print(response)
"
```

---

## Deployment to Vertex AI

### 1. Prepare for Deployment

Ensure your `.env` file has deployment variables:

```bash
# Required for deployment
OMC_GCP_PROJECT_ID=your-project-id
OMC_GCP_LOCATION=us-central1
OMHC_MODEL_NAME=gemini-2.0-flash
```

### 2. Run Deployment Script

**Basic deployment:**
```bash
./deploy.sh
```

**Update existing deployment:**
```bash
./deploy.sh --update
```

**Deploy with MCP server:**
```bash
./deploy.sh --with-mcp
```

### 3. Get Agent Resource Name

After deployment, retrieve your agent's resource name:

```bash
# List deployed agents
gcloud ai agent-engines list --location=us-central1

# Output will look like:
# projects/YOUR_PROJECT/locations/us-central1/agentEngines/AGENT_ID
```

### 4. Configure Agent Resource Name

Add the resource name to your `.env`:

```bash
export OMC_AGENT_ENGINE_RESOURCE_NAME="projects/YOUR_PROJECT/locations/us-central1/agentEngines/YOUR_AGENT_ID"
```

Or add to `.env` file:
```bash
echo "OMC_AGENT_ENGINE_RESOURCE_NAME=projects/YOUR_PROJECT/locations/us-central1/agentEngines/YOUR_AGENT_ID" >> .env
```

---

## MCP Server Setup

The MCP (Model Context Protocol) server provides crisis hotline tools to the Resource Connector agent.

### Option 1: Local MCP Server (Development)

```bash
# Start MCP server locally
fastmcp run mcp/omhc_mcp_server.py \
  --host 127.0.0.1 \
  --port 8002 \
  --transport sse

# Set the URL in your environment
export MENTAL_HEALTH_MCP_URL="http://127.0.0.1:8002/sse"
```

### Option 2: Deploy to Cloud Run (Production)

```bash
# Deploy using the script
./deploy.sh --with-mcp

# Or manually:
gcloud run deploy omhc-mcp-server \
  --source=./mcp \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated \
  --port=8002

# Get the service URL
gcloud run services describe omhc-mcp-server \
  --region=us-central1 \
  --format='value(status.url)'

# Add to .env
export MENTAL_HEALTH_MCP_URL="https://your-service-url/sse"
```

### Option 3: No MCP (Google Search Only)

If you don't configure `MENTAL_HEALTH_MCP_URL`, the Resource Connector will use only Google Search (still functional).

---

## Testing & Validation

### 1. Local Testing

```bash
# Test all components
pytest -v

# Test specific risk levels
pytest -m eval_crisis -v
pytest -m eval_low_risk -v
```

### 2. Test Deployed Agent

```bash
# Run crisis eval against deployed agent
python agent_engine_eval.py --tag crisis

# Run all evals
python agent_engine_eval.py --tag all

# Run specific risk levels
python agent_engine_eval.py --tag low-risk
python agent_engine_eval.py --tag medium-risk
python agent_engine_eval.py --tag unknown-intent
```

### 3. Manual Testing via ADK

```bash
# Test deployed agent interactively
adk web \
  --agent-engine-resource-name "projects/YOUR_PROJECT/locations/us-central1/agentEngines/YOUR_AGENT_ID"
```

### 4. Monitor Logs

```bash
# View recent logs
gcloud logging read "resource.type=agent_engine" --limit 50 --format json

# Tail logs in real-time
gcloud logging tail "resource.type=agent_engine"

# Filter by severity
gcloud logging read "resource.type=agent_engine AND severity>=ERROR" --limit 20
```

---

## Troubleshooting

### Common Issues

#### Authentication Errors

```bash
# Re-authenticate
gcloud auth login
gcloud auth application-default login

# Verify active account
gcloud auth list
```

#### API Not Enabled

```bash
# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com

# Enable Cloud Run API (for MCP)
gcloud services enable run.googleapis.com
```

#### Module Import Errors

```bash
# Ensure all dependencies are installed
pip install -e ".[dev]"

# Verify Python version
python --version  # Should be 3.13+
```

#### MCP Connection Failures

```bash
# Verify MCP server is running
curl http://127.0.0.1:8002/sse

# Check environment variable
echo $MENTAL_HEALTH_MCP_URL

# Restart MCP server
# [Stop existing server]
fastmcp run mcp/omhc_mcp_server.py --host 127.0.0.1 --port 8002 --transport sse
```

#### Deployment Failures

```bash
# Check project configuration
gcloud config list

# Verify permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID

# Check quotas
gcloud compute project-info describe --project=YOUR_PROJECT_ID
```

### Getting Help

1. **Check Logs**: Always start with `gcloud logging read`
2. **Review README**: See [README.md](README.md) for detailed architecture
3. **System Overview**: See [SystemOverview.md](SystemOverview.md) for technical details
4. **Test Locally First**: Run `pytest -v` before deploying

---

## Useful Commands Reference

### Deployment
```bash
# Deploy agent
./deploy.sh

# Update agent
./deploy.sh --update

# Deploy with MCP
./deploy.sh --with-mcp

# List deployed agents
gcloud ai agent-engines list --location=us-central1

# Delete agent
gcloud ai agent-engines delete AGENT_ID --location=us-central1
```

### Testing
```bash
# All tests
pytest

# E2E tests only
pytest -m e2e

# Specific test file
pytest tests/pytests/test_high_risk_safety_ceiling.py -v

# Remote evals
python agent_engine_eval.py --tag all
```

### MCP Server
```bash
# Start locally
fastmcp run mcp/omhc_mcp_server.py --host 127.0.0.1 --port 8002 --transport sse

# Deploy to Cloud Run
gcloud run deploy omhc-mcp-server --source=./mcp --region=us-central1

# View Cloud Run logs
gcloud run logs read omhc-mcp-server --region=us-central1
```

### Monitoring
```bash
# View logs
gcloud logging read "resource.type=agent_engine" --limit 50

# Tail logs
gcloud logging tail "resource.type=agent_engine"

# View metrics (if available)
gcloud monitoring dashboards list
```

---

## Next Steps After Deployment

1. ✅ **Run Evals**: Validate deployment with `python agent_engine_eval.py --tag all`
2. ✅ **Monitor Logs**: Set up log-based alerts for high-risk interactions
3. ✅ **Configure MCP**: Deploy production MCP server with real crisis data
4. ✅ **Set Up CI/CD**: Automate testing and deployment
5. ✅ **Review Safety**: Conduct clinician review of eval results
6. ✅ **Scale Testing**: Run comprehensive load tests
7. ✅ **Documentation**: Update team on deployment and monitoring procedures

---

## Additional Resources

- **README.md**: Comprehensive project documentation
- **SystemOverview.md**: Technical architecture details
- **CONTRIBUTING.md**: Development guidelines
- **SECURITY.md**: Security policies and reporting
- **Tests Directory**: Example usage patterns

---

**Questions or Issues?** Check the troubleshooting section above or review the project documentation.
