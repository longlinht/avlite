# AVLite Formal Development Master Plan for the A2RL Racing Competition

## 1. Document Positioning

This document is the main plan and execution baseline for the subsequent development of `/home/a2rl/avlite`.

From the moment this document is established, all subsequent development must follow these rules by default:

1. All feature development, refactoring, testing, and deployment work must map to the phases, tasks, or acceptance items in this plan.
2. If this plan is found to conflict with new A2RL rules, official interfaces, or the real deployment environment, this document must be updated first before continuing development.
3. Any capability that is "convenient for debugging but unsuitable for competition" must not directly enter the main competition pipeline.
4. The GUI is only a debugging and visualization tool and must no longer serve as the entry point for competition operation.

This plan is based on two inputs:

1. Rule document: `/home/a2rl/Dropbox/Workspace/a2rl-rules.md`
2. In-depth reading and assessment of the current codebase

## 2. A2RL Hard Constraints on This Project

## 2.1 Competition Objective

A2RL is an autonomous racing software competition on a unified hardware platform. Public information indicates that the target capability is not merely "being able to drive one lap autonomously," but rather:

- High-speed single-car lap time performance
- High-speed straight-line speed control
- Two-car overtaking and defending
- Multi-car competition
- Stable unattended operation during official sessions

## 2.2 Typical Competition Phases

This project must ultimately support at least four scenarios:

1. `Lap Test`
2. `Speed Test`
3. `Overtaking Challenge`
4. `Multi-Car Race`

## 2.3 Deployment Constraints

The following software deployment constraints can be inferred from the rule document:

- The software runs on a unified onboard HPC and may not rely on manual remote control or online fixes.
- During official sessions, it may not rely on SSH parameter tuning, manual hotfixes, or human takeover.
- The software must support one-click startup, unattended operation, crash recovery, exception degradation, data logging, and post-race auditing.
- The software must adapt to official input/output interfaces, typically in a form close to `ROS2 + agreed messages/API`.
- The software must be governed by race control states such as `Start / Stop / Safety Car / Yellow Flag / Red Flag`.

## 2.4 Technical Target Range

The rule document does not provide a complete public rulebook with exact numeric thresholds, but as engineering targets, this project will align by default with the following ranges:

- Lateral localization error target: `<= 0.10 ~ 0.15 m`
- Attitude error target: `< 0.5 deg`
- Opponent vehicle update rate: `>= 20 ~ 30 Hz`
- Local planning rate: `>= 20 ~ 50 Hz`
- Control rate: `>= 100 ~ 200 Hz`
- End-to-end perception-to-actuation closed-loop latency: `< 80 ~ 100 ms`
- Session-level stability: `20 ~ 40 min` with no fatal failures

## 3. Assessment of the Current Codebase

Conclusion: `avlite` is currently a clearly structured autonomous driving prototype framework, but it is still clearly far from A2RL race deployment. What is needed is not local patching, but a systematic upgrade from a "prototype stack" to a "competition runtime stack."

## 3.1 Current Reusable Foundations

- Clear modular layering: perception, localization, planning, control, execution, bridging, visualization, and extensions.
- A strategy registration mechanism already exists, making it easier to replace algorithms with competition-grade ones later.
- An initial ROS2/Autoware extension structure already exists.
- Track data and race line files already exist.
- Existing local planning and control baselines can serve as low-speed or simulation baselines.

## 3.2 Current Key Gaps

### A. The runtime entry point and deployment mode do not meet competition requirements

- [`avlite/__main__.py`](/home/a2rl/avlite/avlite/__main__.py) still uses the Tk GUI as the only entry point.
- There is no standalone headless race runner.
- There is no session management, startup checking, exit codes, or run artifact archival.

### B. The execution layer is still in a teaching/prototype style

