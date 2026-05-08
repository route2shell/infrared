# Infrared Telemetry

## Table of Contents

1. [Overview](#overview)
2. [Purpose](#purpose)
3. [Documents](#documents)
4. [Telemetry Sources](#telemetry-sources)
5. [Correlation Model](#correlation-model)
6. [Deferred](#deferred)

## Overview

This directory contains telemetry notes and observations for the VMware Workstation Pro and Windows 11 local lab.

## Purpose

Record what the local tasking workflow looks like from the defender side.

The goal is not automated detection engineering. The goal is to connect one controlled tasking cycle to concrete evidence across the control plane, redirector, and Windows 11 target.

## Documents

- `event-observations.md`: operator, teamserver, redirector, and target-side observation checklist for one V1 run.
- `sysmon/setup.md`: Windows 11 Sysmon installation and minimum configuration guidance for the lab.
- `sysmon/observations.md`: expected Sysmon and Windows Event Viewer observations for the V1 agent workflow.
- `mappings/attack.md`: basic ATT&CK mapping for the V1 `whoami` task.

## Telemetry Sources

| Source | Location | Value |
|---|---|---|
| Teamserver API state | SQLite `sessions`, `tasks`, `results`, and `events` tables | Confirms registration, task lifecycle, and result ingestion |
| Redirector access logs | `infrastructure/nginx/logs/access.log` | Confirms agent traffic used Nginx on port `8080` |
| Windows 11 target logs | Sysmon Operational log | Confirms agent process start and outbound HTTP connection |
| Agent console logs | Windows PowerShell session running `ir-agent.exe` | Confirms local check-in, task execution, and result post |
| Operator CLI output | `.venv/bin/ir ...` commands | Confirms the operator-visible workflow |

## Correlation Model

Correlate a V1 task run with these identifiers:

- `agent_id`, normally `win-vm-v1` in the Phase 9 walkthrough.
- `session_id`, returned by `ir sessions`.
- `task_id`, returned by `ir task create`.
- Redirector path values such as `/api/agent/win-vm-v1/tasks`.
- Windows process image path, normally `C:\Infrared\ir-agent.exe`.
- Destination IP and port, normally `<HOST_REACHABLE_IP>:8080`.

## Deferred

Automated EVTX parsing, Sigma generation, detection rule export, and telemetry correlation engines are deferred beyond V1.
