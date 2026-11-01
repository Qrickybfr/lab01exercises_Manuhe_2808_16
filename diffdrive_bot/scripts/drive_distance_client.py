#!/usr/bin/env python3
"""Send a drive_distance goal and print its feedback and result.

Usage:
    ros2 run diffdrive_bot drive_distance_client.py <distance in m>
"""

import sys

import rclpy
from action_msgs.msg import GoalStatus
from rclpy.action import ActionClient
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from lab_interfaces.action import DriveDistance


class DriveDistanceClient(Node):

    def __init__(self):
        super().__init__("drive_distance_client")
        self.client = ActionClient(self, DriveDistance, "drive_distance")

    def send(self, distance):
        self.client.wait_for_server()
        goal = DriveDistance.Goal()
        goal.distance = distance
        return self.client.send_goal_async(goal, feedback_callback=self.on_feedback)

    def on_feedback(self, msg):
        self.get_logger().info(f"Travelled {msg.feedback.travelled:.2f} m")


def main():
    args = rclpy.utilities.remove_ros_args(sys.argv)
    if len(args) != 2:
        print(__doc__)
        return

    rclpy.init()
    node = DriveDistanceClient()
    try:
        send_future = node.send(float(args[1]))
        rclpy.spin_until_future_complete(node, send_future)
        goal_handle = send_future.result()
        if not goal_handle.accepted:
            node.get_logger().info("Goal rejected")
        else:
            result_future = goal_handle.get_result_async()
            rclpy.spin_until_future_complete(node, result_future)
            status = result_future.result().status
            result = result_future.result().result
            outcome = {
                GoalStatus.STATUS_SUCCEEDED: "reached",
                GoalStatus.STATUS_ABORTED: "aborted",
                GoalStatus.STATUS_CANCELED: "canceled",
            }.get(status, "ended")
            node.get_logger().info(f"Goal {outcome}, travelled {result.travelled:.2f} m")
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == "__main__":
    main()
