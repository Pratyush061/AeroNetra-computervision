---
description: >-
  Tested AeroNetra workflow for PX4 gz_x500_depth, Gazebo IMX214 camera
  bridging, ROS 2 Jazzy, a VisDrone-trained YOLO model, and rqt_image_view.
---

# Verified YOLO Camera Pipeline

This page records the **working end-to-end computer-vision setup** used during AeroNetra development. It is intended to be reproducible by other developers and to give coding agents an authoritative operational reference instead of forcing them to reconstruct terminal history.

{% hint style="success" %}
**Verified workflow:** Ubuntu 24.04 Noble + ROS 2 Jazzy + PX4 SITL + Gazebo + `gz_x500_depth` + IMX214 + VisDrone-trained `best.pt` + `rqt_image_view`.
{% endhint %}

## 1. Architecture

```mermaid
flowchart TD
    CAR[Gazebo Prius / test vehicle] --> CAM[x500_depth IMX214 camera]
    CAM --> GZ[gz.msgs.Image]
    GZ --> BRIDGE[ros_gz_image image_bridge]
    BRIDGE --> ROS[ROS 2 sensor_msgs/msg/Image]
    ROS --> NODE[yolo_car_detector.py]
    NODE --> MODEL[VisDrone best.pt]
    MODEL --> BOXES[Bounding boxes + labels]
    BOXES --> TOPIC[/vision/annotated]
    TOPIC --> VIEW[rqt_image_view]

    PX4[PX4 SITL] -. simulated flight .-> CAM
```

### What is _not_ in the camera path

`MicroXRCEAgent` is for PX4 telemetry/control topics. It is **not** the Gazebo image bridge. For this camera-only CV test:

* QGroundControl is not required.
* Micro XRCE-DDS Agent is not required.
* `ros_gz_image image_bridge` **must remain running** while the detector is active.

## 2. Tested environment

| Component    | Tested value                                   |
| ------------ | ---------------------------------------------- |
| OS           | Ubuntu 24.04 Noble                             |
| ROS 2        | Jazzy                                          |
| Simulator    | Gazebo Sim / Harmonic generation               |
| Flight stack | PX4 SITL                                       |
| PX4 model    | `gz_x500_depth`                                |
| Camera       | IMX214                                         |
| Model        | VisDrone-trained `best.pt`                     |
| Viewer       | `rqt_image_view`                               |
| Test car     | Prius inserted through Gazebo Resource Spawner |

## 3. One-time dependencies

```bash
sudo apt update
sudo apt install -y \
  python3-pip \
  python3-venv \
  python3-opencv \
  ros-jazzy-cv-bridge \
  ros-jazzy-ros-gz-image \
  ros-jazzy-rqt-image-view
```

Verify the ROS executables:

```bash
source /opt/ros/jazzy/setup.bash
ros2 pkg executables ros_gz_image
ros2 pkg executables rqt_image_view
```

Expected entries include:

```
ros_gz_image image_bridge
rqt_image_view rqt_image_view
```

## 4. Python environment

Use a venv that can still see the system-installed ROS Python packages:

```bash
cd ~/px4_ros2_ws
python3 -m venv --system-site-packages yolo_venv
source ~/px4_ros2_ws/yolo_venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install ultralytics
```

Verify the important modules:

```bash
python3 - <<'PY'
import cv2
import rclpy
from cv_bridge import CvBridge
from ultralytics import YOLO

print("OpenCV:", cv2.__version__)
print("ROS 2 Python: OK")
print("cv_bridge: OK")
print("Ultralytics: OK")
PY
```

## 5. Tested local workspace layout

```
~/PX4-Autopilot/

~/px4_ros2_ws/
├── models/
│   └── best.pt
├── aeronetra_cv/
│   └── yolo_car_detector.py
└── yolo_venv/
```

Confirm the trained model is present before starting inference:

```bash
ls -lh ~/px4_ros2_ws/models/best.pt
```

## 6. Daily startup — four terminals

The tested workflow intentionally uses separate terminals so each layer can be diagnosed independently.

### Terminal 1 — PX4 and Gazebo

Clean stale simulator processes first:

