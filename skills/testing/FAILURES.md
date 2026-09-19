# Robotics test failure router

- **Build passes, robot behavior is still unproven**
  - If claiming the behavior works, run the smallest existing check that drives
    it and observes the outcome; add a probe only if needed. Otherwise label it
    unverified and give a concrete manual check, not an automatic new harness.
  - Process presence or a healthy port is readiness evidence, not task success.

- **Test passes after measuring nothing**
  - Count devices, episodes, samples, assertions, and expected artifacts.
  - Fail explicitly when the measured count is zero or the fixture did not
    load.

- **Simulation test flakes**
  - Compare seed, initial state, simulation time, readiness wait, real-time
    factor, and timeout separately.
  - Use event-driven readiness and tolerance bands before increasing retries.

- **Test breaks only in CI**
  - Check display/headless mode, system packages, ROS environment sourcing,
    GPU availability, clocks, filesystem paths, and fixture provenance.
  - Reproduce in the same immutable environment before weakening the assertion.

- **Suite is too slow for normal iteration**
  - Move logic down to unit tests, shrink scenarios and episode sets, and mark
    benchmarks or qualification runs as slow/scheduled.
  - Keep default checks affordable and relevant. Run expensive behavior smokes
    at affected-behavior boundaries or manually/scheduled, not after every edit.

- **A configuration change did not break its test**
  - Look for re-typed literals, assertions on rendered strings, or a test that
    never imports the source constant.

- **Map or sensor-quality assertion is suspiciously easy**
  - Inspect the data encoding and unknown/missing-data representation. A
    numeric midpoint is not automatically a valid free/occupied threshold.

- **Paid remote run fails before application work begins**
  - Separate provider allocation, image pull, hardware compatibility, data
    access, and application startup using provider and workload evidence.
  - Do not spend on another attempt until the failed boundary is known.
