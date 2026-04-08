$containerName = "f1tenth_gym_ros-sim-1"

Write-Host "[1/3] Starting docker compose..."
docker-compose up -d

Write-Host "[2/3] Waiting for container to be ready..."
do {
    Start-Sleep -Seconds 1
    $running = docker ps --format "{{.Names}}" | Select-String -Pattern "^$containerName$"
} until ($running)

Write-Host "[3/3] Launching automation script inside container..."
docker exec -it $containerName sh -lc "/sim_ws/auto_run_sim.sh"