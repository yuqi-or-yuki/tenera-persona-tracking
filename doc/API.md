# API Reference

All endpoints require an `X-API-Key` header.

Base URL: `http://localhost:8000`

## Personas

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/personas` | Create a persona |
| `GET` | `/api/v1/personas` | List personas (with `?search=` and `?limit=`) |
| `GET` | `/api/v1/personas/{id}` | Get a persona with entities |
| `PATCH` | `/api/v1/personas/{id}` | Update persona name/description |
| `DELETE` | `/api/v1/personas/{id}` | Delete persona and all data |

## Entities (Key-Value Properties)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/personas/{id}/entities` | Set key-value entities (upserts) |
| `GET` | `/api/v1/personas/{id}/entities` | Get all entities |
| `DELETE` | `/api/v1/personas/{id}/entities/{key}` | Remove an entity |

## Events (Timeline)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/track?distinct_id=...` | Track an event (auto-creates persona) |
| `GET` | `/api/v1/personas/{id}/events` | Get event timeline |

## Clustering

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/clusters/run` | Trigger a clustering run |
| `GET` | `/api/v1/clusters/runs` | List past runs |
| `GET` | `/api/v1/clusters/runs/{id}` | Get run details + assignments |
| `GET` | `/api/v1/clusters/latest` | Get latest run results |
| `GET` | `/api/v1/clusters/schedule` | Get current schedule |
| `POST` | `/api/v1/clusters/schedule` | Set cron schedule |
| `DELETE` | `/api/v1/clusters/schedule` | Disable schedule |

## Database Modes

| Mode | Config | Best for |
|------|--------|----------|
| **SQLite** | `DATABASE_MODE=sqlite` | Local dev, self-hosted |
| **Supabase** | `DATABASE_MODE=supabase` | Production, Tenera integration |

## Integrating with Tenera

The integration is API-to-API:

1. Deploy this service (or run locally)
2. Set your `API_KEY` in both this service's `.env` and Tenera's config
3. Tenera calls the REST API to read/write persona data

```
Your App  -->  Persona Tracker  <-->  Tenera
                    |
               SQLite / Supabase
```

## Interactive Docs

Start the server and visit `http://localhost:8000/docs` for auto-generated Swagger UI.
