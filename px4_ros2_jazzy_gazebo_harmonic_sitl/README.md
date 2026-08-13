---
description: >-
  Verified PX4 SITL integration for ROS 2 Jazzy and Gazebo, covering both
  flight-control telemetry and the tested AeroNetra YOLO camera pipeline.
---

# PX4 + ROS 2 + Gazebo Integration

This section documents AeroNetra's simulation environment on **Ubuntu 24.04 Noble**, **ROS 2 Jazzy**, **PX4 SITL**, and **Gazebo**. It intentionally separates two integration paths that use different bridges.

{% hint style="info" %}
The camera/vision workflow below is based on the working steps recorded in the AeroNetra development notes and tested with `gz_x500_depth`, the IMX214 camera, a Gazebo Prius, and a VisDrone-trained `best.pt` model.
{% endhint %}

## Two independent integration paths

```mermaid
flowchart LR
    PX4[PX4 SITL] -->|uXRCE-DDS| XRCE[Micro XRCE-DDS Agent]
    XRCE --> FMU[ROS 2 /fmu topics]
    FMU --> CTRL[Offboard control node]

    GZ[Gazebo IMX214 camera] -->|gz.msgs.Image| BRIDGE[ros_gz_image image_bridge]
    BRIDGE --> IMG[ROS 2 Image topic]
    IMG --> YOLO[YOLO detector]
    YOLO --> ANN[/vision/annotated]
    ANN --> RQT[rqt_image_view]
```

| Path                | Purpose                                            | Required bridge             |
| ------------------- | -------------------------------------------------- | --------------------------- |
| **Flight control**  | PX4 telemetry, `/fmu/*` topics, offboard commands  | Micro XRCE-DDS Agent        |
| **Computer vision** | Gazebo camera frames → YOLO → annotated ROS images | `ros_gz_image image_bridge` |

**Micro XRCE-DDS does not carry Gazebo camera frames into ROS 2.** For a camera-only CV test, Micro XRCE-DDS and QGroundControl are not required.

## Where to start

1. Continuing from an Existing Setup — protect a working local installation.
2. Environment Report — verify Ubuntu, ROS 2, Gazebo and PX4 prerequisites.
3. Choose the workflow you need:
   * Running the Simulation for PX4 telemetry/offboard control.
   * Verified YOLO Camera Pipeline for the tested live CV path.
4. Use Troubleshooting when a bridge, topic, detector, or arming check fails.

## Repository layout

```
px4_ros2_jazzy_gazebo_harmonic_sitl/
├── README.md
├── docs/
│   ├── README.md
│   ├── continue-existing-setup.md
│   ├── environment-report.md
│   ├── run-simulation.md
│   ├── verified-yolo-camera-pipeline.md
│   └── troubleshooting.md
├── scripts/
└── ros2_ws/src/px4_offboard_py/
```

{% hint style="warning" %}
A simulation workaround that disables PX4's data-link-loss action is documented only for local SITL troubleshooting. It must **not** be treated as a safe default for real aircraft.
{% endhint %}
