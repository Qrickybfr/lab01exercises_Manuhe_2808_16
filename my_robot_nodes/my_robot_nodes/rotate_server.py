import math
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from rclpy.node import Node

from my_robot_interfaces.action import Rotate


def yaw_from_quaternion(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))


def angle_difference(target, current):
    # target - current, wrapped to [-pi, pi]
    return math.atan2(math.sin(target - current), math.cos(target - current))


class RotateServer(Node):
    def __init__(self):
        super().__init__("rotate_server")
        self.declare_parameter("turn_speed", 0.5)

        self.last_yaw = None
        # Sum of the small yaw changes between odometry messages. It never
        # jumps from pi to -pi, so turned angle = total now - total at start.
        self.total_turned = 0.0

        group = ReentrantCallbackGroup()
        self.pub = self.create_publisher(Twist, "cmd_vel", 10)
        self.create_subscription(Odometry, "odom", self.on_odom, 10, callback_group=group)
        self.action_server = ActionServer(
            self,
            Rotate,
            "rotate",
            execute_callback=self.execute,
            goal_callback=self.on_goal,
            cancel_callback=lambda goal_handle: CancelResponse.ACCEPT,
            callback_group=group,
        )

    def on_odom(self, msg):
        yaw = yaw_from_quaternion(msg.pose.pose.orientation)
        if self.last_yaw is not None:
            self.total_turned += angle_difference(yaw, self.last_yaw)
        self.last_yaw = yaw

    def on_goal(self, goal):
        if goal.angle == 0.0 or self.last_yaw is None:
            return GoalResponse.REJECT
        return GoalResponse.ACCEPT

    def execute(self, goal_handle):
        goal = goal_handle.request.angle
        start = self.total_turned
        direction = 1.0 if goal > 0.0 else -1.0
        turn_speed = self.get_parameter("turn_speed").value
        self.get_logger().info(f"Rotating {goal:.2f} rad")

        twist = Twist()
        twist.angular.z = direction * turn_speed
        feedback = Rotate.Feedback()
        result = Rotate.Result()

        while rclpy.ok():
            turned = self.total_turned - start
            result.turned = float(turned)

            if goal_handle.is_cancel_requested:
                self.pub.publish(Twist())
                goal_handle.canceled()
                self.get_logger().info(f"Canceled after {turned:.2f} rad")
                return result

            if abs(turned) >= abs(goal):
                break

            self.pub.publish(twist)
            feedback.turned = float(turned)
            goal_handle.publish_feedback(feedback)
            time.sleep(0.05)

        self.pub.publish(Twist())
        result.turned = float(self.total_turned - start)
        goal_handle.succeed()
        self.get_logger().info(f"Done, turned {result.turned:.2f} rad")
        return result


def main():
    rclpy.init()
    node = RotateServer()
    try:
        rclpy.spin(node, executor=MultiThreadedExecutor())
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == "__main__":
    main()