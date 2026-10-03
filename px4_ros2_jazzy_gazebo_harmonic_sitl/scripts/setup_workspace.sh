#!/usr/bin/env bash
# scripts/setup_workspace.sh
# Assemble ~/px4_ros2_ws from this repository, PX4/px4_msgs and the CV nodes, then build.
#
# Usage:
#   scripts/setup_workspace.sh                 # link packages, clone px4_msgs, colcon build
#   PX4_MSGS_BRANCH=release/1.16 scripts/setup_workspace.sh
#   INSTALL_CV=1 scripts/setup_workspace.sh    # also create the Ultralytics virtualenv
set -euo pipefail

REPO_SIM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PX4_ROS2_WS="${PX4_ROS2_WS:-$HOME/px4_ros2_ws}"
PX4_MSGS_BRANCH="${PX4_MSGS_BRANCH:-main}"   # match your PX4 release: release/1.15, release/1.16, ...
ROS_DISTRO_NAME="${ROS_DISTRO_NAME:-jazzy}"
INSTALL_CV="${INSTALL_CV:-0}"

echo "Repository simulation dir : $REPO_SIM_DIR"
echo "ROS 2 workspace           : $PX4_ROS2_WS"
echo "px4_msgs branch           : $PX4_MSGS_BRANCH"

mkdir -p "$PX4_ROS2_WS/src" "$PX4_ROS2_WS/aeronetra_cv" "$PX4_ROS2_WS/cv_demo" "$PX4_ROS2_WS/models"

# 1. Link the offboard package and the CV nodes into the workspace. Symlinks keep a
#    single source of truth in the repository, so edits are picked up on the next run.
ln -sfn "$REPO_SIM_DIR/ros2_ws/src/px4_offboard_py" "$PX4_ROS2_WS/src/px4_offboard_py"
ln -sfn "$REPO_SIM_DIR/cv_nodes/yolo_car_detector.py" "$PX4_ROS2_WS/aeronetra_cv/yolo_car_detector.py"
ln -sfn "$REPO_SIM_DIR/cv_nodes/simple_bbox.py"       "$PX4_ROS2_WS/cv_demo/simple_bbox.py"
ln -sfn "$REPO_SIM_DIR/cv_nodes/vision_tracking.py"   "$PX4_ROS2_WS/cv_demo/vision_tracking.py"
echo "Linked px4_offboard_py and the CV nodes into $PX4_ROS2_WS"

# 2. Clone px4_msgs (message definitions must match the PX4 firmware version).
if [ ! -d "$PX4_ROS2_WS/src/px4_msgs/.git" ]; then
    git clone --branch "$PX4_MSGS_BRANCH" --depth 1 \
        https://github.com/PX4/px4_msgs.git "$PX4_ROS2_WS/src/px4_msgs"
else
    echo "px4_msgs already present in $PX4_ROS2_WS/src"
fi

# 3. Build the workspace.
# shellcheck disable=SC1090
source "/opt/ros/$ROS_DISTRO_NAME/setup.bash"
cd "$PX4_ROS2_WS"
colcon build --symlink-install
echo "Build complete. Source $PX4_ROS2_WS/install/setup.bash before running nodes."

# 4. Optional: create the CV virtualenv used by the YOLO detector.
if [ "$INSTALL_CV" = "1" ]; then
    python3 -m venv --system-site-packages "$PX4_ROS2_WS/yolo_venv"
    # shellcheck disable=SC1091
    source "$PX4_ROS2_WS/yolo_venv/bin/activate"
    python3 -m pip install --upgrade pip
    python3 -m pip install -r "$REPO_SIM_DIR/requirements-cv.txt"
    deactivate
    echo "Ultralytics virtualenv ready at $PX4_ROS2_WS/yolo_venv"
fi

echo
echo "Next: copy your trained model to $PX4_ROS2_WS/models/best.pt"
