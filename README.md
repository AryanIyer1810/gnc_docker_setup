k
# GNC Workshop — Environment Setup

Welcome to the GNC Workshop. This repository contains everything you need to install and run the simulation environment on your machine.

Before you begin, select the guide for your operating system:

---

## Choose Your Platform

| Operating System | Setup Guide |
|---|---|
| **Windows 11** | [Windows 11 Setup Guide](./README_Windows.md) |
| **Ubuntu 20.04 and higher** | [Ubuntu Setup Guide](./README_Ubuntu.md) |

---

## What You Will Install

- Docker Desktop — runs the workshop simulation container
- ROS 2 + Gazebo — pre-configured inside the container
- VcXsrv *(Windows only)* — displays Linux graphical windows on your desktop

All software is free and open source. No prior Linux or Docker experience is required.

---

## Repository Contents

```
gnc_docker_setup/
├── README.md                        (this file)
├── README_Windows.md                (Windows 11 setup guide)
├── docker-compose.yml
├── docker-compose.intel_amd.yml
└── gnc_workshop_master_v1.tar       (download separately — see setup guide)
```

---

For issues, contact us at [30006050@iitb.ac.in](mailto:30006050@iitb.ac.in).
