#!/usr/bin/env python3
"""Kubernetes cluster status via client-python."""

from __future__ import annotations

import argparse
import json
import sys
import time

from kubernetes import client, config
from kubernetes.client.rest import ApiException


def load_config(in_cluster: bool) -> None:
    if in_cluster:
        config.load_incluster_config()
    else:
        config.load_kube_config()


def list_pods(namespace: str | None, all_ns: bool) -> list[dict]:
    v1 = client.CoreV1Api()
    if all_ns:
        resp = v1.list_pod_for_all_namespaces(watch=False)
    else:
        resp = v1.list_namespaced_pod(namespace=namespace or "default")
    rows = []
    for p in resp.items:
        rows.append(
            {
                "namespace": p.metadata.namespace,
                "name": p.metadata.name,
                "phase": p.status.phase,
                "node": p.spec.node_name,
                "ready": sum(1 for c in (p.status.container_statuses or []) if c.ready),
            }
        )
    return rows


def list_deployments(all_ns: bool, namespace: str | None) -> list[dict]:
    apps = client.AppsV1Api()
    if all_ns:
        resp = apps.list_deployment_for_all_namespaces(watch=False)
    else:
        resp = apps.list_namespaced_deployment(namespace=namespace or "default")
    rows = []
    for d in resp.items:
        desired = d.spec.replicas or 0
        ready = d.status.ready_replicas or 0
        rows.append(
            {
                "namespace": d.metadata.namespace,
                "name": d.metadata.name,
                "ready": ready,
                "desired": desired,
                "ok": ready == desired and desired > 0,
            }
        )
    return rows


def wait_deployment(namespace: str, name: str, timeout: int) -> bool:
    apps = client.AppsV1Api()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            d = apps.read_namespaced_deployment(name, namespace)
        except ApiException as exc:
            print(f"ERROR: {exc.reason}", file=sys.stderr)
            return False
        desired = d.spec.replicas or 0
        ready = d.status.ready_replicas or 0
        if ready == desired and desired > 0:
            return True
        time.sleep(5)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Kubernetes status lab")
    parser.add_argument("--in-cluster", action="store_true")
    parser.add_argument("-n", "--namespace", help="Namespace (default: default)")
    parser.add_argument("-A", "--all-namespaces", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("pods", help="List pods")
    sub.add_parser("deployments", help="List deployments")
    p_wait = sub.add_parser("wait-deploy", help="Wait for deployment ready")
    p_wait.add_argument("name")
    p_wait.add_argument("namespace")
    p_wait.add_argument("--timeout", type=int, default=300)

    args = parser.parse_args()

    try:
        load_config(args.in_cluster)
    except config.ConfigException as exc:
        print(f"ERROR: kubeconfig: {exc}", file=sys.stderr)
        return 1

    if args.command == "pods":
        rows = list_pods(args.namespace, args.all_namespaces)
        print(json.dumps({"pods": rows}, indent=2))
        return 0

    if args.command == "deployments":
        rows = list_deployments(args.all_namespaces, args.namespace)
        failed = sum(1 for r in rows if not r["ok"])
        print(json.dumps({"deployments": rows, "not_ready": failed}, indent=2))
        return 1 if failed else 0

    if args.command == "wait-deploy":
        ok = wait_deployment(args.namespace, args.name, args.timeout)
        print(json.dumps({"deployment": args.name, "ready": ok}, indent=2))
        return 0 if ok else 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
