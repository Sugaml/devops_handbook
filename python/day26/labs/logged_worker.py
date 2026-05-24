#!/usr/bin/env python3
"""Simulated worker emitting structured logs."""
from __future__ import annotations

import argparse
import os
import random
import time
import uuid

import structlog

from logging_setup import configure_logging


def run(count: int) -> None:
    log = structlog.get_logger()
    job_id = str(uuid.uuid4())[:8]
    structlog.contextvars.bind_contextvars(job_id=job_id, component="logged_worker")

    log.info("job_started", target_count=count)
    for i in range(count):
        structlog.contextvars.bind_contextvars(iteration=i + 1)
        time.sleep(0.2)
        if random.random() < 0.15:
            log.warning("transient_error", retry=True, error="connection reset")
        else:
            log.info("item_processed", item=f"task-{i + 1}")
    log.info("job_finished", duration_ms=int(count * 200))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=3)
    args = parser.parse_args()
    json_output = os.environ.get("LOG_FORMAT", "json") == "json"
    configure_logging(json_output=json_output)
    run(args.count)


if __name__ == "__main__":
    main()
