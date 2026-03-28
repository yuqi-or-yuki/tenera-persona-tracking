# Tenera Persona Tracking

Open-source persona tracking and cohort analytics engine. API-first, designed to integrate with [Tenera](https://tenera.ai).

## What is this?

A lightweight backend service for tracking **user personas** — identity profiles with arbitrary key-value entities and event timelines. Unlike traditional analytics tools that treat segmentation as a query, this tool treats the **persona as the core primitive**.

**Use cases:**
- Track user personas with flexible properties (entities)
- Build event timelines per persona (page views, upgrades, purchases, etc.)
- Self-host with SQLite or connect to Supabase for production
- Integrate with Tenera for AI-powered cohort analysis and clustering

## Quick Start

### 1. Install

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/tenera-persona-tracking.git
cd tenera-persona-tracking

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env — at minimum, set a secure API_KEY
```

### 3. Run

```bash
python run.py
# Server starts at http://localhost:8000
# API docs at http://localhost:8000/docs
```

## API Reference

All endpoints require an `X-API-Key` header.

### Personas

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/personas` | Create a persona |
| `GET` | `/api/v1/personas` | List personas (with search) |
| `GET` | `/api/v1/personas/{id}` | Get a persona with entities |
| `PATCH` | `/api/v1/personas/{id}` | Update persona name/description |
| `DELETE` | `/api/v1/personas/{id}` | Delete persona and all data |

### Entities (Key-Value Properties)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/personas/{id}/entities` | Set key-value entities |
| `GET` | `/api/v1/personas/{id}/entities` | Get all entities |
| `DELETE` | `/api/v1/personas/{id}/entities/{key}` | Remove an entity |

### Events (Timeline)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/track?distinct_id=...` | Track an event (auto-creates persona) |
| `GET` | `/api/v1/personas/{id}/events` | Get event timeline |

## Usage Examples

### Create a persona with entities

```bash
curl -X POST http://localhost:8000/api/v1/personas \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "distinct_id": "user_123",
    "name": "Jane Doe",
    "entities": [
      {"key": "plan", "value": "enterprise"},
      {"key": "company", "value": "Acme Corp"},
      {"key": "role", "value": "engineering_manager"}
    ]
  }'
```

### Track an event

```bash
curl -X POST "http://localhost:8000/api/v1/track?distinct_id=user_123" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "plan_upgrade",
    "properties": {"from": "pro", "to": "enterprise", "mrr_delta": 200}
  }'
```

### Update entities

```bash
curl -X POST http://localhost:8000/api/v1/personas/{id}/entities \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '[
    {"key": "plan", "value": "enterprise_plus"},
    {"key": "seats", "value": "50"}
  ]'
```

## Database Modes

| Mode | Config | Best for |
|------|--------|----------|
| **SQLite** | `DATABASE_MODE=sqlite` | Local dev, self-hosted, small scale |
| **Supabase** | `DATABASE_MODE=supabase` | Production, real-time, Tenera integration |

## Integrating with Tenera

This tool is designed to work alongside Tenera. The integration is API-to-API:

1. Deploy this service (or run locally)
2. Set your `API_KEY` in both this service's `.env` and Tenera's configuration
3. Tenera calls this service's REST API to read/write persona data
4. Persona data flows into Tenera for AI-powered analysis and clustering

```
Your App  -->  Persona Tracker (this tool)  <-->  Tenera
                    |
               SQLite / Supabase
```

## Project Structure

```
tenera-persona-tracking/
├── app/
│   ├── api/v1/
│   │   ├── personas.py      # Persona + entity CRUD
│   │   ├── events.py         # Event tracking + timeline
│   │   └── router.py         # Route aggregation
│   ├── core/
│   │   ├── auth.py           # API key authentication
│   │   ├── config.py         # Settings (env-based)
│   │   └── database.py       # SQLAlchemy async setup
│   ├── models/
│   │   ├── persona.py        # Persona model
│   │   ├── entity.py         # Entity (key-value) model
│   │   └── event.py          # Event model
│   ├── schemas/
│   │   └── persona.py        # Pydantic request/response schemas
│   └── main.py               # FastAPI app
├── run.py                     # Dev server entry point
├── pyproject.toml             # Python project config
└── .env.example               # Environment template
```

## License

MIT
