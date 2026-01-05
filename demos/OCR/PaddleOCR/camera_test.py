import rclpy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

rclpy.init()
node = rclpy.create_node('camera_viewer')
bridge = CvBridge()

def callback(msg):
    frame = bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
    print(f"Received frame: {frame.shape}, timestamp: {msg.header.stamp}")
    # Optionally save: cv2.imwrite(f'frame_{msg.header.seq}.jpg', frame)

sub = node.create_subscription(Image, '/image_left_raw', callback, 10)

try:
    print("Listening to camera stream... Press Ctrl+C to stop")
    rclpy.spin(node)
except KeyboardInterrupt:
    pass
finally:
    node.destroy_node()
    rclpy.shutdown()
