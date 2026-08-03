#!/usr/bin/env bash
# scripts/run_px4_gazebo.sh
# Run this script in Terminal 1.

PX4_DIR=${PX4_DIR:-$HOME/PX4-Autopilot}

if [ ! -d "$PX4_DIR" ]; then
    echo "Error: PX4 directory not found at $PX4_DIR"
    exit 1
fi

echo "Starting PX4 SITL with Gazebo Harmonic..."
cd "$PX4_DIR"
make px4_sitl gz_x500
