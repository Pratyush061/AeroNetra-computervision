#!/usr/bin/env bash
# scripts/install_missing_only.sh
# Installs only confirmed-missing dependencies for Ubuntu 24.04 + ROS 2 Jazzy.
# It never reinstalls PX4, ROS 2 or Gazebo.
set -euo pipefail

ROS_DISTRO_NAME="${ROS_DISTRO_NAME:-jazzy}"

APT_PKGS="python3-pip python3-venv python3-colcon-common-extensions git \
ros-${ROS_DISTRO_NAME}-cv-bridge \
ros-${ROS_DISTRO_NAME}-ros-gz-image \
ros-${ROS_DISTRO_NAME}-rqt-image-view \
python3-opencv"

echo "Checking for missing apt dependencies..."
MISSING=""
for pkg in $APT_PKGS; do
    if ! dpkg -s "$pkg" >/dev/null 2>&1; then
        MISSING="$MISSING $pkg"
    fi
done

if [ -n "$MISSING" ]; then
    echo "Installing missing packages:$MISSING"
    sudo apt-get update
    # shellcheck disable=SC2086
    sudo apt-get install -y $MISSING
else
    echo "All required apt packages are already installed."
fi

if ! python3 -c "import setuptools" 2>/dev/null; then
    echo "Installing python3-setuptools..."
    sudo apt-get install -y python3-setuptools
fi

echo "Done. For the YOLO detector, run scripts/setup_workspace.sh with INSTALL_CV=1."
