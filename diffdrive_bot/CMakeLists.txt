cmake_minimum_required(VERSION 3.10)
project(diffdrive_bot)

find_package(ament_cmake REQUIRED)

install(PROGRAMS
  scripts/obstacle_detector.py
  scripts/drive_controller.py
  scripts/drive_distance_server.py
  scripts/drive_distance_client.py
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  config
  launch
  rviz
  urdf
  worlds
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
