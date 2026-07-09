param(
    [Parameter(Position = 0)]
    [string]$Target = "help"
)

function Invoke-Clean {
    Write-Host "Running clean..."
    docker compose down --rmi all --volumes --remove-orphans
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

function Invoke-RunDockerCompose {
    Invoke-Clean
    Write-Host "Syncing dependencies..."
    uv sync
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host "Starting services..."
    docker compose up --build -d
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

function Invoke-RunEvalRetriever {
    Write-Host "Syncing dependencies..."
    uv sync
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host "Running eval retriever..."
    $env:PYTHONPATH = "$PWD\apps\api;$PWD\apps\api\src;$env:PYTHONPATH;$PWD"
    uv run --env-file .env python -m evals.eval_retriever
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

function Invoke-RunEvalRetrieverExtended {
    Write-Host "Syncing dependencies..."
    uv sync
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host "Running extended eval retriever..."
    Push-Location "apps\api\src"
    $env:PYTHONPATH = "$PWD\apps\api;$PWD\apps\api\src;$env:PYTHONPATH;$PWD"
    uv run --env-file ../../../.env python -m evals.eval_retriever_extended
    $exitCode = $LASTEXITCODE
    Pop-Location
    if ($exitCode -ne 0) { exit $exitCode }
}

switch ($Target) {
    "run-docker-compose"           { Invoke-RunDockerCompose }
    "clean"                        { Invoke-Clean }
    "run-eval-retriever"           { Invoke-RunEvalRetriever }
    "run-eval-retriever-extended"  { Invoke-RunEvalRetrieverExtended }
    default {
        Write-Host "Usage: .\make.ps1 <target>"
        Write-Host ""
        Write-Host "Targets:"
        Write-Host "  run-docker-compose           Clean, sync deps, and start all services"
        Write-Host "  clean                        Stop and remove all containers, images, and volumes"
        Write-Host "  run-eval-retriever           Sync deps and run the retriever eval suite"
        Write-Host "  run-eval-retriever-extended  Sync deps and run the extended retriever eval suite"
    }
}
