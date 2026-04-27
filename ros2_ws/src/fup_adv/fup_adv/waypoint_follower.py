#!/usr/bin/env python3

import rclpy
import math
import pandas as pd  
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from px4_msgs.msg import OffboardControlMode, TrajectorySetpoint, VehicleCommand, VehicleLocalPosition, VehicleStatus


class waypoint_follower(Node):

    def __init__(self) -> None:
        super().__init__('offboard_control_takeoff_and_land')

        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        self.offboard_control_mode_publisher = self.create_publisher(
            OffboardControlMode, '/fmu/in/offboard_control_mode', qos_profile)
        self.trajectory_setpoint_publisher = self.create_publisher(
            TrajectorySetpoint, '/fmu/in/trajectory_setpoint', qos_profile)
        self.vehicle_command_publisher = self.create_publisher(
            VehicleCommand, '/fmu/in/vehicle_command', qos_profile)
        
        self.vehicle_local_position_subscriber = self.create_subscription(
            VehicleLocalPosition, '/fmu/out/vehicle_local_position', self.vehicle_local_position_callback, qos_profile)
        self.vehicle_status_subscriber = self.create_subscription(
            VehicleStatus, '/fmu/out/vehicle_status', self.vehicle_status_callback, qos_profile)

        self.offboard_setpoint_counter = 0
        self.vehicle_local_position = VehicleLocalPosition()
        self.vehicle_status = VehicleStatus()



        # Define a 5x5 meter square at 2 meters altitude.
        # Remember PX4 uses NED coordinates: Z is negative for UP.
        self.waypoints = [
            7.5, 0.0, -5.0,   # Point 1: Fly 5m North
            7.5, 7.5, -5.0,   # Point 2: Fly 5m East
            0.0, 7.5, -5.0,   # Point 3: Fly 5m South
            0.0, 0.0, -5.0    # Point 4: Fly 5m West (Return to origin)
        ]
        
        self.i = 0
        self.takeoff_complete = False  # Required for the state machine
        
        self.timer = self.create_timer(0.1, self.timer_callback)



    def vehicle_local_position_callback(self, vehicle_local_position):
        self.vehicle_local_position = vehicle_local_position

    def vehicle_status_callback(self, vehicle_status):
        self.vehicle_status = vehicle_status

    def arm(self):
        self.publish_vehicle_command(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, param1=1.0)
        self.get_logger().info('Arm command sent')

    def disarm(self):
        self.publish_vehicle_command(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, param1=0.0)
        self.get_logger().info('Disarm command sent')

    def engage_offboard_mode(self):
        self.publish_vehicle_command(VehicleCommand.VEHICLE_CMD_DO_SET_MODE, param1=1.0, param2=6.0)
        self.get_logger().info("Switching to offboard mode")

    def land(self):
        self.publish_vehicle_command(VehicleCommand.VEHICLE_CMD_NAV_LAND)
        self.get_logger().info("Switching to land mode")

    def publish_offboard_control_heartbeat_signal(self):
        msg = OffboardControlMode()
        msg.position = True
        msg.velocity = False
        msg.acceleration = False
        msg.attitude = True
        msg.body_rate = False
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        self.offboard_control_mode_publisher.publish(msg)

    def publish_position_setpoint(self, x: float, y: float, z: float):
        msg = TrajectorySetpoint()
        msg.position = [x, y, z]
        msg.yawspeed = 0.3
        msg.yaw = 1.57079  # (90 degrees)
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        self.trajectory_setpoint_publisher.publish(msg)
        self.get_logger().info(f"Publishing position setpoints {[x, y, z]}")

    def publish_vehicle_command(self, command, **params) -> None:
        msg = VehicleCommand()
        msg.command = command
        msg.param1 = params.get("param1", 0.0)
        msg.param2 = params.get("param2", 0.0)
        msg.param3 = params.get("param3", 0.0)
        msg.param4 = params.get("param4", 0.0)
        msg.param5 = params.get("param5", 0.0)
        msg.param6 = params.get("param6", 0.0)
        msg.param7 = params.get("param7", 0.0)
        msg.target_system = 1
        msg.target_component = 1
        msg.source_system = 1
        msg.source_component = 1
        msg.from_external = True
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        self.vehicle_command_publisher.publish(msg)

    def timer_callback(self) -> None:
        self.publish_offboard_control_heartbeat_signal()

        if self.offboard_setpoint_counter == 10:
            self.engage_offboard_mode()
            self.arm()

        if self.offboard_setpoint_counter < 11:
            self.offboard_setpoint_counter += 1

        if self.vehicle_status.nav_state == VehicleStatus.NAVIGATION_STATE_OFFBOARD:
            
            # PHASE 1: Takeoff to a safe altitude first
            if not self.takeoff_complete:
                takeoff_z = -5.0
                # Command hover at origin
                self.publish_position_setpoint(0.0, 0.0, takeoff_z)
                
                # Check if we have reached the takeoff altitude
                if self.vehicle_local_position.z < (takeoff_z + 0.2): 
                    self.get_logger().info("Takeoff complete. Starting square trajectory.")
                    self.takeoff_complete = True

            # PHASE 2: Navigate the square
            elif self.i < len(self.waypoints):
                x = self.waypoints[self.i]
                y = self.waypoints[self.i+1]
                z = self.waypoints[self.i+2]
                self.publish_position_setpoint(x, y, z)

                # Calculate horizontal distance to current waypoint
                distance = math.sqrt(
                    (self.vehicle_local_position.x - x)**2 + 
                    (self.vehicle_local_position.y - y)**2
                )

                # If within 0.5m of the waypoint, move to the next one
                if distance < 0.5:
                    self.get_logger().info(f"Waypoint {self.i//3 + 1} reached.")
                    self.i += 3

                # If we just incremented past the last waypoint, trigger landing
                if self.i >= len(self.waypoints):
                    self.land()
                    self.get_logger().info("Square mission completed, landing...")
                    rclpy.shutdown()


def main(args=None) -> None:
    print('Starting offboard control node...')
    rclpy.init(args=args)
    offboard_control = waypoint_follower()
    rclpy.spin(offboard_control)
    offboard_control.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)
