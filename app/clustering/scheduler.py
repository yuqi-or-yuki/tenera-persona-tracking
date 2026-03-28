"""Cron-based clustering scheduler.

Runs clustering on a configurable schedule using APScheduler.
The schedule is stored in a config file and can be updated via API/CLI.
"""

import json
import logging
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

_scheduler = AsyncIOScheduler()
_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "scheduler.json"


def _load_config() -> dict:
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH) as f:
            return json.load(f)
    return {"enabled": False, "cron": "0 2 * * *", "algorithm": "kmeans", "params": {}}


def _save_config(config: dict):
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


async def _run_scheduled_clustering():
    """Execute a clustering run from the scheduler."""
    from app.clustering.service import run_clustering_from_db

    config = _load_config()
    logger.info(f"Scheduled clustering run: algorithm={config['algorithm']}")
    try:
        result = await run_clustering_from_db(
            algorithm=config["algorithm"], params=config.get("params", {})
        )
        logger.info(
            f"Scheduled clustering complete: {result['num_clusters']} clusters, "
            f"run_id={result['run_id']}"
        )
    except Exception as e:
        logger.error(f"Scheduled clustering failed: {e}")


def start_scheduler():
    """Start the scheduler with the saved config."""
    config = _load_config()
    if config.get("enabled"):
        _scheduler.add_job(
            _run_scheduled_clustering,
            CronTrigger.from_crontab(config["cron"]),
            id="clustering_job",
            replace_existing=True,
        )
        logger.info(f"Clustering scheduler started: cron='{config['cron']}'")

    if not _scheduler.running:
        _scheduler.start()


def update_schedule(cron_expression: str, algorithm: str = "kmeans", params: dict = None):
    """Update the clustering schedule."""
    config = {
        "enabled": True,
        "cron": cron_expression,
        "algorithm": algorithm,
        "params": params or {},
    }
    _save_config(config)

    # Update the running scheduler
    if _scheduler.running:
        try:
            _scheduler.remove_job("clustering_job", jobstore="default")
        except Exception:
            pass
    _scheduler.add_job(
        _run_scheduled_clustering,
        CronTrigger.from_crontab(cron_expression),
        id="clustering_job",
        replace_existing=True,
    )
    if not _scheduler.running:
        _scheduler.start()

    logger.info(f"Schedule updated: cron='{cron_expression}', algorithm='{algorithm}'")
    return config


def disable_schedule():
    """Disable the clustering schedule."""
    config = _load_config()
    config["enabled"] = False
    _save_config(config)

    try:
        _scheduler.remove_job("clustering_job")
    except Exception:
        pass

    logger.info("Clustering scheduler disabled")
    return config


def get_schedule() -> dict:
    """Get the current schedule config."""
    return _load_config()
