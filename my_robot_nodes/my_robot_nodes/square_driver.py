import math
import time

import rclpy
from action_msgs.msg import GoalStatus
from nav_msgs.msg import Odometry
from rclpy.action import ActionClient
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from lab_interfaces.action import DriveDistance
from my_robot_interfaces.action import Rotate


class SquareDriver(Node):
    def __init__(self):
        super().__init__("square_driver")
        self.declare_parameter("side_length", 0.5)

        self.drive_client = ActionClient(self, DriveDistance, "drive_distance")
        self.rotate_client = ActionClient(self, Rotate, "rotate")

        self.got_odom = False
        self.create_subscription(Odometry, "odom", self.on_odom, 10)

    def on_odom(self, msg):
        self.got_odom = True

    def wait_ready(self):
        self.get_logger().info("Waiting for the action servers and odometry")
        self.drive_client.wait_for_server()
        self.rotate_client.wait_for_server()
        while rclpy.ok() and not self.got_odom:
            rclpy.spin_once(self, timeout_sec=0.1)

    def run_goal(self, client, goal):
        # Send one goal, wait for its result, return True if it succeeded.
        # A server rejects goals until it has odometry, so try a few times.
        for _ in range(5):
            send_future = client.send_goal_async(goal)
            rclpy.spin_until_future_complete(self, send_future)
            goal_handle = send_future.result()
            if goal_handle.accepted:
                break
            time.sleep(1.0)
        else:
            return False

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)
        return result_future.result().status == GoalStatus.STATUS_SUCCEEDED

    def drive_square(self):
        side_length = self.get_parameter("side_length").value
        self.wait_ready()

        for side in range(1, 5):
            drive_goal = DriveDistance.Goal()
            drive_goal.distance = float(side_length)
            self.get_logger().info(f"Side {side}: driving {side_length:.2f} m")
            if not self.run_goal(self.drive_client, drive_goal):
                self.get_logger().error(f"Driving side {side} did not succeed, stopping")
                return

            rotate_goal = Rotate.Goal()
            rotate_goal.angle = math.pi / 2
            self.get_logger().info(f"Side {side}: turning a quarter turn left")
            if not self.run_goal(self.rotate_client, rotate_goal):
                self.get_logger().error(f"Turning after side {side} did not succeed, stopping")
                return

        self.get_logger().info("Square finished")


def main():
    rclpy.init()
    node = SquareDriver()
    try:
        node.drive_square()
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == "__main__":
    main()