```bash
pkill -TERM -f "$HOME/PX4-Autopilot/build/px4_sitl_default/bin/px4" 2>/dev/null || true
pkill -TERM -f "gz sim" 2>/dev/null || true
pkill -TERM -f "gz-sim-server" 2>/dev/null || true
pkill -TERM -f "gz-sim-gui" 2>/dev/null || true
sleep 3
```

Start the camera-equipped vehicle:

```bash
cd ~/PX4-Autopilot
make px4_sitl gz_x500_depth
```

Wait for the PX4 console prompt (`pxh>`), confirm Gazebo is playing, and verify `x500_depth_0` plus the test vehicle are visible.

### Terminal 2 — discover and bridge the Gazebo image

```bash
deactivate 2>/dev/null || true
unset PYTHONPATH
unset VIRTUAL_ENV
source /opt/ros/jazzy/setup.bash

GZ_IMAGE_TOPIC="$(
  gz topic -l |
  grep '/IMX214/image$' |
  head -n 1
)"

echo "Gazebo camera topic:"
echo "$GZ_IMAGE_TOPIC"
```

Expected topic:

```
/world/default/model/x500_depth_0/link/camera_link/sensor/IMX214/image
```

{% hint style="danger" %}
If `GZ_IMAGE_TOPIC` is empty, stop here. Do not start the detector and do not guess the topic.
{% endhint %}

Confirm the Gazebo message type:

```bash
gz topic -i -t "$GZ_IMAGE_TOPIC"
```

Expected:

```
gz.msgs.Image
```

Start the dedicated image bridge:

```bash
ros2 run ros_gz_image image_bridge "$GZ_IMAGE_TOPIC"
```

Leave this terminal open.

### Terminal 3 — verify ROS frames and run YOLO

```bash
deactivate 2>/dev/null || true
unset PYTHONPATH
unset VIRTUAL_ENV
source /opt/ros/jazzy/setup.bash
source ~/px4_ros2_ws/yolo_venv/bin/activate

ROS_IMAGE_TOPIC="$(
  ros2 topic list |
  grep '/IMX214/image$' |
  head -n 1
)"

echo "ROS camera topic:"
echo "$ROS_IMAGE_TOPIC"
```

Verify frames are arriving before loading the model:

```bash
timeout 8 ros2 topic hz "$ROS_IMAGE_TOPIC"
```

A working stream eventually reports an `average rate`.

Configure the tested detector settings:

```bash
export YOLO_MODEL="$HOME/px4_ros2_ws/models/best.pt"
export IMAGE_TOPIC="$ROS_IMAGE_TOPIC"
export OUTPUT_TOPIC="/vision/annotated"
export YOLO_CONF="0.15"
export YOLO_IMGSZ="640"
export YOLO_DEVICE="cpu"
export PROCESS_EVERY_N_FRAMES="1"
```

Start the ROS 2 detector:

```bash
python3 ~/px4_ros2_ws/aeronetra_cv/yolo_car_detector.py
```

Expected startup evidence includes:

```
Loading YOLO model: .../best.pt
Model task: detect
Model classes: ...
Input topic: /world/default/.../IMX214/image
Output topic: /vision/annotated
YOLO car detector is ready.
```

During processing, the node should periodically report received frames, processed frames, and the latest detection count.

### Terminal 4 — inspect annotated output

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

The output should contain the live camera image, YOLO class labels, confidence values, bounding boxes, and the detector status line.

{% hint style="warning" %}
The raw `/IMX214/image` topic will never contain the YOLO boxes. When validating inference, select `/vision/annotated`.
{% endhint %}

## 7. Validation checkpoints

Debug the pipeline in this order:

```mermaid
flowchart TD
    A[IMX214 exists in gz topic -l] --> B[gz topic type = gz.msgs.Image]
    B --> C[ros_gz_image bridge running]
    C --> D[ROS topic has measurable frame rate]
    D --> E[best.pt loads]
    E --> F[/vision/annotated publishes]
    F --> G[Evaluate model detections]
```

This sequence prevents a transport failure from being misdiagnosed as a YOLO accuracy problem.

## 8. Gazebo ↔ VisDrone domain gap

