# Stack selection decision trees

The reasoning behind architect's routing table. Three decisions: middleware,
simulator, training framework. Each ends at a concrete, verified default and the
robium skill that owns the build. **Verify version facts against current docs
before committing them to a brief**; the defaults below were current as of
mid-2026 but robotics moves fast.

## Verified defaults (mid-2026)

| Component | Default | Why |
|---|---|---|
| ROS 2 distro | **Lyrical Luth** (general default); **Jazzy Jalisco** for the Nav2 vertical | Lyrical Luth is the current newest LTS (GA 2026-05-22, supported to May 2031); default for new apps. Nav2 has not yet released binaries for Lyrical (tracked in `ros-navigation/navigation2#6123`), so the ROS 2 + Nav2 + Gazebo path still defaults to Jazzy Jalisco (LTS, supported to May 2029) until that lands. Kilted Kaiju is non-LTS and nearing its own EOL (~Dec 2026); don't pick it as a new default. |
| Simulator (ROS 2) | **Gazebo Jetty** with Lyrical; **Gazebo Harmonic** with Jazzy | Each is the officially paired sim for its ROS 2 distro, installed via ROS vendor packages. Both Jetty and Harmonic are themselves LTS Gazebo releases. |
| Manipulation learning | **LeRobot** (v0.6+) | Open, actively developed; supports ACT, Diffusion Policy, VQ-BeT, TDMPC, SmolVLA, π0/π0.5; ships sim + eval tooling; broad arm support (SO-100/101, Koch, LeKiwi, Reachy2). |
| GPU sim / RL | **Isaac Sim + Isaac Lab** | Only when the NVIDIA RTX GPU floor is met (see below); otherwise stay in LeRobot's sim. |

## Decision 1. Middleware: ROS 2 or not?

```
Is the robot a mobile base / arm / multi-node system that needs
standard drivers, message passing, and an ecosystem of packages?
├─ Yes → ROS 2 (default Lyrical Luth; Jazzy Jalisco for the Nav2
│        vertical; see verified defaults above).  Route: ros2
│        Navigation on top?      → nav2
│        Needs a simulator?      → Decision 2
└─ No  → Is it a pure learning/policy problem with no runtime robot
         middleware (train a policy, evaluate in a learning sim)?
         ├─ Yes → skip ROS 2 for the MVP; LeRobot owns the loop. Route: lerobot
         └─ Unsure → default to ROS 2; it is the safer, more interoperable base
                     and nothing about it blocks adding a learning stack later.
```

**Notes**
- ROS 2 is the substrate for the navigation golden path. Even manipulation apps
  often add ROS 2 later for hardware drivers, but don't force it into an MVP
  that only needs to train and evaluate a policy.
- Middleware/comms choices *within* a ROS 2 app (topics vs services vs zenoh vs
  gRPC across process boundaries) are the `integration` skill's job, not this
  decision.

## Decision 2. Simulator: Gazebo or Isaac?

```
Do you have a dedicated NVIDIA RTX GPU meeting the Isaac floor?
(RTX 4080+, 16 GB VRAM minimum, 32 GB+ system RAM, Linux; no macOS)
├─ No  → Gazebo Harmonic.  Route: gazebo   (the only viable ROS 2 sim here)
└─ Yes → What do you need the sim for?
         ├─ ROS 2 robot in a physics world, sensors, nav testing
         │     → Gazebo Harmonic is still the simpler, better-integrated
         │       choice for the nav vertical. Route: gazebo
         ├─ Photorealistic rendering / synthetic perception data
         │     → Isaac Sim. Route: isaac-sim
         └─ Massively parallel RL environments (thousands of envs on GPU)
               → Isaac Lab (on Isaac Sim). Route: isaac-lab
```

**Notes**
- Default to **Gazebo** unless there's a concrete reason to pay the Isaac cost
  (GPU requirement, driver setup, Linux-only, steeper learning curve). "It looks
  nicer" is not a reason for an MVP.
- If GPU availability is unconfirmed, do **not** design the MVP around Isaac;
  pick Gazebo (or LeRobot's own sim) and log the GPU question as an open risk.
- The `simulation` umbrella covers sensor-simulation correctness (noise, rates,
  frames) independent of which engine you pick.

## Decision 3. Training / policy framework

```
Are you learning a control policy (imitation or RL)?
├─ No  → no training framework needed; classical nav/control via nav2/ros2.
└─ Yes → What kind?
         ├─ Imitation / behavior cloning from demos (teleop or datasets),
         │  manipulation especially
         │     → LeRobot. Route: lerobot   (+ huggingface for data/models)
         ├─ Reinforcement learning at scale, GPU available
         │     → Isaac Lab. Route: isaac-lab
         └─ Small-scale RL / no GPU
               → LeRobot's tooling or a lightweight gym; keep it CPU/uv.
```

**Data sourcing** for any learning path is the `data` skill's call (offline
datasets vs sim-generated vs teleop-collected), and Hub pulls/pushes go through
the self-contained `huggingface` skill.

## Where each decision is recorded

Material branches become concise decisions in `docs/architecture-brief.md`.
Unresolved high-impact branches (GPU unknown, a version pin constrained by an
unverified dependency) remain provisional assumptions with a cheap validation
step and an authorized pivot. See `brief-template.md`.
