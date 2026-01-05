#!/usr/bin/env python3
import os
from datetime import datetime

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
import cv2


OUTPUT_DIR = "/home/sunrise/rdk_model_zoo/demos/OCR/PaddleOCR/output"
TOPIC = "/image_left_raw"
TIMEOUT_SEC = 10.0


def rosimg_to_bgr(msg: Image):
    enc = (msg.encoding or "").lower()

    # Handle NV12 (Y plane + interleaved UV plane)
    if enc == "nv12":
        h, w = msg.height, msg.width
        expected = (h * w * 3) // 2
        buf = np.frombuffer(msg.data, dtype=np.uint8)

        if buf.size < expected:
            raise RuntimeError(f"NV12 buffer too small: got {buf.size}, expected {expected}")

        yuv = buf[:expected].reshape((h * 3 // 2, w))
        bgr = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_NV12)
        return bgr

    # If in future it publishes bgr8/rgb8 etc., handle here
    if enc in ("bgr8", "rgb8", "mono8"):
        h, w = msg.height, msg.width
        channels = 3 if enc in ("bgr8", "rgb8") else 1
        img = np.frombuffer(msg.data, dtype=np.uint8).reshape((h, w, channels)) if channels == 3 else \
              np.frombuffer(msg.data, dtype=np.uint8).reshape((h, w))
        if enc == "rgb8":
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        return img

    raise RuntimeError(f"Unsupported encoding: {msg.encoding}")


class OneShotSnap(Node):
    def __init__(self):
        super().__init__("one_shot_snapshot")
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        self.done = False
        self.create_subscription(Image, TOPIC, self.cb, qos_profile_sensor_data)
        self.get_logger().info(f"Waiting for 1 frame on: {TOPIC} (timeout {TIMEOUT_SEC}s)")

    def cb(self, msg: Image):
        if self.done:
            return

        frame_bgr = rosimg_to_bgr(msg)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        out_path = os.path.join(OUTPUT_DIR, f"snapshot_{ts}.jpg")
        if not cv2.imwrite(out_path, frame_bgr):
            raise RuntimeError(f"cv2.imwrite failed: {out_path}")

        self.get_logger().info(f"Saved: {out_path}  (encoding was: {msg.encoding})")
        self.done = True


def main():
    rclpy.init()
    node = OneShotSnap()
    start = node.get_clock().now()

    try:
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.2)
            elapsed = (node.get_clock().now() - start).nanoseconds / 1e9
            if elapsed > TIMEOUT_SEC:
                node.get_logger().error("Timeout: no image received (topic/QoS).")
                break
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
