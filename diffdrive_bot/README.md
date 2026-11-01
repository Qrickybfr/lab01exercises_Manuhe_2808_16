**Program:** BSc in Software Engineering

**Course:** Introduction to Robotics and Intelligent Systems

**Lecturer:** Mohammed Sraj (MSc AI)

**Lab Assistant:** Mohammed Sraj (MSc AI)

**Academic year:** 2026

# diffdrive_bot: ROS 2 and Gazebo Lab

This is the second part of [Lab 1](../README.md). It shows the ROS 2 ideas from the turtlesim
tutorials again, this time on a complete, working robot in the Gazebo simulator.

diffdrive_bot is a small two-wheeled robot with a lidar and a camera. In this lab you build it, look at
its model in RViz, and drive it around a simulated room in Gazebo. Then Python nodes drive it for you.
The nodes talk to each other with a message, a service and an action, which are defined in the
[lab_interfaces](../lab_interfaces) package next to this one.

The whole robot is described in one file, [urdf/diffdrive_bot.urdf.xacro](urdf/diffdrive_bot.urdf.xacro).
RViz and Gazebo both read this file, so a change you make there shows up in both.

## What you need

- Ubuntu 22.04 with ROS 2 Humble installed (the `ros-humble-desktop` package).
- Gazebo Harmonic and the ROS 2 packages that connect it to Humble. They come from the Gazebo apt
  repository, not the ROS one, so add that repository first:

```bash
sudo curl https://packages.osrfoundation.org/gazebo.gpg --output /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null
sudo apt update
sudo apt install ros-humble-ros-gzharmonic ros-humble-xacro ros-humble-joint-state-publisher-gui ros-humble-teleop-twist-keyboard
```

Install these packages with apt as shown rather than with `rosdep install`. rosdep would also install
the `ros-humble-ros-gz` packages, which are built for an older Gazebo and conflict with the Harmonic ones.

## Step 1: Build the packages

The `lab_01` folder of the repository holds two packages, diffdrive_bot and lab_interfaces. Create a
workspace, clone the repository into its `src` folder, and build:

```bash
source /opt/ros/humble/setup.bash
mkdir -p ~/ros2_ws/src && cd ~/ros2_ws/src
git clone https://github.com/berito/intro_robotics_intelligent_systems_labs.git
cd ~/ros2_ws
colcon build --symlink-install --packages-up-to diffdrive_bot
source install/setup.bash
```

`--packages-up-to` builds diffdrive_bot and the packages it depends on, here lab_interfaces.

`--symlink-install` links the installed files back to your source folder, so when you edit the URDF
or the world later you only need to restart the launch file, not rebuild.

Every new terminal you open needs both `source` lines before ROS 2 can find the package:

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
```

## Step 2: View the model in RViz

```bash
ros2 launch diffdrive_bot display.launch.py
```

Two windows open. RViz shows the grey chassis, two black wheels, the blue lidar on top and the blue
camera on the front, with the coordinate frame of each part drawn on it. The small Joint State
Publisher window has a slider for each wheel: move one and that wheel's frame turns in RViz.

robot_state_publisher reads the URDF and publishes where each part sits relative to the others (the TF
tree). The sliders only spin the wheels on screen. Nothing is simulated yet, so the robot cannot move.

Close both windows, or press Ctrl+C in the terminal, before going on.

## Step 3: Simulate it in Gazebo

```bash
ros2 launch diffdrive_bot gazebo.launch.py
```

Gazebo opens the world in [worlds/obstacles.sdf](worlds/obstacles.sdf): a red box in front of the
robot, a green cylinder to its left and a wall behind it. The robot appears in the middle, and the blue
lidar rays fan out from it. RViz opens as well, now showing the lidar scan as points on the obstacles
and the camera image in a panel on the left.

The launch file also starts a bridge, configured in [config/bridge.yaml](config/bridge.yaml), that
copies the robot's topics between Gazebo and ROS 2. Without it, ROS 2 would not see any of the sensor
data.

## Step 4: Drive the robot

Leave the simulation running. Open a second terminal, run the two `source` lines from Step 1, then:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Keep this terminal selected while you type, otherwise the keys go to another window:

| Key | Action |
|-----|--------|
| `i` | forward |
| `,` | backward |
| `j` / `l` | turn left / right |
| `k` | stop |
| `q` / `z` | faster / slower |

Drive towards the red box and watch its points move closer in the RViz scan and grow larger in the
camera image.

## Step 5: Look at the data

In a third terminal (sourced as before), you can inspect what the robot publishes:

```bash
ros2 topic list                  # every topic in the table below should be there
ros2 topic echo /odom --once     # where the robot thinks it is
ros2 topic hz /scan              # should be about 10 Hz
ros2 run tf2_tools view_frames   # writes frames.pdf showing the TF tree
ros2 run tf2_ros tf2_echo odom base_link   # the live transform between two frames
```

In RViz, the TF display draws the same frames on the model; while you drive, the `base_footprint`
frame moves away from `odom`.

## Step 6: Start the simulation with the nodes

So far you have driven the robot by hand. In the remaining steps the package's own Python nodes drive
it, and they talk to each other and to you in the three ways ROS 2 offers: a topic (a stream of
messages), a service (a request that gets one reply) and an action (a longer task that reports
progress while it runs and a result at the end).

Stop everything from the earlier steps with Ctrl+C in each terminal, then start the simulation
together with the nodes:

```bash
ros2 launch diffdrive_bot control.launch.py
```

Besides Gazebo, the bridge and RViz, this starts three nodes:

| Node | What it does |
|------|--------------|
| `obstacle_detector.py` | reads `/scan` and publishes the nearest obstacle in front of the robot on the `/obstacle` topic |
| `drive_controller.py` | drives the robot forward on `/cmd_vel` while it is switched on through the `/drive_enable` service, and stops it in front of an obstacle |
| `drive_distance_server.py` | serves the `/drive_distance` action: drives forward for a given distance, measured with `/odom`, and gives up in front of an obstacle |

Open a second terminal and source it as in Step 1. You type the commands of the next steps there.

## Step 7: Watch the obstacle topic

```bash
ros2 topic echo /obstacle --once
```

This prints one `ObstacleInfo` message, a message type defined in lab_interfaces. The robot starts facing the
red box, so `distance` is about 1.75 m and `too_close` is `false`. Leave out `--once` to see the
message update ten times a second, and press Ctrl+C to stop.

## Step 8: Drive with the service

Switch the drive controller on:

```bash
ros2 service call /drive_enable std_srvs/srv/SetBool "{data: true}"
```

The reply is `success=True, message='driving'`, and the robot drives towards the red box. About four
seconds later it stops by itself, and the launch terminal shows `Obstacle at 0.48 m, stopping`: the
obstacle detector reported `too_close`, and the controller reacted.

Call the service again with `true`. This time the reply is `success=False, message='obstacle ahead,
not starting'`, because the box is still in the way. `{data: false}` switches the controller off at
any time.

