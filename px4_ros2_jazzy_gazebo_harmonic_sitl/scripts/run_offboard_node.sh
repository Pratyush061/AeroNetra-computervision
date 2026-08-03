#!/usr/bin/env bash
# scripts/run_offboard_node.sh
# Run this script in Terminal 4 to start the offboard control node.

PX4_ROS2_WS=${PX4_ROS2_WS:-$HOME/px4_ros2_ws}

if [ ! -d "$PX4_ROS2_WS" ]; then
    echo "Error: ROS 2 workspace not found at $PX4_ROS2_WS"
    exit 1
fi

echo "Sourcing ROS 2 and workspace..."
cd "$PX4_ROS2_WS"
source /opt/ros/jazzy/setup.bash
if [ -f "install/setup.bash" ]; then
    source install/setup.bash
else
    echo "Error: install/setup.bash not found. Please build the workspace first."
    exit 1
fi

echo "Starting px4_offboard_py node..."
ros2 run px4_offboard_py offboard_control
