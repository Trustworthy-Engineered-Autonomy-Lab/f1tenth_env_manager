#!/usr/bin/env bash
set -e

# ---- CHANGE THIS TO YOUR ACTUAL ROS2 WORKSPACE ROOT ----
WS_DIR="/sim_ws"
# Example alternatives:
# WS_DIR="/sim_ws"
# WS_DIR="/root/f1tenth_ws"

SESSION_NAME="f1sim"

cd "$WS_DIR"

echo "Using workspace: $WS_DIR"

# Kill old tmux session if it exists
tmux has-session -t "$SESSION_NAME" 2>/dev/null && tmux kill-session -t "$SESSION_NAME"

# Create a new detached tmux session
tmux new-session -d -s "$SESSION_NAME"

# Pane 0: build + simulator
tmux send-keys -t "$SESSION_NAME":0.0 "
source /opt/ros/foxy/setup.bash
source install/local_setup.bash
colcon build
source install/local_setup.bash
echo 'Starting simulator...'
ros2 launch f1tenth_gym_ros gym_bridge_launch.py
" C-m

# Split for FTG
tmux split-window -h -t "$SESSION_NAME":0
tmux send-keys -t "$SESSION_NAME":0.1 "
cd $WS_DIR
sleep 8
source /opt/ros/foxy/setup.bash
source install/local_setup.bash
colcon build
echo 'Starting FTG controller...'
ros2 run sim_ftg both
" C-m

# Split bottom for manager
tmux split-window -v -t "$SESSION_NAME":0.1
tmux send-keys -t "$SESSION_NAME":0.2 "
cd $WS_DIR
sleep 10
source /opt/ros/foxy/setup.bash
source install/local_setup.bash
colcon build
echo 'Starting env manager...'
ros2 run env_manager main
" C-m

# Optional: resize panes a bit
tmux select-layout -t "$SESSION_NAME" tiled

# Attach to session
tmux attach -t "$SESSION_NAME"