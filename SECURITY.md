# Security

## Table of Contents

1. [Overview](#overview)
2. [Project Boundaries](#project-boundaries)
3. [Responsible Use](#responsible-use)
4. [Safety Expectations](#safety-expectations)
5. [Reporting Issues](#reporting-issues)

## Overview

Infrared is intended for authorized local lab research, adversary emulation, infrastructure modeling, and defensive validation. The project is designed to learn how operator workflow, redirector infrastructure, tasking, result collection, and telemetry fit together as an engineered system.

## Project Boundaries

The current implementation is limited to a controlled local workflow:

- Operator CLI.
- Local teamserver.
- Local SQLite state.
- Local Nginx redirector.
- Basic Go test agent.
- Local lab profile.
- Manual telemetry notes.

The project does not implement stealth, persistence, credential access, privilege escalation, evasion, injection, exploit weaponization, or unauthorized access workflows.

## Responsible Use

Use Infrared only in environments where you have explicit authorization. Do not use this project against systems you do not own or have permission to test.

## Safety Expectations

- Keep lab targets isolated and clearly identified.
- Use the documented VMware Workstation Pro and Windows 11 workflow for target-side testing.
- Preserve telemetry observations so each task can be explained from the operator and defender perspectives.
- Cleanly stop the agent and tear down local services after a run.
- Do not add advanced capability work without updating scope, safety notes, and telemetry expectations.

## Reporting Issues

For local development, record project issues and safety concerns in the maintainer's chosen issue tracker or private project notes. Public reports should avoid sharing sensitive lab artifacts, private hostnames, tokens, or environment-specific addresses.
