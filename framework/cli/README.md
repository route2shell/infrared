# Infrared CLI

## Table of Contents

1. [Overview](#overview)
2. [Purpose](#purpose)
3. [Commands](#commands)
4. [Deferred](#deferred)

## Overview

This directory contains the Python operator CLI exposed as `ir`.

## Purpose

The CLI is the operator workflow layer. It turns raw teamserver API calls and local Docker Compose commands into a repeatable workflow for lab startup, profile validation, session visibility, task creation, result retrieval, and teardown.

The CLI talks to the teamserver API for operator actions. It does not talk directly to the agent or directly mutate SQLite state.

## Commands

```text
ir lab up
ir lab down
ir lab status
ir profile validate profiles/local-http-basic.yaml
ir sessions
ir sessions show <session-id>
ir task create <session-id> "whoami"
ir task list
ir results <task-id>
```

## Local Development

Run without installing:

```text
cd framework/cli
../../.venv/bin/python -m infrared_cli
```

Install the CLI into the repo virtual environment:

```text
cd framework/cli
../../.venv/bin/python -m pip install -e .
```

Then run:

```text
ir
ir server status
ir sessions
```

## Quality of Life Features

- Bare `ir` prints the launch banner, help, and quick-start commands.
- `--server-url` overrides the teamserver URL.
- `INFRARED_TEAMSERVER_URL` sets the default teamserver URL.
- `--json` prints machine-readable output for supported commands.
- Table output is used for list views.
- Lab commands use the Docker Compose file at `infrastructure/local/docker-compose.yml`.
- Profile validation parses YAML and checks required local HTTP lab fields.

## Deferred

Interactive shells, terminal dashboards, plugin systems, and multi-operator workflows are intentionally deferred. The current CLI focuses on clear, auditable commands for a single local operator.
