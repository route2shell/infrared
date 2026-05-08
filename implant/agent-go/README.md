# Infrared Go Test Agent

Created: 2026-05-08T10:23:49-04:00
Last updated: 2026-05-08T16:23:29-04:00

## Table of Contents

1. [Overview](#overview)
2. [Purpose](#purpose)
3. [Behavior](#behavior)
4. [Deferred](#deferred)

## Overview

This directory contains the Go test agent used by the local Windows 11 lab.

## Purpose

The agent completes the local tasking loop:

```text
load config
check in
poll for task
execute supported V1 validation task
post result
sleep
repeat
```

The agent is intentionally simple and visible. It is designed to prove check-in, polling, task execution, result posting, and telemetry observations without implementing persistence or evasion.

## Behavior

- Load local configuration.
- Check in to the redirector or teamserver.
- Poll for pending tasks.
- Execute only supported validation commands from a narrow allowlist.
- Return stdout, stderr, exit code, and basic timing metadata.

## Supported Commands

The agent does not execute arbitrary shell commands. It supports only:

- `whoami`
- `hostname`
- `pwd`
- `echo <text>`

Unsupported commands return a failed result with exit code `126`.

## Local Development

Run tests:

```text
go test ./...
```

Build the agent:

```text
go build -o bin/ir-agent ./cmd/ir-agent
```

Run one check-in and poll cycle:

```text
go run ./cmd/ir-agent --config configs/local-http-basic.json --once
```

Override local test settings without editing the config:

```text
go run ./cmd/ir-agent --config configs/local-http-basic.json --server-url http://127.0.0.1:8765 --agent-id agent-local-1 --once
```

Run continuously:

```text
go run ./cmd/ir-agent --config configs/local-http-basic.json
```

## Configuration

The agent uses a small JSON config:

```json
{
  "agent_id": "agent-local-1",
  "server_url": "http://127.0.0.1:8000",
  "poll_interval_seconds": 5,
  "timeout_seconds": 10,
  "metadata": {
    "profile": "local-http-basic",
    "phase": "v1"
  }
}
```

In the VMware Workstation Pro workflow, the Windows command usually overrides `server_url` so the agent points at the host's VMware NAT address:

```text
.\ir-agent.exe --config .\local-http-basic.json --server-url http://<HOST_REACHABLE_IP>:8080 --agent-id win-vm-v1
```

## Deferred

Persistence, stealth, privilege escalation, injection, credential access, and dynamic module loading are intentionally out of scope for this agent.
