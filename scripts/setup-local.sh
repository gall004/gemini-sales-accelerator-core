#!/usr/bin/env bash
# =============================================================================
# setup-local.sh — One-command local development setup
#
# Usage:
#   ./scripts/setup-local.sh
#
# What it does:
#   1. Checks that .env exists (copies from .env.example if missing)
#   2. Checks that Docker is running
#   3. Runs docker compose up --build
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "🔧 Gemini Sales Accelerator Core — Local Setup"
echo "================================================"
echo ""

# ── Step 1: .env file ──
if [[ -f ".env" ]]; then
    echo "✅ .env file found"
else
    if [[ -f ".env.example" ]]; then
        cp .env.example .env
        echo "📋 Created .env from .env.example"
        echo "   ⚠️  Review .env and update values (GCP_PROJECT_ID, API_KEY, etc.)"
    else
        echo "❌ No .env.example found at project root. Cannot continue."
        exit 1
    fi
fi

# ── Step 2: Docker check ──
echo ""
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop:"
    echo "   https://www.docker.com/products/docker-desktop/"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker daemon is not running. Please start Docker Desktop."
    exit 1
fi
echo "✅ Docker is running"

# ── Step 3: Build and start ──
echo ""
echo "🐳 Starting services (Postgres, Redis, API)..."
echo ""
docker compose up --build

