#!/usr/bin/env bash
# scripts/run_px4_gazebo.sh  (Terminal 1)
# Start PX4 SITL with Gazebo. Defaults to gz_x500_depth, the camera-equipped
# vehicle used by the computer-vision pipeline (forward depth + IMX214 RGB camera).
set -euo pipefail

PX4_DIR="${PX4_DIR:-$HOME/PX4-Autopilot}"
PX4_GZ_MODEL="${PX4_GZ_MODEL:-gz_x500_depth}"

if [ ! -d "$PX4_DIR" ]; then
    echo "Error: PX4 directory not found at $PX4_DIR"
    exit 1
fi

# Clean up any leftover simulation processes from a previous run.
pkill -TERM -f "$PX4_DIR/build/px4_sitl_default/bin/px4" 2>/dev/null || true
pkill -TERM -f "gz sim" 2>/dev/null || true
pkill -TERM -f "gz-sim-server" 2>/dev/null || true
pkill -TERM -f "gz-sim-gui" 2>/dev/null || true
sleep 3

echo "Starting PX4 SITL ($PX4_GZ_MODEL) with Gazebo..."
cd "$PX4_DIR"
exec make px4_sitl "$PX4_GZ_MODEL"
