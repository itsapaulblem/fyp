[CmdletBinding()]
param(
    [switch]$DryRun,
    [string]$Model = "qwen3.5:27b",
    [string]$OllamaBaseUrl = "http://127.0.0.1:11435",
    [int]$TimeoutSeconds = 7200
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$configPath = Join-Path $projectRoot "config\project_v0.3.0.json"
$cohortPath = Join-Path $projectRoot "config\pilot_cohort_v0.3.0.json"
$outputRoot = Join-Path $projectRoot "output"
$modelFolder = $Model.Replace(":", "_")

$config = Get-Content -Raw -LiteralPath $configPath | ConvertFrom-Json
$cohort = Get-Content -Raw -LiteralPath $cohortPath | ConvertFrom-Json
$configHash = (Get-FileHash -LiteralPath $configPath -Algorithm SHA256).Hash.ToLowerInvariant()
$compatibleConfigHashes = @($configHash)
if ($null -ne $config.input_feasibility.compatible_pilot_config_sha256) {
    $compatibleConfigHashes += @(
        $config.input_feasibility.compatible_pilot_config_sha256 |
            ForEach-Object { ([string]$_).ToLowerInvariant() }
    )
}

if ($config.status -ne "draft_train_only") {
    throw "Sampling pilot requires config status draft_train_only."
}
if ($config.generation.num_gpu -ne 0) {
    throw "This CPU runner requires generation.num_gpu = 0."
}
if ($config.generation.num_ctx -ne 32768) {
    throw "This CPU runner requires generation.num_ctx = 32768."
}
if ($cohort.condition -ne "B0_frames_only") {
    throw "Pilot cohort must use B0_frames_only."
}
if ($cohort.maximum_edge -ne 672) {
    throw "Pilot cohort maximum_edge must be 672."
}
if ($Model -notin @($config.models)) {
    throw "Model $Model is not listed in the active project configuration."
}

function Test-CompletedCell {
    param(
        [Parameter(Mandatory)]
        [string]$ClipId,
        [Parameter(Mandatory)]
        [int]$FrameCount
    )

    $clipRoot = Join-Path $outputRoot "B0_frames_only\$modelFolder\$ClipId"
    if (-not (Test-Path -LiteralPath $clipRoot -PathType Container)) {
        return $false
    }

    $metadataFiles = @(
        Get-ChildItem -LiteralPath $clipRoot -Recurse -Filter "metadata.txt" -File
    )
    foreach ($metadataFile in $metadataFiles) {
        $metadata = Get-Content -Raw -LiteralPath $metadataFile.FullName
        $hasCompatibleConfig = @(
            $compatibleConfigHashes |
                Where-Object { $metadata.Contains(('config_sha256: "{0}"' -f $_)) }
        ).Count -gt 0
        $matchesCell = (
            $metadata.Contains('condition: "B0_frames_only"') -and
            $metadata.Contains(('dataset_b_clip_id: "{0}"' -f $ClipId)) -and
            $metadata.Contains("dataset_b_frame_count: $FrameCount") -and
            $metadata.Contains("maximum_edge: $($cohort.maximum_edge)") -and
            $hasCompatibleConfig -and
            $metadata.Contains(('model: "{0}"' -f $Model)) -and
            $metadata.Contains('run_status: "complete"') -and
            $metadata.Contains('answer_format_status: "valid"')
        )
        if ($matchesCell) {
            return $true
        }
    }
    return $false
}

$pending = [System.Collections.Generic.List[object]]::new()
$skipped = [System.Collections.Generic.List[object]]::new()

foreach ($clipId in @($cohort.clip_ids)) {
    foreach ($frameCount in @($cohort.frame_counts)) {
        $cell = [PSCustomObject]@{
            ClipId = [string]$clipId
            FrameCount = [int]$frameCount
        }
        if (Test-CompletedCell -ClipId $cell.ClipId -FrameCount $cell.FrameCount) {
            $skipped.Add($cell)
        }
        else {
            $pending.Add($cell)
        }
    }
}

Write-Host "Pilot cohort: $($cohort.cohort_id)"
Write-Host "Config SHA-256: $configHash"
Write-Host "Compatible preserved config hashes: $($compatibleConfigHashes -join ',')"
Write-Host "Model: $Model"
Write-Host "Generation: num_ctx=$($config.generation.num_ctx), num_gpu=$($config.generation.num_gpu)"
Write-Host "Completed cells to skip: $($skipped.Count)"
foreach ($cell in $skipped) {
    Write-Host "  SKIP $($cell.ClipId) F$($cell.FrameCount)"
}
Write-Host "Pending cells to run: $($pending.Count)"
foreach ($cell in $pending) {
    Write-Host "  RUN  $($cell.ClipId) F$($cell.FrameCount)"
}

if ($DryRun) {
    Write-Host "Dry run only. No Ollama request was sent."
    exit 0
}

if ($pending.Count -eq 0) {
    Write-Host "All 32 pilot cells are already complete and valid for this config."
    exit 0
}

$env:OLLAMA_BASE_URL = $OllamaBaseUrl
$env:OLLAMA_TIMEOUT_SECONDS = $TimeoutSeconds.ToString()

try {
    $tags = Invoke-RestMethod -Uri "$OllamaBaseUrl/api/tags" -Method Get -TimeoutSec 30
}
catch {
    throw "Cannot reach Ollama at $OllamaBaseUrl. Confirm that the SSH tunnel is open. $($_.Exception.Message)"
}

$installedModels = @($tags.models | ForEach-Object { $_.model })
if ($Model -notin $installedModels) {
    throw "Ollama did not report model $Model."
}

$logDirectory = Join-Path $outputRoot "batch_logs"
New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssffffffZ")
$logPath = Join-Path $logDirectory "sampling_pilot_cpu_$timestamp.log"

$completedNow = 0
Start-Transcript -LiteralPath $logPath | Out-Null
try {
    foreach ($cell in $pending) {
        Write-Host ""
        Write-Host "START $($cell.ClipId) F$($cell.FrameCount) at $((Get-Date).ToString('s'))"

        $uvArguments = @(
            "run",
            "football-coach",
            "run-pair",
            $cell.ClipId,
            "--condition",
            "B0_frames_only",
            "--model",
            $Model,
            "--frame-count-b",
            $cell.FrameCount,
            "--maximum-edge",
            [int]$cohort.maximum_edge
        )
        & uv @uvArguments

        if ($LASTEXITCODE -ne 0) {
            throw "Cell $($cell.ClipId) F$($cell.FrameCount) failed with exit code $LASTEXITCODE."
        }
        if (-not (Test-CompletedCell -ClipId $cell.ClipId -FrameCount $cell.FrameCount)) {
            throw "Cell $($cell.ClipId) F$($cell.FrameCount) returned without a valid preserved run."
        }

        $completedNow += 1
        Write-Host "DONE  $($cell.ClipId) F$($cell.FrameCount) at $((Get-Date).ToString('s'))"
    }
}
finally {
    Stop-Transcript | Out-Null
}

Write-Host ""
Write-Host "Newly completed cells: $completedNow"
Write-Host "Previously completed cells: $($skipped.Count)"
Write-Host "Expected total cells: 32"
Write-Host "Batch log: $logPath"
