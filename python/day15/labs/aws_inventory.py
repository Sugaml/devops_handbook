#!/usr/bin/env python3
"""AWS inventory lab — STS, EC2, and S3 via boto3."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError


def get_session(profile: str | None, region: str) -> boto3.Session:
    kwargs: dict = {"region_name": region}
    if profile:
        kwargs["profile_name"] = profile
    return boto3.Session(**kwargs)


def cmd_identity(session: boto3.Session) -> int:
    sts = session.client("sts")
    ident = sts.get_caller_identity()
    print(json.dumps(ident, indent=2, default=str))
    return 0


def cmd_ec2(session: boto3.Session, state: str) -> int:
    ec2 = session.client("ec2")
    paginator = ec2.get_paginator("describe_instances")
    rows = []
    for page in paginator.paginate(
        Filters=[{"Name": "instance-state-name", "Values": [state]}]
    ):
        for res in page["Reservations"]:
            for inst in res["Instances"]:
                name = next(
                    (t["Value"] for t in inst.get("Tags", []) if t["Key"] == "Name"),
                    "-",
                )
                rows.append(
                    {
                        "instance_id": inst["InstanceId"],
                        "name": name,
                        "type": inst["InstanceType"],
                        "state": inst["State"]["Name"],
                        "az": inst["Placement"]["AvailabilityZone"],
                    }
                )
    print(json.dumps({"instances": rows, "count": len(rows)}, indent=2))
    return 0


def cmd_s3(session: boto3.Session) -> int:
    s3 = session.client("s3")
    resp = s3.list_buckets()
    names = [b["Name"] for b in resp.get("Buckets", [])]
    print(json.dumps({"buckets": names}, indent=2))
    return 0


def cmd_s3_upload(session: boto3.Session, local: Path, s3_uri: str) -> int:
    if "/" not in s3_uri:
        print("ERROR: s3_uri must be bucket/key", file=sys.stderr)
        return 1
    bucket, key = s3_uri.split("/", 1)
    s3 = session.client("s3")
    s3.upload_file(str(local), bucket, key)
    print(json.dumps({"uploaded": s3_uri}, indent=2))
    return 0


def cmd_ec2_tag(session: boto3.Session, instance_id: str, tag: str, dry_run: bool) -> int:
    key, _, value = tag.partition("=")
    if not value:
        print("ERROR: tag must be Key=Value", file=sys.stderr)
        return 1
    ec2 = session.client("ec2")
    try:
        ec2.create_tags(
            Resources=[instance_id],
            Tags=[{"Key": key, "Value": value}],
            DryRun=dry_run,
        )
    except ClientError as exc:
        code = exc.response["Error"]["Code"]
        if code == "DryRunOperation":
            print(json.dumps({"dry_run": True, "would_tag": tag}, indent=2))
            return 0
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"tagged": instance_id, "tag": tag}, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="boto3 AWS inventory lab")
    parser.add_argument("--profile", help="AWS profile name")
    parser.add_argument("--region", default="us-east-1")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("identity", help="STS get-caller-identity")
    p_ec2 = sub.add_parser("ec2", help="List EC2 instances")
    p_ec2.add_argument("--state", default="running")
    sub.add_parser("s3", help="List S3 buckets")
    p_up = sub.add_parser("s3-upload", help="Upload file to s3://bucket/key")
    p_up.add_argument("local", type=Path)
    p_up.add_argument("s3_uri")
    p_tag = sub.add_parser("ec2-tag", help="Tag an instance")
    p_tag.add_argument("instance_id")
    p_tag.add_argument("tag", help="Key=Value")
    p_tag.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    try:
        session = get_session(args.profile, args.region)
    except NoCredentialsError:
        print("ERROR: No AWS credentials found. Configure AWS_PROFILE or env vars.", file=sys.stderr)
        return 1

    handlers = {
        "identity": lambda: cmd_identity(session),
        "ec2": lambda: cmd_ec2(session, args.state),
        "s3": lambda: cmd_s3(session),
        "s3-upload": lambda: cmd_s3_upload(session, args.local, args.s3_uri),
        "ec2-tag": lambda: cmd_ec2_tag(session, args.instance_id, args.tag, args.dry_run),
    }
    return handlers[args.command]()


if __name__ == "__main__":
    raise SystemExit(main())
