#!/usr/bin/env bash
# =============================================================================
# deploy-agent.sh — Deploy a Vertex AI agent from examples/vertex-agents/
#
# Usage:
#   ./scripts/deploy-agent.sh briefing-agent
#   ./scripts/deploy-agent.sh briefing-agent --project-id my-project
#
# What it does:
#   1. Navigates to examples/vertex-agents/$AGENT_NAME
#   2. Creates an isolated .venv
#   3. Installs requirements.txt
#   4. Runs deploy.py (forwarding extra args)
#   5. Cleans up and returns to the project root
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

# ── Deploy ──
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
python deploy.py "$@"

# ── Cleanup ──
deactivate
echo ""
echo "🧹 Cleaning up virtual environment..."
rm -rf .venv

cd "$PROJECT_ROOT"
echo "✅ Done. Returned to project root: $PROJECT_ROOT"
