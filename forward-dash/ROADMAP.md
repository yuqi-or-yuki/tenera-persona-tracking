# Roadmap

## v0.1.0 — Foundation (current)
- [x] Persona CRUD (create, list, get, update, delete)
- [x] Entity key-value properties per persona
- [x] Event tracking with timeline
- [x] API key authentication
- [x] SQLite local database
- [ ] CLI powered by FastAPI server
- [ ] End-to-end working flow

## v0.2.0 — Production Ready
- [ ] Supabase PostgreSQL support with Alembic migrations
- [ ] Batch event ingestion endpoint (`POST /api/v1/batch`)
- [ ] Event property indexing for faster queries
- [ ] Rate limiting

## v0.3.0 — Tenera Integration
- [ ] Export endpoint (dump personas + entities + events as JSON/CSV)
- [ ] Tenera-compatible data format converter
- [ ] Webhook support (notify Tenera on persona changes)

## v0.4.0 — Clustering & Cohorts
- [ ] Auto-clustering personas by entity similarity
- [ ] Cohort definitions (rule-based grouping)
- [ ] Cohort membership tracking over time

## Future
- [ ] Real-time Supabase subscriptions
- [ ] Python SDK for programmatic usage
- [ ] Dashboard UI (optional, separate package)
