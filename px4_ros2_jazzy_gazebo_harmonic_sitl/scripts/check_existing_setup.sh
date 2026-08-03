#!/usr/bin/env bash
# scripts/check_existing_setup.sh
# Verifies the existing Ubuntu 24.04, ROS 2 Jazzy, Gazebo Harmonic, and PX4 environment.
# This script is read-only and does not install or modify anything.

echo "========================================"
echo "Checking Environment for PX4 SITL Setup"
echo "========================================"

# 1. Check Ubuntu Version
if grep -q "Ubuntu 24.04" /etc/os-release; then
    echo "[PASS] Ubuntu 24.04 found."
else
    echo "[WARN] Ubuntu 24.04 not detected. This guide assumes 24.04."
fi

# 2. Check ROS 2
if [ "$ROS_DISTRO" == "jazzy" ]; then
    echo "[PASS] ROS 2 Jazzy is sourced."
elif [ -d "/opt/ros/jazzy" ]; then
    echo "[WARN] ROS 2 Jazzy is installed but not sourced. Run: source /opt/ros/jazzy/setup.bash"
else
    echo "[WARN] ROS 2 Jazzy not found in /opt/ros/jazzy."
fi

# Check ros2 command
if command -v ros2 &> /dev/null; then
    echo "[PASS] ros2 command is available."
else
    echo "[WARN] ros2 command not found."
fi

# 3. Check Gazebo Harmonic
if command -v gz &> /dev/null; then
    GZ_VER=$(gz --version | grep "Harmonic")
    if [ -n "$GZ_VER" ]; then
        echo "[PASS] Gazebo Harmonic found."
    else
        echo "[WARN] gz command found, but it may not be Harmonic. Check your version."
    fi
else
    echo "[WARN] Gazebo (gz) command not found."
fi

# 4. Check PX4-Autopilot directory
PX4_DIR=${PX4_DIR:-$HOME/PX4-Autopilot}
if [ -d "$PX4_DIR" ]; then
    echo "[PASS] PX4-Autopilot directory found at: $PX4_DIR"
    # Check branch/tag if possible
    cd "$PX4_DIR" && PX4_TAG=$(git describe --tags 2>/dev/null || echo "Unknown")
    echo "       -> PX4 Git Tag/Branch: $PX4_TAG"

    # Check if there are uncommitted changes
    if ! git diff --quiet; then
        echo "       -> [WARN] PX4-Autopilot has uncommitted changes."
    fi
    cd - > /dev/null
else
    echo "[WARN] PX4-Autopilot directory not found at $PX4_DIR."
fi

# 5. Check ROS 2 workspace and px4_msgs
PX4_ROS2_WS=${PX4_ROS2_WS:-$HOME/px4_ros2_ws}
if [ -d "$PX4_ROS2_WS" ]; then
    echo "[PASS] ROS 2 Workspace found at: $PX4_ROS2_WS"
    if [ -d "$PX4_ROS2_WS/src/px4_msgs" ]; then
        echo "[PASS] px4_msgs package found in workspace."
        # Simple warning about matching versions
        echo "       -> Note: Ensure your px4_msgs branch matches your PX4 version (e.g. release/1.14 vs v1.14.x, or main/v1.15 vs v1.15.x/main)."
    else
        echo "[WARN] px4_msgs not found in $PX4_ROS2_WS/src. You need px4_msgs to build the offboard node."
    fi
else
    echo "[WARN] ROS 2 workspace not found at $PX4_ROS2_WS."
fi

# 6. Check Micro XRCE-DDS Agent
if command -v MicroXRCEAgent &> /dev/null; then
    echo "[PASS] MicroXRCEAgent command is available."
else
    echo "[WARN] MicroXRCEAgent command not found. You will not be able to bridge PX4 to ROS 2."
fi

# 7. Check colcon and python
if command -v colcon &> /dev/null; then
    echo "[PASS] colcon build tool is available."
else
    echo "[WARN] colcon not found. Install python3-colcon-common-extensions."
fi

if command -v python3 &> /dev/null; then
    echo "[PASS] Python 3 is available."
else
    echo "[WARN] Python 3 not found."
fi

echo "========================================"
echo "Check Complete. Review any [WARN] messages."
echo "========================================"
