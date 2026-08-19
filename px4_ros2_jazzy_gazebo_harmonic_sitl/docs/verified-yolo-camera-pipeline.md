---
description: >-
  Tested AeroNetra workflow for PX4 gz_x500_depth, Gazebo IMX214 camera
  bridging, ROS 2 Jazzy, the recorded VisDrone-trained YOLO model, and
  rqt_image_view.
---

# Verified YOLO Camera Pipeline

This page is the concise operational view of the computer-vision pipeline that was verified during AeroNetra development. The detailed experiment record, including the recorded OpenCV prototypes, PX4/Gazebo issues, and the complete detector code, is preserved in Actual Simulation Record.

{% hint style="success" %}
**Verified workflow:** Ubuntu 24.04 Noble + ROS 2 Jazzy + PX4 SITL + Gazebo + `gz_x500_depth` + IMX214 + VisDrone-trained `best.pt` + `rqt_image_view`.
{% endhint %}

## Camera transport boundary

The working camera path from the actual simulation is:

```
Gazebo camera
→ ros_gz_image image_bridge
→ ROS 2 image topic
→ YOLO detector
→ /vision/annotated
```

`MicroXRCEAgent` is used for PX4 telemetry/control topics, not for Gazebo camera images. For the camera-only computer-vision test, QGroundControl and Micro XRCE-DDS Agent are not required.

## Tested environment

| Component    | Tested value                                                 |
| ------------ | ------------------------------------------------------------ |
| OS           | Ubuntu 24.04 Noble                                           |
| ROS 2        | Jazzy                                                        |
| Simulator    | Gazebo Sim                                                   |
| PX4          | SITL                                                         |
| PX4 model    | `gz_x500_depth`                                              |
| Camera       | IMX214                                                       |
| Model        | VisDrone-trained `best.pt`                                   |
| Test vehicle | Prius from Gazebo Resource Spawner / OpenRobotics collection |
| Viewer       | `rqt_image_view`                                             |

## Four-terminal startup

### Terminal 1 — PX4 and Gazebo

```bash
cd ~/PX4-Autopilot
make px4_sitl gz_x500_depth
```

Wait for `pxh>`, make sure Gazebo is playing, and verify the `x500_depth_0` drone and the previously spawned car are visible.

### Terminal 2 — bridge the camera

```bash
source /opt/ros/jazzy/setup.bash
GZ_IMAGE_TOPIC="$(
  gz topic -l |
  grep '/IMX214/image$' |
  head -n 1
)"
echo "$GZ_IMAGE_TOPIC"
gz topic -i -t "$GZ_IMAGE_TOPIC"
ros2 run ros_gz_image image_bridge "$GZ_IMAGE_TOPIC"
```

Expected camera topic:

```
/world/default/model/x500_depth_0/link/camera_link/sensor/IMX214/image
```

Expected Gazebo type:

```
gz.msgs.Image
```

### Terminal 3 — YOLO detector

```bash
source /opt/ros/jazzy/setup.bash
source ~/px4_ros2_ws/yolo_venv/bin/activate
ROS_IMAGE_TOPIC="$(
  ros2 topic list |
  grep '/IMX214/image$' |
  head -n 1
)"
timeout 8 ros2 topic hz "$ROS_IMAGE_TOPIC"
export YOLO_MODEL="$HOME/px4_ros2_ws/models/best.pt"
export IMAGE_TOPIC="$ROS_IMAGE_TOPIC"
export OUTPUT_TOPIC="/vision/annotated"
export YOLO_CONF="0.15"
export YOLO_IMGSZ="640"
export YOLO_DEVICE="cpu"
export PROCESS_EVERY_N_FRAMES="1"
python3 ~/px4_ros2_ws/aeronetra_cv/yolo_car_detector.py
```

Expected startup evidence:

```
Loading YOLO model: .../best.pt
Model task: detect
Model classes: ...
Input topic: /world/default/.../IMX214/image
Output topic: /vision/annotated
YOLO car detector is ready.
```

### Terminal 4 — inspect results

```bash
source /opt/ros/jazzy/setup.bash
ros2 topic list | grep vision
timeout 10 ros2 topic hz /vision/annotated
ros2 run rqt_image_view rqt_image_view
```

Select:

```
/vision/annotated
```

That is the annotated topic with the YOLO labels, confidence values, bounding boxes, and detection-count status line.

## Model and viewpoint notes from the actual run

The model was trained using VisDrone aerial imagery, so the simulated camera perspective materially affects detection. The recorded guidance is to keep the complete car visible, avoid extreme close-ups and clipping, use a realistic textured car, expose the roof and full body, use an elevated slightly downward angle, keep the car large enough in frame, use daylight or clear simulated lighting, and avoid occlusion.

The recorded default confidence was `0.15`. After stable detection, the PDF raises it to `0.25`; for diagnosis, it records `0.08` with `640` image size.

For CPU responsiveness, the recorded fallback is:

```bash
export YOLO_CONF="0.15"
export YOLO_IMGSZ="416"
export YOLO_DEVICE="cpu"
export PROCESS_EVERY_N_FRAMES="2"
```

## What counts as a successful checkpoint

1. `/IMX214/image` exists in Gazebo and reports `gz.msgs.Image`.
2. `ros_gz_image` is running.
3. ROS 2 reports an image stream with a measurable average rate.
4. `best.pt` loads successfully.
5. `/vision/annotated` is publishing.
6. `rqt_image_view` displays the annotated feed.
7. The model produces boxes/labels for the simulated car when the car is positioned in a VisDrone-like view.

For the exact recorded source code and the failure notes discovered during the simulation, see Actual Simulation Record.
