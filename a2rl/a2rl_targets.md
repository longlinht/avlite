# A2RL Targets

## Purpose

This document defines the quantitative and qualitative targets that AVLite should use as the working engineering baseline for A2RL-style development. These are project targets, not proof that the current codebase already meets them.

## Target Categories

The targets are grouped into runtime, estimation, planning and control, competitive behavior, and reliability.

## Runtime And Frequency Targets

| ID | Metric | Target |
|----|--------|--------|
| `TGT-RT-001` | perception / opponent update rate | `>= 20 Hz`, target design range `20 ~ 30 Hz` |
| `TGT-RT-002` | localization update rate | `>= 50 Hz` preferred, must not bottleneck planning/control loop |
| `TGT-RT-003` | local planning update rate | `>= 20 Hz`, target design range `20 ~ 50 Hz` |
| `TGT-RT-004` | control update rate | `>= 100 Hz`, target design range `100 ~ 200 Hz` |
| `TGT-RT-005` | perception-to-actuation end-to-end latency | `< 100 ms`, target range `< 80 ~ 100 ms` |
| `TGT-RT-006` | timing model | every critical component defines period, deadline, timeout, and stale-data behavior |

## Estimation Targets

| ID | Metric | Target |
|----|--------|--------|
| `TGT-EST-001` | lateral localization error | `<= 0.15 m`, preferred `<= 0.10 m` |
| `TGT-EST-002` | heading error | `< 0.5 deg` |
| `TGT-EST-003` | ego state continuity | no discontinuity that invalidates controller stability across normal session operation |
| `TGT-EST-004` | opponent state freshness | tracker output remains usable at planning rate without stale bursts exceeding defined timeout budget |

## Planning And Control Targets

| ID | Metric | Target |
|----|--------|--------|
| `TGT-PC-001` | global plan quality | supports racing-line management beyond a single static line |
| `TGT-PC-002` | local planner behavior | handles free-track, overtake, defend, and constrained race-control states |
| `TGT-PC-003` | controller suitability | supports high-speed racing operation with bounded actuation and runtime-safe fallback |
| `TGT-PC-004` | degraded behavior | stale inputs, health faults, or race-state constraints can force reduced-speed or safe-stop commands |

## Competitive Behavior Targets

| ID | Metric | Target |
|----|--------|--------|
| `TGT-CMP-001` | lap test readiness | complete stable autonomous laps without human intervention |
| `TGT-CMP-002` | speed test readiness | maintain lane/track discipline at high straight-line speed |
| `TGT-CMP-003` | overtake readiness | generate and execute opponent-aware pass opportunities when safe and legal |
| `TGT-CMP-004` | defense readiness | maintain legal defensive behavior without destabilizing the vehicle |
| `TGT-CMP-005` | multi-car readiness | preserve stable operation with multiple dynamic opponents |

## Reliability Targets

| ID | Metric | Target |
|----|--------|--------|
| `TGT-REL-001` | session stability | `20 ~ 40 min` continuous operation with no fatal runtime failure |
| `TGT-REL-002` | restart behavior | controlled shutdown and restart path with explicit status |
| `TGT-REL-003` | artifact completeness | every run records enough data for replay, debugging, and audit |
| `TGT-REL-004` | test gating | no stage advances without passing the required validation set |

## Acceptance Use

These targets should be used in three ways:

- as architecture constraints for new runtime and algorithm work
- as acceptance thresholds for stage exit criteria
- as metrics definitions for test, replay, and performance tooling

## Known Gaps Against Current Code

Current repository inspection shows the following gaps versus the target baseline:

- GUI is still the primary launch path
- execution loop timing is not governed by explicit deadlines
- race-state and safety handling are not yet implemented as a unified subsystem
- global and local planning are not yet competition-grade
- control stack remains baseline-level
- perception and localization still lean on ground-truth assumptions in critical paths

## Revision Rule

If official rulebooks or interface specifications provide stricter numeric requirements, those numbers supersede this document and this file must be updated before further implementation continues.