- [`avlite/c40_execution/c43_sync_executer.py`](/home/a2rl/avlite/avlite/c40_execution/c43_sync_executer.py) uses a soft loop and `time.sleep()` with no deadline management.
- [`avlite/c40_execution/c44_async_threaded_executer.py`](/home/a2rl/avlite/avlite/c40_execution/c44_async_threaded_executer.py) has a fragile threading model, with unstable lock boundaries and responsibility separation.
- There is no unified runtime health, timeout policy, backpressure mechanism, or degradation policy.

### C. Global and local planning only satisfy a basic closed loop, not competitive racing

- In [`avlite/c20_planning/c24_global_planners.py`](/home/a2rl/avlite/avlite/c20_planning/c24_global_planners.py), `RaceGlobalPlanner.plan()` is empty.
- The current global plan mainly relies on static race line files and lacks multi-line support, attack/defense lines, and speed profile management.
- [`avlite/c20_planning/c26_local_planners.py`](/home/a2rl/avlite/avlite/c20_planning/c26_local_planners.py) is only a basic lattice avoidance logic and lacks a behavior layer, game-theoretic layer, and race-control-state constraints.

### D. The controller does not have high-speed racing capability

- [`avlite/c30_control/c34_stanley.py`](/home/a2rl/avlite/avlite/c30_control/c34_stanley.py) and [`avlite/c30_control/c33_pid.py`](/home/a2rl/avlite/avlite/c30_control/c33_pid.py) are still baseline controllers.
- There is no dynamic limiting, tire-limit management, speed-domain scheduling, feedforward term, or race-state-aware constrained control.
- The current parameters and default vehicle model are only suitable for simplified models and not for A2RL speed levels.

### E. The perception and localization main pipeline heavily depends on ground-truth assumptions

- The world capabilities in [`avlite/c60_common/c62_capabilities.py`](/home/a2rl/avlite/avlite/c60_common/c62_capabilities.py) still lean toward ground truth / RGB / LiDAR and do not cover real racing interfaces.
- [`avlite/extensions/multi_object_prediction/e10_perception/perception.py`](/home/a2rl/avlite/avlite/extensions/multi_object_prediction/e10_perception/perception.py) depends by default on `GT_DETECTION / GT_TRACKING / GT_LOCALIZATION`.
- Although the localization interface has been abstracted, there is still no competition-grade state-estimation pipeline.

### F. ROS2 integration has not yet reached formal deployment quality

- [`avlite/extensions/executer_ros/e41_ros_launcher.py`](/home/a2rl/avlite/avlite/extensions/executer_ros/e41_ros_launcher.py) uses `SingleThreadedExecutor` for multiple high-frequency nodes, which is unsuitable for competition load.
- ROSExecuter both runs local logic and launches ROS nodes, resulting in duplicated responsibilities and mixed timing behavior.
- The Planner/Controller/World nodes are more demonstration-level bridges than strict data contracts and competition-grade runtime components.

### G. The world bridge and vehicle model are overly simplified

- [`avlite/c40_execution/c46_basic_sim.py`](/home/a2rl/avlite/avlite/c40_execution/c46_basic_sim.py) is a simple kinematic model and is insufficient for validating high-speed limit conditions.
- There is no real sensor timing, actuator delay, chassis constraints, or tire dynamics.

### H. Safety, state machine, logging, and testing systems are far from complete

- No unified race state machine.
- No flag handling.
- No watchdog / supervisor / heartbeat.
- No structured run artifacts.
- No system regression testing, performance testing, or long-duration stability testing.
- Current tests are almost limited to style checks, and even `pytest` is not installed locally for direct execution.

## 4. Overall Transformation Goal

The goal of this project is not to "make the current demo a bit stronger," but to evolve AVLite into a competition software baseline suitable for A2RL-style deployment. It should ultimately provide the following capabilities:

1. Support formal competition operation modes beyond the GUI.
2. Support a stable runtime for high-frequency closed-loop control and long sessions.
3. Support real competition interface integration and race-control-state handling.
4. Support single-car lap performance, multi-car competition, fault degradation, and post-race auditing.
5. Support containerization, reproducibility, replay, and acceptance validation.

