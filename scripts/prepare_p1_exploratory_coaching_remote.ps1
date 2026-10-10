Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$projectDir = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $projectDir
$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ')
$source = 'output/v0.4/prompt_chain/P1_human_guided/qwen3.5_27b/B-TRAIN-0054/20260930T083320329816Z'
$names = @(
    'metadata.txt',
    'stage_1_prompt.txt', 'stage_1_response.txt', 'stage_1_raw_api_response.json',
    'initial_review.json', 'initial_review_snapshot.json', 'human_feedback.txt',
    'stage_2_revision_prompt.txt', 'stage_2_revision_response.txt',
    'stage_2_revision_raw_api_response.json', 'revision_review.json',
    'revision_review_snapshot.json', 'human_feedback_2.txt',
    'stage_3_revision_prompt.txt', 'stage_3_revision_response.txt',
    'stage_3_revision_raw_api_response.json', 'revision_review_2.json'
)
$hashes = [ordered]@{}
foreach ($name in $names) {
    $path = Join-Path $source $name
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Missing 0054 source: $path"
    }
    $hashes[$name] = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
}
$transferDir = Join-Path $projectDir 'artifacts/transfer'
New-Item -ItemType Directory -Path $transferDir -Force | Out-Null
$manifest = Join-Path $transferDir 'p1_0054_exploratory_coaching_v1_manifest.json'
$payload = [ordered]@{
    variant = 'p1_unapproved_recognition_coaching_probe_v1'
    source_dir = $source
    output_dir = "output/v0.4/prompt_chain/P1_human_guided/exploratory_unapproved_recognition_v1/qwen3.5_27b/B-TRAIN-0054/$stamp"
    batch_sha256 = (Get-FileHash -LiteralPath 'config/fixed_unattended_development_v0.4.3.json' -Algorithm SHA256).Hash.ToLowerInvariant()
    config_sha256 = (Get-FileHash -LiteralPath 'config/project_v0.4.0_cpu.json' -Algorithm SHA256).Hash.ToLowerInvariant()
    coaching_prompt_sha256 = (Get-FileHash -LiteralPath 'input_prompts/v0.4/p1_coaching.txt' -Algorithm SHA256).Hash.ToLowerInvariant()
    source_sha256 = $hashes
}
[IO.File]::WriteAllText($manifest, ($payload | ConvertTo-Json -Depth 10) + "`n", [Text.UTF8Encoding]::new($false))

$env:UV_CACHE_DIR = Join-Path $projectDir '.uv-cache'
& uv run --system-certs python -m football_coach.remote_p1_exploratory_coaching `
    --manifest artifacts/transfer/p1_0054_exploratory_coaching_v1_manifest.json --validate-only
if ($LASTEXITCODE -ne 0) { throw "Local preflight failed: $LASTEXITCODE" }

$archive = Join-Path $transferDir "p1_0054_exploratory_coaching_v1_$stamp.tar.gz"
& tar.exe -czf $archive `
    src/football_coach/remote_p1_exploratory_coaching.py `
    scripts/run_p1_exploratory_coaching_remote.sh `
    artifacts/transfer/p1_0054_exploratory_coaching_v1_manifest.json
if ($LASTEXITCODE -ne 0) { throw "tar failed: $LASTEXITCODE" }
Write-Output "Archive: $archive"
Write-Output "SHA-256: $((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant())"
Write-Output 'No frames or private reference contents are included; the remote project already has the frozen sampled images.'
