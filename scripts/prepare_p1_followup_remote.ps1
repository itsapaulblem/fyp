Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$projectDir = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $projectDir

$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ')
$b40Original = 'output/v0.4/prompt_chain/P1_human_guided/fixed_unattended_v2/qwen3.5_27b/B-TRAIN-0040/20260930T104115914624Z'
$b40Staging = 'artifacts/transfer/p1_followup_b40_clean_source'
$b40SourceFiles = @(
    'metadata.txt', 'stage_1_prompt.txt', 'stage_1_response.txt',
    'stage_1_raw_api_response.json', 'initial_review.json',
    'initial_review_snapshot.json', 'human_feedback.txt',
    'stage_2_revision_prompt.txt', 'stage_2_revision_response.txt',
    'stage_2_revision_raw_api_response.json', 'revision_review.json',
    'coaching_focus.txt'
)
if (@(Get-ChildItem -LiteralPath $b40Original -File -Filter 'stage_3_*').Count -gt 0 -or
    (Test-Path -LiteralPath (Join-Path $b40Original 'revision_review_snapshot.json'))) {
    throw 'Incomplete B-TRAIN-0040 coaching artifacts remain; do not bundle them'
}
New-Item -ItemType Directory -Path $b40Staging -Force | Out-Null
foreach ($filename in $b40SourceFiles) {
    $original = Join-Path $b40Original $filename
    $staged = Join-Path $b40Staging $filename
    if (-not (Test-Path -LiteralPath $original -PathType Leaf)) {
        throw "Missing abandoned B-TRAIN-0040 source: $original"
    }
    if (Test-Path -LiteralPath $staged) {
        $originalHash = (Get-FileHash -LiteralPath $original -Algorithm SHA256).Hash
        $stagedHash = (Get-FileHash -LiteralPath $staged -Algorithm SHA256).Hash
        if ($originalHash -ne $stagedHash) {
            throw "Existing B-TRAIN-0040 staging differs: $staged"
        }
    } else {
        Copy-Item -LiteralPath $original -Destination $staged
    }
}

