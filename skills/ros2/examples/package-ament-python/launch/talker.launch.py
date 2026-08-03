# status: unverified
# source: https://github.com/ros2/ros2_documentation/blob/rolling/source/How-To-Guides/Launch-file-different-formats.rst
#         (Python launch file: DeclareLaunchArgument, LaunchConfiguration,
#         Node action with parameters/remappings). Fetched via ctx7 this
#         session; docs.ros.org was blocked by an anti-bot page for direct
#         fetch; re-verify there when reachable.
#
# Launches this package's `talker` executable (the console_scripts entry
# point in ../setup.py, which resolves to ros2_example_pkg.talker_node:main).
# Demonstrates a launch argument feeding a declared node parameter, and a
# topic remap: the "write a launch file" and "parameterize a node" usage
# patterns in ../../../SKILL.md. Run with:
#   ros2 launch ros2_example_pkg talker.launch.py message:="hi from launch"

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    message_arg = DeclareLaunchArgument(
        'message',
        default_value='hello from ros2_example_pkg',
        description='Text published on the chatter topic.',
    )

    talker_node = Node(
        package='ros2_example_pkg',
        executable='talker',
        name='example_talker',
        output='screen',
        parameters=[{'message': LaunchConfiguration('message')}],
        remappings=[('chatter', 'example_chatter')],
    )

    return LaunchDescription([message_arg, talker_node])
