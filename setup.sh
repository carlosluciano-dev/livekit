#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ENV_FILE=".env.local"

# ── Create .env.local if it doesn't exist ────────────────────────────────────
if [ ! -f "$ENV_FILE" ]; then
  echo "Creating $ENV_FILE with default dev credentials..."
  cat > "$ENV_FILE" <<'EOF'
# LiveKit credentials (matching config/livekit.yaml dev keys)
LIVEKIT_URL=ws://livekit-server:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
EOF
  echo "  ✔ $ENV_FILE created."
else
  echo "  ✔ $ENV_FILE already exists, skipping."
fi

# ── Build and start containers ───────────────────────────────────────────────
echo ""
echo "Building and starting containers..."
podman-compose up --build -d

echo ""
echo "──────────────────────────────────────────────────"
echo "  LiveKit Server : http://localhost:7880"
echo "  Agent          : running in dev mode"
echo "──────────────────────────────────────────────────"
echo ""
echo "Useful commands:"
echo "  podman-compose logs -f livekit-agent     # agent logs"
echo "  podman-compose logs -f livekit-server    # server logs"
echo "  podman exec livekit-agent uv run src/agent.py console  # console mode"
echo "  podman exec livekit-agent uv run pytest                # run tests"
echo "  podman-compose down                      # stop all"
echo ""
