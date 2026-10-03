#!/usr/bin/env bash
# scripts/run_cv_detector.sh  (Terminal 3)
# Run the VisDrone YOLO detector on the bridged ROS 2 camera topic.
set -euo pipefail

PX4_ROS2_WS="${PX4_ROS2_WS:-$HOME/px4_ros2_ws}"
ROS_DISTRO_NAME="${ROS_DISTRO_NAME:-jazzy}"

# shellcheck disable=SC1090
source "/opt/ros/$ROS_DISTRO_NAME/setup.bash"
if [ -f "$PX4_ROS2_WS/yolo_venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "$PX4_ROS2_WS/yolo_venv/bin/activate"
fi

IMAGE_TOPIC="${IMAGE_TOPIC:-$(ros2 topic list 2>/dev/null | grep '/IMX214/image$' | head -n 1)}"
if [ -z "${IMAGE_TOPIC:-}" ]; then
    echo "Error: no ROS image topic found. Start scripts/run_image_bridge.sh first."
    exit 1
fi

export IMAGE_TOPIC
export YOLO_MODEL="${YOLO_MODEL:-$PX4_ROS2_WS/models/best.pt}"
export OUTPUT_TOPIC="${OUTPUT_TOPIC:-/vision/annotated}"
export YOLO_CONF="${YOLO_CONF:-0.15}"
export YOLO_IMGSZ="${YOLO_IMGSZ:-640}"
export YOLO_DEVICE="${YOLO_DEVICE:-cpu}"
export PROCESS_EVERY_N_FRAMES="${PROCESS_EVERY_N_FRAMES:-1}"

echo "Detector input : $IMAGE_TOPIC"
echo "Model          : $YOLO_MODEL"
echo "Output topic   : $OUTPUT_TOPIC"
exec python3 "$PX4_ROS2_WS/aeronetra_cv/yolo_car_detector.py"
