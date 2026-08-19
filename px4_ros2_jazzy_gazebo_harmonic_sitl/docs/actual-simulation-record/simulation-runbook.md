---
description: >-
  Four-terminal daily startup procedure, car positioning, CPU tuning and clean
  shutdown for the recorded simulation.
---

# Simulation Runbook

This is the daily execution path. The source code itself is not repeated here; use the canonical files on the OpenCV and YOLO pages.

## Four-terminal startup

Do not run everything inside one terminal.

### Terminal 1 — Start PX4 and Gazebo

First ensure old simulation processes are not running:

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
```

Start PX4 with the depth-camera drone:

```bash
cd ~/PX4-Autopilot
make px4_sitl gz_x500_depth
```

Wait until `pxh>` appears.

Make sure Gazebo is open, Gazebo simulation is playing, the `x500_depth_0` drone appears, and the previously spawned car is visible in the Gazebo world.

Do not close this terminal.

### Terminal 2 — Find and bridge the Gazebo camera

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

Stop if the result is blank.

Confirm that Gazebo is publishing the image:

```bash
gz topic -i -t "$GZ_IMAGE_TOPIC"
```

Expected message type:

```
gz.msgs.Image
```

Start the image bridge:

```bash
ros2 run ros_gz_image image_bridge \
  "$GZ_IMAGE_TOPIC"
```

Leave this terminal running. Closing this terminal stops the camera bridge.

### Terminal 3 — Run YOLO detection

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

Confirm frames are arriving:

```bash
timeout 8 ros2 topic hz "$ROS_IMAGE_TOPIC"
```

A working stream prints `average rate: ...`.

Configure the detector:

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

Expected startup messages include:

```
Loading YOLO model: .../best.pt
Model task: detect
Model classes: ...
Input topic: /world/default/.../IMX214/image
Output topic: /vision/annotated
YOLO car detector is ready.
```

While frames are processed, the terminal should periodically print:

```
Received: ... | Processed: ... | Latest detections: ...
```

Leave this terminal running.

### Terminal 4 — View detection results

```bash
source /opt/ros/jazzy/setup.bash
ros2 topic list | grep vision
```

Expected:

```
/vision/annotated
```

Confirm annotated frames are being published:

```bash
timeout 10 ros2 topic hz /vision/annotated
```

Open the image viewer:

```bash
ros2 run rqt_image_view rqt_image_view
```

Select:

```
/vision/annotated
```

The display should contain the live Gazebo camera feed, YOLO class labels, confidence values, bounding boxes, and a status line showing the current detection count.

Do not select the original `/IMX214/image` topic when checking bounding boxes. That topic is the raw camera feed.

## Positioning the car for VisDrone detection

The model was trained using VisDrone aerial imagery. Therefore, camera perspective matters.

For the best chance of detection:

* Keep the complete car visible.
* Do not place the car extremely close to the camera.
* Avoid clipping part of the car outside the image.
* Use a realistic, textured car from Gazebo Fuel.
* Position the drone or car so the roof and full vehicle shape are visible.
* An elevated, slightly downward camera angle is closer to VisDrone imagery.
* Ensure the car is large enough to occupy a meaningful part of the image.
* Use daylight or clear simulated lighting.
* Avoid hiding the car behind another object.

The default confidence is intentionally set to:

```
0.15
```

After reliable detection, increase it to:

```bash
export YOLO_CONF="0.25"
```

Restart the detector after changing the value.

## CPU performance adjustment

The laptop is using CPU inference unless a compatible GPU environment is configured.

If the annotated stream is slow, stop the detector with Ctrl+C.

Use a smaller inference size:

```bash
export YOLO_IMGSZ="416"
```

Optionally process every second frame:

```bash
export PROCESS_EVERY_N_FRAMES="2"
```

Restart:

```bash
python3 \
  ~/px4_ros2_ws/aeronetra_cv/yolo_car_detector.py
```

Recommended CPU settings:

```bash
export YOLO_CONF="0.15"
export YOLO_IMGSZ="416"
export YOLO_DEVICE="cpu"
export PROCESS_EVERY_N_FRAMES="2"
```

These settings improve responsiveness but may reduce detection accuracy for small cars.

## Clean shutdown

Stop each active terminal with Ctrl+C.

Then clean remaining processes:

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

## Minimal daily reference

The complete daily procedure is above. Do not duplicate the commands here: use the four-terminal procedure as the single source of truth.