## 5. Execution Principles

1. Build the runtime, safety, and validation foundation before upgrading algorithms.
2. Eliminate dependence on ground truth in the main pipeline before discussing competition deployment.
3. Establish metrics and acceptance criteria before doing performance optimization.
4. Each phase must have clear deliverables and exit criteria.
5. Any new capability must be accompanied by configuration, documentation, tests, and observability.

## 6. Target Architecture

The target architecture is divided into six layers:

1. `Competition Runtime`
   - headless entry point
   - lifecycle management
   - watchdog / supervisor
   - run artifact management
2. `State & Safety`
   - race state machine
   - safety envelope
   - fault manager
   - degraded mode / safe stop
3. `IO & Bridge`
   - ROS2 / official interface adaptation
   - sensor and chassis data contracts
   - control output contract
4. `Estimation & Perception`
   - fused localization with GNSS/IMU/OSS/wheel speed
   - opponent detection / tracking / prediction
5. `Planning & Control`
   - global racing line management
   - local behavior decision-making and trajectory generation
   - high-frequency racing control
6. `Validation & Deployment`
   - simulation regression
   - replay
   - metrics
   - packaging

## 7. Phased Development Plan

## P0. Rule Consolidation and Requirements Baseline

### Objective

Convert textual requirements from the rule document into engineering requirements, interface requirements, and acceptance metrics.

### Tasks

1. Create `docs/a2rl_requirements.md`
   - Structured recording of competition phases, deployment requirements, safety requirements, interface requirements, and prohibited items.
2. Create `docs/a2rl_targets.md`
   - Record frequency, latency, localization accuracy, adversarial capability, and reliability targets.
3. Create `docs/runtime_modes.md`
   - Clearly define five modes: `debug_gui`, `sim_headless`, `ros_integration`, `competition_headless`, `offline_replay`.
4. Create a requirements traceability table
   - Each requirement maps to code modules, tests, and acceptance items.

### Deliverables

- `docs/a2rl_requirements.md`
- `docs/a2rl_targets.md`
- `docs/runtime_modes.md`

### Acceptance

- All subsequent tasks can be traced back to explicit rules or metrics.

## P1. Refactor Runtime Entry Point and Configuration System

### Objective

Establish a competition-mode entry point and completely remove GUI dependence.

### Tasks

1. Refactor the entry point
   - Change [`avlite/__main__.py`](/home/a2rl/avlite/avlite/__main__.py) into a CLI dispatch entry point.
   - Provide at least three commands:
     - `python -m avlite gui`
     - `python -m avlite race --profile <name>`
     - `python -m avlite replay --run-dir <path>`
2. Create a `competition_headless` runtime path
   - No Tk dependency
   - Can start, stop, and return clear exit codes directly
3. Clean up the configuration system
   - Remove workstation paths, obsolete profiles, and experimental profiles from current YAML files.
   - Define formal profiles:
     - `a2rl_sim_baseline`
     - `a2rl_ros_baseline`
     - `a2rl_replay`
4. Add runtime snapshots
   - Automatically record profile, git revision, dependency versions, command-line arguments, and timestamps.

### Deliverables

- CLI entry point
- Formal profiles
- Run metadata snapshot

### Acceptance

- The system can fully start up and shut down without the GUI.
- Every run is fully reproducible.

## P2. Competition Runtime and Lifecycle Management

### Objective

Refactor the execution layer into a competition runtime rather than a simple synchronous/threaded demo.

### Tasks

1. Create core runtime modules
   - `CompetitionRunner`
   - `LifecycleManager`
   - `HealthMonitor`
   - `FaultManager`
2. Unify periodic scheduling
   - Clearly define periods, deadlines, and timeout policies for perception / localization / planning / control.
   - No longer rely on a loose `time.sleep()` main loop.
3. Unify component health status
   - Components must report:
     - last update time
     - execution time
     - error count
     - stale status
