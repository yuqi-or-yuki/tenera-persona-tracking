# Tenera Persona Tracking — Design Document

## Vision

An open-source, CLI-first persona tracking engine. Users interact through a command line that talks to a FastAPI server under the hood. Designed for transparency and easy integration with Tenera.

## Architecture

```
CLI (typer)  --->  FastAPI Server (localhost:8000)  --->  SQLite / Supabase
    |                       |
    |                  REST API (/api/v1/...)
    |
    +-- `tpt serve`     starts the server
    +-- `tpt persona`   manage personas
    +-- `tpt entity`    manage entities on personas
    +-- `tpt track`     track events
    +-- `tpt events`    view event timelines
```

The CLI is a thin HTTP client. All logic lives in the FastAPI server.
This means the same API that powers the CLI is the same API Tenera (or any other tool) integrates with.

## Core Concepts

### Persona
A tracked identity. Could be a user, customer, account — anything you want to track.
- Has a unique `distinct_id` (your user ID, email, etc.)
- Has optional `name` and `description`
- Created explicitly or auto-created on first event track

### Entity
An arbitrary key-value property attached to a persona.
- Key can be anything: "plan", "company", "role", "favorite_color"
- Value is always a string (serialize complex values as JSON)
- Each key is unique per persona — setting the same key overwrites
- Stored as individual rows (not JSONB) so each change is timestamped

### Event
A tracked action or state change on a persona's timeline.
- Has an `event_type` (e.g. "page_view", "plan_upgrade", "purchase")
- Has optional `properties` (arbitrary JSON)
- Has a `timestamp` (defaults to now)

## Data Model

```
personas
├── id (UUID)
├── distinct_id (unique, indexed)
├── name
├── description
├── created_at
└── updated_at

entities
├── id (UUID)
├── persona_id (FK -> personas)
├── key
├── value
├── created_at
├── updated_at
└── UNIQUE(persona_id, key)

events
├── id (UUID)
├── persona_id (FK -> personas)
├── event_type (indexed)
├── properties (JSON text)
└── timestamp (indexed)
```

## CLI Design

Command structure follows `tpt <resource> <action>` pattern:

```bash
# Server
tpt serve                              # Start the FastAPI server

# Personas
tpt persona create <distinct_id>       # Create a persona
tpt persona list                       # List all personas
tpt persona get <distinct_id>          # Get persona details + entities
tpt persona update <distinct_id>       # Update name/description
tpt persona delete <distinct_id>       # Delete persona + all data

# Entities
tpt entity set <distinct_id> <key> <value>    # Set a property
tpt entity list <distinct_id>                  # List all entities
tpt entity delete <distinct_id> <key>          # Remove a property

# Events
tpt track <distinct_id> <event_type>           # Track an event
tpt events <distinct_id>                        # View event timeline
```

## API Endpoints

| Method | Endpoint | CLI Command |
|--------|----------|-------------|
| `POST` | `/api/v1/personas` | `tpt persona create` |
| `GET` | `/api/v1/personas` | `tpt persona list` |
| `GET` | `/api/v1/personas/{id}` | `tpt persona get` |
| `PATCH` | `/api/v1/personas/{id}` | `tpt persona update` |
| `DELETE` | `/api/v1/personas/{id}` | `tpt persona delete` |
| `POST` | `/api/v1/personas/{id}/entities` | `tpt entity set` |
| `GET` | `/api/v1/personas/{id}/entities` | `tpt entity list` |
| `DELETE` | `/api/v1/personas/{id}/entities/{key}` | `tpt entity delete` |
| `POST` | `/api/v1/track` | `tpt track` |
| `GET` | `/api/v1/personas/{id}/events` | `tpt events` |

## Authentication

Simple API key in `X-API-Key` header. The CLI reads the key from:
1. `--api-key` flag
2. `TPT_API_KEY` environment variable
3. `.env` file in current directory

## Integration with Tenera

The integration is API-to-API. Tenera stores the API key and base URL, then calls the same REST endpoints the CLI uses. No tight coupling — any HTTP client works.

```
User's App  -->  tpt CLI / REST API  -->  Persona Tracker DB
                        ^
                        |
                    Tenera reads persona + entity + event data
                    for AI-powered cohort analysis
```

## Database Modes

- **SQLite** (default): Zero-config, local file, great for dev and self-hosting
- **Supabase PostgreSQL**: Production-grade, real-time capable, direct Tenera integration

## Design Principles

1. **Persona is the primitive** — everything is organized around personas, not raw events
2. **CLI-first** — the CLI is the primary interface; the API is the engine
3. **Open by design** — all code is visible, all data formats are documented
4. **Easy integration** — API key auth, standard REST, JSON in/out
5. **Flexible entities** — any key, any value, per persona
