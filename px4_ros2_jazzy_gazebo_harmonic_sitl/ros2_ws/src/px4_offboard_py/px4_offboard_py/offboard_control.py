#!/usr/bin/env python3
"""
Offboard control node for PX4 in ROS 2.
Commands takeoff to 2 meters, hovers for 10 seconds, then lands.
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy

# Use absolute imports for PX4 messages (assuming px4_msgs is built in the workspace)
try:
    from px4_msgs.msg import (
        OffboardControlMode,
        TrajectorySetpoint,
        VehicleCommand,
        VehicleLocalPosition,
        VehicleStatus,
    )
except ImportError:
    print("Error: px4_msgs not found. Make sure the package is built and sourced.")
    raise


class OffboardControl(Node):
    def __init__(self):
        super().__init__("offboard_control")

        # Configure QoS profile for PX4 topics
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,  # PX4 uXRCE-DDS agent uses VOLATILE
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        # Publishers
        self.offboard_control_mode_publisher = self.create_publisher(
            OffboardControlMode, "/fmu/in/offboard_control_mode", qos_profile
        )
        self.trajectory_setpoint_publisher = self.create_publisher(
            TrajectorySetpoint, "/fmu/in/trajectory_setpoint", qos_profile
        )
        self.vehicle_command_publisher = self.create_publisher(
            VehicleCommand, "/fmu/in/vehicle_command", qos_profile
        )

        # Subscribers
        self.vehicle_local_position_subscriber = self.create_subscription(
            VehicleLocalPosition,
            "/fmu/out/vehicle_local_position",
            self.vehicle_local_position_callback,
            qos_profile,
        )
        self.vehicle_status_subscriber = self.create_subscription(
            VehicleStatus,
            "/fmu/out/vehicle_status",
            self.vehicle_status_callback,
            qos_profile,
        )

        # State variables
        self.nav_state = VehicleStatus.NAVIGATION_STATE_MAX
        self.arming_state = VehicleStatus.ARMING_STATE_DISARMED
        self.vehicle_altitude = 0.0
        self.takeoff_height = -2.0  # NED coordinate system: -2.0 meters is 2 meters up

        # Timestamp trackers for stale data detection
        self.last_status_time = None
        self.last_position_time = None

        # State machine
        self.state = "INIT"
        self.offboard_setpoint_counter = 0
        self.hover_start_time = None
        self.hover_duration = 10.0  # seconds

        # Create a timer to publish control commands at 10 Hz
        timer_period = 0.1  # 10 Hz
        self.timer = self.create_timer(timer_period, self.timer_callback)

        self.get_logger().info("Offboard control node initialized.")

    def vehicle_status_callback(self, vehicle_status):
        """Callback for vehicle_status topic."""
        self.nav_state = vehicle_status.nav_state
        self.arming_state = vehicle_status.arming_state
        self.last_status_time = self.get_clock().now()

    def vehicle_local_position_callback(self, vehicle_local_position):
        """Callback for vehicle_local_position topic."""
        self.vehicle_altitude = vehicle_local_position.z
        self.last_position_time = self.get_clock().now()

    def is_data_stale(self):
        """Check if vehicle data is stale (e.g. lost connection)."""
        now = self.get_clock().now()
        timeout = rclpy.time.Duration(seconds=2.0)

        if self.last_status_time is None or self.last_position_time is None:
            return True  # No data received yet

        if (now - self.last_status_time) > timeout or (
            now - self.last_position_time
        ) > timeout:
            return True

        return False

    def arm(self):
        """Send an arm command to the vehicle."""
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, param1=1.0
        )
        self.get_logger().info("Arm command send")

    def disarm(self):
        """Send a disarm command to the vehicle."""
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, param1=0.0
        )
        self.get_logger().info("Disarm command send")

    def engage_offboard_mode(self):
        """Switch to offboard mode."""
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_DO_SET_MODE, param1=1.0, param2=6.0
        )
        self.get_logger().info("Switching to offboard mode")

    def land(self):
        """Switch to land mode."""
        self.publish_vehicle_command(VehicleCommand.VEHICLE_CMD_NAV_LAND)
        self.get_logger().info("Switching to land mode")

    def publish_offboard_control_heartbeat_signal(self):
        """Publish the offboard control mode."""
        msg = OffboardControlMode()
        msg.position = True
        msg.velocity = False
        msg.acceleration = False
        msg.attitude = False
        msg.body_rate = False
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        self.offboard_control_mode_publisher.publish(msg)

    def publish_position_setpoint(self, x: float, y: float, z: float):
        """Publish the trajectory setpoint."""
        msg = TrajectorySetpoint()
        msg.position = [x, y, z]
        msg.yaw = 0.0  # (90 degree)
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        self.trajectory_setpoint_publisher.publish(msg)

    def publish_vehicle_command(self, command, **params) -> None:
        """Publish a vehicle command."""
        msg = VehicleCommand()
        msg.command = command
        msg.param1 = params.get("param1", 0.0)
        msg.param2 = params.get("param2", 0.0)
        msg.param3 = params.get("param3", 0.0)
        msg.param4 = params.get("param4", 0.0)
        msg.param5 = params.get("param5", 0.0)
        msg.param6 = params.get("param6", 0.0)
        msg.param7 = params.get("param7", 0.0)
        msg.target_system = 1
        msg.target_component = 1
        msg.source_system = 1
        msg.source_component = 1
        msg.from_external = True
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        self.vehicle_command_publisher.publish(msg)

    def timer_callback(self) -> None:
        """Callback function for the timer."""

        # Check for stale data, except if we are just starting up and haven't received anything yet
        if self.state != "INIT":
            if self.is_data_stale():
                self.get_logger().error(
                    "Vehicle data is stale or connection lost. Triggering emergency land."
                )
                self.state = "EMERGENCY_LAND"

        # Must publish heartbeat to maintain offboard mode
        self.publish_offboard_control_heartbeat_signal()

        # State Machine
        if self.state == "INIT":
            # Wait for data to arrive before proceeding
            if self.is_data_stale():
                self.get_logger().debug(
                    "Waiting for vehicle data...", throttle_duration_sec=2.0
                )
                return

            # Send initial setpoints before switching mode (PX4 requires a continuous stream of setpoints for at least 0.5 - 1.0 seconds)
            if self.offboard_setpoint_counter == 0:
                self.get_logger().info(
                    "Streaming setpoints before engaging offboard mode..."
                )

            self.publish_position_setpoint(0.0, 0.0, 0.0)
            self.offboard_setpoint_counter += 1

            # After 1 second (10 ticks at 10Hz), arm and engage offboard mode
            if self.offboard_setpoint_counter >= 10:
                self.arm()
                self.engage_offboard_mode()
                self.state = "TAKEOFF"
                self.get_logger().info("Transitioning to TAKEOFF")

        elif self.state == "TAKEOFF":
            self.publish_position_setpoint(0.0, 0.0, self.takeoff_height)

            # Check if altitude is reached (NED z is negative for up)
            # Add small tolerance
            if self.vehicle_altitude <= (self.takeoff_height + 0.2):
                self.state = "HOVER"
                self.hover_start_time = self.get_clock().now()
                self.get_logger().info(
                    f"Target altitude reached. Transitioning to HOVER for {self.hover_duration} seconds"
                )

        elif self.state == "HOVER":
            self.publish_position_setpoint(0.0, 0.0, self.takeoff_height)
            elapsed_time = (
                self.get_clock().now() - self.hover_start_time
            ).nanoseconds / 1e9
            if elapsed_time >= self.hover_duration:
                self.state = "LAND"
                self.get_logger().info("Hover complete. Transitioning to LAND")
                self.land()

        elif self.state == "LAND":
            # Just wait, land mode takes over. We still send heartbeats and a neutral setpoint
            # just to be safe, though PX4 will prioritize the LAND command.
            self.publish_position_setpoint(0.0, 0.0, self.takeoff_height)

            # If vehicle disarms after landing, we can stop the node
            if self.arming_state == VehicleStatus.ARMING_STATE_DISARMED:
                self.get_logger().info("Vehicle disarmed. Demonstration complete.")
                raise SystemExit

        elif self.state == "EMERGENCY_LAND":
            self.land()
            self.publish_position_setpoint(
                0.0, 0.0, self.vehicle_altitude
            )  # command current altitude

            if self.arming_state == VehicleStatus.ARMING_STATE_DISARMED:
                self.get_logger().info(
                    "Vehicle disarmed after emergency land. Quitting."
                )
                raise SystemExit

        else:
            self.get_logger().warn("Unknown state.")


def main(args=None) -> None:
    print("Starting offboard control node...")
    rclpy.init(args=args)
    offboard_control = OffboardControl()

    try:
        rclpy.spin(offboard_control)
    except SystemExit:
        rclpy.logging.get_logger("Quitting").info("Done")
    except KeyboardInterrupt:
        pass
    except Exception as e:
        offboard_control.get_logger().error(f"Error: {e}")
    finally:
        offboard_control.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
