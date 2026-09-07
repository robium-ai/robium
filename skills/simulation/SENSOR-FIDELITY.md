# Sensor fidelity and repeatability

Use this card for every simulated sensor that affects control, localization,
perception, evaluation, or sim-to-real transfer.

- **Rate:** match the target device and include latency or jitter when they
  materially affect the consumer. A tutorial rate can invalidate downstream
  tuning.
- **Noise:** model the important noise floor, bias, dropout, and quantization.
  Perfect data is a special test fixture, not a realistic default.
- **Geometry:** match pose, field of view, range, resolution, and occlusion.
- **Frames:** publish the same frame names and conventions as the real robot so
  downstream code does not need a simulation-only fork.
- **Time:** derive timestamps from simulation time and set `use_sim_time`
  consistently across every ROS consumer.
- **Dynamics:** for controllers and contacts, state which mass, friction,
  actuator, compliance, and saturation behavior matter. Validate those rather
  than assuming the physics engine's defaults are adequate.

For regression use:

- Control physics step size and seeds for noise, randomization, and initial
  conditions.
- Separate genuine stochastic coverage from accidental nondeterminism.
- Assert behavior with tolerances and invariants: arrival, clearance, bounded
  error, stable contact, or expected message sequence.
- Record the simulator release, relevant model assets, seeds, and configuration
  beside a failing result so it can be reproduced.

For sim-to-real use:

- Name the remaining domain gaps: appearance, contact, friction, latency,
  calibration, actuator limits, or unmodeled safety behavior.
- Compare a small real recording with simulated output before scaling training
  or tuning around the simulator.
- Use domain randomization to cover justified uncertainty, not to hide a model
  whose known hardware specifications were never entered.

The simulator-specific skill owns the SDF, USD, or MJCF syntax. Current sensor
and physics APIs remain upstream facts and should be verified there.
