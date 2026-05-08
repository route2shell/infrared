# Infrared Nginx Redirector

Created: 2026-05-08T10:23:49-04:00
Last updated: 2026-05-08T16:23:29-04:00

## Table of Contents

1. [Overview](#overview)
2. [Purpose](#purpose)
3. [Forwarded Routes](#forwarded-routes)
4. [Deferred](#deferred)

## Overview

This directory contains the local Nginx redirector configuration.

## Purpose

Nginx models the redirector layer between the test agent and the teamserver. The redirector exposes only agent-facing routes and forwards them to the backend control plane.

This separation keeps operator-facing routes off the agent-facing surface and creates useful infrastructure telemetry through access logs.

## Forwarded Routes

```text
/api/agent/checkin
/api/agent/{agent_id}/tasks
/api/agent/{agent_id}/results
```

Operator-facing routes remain directly reachable on the teamserver and are not exposed through the redirector.

## Local Ports

| Service | Address |
|---|---|
| Nginx redirector | `http://127.0.0.1:8080` |
| Teamserver upstream | `http://127.0.0.1:8000` |

## Validation

Validate the config from this directory:

```text
nginx -t -p "$(pwd)" -c nginx.conf
```

Run the redirector locally:

```text
nginx -p "$(pwd)" -c nginx.conf
```

Stop the local redirector:

```text
nginx -p "$(pwd)" -c nginx.conf -s stop
```

Health check:

```text
curl http://127.0.0.1:8080/redirector/health
```

Expected response:

```text
ok
```

## Agent Traffic

When the teamserver is running on `127.0.0.1:8000`, point the Go agent at the redirector:

```text
go run ./cmd/ir-agent --config configs/local-http-basic.json --server-url http://127.0.0.1:8080 --once
```

The redirector forwards only agent-facing routes and returns `404` for all other routes.

## Logs

Nginx writes local logs under:

```text
infrastructure/nginx/logs/
```

The access log uses the `infrared_agent` format and records request path, status, upstream address, user agent, and request time.

## Compose Variant

`nginx.compose.conf` is used by the Phase 7 Docker Compose lab. It has the same route policy as `nginx.conf`, but forwards to the Compose service name:

```text
teamserver:8000
```

## Deferred

TLS automation, cloud redirectors, domain fronting, traffic shaping, and multi-hop routing are deferred. The current redirector is a local architecture model, not a covert transport or evasion layer.
