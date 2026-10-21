[CmdletBinding()]
param(
    [string]$RepositoryPath = (Join-Path $env:USERPROFILE 'source\Ai-Studio36'),
    [string]$ArchivePath = (Join-Path $PSScriptRoot 'ai-trading-oct-21-2026-upload-clean.zip'),
    [string]$InstallPath = '.',
    [string]$BranchName = 'upload/ai-trading-terminal-20261021'
)

$ErrorActionPreference = 'Stop'
$RepositoryUrl = 'https://github.com/sparmar3786-pixel/Ai-Studio36.git'

function Invoke-Git {
    param([Parameter(Mandatory=$true)][string[]]$GitArgs)
    & git @GitArgs
    if ($LASTEXITCODE -ne 0) { throw "Git command failed: git $($GitArgs -join ' ')" }
}

if (-not (Test-Path -LiteralPath $ArchivePath -PathType Leaf)) {
    throw "ZIP not found: $ArchivePath. Keep the ZIP next to this script or pass -ArchivePath."
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'Git is not installed. Install Git for Windows and reopen VS Code.'
}

if (-not (Test-Path -LiteralPath $RepositoryPath)) {
    $parent = Split-Path -Parent $RepositoryPath
    if ($parent -and -not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    Invoke-Git -GitArgs @('clone', $RepositoryUrl, $RepositoryPath)
}

$top = (& git -C $RepositoryPath rev-parse --show-toplevel 2>$null)
if ($LASTEXITCODE -ne 0) { throw "Not a Git repository: $RepositoryPath" }
$top = (Resolve-Path -LiteralPath $top).Path
$origin = (& git -C $top remote get-url origin).Trim()
if ($LASTEXITCODE -ne 0 -or $origin -notmatch 'github\.com[:/]sparmar3786-pixel/Ai-Studio36(?:\.git)?$') {
    throw "The folder's origin is not the requested Ai-Studio36 repository. Found: $origin"
}
$status = (& git -C $top status --porcelain)
if ($LASTEXITCODE -ne 0) { throw 'Could not read Git working tree status.' }
if ($status) { throw 'Working tree is not clean. Commit/stash existing changes first; this script will not touch them.' }

$dest = [System.IO.Path]::GetFullPath((Join-Path $top $InstallPath))
if ($dest -ne $top -and -not $dest.StartsWith($top + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'InstallPath must be the repository root or a subdirectory inside it.'
}

$temp = Join-Path ([System.IO.Path]::GetTempPath()) ('AiTradingUpload-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $temp | Out-Null
try {
    Expand-Archive -LiteralPath $ArchivePath -DestinationPath $temp
    $sourceFiles = @(Get-ChildItem -LiteralPath $temp -File -Recurse -Force)
    if ($sourceFiles.Count -eq 0) { throw 'The ZIP contains no files.' }

    $conflicts = @()
    $toCopy = @()
    foreach ($file in $sourceFiles) {
        $relative = $file.FullName.Substring($temp.Length).TrimStart([char[]]@('\','/'))
        $target = Join-Path $dest $relative
        if (Test-Path -LiteralPath $target -PathType Leaf) {
            $existingHash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
            $incomingHash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
            if ($existingHash -ne $incomingHash) { $conflicts += $relative }
        } elseif (Test-Path -LiteralPath $target) {
            $conflicts += "$relative (path exists as a directory)"
        } else {
            $toCopy += [pscustomobject]@{ Source=$file.FullName; Relative=$relative; Target=$target }
        }
    }
    if ($conflicts.Count -gt 0) {
        $list = $conflicts | Select-Object -First 25
        throw ("Upload stopped safely: {0} existing paths conflict. Nothing was copied. First conflicts:`n - {1}" -f $conflicts.Count, ($list -join "`n - "))
    }

    $remoteHeads = (& git -C $top ls-remote --heads origin)
    if ($LASTEXITCODE -ne 0) { throw 'Could not check remote branches; verify GitHub connectivity and sign-in.' }
    $hasHead = $true
    & git -C $top rev-parse --verify HEAD *> $null
    if ($LASTEXITCODE -ne 0) { $hasHead = $false }

    if (-not $remoteHeads -and -not $hasHead) {
        # This repository has no commits. Initialize its default branch directly;
        # opening a PR from a separate branch would leave main empty.
        $current = (& git -C $top branch --show-current).Trim()
        if ($current -ne 'main') {
            $localMain = (& git -C $top branch --list main)
            if ($localMain) { Invoke-Git -GitArgs @('-C', $top, 'switch', 'main') }
            else { Invoke-Git -GitArgs @('-C', $top, 'switch', '--orphan', 'main') }
        }
        $BranchName = 'main'
        Write-Host 'Empty repository detected: the initial source commit will initialize main.' -ForegroundColor Yellow
    } else {
        $baseBranch = (& git -C $top branch --show-current).Trim()
        if (-not $baseBranch) { throw 'Could not determine the current base branch.' }
        $remoteBranch = (& git -C $top ls-remote --heads origin $BranchName)
        if ($LASTEXITCODE -ne 0) { throw 'Could not check the proposed remote branch.' }
        if ($remoteBranch) { throw "Remote branch '$BranchName' already exists. Choose a new -BranchName." }
        $branchExists = (& git -C $top branch --list $BranchName)
        if ($branchExists) { throw "Branch '$BranchName' already exists locally. Choose a new -BranchName." }
        Invoke-Git -GitArgs @('-C', $top, 'switch', '-c', $BranchName)
    }

    foreach ($entry in $toCopy) {
        $parent = Split-Path -Parent $entry.Target
        if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
        Copy-Item -LiteralPath $entry.Source -Destination $entry.Target
    }

    Invoke-Git -GitArgs @('-C', $top, 'add', '--all')
    $staged = (& git -C $top diff --cached --name-only)
    if (-not $staged) { throw 'No new files to commit. No push was attempted.' }
    Invoke-Git -GitArgs @('-C', $top, 'commit', '-m', 'Upload AI Trading Android terminal source')
    Invoke-Git -GitArgs @('-C', $top, 'push', '-u', 'origin', $BranchName)

    $pushed = (& git -C $top ls-remote --heads origin $BranchName)
    if ($LASTEXITCODE -ne 0 -or -not $pushed) { throw 'Push command returned, but the remote branch could not be verified.' }
    Write-Host ''
    Write-Host 'Upload verified successfully.' -ForegroundColor Green
    Write-Host "Repository: $RepositoryUrl"
    Write-Host "Branch: $BranchName"
    if ($BranchName -eq 'main') {
        Write-Host 'The initial commit was pushed to main. Check GitHub Actions for workflow results.'
        Write-Host 'Repository: https://github.com/sparmar3786-pixel/Ai-Studio36'
    } else {
        Write-Host "Create/review PR: https://github.com/sparmar3786-pixel/Ai-Studio36/compare/main...$BranchName?expand=1"
    }
}
finally {
    Remove-Item -LiteralPath $temp -Recurse -Force -ErrorAction SilentlyContinue
}
