# Docker for DevOps — 7-Day Handbook

A hands-on path from container fundamentals to production-grade Docker workflows. Each day builds on the last with commands, patterns, and labs you can run on any machine with Docker Engine installed.

## Structure

| Day | Topic | Folder |
|-----|--------|--------|
| 1 | Containers, images, and the Docker CLI | [day1](./day1/) |
| 2 | Dockerfiles, layers, and image builds | [day2](./day2/) |
| 3 | Docker Compose and multi-container apps | [day3](./day3/) |
| 4 | Networking — bridge, DNS, and service discovery | [day4](./day4/) |
| 5 | Volumes, bind mounts, and data persistence | [day5](./day5/) |
| 6 | Security, scanning, and production hardening | [day6](./day6/) |
| 7 | Registries, CI/CD, Swarm, and troubleshooting | [day7](./day7/) |

## Prerequisites

- Basic Linux CLI comfort ([Linux handbook](../linux/README.md) Day 1–2 is enough).
- A machine with 4 GB+ RAM free for labs.
- Admin rights to install Docker (or use a cloud VM).

## How to use this handbook

1. Install Docker Engine (Day 1 covers all platforms).
2. Run every command yourself; use throwaway containers (`--rm`) freely.
3. Complete each day's **Lab** before moving on.
4. Keep notes on flags and patterns you reuse at work.

## Recommended lab setup

```bash
# Verify Docker is running
docker version
docker run hello-world

# Optional helpers used throughout the handbook
docker pull alpine:3.20
docker pull nginx:1.27-alpine
docker pull postgres:16-alpine
docker pull redis:7-alpine
```

## Design notes

- Examples use official images and minimal Dockerfiles — swap in your stack as you learn.
- Production callouts mark patterns used in real CI/CD and Kubernetes-adjacent workflows.
- Labs live in each day's folder under `labs/` where sample files are provided.
