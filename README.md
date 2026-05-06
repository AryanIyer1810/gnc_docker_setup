# GNC Workshop — Environment Setup

Welcome to the GNC Workshop. This repository contains everything you need to install and run the simulation environment on your machine.

### 🚁 [Formation Control Experiment](https://github.com/Cramer54/px4-ros2-consensus-demo/tree/main)
*Click the link above to view the original consensus and Olfati-Saber swarm repository.*

---

<div align="center">

### Step 1 — Choose your operating system and follow the setup guide

[![Windows 11 Setup Guide](https://img.shields.io/badge/Setup_Guide-Windows_11-0078D4?style=for-the-badge&logo=windows11&logoColor=white)](./README_Windows.md)
&nbsp;
[![Ubuntu Setup Guide](https://img.shields.io/badge/Setup_Guide-Ubuntu_20.04+-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)](./README_Ubuntu.md)

### Step 2 — Once installed, open the command reference during your session

[![Workshop Command Reference](https://img.shields.io/badge/Workshop-Command_Reference-2ea44f?style=for-the-badge&logo=gnu-bash&logoColor=white)](./WORKSHOP_COMMANDS.md)

</div>

---

## What You Will Install

- Docker Desktop — runs the workshop simulation container
- ROS 2 + Gazebo — pre-configured inside the container
- VcXsrv *(Windows only)* — displays Linux graphical windows on your desktop

All software is free and open source. No prior Linux or Docker experience is required.

---

## Repository Contents
```text
gnc_docker_setup/
├── README.md                        (this file)
├── README_Windows.md                (Windows 11 setup guide)
├── README_Ubuntu.md                 (Ubuntu setup guide)
├── WORKSHOP_COMMANDS.md             (in-session command reference)
├── docker-compose.yml
├── docker-compose.intel_amd.yml
├── docker-compose.nvidia.yml
└── gnc_workshop_master_v1.tar       (download separately — see setup guide)
```

For issues, contact us at 30006050@iitb.ac.in.
