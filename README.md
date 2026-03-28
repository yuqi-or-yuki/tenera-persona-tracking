# Tenera Persona Tracking

Open-source, CLI-first persona tracking and cohort analytics engine. Designed to integrate with [Tenera](https://tenera.ai).

## Quick Start

```bash
git clone https://github.com/yuqi-or-yuki/tenera-persona-tracking.git
cd tenera-persona-tracking
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip && pip install -e .
cp .env.example .env
tpt serve
```

Server runs at `http://localhost:8000` | API docs at `http://localhost:8000/docs` | Dashboard at `http://localhost:8000/`

## Usage

```bash
# Create a persona
tpt persona create user_123 --name "Jane Doe" -e plan=enterprise -e company="Acme Corp"

# Add properties
tpt entity set user_123 role engineering_manager

# Track events
tpt track user_123 plan_upgrade -p '{"from": "pro", "to": "enterprise"}'

# View timeline
tpt events user_123

# Run clustering
tpt cluster run
tpt cluster results

# Schedule recurring clustering (cron)
tpt cluster schedule "0 2 * * *"
```

See [`examples/`](examples/) for runnable scripts.

## Documentation

- [Design & Architecture](doc/DESIGN.md)
- [Clustering Algorithms](doc/CLUSTERING.md)
- [API Reference](doc/API.md)
- [Roadmap](doc/ROADMAP.md)

## License

MIT
