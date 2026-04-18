# LiveKit Voice AI Agent

Voice AI assistant built with [LiveKit Agents](https://docs.livekit.io/agents/) for Python.

## Features

- **Voice AI Pipeline**: STT (Deepgram) → LLM (OpenAI) → TTS (Cartesia)
- **Turn Detection**: LiveKit Multilingual Turn Detector for contextually-aware speaker detection
- **VAD**: Silero Voice Activity Detection
- **Noise Cancellation**: ai_coustics background voice cancellation
- **Eval Suite**: pytest-based testing & evaluation framework
- **Self-hosted LiveKit Server**: Included via Podman Compose

## Requirements

- [Podman](https://podman.io/) & [podman-compose](https://github.com/containers/podman-compose)

## Quick Start

Run the setup script — it creates `.env.local` (dev credentials) and starts everything:

```bash
./setup.sh
```

That's it. The script will:
1. Create `.env.local` with dev credentials matching the local LiveKit Server
2. Build the agent image (Python 3.13 + uv + all dependencies)
3. Start the LiveKit Server and the Agent container

## Architecture

```
podman-compose
├── livekit-server   (livekit/livekit-server:latest)  → :7880 HTTP/WS, :7881 TCP, :7882 UDP
└── livekit-agent    (Dockerfile.dev)                  → connects to livekit-server
```

## Useful Commands

```bash
# View agent logs
podman-compose logs -f livekit-agent

# View server logs
podman-compose logs -f livekit-server

# Run agent in text console mode (works inside container, no audio needed)
podman exec -it livekit-agent uv run src/agent.py console --text

# Run tests
podman exec livekit-agent uv run pytest

# Rebuild after code changes
podman-compose up --build -d

# Stop everything
podman-compose down
```

## Project Structure

```
livekit/
├── config/
│   └── livekit.yaml        # LiveKit Server config (dev keys)
├── src/
│   └── agent.py            # Voice AI agent
├── tests/
│   └── test_agent.py       # Eval suite
├── docker-compose.yml      # Full environment definition
├── Dockerfile.dev          # Dev image (no uv.lock required)
├── Dockerfile              # Production multi-stage image
├── pyproject.toml          # Python dependencies
├── setup.sh                # One-command setup
├── .env.example            # Env template
└── .env.local              # Local credentials (git-ignored)
```

## Configuration

### Environment Variables

| Variable | Description | Dev Default |
|---|---|---|
| `LIVEKIT_URL` | LiveKit Server WebSocket URL | `ws://livekit-server:7880` |
| `LIVEKIT_API_KEY` | API key (must match `config/livekit.yaml`) | `devkey` |
| `LIVEKIT_API_SECRET` | API secret (must match `config/livekit.yaml`) | `secret` |

### LiveKit Server

Server config lives in `config/livekit.yaml`. The dev keys (`devkey` / `secret`) are pre-configured.

## Console Mode (voice in terminal)

The `console` command requires access to host audio devices (mic + speaker). Inside a container this needs PulseAudio passthrough:

```bash
podman exec -e PULSE_SERVER=unix:/tmp/pulse/native \
  -v /run/user/$(id -u)/pulse:/tmp/pulse:ro \
  livekit-agent uv run src/agent.py console
```

> **Recommended alternative**: use the [LiveKit Cloud Playground](https://cloud.livekit.io/) web console to talk to your agent via browser — no audio passthrough needed.

## Production Deployment

For production, use the multi-stage `Dockerfile` (requires `uv.lock`):

```bash
uv lock
podman build -t livekit-agent:prod .
```

## Documentation

- [LiveKit Agents Docs](https://docs.livekit.io/agents/)
- [Voice AI Quickstart](https://docs.livekit.io/agents/start/voice-ai-quickstart/)
- [AI Models](https://docs.livekit.io/agents/models/)
- [Self-hosting LiveKit](https://docs.livekit.io/realtime/self-hosting/)