$runs = @(
    @{ ClipId = 'B-TRAIN-0040'; Action = 'focused_coaching'; Relative = $b40Staging; Retry = "output/v0.4/prompt_chain/P1_human_guided/portable_followup_v2/qwen3.5_27b/B-TRAIN-0040/$stamp" },
    @{ ClipId = 'B-TRAIN-0051'; Action = 'standard_coaching'; Relative = 'output/v0.4/prompt_chain/P1_human_guided/fixed_unattended_v2/qwen3.5_27b/B-TRAIN-0051/20260930T111146551522Z' },
    @{ ClipId = 'B-TRAIN-0054'; Action = 'explicit_recognition_revision'; Relative = 'output/v0.4/prompt_chain/P1_human_guided/qwen3.5_27b/B-TRAIN-0054/20260930T083320329816Z' }
)
$commonSource = @(
    'metadata.txt', 'stage_1_prompt.txt', 'stage_1_response.txt',
    'stage_1_raw_api_response.json', 'initial_review.json',
    'initial_review_snapshot.json', 'human_feedback.txt',
    'stage_2_revision_prompt.txt', 'stage_2_revision_response.txt',
    'stage_2_revision_raw_api_response.json', 'revision_review.json'
)
$entries = @()
$reviewPaths = @()
foreach ($run in $runs) {
    $source = @($commonSource)
    if ($run.Action -eq 'focused_coaching') {
        $source += @('coaching_focus.txt')
    }
    $hashes = [ordered]@{}
    foreach ($filename in $source) {
        $path = Join-Path $run.Relative $filename
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw "Missing P1 source: $path"
        }
        $hashes[$filename] = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    if (Test-Path -LiteralPath (Join-Path $run.Relative 'stage_3_coaching_prompt.txt')) {
        throw "P1 follow-up already attempted: $($run.ClipId)"
    }
    if (Test-Path -LiteralPath (Join-Path $run.Relative 'stage_3_coaching_response.txt')) {
        throw "P1 coaching already completed or partially returned: $($run.ClipId)"
    }
    if (Test-Path -LiteralPath (Join-Path $run.Relative 'stage_3_revision_prompt.txt')) {
        throw "P1 follow-up already attempted: $($run.ClipId)"
    }
    $review = Get-Content -LiteralPath (Join-Path $run.Relative 'revision_review.json') -Raw | ConvertFrom-Json
    if ($review.notes -eq 'PENDING_REVIEW') { throw "Pending review: $($run.ClipId)" }
    if ($run.Action -eq 'explicit_recognition_revision' -and $review.feedback.Count -eq 0) {
        throw 'B-TRAIN-0054 requires explicit frame-cited feedback'
    }
    if ($run.Action -ne 'explicit_recognition_revision' -and $review.feedback.Count -ne 0) {
        throw "Coaching requires approval with empty feedback: $($run.ClipId)"
    }
    $reference = "data/video_b/review/$($run.ClipId).json"
    if (-not (Test-Path -LiteralPath $reference -PathType Leaf)) {
        throw "Missing local human reference: $reference"
    }
    $entries += [ordered]@{
        clip_id = $run.ClipId
        action = $run.Action
        run_dir = $run.Relative
        source_sha256 = $hashes
        human_reference_sha256 = (Get-FileHash -LiteralPath $reference -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    if ($run.Action -eq 'focused_coaching') {
        $entries[-1]['retry_run_dir'] = $run.Retry
    } else {
        $reviewPaths += Join-Path $run.Relative 'revision_review.json'
    }
}

$transferDir = Join-Path $projectDir 'artifacts/transfer'
New-Item -ItemType Directory -Path $transferDir -Force | Out-Null
$manifest = Join-Path $transferDir 'p1_followup_v2_manifest.json'
$payload = [ordered]@{
    variant = 'portable_p1_followup_v2'
    batch_sha256 = (Get-FileHash -LiteralPath 'config/fixed_unattended_development_v0.4.3.json' -Algorithm SHA256).Hash.ToLowerInvariant()
    config_sha256 = (Get-FileHash -LiteralPath 'config/project_v0.4.0_cpu.json' -Algorithm SHA256).Hash.ToLowerInvariant()
    extension_sha256 = (Get-FileHash -LiteralPath 'config/p1_multi_revision_extension_v0.4.4.json' -Algorithm SHA256).Hash.ToLowerInvariant()
    runs = $entries
}
$json = $payload | ConvertTo-Json -Depth 10
[IO.File]::WriteAllText($manifest, $json + "`n", [Text.UTF8Encoding]::new($false))

$env:UV_CACHE_DIR = Join-Path $projectDir '.uv-cache'
& uv run --system-certs python -m football_coach.remote_p1_followup `
    --manifest artifacts/transfer/p1_followup_v2_manifest.json --validate-only
if ($LASTEXITCODE -ne 0) { throw "Local P1 follow-up preflight failed: $LASTEXITCODE" }

$archive = Join-Path $transferDir "p1_followup_v2_$stamp.tar.gz"
$paths = @(
    'src/football_coach/remote_p1_followup.py',
    'scripts/run_p1_followup_remote.sh',
    'config/p1_multi_revision_extension_v0.4.4.json',
    'artifacts/transfer/p1_followup_v2_manifest.json',
    'artifacts/transfer/p1_followup_b40_clean_source'
) + $reviewPaths
& tar.exe -czf $archive @paths
if ($LASTEXITCODE -ne 0) { throw "tar failed with exit code $LASTEXITCODE" }
$digest = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
Write-Output "Archive: $archive"
Write-Output "SHA-256: $digest"
Write-Output 'Contains only follow-up code and researcher reviews/focus; no raw video or private reference contents.'
