# simulation — mined observations

## package layout: TB3 vendors a fully self-contained sim stack; TB4 is a thin wrapper over a separately-maintained base-robot vendor family <!-- id: obs-simulation-002 -->
status: tentative
proof: 1
signal: better-method
sources: [ROBOTIS-GIT/turtlebot3_simulations@9be186f, turtlebot/turtlebot4_simulator@b7d0f3b]
target: simulation (new-section, decision guidance) — decision surface for module boundaries when a robot is built on an existing base platform vs. fully custom. TB3: 3 packages, zero base-robot vendor dependency (`turtlebot3_gazebo/package.xml` depends only on generic `ros_gz_*`/`gz_*_vendor`/message packages — custom base, nothing to compose over). TB4: 4 own packages but `turtlebot4_gz_bringup/package.xml` depends on 7 `irobot_create_*` packages (Create 3, a third-party base maintained separately). Distro-control: both default branches resolve to Jazzy+Harmonic (byte-diff evidence: obs-gazebo-004) — not a distro artifact.
evidence: official repos, illustrates a real structural choice, not yet a robium trial (comparative mining run, direct clone read 2026-08-02 @ b7d0f3b/9be186f; single comparative reading — not independently reproven, re-verify against a robium scaffold before treating either side as the recommended default)
origin: external
source: turtlebot/turtlebot4_simulator@b7d0f3b turtlebot4_gz_bringup/package.xml#L26-L32
quote: <depend>irobot_create_description</depend>
  <depend>irobot_create_common_bringup</depend>
  <depend>irobot_create_nodes</depend>
  <depend>irobot_create_toolbox</depend>
  <depend>irobot_create_gz_bringup</depend>
  <depend>irobot_create_gz_plugins</depend>
  <depend>irobot_create_gz_toolbox</depend>
