#!/bin/bash
# deploy.sh
# Deployment script for OMHC to Vertex AI Agent Engine

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Banner
echo "=================================================="
echo "  OMHC Deployment to Vertex AI Agent Engine"
echo "=================================================="
echo ""

# Load environment variables from .env if it exists
if [ -f .env ]; then
    print_info "Loading environment variables from .env"
    export $(grep -v '^#' .env | xargs)
    print_success "Environment variables loaded"
else
    print_warning ".env file not found, using system environment variables"
fi

# Validate required environment variables
print_info "Validating configuration..."

if [ -z "$OMC_GCP_PROJECT_ID" ]; then
    print_error "OMC_GCP_PROJECT_ID is not set"
    echo "Please set it in .env file or export it:"
    echo "  export OMC_GCP_PROJECT_ID=\"your-project-id\""
    exit 1
fi

# Set defaults for optional variables
OMC_GCP_LOCATION="${OMC_GCP_LOCATION:-us-central1}"
OMHC_MODEL_NAME="${OMHC_MODEL_NAME:-gemini-2.0-flash}"

print_success "Configuration validated"
echo "  Project ID: $OMC_GCP_PROJECT_ID"
echo "  Location: $OMC_GCP_LOCATION"
echo "  Model: $OMHC_MODEL_NAME"
echo ""

# Check if gcloud is authenticated
print_info "Checking gcloud authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    print_warning "gcloud not authenticated"
    echo "Running: gcloud auth login"
    gcloud auth login
fi
print_success "gcloud authenticated"

# Set the active project
print_info "Setting active GCP project..."
gcloud config set project "$OMC_GCP_PROJECT_ID"
print_success "Active project set to $OMC_GCP_PROJECT_ID"

# Check if Vertex AI API is enabled
print_info "Checking if Vertex AI API is enabled..."
if ! gcloud services list --enabled --filter="name:aiplatform.googleapis.com" --format="value(name)" | grep -q "aiplatform.googleapis.com"; then
    print_warning "Vertex AI API not enabled. Enabling now..."
    gcloud services enable aiplatform.googleapis.com
    print_success "Vertex AI API enabled"
else
    print_success "Vertex AI API is already enabled"
fi

# Check for ADK installation
print_info "Checking for ADK installation..."
if ! command -v adk &> /dev/null; then
    print_error "ADK CLI not found"
    echo "Please install it with: pip install google-adk"
    exit 1
fi
print_success "ADK CLI found"

echo ""
echo "=================================================="
echo "  Starting Deployment"
echo "=================================================="
echo ""

# Parse command line arguments
DEPLOY_MCP=false
UPDATE_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --with-mcp)
            DEPLOY_MCP=true
            shift
            ;;
        --update)
            UPDATE_MODE=true
            shift
            ;;
        --help)
            echo "Usage: ./deploy.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --with-mcp    Also deploy MCP server to Cloud Run"
            echo "  --update      Update existing deployment instead of creating new"
            echo "  --help        Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Deploy the main agent to Vertex AI Agent Engine
print_info "Deploying OMHC agent to Vertex AI Agent Engine..."

DEPLOY_CMD="adk deploy \
  --project $OMC_GCP_PROJECT_ID \
  --location $OMC_GCP_LOCATION \
  --agent-module agents.orchestrator_agent.agent \
  --agent-name root_agent \
  --display-name 'OMHC Mental Health Support' \
  --description 'Open Mental Health Collective: Multi-agent mental health support system with safety-first design'"

if [ "$UPDATE_MODE" = true ]; then
    print_info "Running in UPDATE mode..."
    DEPLOY_CMD="$DEPLOY_CMD --update"
fi

# Execute deployment
if eval $DEPLOY_CMD; then
    print_success "Agent deployed successfully!"
else
    print_error "Deployment failed"
    exit 1
fi

echo ""

# Optional: Deploy MCP server
if [ "$DEPLOY_MCP" = true ]; then
    print_info "Deploying MCP server to Cloud Run..."
    
    # Build and deploy MCP server
    gcloud run deploy omhc-mcp-server \
        --source=./mcp \
        --platform=managed \
        --region=$OMC_GCP_LOCATION \
        --allow-unauthenticated \
        --port=8002 \
        --set-env-vars="OMHC_MODEL_NAME=$OMHC_MODEL_NAME"
    
    if [ $? -eq 0 ]; then
        print_success "MCP server deployed successfully!"
        
        # Get the service URL
        MCP_URL=$(gcloud run services describe omhc-mcp-server \
            --region=$OMC_GCP_LOCATION \
            --format='value(status.url)')
        
        print_success "MCP Server URL: $MCP_URL/sse"
        print_warning "Update your agent environment with:"
        echo "  export MENTAL_HEALTH_MCP_URL=\"$MCP_URL/sse\""
    else
        print_warning "MCP server deployment failed (optional)"
    fi
    
    echo ""
fi

# Get the deployed agent resource name
print_info "Retrieving agent resource name..."

# Note: This may need adjustment based on actual ADK CLI output
# For now, we'll show how to find it manually
echo ""
print_success "Deployment Complete!"
echo ""
echo "=================================================="
echo "  Next Steps"
echo "=================================================="
echo ""
echo "1. Find your Agent Engine resource name:"
echo "   gcloud ai agent-engines list --location=$OMC_GCP_LOCATION"
echo ""
echo "2. Set the resource name in your environment:"
echo "   export OMC_AGENT_ENGINE_RESOURCE_NAME=\"projects/$OMC_GCP_PROJECT_ID/locations/$OMC_GCP_LOCATION/agentEngines/YOUR_AGENT_ID\""
echo ""
echo "3. Test the deployment with evals:"
echo "   python agent_engine_eval.py --tag crisis"
echo "   python agent_engine_eval.py --tag all"
echo ""
echo "4. Monitor logs:"
echo "   gcloud logging read \"resource.type=agent_engine\" --limit 50"
echo ""
echo "=================================================="

print_info "Deployment script completed successfully!"
