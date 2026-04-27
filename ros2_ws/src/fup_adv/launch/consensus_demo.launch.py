from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, PythonExpression
from launch.conditions import IfCondition
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def IfEq(lc, target):
    return IfCondition(PythonExpression(["'", lc, "' == '", target, "'"]))

def generate_launch_description():
    variant = LaunchConfiguration('variant')
    pkg = FindPackageShare('fup_adv')
    first_params  = PathJoinSubstitution([pkg, 'config', 'first_order.yaml'])
    olfati_params = PathJoinSubstitution([pkg, 'config', 'olfati_saber.yaml'])
    return LaunchDescription([
        DeclareLaunchArgument('variant', default_value='first_order'),
        Node(package='fup_adv', executable='first_order_consensus',
             name='first_order_consensus', output='screen',
             parameters=[first_params],
             condition=IfEq(variant, 'first_order')),
        Node(package='fup_adv', executable='olfati_saber_flocking',
             name='olfati_saber_flocking', output='screen',
             parameters=[olfati_params],
             condition=IfEq(variant, 'olfati')),
    ])
