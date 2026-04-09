# F1TENTH Automation Setup

This guide explains where to place the automation files and how to run them for the `f1tenth_gym_ros` simulator setup.

## Files and where they go

### 1. Host launcher

Create this file on your **Windows host machine** in the root of your repo:

`C:\TeaLab\f1tenth_gym_ros\start_f1tenth.ps1`

This is the script you run from PowerShell.

**IMPORTANT** You **MUST** create a folder in your local `f1tenth_gym_ros` folder called `src` and place the `sim_ftg` and the `f1tenth_env_manager` packages in there. The easiest way to do this is just to copy the `f1tenth_env_manager` folder and the `sim_ftg` folder from this repo. 

### 2. Container automation script

Create this file **inside the Docker container workspace AND inside your repo root** at:

`/sim_ws/auto_run_sim.sh`
`C:\TeaLab\f1tenth_gym_ros\auto_run_sim.sh`

This script runs inside the container and should:

* source ROS 2
* build with `colcon build`
* launch the simulator
* launch FTG
* launch the manager node

## Important notes

* `start_f1tenth.ps1` runs on your **host machine**.
* `auto_run_sim.sh` runs **inside the container** place it inside the container **AND** inside your f1tenth_gym_ros repo next to `start_f1tenth.ps1`.
* Since you are on Windows PowerShell, `chmod` will **not** work on the host.
* `chmod +x` is only needed **inside the Linux container**.

## Commands to run

### On the Windows host

Open PowerShell in:

`C:\TeaLab\f1tenth_gym_ros`

If PowerShell blocks script execution, run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

Then run the launcher:

```powershell
.\start_f1tenth.ps1
```

## Commands to run inside the container

First make sure Docker is up, then enter the container manually if needed:

Once inside the container, place `auto_run_sim.sh` in `/sim_ws` and make it executable:

```bash
cd /sim_ws
chmod +x auto_run_sim.sh
```

You can test it manually inside the container with:

```bash
/sim_ws/auto_run_sim.sh
```

## Quick verification commands

From PowerShell on the host:

```powershell
docker exec -it f1tenth_gym_ros-sim-1 sh -lc "ls /sim_ws"
```

To check that the automation script exists:

```powershell
docker exec -it f1tenth_gym_ros-sim-1 sh -lc "ls -l /sim_ws/auto_run_sim.sh"
```

## Typical workflow

1. Save `start_f1tenth.ps1` in the repo root on Windows.
2. Put `auto_run_sim.sh` in `/sim_ws` inside the container.
3. Run `chmod +x /sim_ws/auto_run_sim.sh` inside the container one time.
4. From PowerShell, run `./start_f1tenth.ps1`.
5. The script should:

   * start Docker
   * wait for the container
   * enter the container
   * start a `tmux` session
   * build the workspace
   * launch the simulator
   * launch FTG
   * launch the manager

## If something fails

### `chmod` not recognized

That is normal on Windows. Run `chmod` only inside the container.

### `auto_run_sim.sh: not found`

The file is not in `/sim_ws`, or the path is wrong.

### Git Bash path errors

Run the host launcher from **PowerShell**, not Git Bash.
