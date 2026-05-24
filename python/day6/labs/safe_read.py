#!/usr/bin/env python3
"""Read JSON config with explicit error handling — Day 6 lab."""

import json
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger(__name__)


def load_json(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        log.error("config not found: %s", path)
        raise SystemExit(2) from None
    except OSError as exc:
        log.exception("failed to read %s", path)
        raise SystemExit(3) from exc
    else:
        log.info("read %d bytes from %s", len(text), path.name)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        log.error("invalid JSON in %s: %s", path, exc)
        raise SystemExit(4) from exc
    finally:
        log.debug("load_json finished for %s", path)


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "config.json"
    data = load_json(path)
    log.info("keys: %s", sorted(data.keys()))


if __name__ == "__main__":
    main()
