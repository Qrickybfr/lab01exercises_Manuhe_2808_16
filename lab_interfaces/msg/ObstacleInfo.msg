# Nearest obstacle in front of the robot, from the lidar scan
std_msgs/Header header
float32 distance  # m, inf when nothing is in range
float32 angle     # rad, 0 straight ahead, positive to the left
bool too_close    # distance is below the stop distance
