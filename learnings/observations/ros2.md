# ros2 — mined observations

## launch_testing tests a launched process via generate_test_description + ReadyToTest + post_shutdown_test <!-- id: obs-ros2-001 -->
status: absorbed 2026-08-02
proof: 1
signal: better-method
sources: [ros2/examples@90a5b64]
target: ros2 (new-section) — add a "test a launched process with launch_testing" usage pattern: `@pytest.mark.launch_test` + `@launch_testing.markers.keep_alive` (L26 — keeps the launched process alive through the active-test phase instead of exiting immediately) + `generate_test_description()` returning a `LaunchDescription` that ends with `launch_testing.actions.ReadyToTest()`, an undecorated `unittest.TestCase` for active assertions (`proc_output.assertWaitFor(...)`), and a second `unittest.TestCase` decorated `@launch_testing.post_shutdown_test()` for `launch_testing.asserts.assertExitCodes(proc_info)`. The `testing` skill's `ros2-pytest-vs-launch-testing-split` anchor already routes "needs a running node or launch file" tests here and says ros2 currently has none — this closes that named gap. Note: the cited example launches a bare `echo` subprocess via `ExecuteProcess`, not a ROS 2 node — the same four-part scaffolding applies equally to a `launch_ros.actions.Node`-launched node (see the sibling `check_node_launch_test.py` in the same directory, which asserts on `get_node_names()` instead of stdout). Distro note: mined from the `rolling` branch (2026-08-02 @ 90a5b64); re-verify the `launch_testing` decorator/assertion API surface against Lyrical Luth (this skill's default distro) before absorbing verbatim.
evidence: official repo, consistent with current docs (search-synthesis 2026-08-02 — docs.ros.org direct fetch returned an Anubis "Access Denied" page for the Testing/Integration tutorial; WebSearch snippets from docs.ros.org/en/{rolling,humble,kilted,jazzy}/Tutorials/Intermediate/Testing/Integration.html independently confirm the same four-part structure — generate_test_description, ReadyToTest, an active TestCase, and @post_shutdown_test(); re-verify via direct fetch on absorb)
origin: external
source: ros2/examples@90a5b64 launch_testing/launch_testing_examples/launch_testing_examples/hello_world_launch_test.py#L25-L58
quote: launch_testing.actions.ReadyToTest()

