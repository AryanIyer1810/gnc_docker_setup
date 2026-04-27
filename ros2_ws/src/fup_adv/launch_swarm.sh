#!/bin/bash
# Usage: launch_swarm [number_of_drones]
NUM_DRONES=${1:-3}
SPACING=1   

cd /home/gnc_user/PX4-Autopilot

# REMOVED _depth from the compiler target
if [ ! -f "build/px4_sitl_default/bin/px4" ]; then
    echo "Compiling PX4 SITL..."
    DONT_RUN=1 make px4_sitl gz_x500
fi

echo "Starting Micro XRCE-DDS Agent..."
MicroXRCEAgent udp4 -p 8888 &
sleep 2

for i in $(seq 1 $NUM_DRONES); do
    echo "Spawning Drone $i (QGC Vehicle $((i+1))) into ROS 2 Namespace /px4_$i/fmu/..."
    IDX=$((i-1))
    
    X_POS=0
    Y_POS=$((IDX * SPACING))
    Z_POS=0.5 
    
    if [ $i -eq 1 ]; then
        # REMOVED _depth from PX4_SIM_MODEL
        PX4_GZ_WORLD=cylinders PX4_SYS_AUTOSTART=4001 PX4_GZ_MODEL_POSE="$X_POS,$Y_POS,$Z_POS" PX4_SIM_MODEL=gz_x500 ./build/px4_sitl_default/bin/px4 -i $i &
        echo "Waiting 15 seconds for Gazebo physics to stabilize..."
        sleep 15 
    else
        # REMOVED _depth from PX4_SIM_MODEL
        PX4_GZ_WORLD=cylinders PX4_GZ_STANDALONE=1 PX4_SYS_AUTOSTART=4001 PX4_GZ_MODEL_POSE="$X_POS,$Y_POS,$Z_POS" PX4_SIM_MODEL=gz_x500 ./build/px4_sitl_default/bin/px4 -i $i &
        sleep 5
    fi
done

echo "$NUM_DRONES drones deployed! Wait for 'Ready for takeoff!' before launching the ROS 2 node."
trap "pkill -9 px4; pkill -9 ruby; pkill -9 gz; kill -9 0" SIGINT SIGTERM EXIT
wait

