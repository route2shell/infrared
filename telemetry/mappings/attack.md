# Infrared V1 ATT&CK Mapping

## Table of Contents

1. [Overview](#overview)
2. [Primary Mapping](#primary-mapping)
3. [Supporting Infrastructure Context](#supporting-infrastructure-context)
4. [Detection Notes](#detection-notes)
5. [Mapping Boundaries](#mapping-boundaries)
6. [References](#references)

## Overview

This document maps the V1 `whoami` validation task to a basic ATT&CK technique for documentation and defender-context learning.

The V1 task:

```text
ir task create <SESSION_ID> "whoami"
```

The V1 implementation returns the current Windows user context from inside the Go agent. It does not spawn `whoami.exe`.

## Primary Mapping

| Behavior | ATT&CK Tactic | ATT&CK Technique | Why It Fits |
|---|---|---|---|
| Retrieve current user context from the Windows 11 target | Discovery | T1033: System Owner/User Discovery | The task identifies the active user context on the target system |

MITRE ATT&CK describes T1033 as identifying the primary or currently logged-in user, and includes `whoami` as an example utility that can acquire this information.

## Supporting Infrastructure Context

The V1 tasking flow also creates infrastructure and communication evidence:

| Behavior | ATT&CK Relationship | V1 Note |
|---|---|---|
| Agent HTTP check-in to redirector | C2-like communication pattern in a controlled lab | Do not over-map this in V1; the implementation is plain local HTTP for architecture learning |
| Agent polling for tasks | Operator tasking workflow | Useful for telemetry correlation, not a claim of stealth or operational maturity |
| Agent posting result | Result collection through control plane | Supports the local lab lifecycle |

The V1 documentation should keep the ATT&CK mapping narrow. The strongest mapping for the included task is T1033.

## Detection Notes

For V1, defender-visible evidence should include:

- Process creation for `C:\Infrared\ir-agent.exe`.
- Outbound connection from `ir-agent.exe` to `<HOST_REACHABLE_IP>:8080`.
- Nginx access log entries for check-in, task polling, and result posting.
- Teamserver state changes for session registration, task delivery, and result receipt.

Because the V1 runner does not spawn `whoami.exe`, detections that rely only on process creation for `whoami.exe` will not fire for this implementation. A stronger V1 analytic observes the unusual lab agent process plus its network behavior and resulting user discovery output.

## Mapping Boundaries

Do not map V1 to:

- Persistence.
- Privilege escalation.
- Credential access.
- Defense evasion.
- Process injection.
- Exploit execution.

Those behaviors are not implemented in V1.

## References

- MITRE ATT&CK Enterprise T1033, System Owner/User Discovery: `https://attack.mitre.org/techniques/T1033/`
- Microsoft Sysmon documentation: `https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon`
