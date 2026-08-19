---
description: >-
  Recorded camera-first verification procedure for the AeroNetra Gazebo IMX214
  camera and ROS 2 image bridge.
---

# Camera Verification

{% hint style="warning" %}
Do not run the Python detector until the Gazebo camera topic exists and the raw image is visible in ROS 2. This is the camera-first checkpoint used in the actual simulation.
{% endhint %}

## 1. Clean old processes

```bash
pkill -TERM -f "$HOME/PX4-Autopilot/build/px4_sitl_default/bin/px4" 2>/dev/null || true
pkill -TERM -f "gz sim" 2>/dev/null || true
pkill -TERM -f "gz-sim-server" 2>/dev/null || true
pkill -TERM -f "gz-sim-gui" 2>/dev/null || true
pkill -TERM -x MicroXRCEAgent 2>/dev/null || true
pkill -TERM -x image_bridge 2>/dev/null || true
pkill -TERM -x rqt_image_view 2>/dev/null || true
pkill -TERM -f "$HOME/px4_ros2_ws/cv_demo/simple_bbox.py" 2>/dev/null || true
sleep 3
```

Check for leftovers:

```bash
pgrep -af "px4|gz sim|gz-sim|MicroXRCEAgent|image_bridge|rqt_image_view|simple_bbox.py"
```

If nothing relevant appears, continue.

## 2. Verify required packages

```bash
deactivate 2>/dev/null || true
unset PYTHONPATH
unset VIRTUAL_ENV
source /opt/ros/jazzy/setup.bash
sudo apt update
sudo apt install -y \
  ros-jazzy-ros-gz-image \
  ros-jazzy-rqt-image-view \
  ros-jazzy-cv-bridge \
  python3-opencv
```

Verify:

```bash
ros2 pkg executables ros_gz_image
ros2 pkg executables rqt_image_view
python3 -c "
import cv2
import rclpy
from cv_bridge import CvBridge
print('OpenCV:', cv2.__version__)
print('ROS 2 Python and cv_bridge: OK')
"
```

## 3. Start the camera drone

```bash
cd ~/PX4-Autopilot
make px4_sitl gz_x500_depth
```

Wait until:

```
pxh>
```

appears. Ensure Gazebo is running by checking the Play ▶ control.

## 4. Find the Gazebo image topic

```bash
deactivate 2>/dev/null || true
unset PYTHONPATH
unset VIRTUAL_ENV
source /opt/ros/jazzy/setup.bash
GZ_IMAGE_TOPIC="$(gz topic -l | grep '/IMX214/image$' | head -n 1)"
echo "Gazebo image topic:"
echo "$GZ_IMAGE_TOPIC"
```

Expected:

```
/world/default/model/x500_depth_0/link/camera_link/sensor/IMX214/image
```

Confirm its type:

```bash
gz topic -i -t "$GZ_IMAGE_TOPIC"
```

You should see:

```
gz.msgs.Image
```

{% hint style="danger" %}
If `GZ_IMAGE_TOPIC` is blank, stop here. Do not run the Python detector.
{% endhint %}

## 5. Start the image bridge

```bash
ros2 run ros_gz_image image_bridge "$GZ_IMAGE_TOPIC"
```

Leave this terminal running.

## 6. Verify ROS 2 receives frames

```bash
deactivate 2>/dev/null || true
unset PYTHONPATH
unset VIRTUAL_ENV
source /opt/ros/jazzy/setup.bash
ROS_IMAGE_TOPIC="$(ros2 topic list | grep '/IMX214/image$' | head -n 1)"
echo "ROS image topic:"
echo "$ROS_IMAGE_TOPIC"
```

Inspect it:

```bash
ros2 topic info "$ROS_IMAGE_TOPIC" -v
```

Check that frames are arriving:

```bash
ros2 topic hz "$ROS_IMAGE_TOPIC"
```

You should eventually see:

```
average rate: ...
```

Stop only the frequency display with Ctrl+C.

## 7. View the raw camera

```bash
ros2 run rqt_image_view rqt_image_view
```

From the dropdown choose:

```
/world/default/model/x500_depth_0/link/camera_link/sensor/IMX214/image
```

At this checkpoint, you must see the raw drone-camera image. Do not continue until the raw feed works.

## Camera checkpoint

The verified path at this stage is:

```
Gazebo IMX214 camera
→ Gazebo image topic
→ ros_gz_image image_bridge
→ ROS 2 image topic
→ rqt_image_view
```
