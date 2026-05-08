# Infrared Teamserver

## Table of Contents

1. [Overview](#overview)
2. [Purpose](#purpose)
3. [Routes](#routes)
4. [Persistence](#persistence)
5. [Deferred](#deferred)

## Overview

This directory contains the Python FastAPI teamserver for the local control plane.

## Purpose

The teamserver is the system of record for the lab. It tracks sessions, accepts operator-created tasks, delivers tasks to agents, receives results, and records basic lifecycle events.

The operator CLI talks to the operator-facing routes. The agent talks to the agent-facing routes through the Nginx redirector.

## Routes

```text
GET  /health
POST /api/agent/checkin
GET  /api/agent/{agent_id}/tasks
POST /api/agent/{agent_id}/results
GET  /api/operator/sessions
GET  /api/operator/sessions/{session_id}
POST /api/operator/tasks
GET  /api/operator/tasks
GET  /api/operator/results/{task_id}
```

## Persistence

The teamserver uses SQLite for sessions, tasks, results, and events. The default database path is:

```text
framework/teamserver/data/teamserver.sqlite3
```

Override the path with:

```text
INFRARED_TEAMSERVER_DB=/path/to/teamserver.sqlite3
```

## Local Development

Install dependencies from this directory:

```text
python3 -m pip install -r requirements.txt
```

Start the teamserver:

```text
uvicorn app.main:app --reload
```

Run tests:

```text
python3 -m pytest tests
```

## Reset Local State

Stop the teamserver, then remove the local SQLite database file:

```text
rm data/teamserver.sqlite3
```

## Deferred

Authentication, multi-user workflows, advanced scheduling, transport encryption, and production database backends are deferred. Those features should be added only after the local tasking lifecycle remains easy to test and explain.
