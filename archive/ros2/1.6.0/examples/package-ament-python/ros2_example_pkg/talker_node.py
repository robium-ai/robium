# status: unverified
# source: https://github.com/ros2/ros2_documentation/blob/rolling/source/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Py-Publisher-And-Subscriber.rst
#         (rclpy Node/Publisher/Timer pattern, including the current
#         `with rclpy.init(): ...` + ExternalShutdownException idiom — this
#         reflects the `rolling` branch of ros2_documentation via ctx7, not a
#         distro-pinned page; re-confirm the idiom is current for whatever
#         distro is actually installed before relying on it) and
#         https://github.com/ros2/ros2_documentation/blob/rolling/source/Tutorials/Beginner-Client-Libraries/Using-Parameters-In-A-Class-Python.rst
#         (declare_parameter / get_parameter pattern).
#
# Minimal ament_python talker node for the ros2 skill's example package.
# Publishes a parameterized std_msgs/String on 'chatter' at 1 Hz. The class
# name and entry-point function name below are wired up in setup.py's
# console_scripts ('talker = ros2_example_pkg.talker_node:main') and
# referenced by package/executable in ../launch/talker.launch.py — keep all
# three in sync if renaming. Re-verify against current ros2_documentation
# before using in a real project.

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import String


class ExampleTalker(Node):
    """Minimal publisher node demonstrating a declared parameter and
    explicit QoS — see the "parameterize a node" usage pattern in
    ../../../SKILL.md.
    """

    def __init__(self):
        super().__init__('example_talker')

        self.declare_parameter('message', 'hello from ros2_example_pkg')

        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self.publisher_ = self.create_publisher(String, 'chatter', qos)
        self.timer_ = self.create_timer(1.0, self.on_timer)
        self.count_ = 0

    def on_timer(self):
        text = self.get_parameter('message').get_parameter_value().string_value
        msg = String()
        msg.data = f'{text} #{self.count_}'
        self.publisher_.publish(msg)
        self.get_logger().info(f'Publishing: "{msg.data}"')
        self.count_ += 1


def main(args=None):
    try:
        with rclpy.init(args=args):
            node = ExampleTalker()
            rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass


if __name__ == '__main__':
    main()