4. Add supervisor/watchdog
   - Handle thread deadlocks, node disconnects, data timeouts, and abnormal control outputs.
5. Unify shutdown behavior
   - controlled stop
   - log flushing
   - resource release

### Key Files Involved

- [`avlite/c40_execution/c41_execution_model.py`](/home/a2rl/avlite/avlite/c40_execution/c41_execution_model.py)
- [`avlite/c40_execution/c42_factory.py`](/home/a2rl/avlite/avlite/c40_execution/c42_factory.py)
- [`avlite/c40_execution/c43_sync_executer.py`](/home/a2rl/avlite/avlite/c40_execution/c43_sync_executer.py)
- [`avlite/c40_execution/c44_async_threaded_executer.py`](/home/a2rl/avlite/avlite/c40_execution/c44_async_threaded_executer.py)

### Deliverables

- Competition runtime skeleton
- Unified health/status data structures
- Bounded shutdown flow

### Acceptance

- Component timeouts and crashes can be detected and reported.
- The runner can operate for 30 minutes without resource leaks or control thread runaway.

## P3. Refactor Data Contracts and Capability Model

### Objective

Expand the current "prototype world capabilities" into input/output contracts for real racing.

### Tasks

1. Expand the capability enumeration
   - Add:
     - radar
     - GNSS
     - IMU
     - wheel odometry
     - optical speed sensor
     - chassis telemetry
     - race control state
2. Define standard data models
   - `SensorFrame`
   - `VehicleState`
   - `TrackedObject`
   - `RaceControlState`
   - `HealthStatus`
3. Separate the main pipeline from simulation-assistance capabilities
   - Ground truth may only exist in the simulation/debug auxiliary layer.
4. Define versioned input/output contracts
   - To support replay, bridging, and testing.

### Key Files Involved

- [`avlite/c60_common/c62_capabilities.py`](/home/a2rl/avlite/avlite/c60_common/c62_capabilities.py)
- [`avlite/c10_perception/c11_perception_model.py`](/home/a2rl/avlite/avlite/c10_perception/c11_perception_model.py)
- [`avlite/c40_execution/c41_execution_model.py`](/home/a2rl/avlite/avlite/c40_execution/c41_execution_model.py)

### Deliverables

- New capability model
- Unified data contracts
- Contract documentation

### Acceptance

- Any bridge or algorithm module may interact only through the unified contracts.

## P4. Race State Machine and Safety Layer

### Objective

Establish the state machine and safety constraints required for competition.

### Tasks

1. Implement the race state machine
   - `INIT`
   - `READY`
   - `RUNNING`
   - `YELLOW_FLAG`
   - `SAFETY_CAR`
   - `RED_FLAG`
   - `DEGRADED`
   - `SAFE_STOP`
   - `SHUTDOWN`
2. Implement the safety envelope
   - trajectory validity checks
   - control output limiting
   - localization jump checks
   - perception disconnect checks
   - stale trajectory checks
3. Implement fail-safe policies
   - progressive deceleration
   - minimal-risk stop
   - prohibit continued aggressive behavior
4. Introduce a race control input interface
   - Support official race control command injection.

### Deliverables

- state machine module
- safety manager
- fault-to-action mapping table

### Acceptance

- When any critical module times out or data becomes invalid, the vehicle enters controlled degradation.
- Yellow/Red/Safety Car states can alter planning and control outputs.

## P5. Refactor ROS2 / Official Interface Bridge

### Objective

Refactor the current demonstration-grade ROS extension into a formal bridge layer.

### Tasks

1. Refactor ROSExecuter
   - Remove the mixed mode of "local logic execution + ROS node execution."
   - Separate:
     - internal stack mode
     - external ROS integration mode
2. Upgrade `SingleThreadedExecutor` to an architecture suitable for high-frequency nodes
   - multiple executors or `MultiThreadedExecutor`
   - clearly defined callback groups
3. Rewrite the planner/controller/world/perception node contracts
   - Each should have only a single responsibility.
