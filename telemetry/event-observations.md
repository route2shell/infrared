# Infrared V1 Event Observations

## Table of Contents

1. [Overview](#overview)
2. [Run Context](#run-context)
3. [Observation Sequence](#observation-sequence)
4. [Teamserver Observations](#teamserver-observations)
5. [Redirector Observations](#redirector-observations)
6. [Windows 11 Observations](#windows-11-observations)
7. [Agent Console Observations](#agent-console-observations)
8. [Correlation Checklist](#correlation-checklist)
9. [Documentation Notes](#documentation-notes)

## Overview

This document records what to observe during the first complete V1 tasking cycle:

```text
Windows 11 agent -> Nginx redirector -> Teamserver -> operator CLI -> task result
```

The expected task is:

```text
whoami
```

## Run Context

Record these values during each run:

| Field | Value |
|---|---|
| Run date and time | `YYYY-MM-DD HH:MM timezone` |
| VMware network mode | `NAT`, `host-only`, or `bridged` |
| Host redirector address | `http://<HOST_REACHABLE_IP>:8080` |
| Agent ID | `win-vm-v1` |
| Session ID | From `.venv/bin/ir sessions` |
| Task ID | From `.venv/bin/ir task create <SESSION_ID> "whoami"` |
| Windows 11 VM hostname | From `ir sessions` or Windows hostname |
| Windows 11 username | From result stdout |

## Observation Sequence

| Step | Action | Primary Evidence |
|---:|---|---|
| 1 | Start lab services | `ir lab status`, teamserver health, redirector health |
| 2 | Start Windows 11 agent | Agent console and redirector `/api/agent/checkin` log |
| 3 | List sessions | Teamserver session record for `win-vm-v1` |
| 4 | Create `whoami` task | Teamserver task record with `pending` status |
| 5 | Agent polls tasks | Redirector `/api/agent/win-vm-v1/tasks` log and task status `delivered` |
| 6 | Agent posts result | Redirector `/api/agent/win-vm-v1/results` log and result record |
| 7 | Retrieve result | CLI output showing `completed`, exit code `0`, and stdout |
| 8 | Review Windows telemetry | Sysmon process and network observations |

## Teamserver Observations

The V1 teamserver stores state in SQLite. In the Compose lab, the database lives in the `teamserver-data` Docker volume at:

```text
/data/teamserver.sqlite3
```

The important V1 tables are:

| Table | Evidence |
|---|---|
| `sessions` | Agent registration, host metadata, username, platform, check-in count |
| `tasks` | Command, status, creation time, delivery time, completion time |
| `results` | Stdout, stderr, exit code, result status |
| `events` | Lifecycle records such as registration, task creation, task delivery, and result ingestion |

Expected event types for one successful run:

```text
agent.registered
task.created
task.delivered
result.received
```

If the same agent checks in repeatedly, later check-ins use:

```text
agent.checkin
```

Operator-facing commands that confirm state:

```text
.venv/bin/ir sessions
.venv/bin/ir task list
.venv/bin/ir results <TASK_ID>
```

## Redirector Observations

The Compose-managed Nginx redirector writes access logs to:

```text
infrastructure/nginx/logs/access.log
```

Expected paths for `agent_id=win-vm-v1`:

```text
/api/agent/checkin
/api/agent/win-vm-v1/tasks
/api/agent/win-vm-v1/results
```

The access log format records:

- source IP, which should be the Windows 11 VM or VMware NAT-facing address seen by the host;
- request path and HTTP method;
- HTTP status;
- user agent;
- upstream address;
- request time.

For the Compose lab, the upstream should be:

```text
teamserver:8000
```

## Windows 11 Observations

Primary Windows 11 telemetry comes from Sysmon if installed and configured.

Expected high-signal observations:

| Source | Event | Expected Signal |
|---|---|---|
| Sysmon | Event ID 1, Process Create | `C:\Infrared\ir-agent.exe` starts from PowerShell |
| Sysmon | Event ID 3, Network Connection | `ir-agent.exe` connects to `<HOST_REACHABLE_IP>:8080` |
| Sysmon | Event ID 5, Process Terminated | Optional confirmation when the agent exits |
| PowerShell console | Agent logs | Check-in, poll, task execution, and result post messages |

The V1 agent implements `whoami` internally using Go user lookup behavior. It does not spawn `whoami.exe` for the V1 task. For this reason, a successful `whoami` task should show the agent process and network activity, not a child `whoami.exe` process.

## Agent Console Observations

Expected console messages during a successful continuous run:

```text
checked in: agent_id=win-vm-v1 session_id=<session-id>
no pending tasks
running task_id=<task-id> command="whoami"
posted result: task_id=<task-id> status=completed exit_code=0
```

Expected result:

```text
status=completed
exit_code=0
stdout=<windows-user-context>
```

## Correlation Checklist

Use this checklist to connect one action across evidence sources:

| Question | Evidence |
|---|---|
| Did the agent check in? | `ir sessions`, teamserver `sessions`, redirector `/api/agent/checkin` |
| Did the operator create the task? | `ir task list`, teamserver `tasks`, teamserver `task.created` event |
| Did the agent receive the task? | redirector `/tasks`, task status `delivered`, teamserver `task.delivered` event |
| Did the agent post a result? | redirector `/results`, teamserver `results`, `result.received` event |
| Did the result match expected behavior? | `ir results <TASK_ID>` shows completed status and user context |
| Did Windows show target-side activity? | Sysmon process creation and network connection for `ir-agent.exe` |

## Documentation Notes

When turning observations into portfolio notes, keep the phrasing precise:

- Good: "The V1 task produced agent process execution, outbound HTTP to the redirector, redirector access logs, teamserver task state changes, and a completed result."
- Avoid: "The task bypassed detection" or "The agent was stealthy."

V1 telemetry is about visibility and correlation, not evasion.
