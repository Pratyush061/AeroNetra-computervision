# Running the Simulation Demonstration

This guide outlines the exact multi-terminal sequence needed to run the SITL simulation. We recommend opening 4 separate terminal tabs/windows so you can monitor the output of each process.

Ensure you have copied or symlinked the `px4_offboard_py` package into `~/px4_ros2_ws/src` and built it (see `continue-existing-setup.md`).

## Terminal 1: Launch PX4 and Gazebo

This compiles (if necessary) and starts the PX4 Software In The Loop (SITL) firmware along with Gazebo Harmonic.

```bash
cd "$HOME/PX4-Autopilot"
make px4_sitl gz_x500
```

Wait until you see the `px4>` prompt and the Gazebo UI opens with the drone spawned.

## Terminal 2: Start Micro XRCE-DDS Agent

The agent acts as the bridge between the PX4 uORB internal messaging system and the external ROS 2 DDS system.

```bash
MicroXRCEAgent udp4 -p 8888
```

You should see output indicating it is listening on UDP port 8888. Once PX4 is running in Terminal 1, it will automatically connect to this agent, and you'll see a connection message here.

## Terminal 3: Verify the ROS 2 Bridge

Before running any control nodes, we must ensure ROS 2 is receiving data from PX4.

```bash
cd "$HOME/px4_ros2_ws"
source /opt/ros/jazzy/setup.bash
source install/setup.bash

# List topics to verify bridge is working
ros2 topic list | grep '^/fmu/'

# Echo a topic to ensure data is flowing
ros2 topic echo /fmu/out/vehicle_status
```

If you see live data streaming, press `Ctrl+C` to stop the echo. Your bridge is working perfectly!

## Terminal 4: Run the Offboard Control Node

This will start the Python `rclpy` node. The node will immediately arm the vehicle, switch it into offboard mode, command it to take off to 2 meters, hover for 10 seconds, and then land safely.

```bash
cd "$HOME/px4_ros2_ws"
source /opt/ros/jazzy/setup.bash
source install/setup.bash

# Start the node
ros2 run px4_offboard_py offboard_control
```

Watch Terminal 4 for state machine logs, and watch Gazebo (opened by Terminal 1) to see the drone physically execute the commands. The node will exit automatically once the drone lands and disarms.
