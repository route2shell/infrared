# Infrared Local V1 Walkthrough

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Step 1: Confirm VMware Network Mode](#step-1-confirm-vmware-network-mode)
4. [Step 2: Start the Lab](#step-2-start-the-lab)
5. [Step 3: Validate the Profile](#step-3-validate-the-profile)
6. [Step 4: Confirm Services](#step-4-confirm-services)
7. [Step 5: Confirm VM Connectivity](#step-5-confirm-vm-connectivity)
8. [Step 6: Start the Windows Agent](#step-6-start-the-windows-agent)
9. [Step 7: List Sessions](#step-7-list-sessions)
10. [Step 8: Create a Task](#step-8-create-a-task)
11. [Step 9: Retrieve the Result](#step-9-retrieve-the-result)
12. [Step 10: Review Redirector Evidence](#step-10-review-redirector-evidence)
13. [Step 11: Review Telemetry Notes](#step-11-review-telemetry-notes)
14. [Step 12: Shut Down](#step-12-shut-down)
15. [Demo Completion Criteria](#demo-completion-criteria)
16. [Troubleshooting Checkpoints](#troubleshooting-checkpoints)

## Overview

This walkthrough exercises the V1 flow with a VMware Workstation Pro Windows 11 VM target:

```text
ir CLI -> Teamserver -> Nginx redirector -> Windows Go agent -> result retrieval
```

Use [setup.md](setup.md) first to prepare VMware Workstation Pro, build the Windows agent, and identify the host address reachable from the Windows 11 VM.

Use [demo-checklist.md](demo-checklist.md) when presenting the workflow as a short demo.

## Prerequisites

Before starting:

- The operator is at the repository root.
- The repo virtual environment contains the `ir` CLI.
- Docker Compose is available.
- VMware Workstation Pro is running a Windows 11 VM.
- The Windows 11 VM can reach the operator host on TCP port `8080`.
- `ir-agent.exe` and `local-http-basic.json` are present in `C:\Infrared`.

For the recommended NAT setup, set this value to the host's `vmnet8` IPv4 address:

```text
HOST_REACHABLE_IP=<host address reachable from Windows 11 VM>
```

## Step 1: Confirm VMware Network Mode

In VMware Workstation Pro, confirm the Windows 11 VM network adapter is attached to the intended network:

```text
VM Settings -> Network Adapter -> NAT
```

NAT is the recommended V1 default. On the operator host, identify the host's NAT adapter address:

```text
ip -4 addr show vmnet8
```

Use the `vmnet8` IPv4 address as `HOST_REACHABLE_IP`.

## Step 2: Start the Lab

From the repository root on the operator host:

```text
.venv/bin/ir lab up
```

Check service state:

```text
.venv/bin/ir lab status
```

Expected output shape:

```text
Compose file  infrastructure/local/docker-compose.yml
Compose ready yes
Teamserver URL http://127.0.0.1:8000

Services:
NAME                  ... STATUS
infrared-teamserver   ... Up ... (healthy)
infrared-redirector   ... Up ... (healthy)
```

## Step 3: Validate the Profile

From the repository root:

```text
.venv/bin/ir profile validate profiles/local-http-basic.yaml
```

Expected result:

```text
Profile    profiles/local-http-basic.yaml
Name       local-http-basic
Valid      yes
Transport  http
Redirector 127.0.0.1:8080
Teamserver 127.0.0.1:8000
```

The profile confirms the intended local service ports and agent-facing redirector routes.

## Step 4: Confirm Services

Confirm the operator-facing teamserver health endpoint:

```text
curl -sS http://127.0.0.1:8000/health
```

Expected teamserver response shape:

```json
{"status":"ok","service":"infrared-teamserver","version":"0.1.0-v1"}
```

Confirm the redirector readiness endpoint:

```text
curl -sS http://127.0.0.1:8080/redirector/health
```

Expected redirector response:

```text
ok
```

## Step 5: Confirm VM Connectivity

From PowerShell in the Windows 11 VM:

```text
Test-NetConnection <HOST_REACHABLE_IP> -Port 8080
Invoke-WebRequest http://<HOST_REACHABLE_IP>:8080/redirector/health -UseBasicParsing
```

Do not continue until TCP connectivity succeeds and the health endpoint returns `ok`.

Expected PowerShell TCP result includes:

```text
TcpTestSucceeded : True
```

## Step 6: Start the Windows Agent

From PowerShell in the Windows 11 VM:

```text
cd C:\Infrared
.\ir-agent.exe --config .\local-http-basic.json --server-url http://<HOST_REACHABLE_IP>:8080 --agent-id win-vm-v1
```

Expected initial agent logs:

```text
checked in: agent_id=win-vm-v1 session_id=<session-id>
no pending tasks
```

Leave this PowerShell window running while creating tasks from the operator host.

## Step 7: List Sessions

From the operator host:

```text
.venv/bin/ir sessions
```

Expected output shape:

```text
Session ID     Agent ID   Host              User              Platform Last Seen
sess-...       win-vm-v1  <windows-host>    <windows-user>    windows  <timestamp>
```

Record the session ID:

```text
SESSION_ID=<session id for win-vm-v1>
```

## Step 8: Create a Task

Create a V1 validation task:

```text
.venv/bin/ir task create <SESSION_ID> "whoami"
```

Expected output shape:

```text
Task created.
Task ID    <task-id>
Session ID <session-id>
Command    whoami
Status     pending
```

Expected Windows agent log after the next poll:

```text
running task_id=<task-id> command="whoami"
posted result: task_id=<task-id> status=completed exit_code=0
```

Optional task list check:

```text
.venv/bin/ir task list
```

Expected task list status after completion:

```text
Task ID Session ID Command Status    Created
<id>    sess-...   whoami  completed <timestamp>
```

## Step 9: Retrieve the Result

After the agent logs that it posted the result, retrieve it from the operator host:

```text
.venv/bin/ir results <TASK_ID>
```

Expected result content:

```text
Task ID    <task-id>
Session ID <session-id>
Status     completed
Exit Code  0
Created    <timestamp>

STDOUT:
<windows-host>\<windows-user>
```

If the result is not ready yet, wait for the next poll cycle and retry.

## Step 10: Review Redirector Evidence

Review local redirector access logs on the operator host:

```text
sed -n '1,200p' infrastructure/nginx/logs/access.log
```

Expected request paths include:

```text
/api/agent/checkin
/api/agent/win-vm-v1/tasks
/api/agent/win-vm-v1/results
```

These entries are the infrastructure evidence that the agent used the redirector path instead of talking directly to the teamserver.

## Step 11: Review Telemetry Notes

Review the Phase 10 telemetry guidance:

```text
telemetry/event-observations.md
telemetry/sysmon/setup.md
telemetry/sysmon/observations.md
telemetry/mappings/attack.md
```

Expected telemetry correlation:

- Sysmon Event ID 1 for `C:\Infrared\ir-agent.exe`.
- Sysmon Event ID 3 for `ir-agent.exe` connecting to `<HOST_REACHABLE_IP>:8080`.
- Nginx access logs for check-in, task polling, and result posting.
- Teamserver state showing session, task, and result lifecycle.
- ATT&CK mapping to T1033: System Owner/User Discovery.

## Step 12: Shut Down

Stop the Windows agent with `Ctrl+C`.

From the operator host:

```text
.venv/bin/ir lab down
```

Confirm services are stopped:

```text
.venv/bin/ir lab status
```

## Demo Completion Criteria

The V1 demo is complete when all of the following are true:

- Compose services started and reached healthy state.
- The local profile validated successfully.
- The Windows 11 VM reached the redirector health endpoint.
- The Windows agent checked in as `win-vm-v1`.
- The operator created a `whoami` task.
- The agent posted a completed result with exit code `0`.
- `ir results <TASK_ID>` displayed the Windows user context.
- Redirector logs showed `/checkin`, `/tasks`, and `/results` paths.
- Telemetry notes identify expected Windows process and network observations.
- The lab was shut down cleanly.

## Troubleshooting Checkpoints

Connectivity failures usually mean the Windows 11 VM cannot reach the host address selected in setup. For VMware NAT, retest with `Test-NetConnection` against the host's `vmnet8` IPv4 address. For host-only, use `vmnet1`. For bridged, use the host LAN address.

Missing sessions usually mean the agent is pointed at the wrong URL. The Windows command should use the redirector on port `8080`, not the teamserver on port `8000`.

Tasks that remain pending usually mean the agent is not running continuously or has not polled again since task creation. Leave the agent running or rerun it with `--once`.

Failed results with exit code `126` mean the command is outside the V1 allowlist. Use `whoami`, `hostname`, `pwd`, or `echo <text>`.
