#!/usr/bin/env python3
"""
CG_camera_handler.py - Camera Capture Handler using ROS2

This module handles capturing images from the MIPI stereo camera
on the RDK X5 kit using ROS2 topics.

IMPORTANT: Before using this module, start the camera in a separate terminal:
    source /opt/tros/humble/setup.bash
    export ROS_LOCALHOST_ONLY=1
    ros2 daemon stop
    ros2 launch mipi_cam mipi_cam_dual_channel.launch.py

Target Platform: RDK X5 Kit (4GB RAM, Ubuntu 22.04 ARM64)
"""

import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Global ROS2 flag
_ros2_initialized = False


def init_ros2():
    """Initialize ROS2 if not already done."""
    global _ros2_initialized
    if not _ros2_initialized:
        try:
            import rclpy
            if not rclpy.ok():
                rclpy.init()
            _ros2_initialized = True
            return True
        except Exception as e:
            print(f"[CAMERA] ❌ Failed to initialize ROS2: {e}")
            return False
    return True


def shutdown_ros2():
    """Shutdown ROS2."""
    global _ros2_initialized
    if _ros2_initialized:
        try:
            import rclpy
            if rclpy.ok():
                rclpy.shutdown()
            _ros2_initialized = False
        except:
            pass


def rosimg_to_bgr(msg):
    """
    Convert ROS Image message to BGR numpy array.
    
    Handles NV12 encoding from MIPI camera.
    """
    import numpy as np
    import cv2
    
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
    
    # Handle other encodings
    if enc in ("bgr8", "rgb8", "mono8"):
        h, w = msg.height, msg.width
        channels = 3 if enc in ("bgr8", "rgb8") else 1
        
        if channels == 3:
            img = np.frombuffer(msg.data, dtype=np.uint8).reshape((h, w, channels))
        else:
            img = np.frombuffer(msg.data, dtype=np.uint8).reshape((h, w))
        
        if enc == "rgb8":
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        return img
    
    raise RuntimeError(f"Unsupported encoding: {msg.encoding}")


def capture_image(
    output_path: Optional[str] = None,
    topic: str = "/image_left_raw",
    timeout_sec: float = 10.0
) -> Optional[str]:
    """
    Capture a single image from the stereo camera.
    
    Args:
        output_path: Path to save the image (auto-generated if None)
        topic: ROS2 topic name
        timeout_sec: Timeout in seconds
        
    Returns:
        Path to saved image or None on failure
    """
    try:
        import rclpy
        from rclpy.node import Node
        from rclpy.qos import qos_profile_sensor_data
        from sensor_msgs.msg import Image
        import cv2
        
        from CG_config import OUTPUT_DIR, SNAPSHOT_PREFIX
        
        # Initialize ROS2
        if not init_ros2():
            return None
        
        # Generate output path if not provided
        if output_path is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(OUTPUT_DIR / f"{SNAPSHOT_PREFIX}{ts}.jpg")
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Capture node
        class SnapshotNode(Node):
            def __init__(self):
                super().__init__("caregiver_snapshot")
                self.image_data = None
                self.done = False
                self.create_subscription(
                    Image, topic, self.callback, qos_profile_sensor_data
                )
                self.get_logger().info(f"Waiting for image on {topic}")
            
            def callback(self, msg):
                if not self.done:
                    self.image_data = msg
                    self.done = True
        
        # Create node and wait for image
        node = SnapshotNode()
        start_time = time.time()
        
        try:
            while rclpy.ok() and not node.done:
                rclpy.spin_once(node, timeout_sec=0.2)
                
                if time.time() - start_time > timeout_sec:
                    print(f"[CAMERA] ❌ Timeout: no image received after {timeout_sec}s")
                    return None
            
            if node.image_data:
                # Convert and save image
                frame_bgr = rosimg_to_bgr(node.image_data)
                
                if cv2.imwrite(output_path, frame_bgr):
                    print(f"[CAMERA] ✅ Saved: {output_path}")
                    return output_path
                else:
                    print(f"[CAMERA] ❌ Failed to save image")
                    return None
        finally:
            node.destroy_node()
        
    except Exception as e:
        print(f"[CAMERA] ❌ Error: {e}")
        return None


