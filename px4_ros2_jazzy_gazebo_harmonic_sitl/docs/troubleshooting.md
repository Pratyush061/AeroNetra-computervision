# Troubleshooting

If the demo doesn't work out of the box, here are the most common issues when integrating PX4 SITL, Gazebo, Micro XRCE-DDS, and ROS 2.

## 1. No `/fmu/` Topics Found

**Symptom**: Running `ros2 topic list | grep '^/fmu/'` returns nothing.

**Possible Causes**:
- The `MicroXRCEAgent` isn't running in Terminal 2, or PX4 hasn't connected to it. Check Terminal 2 for connection logs.
- Port collision: Make sure nothing else is using UDP port 8888.
- The `px4_msgs` package was not built. The Agent dynamically looks for message definitions in the ROS 2 space. Ensure your workspace is built and sourced.

## 2. Topics are visible, but `ros2 topic echo` is empty

**Symptom**: `ros2 topic list` shows topics, but `ros2 topic echo /fmu/out/vehicle_status` hangs without printing data.

**Possible Causes**:
- **QoS Mismatch**: PX4 uses specific Quality of Service (QoS) settings (Best Effort, Transient Local). If you are using a standard `ros2 topic echo`, try forcing Best Effort: `ros2 topic echo --qos-reliability best_effort /fmu/out/vehicle_status`.
- **DDS Discovery Issues**: Ensure you don't have conflicting DDS implementations or network configurations (like `ROS_DOMAIN_ID` set incorrectly on one terminal but not another).

## 3. Node runs but drone doesn't arm or switch to offboard

**Symptom**: The Python node prints "Transitioning to TAKEOFF" but the drone in Gazebo just sits there.

**Possible Causes**:
- **Message Version Mismatch**: If your `px4_msgs` repository branch does not match the PX4-Autopilot firmware version, the binary layout of the messages differs. The XRCE-DDS bridge drops the mismatched messages silently. Fix: Check out the matching branch in `px4_msgs` and rebuild the workspace.
- **Heartbeat Timeout**: The vehicle will drop out of offboard mode if it does not receive a continuous stream of setpoints (at least 2 Hz). The provided node runs a timer at 10 Hz to prevent this. Ensure your machine is not bogged down.
- **No Local Position**: Offboard mode requires a valid position estimate. In SITL, this is usually provided immediately. Check `ros2 topic echo /fmu/out/vehicle_local_position` to ensure the simulated GPS/EKF is publishing valid coordinates.
