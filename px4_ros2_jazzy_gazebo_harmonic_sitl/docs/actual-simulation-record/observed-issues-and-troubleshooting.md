---
description: >-
  Actual PX4, Gazebo camera and YOLO troubleshooting observations recorded
  during the simulation.
---

# Observed Issues and Troubleshooting

## PX4 SITL arming issue

### Environment

* OS: Ubuntu 24.04 Noble
* Simulator: Gazebo / PX4 SITL
* PX4 vehicle: `gz_x500_depth`
* ROS 2 bridge: Micro XRCE-DDS Agent

### Issue

PX4 SITL was running correctly, Gazebo was open, and the Micro XRCE-DDS Agent was connected successfully. The DDS topics were being created, but the drone could not take off using:

```
commander takeoff
```

PX4 showed:

```
Arming denied: Resolve system health failures first
```

Running:

```bash
commander check
```

showed:

```
Preflight Fail: No connection to the GCS
```

### Cause

PX4 was treating the missing Ground Control Station/data-link connection as a blocking preflight health failure. In this setup, the drone was controlled directly from the PX4 console and ROS 2/DDS, without QGroundControl. The saved PX4 parameter `NAV_DLL_ACT` was causing the missing GCS/data-link condition to block arming.

### Fix used in SITL

Inside the PX4 `pxh` console:

```
param set NAV_DLL_ACT 0
param save
commander check
commander takeoff
```

After this, the preflight check passed and the drone was able to take off.

{% hint style="danger" %}
This fix is acceptable for local simulation/SITL testing only. For a real drone, data-link-loss failsafe should not be disabled casually because it is an important safety feature.
{% endhint %}

## Gazebo camera not appearing in ROS 2

### Error

The Gazebo camera topic was visible with:

```bash
gz topic -l
```

but this returned no ROS 2 image topics:

```bash
ros2 topic list | grep -i image
```

The camera topic existed only inside Gazebo:

```
/world/default/model/x500_depth_0/link/camera_link/sensor/IMX214/image
```

### Root cause

PX4 Micro XRCE-DDS does not bridge Gazebo camera images into ROS 2. The Gazebo image topic must be bridged separately using `ros_gz_image`.

The `GZ_IMAGE_TOPIC` variable also became empty when commands were run from a different terminal because shell variables do not persist between terminals.

### Fix

First confirm the Gazebo camera topic:

```bash
gz topic -l | grep '/IMX214/image$'
```

Set the topic explicitly:

```bash
export GZ_IMAGE_TOPIC="/world/default/model/x500_depth_0/link/camera_link/sensor/IMX214/image"
```

Confirm that Gazebo is publishing it:

```bash
gz topic -i -t "$GZ_IMAGE_TOPIC"
```

Start the image bridge:

```bash
source /opt/ros/jazzy/setup.bash
ros2 run ros_gz_image image_bridge "$GZ_IMAGE_TOPIC"
```

Keep this terminal running.

In a new terminal, verify the ROS 2 topic:

```bash
source /opt/ros/jazzy/setup.bash
ros2 topic list | grep -i image
ros2 topic hz /world/default/model/x500_depth_0/link/camera_link/sensor/IMX214/image
```

View the camera:

```bash
ros2 run rqt_image_view rqt_image_view
```

Select:

```
/world/default/model/x500_depth_0/link/camera_link/sensor/IMX214/image
```

The working camera pipeline is:

```
Gazebo camera
→ ros_gz_image image_bridge
→ ROS 2 image topic
→ YOLO detector
→ /vision/annotated
```

Micro XRCE-DDS is used for PX4 telemetry and control topics, not for bridging Gazebo camera images. The image bridge must remain running while the detector is active.

## `GZ_IMAGE_TOPIC` is empty

Example:

```
Invalid topic. Topic must not be empty.
```

Cause:

* Gazebo is not running.
* The camera drone has not loaded.
* The variable was created in another terminal.
* The command was run before the IMX214 topic appeared.

Fix:

```bash
gz topic -l | grep '/IMX214/image$'
export GZ_IMAGE_TOPIC="$(
  gz topic -l |
  grep '/IMX214/image$' |
  head -n 1
)"
echo "$GZ_IMAGE_TOPIC"
```

## Gazebo topic exists but ROS image topic is absent

Cause: Gazebo image topics do not automatically become ROS 2 topics. The `ros_gz_image` bridge is not running.

Fix:

```bash
source /opt/ros/jazzy/setup.bash
export GZ_IMAGE_TOPIC="$(
  gz topic -l |
  grep '/IMX214/image$' |
  head -n 1
)"
ros2 run ros_gz_image image_bridge \
  "$GZ_IMAGE_TOPIC"
```

Keep the bridge terminal running.

## Raw camera works but `/vision/annotated` is absent

Cause: the YOLO detector is not running, failed during startup, or subscribed to an incorrect image topic.

Check:

```bash
ros2 node list
ros2 topic list | grep vision
```

Expected node:

```
/yolo_car_detector
```

Restart the detector using the canonical implementation on the [YOLO Car Detector](yolo-car-detector.md) page and the startup commands on the [Simulation Runbook](simulation-runbook.md) page.

## Annotated image works but no car is detected

If `/vision/annotated` updates and displays:

```
Detections: 0
```

then ROS 2 and the detector pipeline are working. The remaining issue is likely:

* Car is too small.
* Car is partially outside the frame.
* Camera angle differs too much from VisDrone.
* Gazebo car texture is unrealistic.
* Confidence threshold is too high.
* Simulation-to-real visual domain gap.

Try:

```bash
export YOLO_CONF="0.08"
export YOLO_IMGSZ="640"
```

Restart the detector. Also reposition the car so its complete roof and body are visible from an elevated angle.

## Model file reports permission denied

Do not execute the model directly:

```bash
~/px4_ros2_ws/models/best.pt
```

A `.pt` file is model data, not an executable program. It must be loaded through Python:

```python
from ultralytics import YOLO
model = YOLO(
    "/home/pratyush-jain/px4_ros2_ws/models/best.pt"
)
```

## `rqt_image_view` displays raw image without boxes

The wrong topic was selected.

Raw camera:

```
/world/default/model/x500_depth_0/link/camera_link/sensor/IMX214/image
```

YOLO output:

```
/vision/annotated
```

Select `/vision/annotated`.
