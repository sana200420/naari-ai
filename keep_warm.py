"""
Phase 4 — Uptime monitoring & cold-start mitigation
Pings /health every 10 minutes to keep the Railway service warm.
Run this as a separate process or scheduled job.
"""
import os
import time
import logging
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("naari.keepwarm")

API_URL = os.getenv("API_URL", "https://naari-ai-production.up.railway.app")
PING_INTERVAL = int(os.getenv("PING_INTERVAL_SECONDS", "600"))  # 10 minutes


def ping():
    try:
        r = requests.get(f"{API_URL}/health", timeout=30)
        if r.status_code == 200:
            logger.info(f"[OK] /health returned 200 — service warm")
        else:
            logger.warning(f"[WARN] /health returned {r.status_code}")
    except Exception as e:
        logger.error(f"[DOWN] /health failed: {e}")


if __name__ == "__main__":
    logger.info(f"Keep-warm started — pinging {API_URL} every {PING_INTERVAL}s")
    while True:
        ping()
        time.sleep(PING_INTERVAL)
