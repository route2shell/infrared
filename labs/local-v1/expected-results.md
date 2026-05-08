# Infrared Local V1 Expected Results

## Table of Contents

1. [Overview](#overview)
2. [Service Expectations](#service-expectations)
3. [Profile Expectations](#profile-expectations)
4. [Connectivity Expectations](#connectivity-expectations)
5. [Agent Expectations](#agent-expectations)
6. [Session Expectations](#session-expectations)
7. [Task Expectations](#task-expectations)
8. [Result Expectations](#result-expectations)
9. [Redirector Log Expectations](#redirector-log-expectations)
10. [Failure Expectations](#failure-expectations)

## Overview

This document defines what a successful V1 VMware Workstation Pro Windows 11 VM lab run should look like. Exact timestamps, session IDs, task IDs, VMware network addresses, and Windows account names will vary by run.

## Service Expectations

After:

```text
.venv/bin/ir lab up
.venv/bin/ir lab status
```

Expected outcome:

| Component | Expected Result |
|---|---|
| Teamserver | Running and healthy on `127.0.0.1:8000` |
| Redirector | Running and healthy on `127.0.0.1:8080` |
| SQLite state | Stored in the Compose `teamserver-data` volume |
| Operator API | Reachable directly through the teamserver |
| Agent API | Reachable through the redirector |

Health checks:

```text
curl -sS http://127.0.0.1:8000/health
curl -sS http://127.0.0.1:8080/redirector/health
```

The redirector health response should be:

```text
ok
```

## Profile Expectations

After:

```text
.venv/bin/ir profile validate profiles/local-http-basic.yaml
```

Expected outcome:

```text
Valid yes
```

The profile should align with:

| Field | Expected Value |
|---|---|
| `transport.type` | `http` |
| `teamserver.host` | `127.0.0.1` |
| `teamserver.port` | `8000` |
| `redirector.host` | `127.0.0.1` |
| `redirector.port` | `8080` |
| `redirector.routes.checkin` | `/api/agent/checkin` |
| `redirector.routes.tasks` | `/api/agent/{agent_id}/tasks` |
| `redirector.routes.results` | `/api/agent/{agent_id}/results` |

## Connectivity Expectations

From the Windows 11 VM:

```text
Test-NetConnection <HOST_REACHABLE_IP> -Port 8080
```

Expected TCP result:

```text
TcpTestSucceeded : True
```

From the Windows 11 VM:

```text
Invoke-WebRequest http://<HOST_REACHABLE_IP>:8080/redirector/health -UseBasicParsing
```

Expected content:

```text
ok
```

For the recommended VMware NAT setup, `<HOST_REACHABLE_IP>` should be the operator host's `vmnet8` IPv4 address. For a VMware host-only setup, it should be the host's `vmnet1` IPv4 address.

## Agent Expectations

For a one-cycle smoke test:

```text
.\ir-agent.exe --config .\local-http-basic.json --server-url http://<HOST_REACHABLE_IP>:8080 --agent-id win-vm-v1 --once
```

Expected logs when no task is pending:

```text
checked in: agent_id=win-vm-v1 session_id=<session-id>
no pending tasks
```

For the full walkthrough, the agent should stay running and poll every configured interval:

```text
.\ir-agent.exe --config .\local-http-basic.json --server-url http://<HOST_REACHABLE_IP>:8080 --agent-id win-vm-v1
```

Expected logs after a task is created:

```text
running task_id=<task-id> command="whoami"
posted result: task_id=<task-id> status=completed exit_code=0
```

## Session Expectations

After the agent checks in:

```text
.venv/bin/ir sessions
```

Expected outcome:

| Field | Expected Result |
|---|---|
| Agent ID | `win-vm-v1` |
| Session ID | Present and usable for task creation |
| Hostname | Windows 11 VM hostname reported by the agent |
| Username | Windows user context reported by the agent |
| Last check-in | Recent timestamp |

## Task Expectations

After:

```text
.venv/bin/ir task create <SESSION_ID> "whoami"
```

Expected outcome:

| Field | Expected Result |
|---|---|
| Task ID | New numeric task identifier |
| Session ID | Matches the Windows 11 VM session |
| Command | `whoami` |
| Initial status | `pending` |
| Later status | `delivered`, then `completed` after agent result posting |

Supported V1 validation commands:

- `whoami`
- `hostname`
- `pwd`
- `echo <text>`

## Result Expectations

After:

```text
.venv/bin/ir results <TASK_ID>
```

Expected outcome for `whoami`:

| Field | Expected Result |
|---|---|
| Status | `completed` |
| Exit code | `0` |
| Stdout | Windows account context, usually `hostname\username` or `domain\username` |
| Stderr | Empty for a successful run |

The exact `stdout` value depends on how the Windows 11 VM user is configured.

## Redirector Log Expectations

After a successful check-in, poll, and result post, `infrastructure/nginx/logs/access.log` should contain agent-facing route activity:

```text
/api/agent/checkin
/api/agent/win-vm-v1/tasks
/api/agent/win-vm-v1/results
```

This confirms the V1 infrastructure path:

```text
Windows 11 agent -> Nginx redirector -> Teamserver
```

## Failure Expectations

Some failures are expected and useful during validation:

| Symptom | Likely Cause | Expected Fix |
|---|---|---|
| `TcpTestSucceeded : False` | Windows 11 VM cannot reach host or host firewall blocks port `8080` | For VMware NAT, use the host `vmnet8` IPv4 address and allow lab traffic to `8080` |
| Redirector health does not return `ok` | Redirector service is not running or wrong URL is used | Run `.venv/bin/ir lab status` and test host-local redirector health |
| Agent check-in fails | Agent points to `127.0.0.1` inside the VM or wrong port | Use `--server-url http://<HOST_REACHABLE_IP>:8080` |
| No session appears | Agent did not complete check-in | Review agent logs and redirector access logs |
| Task remains pending | Agent is stopped or has not polled since task creation | Start the agent continuously or rerun with `--once` |
| Result status is `failed` with exit code `126` | Unsupported command | Use the V1 command allowlist |

## Final V1 Acceptance Expectations

V1 is accepted when the final walkthrough demonstrates:

- Local control-plane startup through Docker Compose.
- Profile validation through `ir profile validate`.
- Windows 11 VM connectivity to the redirector.
- Agent check-in through the redirector.
- Operator-created task through the CLI.
- Agent result posting through the redirector.
- Result retrieval through the CLI.
- Redirector log evidence.
- Windows process and network telemetry expectations.
- Clean lab shutdown.
