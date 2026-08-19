---
description: >-
  Recorded VisDrone-trained YOLO car detector setup, dependencies, model checks
  and complete ROS 2 implementation.
---

# YOLO Car Detector

## Environment

The setup was tested with:

* Ubuntu 24.04 Noble
* ROS 2 Jazzy
* PX4 SITL
* Gazebo Sim
* PX4 vehicle: `gz_x500_depth`
* Camera sensor: IMX214
* YOLO model: VisDrone-trained `best.pt`
* Visualization: `rqt_image_view`

The car model is manually inserted into Gazebo using Resource Spawner.

QGroundControl is not required. Micro XRCE-DDS Agent is not required for this camera-only computer-vision test. It may be started separately later when PX4 telemetry or ROS 2 flight-control topics are needed.

## Folder structure

```
~/PX4-Autopilot/
~/px4_ros2_ws/
├── models/
│   └── best.pt
├── aeronetra_cv/
│   └── yolo_car_detector.py
└── yolo_venv/
```

Confirm the model exists:

```bash
ls -lh ~/px4_ros2_ws/models/best.pt
```

## One-time dependency installation

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

Verify the ROS packages:

```bash
source /opt/ros/jazzy/setup.bash
ros2 pkg executables ros_gz_image
ros2 pkg executables rqt_image_view
```

Expected output should include:

```
ros_gz_image image_bridge
rqt_image_view rqt_image_view
```

## One-time Python environment setup

```bash
cd ~/px4_ros2_ws
python3 -m venv --system-site-packages yolo_venv
source ~/px4_ros2_ws/yolo_venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install ultralytics
```

Test that the required modules load:

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

Test the trained model:

```bash
python3 - <<'PY'
from ultralytics import YOLO
model_path =
"/home/pratyush-jain/px4_ros2_ws/models/best.pt"
model = YOLO(model_path)
print("MODEL LOAD: SUCCESS")
print("Task:", model.task)
print("Classes:", model.names)
PY
```

The task should normally be:

```
detect
```

The printed classes should contain your VisDrone classes, including car if it was included during training.

Deactivate the environment after the test:

```bash
deactivate
```

## Complete YOLO ROS 2 detector — recorded code

Create the folder:

```bash
mkdir -p ~/px4_ros2_ws/aeronetra_cv
```

Create the detector:

```bash
cat > ~/px4_ros2_ws/aeronetra_cv/yolo_car_detector.py <<'PY'
```

Replace the file with:

```python
#!/usr/bin/env python3
import os
import time
from pathlib import Path
import cv2
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from ultralytics import YOLO


class YoloCarDetector(Node):
    """Run a trained YOLO model on a ROS 2 camera
    image stream."""

    def __init__(self) -> None:
        super().__init__("yolo_car_detector")
        self.input_topic = os.environ.get(
            "IMAGE_TOPIC",
            (
                "/world/default/model/x500_depth_0/link/"
                "camera_link/sensor/IMX214/image"
            ),
        )
        self.output_topic = os.environ.get(
            "OUTPUT_TOPIC",
            "/vision/annotated",
        )
        self.model_path = os.environ.get(
            "YOLO_MODEL",
            "/home/pratyush-jain/px4_ros2_ws/models/best.pt",
        )
        self.confidence = float(
            os.environ.get("YOLO_CONF", "0.15")
        )
        self.image_size = int(
            os.environ.get("YOLO_IMGSZ", "640")
        )
        self.device = os.environ.get(
            "YOLO_DEVICE",
            "cpu",
        )
        self.process_every_n_frames = max(
            1,
            int(os.environ.get("PROCESS_EVERY_N_FRAMES", "1")),
        )

        model_file = Path(self.model_path).expanduser()
        if not model_file.is_file():
            raise FileNotFoundError(
                f"YOLO model was not found: {model_file}"
            )

        self.get_logger().info(
            f"Loading YOLO model: {model_file}"
        )
        self.model = YOLO(str(model_file))
        self.bridge = CvBridge()
        self.received_frames = 0
        self.processed_frames = 0
        self.last_log_time = time.monotonic()

        self.subscription = self.create_subscription(
            Image,
            self.input_topic,
            self.image_callback,
            qos_profile_sensor_data,
        )
        self.annotated_publisher = self.create_publisher(
            Image,
            self.output_topic,
            qos_profile_sensor_data,
        )

        self.get_logger().info(
            f"Model task: {self.model.task}"
        )
        self.get_logger().info(
            f"Model classes: {self.model.names}"
        )
        self.get_logger().info(
            f"Input topic: {self.input_topic}"
        )
        self.get_logger().info(
            f"Output topic: {self.output_topic}"
        )
        self.get_logger().info(
            f"Confidence threshold: {self.confidence}"
        )
        self.get_logger().info(
            f"Inference image size: {self.image_size}"
        )
        self.get_logger().info(
            f"Inference device: {self.device}"
        )
        self.get_logger().info(
            "YOLO car detector is ready."
        )

    def image_callback(self, message: Image) -> None:
        self.received_frames += 1
        if (
            self.received_frames
            % self.process_every_n_frames
            != 0
        ):
            return

        try:
            frame = self.bridge.imgmsg_to_cv2(
                message,
                desired_encoding="bgr8",
            )
            results = self.model.predict(
                source=frame,
                conf=self.confidence,
                imgsz=self.image_size,
                device=self.device,
                verbose=False,
            )
            result = results[0]
            annotated_frame = result.plot()
            detection_count = 0
            if result.boxes is not None:
                detection_count = len(result.boxes)

            # Add a visible status line so it is obvious that the
            # annotated ROS topic is being viewed.
            status = (
                f"Detections: {detection_count} | "
                f"Confidence: {self.confidence:.2f}"
            )
            cv2.rectangle(
                annotated_frame,
                (8, 8),
                (520, 46),
                (0, 0, 0),
                -1,
            )
            cv2.putText(
                annotated_frame,
                status,
                (18, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 255),
                2,
                cv2.LINE_AA,
            )

            output_message = self.bridge.cv2_to_imgmsg(
                annotated_frame,
                encoding="bgr8",
            )
            output_message.header = message.header
            self.annotated_publisher.publish(output_message)
            self.processed_frames += 1

            current_time = time.monotonic()
            if current_time - self.last_log_time >= 2.0:
                self.get_logger().info(
                    f"Received: {self.received_frames} | "
                    f"Processed: {self.processed_frames} | "
                    f"Latest detections: {detection_count}"
                )
                self.last_log_time = current_time
        except Exception as error:
            self.get_logger().error(
                f"YOLO processing failed: {error}"
            )


def main(args=None) -> None:
    rclpy.init(args=args)
    node = None
    try:
        node = YoloCarDetector()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as error:
        print(f"Detector startup failed: {error}")
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
PY
```

Make it executable:

```bash
chmod +x \
  ~/px4_ros2_ws/aeronetra_cv/yolo_car_detector.py
```

Verify Python syntax:

```bash
source /opt/ros/jazzy/setup.bash
source ~/px4_ros2_ws/yolo_venv/bin/activate
python3 -m py_compile \
  ~/px4_ros2_ws/aeronetra_cv/yolo_car_detector.py
```

No output means the syntax is valid.

## Model-to-output flow

```
ROS 2 camera image
→ cv_bridge
→ YOLO best.pt
→ bounding boxes and labels
→ /vision/annotated
```