4. Introduce staleness, QoS, clock synchronization, and message latency statistics.
5. Add topic / service / API adaptation for race control.

### Key Files Involved

- [`avlite/extensions/executer_ros/e41_ros_launcher.py`](/home/a2rl/avlite/avlite/extensions/executer_ros/e41_ros_launcher.py)
- [`avlite/extensions/executer_ros/e43_planner_node.py`](/home/a2rl/avlite/avlite/extensions/executer_ros/e43_planner_node.py)
- [`avlite/extensions/executer_ros/e44_controller_node.py`](/home/a2rl/avlite/avlite/extensions/executer_ros/e44_controller_node.py)
- [`avlite/extensions/executer_ros/e45_world_node.py`](/home/a2rl/avlite/avlite/extensions/executer_ros/e45_world_node.py)
- [`avlite/extensions/executer_ros/e47_proxy_strategies.py`](/home/a2rl/avlite/avlite/extensions/executer_ros/e47_proxy_strategies.py)

### Deliverables

- Stable ROS2 bridge
- Clear topic contracts
- QoS / latency configuration

### Acceptance

- Under ROS integration mode, long-duration operation does not produce responsibility conflicts or duplicate control.

## P6. Localization and State Estimation Main Pipeline

### Objective

Build a competition-grade localization main pipeline and remove dependence on ground-truth ego state.

### Tasks

1. Design the state estimation interface
   - GNSS/IMU/OSS/wheel-speed inputs
   - unified timestamps and coordinate frames
2. Implement baseline localization
   - EKF/UKF fused localization
   - estimate velocity, heading, and yaw rate
3. Add localization health monitoring
   - covariance
   - stale
   - jump detection
   - confidence degradation
4. Support simulation and replay inputs
   - Simulation should generate approximate sensor streams instead of directly injecting ground-truth pose.

### Deliverables

- baseline state estimator
- localization health metrics
- replayable sensor interface

### Acceptance

- The main pipeline no longer requires `GT_LOCALIZATION`.

## P7. Perception, Tracking, and Prediction Main Pipeline

### Objective

Build the opponent perception main pipeline and remove dependence on GT detection/tracking.

### Tasks

1. Refactor perception capabilities and pipeline
   - detection
   - tracking
   - prediction
   - fusion
2. Define a baseline opponent detection pipeline
   - lidar/radar/camera input interfaces
   - ROI filtering
   - multi-object tracking
3. Implement relative-state outputs
   - position
   - velocity
   - heading
   - occupancy / prediction
4. Convert the existing `MultiObjectPredictor` into a pluggable prediction component rather than GT-based main perception.
5. Add perception health and fallback
   - Limit aggressive overtaking when confidence is low.

### Deliverables

- baseline perception pipeline
- tracked object schema
- prediction plugin contract

### Acceptance

- The main pipeline no longer depends on `GT_DETECTION / GT_TRACKING`.

## P8. Upgrade Global Racing Line, Behavior Layer, and Local Planning

### Objective

Upgrade the current "static race line + basic lattice" into a planning system suitable for racing competition.

### Tasks

1. Complete `RaceGlobalPlanner`
   - multi-racing-line management
   - baseline lap line
   - attack line
   - defend line
   - caution line
2. Refactor the global plan data structure
   - route version
   - speed profile
   - lateral boundary
   - attack/defense priority
3. Add a behavior layer
   - follow
   - attack
   - defend
   - yield
   - caution
   - safe stop
4. Upgrade the local planner
   - Transition from random-sampling lattice to a controllable candidate trajectory set
   - Introduce spatiotemporal prediction constraints for opponent vehicles
   - Introduce race-control-state constraints
   - Introduce speed / curvature / acceleration constraints

### Key Files Involved

