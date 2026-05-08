# Infrared Local V1 Lab

Created: 2026-05-08T10:23:49-04:00
Last updated: 2026-05-08T16:23:29-04:00

## Table of Contents

1. [Overview](#overview)
2. [Purpose](#purpose)
3. [Documents](#documents)
4. [Deferred](#deferred)

## Overview

This directory contains setup, walkthrough, expected-results, and demo-checklist documentation for the VMware Workstation Pro and Windows 11 lab.

## Purpose

Document how to prepare and operate the controlled local workflow:

```text
start services
validate profile
prepare Windows 11 VM
run agent from Windows 11 VM
list session
create task
retrieve result
review telemetry
shut down services
```

## Documents

- `setup.md`: host, VMware Workstation Pro, Windows 11 VM, network, build, transfer, and troubleshooting prerequisites.
- `walkthrough.md`: final ordered operator and target steps for one complete V1 run.
- `expected-results.md`: expected service, agent, CLI, result, and troubleshooting outcomes.
- `demo-checklist.md`: concise demo readiness and execution checklist.

## Deferred

Automated VM provisioning, cloud targets, domain labs, and Active Directory requirements are deferred. The current lab is intentionally focused on one Windows 11 VM and one local control plane.
