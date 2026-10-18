Write-Host "Checking if Docker is running..."
$dockerReady = $false
for ($i=0; $i -lt 30; $i++) {
    docker info > $null 2>&1
    if ($LASTEXITCODE -eq 0) {
        $dockerReady = $true
        break
    }
    Write-Host "Waiting for Docker Desktop to start ($i/30)..."
    Start-Sleep -Seconds 5
}

if (-not $dockerReady) {
    Write-Host "Error: Docker Desktop failed to start within the timeout period."
    exit 1
}

Write-Host "Building and starting Docker containers..."
docker-compose up -d --build

Write-Host "Waiting for postgres to be ready..."
Start-Sleep -Seconds 10

Write-Host "Running database migrations..."
docker-compose exec backend alembic upgrade head

Write-Host "Seeding database..."
docker-compose exec backend python scripts/seed_compliance_rules.py

Write-Host "Running backend tests..."
docker-compose exec backend python test_backend.py

Write-Host "Tests completed! To stop the containers, run: docker-compose down"
