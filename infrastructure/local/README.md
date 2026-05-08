# Infrared Local Infrastructure

Created: 2026-05-08T10:23:49-04:00
Last updated: 2026-05-08T16:23:29-04:00

## Table of Contents

1. [Overview](#overview)
2. [Purpose](#purpose)
3. [Commands](#commands)
4. [Deferred](#deferred)

## Overview

This directory contains Docker Compose configuration for the local control plane.

## Purpose

Run the local control-plane services in a reproducible way:

- Teamserver.
- Nginx redirector.
- Local service network.
- Predictable SQLite state location.

The Compose file keeps the teamserver and redirector startup path explicit, reviewable, and easy to tear down after a lab run.

## Commands

```text
docker compose -f infrastructure/local/docker-compose.yml up -d --build
docker compose -f infrastructure/local/docker-compose.yml ps
docker compose -f infrastructure/local/docker-compose.yml down
```

The CLI wraps these through:

```text
ir lab up
ir lab down
ir lab status
```

## Services

| Service | Local Port | Purpose |
|---|---:|---|
| `teamserver` | `8000` | FastAPI control plane and SQLite persistence |
| `redirector` | `8080` | Nginx redirector for agent-facing routes |

## State

The teamserver stores SQLite state in the `teamserver-data` Docker volume at:

```text
/data/teamserver.sqlite3
```

## Validation

Validate Compose syntax:

```text
docker compose -f infrastructure/local/docker-compose.yml config
```

Start the lab:

```text
ir lab up
```

Check status:

```text
ir lab status
```

Stop the lab:

```text
ir lab down
```

## Agent Path

When the local lab is running, point the Go agent at the redirector:

```text
go run ./cmd/ir-agent --config configs/local-http-basic.json --server-url http://127.0.0.1:8080 --once
```

## Deferred

Kubernetes, cloud deployment, production hardening, and multi-host orchestration are deferred. The current Compose lab is the reproducible local baseline.
