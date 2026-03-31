# Requirements Traceability

## Purpose

This table maps the current requirement baseline to the repository areas, planned tests, and acceptance evidence that should own each requirement.

## Traceability Table

| Requirement ID | Requirement Summary | Current / Planned Code Ownership | Test Or Validation Path | Stage Exit / Acceptance Evidence |
|----------------|---------------------|----------------------------------|-------------------------|----------------------------------|
| `REQ-SCN-001` | lap-test capable runtime | [avlite/c20_planning](/home/a2rl/avlite/avlite/c20_planning), [avlite/c30_control](/home/a2rl/avlite/avlite/c30_control), [avlite/c40_execution](/home/a2rl/avlite/avlite/c40_execution) | headless sim regression, replay comparison | stable autonomous laps in sim or integration environment |
| `REQ-SCN-002` | speed-test capable runtime | [avlite/c20_planning](/home/a2rl/avlite/avlite/c20_planning), [avlite/c30_control](/home/a2rl/avlite/avlite/c30_control) | straight-line speed scenario, control limit validation | bounded deviation at target speed envelope |
| `REQ-SCN-003` | overtaking capability | [avlite/c20_planning](/home/a2rl/avlite/avlite/c20_planning), [avlite/extensions/multi_object_prediction](/home/a2rl/avlite/avlite/extensions/multi_object_prediction) | multi-agent simulation scenarios | safe and legal pass behavior under defined scenarios |
| `REQ-SCN-004` | multi-car race capability | [avlite/c10_perception](/home/a2rl/avlite/avlite/c10_perception), [avlite/c20_planning](/home/a2rl/avlite/avlite/c20_planning), [avlite/c40_execution](/home/a2rl/avlite/avlite/c40_execution) | multi-car stress and long-run tests | stable multi-agent session completion |
| `REQ-DEP-001` | onboard-HPC compatible runtime | [avlite/__main__.py](/home/a2rl/avlite/avlite/__main__.py), [configs](/home/a2rl/avlite/configs) | CLI launch validation | no GUI dependency on competition path |
| `REQ-DEP-002` | no manual intervention during official session | planned runtime modules under `P1/P2` | unattended run drills | no SSH-only dependency in operating procedure |
| `REQ-DEP-003` | one-command start and deterministic stop | [avlite/__main__.py](/home/a2rl/avlite/avlite/__main__.py), planned `CompetitionRunner` | CLI smoke tests | explicit exit code and clean shutdown |
| `REQ-DEP-004` | unattended execution with health checks | planned lifecycle/health modules under `P2` | health fault injection tests | degraded behavior and fault visibility verified |
| `REQ-DEP-005` | run artifact preservation | planned runtime artifact manager under `P1/P2` | replay and metadata completeness checks | reproducible run directory with metadata and logs |
| `REQ-SAF-001` | race state machine gating | planned state and safety subsystem under `P3` | state transition tests | planner/controller obey race state |
| `REQ-SAF-002` | flag handling | planned state and safety subsystem under `P3` | scenario tests for `Start/Stop/SC/Yellow/Red` | required behavior per state demonstrated |
| `REQ-SAF-003` | abnormal-condition handling | planned `HealthMonitor` and `FaultManager` under `P2` | timeout and stale-data injection tests | safe-stop or degraded mode works as designed |
| `REQ-SAF-004` | controlled restart and recovery | planned lifecycle manager under `P2` | restart drills | startup checks and controlled restart behavior documented |
| `REQ-SAF-005` | post-session auditability | planned runtime logging and replay path | replay validation, artifact review | operator can reconstruct session events |
| `REQ-IO-001` | official I/O compatibility | [avlite/extensions/executer_ros](/home/a2rl/avlite/avlite/extensions/executer_ros) | ROS integration tests | message/API compatibility demonstrated |
| `REQ-IO-002` | explicit ego/opponent/session contracts | [avlite/c10_perception](/home/a2rl/avlite/avlite/c10_perception), [avlite/c40_execution](/home/a2rl/avlite/avlite/c40_execution), [avlite/extensions/executer_ros](/home/a2rl/avlite/avlite/extensions/executer_ros) | contract tests | interfaces documented and validated |
| `REQ-IO-003` | planning versus control output separation | [avlite/c20_planning](/home/a2rl/avlite/avlite/c20_planning), [avlite/c30_control](/home/a2rl/avlite/avlite/c30_control) | planner/controller integration tests | command ownership remains clear and testable |
| `REQ-IO-004` | explicit time semantics | [avlite/c40_execution](/home/a2rl/avlite/avlite/c40_execution), planned runtime scheduler under `P2` | timing-budget tests | component periods and deadlines enforced |
| `REQ-IO-005` | offline replay support | planned replay path under `P1/P2` | replay determinism checks | stored artifacts can reproduce key events |
| `REQ-ENG-001` | GUI is debug-only | [avlite/c50_visualization](/home/a2rl/avlite/avlite/c50_visualization), [avlite/__main__.py](/home/a2rl/avlite/avlite/__main__.py) | entrypoint smoke tests | headless path exists and GUI is optional |
| `REQ-ENG-002` | no GT-only competition mainline | [avlite/c60_common/c62_capabilities.py](/home/a2rl/avlite/avlite/c60_common/c62_capabilities.py), [avlite/extensions/multi_object_prediction/e10_perception/perception.py](/home/a2rl/avlite/avlite/extensions/multi_object_prediction/e10_perception/perception.py) | integration tests with non-GT inputs | competition path no longer requires GT assumptions |
| `REQ-ENG-003` | reproducible runtime behavior | [configs](/home/a2rl/avlite/configs), planned runtime metadata snapshot | metadata snapshot tests | run configuration and revision are recoverable |
| `REQ-ENG-004` | feature-to-requirement traceability | this document plus stage docs/tests | document review in every stage | new work mapped before acceptance |
| `REQ-ENG-005` | tests and observability for runtime-critical work | all competition-path modules | unit, integration, replay, and long-run suites | no stage exit without validation evidence |

## Usage Rules

- update this file whenever a new competition-path module is introduced
- add concrete test file references once the tests exist
- keep requirement IDs stable; revise summaries or ownership rather than renumbering without cause
- stage acceptance reviews should cite this table explicitly
