"""CLI entrypoint for handbook-deploy."""

from handbook_deploy.util import banner


def main() -> None:
    print(banner("payments-api", "staging"))
    print("Use Day 8 argparse for real flags.")


if __name__ == "__main__":
    main()
