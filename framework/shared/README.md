# Infrared Shared Framework

## Table of Contents

1. [Overview](#overview)
2. [Purpose](#purpose)
3. [Current Use](#current-use)
4. [Deferred](#deferred)

## Overview

This directory is reserved for shared contracts that are useful across Infrared components. It exists to keep cross-component concepts explicit without forcing premature abstraction.

## Purpose

Shared code should be added only when two or more components need the same stable concept. Good candidates include profile schemas, task status constants, result models, and validation helpers.

## Current Use

The current implementation keeps most logic local to the owning component:

- profile validation lives in `framework/cli`;
- API schemas live in `framework/teamserver`;
- agent config parsing lives in `implant/agent-go`.

This is intentional. The project should not create shared libraries until the duplication is real and the interface is stable.

## Deferred

Large shared libraries, plugin interfaces, generated SDKs, and multi-version compatibility layers are deferred until the platform has more than one stable transport, profile type, or agent implementation.
