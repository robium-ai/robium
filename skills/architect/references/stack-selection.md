# Stack selection

Use these decisions only when the first application slice has not already made
the stack obvious. Verify supported versions, operating systems, hardware, and
package combinations in current official documentation before recording them.

## Start with the runtime shape

- Choose ROS 2 when the first slice benefits from standard robot drivers,
  multi-node communication, TF, ecosystem packages, or mobile navigation.
- Skip ROS 2 for a self-contained training or policy experiment that does not
  need robot middleware yet. It can be added at the hardware boundary later.
- If processes or hosts need nontrivial boundaries beyond a normal ROS graph,
  let `integration` choose the communication shape after the application
  modules are clear.

Official starting point: [ROS 2 documentation](https://docs.ros.org/).

## Choose a simulator for the evidence

- Prefer Gazebo for ROS-centric mobile robotics, common sensor simulation, and
  machines without a supported NVIDIA GPU.
- Prefer MuJoCo for lightweight contact-rich manipulation where a full ROS
  stack is unnecessary.
- Consider Isaac Sim when photorealistic perception, synthetic data, or the
  NVIDIA ecosystem materially changes the first slice and the machine meets
  its current GPU, driver, memory, OS, and storage requirements.
- Consider Isaac Lab when the actual goal is parallel reinforcement or
  imitation learning on top of Isaac Sim, not simply because a GPU is present.
- If hardware availability is unknown, choose a viable lower-cost path and
  record the higher-cost simulator as a provisional alternative.

Route final selection through `simulation`, then use `gazebo`, `mujoco`, or
`isaac-sim`/`isaac-lab` for mechanics. Current sources:
[Gazebo](https://gazebosim.org/docs/),
[MuJoCo](https://mujoco.readthedocs.io/), and
[Isaac Sim](https://docs.isaacsim.omniverse.nvidia.com/).

## Choose classical or learned behavior

- Use Nav2 through `navigation` when the robot needs classical localization,
  planning, and control for mobile navigation.
- Use `lerobot` for manipulation imitation learning, supported policies, data
  recording, training, and evaluation.
- Use `isaac-lab` for GPU-parallel RL or IL only after the simulator and
  hardware constraints are proven.
- Do not add a training framework to an application whose first behavior is
  fully served by conventional planning or control.

Data sourcing belongs to `data`; Hub operations belong to `huggingface`.
Current sources: [Nav2](https://docs.nav2.org/) and
[LeRobot](https://github.com/huggingface/lerobot).

## Select versions last

- Start from the compatibility matrix of the chosen upstream stack rather than
  selecting every component's newest release independently.
- Prefer a supported release with available binaries for all first-slice
  dependencies. An LTS label alone does not prove that the full combination is
  packaged.
- Verify the installed or containerized combination with the cheapest build and
  launch probe before treating it as an architecture decision.
- Record the working versions as implementation evidence. Revisit them only
  when a dependency, security issue, or required capability forces the change.

## Record only real branches

Put the chosen direction, why it fits now, and the cheapest falsifying probe in
`docs/architecture-brief.md`. Mention alternatives only when they were genuine
contenders. Keep unresolved hardware or compatibility questions provisional
with an explicit fallback.
