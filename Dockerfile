# Start with the official ROS 2 Humble Desktop image
FROM osrf/ros:humble-desktop

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# 0. The GPG & Time Expiration Bypass
RUN echo 'Acquire::Check-Valid-Until "false";' > /etc/apt/apt.conf.d/99bypass \
    && echo 'Acquire::AllowInsecureRepositories "true";' >> /etc/apt/apt.conf.d/99bypass \
    && echo 'APT::Get::AllowUnauthenticated "true";' >> /etc/apt/apt.conf.d/99bypass

# 1. Install System Tools and Python Libraries
RUN sed -i 's/archive.ubuntu.com/in.archive.ubuntu.com/g' /etc/apt/sources.list \
    && sed -i 's/security.ubuntu.com/in.archive.ubuntu.com/g' /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y \
    git wget curl nano terminator \
    python3-pip python3-dev \
    software-properties-common \
    libgl1-mesa-glx libgl1-mesa-dri libglx-mesa0 mesa-utils libvulkan1 mesa-vulkan-drivers vulkan-tools \
    python3-pandas \
    python3-geopandas \
    python3-matplotlib \
    lsb-release apt-transport-https \
    libfuse2 \
    libpulse-dev \
    libxcb-xinerama0 \
    libxkbcommon-x11-0 \
    libxcb-cursor0 \
    libgstreamer-gl1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    && rm -rf /var/lib/apt/lists/*
    
# 1.5 Install Python Dependencies for PX4 SITL and ROS 2
RUN pip3 install pandas numpy scipy setuptools==58.2.0 \
    kconfiglib jinja2 jsonschema pyros-genmsg future symforce networkx

# 2. Install Gazebo Harmonic
RUN curl https://packages.osrfoundation.org/gazebo.gpg --output /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null \
    && apt-get update || true \
    && apt-get install -y gz-harmonic \
    && rm -rf /var/lib/apt/lists/*

# 3. Install ROS-Gazebo Bridge (HARMONIC SPECIFIC) and PX4 Dependencies
RUN apt-get update || true \
    && apt-get install -y \
    ros-humble-ros-gzharmonic \
    && rm -rf /var/lib/apt/lists/*

# 4. Create a non-root user (Crucial for GUI/X11 forwarding)
ARG USERNAME=gnc_user
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME -s /bin/bash \
    && apt-get update || true \
    && apt-get install -y sudo \
    && echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME \
    && usermod -aG video $USERNAME && usermod -aG render $USERNAME || true
USER $USERNAME

WORKDIR /home/$USERNAME

# 5. Build the Micro XRCE-DDS Agent
RUN git clone https://github.com/eProsima/Micro-XRCE-DDS-Agent.git \
    && cd Micro-XRCE-DDS-Agent \
    && mkdir build && cd build \
    && cmake .. \
    && make -j$(nproc) \
    && sudo make install \
    && sudo ldconfig

# 6. Clone PX4 Autopilot (v1.15)
RUN git clone -b release/1.15 --recursive https://github.com/PX4/PX4-Autopilot.git

# 7. Setup the ROS 2 Workspace
RUN mkdir -p /home/$USERNAME/ros2_ws/src
WORKDIR /home/$USERNAME/ros2_ws

# Clone the EXACT MATCHING px4_msgs branch into the workspace
RUN git clone -b release/1.15 https://github.com/PX4/px4_msgs.git /home/$USERNAME/ros2_ws/src/px4_msgs

# SWITCHED: Path corrected to look inside the ros2_ws folder
COPY --chown=$USERNAME:$USERNAME ros2_ws/src/fup_adv/ /home/$USERNAME/ros2_ws/src/fup_adv/

COPY --chown=$USERNAME:$USERNAME px4_worlds/cylinders.sdf /home/$USERNAME/PX4-Autopilot/Tools/simulation/gz/worlds/cylinders.sdf

# --- INSTALL QGROUNDCONTROL ---
RUN cd /home/$USERNAME \
    && wget https://github.com/mavlink/qgroundcontrol/releases/download/v4.3.0/QGroundControl.AppImage \
    && chmod +x QGroundControl.AppImage \
    && ./QGroundControl.AppImage --appimage-extract \
    && rm QGroundControl.AppImage \
    && sudo chown -R $USERNAME:$USERNAME /home/$USERNAME/squashfs-root

# Build the ROS 2 workspace
RUN /bin/bash -c "source /opt/ros/humble/setup.bash && colcon build"

# --- RELOCATE GAZEBO WORLD TO IIT BOMBAY ---
RUN sed -i 's/<latitude_deg>.*<\/latitude_deg>/<latitude_deg>19.1313305<\/latitude_deg>/g' /home/$USERNAME/PX4-Autopilot/Tools/simulation/gz/worlds/default.sdf \
    && sed -i 's/<longitude_deg>.*<\/longitude_deg>/<longitude_deg>72.9179216<\/longitude_deg>/g' /home/$USERNAME/PX4-Autopilot/Tools/simulation/gz/worlds/default.sdf

# 8. Setup bash environment variables
RUN echo "source /opt/ros/humble/setup.bash" >> /home/$USERNAME/.bashrc \
    && echo "source /home/$USERNAME/ros2_ws/install/setup.bash" >> /home/$USERNAME/.bashrc \
    && echo "export GZ_VERSION=harmonic" >> /home/$USERNAME/.bashrc \
    && echo "alias start_agent='MicroXRCEAgent udp4 -p 8888'" >> /home/$USERNAME/.bashrc \
    && echo "alias refresh_gazebo='pkill -9 ruby; pkill -9 gz; pkill -9 px4'" >> /home/$USERNAME/.bashrc \
    && echo "export ROS_LOCALHOST_ONLY=1" >> /home/$USERNAME/.bashrc \
    && echo "export ROS_DOMAIN_ID=0" >> /home/$USERNAME/.bashrc \
    && echo "alias qgc='/home/$USERNAME/squashfs-root/AppRun'" >> /home/$USERNAME/.bashrc \
    && sudo chmod +x /home/$USERNAME/ros2_ws/src/fup_adv/launch_swarm.sh \
    # RESTORED: Appended the custom px4_worlds folder to Gazebo's resource path!
    && echo "export GZ_SIM_RESOURCE_PATH=\$GZ_SIM_RESOURCE_PATH:/home/$USERNAME/PX4-Autopilot/Tools/simulation/gz/worlds:/home/$USERNAME/PX4-Autopilot/Tools/simulation/gz/models:/home/$USERNAME/px4_worlds" >> /home/$USERNAME/.bashrc 

# --- PERMANENT FASTDDS NETWORK FIX ---
COPY --chown=gnc_user:gnc_user fastdds.xml /home/gnc_user/fastdds.xml

RUN echo "export FASTRTPS_DEFAULT_PROFILES_FILE=/home/gnc_user/fastdds.xml" >> /home/gnc_user/.bashrc \
    && echo "export ROS_LOCALHOST_ONLY=1" >> /home/gnc_user/.bashrc

CMD ["terminator"]
