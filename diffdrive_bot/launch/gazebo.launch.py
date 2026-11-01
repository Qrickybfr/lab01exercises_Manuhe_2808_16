"""
Run the lab robot in Gazebo: start the world, spawn the robot from its URDF, bridge its
topics to ROS 2, and show the model, TF tree, lidar scan and camera image in RViz.

The Gazebo server starts first and the robot is spawned once the server is up. The Gazebo
window opens after the robot is spawned: a window still loading its world misses the models
created meanwhile, while one that starts later receives the whole scene.

Usage:
    ros2 launch diffdrive_bot gazebo.launch.py
    ros2 run teleop_twist_keyboard teleop_twist_keyboard
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, RegisterEventHandler, Shutdown, TimerAction
from launch.event_handlers import OnProcessExit
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

# Time the Gazebo server needs to load the world before it answers a spawn request
SPAWN_DELAY_S = 2.0


def generate_launch_description():
    pkg_share = get_package_share_directory("diffdrive_bot")

    robot_description = ParameterValue(
        Command(["xacro ", os.path.join(pkg_share, "urdf", "diffdrive_bot.urdf.xacro")]),
        value_type=str,
    )

    # gz itself, not through a shell, so that stopping the launch reaches the server
    gazebo_server = ExecuteProcess(
        cmd=["gz", "sim", "-s", "-r", os.path.join(pkg_share, "worlds", "obstacles.sdf")],
        name="gazebo_server",
        output="screen",
        on_exit=Shutdown(),
    )

    # closing the window ends the launch
    gazebo_gui = ExecuteProcess(
        cmd=["gz", "sim", "-g"],
        name="gazebo_gui",
        output="screen",
        on_exit=Shutdown(),
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[{"robot_description": robot_description, "use_sim_time": True}],
        output="screen",
    )

    spawn = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=["-world", "obstacles", "-topic", "robot_description", "-name", "diffdrive_bot", "-z", "0.05"],
        output="screen",
    )

    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        parameters=[{"config_file": os.path.join(pkg_share, "config", "bridge.yaml")}],
        output="screen",
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", os.path.join(pkg_share, "rviz", "diffdrive_bot.rviz"), "-f", "odom"],
        parameters=[{"use_sim_time": True}],
        output="screen",
    )

    return LaunchDescription([
        gazebo_server,
        robot_state_publisher,
        TimerAction(period=SPAWN_DELAY_S, actions=[spawn]),
        RegisterEventHandler(OnProcessExit(target_action=spawn, on_exit=[gazebo_gui])),
        bridge,
        rviz,
    ])
