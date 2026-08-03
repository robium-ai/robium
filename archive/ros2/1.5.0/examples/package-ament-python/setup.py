# status: unverified
# source: https://github.com/ros2/ros2_documentation/blob/rolling/source/Tutorials/Beginner-Client-Libraries/Creating-Your-First-ROS2-Package.rst
#         (ament_python setup.py shape) and
#         https://github.com/ros2/ros2_documentation/blob/rolling/source/Tutorials/Intermediate/Launch/Using-Substitutions.rst
#         (data_files pattern for installing a package's launch directory).
#         Fetched via ctx7 on 2026-07-10; docs.ros.org was blocked by an
#         anti-bot page for direct fetch — re-verify there when reachable.
#
# package_name must match package.xml's <name>, the resource/ marker file
# name, and the 'package=' argument in launch/talker.launch.py. The
# console_scripts entry point name ('talker') must match the 'executable='
# argument in that same launch file. See ../../SKILL.md's Customization
# section for what to keep in sync when renaming.

import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'ros2_example_pkg'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='robium',
    maintainer_email='robium@example.invalid',
    description='Minimal ament_python example package for the robium ros2 skill.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'talker = ros2_example_pkg.talker_node:main',
        ],
    },
)