- [`avlite/c20_planning/c24_global_planners.py`](/home/a2rl/avlite/avlite/c20_planning/c24_global_planners.py)
- [`avlite/c20_planning/c23_local_planning_strategy.py`](/home/a2rl/avlite/avlite/c20_planning/c23_local_planning_strategy.py)
- [`avlite/c20_planning/c26_local_planners.py`](/home/a2rl/avlite/avlite/c20_planning/c26_local_planners.py)
- [`avlite/c20_planning/c27_lattice.py`](/home/a2rl/avlite/avlite/c20_planning/c27_lattice.py)
- [`avlite/c20_planning/c28_trajectory.py`](/home/a2rl/avlite/avlite/c20_planning/c28_trajectory.py)

### Deliverables

- Multi-line global planning
- Behavior layer
- New local planner

### Acceptance

- Supports high-speed single-car lap performance and two-car attack/defense line switching.

## P9. Racing Control Upgrade

### Objective

Upgrade the current baseline control into a control architecture suitable for high-speed racing.

### Tasks

1. Keep Stanley/PID as baseline/debug controllers.
2. Add a primary competition controller
   - Recommended priority:
     - feedforward + feedback racing trajectory tracking control
     - linear MPC
     - constraint-aware longitudinal controller
3. Add control protection
   - steering rate limit
   - accel/brake jerk limit
   - lateral acceleration limit
   - trajectory feasibility check
4. Establish speed-profile tracking and emergency braking mechanisms
   - Integrated with the safety layer.

### Key Files Involved

- [`avlite/c30_control/c32_control_strategy.py`](/home/a2rl/avlite/avlite/c30_control/c32_control_strategy.py)
- [`avlite/c30_control/c33_pid.py`](/home/a2rl/avlite/avlite/c30_control/c33_pid.py)
- [`avlite/c30_control/c34_stanley.py`](/home/a2rl/avlite/avlite/c30_control/c34_stanley.py)

### Deliverables

- Primary competition controller
- Protective limiters
- Control metrics dashboard

### Acceptance

- Under high-speed conditions, control outputs are stable, limitable, and degradable.

## P10. Simulation and Digital Twin Capability

### Objective

Build a simulation layer that genuinely supports development and regression, rather than relying only on `BasicSim`.

### Tasks

1. Explicitly downgrade `BasicSim` to a simplified debugging world.
2. Enhance the simulation interface
   - sensor latency
   - actuator latency
   - noise model
   - data loss
3. Create A2RL-style simulation profiles
   - single car
   - two cars
   - six-car multi-lap
4. Support offline replay
   - Record sensor inputs and control outputs to support offline reproduction.

### Deliverables

- replay engine
- regression scenarios
- more realistic simulation configuration

### Acceptance

- Any critical bug can be stably reproduced through replay.

## P11. Observability, Logging, Data Recording, and Post-Race Analysis

### Objective

Meet unattended-operation and post-race auditing requirements.

### Tasks

1. Design the run artifact directory structure
   - config snapshot
   - metrics
   - events
   - control log
   - localization log
   - perception log
   - replay bundle
2. Add structured event logging
   - state transition
   - fault
   - safety intervention
   - overtake event
3. Add online metrics
   - loop frequency
   - latency
   - stale rate
   - control saturation
   - tracking error
4. Add post-race analysis scripts
   - lap summary
   - overtake summary
   - failure summary

### Deliverables

- artifact specification
- metrics pipeline
- post-run analysis tools

### Acceptance

- For any session, key states and fault chains can be traced.

## P12. Testing, Regression, and Entry Gates

### Objective

Establish an entry mechanism where "nothing moves to the next phase unless tests pass."

### Tasks

1. Establish a testing hierarchy
   - unit tests
   - contract tests
   - replay tests
   - scenario tests
   - soak tests
   - performance tests
2. Establish minimum coverage for key modules
   - runtime
   - safety
   - planner
   - controller
   - ROS bridge
3. Establish the CI baseline
   - lint
   - type check
   - unit
   - replay regression
4. Define release gates
   - all mandatory tests pass
   - no blocker faults
   - metrics meet the current phase threshold

### Deliverables

- restructured test directories
- CI configuration
- phase entry criteria

