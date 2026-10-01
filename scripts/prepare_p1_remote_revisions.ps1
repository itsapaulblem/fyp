Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$projectDir = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $projectDir

$runs = @(
    @{ ClipId = 'B-TRAIN-0040'; Relative = 'output/v0.4/prompt_chain/P1_human_guided/fixed_unattended_v2/qwen3.5_27b/B-TRAIN-0040/20260930T104115914624Z' },
    @{ ClipId = 'B-TRAIN-0051'; Relative = 'output/v0.4/prompt_chain/P1_human_guided/fixed_unattended_v2/qwen3.5_27b/B-TRAIN-0051/20260930T111146551522Z' },
    @{ ClipId = 'B-TRAIN-0054'; Relative = 'output/v0.4/prompt_chain/P1_human_guided/qwen3.5_27b/B-TRAIN-0054/20260930T083320329816Z' }
)
$sourceFiles = @('metadata.txt', 'stage_1_prompt.txt', 'stage_1_response.txt', 'stage_1_raw_api_response.json', 'initial_review.json')
$entries = @()
foreach ($run in $runs) {
    $hashes = [ordered]@{}
    foreach ($filename in $sourceFiles) {
        $path = Join-Path $run.Relative $filename
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing P1 source: $path" }
        $hashes[$filename] = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    if (Test-Path -LiteralPath (Join-Path $run.Relative 'stage_2_revision_prompt.txt')) {
        throw "P1 revision already attempted: $($run.ClipId)"
    }
    $review = Get-Content -LiteralPath (Join-Path $run.Relative 'initial_review.json') -Raw | ConvertFrom-Json
    if ($review.notes -eq 'PENDING_REVIEW' -or $review.feedback.Count -eq 0) {
        throw "P1 review is pending or does not request a correction: $($run.ClipId)"
    }
    $reference = "data/video_b/review/$($run.ClipId).json"
    if (-not (Test-Path -LiteralPath $reference -PathType Leaf)) { throw "Missing local reference: $reference" }
    $entries += [ordered]@{
        clip_id = $run.ClipId
        run_dir = $run.Relative
        source_sha256 = $hashes
        human_reference_sha256 = (Get-FileHash -LiteralPath $reference -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}

$transferDir = Join-Path $projectDir 'artifacts/transfer'
New-Item -ItemType Directory -Path $transferDir -Force | Out-Null
$manifest = Join-Path $transferDir 'p1_remote_revisions_v1_manifest.json'
$payload = [ordered]@{
    variant = 'portable_p1_revisions_v1'
    batch_sha256 = (Get-FileHash -LiteralPath 'config/fixed_unattended_development_v0.4.3.json' -Algorithm SHA256).Hash.ToLowerInvariant()
    config_sha256 = (Get-FileHash -LiteralPath 'config/project_v0.4.0_cpu.json' -Algorithm SHA256).Hash.ToLowerInvariant()
    runs = $entries
}
$json = $payload | ConvertTo-Json -Depth 10
[IO.File]::WriteAllText($manifest, $json + "`n", [Text.UTF8Encoding]::new($false))

# Remote preflight is authoritative. In particular, it verifies the sampled
# images used for inference on the workstation before any revision call.

$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ')
$archive = Join-Path $transferDir "p1_remote_revisions_v1_$stamp.tar.gz"
$paths = @(
    'src/football_coach/remote_p1_revisions.py',
    'scripts/run_p1_remote_revisions.sh',
    'artifacts/transfer/p1_remote_revisions_v1_manifest.json',
    'output/v0.4/prompt_chain/P1_human_guided/fixed_unattended_v2/qwen3.5_27b/B-TRAIN-0040/20260930T104115914624Z/initial_review.json',
    'output/v0.4/prompt_chain/P1_human_guided/fixed_unattended_v2/qwen3.5_27b/B-TRAIN-0051/20260930T111146551522Z/initial_review.json',
    'output/v0.4/prompt_chain/P1_human_guided/qwen3.5_27b/B-TRAIN-0054/20260930T083320329816Z'
)
& tar.exe -czf $archive @paths
if ($LASTEXITCODE -ne 0) { throw "tar failed with exit code $LASTEXITCODE" }
$digest = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
Write-Output "Archive: $archive"
Write-Output "SHA-256: $digest"
Write-Output 'Contents: portable runner, frozen manifest, two completed P1 reviews, and existing B-TRAIN-0054 P1 first pass.'
Write-Output 'No private reference contents or raw Dataset B archives are included.'
