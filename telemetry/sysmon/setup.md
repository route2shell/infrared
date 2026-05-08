# Infrared V1 Sysmon Setup

## Table of Contents

1. [Overview](#overview)
2. [Reference](#reference)
3. [Minimum Events](#minimum-events)
4. [Install Location](#install-location)
5. [Minimal Lab Configuration](#minimal-lab-configuration)
6. [Install Sysmon](#install-sysmon)
7. [Validate Logging](#validate-logging)
8. [Operational Notes](#operational-notes)

## Overview

This guide prepares the Windows 11 VM to collect basic target-side telemetry for the Infrared V1 lab. The goal is to observe process creation and outbound network connection behavior for:

```text
C:\Infrared\ir-agent.exe
```

## Reference

Sysmon writes events to:

```text
Applications and Services Logs\Microsoft\Windows\Sysmon\Operational
```

Microsoft documents Sysmon Event ID 1 as process creation and Event ID 3 as network connection telemetry. Event ID 3 is disabled by default unless the Sysmon configuration includes network connection logging.

Reference:

```text
https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon
```

## Minimum Events

The V1 lab should capture:

| Event ID | Name | V1 Use |
|---:|---|---|
| 1 | Process Create | Observe `ir-agent.exe` started from PowerShell |
| 3 | Network Connection | Observe `ir-agent.exe` connecting to `<HOST_REACHABLE_IP>:8080` |
| 5 | Process Terminated | Optional agent exit confirmation |

## Install Location

Use a dedicated tools directory:

```text
C:\Tools\Sysmon
```

Keep lab files separate:

```text
C:\Infrared
```

## Minimal Lab Configuration

Create:

```text
C:\Tools\Sysmon\infrared-v1-sysmon.xml
```

Minimal configuration:

```xml
<Sysmon schemaversion="4.82">
  <HashAlgorithms>SHA256</HashAlgorithms>
  <EventFiltering>
    <ProcessCreate onmatch="include">
      <Image condition="is">C:\Infrared\ir-agent.exe</Image>
      <ParentImage condition="end with">powershell.exe</ParentImage>
      <ParentImage condition="end with">pwsh.exe</ParentImage>
    </ProcessCreate>
    <NetworkConnect onmatch="include">
      <Image condition="is">C:\Infrared\ir-agent.exe</Image>
      <DestinationPort condition="is">8080</DestinationPort>
    </NetworkConnect>
    <ProcessTerminate onmatch="include">
      <Image condition="is">C:\Infrared\ir-agent.exe</Image>
    </ProcessTerminate>
  </EventFiltering>
</Sysmon>
```

This is intentionally narrow for the V1 lab. Broader configs can generate much more data than needed for Phase 10.

## Install Sysmon

From an elevated PowerShell prompt:

```text
cd C:\Tools\Sysmon
.\Sysmon64.exe -accepteula -i .\infrared-v1-sysmon.xml
```

Confirm configuration:

```text
.\Sysmon64.exe -c
```

Print the schema supported by the local Sysmon binary:

```text
.\Sysmon64.exe -s
```

If the supported schema version differs from the XML snippet below, update the `schemaversion` value before installing the configuration.

If Sysmon is already installed, update the config:

```text
.\Sysmon64.exe -c .\infrared-v1-sysmon.xml
```

## Validate Logging

Start the agent once:

```text
cd C:\Infrared
.\ir-agent.exe --config .\local-http-basic.json --server-url http://<HOST_REACHABLE_IP>:8080 --agent-id win-vm-v1 --once
```

Open Event Viewer:

```text
Event Viewer -> Applications and Services Logs -> Microsoft -> Windows -> Sysmon -> Operational
```

Expected events:

- Event ID 1 for `C:\Infrared\ir-agent.exe`.
- Event ID 3 for a connection from `ir-agent.exe` to `<HOST_REACHABLE_IP>:8080`.
- Event ID 5 if the agent process termination is included by the active Sysmon configuration.

## Operational Notes

Sysmon timestamps are UTC. Convert them when correlating with local operator commands in `America/New_York`.

If Event ID 3 does not appear, confirm the active Sysmon configuration includes `NetworkConnect` for `ir-agent.exe` and destination port `8080`.

If no events appear, confirm the agent binary path is exactly:

```text
C:\Infrared\ir-agent.exe
```

If using a different path, update the Sysmon configuration to match that path.
