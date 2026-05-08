# Infrared Roadmap

## Table of Contents

1. [Working Skeleton](#working-skeleton)
2. [Next Research Tracks](#next-research-tracks)
3. [Deferred Work](#deferred-work)

## Working Skeleton

The first release proves the full local tasking lifecycle with minimal moving parts. It is a deliberately small vertical slice that demonstrates architecture, operator workflow, infrastructure routing, agent tasking, and telemetry awareness without implementing advanced tradecraft.

### Completed Capabilities

- Python operator CLI exposed as `ir`.
- FastAPI teamserver with session, task, result, and event tracking.
- SQLite persistence for local lab state.
- Go test agent with a narrow validation-command allowlist.
- Nginx redirector forwarding only agent-facing routes.
- Docker Compose local control plane.
- Local HTTP YAML profile and CLI validation.
- VMware Workstation Pro and Windows 11 lab workflow.
- Telemetry notes for teamserver state, redirector logs, Sysmon observations, and ATT&CK mapping.
- End-to-end setup, walkthrough, expected-results, and demo-checklist documentation.

### Success Criteria

The skeleton is complete when an operator can start the local lab, register an agent session from the Windows target, create a simple task, retrieve the result, and review related logs and telemetry notes.

## Next Research Tracks

Future work should preserve the same discipline: add one capability at a time, document its purpose, test it in the lab, and record defender-visible telemetry.

High-value next tracks include:

- richer profile schema and shared validation contracts;
- generated agent and redirector configuration from one profile source;
- improved run reporting and operator notes;
- stronger operator authentication and audit logging;
- safer task approval and task history workflows;
- improved telemetry collection and correlation;
- controlled cloud or VPS redirector deployment with infrastructure-as-code.

## Deferred Work

The following work is intentionally deferred:

- Transport abstraction.
- Staging service.
- Generated redirector configuration.
- Automated telemetry parsing.
- Run report generation.
- ATT&CK-aligned playbooks.
- Terraform or cloud deployment.
- Multi-redirector topologies.
- Rust agent research track.
- Capability module format.
