# 1. Install Docker (if not already)
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker     # apply group change in current shell

# 2. Allow GUI apps from container to use display
xhost +local:docker

# 3. Clone the repo
cd ~
git clone https://github.com/Cramer54/px4-ros2-consensus-demo.git
cd px4-ros2-consensus-demo

# 4. Build Docker image (~30 min, unattended)
chmod +x docker/build.sh docker/run.sh
./docker/build.sh

# 5. Once built, run the container
./docker/run.sh

##Step 1: Verify they have prerequisites (1 min)

lsb_release -a
which docker || echo "no docker"
nvidia-smi 2>/dev/null || echo "no nvidia"
free -h | head -2

##If docker installation missing

sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version
docker run hello-world

xhost +local:docker

#clone the repo
cd ~
git clone https://github.com/Cramer54/px4-ros2-consensus-demo.git
cd px4-ros2-consensus-demo

chmod +x docker/build.sh docker/run.sh
#docker running for the container
./docker/run.sh
