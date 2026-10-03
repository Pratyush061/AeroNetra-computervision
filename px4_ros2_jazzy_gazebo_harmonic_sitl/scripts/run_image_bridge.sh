#!/usr/bin/env bash
# scripts/run_image_bridge.sh  (Terminal 2)
# Bridge the Gazebo camera topic into ROS 2 with ros_gz_image.
set -euo pipefail

ROS_DISTRO_NAME="${ROS_DISTRO_NAME:-jazzy}"
# shellcheck disable=SC1090
source "/opt/ros/$ROS_DISTRO_NAME/setup.bash"

GZ_IMAGE_TOPIC="${GZ_IMAGE_TOPIC:-$(gz topic -l 2>/dev/null | grep '/IMX214/image$' | head -n 1)}"
if [ -z "${GZ_IMAGE_TOPIC:-}" ]; then
    echo "Error: no Gazebo camera topic found."
    echo "Is 'make px4_sitl gz_x500_depth' running? Try: gz topic -l | grep IMX214"
    exit 1
fi

echo "Gazebo camera topic: $GZ_IMAGE_TOPIC"
gz topic -i -t "$GZ_IMAGE_TOPIC"
echo "Starting image bridge (leave this terminal running)..."
exec ros2 run ros_gz_image image_bridge "$GZ_IMAGE_TOPIC"
