# ROS 2 callback concurrency

An executor supplies threads; callback groups decide which callbacks may use
them concurrently.

- A multithreaded executor alone does not parallelize a node whose callbacks
  all use its implicit mutually exclusive callback group.
- Put callbacks that may overlap in different mutually exclusive groups, or
  use a reentrant group only when the same callback may safely overlap itself.
- Keep shared state, blocking calls, callback duration, and downstream thread
  safety visible when choosing a group. More threads do not make unsafe code
  safe.
- Prove the intended overlap with timestamps or tracing. Do not infer it from
  the executor name.
- Callback-group APIs and executor behavior vary across client libraries and
  ROS distributions. Check the project's installed API and current
  [ROS 2 executor documentation](https://docs.ros.org/en/rolling/Concepts/Intermediate/About-Executors.html)
  before copying exact syntax.

Robium observed this failure mode in the Rolling `ros2/examples` repository on
2026-08-02: callbacks left in the default group remained serialized under a
`MultiThreadedExecutor`. Treat that as evidence for the model, not a frozen API
example for another distribution.
