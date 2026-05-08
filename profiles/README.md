# Infrared Profiles

## Table of Contents

1. [Overview](#overview)
2. [Purpose](#purpose)
3. [Local HTTP Profile](#local-http-profile)
4. [Deferred](#deferred)

## Overview

This directory contains YAML profiles for local lab configuration.

## Purpose

Profiles document the expected lab shape so service addresses, route names, and telemetry assumptions do not live only in code or walkthrough prose.

## Local HTTP Profile

```text
profiles/local-http-basic.yaml
```

The profile includes:

- Profile name.
- HTTP transport settings.
- Redirector host, port, and routes.
- Teamserver host and port.
- Telemetry expectations.

## Validate

From the repository root:

```text
ir profile validate profiles/local-http-basic.yaml
```

Or without relying on the installed entrypoint:

```text
cd framework/cli
../../.venv/bin/python -m infrared_cli profile validate ../../profiles/local-http-basic.yaml
```

## Fields

`local-http-basic.yaml` defines:

- `operator.cli_name`: expected operator command name.
- `transport.type`: transport type, currently `http`.
- `transport.beacon_interval_seconds`: default polling interval for lab runs.
- `transport.jitter_percent`: present for profile shape, currently `0`.
- `redirector`: Nginx host, port, and agent-facing routes.
- `teamserver`: local FastAPI teamserver host and port.
- `telemetry`: expected manual observation categories for the lab.

## Deferred

Profile inheritance, generated redirector configs, complex schema versioning, and advanced transport behavior are deferred until the local HTTP profile is used consistently across more components.
