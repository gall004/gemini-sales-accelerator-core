#!/usr/bin/env bash
# =============================================================================
# deploy-agent.sh — Deploy a Vertex AI agent from examples/vertex-agents/
#
# Usage:
#   ./scripts/deploy-agent.sh briefing-agent
#   ./scripts/deploy-agent.sh briefing-agent --project-id override-project
#
# GCP_PROJECT_ID and GCP_LOCATION are auto-read from the root .env file.
# Explicitly passed args (--project-id, --location) take precedence.
#
# What it does:
#   1. Sources root .env for GCP config
#   2. Navigates to examples/vertex-agents/$AGENT_NAME
#   3. Creates an isolated .venv
#   4. Installs requirements.txt
#   5. Runs deploy.py (forwarding extra args)
#   6. Cleans up and returns to the project root
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ── Validate args ──
if [[ $# -lt 1 ]]; then
    echo "❌ Usage: $0 <agent-name> [deploy.py args...]"
    echo ""
    echo "Available agents:"
    for dir in "$PROJECT_ROOT"/examples/vertex-agents/*/; do
        if [[ -f "$dir/deploy.py" ]]; then
            echo "  • $(basename "$dir")"
        fi
    done
    exit 1
fi

AGENT_NAME="$1"
shift  # remaining args forwarded to deploy.py
AGENT_DIR="$PROJECT_ROOT/examples/vertex-agents/$AGENT_NAME"

if [[ ! -d "$AGENT_DIR" ]]; then
    echo "❌ Agent directory not found: $AGENT_DIR"
    exit 1
fi

if [[ ! -f "$AGENT_DIR/deploy.py" ]]; then
    echo "❌ No deploy.py found in: $AGENT_DIR"
    exit 1
fi

if [[ ! -f "$AGENT_DIR/requirements.txt" ]]; then
    echo "❌ No requirements.txt found in: $AGENT_DIR"
    exit 1
fi

# ── Load root .env ──
ENV_FILE="$PROJECT_ROOT/.env"
if [[ -f "$ENV_FILE" ]]; then
    echo "📄 Loading config from .env"
    set -a
    source "$ENV_FILE"
    set +a
else
    echo "⚠️  No .env found at project root. GCP vars must be passed as args."
fi

# ── Auto-inject GCP args if not explicitly provided ──
EXTRA_ARGS=()

# Only inject --project-id if the user didn't provide it
if ! echo "$*" | grep -q -- "--project-id"; then
    if [[ -n "${GCP_PROJECT_ID:-}" && "$GCP_PROJECT_ID" != "your-gcp-project-id" ]]; then
        EXTRA_ARGS+=("--project-id" "$GCP_PROJECT_ID")
        echo "   Using GCP_PROJECT_ID=$GCP_PROJECT_ID from .env"
    fi
fi

# Only inject --location if the user didn't provide it
if ! echo "$*" | grep -q -- "--location"; then
    if [[ -n "${GCP_LOCATION:-}" ]]; then
        EXTRA_ARGS+=("--location" "$GCP_LOCATION")
        echo "   Using GCP_LOCATION=$GCP_LOCATION from .env"
    fi
fi

# ── Deploy ──
echo ""
echo "🚀 Deploying agent: $AGENT_NAME"
echo "   Directory: $AGENT_DIR"
echo ""

cd "$AGENT_DIR"

echo "📦 Creating isolated virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "🤖 Running deploy.py..."
python deploy.py "${EXTRA_ARGS[@]}" "$@"

# ── Cleanup ──
deactivate
echo ""
echo "🧹 Cleaning up virtual environment..."
rm -rf .venv

cd "$PROJECT_ROOT"
echo "✅ Done. Returned to project root: $PROJECT_ROOT"
