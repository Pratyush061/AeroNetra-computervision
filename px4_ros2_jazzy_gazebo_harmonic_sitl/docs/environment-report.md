# Environment Report Template

You can run the included `scripts/check_existing_setup.sh` utility script to check these requirements on your Ubuntu 24.04 machine.

## Required Software Checklist

- [ ] **OS**: Ubuntu 24.04
- [ ] **ROS 2**: Jazzy Jalisco (`/opt/ros/jazzy`)
- [ ] **Gazebo**: Harmonic (verify using `gz --version`)
- [ ] **PX4-Autopilot**: Cloned (e.g. at `~/PX4-Autopilot`). Tested with branches compatible with `px4_msgs`.
- [ ] **Micro XRCE-DDS Agent**: Installed and available in PATH (test `MicroXRCEAgent --version`).
- [ ] **px4_msgs**: Placed inside `~/px4_ros2_ws/src/px4_msgs`. Must match the branch/tag of your PX4-Autopilot.

## Validating Message Versions

The ROS 2 interface requires that the `.msg` files inside `px4_msgs` exactly match the `.msg` files in the PX4-Autopilot firmware you compiled.

If you get QoS errors or topics appear but nodes don't communicate, verify that:
1. `PX4-Autopilot` is checked out to a specific tag (e.g. `v1.14.0`).
2. `px4_msgs` is checked out to the matching branch (e.g. `release/1.14`).

## Checking with the Utility Script

Run the verification tool before starting:

```bash
cd px4_ros2_jazzy_gazebo_harmonic_sitl
./scripts/check_existing_setup.sh
```

Ensure you read and fix any `[WARN]` messages before proceeding.
