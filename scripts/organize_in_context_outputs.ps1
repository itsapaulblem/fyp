param([switch]$Apply)

$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$sourceRoot = [IO.Path]::GetFullPath((Join-Path $projectRoot 'output\in_context_events'))
$targetRoot = [IO.Path]::GetFullPath((Join-Path $projectRoot 'output\in_context_learning'))
$mapping = @(
    @{ Source='comparison_v1'; Destination='corner\B-TRAIN-0025\mixed_demonstrations'; Wrapper='b25_exploratory_override_v1' },
    @{ Source='two_corner_examples_v1'; Destination='corner\B-TRAIN-0025\corner_demonstrations'; Wrapper='b25_exploratory_v1' },
    @{ Source='b25_explicit_correction_v1'; Destination='corner\B-TRAIN-0025\human_correction'; Wrapper=$null },
    @{ Source='b25_corner_conditioned_coaching_v1'; Destination='corner\B-TRAIN-0025\label_conditioned_coaching'; Wrapper='exploratory_probe_v1' },
    @{ Source='two_penalty_examples_v1'; Destination='penalty\E-0127\demonstrations'; Wrapper='e0127_exploratory_v1' },
    @{ Source='e0127_explicit_correction_v1'; Destination='penalty\E-0127\human_correction'; Wrapper='recognition_revision' }
)

function Assert-Contained([string]$Path, [string]$Parent) {
    $resolved = [IO.Path]::GetFullPath($Path)
    if (-not $resolved.StartsWith($Parent.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path escapes intended output directory: $resolved"
    }
    return $resolved
}

function Assert-NoLinks([string]$Path) {
    $items = @(Get-Item -LiteralPath $Path) + @(Get-ChildItem -LiteralPath $Path -Force -Recurse)
    foreach ($item in $items) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw "Refusing to traverse a link/reparse point: $($item.FullName)"
        }
    }
}

if (-not (Test-Path -LiteralPath $sourceRoot)) {
    throw "Source output directory not found: $sourceRoot. No changes made."
}
Assert-NoLinks $sourceRoot
if (Test-Path -LiteralPath $targetRoot) { Assert-NoLinks $targetRoot }
$known = @($mapping | ForEach-Object { $_.Source })
$unknown = @(Get-ChildItem -LiteralPath $sourceRoot -Directory | Where-Object { $_.Name -notin $known })
if ($unknown.Count) {
    throw "Unexpected experiment directories; review before moving: $($unknown.Name -join ', ')"
}

$plan = @()
foreach ($entry in $mapping) {
    $source = Assert-Contained (Join-Path $sourceRoot $entry.Source) $sourceRoot
    $destination = Assert-Contained (Join-Path $targetRoot $entry.Destination) $targetRoot
    if (-not (Test-Path -LiteralPath $source)) { continue }
    if (Test-Path -LiteralPath $destination) { throw "Destination exists; nothing overwritten: $destination" }
    $wrapper = if ($entry.Wrapper) { Join-Path $source $entry.Wrapper } else { $null }
    $flatten = $wrapper -and (Test-Path -LiteralPath $wrapper -PathType Container)
    if ($flatten) {
        $siblings = @(Get-ChildItem -LiteralPath $source -Force | Where-Object { $_.Name -ne $entry.Wrapper })
        $inside = @(Get-ChildItem -LiteralPath $wrapper -Force)
        foreach ($item in $siblings) {
            if ($item.Name -in $inside.Name) { throw "Flattening would collide on $($item.Name)" }
        }
    }
    $plan += [PSCustomObject]@{Source=$source; Destination=$destination; Flatten=$flatten; Wrapper=$entry.Wrapper}
}
$plan | Select-Object Source, Destination, Flatten | Format-Table -AutoSize -Wrap
if (-not $Apply) {
    Write-Host 'Dry run only. No files moved. Review, then repeat with -Apply.'
    exit
}
if (-not $plan.Count) { throw 'No source experiments found to move.' }

# Record original bytes and exact final paths BEFORE moving. All child artifacts,
# including failed attempts, requests, reviews and freezes, are preserved.
$files = @()
foreach ($entry in $plan) {
    foreach ($file in Get-ChildItem -LiteralPath $entry.Source -File -Force -Recurse) {
        $relative = $file.FullName.Substring($entry.Source.Length + 1)
        if ($entry.Flatten -and $relative.StartsWith($entry.Wrapper + '\')) {
            $relative = $relative.Substring($entry.Wrapper.Length + 1)
        }
        $final = Assert-Contained (Join-Path $entry.Destination $relative) $targetRoot
        $files += [PSCustomObject]@{OldPath=$file.FullName; NewPath=$final; SHA256=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash}
    }
}
New-Item -ItemType Directory -Path $targetRoot -Force | Out-Null
$recordPath = Join-Path $targetRoot ('relocation_' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffffffZ') + '.json')
@{Status='planned'; Files=$files; Note='Frozen historical paths remain unchanged. This record maps them to relocated files; old runner paths may need explicit updates before reuse.'} |
    ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $recordPath -Encoding UTF8
foreach ($entry in $plan) {
    New-Item -ItemType Directory -Path (Split-Path -Parent $entry.Destination) -Force | Out-Null
    Move-Item -LiteralPath $entry.Source -Destination $entry.Destination
    if ($entry.Flatten) {
        $wrapperPath = Assert-Contained (Join-Path $entry.Destination $entry.Wrapper) $targetRoot
        foreach ($child in Get-ChildItem -LiteralPath $wrapperPath -Force) {
            Move-Item -LiteralPath $child.FullName -Destination $entry.Destination
        }
        # Only this validated, now-empty wrapper is removed; no recursive deletion.
        Remove-Item -LiteralPath $wrapperPath
    }
}
foreach ($file in $files) {
    if ((Get-FileHash -LiteralPath $file.NewPath -Algorithm SHA256).Hash -ne $file.SHA256) {
        throw "Post-move verification failed: $($file.NewPath). Keep relocation record for recovery."
    }
}
@{Status='completed_verified'; Files=$files; Note='All moved file bytes verified. Frozen paths unchanged; use this mapping when locating historical artifacts.'} |
    ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $recordPath -Encoding UTF8
Write-Host "Moved and hash-verified $($files.Count) files. No result files deleted. Mapping: $recordPath"
Write-Host 'Frames, input prompts, configs, and remote workstation files were not changed.'
Write-Host 'Any supporting files remaining under output/in_context_events were preserved.'
