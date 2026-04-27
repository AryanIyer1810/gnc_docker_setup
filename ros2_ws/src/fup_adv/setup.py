from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'fup_adv'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Grab ALL RViz and YAML config files
        (os.path.join('share', package_name, 'config'), glob('config/*.rviz')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        # Uniformly grab all launch files (covers consensus, depth, and swarm!)
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='shashi',
    maintainer_email='shashi@todo.todo',
    description='Advanced GNC and Consensus Package',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'attitude_control = fup_adv.attitude_controller:main',
            'velocity_control = fup_adv.velocity_controller:main',
            'acceleration_control = fup_adv.acceleration_controller:main',
            'motor_control = fup_adv.motor_controller:main',
            'waypoint_follower = fup_adv.waypoint_follower:main',
            'qgc_waypoint_follower = fup_adv.qgc_waypoint_follower:main',
            'drone_interface = fup_adv.drone_interface:main',
            # -- Absorbed Consensus Scripts --
            'first_order_consensus = fup_adv.first_order_consensus:main',
            'olfati_saber_flocking = fup_adv.olfati_saber_flocking:main'
        ],
    },
)
