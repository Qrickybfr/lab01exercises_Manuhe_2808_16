#!/usr/bin/env python3
"""Publish the nearest obstacle in front of the robot, found in the lidar scan."""

import math

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import LaserScan

from lab_interfaces.msg import ObstacleInfo


class ObstacleDetector(Node):

    def __init__(self):
        super().__init__("obstacle_detector")
        # Half-width of the sector in front of the robot that is checked, in rad
        self.declare_parameter("front_angle", 0.35)
        self.declare_parameter("stop_distance", 0.5)

        self.publisher = self.create_publisher(ObstacleInfo, "obstacle", 10)
        self.create_subscription(LaserScan, "scan", self.on_scan, 10)

    def on_scan(self, scan):
        front_angle = self.get_parameter("front_angle").value
        stop_distance = self.get_parameter("stop_distance").value

        nearest_distance = math.inf
        nearest_angle = 0.0
        for i, distance in enumerate(scan.ranges):
            angle = scan.angle_min + i * scan.angle_increment
            if abs(angle) > front_angle:
                continue
            # Readings outside the sensor's range are no return, not an obstacle
            if not scan.range_min <= distance <= scan.range_max:
                continue
            if distance < nearest_distance:
                nearest_distance = distance
                nearest_angle = angle

        msg = ObstacleInfo()
        msg.header = scan.header
        msg.distance = nearest_distance
        msg.angle = nearest_angle
        msg.too_close = nearest_distance < stop_distance
        self.publisher.publish(msg)


def main():
    rclpy.init()
    node = ObstacleDetector()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == "__main__":
    main()
