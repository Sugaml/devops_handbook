#!/usr/bin/env python3
"""One-line host resource summary — Day 1 lab."""

def main() -> None:
    hostname: str = "web-prod-01"
    cpu_percent: float = 42.3
    mem_percent: float = 71.8
    disk_percent: float = 58.0

    print(
        f"{hostname}  "
        f"CPU={cpu_percent:5.1f}%  "
        f"MEM={mem_percent:5.1f}%  "
        f"DISK={disk_percent:5.1f}%"
    )


if __name__ == "__main__":
    main()
