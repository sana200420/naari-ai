"""One-shot wrapper around keep_warm.py's ping() for CI.

keep_warm.py's own __main__ loops forever with a sleep, which is right for
"leave it running on a laptop before a demo" but wrong for a scheduled CI
job, which needs to do one check and exit with a code that reflects success
or failure -- see .github/workflows/keep_warm.yml. Reuses ping() rather
than duplicating the check, so the manual and automated paths can't drift
apart.
"""
import sys

from keep_warm import ping

if __name__ == "__main__":
    sys.exit(0 if ping() else 1)
