#!/usr/bin/env bash
# scripts/install_missing_only.sh
# Safely installs only confirmed missing basic dependencies for Ubuntu 24.04 and ROS 2 Jazzy.
# It does NOT reinstall PX4, ROS 2, or Gazebo.

set -e

echo "Checking for missing apt dependencies..."

DEPS_TO_INSTALL=""

# Check colcon
if ! command -v colcon &> /dev/null; then
    DEPS_TO_INSTALL="$DEPS_TO_INSTALL python3-colcon-common-extensions"
fi

# Check pip
if ! command -v pip3 &> /dev/null; then
    DEPS_TO_INSTALL="$DEPS_TO_INSTALL python3-pip"
fi

# Check git
if ! command -v git &> /dev/null; then
    DEPS_TO_INSTALL="$DEPS_TO_INSTALL git"
fi

if [ -n "$DEPS_TO_INSTALL" ]; then
    echo "Installing missing dependencies: $DEPS_TO_INSTALL"
    sudo apt-get update
    sudo apt-get install -y $DEPS_TO_INSTALL
else
    echo "All checked basic apt dependencies are already installed."
fi

# Check python dependencies if pip is available
if command -v pip3 &> /dev/null; then
    # In Ubuntu 24.04 (PEP 668), pip install might fail without --break-system-packages or venv.
    # Typically user dependencies for rclpy/colcon are handled via apt (e.g. python3-rclpy).
    # We will just verify setuptools is there.
    if ! python3 -c "import setuptools" 2>/dev/null; then
        echo "setuptools missing, installing via apt..."
        sudo apt-get install -y python3-setuptools
    fi
fi

echo "Done."
