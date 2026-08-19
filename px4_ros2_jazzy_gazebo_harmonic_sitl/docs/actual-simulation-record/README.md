---
description: >-
  Navigation hub for the actual AeroNetra PX4 SITL, Gazebo, ROS 2, OpenCV and
  YOLO simulation documented in the provided PDF.
---

# Actual Simulation Record

{% hint style="warning" %}
This section records the simulation that was actually performed. The detailed commands and code remain preserved in the dedicated pages below. They are not rewritten as generic examples.
{% endhint %}

## How to use this section

Follow the pages in order. Each page answers one practical question and keeps its executable code in one canonical location, so the same code is not repeated in multiple places.

1. [Camera Verification](camera-verification.md) — establish that Gazebo is publishing the IMX214 camera and ROS 2 is receiving frames.
2. [OpenCV Bounding-Box Experiments](opencv-bounding-box-experiments.md) — the two recorded OpenCV experiments: background-calibrated bounding boxes and enhanced position/size tracking.
3. [YOLO Car Detector](yolo-car-detector.md) — the recorded VisDrone-trained `best.pt` setup and the complete `yolo_car_detector.py` implementation.
4. [Simulation Runbook](simulation-runbook.md) — the four-terminal daily startup, object placement, CPU tuning and clean shutdown procedure.
5. [Observed Issues and Troubleshooting](observed-issues-and-troubleshooting.md) — the PX4 arming issue, Gazebo-to-ROS camera issue and detector troubleshooting actually encountered.

## Environment recorded in the experiment

The PDF records work across Ubuntu 24.04 Noble, ROS 2 Jazzy, PX4 SITL, Gazebo, the `gz_x500_depth` vehicle, the IMX214 camera, `rqt_image_view`, a VisDrone-trained `best.pt`, and a Prius model inserted through Gazebo Resource Spawner.

## Final architecture

```
Gazebo car model
↓
x500_depth IMX214 camera
↓
Gazebo gz.msgs.Image
↓
ros_gz_image image_bridge
↓
ROS 2 sensor_msgs/msg/Image
↓
yolo_car_detector.py
↓
VisDrone best.pt inference
↓
YOLO bounding boxes and labels
↓
/vision/annotated
↓
rqt_image_view
```

The PX4 flight controller is responsible for simulated drone flight. Gazebo is responsible for the world, vehicle rendering, car model and camera sensor. `ros_gz_image` transfers camera frames from Gazebo Transport into ROS 2. The Python node uses `cv_bridge` to convert ROS images into OpenCV arrays. The custom Ultralytics model processes each frame and draws detections. The annotated frames are published on `/vision/annotated` and displayed with `rqt_image_view`.

## Canonical-code rule

The complete source code is intentionally kept only on the page where it is introduced. Later runbooks use commands to execute that canonical file rather than embedding another copy of the same source. This prevents the documentation from drifting when the implementation changes.