## Step 9: Drive a set distance with the action

The robot is now stuck in front of the box, so restart it: press Ctrl+C in the launch terminal and run
`ros2 launch diffdrive_bot control.launch.py` again. Then, in the second terminal, ask the action server
to drive 1 m:

```bash
ros2 run diffdrive_bot drive_distance_client.py 1.0
```

The client prints the feedback, `Travelled 0.03 m`, `Travelled 0.06 m` and so on, then
`Goal reached, travelled 1.02 m` (the last figure varies a little). Send the same goal again. The box is now only 0.75 m ahead, so the
server gives up when the robot gets within 0.5 m of it, and the client prints
`Goal aborted, travelled 0.24 m`.

You can send the same goal without the client node, straight from the command line:

```bash
ros2 action send_goal --feedback /drive_distance lab_interfaces/action/DriveDistance "{distance: 1.0}"
```

## Step 10: Change the parameters

The forward speed and the stopping distance are launch arguments, which the launch file passes on to
the nodes as parameters. Restart the launch with different values and repeat Step 8 to see the robot
drive more slowly and stop further from the box:

```bash
ros2 launch diffdrive_bot control.launch.py speed:=0.2 stop_distance:=0.8
```

## Step 11: Set the speed with a service

`drive_controller.py` offers a second service, `/set_speed`, with a service type of its own,
`SetSpeed` from lab_interfaces. Its request is a speed, and its reply says whether the speed was
accepted:

```bash
ros2 service call /set_speed lab_interfaces/srv/SetSpeed "{speed: 0.5}"
```

The reply is `success=True, message='speed set to 0.50 m/s'`. The controller stores the speed as its
`speed` parameter, so `ros2 param get /drive_controller speed` now shows 0.5, and the next
`/drive_enable` call drives at that speed. A speed of zero or less, or above the `max_speed`
parameter (1.0 m/s), is rejected with `success=False`.

You have now used every part of the package. The [exercise](../EXERCISE.md) asks you to write your
own nodes for the robot.

## Reference

### Robot parts

| Part | Shape | Size |
|------|-------|------|
| Chassis | box | 0.40 x 0.30 x 0.10 m, 5 kg |
| Driven wheels | 2 cylinders | radius 0.08 m, 0.34 m apart |
| Caster | sphere at the rear | radius 0.04 m, frictionless |
| Lidar | cylinder on top | 360 samples, 0.12 to 10 m, 10 Hz |
| Camera | box on the front | 640 x 480, 60 degree field of view, 15 Hz |

### Interfaces

The nodes use one message, one service and one action, all defined in the lab_interfaces package.

[msg/ObstacleInfo.msg](../lab_interfaces/msg/ObstacleInfo.msg) is the nearest obstacle in front of the robot:

```
std_msgs/Header header
float32 distance  # m, inf when nothing is in range
float32 angle     # rad, 0 straight ahead, positive to the left
bool too_close    # distance is below the stop distance
```

