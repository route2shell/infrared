# Infrared V1 Sysmon Observations

## Table of Contents

1. [Overview](#overview)
2. [Expected Process Creation](#expected-process-creation)
3. [Expected Network Connection](#expected-network-connection)
4. [Expected Process Termination](#expected-process-termination)
5. [What Not to Expect](#what-not-to-expect)
6. [Manual Observation Template](#manual-observation-template)
7. [Correlation Notes](#correlation-notes)

## Overview

This document describes expected Windows 11 Sysmon observations for the V1 agent running from:

```text
C:\Infrared\ir-agent.exe
```

The default V1 task is:

```text
whoami
```

## Expected Process Creation

Expected Sysmon event:

| Field | Expected Value |
|---|---|
| Event ID | `1` |
| Event name | Process Create |
| Image | `C:\Infrared\ir-agent.exe` |
| ParentImage | Usually `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe` or `pwsh.exe` |
| CommandLine | Includes `--config`, `--server-url`, and `--agent-id win-vm-v1` |
| User | Windows account used to run the agent |
| Hashes | SHA256 if configured in Sysmon |

Interpretation:

```text
The Windows 11 target executed the V1 agent from the lab working directory.
```

## Expected Network Connection

Expected Sysmon event:

| Field | Expected Value |
|---|---|
| Event ID | `3` |
| Event name | Network Connection |
| Image | `C:\Infrared\ir-agent.exe` |
| DestinationIp | `<HOST_REACHABLE_IP>` |
| DestinationPort | `8080` |
| Protocol | `tcp` |
| Initiated | `true` |

Expected connection purpose:

| HTTP Route | Meaning |
|---|---|
| `/api/agent/checkin` | Agent registration or check-in |
| `/api/agent/win-vm-v1/tasks` | Task polling |
| `/api/agent/win-vm-v1/results` | Result posting |

Sysmon records the network connection, while Nginx records the HTTP path.

## Expected Process Termination

If ProcessTerminate is included in the active Sysmon configuration:

| Field | Expected Value |
|---|---|
| Event ID | `5` |
| Event name | Process Terminated |
| Image | `C:\Infrared\ir-agent.exe` |

This is most visible when running the agent with:

```text
--once
```

## What Not to Expect

The V1 agent does not spawn `whoami.exe` when executing the `whoami` task. The task is implemented inside the Go agent with local user lookup behavior.

Do not expect:

```text
C:\Windows\System32\whoami.exe
cmd.exe /c whoami
powershell.exe whoami
```

for the V1 `whoami` task unless a later implementation changes the runner behavior.

Also do not expect persistence, privilege escalation, injection, credential access, or defense evasion events in V1. Those behaviors are outside the V1 implementation scope.

## Manual Observation Template

Use this template for a real run:

| Field | Observation |
|---|---|
| Run timestamp local | |
| Run timestamp UTC | |
| Agent ID | `win-vm-v1` |
| Session ID | |
| Task ID | |
| Agent image path | `C:\Infrared\ir-agent.exe` |
| Parent process | |
| User | |
| Destination IP | |
| Destination port | `8080` |
| Sysmon Event ID 1 present | `yes/no` |
| Sysmon Event ID 3 present | `yes/no` |
| Sysmon Event ID 5 present | `yes/no/optional` |
| Result stdout | |

## Correlation Notes

Correlate Sysmon Event ID 3 with the Nginx access log by time and destination port. Sysmon provides the process context; Nginx provides HTTP route context.

Example correlation:

| Evidence | Meaning |
|---|---|
| Sysmon Event ID 1, `ir-agent.exe` | Agent process started |
| Nginx `POST /api/agent/checkin` | Agent registered through redirector |
| Nginx `GET /api/agent/win-vm-v1/tasks` | Agent polled for tasking |
| Nginx `POST /api/agent/win-vm-v1/results` | Agent returned result |
| `ir results <TASK_ID>` | Operator retrieved stored task result |
