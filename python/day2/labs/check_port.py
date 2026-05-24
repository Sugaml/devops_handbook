#!/usr/bin/env python3
"""Classify ports as expected for a simple service map — Day 2 lab."""

PORTS: dict[str, int] = {
    "ssh": 22,
    "http": 80,
    "https": 443,
    "app": 8080,
}


def classify(port: int) -> str:
    if port < 0 or port > 65535:
        return "invalid"
    if port < 1024:
        return "privileged"
    if port in PORTS.values():
        return "registered"
    return "custom"


def main() -> None:
    for name, port in PORTS.items():
        category = classify(port)
        print(f"{name:6} {port:5} -> {category}")


if __name__ == "__main__":
    main()
