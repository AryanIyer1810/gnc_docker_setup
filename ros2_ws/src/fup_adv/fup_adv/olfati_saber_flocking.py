"""Olfati-Saber Algorithm 3 - flocking with obstacle avoidance (n=3).
   Reference: R. Olfati-Saber, IEEE TAC 51(3):401-420, 2006."""
import math, numpy as np, rclpy
from rclpy.node import Node
from fup_adv.px4_interface import PX4Agent

def sigma_norm(z, eps): return (math.sqrt(1.0 + eps * float(np.dot(z,z))) - 1.0) / eps
def sigma_eps(z, eps):  return z / math.sqrt(1.0 + eps * float(np.dot(z,z)))
def sigma1_scalar(z):   return z / math.sqrt(1.0 + z*z)
def sigma1_vec(z):      return z / math.sqrt(1.0 + float(np.dot(z,z)))
def bump(z, h):
    if z < 0: return 0.0
    if z < h: return 1.0
    if z <= 1.0: return 0.5*(1.0 + math.cos(math.pi*(z-h)/(1.0-h)))
    return 0.0
def phi(z, a, b):
    c = abs(a-b)/math.sqrt(4.0*a*b) if a != b else 0.0
    return 0.5*((a+b)*sigma1_scalar(z+c) + (a-b))
def phi_alpha(z, r_a, d_a, h_a, a, b): return bump(z/r_a, h_a) * phi(z-d_a, a, b)
def phi_beta (z, d_b, h_b):            return bump(z/d_b, h_b) * (sigma1_scalar(z-d_b) - 1.0)

