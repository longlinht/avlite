# Runtime Modes

## Purpose

This document defines the supported AVLite runtime modes and the intended boundary between debug workflows and competition workflows.

## Mode Summary

| Mode | Primary Use | Human Interaction | Competition Main Path |
|------|-------------|-------------------|-----------------------|
| `debug_gui` | local debugging, visualization, rapid tuning | high | no |
| `sim_headless` | headless simulation and regression | low | indirect |
| `ros_integration` | ROS2 / external interface integration | low to medium | yes, as bridge path |
| `competition_headless` | unattended competition execution | none after launch | yes |
| `offline_replay` | replay, metrics, audit, regression triage | none required | supporting path |

## `debug_gui`

### Purpose

Use the Tk-based visualizer to inspect stack behavior, tune parameters, and debug components interactively.

### Characteristics

- may expose rich controls and debug views
- may use simulator shortcuts or developer conveniences
- supports rapid iteration and visualization

### Constraints

- must not be the only way to start the stack
- must not be treated as the competition runtime
- any debug-only capability must be clearly isolated from competition profiles

## `sim_headless`

### Purpose

Run the stack without GUI for simulation-based testing, CI-style regression, and timing checks.

### Characteristics

- deterministic command-line launch
- explicit profile selection
- structured logs and artifacts
- suitable for repeatable automated validation

### Required Outcomes

- start and stop without Tk dependencies
- capture run metadata
- support scripted regression scenarios

## `ros_integration`

### Purpose

Exercise AVLite through ROS2 or official external interfaces rather than through an internal simulator-only path.

### Characteristics

- strict topic / message / API contracts
- bridge between AVLite modules and external ecosystem
- timing and lifecycle expectations closer to deployment conditions

### Required Outcomes

- clear ownership between runtime, ROS nodes, and bridge logic
- documented message contracts and race-state inputs
- support for validation of interface compatibility

## `competition_headless`

### Purpose

Serve as the primary race-day execution mode for official sessions or session-like dry runs.

### Characteristics

- no GUI dependency
- unattended operation after launch
- lifecycle-managed startup and shutdown
- watchdog, health, fault, and state handling
- explicit exit codes and run artifact capture

### Required Outcomes

- one-command startup with a competition profile
- deterministic runtime initialization order
- reaction to race-state and safety events
- crash/fault visibility and controlled degraded behavior

## `offline_replay`

### Purpose

Replay recorded runs for debugging, metrics extraction, incident analysis, and regression comparison.

### Characteristics

- consumes stored run artifacts
- can run slower or faster than wall clock if needed
- should reproduce enough runtime context for diagnosis

### Required Outcomes

- input format aligned with run artifact schema
- deterministic reprocessing of key events and timing
- compatibility with traceability and acceptance metrics

## Mode Boundaries

The following boundaries apply across all modes:

- `debug_gui` is for developer productivity, not race operations
- `competition_headless` is the canonical deployment target
- `sim_headless` and `offline_replay` are validation paths for `competition_headless`
- `ros_integration` is the interface validation and deployment-adjacent path

## CLI Direction

The planned CLI mapping is:

- `python -m avlite gui`
- `python -m avlite race --profile <name>`
- `python -m avlite replay --run-dir <path>`

This mode split is the design contract that `P1` must implement.