[srv/SetSpeed.srv](../lab_interfaces/srv/SetSpeed.srv) sets the forward speed:

```
float32 speed     # request, m/s
---
bool success
string message
```

[action/DriveDistance.action](../lab_interfaces/action/DriveDistance.action) drives straight forward for a distance:

```
float32 distance    # goal, m
---
float32 travelled   # result, m
bool reached
---
float32 travelled   # feedback, m
```

### Parameters

| Node | Parameter | Default | Meaning |
|------|-----------|---------|---------|
| `obstacle_detector.py` | `front_angle` | 0.35 | half-width of the sector in front of the robot that is checked, rad |
| `obstacle_detector.py` | `stop_distance` | 0.5 | obstacles closer than this, in m, are `too_close` |
| `drive_controller.py` | `speed` | 0.3 | forward speed, m/s |
| `drive_controller.py` | `max_speed` | 1.0 | highest speed `/set_speed` accepts, m/s |
| `drive_distance_server.py` | `speed` | 0.3 | forward speed, m/s |
| `drive_distance_server.py` | `heading_gain` | 1.0 | turning speed per radian of heading error, 1/s; keeps the robot on its starting heading |

### Topics

| Topic | Type | Direction |
|-------|------|-----------|
| `/cmd_vel` | `geometry_msgs/msg/Twist` | ROS 2 to Gazebo |
| `/odom` | `nav_msgs/msg/Odometry` | Gazebo to ROS 2 |
| `/tf` | `tf2_msgs/msg/TFMessage` | Gazebo to ROS 2 (`odom` to `base_footprint`) |
| `/joint_states` | `sensor_msgs/msg/JointState` | Gazebo to ROS 2 |
| `/scan` | `sensor_msgs/msg/LaserScan` | Gazebo to ROS 2 |
| `/camera/image` | `sensor_msgs/msg/Image` | Gazebo to ROS 2 |
| `/camera/camera_info` | `sensor_msgs/msg/CameraInfo` | Gazebo to ROS 2 |
| `/clock` | `rosgraph_msgs/msg/Clock` | Gazebo to ROS 2 |
| `/obstacle` | `lab_interfaces/msg/ObstacleInfo` | published by `obstacle_detector.py` |

| Service | Type |
|---------|------|
| `/drive_enable` | `std_srvs/srv/SetBool` |
| `/set_speed` | `lab_interfaces/srv/SetSpeed` |

| Action | Type |
|--------|------|
| `/drive_distance` | `lab_interfaces/action/DriveDistance` |

### Frames

```
odom -> base_footprint -> base_link -> left_wheel, right_wheel, caster, lidar_link, camera_link
```

### Files

| File | What it contains |
|------|------------------|
| [urdf/diffdrive_bot.urdf.xacro](urdf/diffdrive_bot.urdf.xacro) | The robot: its parts, joints, sensors and Gazebo plugins |
| [launch/display.launch.py](launch/display.launch.py) | Starts RViz with the model only (Step 2) |
| [launch/gazebo.launch.py](launch/gazebo.launch.py) | Starts Gazebo, the bridge and RViz (Step 3) |
| [launch/control.launch.py](launch/control.launch.py) | Starts the simulation and the nodes (Steps 6 to 11) |
| [scripts/](scripts/) | The Python nodes and the action client |
| [config/bridge.yaml](config/bridge.yaml) | Which topics are copied between Gazebo and ROS 2 |
| [worlds/obstacles.sdf](worlds/obstacles.sdf) | The simulated room and its obstacles |
| [rviz/diffdrive_bot.rviz](rviz/diffdrive_bot.rviz) | The RViz layout used by both launch files |

## Troubleshooting

**`Package 'diffdrive_bot' not found`.** The terminal has not been sourced. Run the two `source` lines
from Step 1.

**The build ends with `1 package had stderr output`.** If the output above it shows only CMake
warnings, not errors, the package was built and you can carry on. Newer CMake versions print these
warnings for the message generator that comes with ROS 2 Humble.

**The robot does not move when you press keys.** Click on the teleop terminal so it has focus, then
check that `ros2 topic echo /cmd_vel` shows messages while you press `i`.

**RViz shows "No transform" or an empty scan.** Gazebo may still be loading; wait a few seconds. If it
stays like that, check that the simulation is running (the play button in the bottom left of Gazebo).

**`Goal rejected` from the action client.** The server rejects a distance of zero or less, and any
goal sent before the robot's odometry has arrived. Wait until the simulation is fully loaded and try
again.

**`ros2 topic echo /obstacle` says the topic is not published, or the type cannot be found.** Check
that `control.launch.py` is running and that this terminal is sourced. If it still fails, run
`ros2 daemon stop` and try again.

**Gazebo will not start again, or two robots appear.** A previous run is still alive in the
background. Stop it with `pkill -f "gz sim"` and launch again.

**Your change to the URDF does not show up.** Restart the launch file. If you built without
`--symlink-install`, run `colcon build --packages-up-to diffdrive_bot` again first.