The model was trained on aerial imagery, so camera geometry matters in simulation. For the best chance of detection:

* keep the full car visible;
* avoid extreme close-ups;
* use an elevated, slightly downward camera angle;
* keep the roof and overall body shape visible;
* use a realistic textured vehicle;
* avoid occlusion and poor simulated lighting.

The tested simulation starts with:

```bash
export YOLO_CONF="0.15"
```

Once detections are stable, test a stricter value such as `0.25`. For diagnosis only, a lower value such as `0.08` can reveal whether the model is producing weak predictions.

## 9. CPU performance fallback

CPU inference can slow both the annotated feed and the apparent simulator responsiveness. A tested lighter configuration is:

```bash
export YOLO_CONF="0.15"
export YOLO_IMGSZ="416"
export YOLO_DEVICE="cpu"
export PROCESS_EVERY_N_FRAMES="2"
```

This reduces compute load, but smaller input resolution can hurt small-object detection.

## 10. PX4 arming issue observed in SITL

Observed symptom:

```
Arming denied: Resolve system health failures first
```

Running:

```
commander check
```

identified:

```
Preflight Fail: No connection to the GCS
```

In the tested **local SITL-only** environment, the saved data-link-loss action was blocking arming without QGroundControl. The working PX4 console change was:

```
param set NAV_DLL_ACT 0
param save
commander check
commander takeoff
```

{% hint style="danger" %}
This is a **simulation-only workaround**. A data-link-loss failsafe is a real flight-safety mechanism. Do not carry this setting onto physical aircraft as a convenience fix.
{% endhint %}

## 11. Common failures

### `GZ_IMAGE_TOPIC` is empty

The camera may not be loaded yet, Gazebo may not be running, or the variable may have been created in another shell. Shell variables do not persist between terminals.

Re-discover it in the current terminal:

```bash
export GZ_IMAGE_TOPIC="$(gz topic -l | grep '/IMX214/image$' | head -n 1)"
echo "$GZ_IMAGE_TOPIC"
```

### Gazebo image exists but ROS has no image topic

The dedicated image bridge is missing:

```bash
source /opt/ros/jazzy/setup.bash
ros2 run ros_gz_image image_bridge "$GZ_IMAGE_TOPIC"
```

### Raw camera works but `/vision/annotated` is absent

Check whether the detector node exists and whether it subscribed to the correct input:

```bash
ros2 node list
ros2 topic list | grep vision
```

Expected node:

```
/yolo_car_detector
```

### `/vision/annotated` works but detections remain zero

At this point the transport pipeline is working. Investigate model-facing conditions: object scale, framing, camera angle, Gazebo texture/domain gap, or confidence threshold.

### A `.pt` model reports permission denied

Do not execute `best.pt` directly. It is model data, not a program. It must be loaded from Python/Ultralytics.

## 12. Clean shutdown

Stop foreground processes with `Ctrl+C`, then clean leftovers if necessary:

```bash
pkill -TERM -f "yolo_car_detector.py" 2>/dev/null || true
pkill -TERM -x image_bridge 2>/dev/null || true
pkill -TERM -x rqt_image_view 2>/dev/null || true
pkill -TERM -f "$HOME/PX4-Autopilot/build/px4_sitl_default/bin/px4" 2>/dev/null || true
pkill -TERM -f "gz sim" 2>/dev/null || true
pkill -TERM -f "gz-sim-server" 2>/dev/null || true
pkill -TERM -f "gz-sim-gui" 2>/dev/null || true

pgrep -af "px4|gz sim|gz-sim|image_bridge|yolo_car_detector.py|rqt_image_view"
```

## Coding-agent rules for this workflow

* Treat this page as the authoritative record of the **tested simulation sequence**.
* Do not replace `ros_gz_image` with Micro XRCE-DDS for camera transport.
* Do not require QGroundControl for the camera-only test.
* Re-discover shell-local topic variables in each terminal rather than assuming they persist.
* Preserve the core AeroNetra model-adapter contract for reusable library code. The standalone ROS detector is an **integration harness**, not a new rule for `src/aeronetra/`.
* Never generalize the `NAV_DLL_ACT 0` SITL workaround to real flight hardware.
