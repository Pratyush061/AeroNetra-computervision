#!/usr/bin/env bash
# scripts/run_cv_viewer.sh  (Terminal 4)
# View the annotated detector output (/vision/annotated) in rqt_image_view.
set -euo pipefail

ROS_DISTRO_NAME="${ROS_DISTRO_NAME:-jazzy}"
# shellcheck disable=SC1090
source "/opt/ros/$ROS_DISTRO_NAME/setup.bash"

echo "Vision topics currently published:"
ros2 topic list | grep vision || echo "  (none yet - is the detector running?)"

exec ros2 run rqt_image_view rqt_image_view /vision/annotated
