# A2RL Requirements Baseline

## Purpose

This document converts the rule-driven constraints captured in [Plan.md](/home/a2rl/avlite/Plan.md) into engineering requirements for AVLite's competition-oriented roadmap. It is the normative baseline for all follow-on work from `P1` onward.

## Scope

The baseline covers the minimum set of requirements needed to evolve AVLite from a GUI-first prototype into a headless competition stack for A2RL-style sessions:

- race scenarios
- deployment and operations
- safety and session control
- software interfaces
- prohibited assumptions and practices

## Competition Scenarios

AVLite must eventually support these operating scenarios as first-class targets:

| ID | Scenario | Required Capability |
|----|----------|---------------------|
| `REQ-SCN-001` | `Lap Test` | stable single-car autonomous lap completion with repeatable timing |
| `REQ-SCN-002` | `Speed Test` | controlled high-speed straight-line operation with bounded lateral deviation |
| `REQ-SCN-003` | `Overtaking Challenge` | opponent-aware planning, overtake and defend behaviors |
| `REQ-SCN-004` | `Multi-Car Race` | multi-agent perception, planning, safety handling, and sustained operation |

## Deployment Requirements

| ID | Requirement | Engineering Interpretation |
|----|-------------|----------------------------|
| `REQ-DEP-001` | The software shall run on the official onboard HPC. | No competition-critical dependency may require a developer workstation or external GUI. |
| `REQ-DEP-002` | Official sessions shall not depend on SSH tuning, hot fixes, or manual intervention. | The competition path must be self-contained, preconfigured, and restartable. |
| `REQ-DEP-003` | The system shall support one-command startup and deterministic shutdown. | A headless CLI entrypoint and explicit exit codes are required. |
| `REQ-DEP-004` | The system shall support unattended execution. | Runtime health checks, startup validation, and fault-triggered degradation are required. |
| `REQ-DEP-005` | The system shall preserve run artifacts for audit and replay. | Each run must record configuration, runtime metadata, logs, and outputs. |

## Safety And Session-State Requirements

| ID | Requirement | Engineering Interpretation |
|----|-------------|----------------------------|
| `REQ-SAF-001` | The software shall obey race control state transitions. | A race state machine must gate planning and actuation. |
| `REQ-SAF-002` | The software shall react to `Start`, `Stop`, `Safety Car`, `Yellow Flag`, and `Red Flag`. | Runtime must map external race-state inputs to behavior constraints and control limits. |
| `REQ-SAF-003` | The system shall support abnormal-condition handling. | Fault detection, watchdogs, and degraded mode / safe stop paths are required. |
| `REQ-SAF-004` | The system shall support crash recovery and controlled restart. | Lifecycle management must define startup checks, shutdown behavior, and restart policy. |
| `REQ-SAF-005` | The system shall support post-session auditability. | Structured logs, timing data, faults, and operator-visible state changes must be recorded. |

## Interface Requirements

| ID | Requirement | Engineering Interpretation |
|----|-------------|----------------------------|
| `REQ-IO-001` | The stack shall integrate with official I/O interfaces. | The runtime architecture must support `ROS2 + agreed messages/API` style deployment. |
| `REQ-IO-002` | Input contracts shall distinguish ego state, opponent state, and session control. | Perception, localization, world bridge, and race-state interfaces must be explicit and typed. |
| `REQ-IO-003` | Output contracts shall separate planning intent from low-level actuation. | Planner output, controller commands, and supervisor overrides must have independent interfaces. |
| `REQ-IO-004` | Time semantics shall be explicit. | All high-rate components must define update period, latency expectation, and timeout policy. |
| `REQ-IO-005` | The runtime shall support offline replay using recorded artifacts. | Run output format must be sufficient to drive deterministic replay and post-analysis. |

## Engineering Constraints

| ID | Constraint | Required Project Policy |
|----|------------|-------------------------|
| `REQ-ENG-001` | GUI is a debug tool only. | GUI must not remain the sole runtime entrypoint. |
| `REQ-ENG-002` | Competition runtime shall not depend on ground-truth-only inputs. | Ground truth may exist for simulation/debug, but cannot remain the competition mainline assumption. |
| `REQ-ENG-003` | Runtime behavior shall be reproducible. | Profiles, code revision, dependency versions, and launch arguments must be snapshotted. |
| `REQ-ENG-004` | Every feature shall map to a requirement and acceptance criterion. | Requirements traceability must be maintained as code and tests evolve. |
| `REQ-ENG-005` | New competition-path capabilities shall include tests and observability. | No runtime-critical feature is complete without validation and metrics hooks. |

## Prohibited Practices

The following are disallowed on the competition main path unless explicitly reclassified by a later plan update:

- GUI-only startup or control flow
- manual SSH intervention during an official session
- ad hoc developer-machine paths in competition profiles
- reliance on `GT_DETECTION`, `GT_TRACKING`, or `GT_LOCALIZATION` as the only path for competition operation
- hidden runtime state that is not logged or reproducible from artifacts
- algorithm upgrades without corresponding safety, validation, and traceability updates

## Derived Work Items

This baseline drives the next stages as follows:

- `P1` builds compliant runtime entrypoints, profiles, and run snapshots
- `P2` builds lifecycle, health, fault, and timing control
- `P3` introduces race state machine and safety envelope
- `P4+` removes competition-path ground-truth assumptions and upgrades planning/control/perception

## Change Control

Update this document before continuing development if either condition is met:

- A2RL rule interpretation changes
- official interfaces or deployment expectations differ from the current assumptions
