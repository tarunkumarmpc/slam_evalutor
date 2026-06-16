import rclpy
from rclpy.serialization import serialize_message
import rosbag2_py
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped
import math
import numpy as np
import os
import shutil

def main():
    bag_path = 'test_bag'
    
    # Remove existing bag if it exists
    if os.path.exists(bag_path):
        shutil.rmtree(bag_path)

    writer = rosbag2_py.SequentialWriter()
    storage_options = rosbag2_py._storage.StorageOptions(
        uri=bag_path,
        storage_id='sqlite3'
    )
    converter_options = rosbag2_py._storage.ConverterOptions('', '')
    writer.open(storage_options, converter_options)
    
    try:
        topic_info_gt = rosbag2_py._storage.TopicMetadata(
            id=1,
            name='/slam/gt_path',
            type='nav_msgs/msg/Path',
            serialization_format='cdr'
        )
    except TypeError:
        topic_info_gt = rosbag2_py._storage.TopicMetadata(
            name='/slam/gt_path',
            type='nav_msgs/msg/Path',
            serialization_format='cdr'
        )
    writer.create_topic(topic_info_gt)

    try:
        topic_info_slam = rosbag2_py._storage.TopicMetadata(
            id=2,
            name='/slam/path',
            type='nav_msgs/msg/Path',
            serialization_format='cdr'
        )
    except TypeError:
        topic_info_slam = rosbag2_py._storage.TopicMetadata(
            name='/slam/path',
            type='nav_msgs/msg/Path',
            serialization_format='cdr'
        )
    writer.create_topic(topic_info_slam)
    
    # 30 seconds at 10Hz = 300 points
    num_points = 300
    t_vals = np.linspace(0, 2*np.pi, num_points)
    
    gt_path = Path()
    gt_path.header.frame_id = "map"
    
    slam_path = Path()
    slam_path.header.frame_id = "map"
    
    for i, t in enumerate(t_vals):
        # Figure 8 (Lemniscate of Bernoulli)
        a = 5.0
        x = (a * math.sqrt(2) * math.cos(t)) / (math.sin(t)**2 + 1)
        y = (a * math.sqrt(2) * math.cos(t) * math.sin(t)) / (math.sin(t)**2 + 1)
        
        # Add noise for SLAM
        noise_x = np.random.normal(0, 0.1)
        noise_y = np.random.normal(0, 0.1)
        
        # Current time in nanoseconds
        timestamp_ns = i * 100000000  # 0.1s increments
        
        pose_gt = PoseStamped()
        pose_gt.header.frame_id = "map"
        pose_gt.header.stamp.sec = i // 10
        pose_gt.header.stamp.nanosec = (i % 10) * 100000000
        pose_gt.pose.position.x = x
        pose_gt.pose.position.y = y
        pose_gt.pose.position.z = 0.0
        pose_gt.pose.orientation.w = 1.0
        
        pose_slam = PoseStamped()
        pose_slam.header.frame_id = "map"
        pose_slam.header.stamp.sec = i // 10
        pose_slam.header.stamp.nanosec = (i % 10) * 100000000
        pose_slam.pose.position.x = x + noise_x
        pose_slam.pose.position.y = y + noise_y
        pose_slam.pose.position.z = np.random.normal(0, 0.05)
        pose_slam.pose.orientation.w = 1.0
        
        gt_path.poses.append(pose_gt)
        slam_path.poses.append(pose_slam)
        
        # Write to bag
        writer.write(
            '/slam/gt_path',
            serialize_message(gt_path),
            timestamp_ns
        )
        writer.write(
            '/slam/path',
            serialize_message(slam_path),
            timestamp_ns
        )
        
    print(f"Created {bag_path} successfully.")

if __name__ == '__main__':
    main()
