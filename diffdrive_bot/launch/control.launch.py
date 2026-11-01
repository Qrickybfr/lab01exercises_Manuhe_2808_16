"""
Run diffdrive_bot in Gazebo with its nodes: the obstacle detector, the drive controller
and the drive_distance action server.

Usage:
    ros2 launch diffdrive_bot control.launch.py speed:=0.3 stop_distance:=0.5
    ros2 service call /drive_enable std_srvs/srv/SetBool "{data: true}"
    ros2 run diffdrive_bot drive_distance_client.py 1.0
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_share = get_package_share_directory("diffdrive_bot")

    speed = ParameterValue(LaunchConfiguration("speed"), value_type=float)
    stop_distance = ParameterValue(LaunchConfiguration("stop_distance"), value_type=float)

    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_share, "launch", "gazebo.launch.py")),
    )

    obstacle_detector = Node(
        package="diffdrive_bot",
        executable="obstacle_detector.py",
        parameters=[{"stop_distance": stop_distance, "use_sim_time": True}],
        output="screen",
    )

    drive_controller = Node(
        package="diffdrive_bot",
        executable="drive_controller.py",
        parameters=[{"speed": speed, "use_sim_time": True}],
        output="screen",
    )

    drive_distance_server = Node(
        package="diffdrive_bot",
        executable="drive_distance_server.py",
        parameters=[{"speed": speed, "use_sim_time": True}],
        output="screen",
    )

    return LaunchDescription([
        DeclareLaunchArgument("speed", default_value="0.3", description="Forward speed in m/s"),
        DeclareLaunchArgument("stop_distance", default_value="0.5",
                              description="Distance to an obstacle at which the robot stops, in m"),
        simulation,
        obstacle_detector,
        drive_controller,
        drive_distance_server,
    ])
