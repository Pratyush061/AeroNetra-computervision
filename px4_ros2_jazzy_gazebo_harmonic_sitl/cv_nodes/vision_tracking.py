#!/usr/bin/env python3

import cv2
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image


class VisionTrackingNode(Node):
    CALIBRATION_FRAMES = 90
    MIN_CONTOUR_AREA = 600.0

    def __init__(self) -> None:
        super().__init__("vision_tracking_node")
        self.bridge = CvBridge()
        self.frame_number = 0
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=self.CALIBRATION_FRAMES,
            varThreshold=25,
            detectShadows=False,
        )
        self.create_subscription(
            Image,
            "camera_image",
            self.process_image,
            qos_profile_sensor_data,
        )
        self.annotated_publisher = self.create_publisher(
            Image,
            "/vision/annotated",
            qos_profile_sensor_data,
        )
        self.get_logger().info(
            "Vision tracker started. Keep scene empty during calibration."
        )

    def process_image(self, message: Image) -> None:
        try:
            frame = self.bridge.imgmsg_to_cv2(
                message,
                desired_encoding="bgr8",
            )
        except Exception as error:
            self.get_logger().error(f"Image conversion failed: {error}")
            return

        self.frame_number += 1
        image_height, image_width = frame.shape[:2]
        image_area = image_height * image_width

        if self.frame_number <= self.CALIBRATION_FRAMES:
            foreground_mask = self.background_subtractor.apply(
                frame,
                learningRate=0.05,
            )
            status = (
                f"CALIBRATING {self.frame_number}/"
                f"{self.CALIBRATION_FRAMES}"
            )
            status_colour = (0, 165, 255)
        else:
            foreground_mask = self.background_subtractor.apply(
                frame,
                learningRate=0.0,
            )
            _, foreground_mask = cv2.threshold(
                foreground_mask,
                200,
                255,
                cv2.THRESH_BINARY,
            )
            open_kernel = cv2.getStructuringElement(
                cv2.MORPH_ELLIPSE,
                (5, 5),
            )
            close_kernel = cv2.getStructuringElement(
                cv2.MORPH_RECT,
                (15, 15),
            )
            foreground_mask = cv2.morphologyEx(
                foreground_mask,
                cv2.MORPH_OPEN,
                open_kernel,
                iterations=1,
            )
            foreground_mask = cv2.morphologyEx(
                foreground_mask,
                cv2.MORPH_CLOSE,
                close_kernel,
                iterations=2,
            )
            contours, _ = cv2.findContours(
                foreground_mask,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE,
            )
            valid_contours = []
            for contour in contours:
                contour_area = cv2.contourArea(contour)
                if contour_area < self.MIN_CONTOUR_AREA:
                    continue
                x, y, box_width, box_height = cv2.boundingRect(contour)
                box_area = box_width * box_height
                if box_area > image_area * 0.80:
                    continue
                valid_contours.append(contour)

            if valid_contours:
                largest_contour = max(
                    valid_contours,
                    key=cv2.contourArea,
                )
                x, y, box_width, box_height = cv2.boundingRect(
                    largest_contour
                )
                centre_x = x + box_width // 2
                centre_y = y + box_height // 2

                if centre_x < image_width / 3:
                    horizontal_position = "LEFT"
                elif centre_x > (2 * image_width) / 3:
                    horizontal_position = "RIGHT"
                else:
                    horizontal_position = "CENTRE"

                box_area_ratio = (
                    box_width * box_height
                ) / image_area
                if box_area_ratio < 0.05:
                    distance_hint = "FAR"
                elif box_area_ratio < 0.20:
                    distance_hint = "MEDIUM"
                else:
                    distance_hint = "CLOSE"

                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + box_width, y + box_height),
                    (0, 255, 0),
                    4,
                )
                cv2.circle(
                    frame,
                    (centre_x, centre_y),
                    7,
                    (0, 0, 255),
                    -1,
                )
                cv2.line(
                    frame,
                    (image_width // 2, 0),
                    (image_width // 2, image_height),
                    (255, 0, 0),
                    2,
                )
                cv2.putText(
                    frame,
                    f"Position: {horizontal_position}",
                    (x, max(30, y - 55)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )
                cv2.putText(
                    frame,
                    f"Centre: ({centre_x}, {centre_y})",
                    (x, max(30, y - 30)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 255, 0),
                    2,
                )
                cv2.putText(
                    frame,
                    f"Size: {box_width}x{box_height} | {distance_hint}",
                    (x, max(30, y - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 255, 0),
                    2,
                )
                status = "OBJECT TRACKED"
                status_colour = (0, 255, 0)
                self.get_logger().info(
                    f"Object {horizontal_position} | "
                    f"centre=({centre_x}, {centre_y}) | "
                    f"size={box_width}x{box_height} | "
                    f"distance={distance_hint}"
                )
            else:
                status = "READY - INSERT OBJECT"
                status_colour = (0, 255, 255)

        cv2.rectangle(
            frame,
            (8, 8),
            (min(image_width - 8, 620), 48),
            (0, 0, 0),
            -1,
        )
        cv2.putText(
            frame,
            status,
            (18, 36),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            status_colour,
            2,
        )

        try:
            output = self.bridge.cv2_to_imgmsg(
                frame,
                encoding="bgr8",
            )
            output.header = message.header
            self.annotated_publisher.publish(output)
        except Exception as error:
            self.get_logger().error(
                f"Annotated image publishing failed: {error}"
            )


def main() -> None:
    rclpy.init()
    node = VisionTrackingNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
