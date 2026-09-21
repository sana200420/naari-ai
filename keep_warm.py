"""
Phase 4 — Uptime monitoring & cold-start mitigation (manual/local tool).

Was pointed at the Railway backend, retired since ADR 0001's amendment --
pinging it did nothing (docs/runbook.md's own service table says so; this
script disagreed with its own project's runbook). Retargeted to the live
HF Space.

There is no /health endpoint -- Gradio Spaces don't expose one, and this
project's API surface is entirely gr.api (see app.py: ask_api,
retrieve_api). So "is it warm" is checked the way the runbook's own
"Quick health check" section already does it: fetch the root page (proves
the container is up) and call /ask with a fixed benign query (proves the
actual model + retrieval pipeline has finished warming up, not just that
the process exists).

For routine automated monitoring, prefer
.github/workflows/keep_warm.yml -- it runs this same check on a schedule
with no one needing to leave a terminal open. This script is for the
"run it 30 minutes before a demo" case docs/runbook.md's pre-demo
checklist already calls for, where you want ongoing pings visible in
your own terminal rather than in the Actions tab.

    python3 keep_warm.py
    PING_INTERVAL_SECONDS=300 python3 keep_warm.py
"""
import logging
import os
import time

import requests
from gradio_client import Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("naari.keepwarm")

SPACE = os.getenv("SPACE", "Sanapalijo/naari-ai")
ROOT_URL = os.getenv("ROOT_URL", "https://sanapalijo-naari-ai.hf.space")
PING_INTERVAL = int(os.getenv("PING_INTERVAL_SECONDS", "600"))  # 10 minutes
TEST_QUERY = "حيض جي چڪر ڇا آهي؟"

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = Client(SPACE)
    return _client


def ping() -> bool:
    """One check: root page up, then a real /ask call through the pipeline.

    Returns True/False rather than just logging, so a caller (the CI
    one-shot entrypoint, keep_warm_once.py) can turn "down" into a non-zero
    exit code and make the failure visible in the Actions tab. A slow but
    successful cold-start response still returns True -- only a genuinely
    unreachable container or a broken /ask call returns False.
    """
    try:
        r = requests.get(ROOT_URL, timeout=30)
        if r.status_code != 200:
            logger.warning(f"[WARN] root page returned {r.status_code}")
            return False
    except Exception as e:
        logger.error(f"[DOWN] container unreachable: {e}")
        return False

    try:
        t0 = time.perf_counter()
        _get_client().predict(query=TEST_QUERY, language="sindhi", api_name="/ask")
        elapsed = time.perf_counter() - t0
        cold = " (looked like a cold start)" if elapsed > 5 else ""
        logger.info(f"[OK] pipeline warm, answered in {elapsed:.1f}s{cold}")
        return True
    except Exception as e:
        logger.error(f"[DOWN] /ask failed even though the container is up: {e}")
        return False


if __name__ == "__main__":
    logger.info(f"Keep-warm started -- pinging {SPACE} every {PING_INTERVAL}s")
    while True:
        ping()
        time.sleep(PING_INTERVAL)
