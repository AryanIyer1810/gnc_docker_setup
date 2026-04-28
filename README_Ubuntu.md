# GNC Workshop — Ubuntu 22.04 Setup Guide

> **Target system:** Ubuntu 20.04 and higher (native installation)
> **Time required:** ~15–20 minutes

Because the workshop image was built natively on Ubuntu, this installation is faster and simpler than the Windows guide. However, you must identify your GPU type before starting — Docker needs to know which graphics hardware to use inside the container.

Follow every step in order. Do not skip sections.

---

## Before You Begin — Identify Your GPU

Run the following command in a terminal to check your graphics hardware:

```bash
lspci | grep -i vga
```

- If the output contains **NVIDIA** — follow the NVIDIA path where indicated below.
- If the output contains **Intel** or **AMD** — follow the Intel/AMD path.

> **Tip:** Most laptops without a dedicated GPU will show Intel integrated graphics.

---

## Phase 1 — Install Prerequisites

Open a terminal (`Ctrl+Alt+T`) and run the following commands.

### Step 1.1 — Install Git

```bash
sudo apt update
sudo apt install git -y
```

---

### Step 1.2 — Install Docker Engine

Run the following block in full. It adds Docker's official repository and installs the engine:

```bash
sudo apt-get update
sudo apt-get install ca-certificates curl -y
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y
```

---

### Step 1.3 — NVIDIA Users Only: Install the NVIDIA Container Toolkit

> Skip this step if you have an Intel or AMD GPU.

This toolkit allows Docker to access your dedicated NVIDIA GPU inside the container:

```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

---

## Phase 2 — Download the Workshop Environment

### Step 2.1 — Clone the Repository

```bash
cd ~/Downloads
git clone https://github.com/AryanIyer1810/gnc_docker_setup.git
cd gnc_docker_setup
```

### Step 2.2 — Download the Docker Image

Download the workshop Docker image from the following link:

[Download Docker Image — Google Drive](https://drive.google.com/file/d/1IYebz1YA7_8cuvxFhdJ4KD329GcxV2zr/view?usp=sharing)

Once downloaded, move the `.tar` file into the `gnc_docker_setup` folder. Your folder should look like this:

```
Downloads/
└── gnc_docker_setup/
    ├── docker-compose.yml
    ├── docker-compose.intel_amd.yml
    ├── docker-compose.nvidia.yml
    ├── ...
    └── gnc_workshop_master_v1.tar    (the file you just downloaded)
```

---

## Phase 3 — Allow GUI Forwarding

This command grants the Docker container permission to draw the Gazebo window on your desktop. Run it once per session before launching the container:

```bash
xhost +local:root
```

---

## Phase 4 — Load and Test the Simulation

### Step 4.1 — Load the Docker Image

This imports the workshop environment into Docker. **It will take 5–10 minutes — do not close the terminal.**

```bash
sudo docker load -i gnc_workshop_master_v1.tar
```

Wait until you see a confirmation message before continuing.

### Step 4.2 — Start the Container

Run the command that matches your GPU type.

**Intel or AMD (integrated GPU):**

```bash
sudo docker compose -f docker-compose.yml -f docker-compose.intel_amd.yml up -d
```

**NVIDIA (dedicated GPU):**

```bash
sudo docker compose -f docker-compose.yml -f docker-compose.nvidia.yml up -d
```

### Step 4.3 — Enter the Simulation Environment

```bash
sudo docker exec -it advanced_gnc_env bash
```

Your terminal prompt will change — you are now inside the Linux container.

### Step 4.4 — Launch the Swarm Test

Run the following commands inside the container:

```bash
refresh_gazebo
```

> `refresh_gazebo` is a built-in command that clears any existing Gazebo processes for a clean start. Wait for it to complete before continuing.

```bash
cd ~/ros2_ws/src/fup_adv
./launch_swarm.sh 3
```

If everything is working, the Gazebo simulation window will open with a 3-drone swarm scenario and coloured cylinders.

---

> **Each new session:** Run `xhost +local:root` (Phase 3) first, then repeat Steps 4.2–4.4.

---

## Quick Reference — Troubleshooting

| Problem | Fix |
|---|---|
| `docker: command not found` | Rerun the Docker Engine install block in Step 1.2 |
| `permission denied` on docker commands | Prefix all docker commands with `sudo` |
| Gazebo window does not appear | Run `xhost +local:root` and restart the container |
| NVIDIA GPU not detected in container | Confirm NVIDIA Container Toolkit is installed (Step 1.3) and run `sudo systemctl restart docker` |
| Container fails to start | Ensure the correct compose file for your GPU was used (Step 4.2) |

---

For issues not covered here, contact us at [30006050@iitb.ac.in](mailto:30006050@iitb.ac.in).

- Workshop Repository: [github.com/AryanIyer1810/gnc_docker_setup](https://github.com/AryanIyer1810/gnc_docker_setup)
- Docker Image: [Google Drive](https://drive.google.com/file/d/1IYebz1YA7_8cuvxFhdJ4KD329GcxV2zr/view?usp=sharing)
