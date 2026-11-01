#!/usr/bin/env python3
"""Drive the robot straight forward while enabled through a service, and stop it in
front of an obstacle. A second service sets the speed."""

import rclpy
from geometry_msgs.msg import Twist
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.parameter import Parameter
from std_srvs.srv import SetBool

from lab_interfaces.msg import ObstacleInfo
from lab_interfaces.srv import SetSpeed


class DriveController(Node):

    def __init__(self):
        super().__init__("drive_controller")
        self.declare_parameter("speed", 0.3)
        self.declare_parameter("max_speed", 1.0)

        self.enabled = False
        self.too_close = False

        self.cmd_vel = self.create_publisher(Twist, "cmd_vel", 10)
        self.create_subscription(ObstacleInfo, "obstacle", self.on_obstacle, 10)
        self.create_service(SetBool, "drive_enable", self.on_enable)
        self.create_service(SetSpeed, "set_speed", self.on_set_speed)
        self.create_timer(0.1, self.on_timer)

    def on_obstacle(self, msg):
        self.too_close = msg.too_close
        if self.enabled and self.too_close:
            self.get_logger().info(f"Obstacle at {msg.distance:.2f} m, stopping")
            self.stop()

    def on_enable(self, request, response):
        if request.data and self.too_close:
            response.success = False
            response.message = "obstacle ahead, not starting"
        elif request.data:
            self.enabled = True
            response.success = True
            response.message = "driving"
        else:
            self.stop()
            response.success = True
            response.message = "stopped"
        self.get_logger().info(response.message)
        return response

    def on_set_speed(self, request, response):
        max_speed = self.get_parameter("max_speed").value
        if not 0.0 < request.speed <= max_speed:
            response.success = False
            response.message = f"speed must be above 0 and at most {max_speed} m/s"
        else:
            # Stored as the parameter, so ros2 param get shows the speed in use
            self.set_parameters([Parameter("speed", value=float(request.speed))])
            response.success = True
            response.message = f"speed set to {request.speed:.2f} m/s"
        self.get_logger().info(response.message)
        return response

    def on_timer(self):
        # Publishes only while enabled, so other nodes can drive the robot when it is not
        if self.enabled:
            twist = Twist()
            twist.linear.x = self.get_parameter("speed").value
            self.cmd_vel.publish(twist)

    def stop(self):
        self.enabled = False
        self.cmd_vel.publish(Twist())


def main():
    rclpy.init()
    node = DriveController()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == "__main__":
    main()
