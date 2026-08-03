#!/usr/bin/env python3
# status: unverified
# source: https://raw.githubusercontent.com/ros-navigation/navigation2/jazzy/nav2_bringup/launch/bringup_launch.py
#         fetched directly via `curl` of the raw GitHub file (jazzy branch)
#         this session — the launch-argument names and defaults below
#         (namespace, slam, map, use_sim_time, params_file, autostart,
#         use_composition, use_respawn, log_level, use_localization) mirror
#         that file's DeclareLaunchArgument calls.
#
# Rather than reimplementing bringup_launch.py's internals (GroupAction /
# PushROSNamespace / RewrittenYaml param-file rewriting for namespacing),
# this project launch file includes nav2_bringup's own bringup_launch.py and
# just points it at this skill's example params file. That keeps this
# snippet honest about what it does and lets nav2_bringup's own
# (independently-versioned) logic stay authoritative.
#
# Pairs with ../examples/nav2-params-diffdrive.yaml: same frame names
# (map/odom/base_link) and the same use_sim_time value must be used by every
# other node in the system (robot_state_publisher, the sim, any odometry
# source) — see the "use_sim_time must be consistent" key directive in
# ../SKILL.md.
#
# Run against an existing map (see the "bringup with an existing map" usage
# pattern in ../SKILL.md):
#   ros2 launch ./bringup-launch-snippet.py map:=/path/to/your_map.yaml
#
# Run with SLAM instead (see the "SLAM-then-navigate" usage pattern; launch
# slam_toolbox's online_async_launch.py alongside this, separately):
#   ros2 launch ./bringup-launch-snippet.py slam:=true

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node  # noqa: F401  (kept for extension: add sensor/robot_state_publisher nodes here)


def generate_launch_description():
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    this_dir = os.path.dirname(os.path.abspath(__file__))

    map_yaml_file = LaunchConfiguration('map')
    params_file = LaunchConfiguration('params_file')
    use_sim_time = LaunchConfiguration('use_sim_time')
    slam = LaunchConfiguration('slam')
    autostart = LaunchConfiguration('autostart')

    declare_map_cmd = DeclareLaunchArgument(
        'map',
        default_value='',
        description=(
            "Full path to a saved map YAML file. Unused when slam:=true — "
            "leave empty in that case."
        ),
    )
    declare_params_file_cmd = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(this_dir, 'nav2-params-diffdrive.yaml'),
        description=(
            "Full path to the Nav2 params file for all launched nodes. Keep "
            "in sync with the actual filename of "
            "examples/nav2-params-diffdrive.yaml if either is renamed."
        ),
    )
    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description=(
            "Use simulation (Gazebo) clock if true. Must match every other "
            "node in the system, not just Nav2's own nodes — see SKILL.md's "
            "use_sim_time key directive."
        ),
    )
    declare_slam_cmd = DeclareLaunchArgument(
        'slam',
        default_value='False',
        description=(
            "Run slam_toolbox instead of nav2_map_server + nav2_amcl. "
            "Launch slam_toolbox's online_async_launch.py separately when "
            "this is true — it is not included by this file."
        ),
    )
    declare_autostart_cmd = DeclareLaunchArgument(
        'autostart',
        default_value='true',
        description='Automatically bring every lifecycle-managed node to active.',
    )

    bringup_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')
        ),
        launch_arguments={
            'map': map_yaml_file,
            'params_file': params_file,
            'use_sim_time': use_sim_time,
            'slam': slam,
            'autostart': autostart,
        }.items(),
    )

    return LaunchDescription([
        declare_map_cmd,
        declare_params_file_cmd,
        declare_use_sim_time_cmd,
        declare_slam_cmd,
        declare_autostart_cmd,
        bringup_cmd,
    ])
