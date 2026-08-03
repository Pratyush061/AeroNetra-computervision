#!/usr/bin/env bash
# scripts/build_offboard_package.sh
# Run this script to build the workspace.

PX4_ROS2_WS=${PX4_ROS2_WS:-$HOME/px4_ros2_ws}

if [ ! -d "$PX4_ROS2_WS" ]; then
    echo "Error: ROS 2 workspace not found at $PX4_ROS2_WS"
    exit 1
fi

echo "Building ROS 2 workspace at $PX4_ROS2_WS..."
cd "$PX4_ROS2_WS"
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
echo "Build complete. Remember to source install/setup.bash before running nodes."
