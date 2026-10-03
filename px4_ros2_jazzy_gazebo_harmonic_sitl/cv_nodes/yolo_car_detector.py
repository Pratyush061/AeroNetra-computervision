#!/usr/bin/env python3
"""Run a VisDrone-trained YOLO model on a ROS 2 camera image stream.

Input topic, output topic, model path and inference settings are all read from
environment variables so the node can be retargeted without editing the file:

    IMAGE_TOPIC            (default: gz_x500_depth IMX214 image topic)
    OUTPUT_TOPIC           (default: /vision/annotated)
    YOLO_MODEL             (default: ~/px4_ros2_ws/models/best.pt)
    YOLO_CONF              (default: 0.15)
    YOLO_IMGSZ             (default: 640)
    YOLO_DEVICE            (default: cpu)
    PROCESS_EVERY_N_FRAMES (default: 1)
"""

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

DEFAULT_IMAGE_TOPIC = (
    "/world/default/model/x500_depth_0/link/"
    "camera_link/sensor/IMX214/image"
)


class YoloCarDetector(Node):
    """Run a trained YOLO model on a ROS 2 camera image stream."""

    def __init__(self) -> None:
        super().__init__("yolo_car_detector")
        self.input_topic = os.environ.get("IMAGE_TOPIC", DEFAULT_IMAGE_TOPIC)
        self.output_topic = os.environ.get("OUTPUT_TOPIC", "/vision/annotated")
        self.model_path = os.environ.get(
            "YOLO_MODEL",
            "~/px4_ros2_ws/models/best.pt",
        )
        self.confidence = float(os.environ.get("YOLO_CONF", "0.15"))
        self.image_size = int(os.environ.get("YOLO_IMGSZ", "640"))
        self.device = os.environ.get("YOLO_DEVICE", "cpu")
        self.process_every_n_frames = max(
            1,
            int(os.environ.get("PROCESS_EVERY_N_FRAMES", "1")),
        )

        model_file = Path(self.model_path).expanduser()
        if not model_file.is_file():
            raise FileNotFoundError(
                f"YOLO model was not found: {model_file}"
            )

        self.get_logger().info(f"Loading YOLO model: {model_file}")
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

        self.get_logger().info(f"Model task: {self.model.task}")
        self.get_logger().info(f"Model classes: {self.model.names}")
        self.get_logger().info(f"Input topic: {self.input_topic}")
        self.get_logger().info(f"Output topic: {self.output_topic}")
        self.get_logger().info(f"Confidence threshold: {self.confidence}")
        self.get_logger().info(f"Inference image size: {self.image_size}")
        self.get_logger().info(f"Inference device: {self.device}")
        self.get_logger().info("YOLO car detector is ready.")

    def image_callback(self, message: Image) -> None:
        self.received_frames += 1
        if self.received_frames % self.process_every_n_frames != 0:
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

            # A visible status line proves the annotated topic is being viewed.
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
        except Exception as error:  # noqa: BLE001 - keep the node alive on a bad frame
            self.get_logger().error(f"YOLO processing failed: {error}")


def main(args=None) -> None:
    rclpy.init(args=args)
    node = None
    try:
        node = YoloCarDetector()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as error:  # noqa: BLE001 - report startup failure clearly
        print(f"Detector startup failed: {error}")
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
