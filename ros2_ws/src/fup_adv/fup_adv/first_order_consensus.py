"""First-order consensus with triangle formation offsets + leader tracking.
   x_dot_i = u_i,   u_i = -kC Sum a_ij[(x_i-x_j)-(d_i-d_j)] - kL(x_i - d_i - x_L)
   For n=3 the ring topology == complete graph K3 (every pair adjacent).
"""
import math, numpy as np, rclpy
from rclpy.node import Node
from fup_adv.px4_interface import PX4Agent

class FirstOrderConsensus(Node):
    def __init__(self):
        super().__init__('first_order_consensus')
        self.declare_parameter('n', 3)
        self.declare_parameter('takeoff_alt', 2.5)
        self.declare_parameter('side', 2.5)         # triangle side (m)
        self.declare_parameter('kL', 0.6)
        self.declare_parameter('kC', 1.0)
        self.declare_parameter('v_max', 1.5)
        self.declare_parameter('leader_radius', 3.0)
        self.declare_parameter('leader_omega', 0.15)
        self.n = self.get_parameter('n').value
        self.h = self.get_parameter('takeoff_alt').value
        s      = self.get_parameter('side').value
        # Equilateral triangle centred on origin (ENU): vertices at 90°, 210°, 330°
        R = s / math.sqrt(3.0)                      # circumradius
        self.delta = np.array([
            [R*math.cos(math.radians( 90)), R*math.sin(math.radians( 90)), self.h],
            [R*math.cos(math.radians(210)), R*math.sin(math.radians(210)), self.h],
            [R*math.cos(math.radians(330)), R*math.sin(math.radians(330)), self.h],
        ])
        # K3 adjacency (fully connected triangle)
        self.A = np.ones((3,3)) - np.eye(3)
        self.agents = [PX4Agent(self, i+1) for i in range(self.n)]
        self.t0 = self.get_clock().now().nanoseconds * 1e-9
        self.phase = 'boot'; self.boot_cnt = 0
        self.create_timer(0.02, self.loop)

    def leader_enu(self, t):
        R = self.get_parameter('leader_radius').value
        w = self.get_parameter('leader_omega').value
        return np.array([R*math.cos(w*t), R*math.sin(w*t), self.h])

    def loop(self):
        t = self.get_clock().now().nanoseconds * 1e-9 - self.t0
        for ag in self.agents:
            ag.send_ocm(position=(self.phase != 'consensus'),
                        velocity=(self.phase == 'consensus'))
        if self.phase == 'boot':
            for i, ag in enumerate(self.agents):
                ag.send_position_sp_enu(self.delta[i])
            self.boot_cnt += 1
            if self.boot_cnt > 20:
                for ag in self.agents: ag.set_offboard(); ag.arm()
                self.phase = 'takeoff'; self.get_logger().info('-> takeoff')
            return
        if self.phase == 'takeoff':
            ready = True
            for i, ag in enumerate(self.agents):
                ag.send_position_sp_enu(self.delta[i])
                if not ag.valid or abs(ag.pos_enu[2] - self.h) > 0.2: ready = False
            if ready:
                self.phase = 'consensus'; self.get_logger().info('-> consensus engaged')
            return
        if not all(ag.valid for ag in self.agents): return
        X  = np.array([ag.pos_enu for ag in self.agents])
        xL = self.leader_enu(t)
        kC = self.get_parameter('kC').value
        kL = self.get_parameter('kL').value
        vmax = self.get_parameter('v_max').value
        for i, ag in enumerate(self.agents):
            u = np.zeros(3)
            for j in range(self.n):
                if self.A[i, j] > 0:
                    u -= kC * self.A[i, j] * ((X[i]-X[j]) - (self.delta[i]-self.delta[j]))
            u -= kL * (X[i] - self.delta[i] - xL)
            nv = np.linalg.norm(u)
            if nv > vmax: u *= vmax / nv
            ag.send_velocity_sp_enu(u)

def main():
    rclpy.init(); n = FirstOrderConsensus(); rclpy.spin(n); rclpy.shutdown()
if __name__ == '__main__': main()
