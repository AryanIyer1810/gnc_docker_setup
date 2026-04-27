#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from px4_msgs.msg import OffboardControlMode, TrajectorySetpoint, VehicleCommand, VehicleStatus, VehicleLocalPosition

class AccelerationController(Node):

    def __init__(self) -> None:
        super().__init__('acceleration_controller')

        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        # Publishers
        self.offboard_control_mode_publisher = self.create_publisher(
            OffboardControlMode, '/fmu/in/offboard_control_mode', qos_profile)
        self.trajectory_setpoint_publisher = self.create_publisher(
            TrajectorySetpoint, '/fmu/in/trajectory_setpoint', qos_profile)
        self.vehicle_command_publisher = self.create_publisher(
            VehicleCommand, '/fmu/in/vehicle_command', qos_profile)
        
        # Subscribers
        self.vehicle_status_subscriber = self.create_subscription(
            VehicleStatus, '/fmu/out/vehicle_status', self.vehicle_status_callback, qos_profile)
        self.vehicle_local_position_subscriber = self.create_subscription(
            VehicleLocalPosition, '/fmu/out/vehicle_local_position', self.vehicle_local_position_callback, qos_profile)
        
        # Variables
        self.vehicle_local_position = VehicleLocalPosition()
        self.vehicle_status = VehicleStatus()
        self.offboard_setpoint_counter = 0
        self.takeoff_complete = False

        self.timer = self.create_timer(0.1, self.timer_callback)

    def vehicle_status_callback(self, vehicle_status):
        self.vehicle_status = vehicle_status
        
    def vehicle_local_position_callback(self, vehicle_local_position):
        self.vehicle_local_position = vehicle_local_position

    def arm(self):
        self.publish_vehicle_command(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, param1=1.0)
        self.get_logger().info('Arm command sent')

    def engage_offboard_mode(self):
        self.publish_vehicle_command(VehicleCommand.VEHICLE_CMD_DO_SET_MODE, param1=1.0, param2=6.0)
        self.get_logger().info("Switching to offboard mode")

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
        # Phase 1: Arm and Takeoff
        if not self.takeoff_complete:
            # 1. Publish Heartbeat for Position Control
            msg = OffboardControlMode()
            msg.position = True
            msg.velocity = False
            msg.acceleration = False
            msg.attitude = False
            msg.body_rate = False
            msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
            self.offboard_control_mode_publisher.publish(msg)

            # 2. Publish Takeoff Setpoint (2 meters up)
            setpoint = TrajectorySetpoint()
            setpoint.position = [0.0, 0.0, -2.0] # Remember NED coordinates: -2 is UP
            setpoint.yaw = 0.0
            setpoint.timestamp = int(self.get_clock().now().nanoseconds / 1000)
            self.trajectory_setpoint_publisher.publish(setpoint)

            # 3. Check if we reached altitude
            if self.vehicle_local_position.z < -1.8: # Close enough to 2 meters up
                self.get_logger().info("Takeoff altitude reached. Switching to Acceleration Control.")
                self.takeoff_complete = True
                
        # Phase 2: Execute Custom Acceleration Control
        else:
            # 1. Publish Heartbeat for Acceleration Control
            msg = OffboardControlMode()
            msg.position = False
            msg.velocity = False
            msg.acceleration = True
            msg.attitude = False
            msg.body_rate = False
            msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
            self.offboard_control_mode_publisher.publish(msg)

            # 2. Publish Acceleration Setpoint (NaN for position AND velocity!)
            setpoint = TrajectorySetpoint()
            setpoint.position = [float('nan'), float('nan'), float('nan')]
            setpoint.velocity = [float('nan'), float('nan'), float('nan')]
            
            # Command: 0.5 m/s^2 acceleration upwards (NED: negative is up)
            setpoint.acceleration = [0.0, 1.0, -0.5] 
            setpoint.yaw = 0.0
            setpoint.timestamp = int(self.get_clock().now().nanoseconds / 1000)
            self.trajectory_setpoint_publisher.publish(setpoint)

        # Handle arming sequence as usual
        if self.offboard_setpoint_counter == 10:
            self.engage_offboard_mode()
            self.arm()
        if self.offboard_setpoint_counter < 11:
            self.offboard_setpoint_counter += 1

def main(args=None) -> None:
    rclpy.init(args=args)
    acceleration_control = AccelerationController()
    rclpy.spin(acceleration_control)
    acceleration_control.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()