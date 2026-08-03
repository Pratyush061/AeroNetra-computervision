# PX4 ROS 2 Jazzy Gazebo Harmonic SITL

This folder contains a documented integration and demonstration of PX4 SITL using ROS 2 Jazzy and Gazebo Harmonic on Ubuntu 24.04.

It is designed to be **non-destructive** and run on top of your existing installation without re-cloning or overwriting working code.

## Requirements

- Ubuntu 24.04
- ROS 2 Jazzy Jalisco
- Gazebo Harmonic
- PX4-Autopilot (v1.14+ or main branch)
- Micro XRCE-DDS Agent

## Getting Started

1. Read `docs/continue-existing-setup.md` for information on how to proceed safely with your current installation.
2. Read `docs/environment-report.md` for a checklist of things to verify.
3. Once ready, follow the terminal commands outlined in `docs/run-simulation.md` to run the demonstration.

## Structure

- `docs/`: Markdown files explaining the setup, testing, and troubleshooting.
- `scripts/`: Safe, reusable Bash scripts to run checks, build, and launch components.
- `ros2_ws/src/px4_offboard_py/`: A Python-based `rclpy` node that connects to PX4 and commands the vehicle to take off, hover for 10 seconds, and land.

## How to use the `px4_offboard_py` package

Since your existing ROS 2 workspace is at `~/px4_ros2_ws`, you can symlink or copy this package into it:

```bash
# Option A: Copy
cp -r px4_ros2_jazzy_gazebo_harmonic_sitl/ros2_ws/src/px4_offboard_py ~/px4_ros2_ws/src/

# Option B: Symlink
ln -s $(pwd)/px4_ros2_jazzy_gazebo_harmonic_sitl/ros2_ws/src/px4_offboard_py ~/px4_ros2_ws/src/
```

After doing so, you can build your workspace:
```bash
./scripts/build_offboard_package.sh
```
