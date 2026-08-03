#!/usr/bin/env bash
# scripts/verify_topics.sh
# Run this script in Terminal 3 after building.

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
    echo "Warning: install/setup.bash not found. Did you build the workspace?"
fi

echo "----------------------------------------"
echo "Listing /fmu/ topics available:"
ros2 topic list | grep '^/fmu/' || echo "No /fmu/ topics found. Is PX4 and the MicroXRCEAgent running?"

echo "----------------------------------------"
echo "Echoing /fmu/out/vehicle_status (Ctrl+C to stop)..."
ros2 topic echo /fmu/out/vehicle_status
