"""Watch landing/inbox and label each review with the local Ollama model."""

import argparse
import time

import httpx

from worker.config import WorkerSettings
from worker.pipeline import ensure_dirs, run_once


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="process what is waiting, then exit")
    args = parser.parse_args()

    settings = WorkerSettings()
    ensure_dirs(settings.landing_dir)
    with httpx.Client() as client:
        if args.once:
            run_once(settings, client)
            return
        while True:
            run_once(settings, client)
            time.sleep(settings.poll_seconds)


if __name__ == "__main__":
    main()
