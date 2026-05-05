# Workshop Command Reference
ROS 2 & Gazebo — Tutorial 2 .
---

## Linux Basics

### Navigation

```bash
# Print current directory
pwd

# List files
ls

# Move into a folder
cd <folder>

# Go up one folder
cd ..

# Print file contents
cat <file>

# Run as administrator
sudo <cmd>
```

### Essential Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl + C` | Kill running process |
| `Ctrl + D` | Exit terminal / end input |
| `Ctrl + L` | Clear screen |
| `Ctrl + Shift + V` | Paste into terminal |
| `Tab` | Autocomplete |

---

## ROS 2 — Inspect Nodes & Topics

```bash
# List all active nodes
ros2 node list
```

```bash
# List all active topics
ros2 topic list
```

```bash
# Echo messages on a topic
ros2 topic echo /turtle1/pose
```

```bash
# Check publish rate of a topic
ros2 topic hz /camera/image_raw
```

```bash
# Echo camera info
ros2 topic echo /camera/camera_info
```

```bash
# View computation graph
rqt_graph
```

---

## Turtlesim Demo

### Terminal 1 — Launch Turtlesim

```bash
ros2 run turtlesim turtlesim_node
```

### Terminal 2 — Drive the Turtle
> Use arrow keys to move. Keep this terminal focused.

```bash
ros2 run turtlesim turtle_teleop_key
```

### Terminal 3 — Inspect the Graph

```bash
ros2 node list
```

```bash
ros2 topic list
```

```bash
ros2 topic echo /turtle1/pose
```

```bash
rqt_graph
```

### Publish Commands from Terminal

```bash
# Publish exactly once (-1 flag)
ros2 topic pub -1 /turtle1/cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 2.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 1.8}}"
```

```bash
# Publish continuously at 10 Hz (-r flag) — stop with Ctrl+C
ros2 topic pub -r 10 /turtle1/cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 2.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 1.8}}"
```

---

## Full Stack Launch
> **Order matters:** Terminal 1 → wait → Terminal 2 → Terminal 3 → Terminal 4

### Terminal 1 — PX4 SITL
> Run first. Wait for `"Ready for takeoff"` before opening Terminal 2.

```bash
cd ~/PX4-Autopilot
make px4_sitl gz_x500_depth
```

### Terminal 2 — ROS 2 Bridge

```bash
MicroXRCEAgent udp4 -p 8888
```

```bash
# Confirm topics are visible
ros2 topic list
```

### Terminal 3 — QGroundControl
> Connects automatically over MAVLink. Do not configure UDP manually.

```bash
qgc
```

### Terminal 4 — ROS 2 Node

```bash
cd ~/ros2_ws
source install/setup.bash
ros2 launch fup_adv depth_launch.bringup.py
```