### Acceptance

- Regressions in key functionality can be prevented through automated testing.

## P13. Packaging, Deployment, and Submission Workflow

### Objective

Establish a formal delivery method for the onboard HPC.

### Tasks

1. Add containerization or a fixed deployment manifest
   - image/build recipe
   - runtime environment
   - startup script
2. Complete system dependencies and version pinning
   - Python deps
   - ROS deps
   - optional CUDA deps
3. Add deployment self-checks
   - topic availability
   - config validation
   - health readiness
4. Define submission artifact standards
   - version number
   - change notes
   - configuration package
   - regression result summary

### Deliverables

- deployment documentation
- packaging scripts
- readiness checks

### Acceptance

- Deployment and startup can be completed on the target machine using a fixed procedure.

## 8. Phase Dependency Relationships

The strict dependency order is as follows:

1. `P0 -> P1 -> P2 -> P3 -> P4`
2. `P5` depends on `P2 ~ P4`
3. `P6` and `P7` can proceed in parallel, but both depend on `P3 ~ P5`
4. `P8` depends on `P6` and `P7`
5. `P9` depends on `P8`
6. `P10`, `P11`, and `P12` may progress interleaved, but must not wait until after `P8/P9` is complete to begin
7. `P13` must be completed after the `P11/P12` baseline is established

## 9. Milestone Definitions

## M1. Reproducible Headless Closed Loop

Completion conditions:

- `P0 ~ P2` completed
- Headless baseline can start without GUI
- Configuration snapshot and basic logs exist

## M2. Controllable Safe Operation Baseline

Completion conditions:

- `P3 ~ P5` completed
- Race state machine, safety layer, and stable ROS bridge are in place

## M3. Removal of GT Main-Pipeline Dependence

Completion conditions:

- `P6 ~ P7` completed
- The main pipeline does not rely on GT detection/tracking/localization

## M4. Competition Planning and Control Baseline Achieved

Completion conditions:

- `P8 ~ P9` completed
- Supports single-car lap performance and two-car attack/defense

## M5. Deployment and Regression Capability Achieved

Completion conditions:

- `P10 ~ P13` completed
- Supports replay, long-duration stability, packaging, deployment, and entry gates

## 10. Priority of Phased Deliverables

If resources are insufficient, the priority order is fixed as follows:

1. Runtime and safety
2. Bridge and data contracts
3. Localization and perception main pipeline
4. Planning and control upgrades
5. Regression and deployment workflow
6. GUI and presentation enhancements

## 11. Explicitly Prohibited Items

The following practices are prohibited in subsequent development:

1. Using the GUI as the only runtime entry point.
2. Directly relying on ground truth in the competition main pipeline.
3. Implementing aggressive overtaking algorithms before the state machine and safety layer exist.
4. Doing extensive parameter trial-and-error development before replay and logging closed loops exist.
5. Continuing to mix ROS bridge, planner, controller, and world responsibilities inside one executor.
6. Adding features without adding tests, configuration, and documentation.

## 12. First-Round Implementation Order

Starting from the next development cycle, execution must strictly follow this order:

1. `P0` produces the rules and target documents.
2. `P1` completes the CLI and headless runtime entry point.
3. `P2` establishes the Competition Runtime skeleton.
4. `P3` consolidates the data contracts and capability model.
5. `P4` implements the state machine and safety layer.

Before `P0 ~ P4` are completed, do not proceed to competition-grade perception, adversarial planning, or major controller upgrades.

## 13. Supplementary Notes for This Assessment

This assessment also confirmed the following facts:

- There was previously an untracked version of `Plan.md` in the current repository, and it has now been rewritten as the formal master plan.
- `pytest` is not currently installed in the local environment, so automated tests have not yet been executed; only code reading and structural assessment have been completed.
- The current `requirements.txt` also does not yet include the full dependencies required for testing/CI, which is itself a later refactoring item under `P12/P13`.

This document takes effect from this point onward.
