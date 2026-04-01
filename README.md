# OpenRouter FastAPI Service

A production-grade, modular FastAPI service that routes LLM requests through the **OpenRouter API**. Built with `langchain-openrouter`, async-first patterns, and comprehensive error handling.

## Features

✅ **Async-first design** — Non-blocking I/O with `FastAPI` + `uvicorn`  
✅ **Intelligent routing** — Model selection via `MODEL_ID` env var or per-request override  
✅ **Retry logic** — Exponential backoff (3 attempts, 1–10s wait) via `tenacity`  
✅ **Type safety** — Full Pydantic validation on requests/responses  
✅ **Streaming support** — SSE (Server-Sent Events) for real-time response chunks  
✅ **Structured error handling** — Consistent JSON error responses  
✅ **Docker ready** — Multi-stage Dockerfile + docker-compose  
✅ **Secure config** — `SecretStr` for API key storage; environment-driven configuration  

---

## Quick Start

### Prerequisites

- Python 3.12+
- An active OpenRouter account with API key (<https://openrouter.ai>)
- `uv` package manager

### 1. Clone & Setup Environment

```bash
git clone https://github.com/ParzivalXIII/openrouter-llm.git
cd openrouter-api

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# OPENROUTER_API_KEY=sk-or-v1-...
# MODEL_ID=anthropic/claude-sonnet-4.5
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Run the Service

```bash
# Development (with auto-reload)
uv run uvicorn main:app --reload

# Or production-style
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

### 4. Test the Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Chat completion (single response)
curl -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello, world!"}
    ]
  }'

# Streaming chat (SSE)
curl -X POST http://localhost:8000/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "List three colors"}
    ]
  }'
```

Or use the included test script:

```bash
chmod +x test_endpoints.sh
./test_endpoints.sh
```

---

## API Endpoints

### `GET /health`

**Health check endpoint.**

**Response:**

```json
{
  "status": "healthy",
  "service": "OpenRouter FastAPI Service",
  "model": "anthropic/claude-sonnet-4.5"
}
```

### `POST /v1/chat`

**Single-turn chat completion** (non-streaming).

**Request:**

```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is the capital of France?"}
  ],
  "model": "anthropic/claude-sonnet-4.5",
  "temperature": 0.7,
  "max_tokens": 100
}
```

**Fields:**

- `messages` *(required)*: Array of message objects with `role` and `content`.
  - `role`: One of `"system"`, `"user"`, or `"assistant"`.
  - `content`: The message text.
- `model` *(optional)*: Override the default `MODEL_ID`. Defaults to env var `MODEL_ID`.
- `temperature` *(optional)*: Sampling temperature (0.0–2.0). Default: 0.7.
- `max_tokens` *(optional)*: Maximum tokens to generate. Default: None (model limit).

**Response:**

```json
{
  "content": "The capital of France is Paris.",
  "model": "anthropic/claude-sonnet-4.5",
  "usage": {
    "input_tokens": 15,
    "output_tokens": 8,
    "total_tokens": 23
  },
  "finish_reason": "stop"
}
```

### `POST /v1/chat/stream`

**Streaming chat completion** (Server-Sent Events).

**Request:** Same as `/v1/chat`.

**Response** (SSE format):

```
data: {"content": "The", "model": "anthropic/claude-sonnet-4.5"}

data: {"content": " capital", "model": "anthropic/claude-sonnet-4.5"}

data: {"content": " of", "model": "anthropic/claude-sonnet-4.5"}

...

data: [DONE]

```

---

## Configuration

All configuration is environment-driven via `.env`:

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | ✅ | `sk-or-v1-...` | OpenRouter API key (keep secret!) |
| `MODEL_ID` | ✅ | `anthropic/claude-sonnet-4.5` | Default model to use |
| `APP_TITLE` | ❌ | `OpenRouter FastAPI Service` | Application name for attribution |
| `APP_URL` | ❌ | `http://localhost:8000` | Application URL for attribution |
| `ENVIRONMENT` | ❌ | `development` | Deployment stage (development, staging, production) |
| `LOG_LEVEL` | ❌ | `INFO` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) |

**Security Note:** Never commit `.env` with real credentials. Use `.env.example` as a template.

---

## Project Structure

```
openrouter-api/
├── main.py                  # FastAPI app factory & entry point
├── pyproject.toml           # Project metadata & dependencies
├── README.md                # This file
├── .env                     # Environment variables (NEVER commit with real keys!)
├── .env.example             # Environment template
├── Dockerfile               # Multi-stage production build
├── docker-compose.yml       # Local development orchestration
├── test_endpoints.sh        # Manual test script
│
└── app/
    ├── __init__.py          # Package marker
    ├── config.py            # Settings management (Pydantic BaseSettings)
    ├── schemas.py           # Request/response Pydantic models
    ├── exceptions.py        # Custom exception hierarchy & handlers
    ├── llm_client.py        # LLM factory & async invocation with retry
    └── router.py            # API route handlers (/health, /v1/chat, /v1/chat/stream)
```

---

## Architecture

### Layered Design

