<#
.SYNOPSIS
    🦾 All-in Git: The brutally simple, emoji-powered, forceful git-sync script.
.DESCRIPTION
    - Commits all, merges/pulls, resolves conflicts, force-pushes, shows info (with emoji!)
    - Progress bars, diffs, branch info, summary, log file, and robust error handling
    - --RemoteWins (default): conflicts use remote, --LocalWins: keep local changes
    - 100% PowerShell 7+ compatible!
#>

param(
    [switch]$RemoteWins = $true,   # 🏆 Remote wins on conflict (default)
    [switch]$LocalWins = $false    # 🏆 Local wins on conflict (manual switch)
)

function Section($label, $color="Cyan") {
    $now = Get-Date -Format "HH:mm:ss"
    Write-Host ""
    Write-Host ("━"*70) -ForegroundColor DarkGray
    Write-Host "[$now] $label" -ForegroundColor $color
    Write-Host ("━"*70) -ForegroundColor DarkGray
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
    Write-Host "✅ $Text" -ForegroundColor Green
}

function Get-CurrentBranch {
    # 🌿 Robust branch detection (main/master/whatever)
    $branch = git symbolic-ref --short HEAD 2>$null
    if (-not $branch) {
        $branch = $(git branch --show-current)
        if (-not $branch) {
            if (git show-ref --verify --quiet refs/heads/main) { $branch = "main" }
            elseif (git show-ref --verify --quiet refs/heads/master) { $branch = "master" }
            else { $branch = "main" }
        }
    }
    return $branch
}

# 🗒️ Begin transcript logging (every run gets a unique log file!)
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logPath = "git_all_run_${timestamp}.log"
Start-Transcript -Path $logPath | Out-Null

$ErrorActionPreference = "Continue"
[int]$commitCountBefore = (git rev-list --count HEAD 2>$null)
$changedFilesBefore = git status --porcelain | Measure-Object | Select-Object -ExpandProperty Count

# 🛰️ Detect branch and repo
Section "🛰️  Detecting Current Branch and Repo"
$branch = Get-CurrentBranch
Write-Host "🌿 Current branch: " -NoNewline; ColorLine $branch "Yellow"
$remotes = git remote
if (-not $remotes) { Show-Error "🛑 No git remote set!"; Stop-Transcript; exit 1 }
git status

Show-ProgressBar "🚚 Git Sync" "🗂️ Staging changes..." 10

# 📝 Show diff, stage all
Section "📝 Working Directory Diff"
git diff --stat

Section "➕ Staging Everything"
git add -A
git diff --cached --stat

Show-ProgressBar "🚚 Git Sync" "💾 Committing..." 20

# 💾 Commit
Section "💾 Committing"
$commit = git commit -am "📝 Auto-commit: all changes" --allow-empty
$commit | Write-Host
if ($commit -match "nothing to commit") { ColorLine "😴 Nothing new to commit." "DarkGray" }

Show-ProgressBar "🚚 Git Sync" "🌎 Fetching remote info..." 30

# 🌿 Branch/remote info
Section "🌿 Local Branches"
git branch -vv | Select-String $branch

Section "🌎 Remote Info"
git remote -v
Write-Host "🔗 Relevant remote branches for ${branch}:" -ForegroundColor Cyan
git branch -r | Select-String $branch

Section "🕓 Recent Local Commits"
git log --oneline -5

Show-ProgressBar "🚚 Git Sync" "⬇️  Pulling remote changes..." 40

# ⬇️ Pull from remote
Section "⬇️  Pulling from Remote"
$pull = git pull --no-edit --allow-unrelated-histories --rebase=false 2>&1
$pull | Write-Host

if ($LASTEXITCODE -ne 0 -or $pull -match "CONFLICT") {
    ColorLine "🚨‼️ Merge conflicts detected. Attempting dirty auto-resolve..." "Red"
    Section "⚡ Conflicted Files"
    $conflicted = git diff --name-only --diff-filter=U
    $conflicted | ForEach-Object { Write-Host "⚠️ $_" -ForegroundColor Red }
    $mode = if ($LocalWins) {"ours"} else {"theirs"}
    foreach ($file in $conflicted) {
        ColorLine "🤖 Resolving ${file}: keep ${mode}" "Yellow"
        git checkout --$mode $file
        git add $file
    }
    $mergeCommit = git commit -am "🤖 Auto-merge: resolved all conflicts with ${mode}" --allow-empty
    Show-Success "🔧 Merge conflict resolved using ${mode}."
    $mergeCommit | Write-Host
} else {
    Show-Success "🆗 No merge conflicts."
}

Show-ProgressBar "🚚 Git Sync" "🧾 Reviewing post-merge status..." 60

# 📋 Status after merge
Section "📋 Status After Merge"
git status

# 🗂️ Files changed in last commit (ALWAYS works, even on first commit)
Section "🗂️  Files Changed in Last Commit"
git show --stat --oneline -1

Show-ProgressBar "🚚 Git Sync" "⏫ Force-pushing to remote..." 80

# ⏫ Force push
Section "⏫ Force Pushing"
$push = git push --force-with-lease 2>&1
$push | Write-Host
if ($LASTEXITCODE -eq 0) {
    Show-Success "🚀 Force push successful!"
} else {
    Show-Error "💣 Force push failed."
}

Show-ProgressBar "🚚 Git Sync" "🛰️  Fetching latest remote log..." 100

# 🛰️ Remote log after push
Section "🛰️  Remote Log After Push"
git fetch
git log origin/$branch --oneline -5

[int]$commitCountAfter = (git rev-list --count HEAD 2>$null)
$changedFilesAfter = git diff --stat | Measure-Object | Select-Object -ExpandProperty Count

# 🎯 Final summary!
Section "🎯 Summary" "Green"
$summary = @()
$summary += "⏰ Run timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$summary += "🌿 Branch synced: ${branch}"
$summary += "🔢 Commits before: $commitCountBefore, after: $commitCountAfter (Δ $($commitCountAfter-$commitCountBefore))"
$summary += "🗂️ Files changed in last commit:"
$summary += (git show --oneline --name-status -1)
$summary += ""
if ($push -like "*Everything up-to-date*") {
    $summary += "🟢 Everything already up-to-date. ✔"
} else {
    $summary += "💥 Repository was force-updated."
}
$summary | ForEach-Object { Write-Host $_ -ForegroundColor Green }

Show-Success "`n🎉 All done! Your repo is now synced and brutally up to date. 💥"
Write-Host "`n💡 [Tip] Run '.\git_all.ps1 --LocalWins' to always keep your local changes in case of conflict." -ForegroundColor Yellow
Write-Host "🗒️  Run transcript saved at: $logPath" -ForegroundColor Magenta

# 🛑 End transcript logging
Stop-Transcript | Out-Null
