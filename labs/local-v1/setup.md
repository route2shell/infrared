# Infrared Local V1 Lab Setup

## Table of Contents

1. [Overview](#overview)
2. [Lab Topology](#lab-topology)
3. [Host Prerequisites](#host-prerequisites)
4. [VMware Workstation Pro Baseline](#vmware-workstation-pro-baseline)
5. [Windows 11 VM Prerequisites](#windows-11-vm-prerequisites)
6. [Network Assumptions](#network-assumptions)
7. [Start Control Plane](#start-control-plane)
8. [Find the VMware Host Address](#find-the-vmware-host-address)
9. [Validate VM Connectivity](#validate-vm-connectivity)
10. [Build the Windows Agent](#build-the-windows-agent)
11. [Transfer Agent Files](#transfer-agent-files)
12. [Run the Agent](#run-the-agent)
13. [Troubleshooting](#troubleshooting)

## Overview

This guide prepares the controlled VMware Workstation Pro Windows 11 VM workflow for Infrared V1. The control plane runs on the operator host through Docker Compose. The Windows 11 VM runs the Go test agent and reaches the Nginx redirector over HTTP.

## Lab Topology

```text
Operator host
  ir CLI
  Docker Compose
  Teamserver: http://127.0.0.1:8000
  Redirector: http://<host-reachable-ip>:8080

Windows 11 VM target
  ir-agent.exe
  local-http-basic.json
  outbound HTTP to redirector
```

The operator CLI talks directly to the teamserver. The agent talks to the redirector.

## Host Prerequisites

From the repository root, confirm the local project tooling is available:

```text
.venv/bin/ir --version
docker compose -f infrastructure/local/docker-compose.yml config
go version
```

The V1 profile should validate before the VM workflow begins:

```text
.venv/bin/ir profile validate profiles/local-http-basic.yaml
```

Expected profile result:

```text
Valid yes
```

## VMware Workstation Pro Baseline

Use VMware Workstation Pro with one Windows 11 guest VM dedicated to the lab.

Recommended VMware settings:

| Setting | Recommended V1 Value | Notes |
|---|---|---|
| Guest OS | Windows 11 x64 | V1 target-side workflow |
| Network Adapter | NAT | Recommended default because the VM can reach the host through the VMware NAT network |
| Alternative Network | Host-only | Useful for tighter host-to-VM isolation |
| Bridged Network | Optional | Works if the host firewall and LAN allow VM-to-host traffic |
| Shared Folders | Optional | Convenient for transferring `ir-agent.exe` and config |

The simplest V1 path is NAT mode with the agent connecting to the host's `vmnet8` address on port `8080`.

## Windows 11 VM Prerequisites

Use a Windows 11 VM that you control and can isolate for lab work. V1 does not require Active Directory, a domain controller, local administrator privileges, or endpoint bypass research.

Minimum VM preparation:

- PowerShell available.
- Outbound HTTP access from the VM to the operator host on TCP port `8080`.
- A working directory such as `C:\Infrared`.
- VMware Tools installed if using shared folders or smoother file transfer.
- Optional Sysmon or Windows event logging configuration for later Phase 10 telemetry notes.

Create the working directory from PowerShell:

```text
New-Item -ItemType Directory -Force C:\Infrared
```

## Network Assumptions

The profile uses loopback addresses for services running on the operator host:

```text
teamserver: 127.0.0.1:8000
redirector: 127.0.0.1:8080
```

From inside the Windows 11 VM, `127.0.0.1` means the VM itself, not the operator host. The agent must use a host address reachable from the VM.

For VMware Workstation Pro:

```text
NAT:       use the host's vmnet8 IPv4 address
Host-only: use the host's vmnet1 IPv4 address
Bridged:   use the host's LAN IPv4 address
```

Example redirector URLs:

```text
http://<vmnet8-ip>:8080
http://<vmnet1-ip>:8080
http://<host-lan-ip>:8080
```

The exact address depends on the VMware virtual network selected for the VM.

## Start Control Plane

From the repository root on the operator host:

```text
.venv/bin/ir lab up
.venv/bin/ir lab status
```

Confirm direct teamserver health:

```text
curl -sS http://127.0.0.1:8000/health
```

Confirm redirector health:

```text
curl -sS http://127.0.0.1:8080/redirector/health
```

## Find the VMware Host Address

On the Linux operator host, list the VMware virtual adapter addresses:

```text
ip -4 addr show vmnet8
ip -4 addr show vmnet1
```

For the recommended NAT setup, use the IPv4 address on `vmnet8`. For a host-only setup, use the IPv4 address on `vmnet1`. For bridged networking, use the host's LAN IPv4 address.

If the VMware adapter names are different or unavailable, list all addresses:

```text
ip -4 addr
```

Record the chosen value as:

```text
HOST_REACHABLE_IP=<host address reachable from Windows 11 VM>
REDIRECTOR_URL=http://<host address reachable from Windows 11 VM>:8080
```

## Validate VM Connectivity

From PowerShell in the Windows 11 VM, test TCP connectivity:

```text
Test-NetConnection <HOST_REACHABLE_IP> -Port 8080
```

Expected result:

```text
TcpTestSucceeded : True
```

Then test the redirector health endpoint:

```text
Invoke-WebRequest http://<HOST_REACHABLE_IP>:8080/redirector/health -UseBasicParsing
```

Expected content:

```text
ok
```

If this fails, fix network reachability before running the agent.

For the recommended NAT setup, most failures come from choosing the wrong host address or from a host firewall rule blocking inbound traffic to `8080` on the VMware NAT interface.

## Build the Windows Agent

From the operator host:

```text
cd implant/agent-go
GOOS=windows GOARCH=amd64 go build -o bin/ir-agent-windows-amd64.exe ./cmd/ir-agent
```

Keep the V1 agent config with the binary:

```text
implant/agent-go/configs/local-http-basic.json
```

The config can retain its default `server_url` because the Windows command uses `--server-url` to point at the VM-reachable redirector.

## Transfer Agent Files

Copy these files into the Windows 11 VM working directory:

```text
ir-agent-windows-amd64.exe
local-http-basic.json
```

Recommended target layout:

```text
C:\Infrared\ir-agent.exe
C:\Infrared\local-http-basic.json
```

Use the transfer method already available in the local lab, such as a shared folder, hypervisor clipboard, or controlled file copy. Record the transfer method in the lab notes if it matters for telemetry.

For VMware Workstation Pro, the most convenient options are:

- VMware shared folders, if enabled for the Windows 11 VM.
- Drag-and-drop or copy/paste, if VMware Tools supports it in the guest.
- A temporary controlled file share on the host-only or NAT network.

## Run the Agent

From PowerShell in the Windows 11 VM:

```text
cd C:\Infrared
.\ir-agent.exe --config .\local-http-basic.json --server-url http://<HOST_REACHABLE_IP>:8080 --agent-id win-vm-v1 --once
```

Expected behavior:

- The agent checks in through the redirector.
- The agent polls once for tasks.
- If no task is pending, it logs `no pending tasks` and exits successfully.

For the walkthrough tasking cycle, run the agent continuously:

```text
.\ir-agent.exe --config .\local-http-basic.json --server-url http://<HOST_REACHABLE_IP>:8080 --agent-id win-vm-v1
```

Stop the continuous agent with `Ctrl+C` after the task result is posted.

## Troubleshooting

If `Test-NetConnection` fails:

- Confirm Docker Compose services are running on the host.
- Confirm the Windows 11 VM network adapter is attached to NAT, host-only, or bridged as expected.
- For NAT, confirm the agent is using the host's `vmnet8` IPv4 address.
- For host-only, confirm the agent is using the host's `vmnet1` IPv4 address.
- For bridged, confirm the agent is using the host LAN IPv4 address.
- Confirm the host firewall allows inbound TCP `8080` from the VMware network.

If `/redirector/health` fails but TCP succeeds:

- Confirm the redirector container is healthy with `.venv/bin/ir lab status`.
- Confirm `curl -sS http://127.0.0.1:8080/redirector/health` works on the host.
- Review `infrared-redirector` container status through Docker Compose.

If the agent check-in fails:

- Confirm the agent command uses the redirector URL on port `8080`, not the teamserver URL on port `8000`.
- Confirm the URL does not use `127.0.0.1` from inside the VM unless the redirector is also running inside the VM.
- Confirm the agent config file path is correct.
- Confirm Windows 11 can resolve and route to the selected VMware host address with `Test-NetConnection`.

If tasks do not appear:

- Confirm the session ID in `ir sessions` matches the agent ID used from Windows 11.
- Confirm the agent is running continuously or rerun it with `--once` after creating a task.
- Confirm the command is one of the V1 supported commands: `whoami`, `hostname`, `pwd`, or `echo <text>`.

If a command returns failed with exit code `126`:

- The command is outside the V1 allowlist.
- Create a new task using one of the supported V1 validation commands.
