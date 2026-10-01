Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$projectDir = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $projectDir

$paths = @(
    'README.md',
    'pyproject.toml',
    'uv.lock',
    'src',
    'scripts/run_fixed_development_remote.sh',
    'config/fixed_unattended_development_v0.4.3.json',
    'config/project_v0.4.0_cpu.json',
    'config/label_informed_development_order_v0.4.1.json',
    'config/prompt_development_cohort_v0.4.0.json',
    'input_prompts/v0.4/p1_recognition.txt',
    'input_prompts/v0.4/p1_revision.txt',
    'input_prompts/v0.4/p1_coaching.txt',
    'input_prompts/v0.4/p2_progressive_hint.txt',
    'input_prompts/v0.4/p2_fixed_hints.v1.txt',
    'input_prompts/v0.4/p3_visible_cue_revision.txt',
    'output/v0.4/prompt_chain/P3_visible_cue_hint/B-TRAIN-0054_visible_cues.v1.txt',
    'output/v0.4/prompt_chain/P3_visible_cue_hint/B-TRAIN-0040_visible_cues.v1.txt',
    'output/v0.4/prompt_chain/P3_visible_cue_hint/B-TRAIN-0051_visible_cues.v1.txt',
    'artifacts/model_inputs/dataset_b/B-TRAIN-0054/uniform_30_edge_672',
    'artifacts/model_inputs/dataset_b/B-TRAIN-0040/uniform_30_edge_672',
    'artifacts/model_inputs/dataset_b/B-TRAIN-0051/uniform_30_edge_672'
)

foreach ($path in $paths) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Required bundle input is missing: $path"
    }
}

$transferDir = Join-Path $projectDir 'artifacts/transfer'
New-Item -ItemType Directory -Path $transferDir -Force | Out-Null
$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ')
$archive = Join-Path $transferDir "fixed_unattended_v2_$stamp.tar.gz"
& tar.exe --exclude='*/__pycache__' --exclude='*/__pycache__/*' --exclude='*.pyc' -czf $archive @paths
if ($LASTEXITCODE -ne 0) {
    throw "tar failed with exit code $LASTEXITCODE"
}
$digest = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
Write-Output "Bundle: $archive"
Write-Output "SHA-256: $digest"
Write-Output 'Private sampled frames are included. Transfer only to the authorized workstation.'
