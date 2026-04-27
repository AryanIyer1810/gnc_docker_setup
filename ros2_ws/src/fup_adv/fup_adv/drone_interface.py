#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy

from px4_msgs.msg import VehicleLocalPosition, VehicleStatus
from px4_msgs.msg import VehicleCommand, OffboardControlMode, TrajectorySetpoint
from geometry_msgs.msg import Twist, Accel, PoseStamped
from nav_msgs.msg import Path

import numpy as np

class DroneInterfaceNode(Node):
    def __init__(self):
        super().__init__('drone_interface')

        # --- Dynamic ROS 2 Parameters ---
        self.declare_parameter('control_mode', 'velocity') # Options: 'velocity' or 'acceleration'
        self.control_mode = self.get_parameter('control_mode').get_parameter_value().string_value

        # --- Parameters ---
        self.target_altitude = -2.0  
        self.alt_kp = 1.0  # P-gain for Velocity Z-hold
        self.alt_kd = 0.5  # D-gain for Acceleration Z-hold
        
        # --- State Variables ---
        self.current_pos = np.array([0.0, 0.0, 0.0])
        self.current_vel = np.array([0.0, 0.0, 0.0])
        self.cmd_input = np.array([0.0, 0.0]) # Stores either [Vx, Vy] or [Ax, Ay] depending on mode
        
        self.vehicle_status = VehicleStatus()
        self.offboard_setpoint_counter = 0
        self.takeoff_complete = False

        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        # --- Subscribers ---
        self.pos_sub = self.create_subscription(
            VehicleLocalPosition, 'fmu/out/vehicle_local_position', self.pos_callback, qos_profile)
        self.status_sub = self.create_subscription(
            VehicleStatus, 'fmu/out/vehicle_status', self.status_callback, qos_profile)
        
        # Listen to BOTH command topics, but we only act on the one matching our mode
        self.cmd_vel_sub = self.create_subscription(Twist, 'cmd_vel', self.cmd_vel_callback, 10)
        self.cmd_accel_sub = self.create_subscription(Accel, 'cmd_accel', self.cmd_accel_callback, 10)

        # --- Publishers ---
        self.offboard_control_mode_publisher = self.create_publisher(
            OffboardControlMode, 'fmu/in/offboard_control_mode', qos_profile)
        self.trajectory_setpoint_publisher = self.create_publisher(
            TrajectorySetpoint, 'fmu/in/trajectory_setpoint', qos_profile)
        self.vehicle_command_publisher = self.create_publisher(
            VehicleCommand, 'fmu/in/vehicle_command', qos_profile)
        
        self.path_pub = self.create_publisher(Path, 'rviz/path', 10)
        self.path_msg = Path()

        self.timer = self.create_timer(0.05, self.timer_callback)
        self.get_logger().info(f"Interface Initialized in {self.control_mode.upper()} mode.")

    def status_callback(self, msg):
        self.vehicle_status = msg

    def pos_callback(self, msg):
        self.current_pos = np.array([msg.x, msg.y, msg.z])
        self.current_vel = np.array([msg.vx, msg.vy, msg.vz]) # Needed for acceleration damping
        
        # RViz Path
        self.path_msg.header.frame_id = "map"
        self.path_msg.header.stamp = self.get_clock().now().to_msg()
        pose = PoseStamped()
        pose.header = self.path_msg.header
        pose.pose.position.x = msg.y  
        pose.pose.position.y = msg.x  
        pose.pose.position.z = -msg.z 
        
        self.path_msg.poses.append(pose)
        if len(self.path_msg.poses) > 500:
            self.path_msg.poses.pop(0)
        self.path_pub.publish(self.path_msg)

    def cmd_vel_callback(self, msg):
        if self.control_mode == 'velocity':
            self.cmd_input[0] = msg.linear.x 
            self.cmd_input[1] = msg.linear.y

    def cmd_accel_callback(self, msg):
        if self.control_mode == 'acceleration':
            self.cmd_input[0] = msg.linear.x 
            self.cmd_input[1] = msg.linear.y

    def arm(self):
        self.publish_vehicle_command(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, param1=1.0)
        self.get_logger().info('Arm command sent')

    def engage_offboard_mode(self):
        self.publish_vehicle_command(VehicleCommand.VEHICLE_CMD_DO_SET_MODE, param1=1.0, param2=6.0)
        self.get_logger().info("Switching to offboard mode")

    def publish_vehicle_command(self, command, **params):
        msg = VehicleCommand()
        msg.command = command
        msg.param1 = params.get("param1", 0.0)
        msg.param2 = params.get("param2", 0.0)
        msg.target_system = 1
        msg.target_component = 1
        msg.source_system = 1
        msg.source_component = 1
        msg.from_external = True
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        self.vehicle_command_publisher.publish(msg)

    def timer_callback(self):
        if self.offboard_setpoint_counter == 10:
            self.engage_offboard_mode()
            self.arm()
        if self.offboard_setpoint_counter < 11:
            self.offboard_setpoint_counter += 1

        # Phase 1: Takeoff
        if not self.takeoff_complete:
            msg = OffboardControlMode()
            msg.position = True
            msg.velocity = False
            msg.acceleration = False
            msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
            self.offboard_control_mode_publisher.publish(msg)

            setpoint = TrajectorySetpoint()
            setpoint.position = [0.0, 0.0, self.target_altitude]
            setpoint.yaw = 0.0
            setpoint.timestamp = int(self.get_clock().now().nanoseconds / 1000)
            self.trajectory_setpoint_publisher.publish(setpoint)

            if self.current_pos[2] < (self.target_altitude + 0.2):
                self.get_logger().info(f"Takeoff complete. Awaiting {self.control_mode} commands.")
                self.takeoff_complete = True
                
        # Phase 2: Follow Algorithm Commands
        else:
            msg = OffboardControlMode()
            msg.position = False
            msg.velocity = (self.control_mode == 'velocity')
            msg.acceleration = (self.control_mode == 'acceleration')
            msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
            self.offboard_control_mode_publisher.publish(msg)

            setpoint = TrajectorySetpoint()
            setpoint.position = [float('nan'), float('nan'), float('nan')]
            setpoint.yaw = 0.0

            z_err = self.current_pos[2] - self.target_altitude

            if self.control_mode == 'velocity':
                # P-Controller for Altitude Velocity
                v_z = -self.alt_kp * z_err 
                v_z = np.clip(v_z, -1.5, 1.5)
                
                setpoint.velocity = [float(self.cmd_input[0]), float(self.cmd_input[1]), float(v_z)]
                setpoint.acceleration = [float('nan'), float('nan'), float('nan')]

            elif self.control_mode == 'acceleration':
                # PD-Controller for Altitude Acceleration (Requires D-gain to prevent bouncing)
                a_z = (-self.alt_kp * z_err) - (self.alt_kd * self.current_vel[2])
                a_z = np.clip(a_z, -2.0, 2.0)

                setpoint.velocity = [float('nan'), float('nan'), float('nan')]
                setpoint.acceleration = [float(self.cmd_input[0]), float(self.cmd_input[1]), float(a_z)]

            setpoint.timestamp = int(self.get_clock().now().nanoseconds / 1000)
            self.trajectory_setpoint_publisher.publish(setpoint)

def main(args=None):
    rclpy.init(args=args)
    node = DroneInterfaceNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()