class OlfatiSaberFlocking(Node):
    def __init__(self):
        super().__init__('olfati_saber_flocking')
        self.declare_parameters('', [
            ('n', 3), ('takeoff_alt', 2.5), ('dt', 0.02), ('v_max', 3.0),
            ('r', 2.2), ('d', 1.5), ('rp', 1.2), ('dp', 0.8),
            ('eps', 0.1), ('h_alpha', 0.2), ('h_beta', 0.9),
            ('a', 5.0), ('b', 5.0),
            ('c1_alpha', 3.0), ('c1_beta', 20.0), ('c1_gamma', 1.1),
            ('gamma_mode', 'line'), ('gamma_speed', 0.4),
        ])
        self.n = self.get_parameter('n').value
        self.h = self.get_parameter('takeoff_alt').value
        self.c2_alpha = 2.0 * math.sqrt(self.get_parameter('c1_alpha').value)
        self.c2_beta  = 2.0 * math.sqrt(self.get_parameter('c1_beta').value)
        self.c2_gamma = 2.0 * math.sqrt(self.get_parameter('c1_gamma').value)
        eps = self.get_parameter('eps').value
        self.r_alpha = sigma_norm(np.array([self.get_parameter('r').value, 0, 0]), eps)
        self.d_alpha = sigma_norm(np.array([self.get_parameter('d').value, 0, 0]), eps)
        self.r_beta  = sigma_norm(np.array([self.get_parameter('rp').value, 0, 0]), eps)
        self.d_beta  = sigma_norm(np.array([self.get_parameter('dp').value, 0, 0]), eps)
        # Obstacles match cylinders.sdf exactly (ENU)
        self.obstacles = [(np.array([8.0, 3.0, self.h]), 0.5),
                          (np.array([8.0, 7.0, self.h]), 0.5)]
        self.agents = [PX4Agent(self, i+1) for i in range(self.n)]
        self.t0 = self.get_clock().now().nanoseconds * 1e-9
        self.v_cmd = np.zeros((self.n, 3))
        self.phase = 'boot'; self.boot_cnt = 0
        dt = self.get_parameter('dt').value
        self.create_timer(dt, self.loop)

    def gamma_ref(self, t):
        mode  = self.get_parameter('gamma_mode').value
        speed = self.get_parameter('gamma_speed').value
        if mode == 'circle':
            R, w = 4.0, speed/4.0
            q_r = np.array([8.0 + R*math.cos(w*t), 5.0 + R*math.sin(w*t), self.h])
            p_r = np.array([-R*w*math.sin(w*t),    R*w*math.cos(w*t),     0.0])
        else:
            q_r = np.array([min(-4.0 + speed*t, 16.0), 5.0, self.h])
            p_r = np.array([speed if q_r[0] < 16.0 else 0.0, 0.0, 0.0])
        return q_r, p_r

    def _u_alpha(self, i, Q, P, eps, h_a, a, b):
        u1 = np.zeros(3); u2 = np.zeros(3)
        c1 = self.get_parameter('c1_alpha').value
        r  = self.get_parameter('r').value
        for j in range(self.n):
            if j == i: continue
            diff = Q[j] - Q[i]
            if np.linalg.norm(diff) > r: continue
            z = sigma_norm(diff, eps); nij = sigma_eps(diff, eps)
            aij = bump(z / self.r_alpha, h_a)
            u1 += phi_alpha(z, self.r_alpha, self.d_alpha, h_a, a, b) * nij
            u2 += aij * (P[j] - P[i])
        return c1*u1 + self.c2_alpha*u2

    def _u_beta(self, i, Q, P, eps, h_b):
        u1 = np.zeros(3); u2 = np.zeros(3)
        c1 = self.get_parameter('c1_beta').value
        rp = self.get_parameter('rp').value
        for (yk, Rk) in self.obstacles:
            diff = Q[i] - yk; diff[2] = 0.0
            dist = np.linalg.norm(diff)
            if dist <= Rk + 1e-3 or dist > Rk + rp: continue
            mu = Rk / dist; a_k = diff / dist
            P_proj = np.eye(3) - np.outer(a_k, a_k)
            q_hat = mu*Q[i] + (1.0 - mu)*yk
            p_hat = mu * P_proj @ P[i]
            d_ik  = q_hat - Q[i]
            z = sigma_norm(d_ik, eps); nhat = sigma_eps(d_ik, eps)
            bik = bump(z / self.d_beta, h_b)
            u1 += phi_beta(z, self.d_beta, h_b) * nhat
            u2 += bik * (p_hat - P[i])
        return c1*u1 + self.c2_beta*u2

    def _u_gamma(self, i, Q, P, q_r, p_r):
        c1 = self.get_parameter('c1_gamma').value
        return -c1 * sigma1_vec(Q[i] - q_r) - self.c2_gamma*(P[i] - p_r)

    def loop(self):
        t = self.get_clock().now().nanoseconds * 1e-9 - self.t0
        for ag in self.agents:
            ag.send_ocm(position=(self.phase != 'flock'),
                        velocity=(self.phase == 'flock'))
        # Staging positions along y = 2, 5, 8 (match SITL default spawns below)
        stage = np.array([[0,2,self.h],[0,5,self.h],[0,8,self.h]], float)
        if self.phase == 'boot':
            for i, ag in enumerate(self.agents): ag.send_position_sp_enu(stage[i])
            self.boot_cnt += 1
            if self.boot_cnt > 20:
                for ag in self.agents: ag.set_offboard(); ag.arm()
                self.phase = 'takeoff'; self.get_logger().info('-> takeoff')
            return
        if self.phase == 'takeoff':
            ready = True
            for i, ag in enumerate(self.agents):
                ag.send_position_sp_enu(stage[i])
                if not ag.valid or abs(ag.pos_enu[2]-self.h) > 0.2: ready = False
            if ready: self.phase = 'flock'; self.get_logger().info('-> flock engaged')
            return
        if not all(ag.valid for ag in self.agents): return
        Q = np.array([ag.pos_enu for ag in self.agents])
        P = np.array([ag.vel_enu for ag in self.agents])
        eps = self.get_parameter('eps').value
        h_a = self.get_parameter('h_alpha').value
        h_b = self.get_parameter('h_beta').value
        a   = self.get_parameter('a').value
        b   = self.get_parameter('b').value
        q_r, p_r = self.gamma_ref(t)
        dt   = self.get_parameter('dt').value
        vmax = self.get_parameter('v_max').value
        for i, ag in enumerate(self.agents):
            u = (self._u_alpha(i, Q, P, eps, h_a, a, b)
               + self._u_beta (i, Q, P, eps, h_b)
               + self._u_gamma(i, Q, P, q_r, p_r))
            self.v_cmd[i] += u * dt
            nv = np.linalg.norm(self.v_cmd[i])
            if nv > vmax: self.v_cmd[i] *= vmax / nv
            ag.send_velocity_sp_enu(self.v_cmd[i])

def main():
    rclpy.init(); n = OlfatiSaberFlocking(); rclpy.spin(n); rclpy.shutdown()
if __name__ == '__main__': main()
