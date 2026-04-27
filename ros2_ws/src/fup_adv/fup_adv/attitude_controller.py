#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from px4_msgs.msg import OffboardControlMode, VehicleCommand, VehicleStatus, VehicleAttitudeSetpoint

class AttitudeController(Node):

    def __init__(self) -> None:
        super().__init__('attitude_controller')

        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        # Publishers
        self.offboard_control_mode_publisher = self.create_publisher(
            OffboardControlMode, '/fmu/in/offboard_control_mode', qos_profile)
        self.vehicle_command_publisher = self.create_publisher(
            VehicleCommand, '/fmu/in/vehicle_command', qos_profile)
        
        # NOTE: We are now publishing to vehicle_attitude_setpoint
        self.attitude_setpoint_publisher = self.create_publisher(
            VehicleAttitudeSetpoint, '/fmu/in/vehicle_attitude_setpoint', qos_profile)

        # Subscribers
        self.vehicle_status_subscriber = self.create_subscription(
            VehicleStatus, '/fmu/out/vehicle_status', self.vehicle_status_callback, qos_profile)

        self.vehicle_status = VehicleStatus()
        self.offboard_setpoint_counter = 0

        self.timer = self.create_timer(0.1, self.timer_callback)

    def vehicle_status_callback(self, vehicle_status):
        self.vehicle_status = vehicle_status

    def arm(self):
        self.publish_vehicle_command(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, param1=1.0)
        self.get_logger().info('Arm command sent')

    def engage_offboard_mode(self):
        self.publish_vehicle_command(VehicleCommand.VEHICLE_CMD_DO_SET_MODE, param1=1.0, param2=6.0)
        self.get_logger().info("Switching to offboard mode")

    def publish_offboard_control_heartbeat_signal(self):
        msg = OffboardControlMode()
        # CRITICAL CHANGE: We only want attitude control now
        msg.position = False
        msg.velocity = False
        msg.acceleration = False
        msg.attitude = True 
        msg.body_rate = False
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        self.offboard_control_mode_publisher.publish(msg)

    def publish_attitude_setpoint(self):
        msg = VehicleAttitudeSetpoint()
        
        # Quaternions: [w, x, y, z]
        # [1.0, 0.0, 0.0, 0.0] means flat and level, heading North.
        msg.q_d = [1.0, 0.0, 0.0, 0.0] 
        
        # Normalized thrust vector in body frame [-1.0, 1.0]
        # X: Forward/Back, Y: Left/Right, Z: Up/Down
        # Hover thrust is usually around -0.6 to -0.7 (Z points DOWN in NED frame)
        msg.thrust_body = [0.0, 0.0, -0.65] 
        
        msg.yaw_sp_move_rate = 0.0
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        self.attitude_setpoint_publisher.publish(msg)

    def publish_vehicle_command(self, command, **params) -> None:
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

    def timer_callback(self) -> None:
        # 1. Always publish the heartbeat
        self.publish_offboard_control_heartbeat_signal()

        # 2. Always publish the setpoint (even before arming)
        self.publish_attitude_setpoint()

        if self.offboard_setpoint_counter == 10:
            self.engage_offboard_mode()
            self.arm()

        if self.offboard_setpoint_counter < 11:
            self.offboard_setpoint_counter += 1

def main(args=None) -> None:
    rclpy.init(args=args)
    offboard_control = AttitudeController()
    rclpy.spin(offboard_control)
    offboard_control.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()