# Launch patterns

How to write, install, and run ROS 2 launch files, and how to use
remapping/relay to bridge two third-party packages without editing either.

Sources: [ros2/ros2_documentation](https://github.com/ros2/ros2_documentation)
(Launch-file-different-formats.rst, Launch-system.rst,
Using-Substitutions.rst), [ros2/launch](https://github.com/ros2/launch)
(architecture.md), and [ros-tooling/topic_tools
README](https://github.com/ros-tooling/topic_tools/blob/main/README.md),
all fetched via ctx7/direct GitHub raw fetch on 2026-07-10 (docs.ros.org was
blocked by an anti-bot page for direct fetch; re-verify there when
reachable).

## Python launch files are the default

ROS 2 supports Python, XML, and YAML launch files with equivalent core
functionality. Python is the default choice for anything beyond the
simplest static node list: it's the only format with real conditionals,
loops, and composability without a substitution-language workaround. Reserve
XML/YAML for trivial cases or when matching an existing package's convention.

## Minimal launch file

```python
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='my_package',
            executable='my_node',
            name='my_node',
            output='screen',
        ),
    ])
```

`generate_launch_description()` is the required entry point: `ros2 launch`
imports the file and calls this function. `output='screen'` sends the node's
logging to the launching terminal instead of only to the log files.

## Launch arguments and parameters

```python
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'message',
            default_value='hello',
            description='Text this node publishes.',
        ),
        Node(
            package='my_package',
            executable='my_node',
            name='my_node',
            output='screen',
            parameters=[{'message': LaunchConfiguration('message')}],
        ),
    ])
```

Run with `ros2 launch my_package my_launch.py message:="custom text"`.
`parameters=` also accepts a path to a YAML params file (or a
`launch_ros.parameter_descriptions.ParameterFile` when the YAML itself needs
launch substitutions resolved, e.g. `$(env HOME)`-style values); prefer a
YAML file over a long inline dict once a node has more than a handful of
parameters, so the values are reviewable outside the launch file.

## Remapping

```python
Node(
    package='my_package',
    executable='my_node',
    remappings=[('input_topic', 'renamed_topic')],
),
```

Equivalent XML: `<remap from="input_topic" to="renamed_topic"/>` nested
inside a `<node>` tag. Remapping is the first tool to reach for when two
packages almost line up but use different topic/service names; it requires
no source changes in either package.

## Including other launch files

```python
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

IncludeLaunchDescription(
    PythonLaunchDescriptionSource([
        PathJoinSubstitution([
            FindPackageShare('other_package'), 'launch', 'other.launch.py',
        ])
    ]),
    launch_arguments={'some_arg': 'value'}.items(),
),
```

`FindPackageShare` resolves to the installed `share/<package>` directory;
use it instead of a hardcoded path so the include works regardless of where
the workspace was built.

## Installing launch files (ament_python)

Launch files live in a `launch/` directory at the package root and must be
registered in `setup.py`'s `data_files` for `ros2 launch` to find them after
install:

```python
import os
from glob import glob

setup(
    # ...
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
)
```

Also add `<exec_depend>launch</exec_depend>` and
`<exec_depend>launch_ros</exec_depend>` to `package.xml`; a package that
ships launch files but doesn't declare these depends will build fine and
then fail at `ros2 launch` time on a machine that happens not to have them
installed already. See `examples/package-ament-python/` for the full,
working shape.

## Bridging two third-party packages: remap + relay

Two common shapes for gluing packages you don't want to modify:

**Rename at launch time (no extra running node).** Put the remap directly on
whichever `Node` action you already control, as shown above. This is the
default; reach for it first.

**Republish as a standalone node (when neither package's launch file is a
good place to put the remap, or the "bridge" needs to run independently).**
`topic_tools`' `relay` node subscribes to one topic and republishes to
another:

```bash
ros2 run topic_tools relay <intopic> [outtopic]
# e.g.: ros2 run topic_tools relay base_scan my_base_scan
```

If the message *type* also needs to change (not just the topic name),
`relay_field` republishes a field-level expression into a different message
type instead of a straight pass-through:

```bash
ros2 run topic_tools relay_field /chatter /header std_msgs/Header \
  "{stamp: {sec: 0, nanosec: 0}, frame_id: m.data}"
```

Both are separate nodes from the `ros-tooling/topic_tools` package; add
`topic_tools` as a dependency and launch the relay as its own `Node` action
(or `ExecuteProcess`) alongside the two packages being bridged, rather than
forking either package to add compatibility code. This pattern stays inside
one ROS 2 system; if the "third-party package" is actually on the other side
of a non-ROS system boundary, that's the `integration` skill's comms-choice
table, not this one.
