"""Shared PX4 offboard interface for SITL drones. NED<->ENU at the boundary."""
import math, numpy as np
from rclpy.node import Node
from rclpy.qos  import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from px4_msgs.msg import (OffboardControlMode, TrajectorySetpoint, VehicleCommand,
                          VehicleLocalPosition, VehicleStatus)

NAN = float('nan')
def ned2enu(v): return np.array([v[1], v[0], -v[2]], dtype=float)
def enu2ned(v): return np.array([v[1], v[0], -v[2]], dtype=float)

PX4_QOS = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT,
                     durability=DurabilityPolicy.TRANSIENT_LOCAL,
                     history=HistoryPolicy.KEEP_LAST, depth=1)

class PX4Agent:
    def __init__(self, node: Node, idx: int):
        self.node, self.idx = node, idx
        self.sys_id = idx + 1
        ns = f'/px4_{idx}'
        self.pos_enu = np.zeros(3); self.vel_enu = np.zeros(3)
        self.yaw = 0.0; self.valid = False
        self.nav_state = 0; self.arming_state = 0
        self.ocm_pub = node.create_publisher(OffboardControlMode, f'{ns}/fmu/in/offboard_control_mode', PX4_QOS)
        self.sp_pub  = node.create_publisher(TrajectorySetpoint,  f'{ns}/fmu/in/trajectory_setpoint',   PX4_QOS)
        self.cmd_pub = node.create_publisher(VehicleCommand,      f'{ns}/fmu/in/vehicle_command',       PX4_QOS)
        node.create_subscription(VehicleLocalPosition, f'{ns}/fmu/out/vehicle_local_position', self._on_pos, PX4_QOS)
        node.create_subscription(VehicleStatus,        f'{ns}/fmu/out/vehicle_status',         self._on_st,  PX4_QOS)

    def _on_pos(self, m):
        if not (m.xy_valid and m.z_valid and m.v_xy_valid and m.v_z_valid):
            self.valid = False; return
        self.pos_enu = ned2enu(np.array([m.x, m.y, m.z]))
        self.vel_enu = ned2enu(np.array([m.vx, m.vy, m.vz]))
        self.yaw = math.pi/2 - m.heading
        self.valid = True
    def _on_st(self, m):
        self.nav_state, self.arming_state = m.nav_state, m.arming_state
    def _ts(self): return int(self.node.get_clock().now().nanoseconds / 1000)
    def _cmd(self, command, p1=0.0, p2=0.0):
        m = VehicleCommand()
        m.command = command; m.param1 = p1; m.param2 = p2
        m.target_system = self.sys_id; m.target_component = 1
        m.source_system = 1; m.source_component = 1
        m.from_external = True; m.timestamp = self._ts()
        self.cmd_pub.publish(m)
    def arm(self):          self._cmd(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, 1.0)
    def disarm(self):       self._cmd(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, 0.0)
    def set_offboard(self): self._cmd(VehicleCommand.VEHICLE_CMD_DO_SET_MODE, 1.0, 6.0)
    def send_ocm(self, *, position=False, velocity=True):
        o = OffboardControlMode()
        o.position, o.velocity = position, velocity
        o.acceleration = o.attitude = o.body_rate = False
        o.thrust_and_torque = o.direct_actuator = False
        o.timestamp = self._ts()
        self.ocm_pub.publish(o)
    def send_position_sp_enu(self, p_enu, yaw_enu=0.0):
        p_ned = enu2ned(p_enu)
        s = TrajectorySetpoint()
        s.position = [float(p_ned[0]), float(p_ned[1]), float(p_ned[2])]
        s.velocity = [NAN, NAN, NAN]; s.acceleration = [NAN, NAN, NAN]; s.jerk = [NAN, NAN, NAN]
        s.yaw = math.pi/2 - yaw_enu
        s.yawspeed = 0.0; s.timestamp = self._ts()
        self.sp_pub.publish(s)
    def send_velocity_sp_enu(self, v_enu, yaw_enu=None):
        v_ned = enu2ned(v_enu)
        s = TrajectorySetpoint()
        s.position = [NAN, NAN, NAN]
        s.velocity = [float(v_ned[0]), float(v_ned[1]), float(v_ned[2])]
        s.acceleration = [NAN, NAN, NAN]; s.jerk = [NAN, NAN, NAN]
        s.yaw      = NAN if yaw_enu is None else (math.pi/2 - yaw_enu)
        s.yawspeed = 0.0; s.timestamp = self._ts()
        self.sp_pub.publish(s)
