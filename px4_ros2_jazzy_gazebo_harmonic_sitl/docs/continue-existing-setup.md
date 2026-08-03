# Continuing from an Existing Setup

This repository is designed to respect your existing environment. It will **not** attempt to overwrite, delete, or reinstall software you have already configured.

## Overview of Existing Paths

The scripts in this package assume the following default paths for your existing environment:

- **PX4-Autopilot directory**: `~/PX4-Autopilot`
- **ROS 2 Workspace directory**: `~/px4_ros2_ws`

If your directories are in different locations, you can export environment variables before running any scripts:

```bash
export PX4_DIR=/path/to/your/PX4-Autopilot
export PX4_ROS2_WS=/path/to/your/px4_ros2_ws
```

## Adding the Demo Node

To use the `px4_offboard_py` demo without touching your core files, simply add it to your existing workspace:

1. Link or copy the package into your `src` directory:
   ```bash
   ln -s $(pwd)/px4_ros2_jazzy_gazebo_harmonic_sitl/ros2_ws/src/px4_offboard_py ~/px4_ros2_ws/src/
   ```

2. Source ROS 2 and build your workspace:
   ```bash
   cd ~/px4_ros2_ws
   source /opt/ros/jazzy/setup.bash
   colcon build --symlink-install
   ```

## Missing Basic Dependencies

If `check_existing_setup.sh` alerts you that basic tools like `colcon`, `git`, or `pip3` are missing, you can safely install them using:

```bash
./scripts/install_missing_only.sh
```

This script only installs packages via `apt` (like `python3-colcon-common-extensions`) if they are completely missing. It does not run risky `pip install` commands outside of virtual environments or attempt to modify your core ROS/PX4 installations.
