# Infrared

Infrared is a local-first adversary emulation and infrastructure research platform for studying operator workflows, teamserver design, redirector architecture, target-side tasking, and telemetry-aware tradecraft.

V1 is intentionally small: it proves the end-to-end architecture before adding advanced capability work.

```text
Operator CLI
  -> Teamserver API
  -> SQLite state
  -> Nginx redirector
  -> Go test agent
  -> Windows 11 target VM
  -> telemetry observations
```

## What It Demonstrates

- A Python operator CLI exposed as `ir`.
- A FastAPI teamserver with session, task, result, and event tracking.
- SQLite-backed local persistence.
- An Nginx redirector in front of agent-facing routes.
- A Go test agent that checks in, polls for tasks, runs a narrow V1 command allowlist, and posts results.
- Docker Compose orchestration for the local control plane.
- YAML profile validation for the local HTTP lab.
- VMware Workstation Pro and Windows 11 lab documentation.
- Telemetry notes for teamserver state, redirector logs, Sysmon observations, and ATT&CK mapping.

## Architecture

```text
Operator host
  .venv/bin/ir
  Docker Compose
  Teamserver: http://127.0.0.1:8000
  Redirector: http://127.0.0.1:8080

Windows 11 VM
  C:\Infrared\ir-agent.exe
  C:\Infrared\local-http-basic.json
  Agent URL: http://<host-vmnet8-ip>:8080
```

The operator talks directly to the teamserver. The agent talks to the redirector. The redirector forwards only V1 agent routes to the teamserver.

## Repository Layout

```text
framework/
  cli/              Python operator CLI
  teamserver/       FastAPI teamserver and SQLite store
  shared/           Shared framework placeholder
implant/
  agent-go/         Go test agent
infrastructure/
  local/            Docker Compose lab
  nginx/            Redirector configs and logs
profiles/           Local HTTP profile
labs/
  local-v1/         Setup, walkthrough, expected results, demo checklist
telemetry/          Event observations, Sysmon notes, ATT&CK mapping
```

## Quickstart

Start the local control plane:

```text
.venv/bin/ir lab up
.venv/bin/ir lab status
```

Validate the profile:

```text
.venv/bin/ir profile validate profiles/local-http-basic.yaml
```

Check service health:

```text
curl -sS http://127.0.0.1:8000/health
curl -sS http://127.0.0.1:8080/redirector/health
```

Stop the lab:

```text
.venv/bin/ir lab down
```

## Demo Workflow

The full V1 demo uses VMware Workstation Pro with a Windows 11 VM.

1. Start the local lab on the operator host.
2. Confirm the Windows 11 VM can reach the host redirector on TCP `8080`.
3. Run the Go agent from `C:\Infrared`.
4. List the new session with `ir sessions`.
5. Create a task with `ir task create <session-id> "whoami"`.
6. Let the agent poll, execute, and post the result.
7. Retrieve output with `ir results <task-id>`.
8. Review Nginx logs and Windows/Sysmon observations.

Detailed guides:

- `labs/local-v1/setup.md`
- `labs/local-v1/walkthrough.md`
- `labs/local-v1/expected-results.md`
- `labs/local-v1/demo-checklist.md`

## Agent Commands

The V1 agent does not execute arbitrary shell commands. It supports only:

- `whoami`
- `hostname`
- `pwd`
- `echo <text>`

Unsupported commands return a failed result with exit code `126`.

## Telemetry

Infrared treats telemetry as part of the system, not an afterthought.

V1 documents expected evidence from:

- teamserver session, task, result, and event state;
- Nginx redirector access logs;
- Windows 11 Sysmon process and network events;
- agent console output;
- operator CLI output.

Telemetry references:

- `telemetry/event-observations.md`
- `telemetry/sysmon/setup.md`
- `telemetry/sysmon/observations.md`
- `telemetry/mappings/attack.md`

## Boundaries

V1 does not include stealth, persistence, privilege escalation, credential access, EDR bypass, injection, exploit weaponization, cloud deployment, or multi-operator workflows.

Those topics are intentionally out of scope for the first vertical slice. V1 focuses on clean architecture, reproducible local infrastructure, task lifecycle, and defender-visible telemetry.