def capture_image_subprocess(output_path: Optional[str] = None) -> Optional[str]:
    """
    Alternative: Capture image using subprocess call to camera_snapshot_once.py
    
    This method uses less memory by running capture in a separate process.
    
    Args:
        output_path: Path to save the image (uses default if None)
        
    Returns:
        Path to saved image or None on failure
    """
    try:
        from CG_config import BASE_DIR, OUTPUT_DIR, SNAPSHOT_PREFIX
        
        # Run the capture script
        script_path = BASE_DIR / "camera_snapshot_once.py"
        
        cmd = f"source /opt/tros/humble/setup.bash && export ROS_LOCALHOST_ONLY=1 && python3 {script_path}"
        
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=15,
            executable="/bin/bash"
        )
        
        if result.returncode == 0:
            # Find the most recent snapshot
            import glob
            snapshots = sorted(
                glob.glob(str(OUTPUT_DIR / "snapshot_*.jpg")),
                key=os.path.getmtime,
                reverse=True
            )
            
            if snapshots:
                latest = snapshots[0]
                
                # Rename if output_path specified
                if output_path:
                    import shutil
                    shutil.move(latest, output_path)
                    print(f"[CAMERA] ✅ Saved: {output_path}")
                    return output_path
                else:
                    print(f"[CAMERA] ✅ Saved: {latest}")
                    return latest
        
        print(f"[CAMERA] ❌ Capture failed: {result.stderr}")
        return None
        
    except subprocess.TimeoutExpired:
        print("[CAMERA] ❌ Capture timed out")
        return None
    except Exception as e:
        print(f"[CAMERA] ❌ Error: {e}")
        return None


def get_latest_image() -> Optional[str]:
    """
    Get the path to the most recent captured image.
    
    Returns:
        Path to latest image or None
    """
    try:
        from CG_config import OUTPUT_DIR
        import glob
        
        # Look for prescription images first, then snapshots
        patterns = [
            str(OUTPUT_DIR / "prescription_*.jpg"),
            str(OUTPUT_DIR / "snapshot_*.jpg")
        ]
        
        all_images = []
        for pattern in patterns:
            all_images.extend(glob.glob(pattern))
        
        if all_images:
            latest = max(all_images, key=os.path.getmtime)
            return latest
        
        return None
        
    except Exception as e:
        print(f"[CAMERA] ❌ Error finding latest image: {e}")
        return None


def check_camera_available() -> bool:
    """
    Check if the camera ROS2 topic is available.
    
    Returns:
        True if camera topic is publishing
    """
    try:
        result = subprocess.run(
            "source /opt/tros/humble/setup.bash && ros2 topic list",
            shell=True,
            capture_output=True,
            text=True,
            timeout=5,
            executable="/bin/bash"
        )
        
        from CG_config import CAMERA_TOPIC
        return CAMERA_TOPIC in result.stdout
        
    except Exception:
        return False


# ============================================================
# TEST FUNCTION
# ============================================================
def test_camera_handler():
    """Test camera capture."""
    print("=" * 50)
    print("📷 Camera Handler Test")
    print("=" * 50)
    
    print("\n[TEST] Checking camera availability...")
    if check_camera_available():
        print("[TEST] ✅ Camera topic is available")
        
        print("\n[TEST] Capturing image...")
        image_path = capture_image()
        
        if image_path:
            print(f"[TEST] ✅ Image captured: {image_path}")
        else:
            print("[TEST] ❌ Failed to capture image")
    else:
        print("[TEST] ❌ Camera topic not found")
        print("[TEST] Please start the camera first:")
        print("       source /opt/tros/humble/setup.bash")
        print("       ros2 launch mipi_cam mipi_cam_dual_channel.launch.py")
    
    print("\n[TEST] Camera test complete!")


if __name__ == "__main__":
    test_camera_handler()
