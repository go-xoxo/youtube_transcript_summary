<#
.SYNOPSIS
    Dirty Power Git: Commit/pull/merge/push everything with color and progress!
.DESCRIPTION
    - Commits all, merges/pulls, resolves conflicts, force-pushes, shows info
    - Shows progress bars, diffs, color, branch info, and conflict repair
    - Switch --RemoteWins (default) to auto-resolve with "theirs", --LocalWins for "ours"
    - Modern output, safe for PowerShell 7+
#>

param(
    [switch]$RemoteWins = $true,
    [switch]$LocalWins = $false
)

function Section($label, $color="Cyan") {
    Write-Host "`n==== $label ====" -ForegroundColor $color
}

function Show-ProgressBar($Activity, $Status, $Percent) {
    Write-Progress -Activity $Activity -Status $Status -PercentComplete $Percent
}

function ColorLine($Text, $Color) {
    Write-Host $Text -ForegroundColor $Color
}

function Show-Error($Text) {
    Write-Host "❌ $Text" -ForegroundColor Red
}

function Show-Success($Text) {
    Write-Host "✔ $Text" -ForegroundColor Green
}

$ErrorActionPreference = "Continue"

# 1. Detect branch and repo
Section "Detecting Current Branch and Repo"
$branch = git symbolic-ref --short HEAD 2>$null
if (-not $branch) { $branch = "main" }
Write-Host "Current branch: " -NoNewline; ColorLine $branch "Yellow"
$remotes = git remote
if (-not $remotes) { Show-Error "No git remote set!"; exit 1 }
git status

Show-ProgressBar "Git Sync" "Staging changes..." 10

# 2. Show diff, stage all
Section "Working Directory Diff"
git diff --stat

Section "Staging Everything"
git add -A
git diff --cached --stat

Show-ProgressBar "Git Sync" "Committing..." 20

# 3. Commit
Section "Committing"
$commit = git commit -am "Auto-commit: all changes" --allow-empty
$commit | Write-Host
if ($commit -match "nothing to commit") { ColorLine "Nothing new to commit." "DarkGray" }

Show-ProgressBar "Git Sync" "Fetching remote info..." 30

# 4. Show branch/remote info
Section "Local Branches" "DarkMagenta"
git branch -vv

Section "Remote Info" "DarkMagenta"
git remote -v
git branch -r

Section "Recent Local Commits" "Green"
git log --oneline -5

Show-ProgressBar "Git Sync" "Pulling remote changes..." 40

# 5. Pull from remote
Section "Pulling from Remote" "Blue"
$pull = git pull --no-edit --allow-unrelated-histories --rebase=false 2>&1
$pull | Write-Host

if ($LASTEXITCODE -ne 0 -or $pull -match "CONFLICT") {
    ColorLine "!! Merge conflicts detected. Attempting dirty auto-resolve..." "Red"
    Section "Conflicted Files" "Red"
    $conflicted = git diff --name-only --diff-filter=U
    $conflicted | ForEach-Object { Write-Host $_ -ForegroundColor Red }

    $mode = if ($LocalWins) {"ours"} else {"theirs"}
    foreach ($file in $conflicted) {
        ColorLine "Resolving ${file}: keep ${mode}" "Yellow"
        git checkout --$mode $file
        git add $file
    }
    $mergeCommit = git commit -am "Auto-merge: resolved all conflicts with ${mode}" --allow-empty
    Show-Success "Merge conflict resolved using ${mode}."
    $mergeCommit | Write-Host
} else {
    Show-Success "No merge conflicts."
}

Show-ProgressBar "Git Sync" "Reviewing post-merge status..." 60

Section "Status After Merge" "Cyan"
git status

Section "Files Changed in Last Commit" "Cyan"
git diff HEAD@{1} --stat

Show-ProgressBar "Git Sync" "Force-pushing to remote..." 80

# 6. Force push
Section "Force Pushing" "Magenta"
$push = git push --force-with-lease 2>&1
$push | Write-Host
if ($LASTEXITCODE -eq 0) {
    Show-Success "Force push successful!"
} else {
    Show-Error "Force push failed."
}

Show-ProgressBar "Git Sync" "Fetching latest remote log..." 100

Section "Remote Log After Push" "Green"
git fetch
git log origin/$branch --oneline -5

Show-Success "`nAll done! Your repo is now synced and brutally up to date. 💥"
Write-Host "`n[Tip] You can run '.\git_all.ps1 --LocalWins' to always keep your local changes in case of conflict." -ForegroundColor Yellow