## rclcpp manual composition: NodeOptions constructor + RCLCPP_COMPONENTS_REGISTER_NODE <!-- id: obs-ros2-002 -->
status: ready
proof: 1
signal: better-method
sources: [ros2/examples@90a5b64]
target: ros2 (new-section) — add a "compose nodes into one process" usage pattern for rclcpp, cross-referencing `nav2#composition-vs-standalone` both ways (nav2 already carries the field-tested caveat that composition is "a later performance optimization, not a default to fight while still debugging" — this ros2 addition should link to that caveat, and nav2's anchor should gain a pointer back here for the mechanics, when absorbed — this observation documents how composition works, not a recommendation to prefer it): the node's constructor takes an `rclcpp::NodeOptions` and forwards it to `Node(name, options)` — this example passes it **by value** (`PublisherNode(rclcpp::NodeOptions options)`, L23; upstream docs commonly show `const rclcpp::NodeOptions &` instead, but by-value is what's actually shipped here, so state both forms rather than asserting one); `#include <rclcpp_components/register_node_macro.hpp>` then `RCLCPP_COMPONENTS_REGISTER_NODE(<Class>)` registers the class with `pluginlib` so it *can* be dynamically loaded by a running component container via `ros2 component load` — but note this example's `CMakeLists.txt` only builds `composition_nodes` as a plain `add_library(... SHARED ...)` and never calls the CMake-side `rclcpp_components_register_nodes()`, so as shipped it is **not** loadable that way; instead `composed.cpp`'s hand-written `main()` manually `std::make_shared<PublisherNode>(options)`s two such nodes onto one `SingleThreadedExecutor` — cite this as **manual composition**, not dynamic component loading. Composition only *enables* intra-process comms when `NodeOptions().use_intra_process_comms(true)` is explicitly set; `composed.cpp` uses a default-constructed `rclcpp::NodeOptions options;` (no such call), so intra-process comms are **not** enabled in the cited code — drop "zero-copy" from any framing entirely (it additionally requires `unique_ptr`-based pub/sub on top of intra-process comms, neither of which this example does). Distro note: mined from the `rolling` branch (2026-08-02 @ 90a5b64); re-verify the `rclcpp_components`/CMake shape against Lyrical Luth (this skill's default distro) before absorbing verbatim.
evidence: official repo, consistent with current docs (search-synthesis 2026-08-02 — docs.ros.org direct fetch of Tutorials/Intermediate/Writing-a-Composable-Node.html returned an Anubis "Access Denied" page; WebSearch snippets from the same docs.ros.org URL independently confirm the NodeOptions-constructor requirement and the RCLCPP_COMPONENTS_REGISTER_NODE registration macro as the current, still-recommended pattern; re-verify via direct fetch on absorb)
origin: external
source: ros2/examples@90a5b64 rclcpp/composition/minimal_composition/src/publisher_node.cpp#L23-L41
quote: RCLCPP_COMPONENTS_REGISTER_NODE(PublisherNode)

## rclpy MultiThreadedExecutor concurrency is scoped per callback_group, not per executor <!-- id: obs-ros2-003 -->
status: absorbed 2026-08-02
proof: 1
signal: better-method
sources: [ros2/examples@90a5b64]
target: ros2 (new-section) — add a "control callback concurrency with executors + callback groups" usage pattern: passing a `MutuallyExclusiveCallbackGroup()` instance as `callback_group=` to `create_timer`/`create_subscription`/etc. serializes only that group's callbacks — other callbacks on the node (or a different group) can still run concurrently under a `MultiThreadedExecutor(num_threads=N)`. Without an explicit group, a node's callbacks share one implicit MutuallyExclusiveCallbackGroup by default, so a bare `MultiThreadedExecutor` alone does not parallelize a single node's own callbacks. Name the counterpart too: `ReentrantCallbackGroup` (not exercised in the cited file) lets its own callbacks run concurrently with each other, for when serialization isn't wanted.
evidence: official repo, consistent with current docs (search-synthesis 2026-08-02 — docs.ros.org direct fetch of How-To-Guides/Using-callback-groups.html was not attempted directly this pass; WebSearch snippets from docs.ros.org/en/{humble,iron}/How-To-Guides/Using-callback-groups.html independently confirm both the callback_group= pass-through pattern and that a node's default callback group is itself a MutuallyExclusiveCallbackGroup; re-verify via direct fetch on absorb)
origin: external
source: ros2/examples@90a5b64 rclpy/executors/examples_rclpy_executors/callback_group.py#L33-L37
quote: self.timer = self.create_timer(1.0, self.timer_callback, callback_group=self.group)

## rclpy.init() context-manager + ExternalShutdownException idiom confirmed independent of ros2_documentation <!-- id: obs-ros2-004 -->
status: ready
proof: 1
signal: verified
sources: [ros2/examples@90a5b64]
target: ros2#no-version-facts-from-memory (annotate) — the skill's own `examples/package-ament-python/ros2_example_pkg/talker_node.py` already uses `with rclpy.init(args=args):` + `except (KeyboardInterrupt, ExternalShutdownException): pass`, but cites only `ros2_documentation`'s rolling-branch tutorial and is marked `status: unverified`. ros2/examples' own `rclpy/executors` sample independently uses the identical idiom in real, currently-building code (not a doc snippet) — an independent official-code witness for the same claim, worth citing alongside the docs source. Distro note: this second witness is also from the `rolling` branch (2026-08-02 @ 90a5b64) — the skill's own directive already treats this exact idiom as release-dependent (that's why it's marked unverified in the first place), so this observation adds a second rolling-branch confirmation, it does not lift the general caution for other distros; re-verify against Lyrical Luth (this skill's default distro) specifically before removing the `unverified` marker.
evidence: official repo, consistent with current docs (search-synthesis 2026-08-02 — docs.ros.org direct fetch of rclpy's init_shutdown page was not attempted directly this pass; WebSearch snippets confirm `with rclpy.init(args=args):` as a context manager that raises `ExternalShutdownException` on external shutdown is the documented current idiom, matching what ros2/examples' own code does; re-verify via direct fetch on absorb)
origin: external
source: ros2/examples@90a5b64 rclpy/executors/examples_rclpy_executors/callback_group.py#L47-L64
quote: with rclpy.init(args=args):

## launch-argument philosophy: TB3 duplicates a launch file per world with zero DeclareLaunchArgument; TB4 exposes one parametrized entry with validated toggles — a launch-composition pattern, not a simulator-selection one <!-- id: obs-ros2-005 -->
status: tentative
proof: 1
signal: better-method
sources: [ROBOTIS-GIT/turtlebot3_simulations@9be186f, turtlebot/turtlebot4_simulator@b7d0f3b]
target: ros2#python-launch-default (annotate) — argument-surface decision, via two Gazebo bringup repos. Re-targeted from simulation: `placement.py` scores `ros2` above `simulation` here, and simulation's own anchors are all selection/fidelity, not launch design. TB3: 7 near-duplicate launch files, one per world (`turtlebot3_house.launch.py` vs `turtlebot3_world.launch.py` differ by one filename string, `#L40`, per `diff`), zero `DeclareLaunchArgument`s, nav2 unwired. TB4: one entry launch, `choices=[...]`-validated args + `IfCondition`-gated toggles for rviz/localization/slam/nav2 + namespace. Third design point: nav-trial hand-composed `slam.launch.py`/`nav.launch.py`, used compose `PROFILES` as its toggle (apps/nav-trial/docs/architecture-brief.md:49,58-59,76-79) — a datum, not a recommendation. Distro-control: both default branches resolve to Jazzy+Harmonic (byte-diff: obs-gazebo-004).
evidence: official repos, illustrates a real structural choice, not yet a robium trial (comparative mining run, direct clone read 2026-08-02 @ b7d0f3b/9be186f; single comparative reading — not independently reproven, re-verify against a robium scaffold before treating either side as the recommended default)
origin: external
source: turtlebot/turtlebot4_simulator@b7d0f3b turtlebot4_gz_bringup/launch/turtlebot4_spawn.launch.py#L44-L52
quote: DeclareLaunchArgument('slam', default_value='false',
                          choices=['true', 'false'],
                          description='Whether to launch SLAM'),
    DeclareLaunchArgument('nav2', default_value='false',
                          choices=['true', 'false'],
                          description='Whether to launch Nav2'),
