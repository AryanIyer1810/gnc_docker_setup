# GNC Workshop — Windows 11 Setup Guide

> **Target system:** Windows 11 with WSL 2 + Docker Desktop
> **Time required:** ~20–30 minutes (plus one restart)

Follow every step in order. Do not skip sections.

---

## Phase 1 — Install Required Tools

All tools are installed via the Windows Package Manager (`winget`) for clean, reliable installations.

### Step 1.1 — Open an Administrator PowerShell

1. Click the **Windows Start** button.
2. Type `PowerShell`.
3. Right-click **Windows PowerShell** and select **Run as Administrator**.
4. Click **Yes** if Windows asks for permission.

> All commands in Phase 1 are run in this Administrator PowerShell window.

---

### Step 1.2 — Install Git

```powershell
winget install Git.Git
```

If prompted to agree to source terms, type `Y` and press **Enter**.

---

### Step 1.3 — Install WSL 2 (version 2.6.3 or later)

Docker Desktop requires WSL 2. Install it now to avoid issues later:

```powershell
winget install Microsoft.WSL
```

> If you see a message saying the latest version is already installed, that is fine — continue to the next step.

---

### Step 1.4 — Install Docker Desktop

```powershell
winget install Docker.DockerDesktop
```

---

### Step 1.5 — Install VcXsrv (Windows X Server)

To display graphical Linux windows on your Windows desktop, you need an X server.

1. Download the installer from SourceForge: [VcXsrv Windows X Server](https://sourceforge.net/projects/vcxsrv/)
2. Run the downloaded installer (double-click it).
3. Click **Yes** when Windows asks for permission to make changes.
4. Accept all **default settings** and complete the installation.

When installation is complete, you should see an **XLaunch** shortcut on your Desktop.

---

### CRITICAL: Restart Your Computer

**You must restart before continuing.**

```
Start → Power → Restart
```

This applies WSL 2 updates, finalises Docker Desktop installation, and prepares the X server.

---

## Phase 2 — Start and Verify Docker

### Step 2.1 — Launch Docker Desktop

After restarting, open **Docker Desktop** from the Start menu.
Accept any service agreements if prompted.

### Step 2.2 — Wait for the Engine to Start

Look at the **bottom-left corner** of the Docker Desktop window.

- Yellow — starting up, please wait.
- **Green + "Engine running"** — you are ready to continue.

> **Troubleshooting — Virtualisation Error:**
> If Docker throws an error about Virtualisation not being enabled:
> 1. Restart your PC and enter **BIOS/UEFI settings** (usually by pressing `F2`, `F10`, `DEL`, or `ESC` during boot — check your PC manufacturer's instructions).
> 2. Find the **CPU Virtualisation** option (labelled **Intel VT-x** or **AMD-V** depending on your processor).
> 3. **Enable** it, save, and reboot.

---

## Phase 3 — Download the Workshop Environment

> The following steps use a **standard (non-administrator)** PowerShell window.
>
> Open a new PowerShell: Start → type `PowerShell` → press Enter (do **not** right-click → Run as Administrator this time).

### Step 3.1 — Navigate to Your Desktop

Replace `YOUR_USERNAME` with your actual Windows username (e.g., `C:\Users\Maria\Desktop`):

```powershell
cd C:\Users\YOUR_USERNAME\Desktop
```

> **Tip:** Not sure of your username? Run `echo $env:USERNAME` to find it.

### Step 3.2 — Clone the Repository

```powershell
git clone https://github.com/AryanIyer1810/gnc_docker_setup.git
```

This creates a `gnc_docker_setup` folder on your Desktop.

### Step 3.3 — Download the Docker Image

Download the workshop Docker image from the following link:

[Download Docker Image — Google Drive](https://drive.google.com/file/d/1IYebz1YA7_8cuvxFhdJ4KD329GcxV2zr/view?usp=sharing)

Once downloaded (it may take a few minutes depending on your connection), **move** the `.tar` file directly into the `gnc_docker_setup` folder on your Desktop.

Your folder should now look like this:

```
Desktop/
└── gnc_docker_setup/
    ├── docker-compose.yml            (from git clone)
    ├── ...                           (other repo files)
    └── gnc_workshop_master_v1.tar    (the file you just downloaded)
```

---

## Phase 4 — Configure the Graphics Server (XLaunch)

> **You must repeat this phase every time before running the simulation** — XLaunch does not start automatically on boot.

### Step 4.1 — Launch XLaunch

Search for **XLaunch** in the Windows Start menu and open it.

### Step 4.2 — Display Settings

Select **Multiple windows** → click **Next**.

### Step 4.3 — Client Startup

Select **Start no client** → click **Next**.

### Step 4.4 — Extra Settings

> This step is critical. Without it, Linux graphical windows cannot connect to your display.

- Check **Disable access control**
- Leave the other two checkboxes as they are

Click **Next**.

### Step 4.5 — Finish

Click **Finish**.

A small black **X icon** will appear in your system tray (bottom-right, near the clock). This confirms XLaunch is running and ready.

---

## Phase 5 — Load and Test the Simulation

> **Docker Desktop must be open and the engine must be running** (green indicator, bottom-left) before executing any command in this phase.

Open a standard (non-administrator) PowerShell window for all commands below.

### Step 5.1 — Navigate to the Workshop Folder

```powershell
cd C:\Users\YOUR_USERNAME\Desktop\gnc_docker_setup
```

### Step 5.2 — Load the Docker Image

This imports the workshop environment into Docker. **It will take 5–10 minutes — do not close the window.**

```powershell
docker load -i .\gnc_workshop_master_v1.tar
```

Wait until you see a confirmation message before continuing.

### Step 5.3 — Start the Container

These two commands must be run together. The first tells Docker where to send graphics (your running XLaunch window); the second starts the container.

```powershell
$env:DISPLAY="host.docker.internal:0.0"
docker compose -f .\docker-compose.yml -f .\docker-compose.intel_amd.yml up -d
```

### Step 5.4 — Enter the Simulation Environment

```powershell
docker exec -it advanced_gnc_env bash
```

Your terminal prompt will change — you are now inside the Linux container.

### Step 5.5 — Launch the Swarm Test

Run the following commands inside the container:

```bash
refresh_gazebo
```

> `refresh_gazebo` is a built-in command that clears any existing Gazebo processes for a clean start. Wait for it to complete before continuing.

```bash
cd ~/ros2_ws/src/fup_adv
./launch_swarm.sh 3
```

If everything is working, the Gazebo simulation window will open on your Windows desktop with a 3-drone swarm scenario.

---

> **Each new session:** Open **Docker Desktop** first, then run **XLaunch** (Phase 4), then repeat Steps 5.3–5.5.

---

## Quick Reference — Troubleshooting

| Problem | Fix |
|---|---|
| `winget` not found | Update Windows 11 via Windows Update, then retry |
| Docker Engine won't start | Enable CPU Virtualisation in BIOS (see Phase 2) |
| WSL update prompt inside Docker | Run `winget install Microsoft.WSL` in admin PowerShell |
| `git` not found after install | Close and reopen PowerShell, then retry |
| VcXsrv / XLaunch not on Desktop | Check Start menu — search for `XLaunch` |

---

For issues not covered here, contact us at [30006050@iitb.ac.in](mailto:30006050@iitb.ac.in).

- Workshop Repository: [github.com/AryanIyer1810/gnc_docker_setup](https://github.com/AryanIyer1810/gnc_docker_setup)
- Docker Image: [Google Drive](https://drive.google.com/file/d/1IYebz1YA7_8cuvxFhdJ4KD329GcxV2zr/view?usp=sharing)
