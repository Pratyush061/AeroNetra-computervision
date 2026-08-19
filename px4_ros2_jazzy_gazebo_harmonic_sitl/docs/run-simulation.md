---
description: >-
  The exact four-terminal camera-and-YOLO simulation startup procedure recorded
  during AeroNetra's PX4 SITL and Gazebo experiment.
---

# Running the Simulation Demonstration

This page now follows the **actual camera-and-car simulation** documented in the AeroNetra experiment PDF. The computer-vision run uses four terminals so PX4/Gazebo, the Gazebo image bridge, the YOLO detector, and the visualizer remain independently observable.

{% hint style="success" %}
The tested vehicle is `gz_x500_depth` with the IMX214 camera. The car is a Prius model inserted into Gazebo through Resource Spawner. The camera path uses `ros_gz_image`; Micro XRCE-DDS is separate and is only needed later when PX4 telemetry/control topics are required.
{% endhint %}

## Terminal 1 — Start PX4 and Gazebo

```bash
pkill -TERM -f "$HOME/PX4-Autopilot/build/px4_sitl_default/bin/px4" \
  2>/dev/null || true
pkill -TERM -f "gz sim" \
  2>/dev/null || true
pkill -TERM -f "gz-sim-server" \
  2>/dev/null || true
pkill -TERM -f "gz-sim-gui" \
  2>/dev/null || true
sleep 3
cd ~/PX4-Autopilot
make px4_sitl gz_x500_depth
```

Wait until:

```
pxh>
```

appears. Make sure Gazebo is open and playing, the `x500_depth_0` drone is visible, and the previously spawned car is visible in the world.

## Terminal 2 — Find and bridge the Gazebo camera

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

Expected:

```
/world/default/model/x500_depth_0/link/camera_link/sensor/IMX214/image
```

Confirm the topic type:

```bash
gz topic -i -t "$GZ_IMAGE_TOPIC"
```

Expected:

```
gz.msgs.Image
```

Start the dedicated image bridge:

```bash
ros2 run ros_gz_image image_bridge \
  "$GZ_IMAGE_TOPIC"
```

Leave this terminal running. Closing it stops the camera bridge.

## Terminal 3 — Verify the ROS stream and run YOLO

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
timeout 8 ros2 topic hz "$ROS_IMAGE_TOPIC"
```

Then configure the detector exactly as recorded:

```bash
export YOLO_MODEL="$HOME/px4_ros2_ws/models/best.pt"
export IMAGE_TOPIC="$ROS_IMAGE_TOPIC"
export OUTPUT_TOPIC="/vision/annotated"
export YOLO_CONF="0.15"
export YOLO_IMGSZ="640"
export YOLO_DEVICE="cpu"
export PROCESS_EVERY_N_FRAMES="1"
```

Start detection:

```bash
python3 \
  ~/px4_ros2_ws/aeronetra_cv/yolo_car_detector.py
```

Expected startup messages:

```
Loading YOLO model: .../best.pt
Model task: detect
Model classes: ...
Input topic: /world/default/.../IMX214/image
Output topic: /vision/annotated
YOLO car detector is ready.
```

## Terminal 4 — View detection results

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

The display should contain the live Gazebo camera feed, YOLO class labels, confidence values, bounding boxes, and a status line showing the current detection count.

Do not select the raw `/IMX214/image` topic when checking bounding boxes.

## Detection positioning guidance from the experiment

The model was trained using VisDrone aerial imagery. Keep the complete car visible, avoid extreme close-ups and clipping, use a realistic textured car, expose the roof and full vehicle shape, use an elevated slightly downward camera angle, keep the car large enough in the image, use daylight or clear simulated lighting, and avoid occlusion.

The recorded default confidence is:

```bash
export YOLO_CONF="0.15"
```

After reliable detection:

```bash
export YOLO_CONF="0.25"
```

For CPU fallback:

```bash
export YOLO_CONF="0.15"
export YOLO_IMGSZ="416"
export YOLO_DEVICE="cpu"
export PROCESS_EVERY_N_FRAMES="2"
```

## Clean shutdown

Stop the active processes with Ctrl+C, then:

```bash
pkill -TERM -f "yolo_car_detector.py" \
  2>/dev/null || true
pkill -TERM -x image_bridge \
  2>/dev/null || true
pkill -TERM -x rqt_image_view \
  2>/dev/null || true
pkill -TERM -f \
  "$HOME/PX4-Autopilot/build/px4_sitl_default/bin/px4" \
  2>/dev/null || true
pkill -TERM -f "gz sim" \
  2>/dev/null || true
pkill -TERM -f "gz-sim-server" \
  2>/dev/null || true
pkill -TERM -f "gz-sim-gui" \
  2>/dev/null || true
```

Check for leftovers:

```bash
pgrep -af \
  "px4|gz sim|gz-sim|image_bridge|yolo_car_detector.py|rqt_image_view"
```

For the complete recorded code and step-by-step experiment history, see Actual Simulation Record.
