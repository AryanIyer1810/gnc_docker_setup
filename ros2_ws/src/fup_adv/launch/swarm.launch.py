#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_swarm_nodes(context, *args, **kwargs):
    # Extract the actual integer value from the launch arguments
    num_drones_str = LaunchConfiguration('num_drones').perform(context)
    num_drones = int(num_drones_str)
    
    # Extract the control mode string
    control_mode = LaunchConfiguration('control_mode')

    nodes = []
    
    # Dynamically generate a node for each drone with its specific namespace
    for i in range(1, num_drones + 1):
        namespace = f'/px4_{i}'
        
        interface_node = Node(
            package='fup_adv',
            executable='drone_interface',
            namespace=namespace,
            name=f'drone_interface_{i}',
            parameters=[{'control_mode': control_mode}],
            output='screen',
            emulate_tty=True # Keeps the terminal output colored and readable
        )
        nodes.append(interface_node)

    return nodes

def generate_launch_description():
    return LaunchDescription([
        # Declare the arguments so they can be passed via command line
        DeclareLaunchArgument(
            'num_drones',
            default_value='4',
            description='Number of drone interface nodes to spawn'
        ),
        DeclareLaunchArgument(
            'control_mode',
            default_value='velocity',
            description='Mode for interface nodes: velocity or acceleration'
        ),
        # Run the Python loop to create the nodes
        OpaqueFunction(function=generate_swarm_nodes)
    ])
