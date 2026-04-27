from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Get the path to the fup_adv share directory
    pkg_share = get_package_share_directory('fup_adv')
    
    # Define the exact path to the RViz config file
    rviz_config_path = os.path.join(pkg_share, 'config', 'depth_cam.rviz')

    return LaunchDescription([
        # 1. Run your Velocity Controller Node
        Node(
            package='fup_adv',
            executable='waypoint_follower',
            name='waypoint_follower',
            output='screen'
        ),

        # 2. Bridge the RGB Camera Image
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='camera_bridge',
            arguments=[
                '/camera@sensor_msgs/msg/Image[gz.msgs.Image',
                '/depth_camera/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked',
                '/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo'
            ],
            output='screen'
        ),

        # 5. Static Transform Publisher
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='camera_static_tf',
            arguments=[
                '--x', '0.1', '--y', '0.0', '--z', '0.0',
                '--roll', '-1.5708', '--pitch', '0.0', '--yaw', '-1.5708',
                '--frame-id', 'base_link',
                '--child-frame-id', 'x500_depth_0/OakD-Lite/base_link/StereoOV7251'
            ],
            output='screen'
        ),

        # 6. Launch RViz2 WITH the Config File
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config_path],
            output='screen'
        )
    ])