```
┌─────────────────────────────────────┐
│         FastAPI Routes              │  app/router.py
│  (/health, /v1/chat, /v1/chat/stream)
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│    LLM Client & Retry Logic         │  app/llm_client.py
│  (Tenacity, ChatOpenRouter)         │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  OpenRouter API                     │
│  (https://openrouter.ai/api/v1)     │
└─────────────────────────────────────┘
```

### Key Design Decisions

1. **Async-first**: All I/O is non-blocking. Uses `async/await` throughout.
2. **Dependency Injection**: FastAPI's `Depends()` for clean, testable code.
3. **Retry Logic**: Tenacity's `AsyncRetrying` for robust error recovery on 429/transient failures.
4. **Model Override**: Requests can override the default model without changing config.
5. **Streaming**: SSE format compatible with browsers, curl, and standard HTTP clients.
6. **Error Handling**: Structured exception hierarchy with FastAPI exception handlers.

---

## Docker Deployment

### Build & Run with Docker Compose

```bash
# Copy .env and populate with real credentials
cp .env.example .env
nano .env  # Edit with your API key

# Build and start the service
docker compose up --build

# In another terminal, test the endpoint
curl http://localhost:8000/health
```

### Manual Docker Build

```bash
docker build -t openrouter-api:latest .
docker run -p 8000:8000 \
  -e OPENROUTER_API_KEY=sk-or-v1-... \
  -e MODEL_ID=anthropic/claude-sonnet-4.5 \
  openrouter-api:latest
```

---

## Error Handling

The service returns structured JSON errors:

**Example (Missing API Key):**

```json
{
  "error": {
    "code": "LLM_INVOCATION_FAILED",
    "message": "Failed to invoke LLM after retries: Missing Authentication header",
    "path": "/v1/chat"
  }
}
```

**HTTP Status Codes:**

- `200 OK` — Successful request
- `400 Bad Request` — Invalid input (validation failed)
- `422 Unprocessable Entity` — Request validation error
- `500 Internal Server Error` — Server-side error (config, LLM unavailable)
- `503 Service Unavailable` — LLM invocation failed after retries

---

## Performance Optimizations

- **Async I/O**: Non-blocking HTTP calls to OpenRouter via `httpx`
- **Connection Pooling**: FastAPI auto-manages connection pools
- **Retry Backoff**: Exponential backoff (1–10s) reduces thundering herd on failures
- **Caching**: Settings object is cached via `@lru_cache` for zero initialization cost
- **Pre-compiled Schemas**: Pydantic models are compiled at startup

---

## Development

### Running Tests

```bash
# Install dev dependencies
uv sync

# Run pytest
uv run pytest -v

# Run with coverage
uv run pytest --cov=app --cov-report=html
```

### Type Checking

```bash
uv run mypy app/ main.py
```

### Linting

```bash
uv run ruff check app/ main.py
```

---

## Production Deployment

### Environment Configuration

For production, ensure:

1. **Secure Credentials**: Store `OPENROUTER_API_KEY` in a secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.)
2. **CORS** *(in main.py)*: Restrict origins to trusted domains
3. **Rate Limiting**: Add rate limiting middleware if needed
4. **Logging**: Send logs to a centralized service (ELK, Datadog, etc.)

### Example K8s Deployment

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: openrouter-secrets
type: Opaque
stringData:
  OPENROUTER_API_KEY: sk-or-v1-...
  MODEL_ID: anthropic/claude-sonnet-4.5

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: openrouter-api
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: openrouter-api:latest
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: openrouter-secrets
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
```

---

## Troubleshooting

### Rate Limit (429) Errors

OpenRouter enforces rate limits. The service retries with exponential backoff. If you continue to get 429s:

- Check your account's usage limits at <https://openrouter.ai/settings>
- Consider using a different model with higher quota
- Implement request queuing for high-traffic scenarios

### Connection Timeout

If requests hang:

1. Verify `OPENROUTER_API_KEY` is valid (and not expired)
2. Check network connectivity to `openrouter.ai`
3. Verify the `MODEL_ID` is supported by OpenRouter
4. Check server logs: `docker logs -f openrouter-api`

### Environment Variables Not Loaded

If the app complains about missing `OPENROUTER_API_KEY`:

1. Ensure `.env` exists in the project root
2. Verify you've run `uv sync` to install `python-dotenv`
3. When using Docker, verify `.env` is deployed or passed via `-e` flags

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

[Add your license here, e.g., MIT, Apache 2.0, etc.]

---

## References

- **OpenRouter Docs**: <https://openrouter.ai/docs>
- **LangChain**: <https://python.langchain.com>
- **FastAPI**: <https://fastapi.tiangolo.com>
- **Pydantic**: <https://docs.pydantic.dev>
- **Tenacity**: <https://tenacity.readthedocs.io>

---

## Support

For issues or questions:

1. Check existing GitHub issues
2. Review the troubleshooting section above
3. Create a detailed GitHub issue with:
   - Error messages (logs)
   - Steps to reproduce
   - Python version, OS
   - `.env` variables (sanitize your API key!)

---

**Built with ❤️ for the LLM community.**
