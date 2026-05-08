# Infrared Local V1 Demo Checklist

## Table of Contents

1. [Readiness](#readiness)
2. [Demo Commands](#demo-commands)
3. [Windows 11 Target Commands](#windows-11-target-commands)
4. [Evidence to Show](#evidence-to-show)
5. [Closeout](#closeout)

## Readiness

- [ ] VMware Workstation Pro is installed.
- [ ] Windows 11 VM is running.
- [ ] Windows 11 VM network adapter is set to NAT.
- [ ] Operator host `vmnet8` IPv4 address is known.
- [ ] Windows 11 VM can reach `http://<HOST_REACHABLE_IP>:8080/redirector/health`.
- [ ] `C:\Infrared\ir-agent.exe` exists.
- [ ] `C:\Infrared\local-http-basic.json` exists.
- [ ] Optional Sysmon collection is enabled.

## Demo Commands

From the repository root on the operator host:

```text
.venv/bin/ir lab up
.venv/bin/ir lab status
.venv/bin/ir profile validate profiles/local-http-basic.yaml
curl -sS http://127.0.0.1:8000/health
curl -sS http://127.0.0.1:8080/redirector/health
.venv/bin/ir sessions
.venv/bin/ir task create <SESSION_ID> "whoami"
.venv/bin/ir task list
.venv/bin/ir results <TASK_ID>
sed -n '1,200p' infrastructure/nginx/logs/access.log
.venv/bin/ir lab down
```

## Windows 11 Target Commands

From PowerShell in the Windows 11 VM:

```text
Test-NetConnection <HOST_REACHABLE_IP> -Port 8080
Invoke-WebRequest http://<HOST_REACHABLE_IP>:8080/redirector/health -UseBasicParsing
cd C:\Infrared
.\ir-agent.exe --config .\local-http-basic.json --server-url http://<HOST_REACHABLE_IP>:8080 --agent-id win-vm-v1
```

Stop the agent with `Ctrl+C` after result posting is visible.

## Evidence to Show

- [ ] `ir lab status` shows healthy teamserver and redirector services.
- [ ] `ir profile validate` returns `Valid yes`.
- [ ] Windows PowerShell shows `TcpTestSucceeded : True`.
- [ ] Agent console shows check-in and result post.
- [ ] `ir sessions` shows `win-vm-v1`.
- [ ] `ir task list` shows task status moving to `completed`.
- [ ] `ir results <TASK_ID>` shows exit code `0` and Windows user context.
- [ ] Nginx access log shows `/api/agent/checkin`, `/tasks`, and `/results`.
- [ ] Telemetry notes explain expected Sysmon process and network events.

## Closeout

- [ ] Stop the Windows agent.
- [ ] Run `.venv/bin/ir lab down`.
- [ ] Confirm lab services are stopped.
- [ ] Record any deviations in `telemetry/event-observations.md` or separate run notes.
