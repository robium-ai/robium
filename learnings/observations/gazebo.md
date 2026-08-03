# gazebo — mined observations

## vendor top-level gz sim launch always starts the GUI, no headless toggle — second official repo confirms it <!-- id: obs-gazebo-001 -->
status: absorbed 2026-08-02
proof: 2
signal: verified
sources: [ROBOTIS-GIT/turtlebot3_simulations@9be186f, turtlebot/turtlebot4_simulator@b7d0f3b]
target: gazebo#vendor-launch-not-headless (annotate) — second official-repo witness: turtlebot4_gz_bringup's sim.launch.py builds `gz_args` from `world` + `-r` + `-v 4` + `--gui-config` (no `-s`/headless split, no launch arg to skip the GUI) — same no-headless-by-default outcome as TB3's hardcoded `-g` client this anchor already cites, via a structurally different mechanism (one combined launch vs. two split ones).
evidence: official repo, consistent with this skill's existing claim (comparative mining run, direct clone read 2026-08-02 @ b7d0f3b; convergence: present in both members — TB3's own `-s`/`-g` split is already cited in this skill's 1.1.0 changelog note, TB4 independently confirmed here as a second, structurally different instance of the same outcome)
origin: external
source: turtlebot/turtlebot4_simulator@b7d0f3b turtlebot4_gz_bringup/launch/sim.launch.py#L88-L93
quote: ' --gui-config ',

## spawn via ros_gz_sim's create executable: both documented variants (-file and -topic) are live production usage <!-- id: obs-gazebo-002 -->
status: ready
proof: 2
signal: verified
sources: [ROBOTIS-GIT/turtlebot3_simulations@9be186f, turtlebot/turtlebot4_simulator@b7d0f3b]
target: gazebo#spawn-robot-create (annotate) — confirms both documented variants are real, current production usage, not a hypothetical pairing: TB3 spawns via `-file <model.sdf path>` (turtlebot3_gazebo/launch/spawn_turtlebot3.launch.py#L47-L54, not separately cited); TB4 spawns via `-topic robot_description`, publishing the URDF through `robot_state_publisher` first.
evidence: official repo, consistent with this skill's existing claim (comparative mining run, direct clone read 2026-08-02 @ b7d0f3b; convergence: present in both members — the `-file` and `-topic` forms are the same two variants the anchor already documents as alternatives)
origin: external
source: turtlebot/turtlebot4_simulator@b7d0f3b turtlebot4_gz_bringup/launch/turtlebot4_spawn.launch.py#L145-L155
quote: '-topic', 'robot_description'],

## official TB4 sim repo never uses a YAML bridge config_file — bridges via 5 separate CLI-argument parameter_bridge Nodes in ros_gz_bridge.launch.py (6 repo-wide) instead <!-- id: obs-gazebo-003 -->
status: tentative
proof: 1
signal: wrong-guidance
sources: [turtlebot/turtlebot4_simulator@b7d0f3b]
target: gazebo#bridge-config-file (annotate) — TB4 (official, actively-CI'd Jazzy vendor repo cloned 2026-08-02) never uses a YAML `config_file` in its bridge launch (grep: zero matches); it wires 5 separate `parameter_bridge` `Node`s in `ros_gz_bridge.launch.py`, one per topic group (lidar, HMI display/buttons/LEDs, camera) — 6 repo-wide incl. `clock_bridge` at `sim.launch.py:105`. The "belongs in one YAML file" framing overstates universality — a real exception, not a retraction.
evidence: official repo, contradicts this directive as currently worded (comparative mining run, direct clone read 2026-08-02 @ b7d0f3b; single-repo counter-example, not a second convergence witness for a different claim — field-tested-leads: robium's one-YAML-file guidance stays the default recommendation for a project's own bridge set; TB4's grouped-Node pattern is noted alongside as a current vendor exception, flagged for re-verification rather than treated as an established alternative)
origin: external
source: turtlebot/turtlebot4_simulator@b7d0f3b turtlebot4_gz_bringup/launch/ros_gz_bridge.launch.py#L88-L93
quote: arguments=[
            ['/world/', world,
             '/model/', robot_name,
             '/link/rplidar_link/sensor/rplidar/scan' +
             '@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan']
        ],

## vendor branch convention: TB3 ADDITIONALLY keeps a generic main branch (CI'd jazzy+rolling) on top of per-distro branches; TB4 has ONLY per-distro branches, no main/master at all <!-- id: obs-gazebo-004 -->
status: tentative
proof: 1
signal: better-method
sources: [ROBOTIS-GIT/turtlebot3_simulations@9be186f, turtlebot/turtlebot4_simulator@b7d0f3b]
target: gazebo#confirm-gz-ros2-pairing (annotate) — consumer lesson: pin the branch, not just the repo. `git ls-remote --heads`: TB3 = humble/jazzy/main/noetic — ADDITIONALLY keeps a generic `main`, CI'd jazzy+rolling, byte-identical to its `jazzy` package.xml. TB4 = galactic/humble/jazzy only — ONLY distro-named branches, no `main`/`master`. Both default HEADs resolve to Jazzy+Harmonic (distro-control: obs-ros2-005/obs-simulation-002) — coincidence of default branch, not a safer convention. Not a distro-*pairing* divergence; a branch-*naming* one — pin an explicit branch, don't trust default HEAD to imply a distro.
evidence: official repos, illustrates a real structural choice, not yet a robium trial (comparative mining run, direct clone read 2026-08-02 @ b7d0f3b/9be186f; single comparative reading — not independently reproven; branch list for both repos fetched via `git ls-remote --heads` 2026-08-02, not just the shallow clone's default branch)
origin: external
source: ROBOTIS-GIT/turtlebot3_simulations@9be186f .github/workflows/ros-ci.yml#L19-L22
quote: ros_distribution:
          # - humble
          - jazzy
          - rolling
