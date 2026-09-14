# sync-skills.ps1 — 私有仓库 → CC Switch 本地 SSOT 同步
#
# 模式：agent-tools（私有 GitHub 仓库）是 skill 唯一事实源；
#       本脚本检测远端更新 → 平铺复制 skills/* 到 CC Switch SSOT（~/.cc-switch/skills）
#       → CC Switch 扫描识别为「本地 skill」，照常分发到 Claude/Codex 等。
#
# 运行方式：
#   powershell -ExecutionPolicy Bypass -File scripts\sync-skills.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\sync-skills.ps1 -DryRun
#   powershell -ExecutionPolicy Bypass -File scripts\sync-skills.ps1 -RepoRoot "D:\tools\agent-tools"
#
# 说明：
#   - git clone 由人来做（一次）；检测/同步由脚本自动完成
#   - 默认会 git fetch 检测远端更新；有更新且工作区干净时自动 pull（可用 -NoAutoPull 关闭）
#   - robocopy 增量复制：新增 skill 自动进 SSOT、改动文件自动覆盖、未动文件跳过
#   - 不自动删除 SSOT 副本（防误删），只提示「仓库已移除的 skill」
#
# 注意：脚本须以 UTF-8 with BOM 保存，否则 Windows PowerShell 5.1 中文解析出错。

param(
    [string]$RepoRoot = "$HOME\Desktop\agent-tools",   # 本机 clone 路径（B 机改成自己的路径）
    [string]$Branch = "main",
    [string]$SsotRoot = "$HOME\.cc-switch\skills",     # CC Switch 技能 SSOT
    [switch]$DryRun,                                   # 只报告，不复制 / 不 pull
    [switch]$NoAutoPull                                # 检测到远端更新时不自动 pull，仅提示
)

$ErrorActionPreference = "Continue"  # 外部命令 stderr 不触发异常，一律看 $LASTEXITCODE

# 控制台 UTF-8 输出（解决中文乱码；Windows PowerShell 5.1 需要）
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }
try { $OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

$srcRoot = Join-Path $RepoRoot "skills"
$manifestPath = Join-Path $SsotRoot ".agent-tools-sync.json"

function Write-Step($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "    $msg" -ForegroundColor Green }

# ---------- 0. 前置校验 ----------
if (-not (Test-Path $RepoRoot))      { Write-Error "仓库不存在: $RepoRoot"; exit 1 }
if (-not (Test-Path (Join-Path $RepoRoot ".git"))) { Write-Error "不是 git 仓库: $RepoRoot"; exit 1 }
if (-not (Test-Path $srcRoot))       { Write-Error "仓库 skills 目录不存在: $srcRoot"; exit 1 }
if (-not (Test-Path $SsotRoot))      { New-Item -ItemType Directory -Path $SsotRoot -Force | Out-Null }

# ---------- 1. 检测远端更新（git fetch，不改变工作区） ----------
Write-Step "检测远端更新 (origin/$Branch)"
if ($DryRun) {
    Write-Ok "[DryRun] 跳过 fetch/pull"
} else {
    & git -C $RepoRoot fetch origin $Branch 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "git fetch 失败（网络 / 代理 / SSH 问题？）——继续用本地内容同步；远端更新请稍后重试。"
    } else {
        $localHead  = (& git -C $RepoRoot rev-parse HEAD 2>$null).Trim()
        $remoteHead = (& git -C $RepoRoot rev-parse "origin/$Branch" 2>$null).Trim()
        $statusLines = @(& git -C $RepoRoot status --porcelain 2>$null)
        $dirty = $statusLines.Count -gt 0

        if ($localHead -and $remoteHead -and $localHead -ne $remoteHead) {
            if ($dirty) {
                Write-Warning "远端有更新，但本地工作区有未提交修改——请先提交/暂存，再手动 git pull。"
            } elseif ($NoAutoPull) {
                Write-Warning "远端有更新（$localHead → $remoteHead）。跳过自动 pull，请手动 git pull 后重跑。"
            } else {
                Write-Ok "远端有更新，自动 pull（--ff-only）..."
                & git -C $RepoRoot pull --ff-only origin $Branch 2>&1 | Out-Null
                if ($LASTEXITCODE -ne 0) {
                    Write-Warning "自动 pull 失败（可能分叉），请手动处理。"
                } else {
                    Write-Ok "pull 完成: $((& git -C $RepoRoot rev-parse --short HEAD 2>$null))"
                }
            }
        } else {
            Write-Ok "本地与远端一致（或 fetch 无更新）。"
        }
    }
}

# ---------- 2. 扫描仓库 skills ----------
Write-Step "扫描仓库 skills/"
$repoSkills = @()
Get-ChildItem $srcRoot -Directory | ForEach-Object {
    $name = $_.Name
    $md = Join-Path $_.FullName "SKILL.md"
    if (Test-Path $md) {
        $repoSkills += $name
        Write-Ok "发现 skill: $name"
    } else {
        Write-Warning "跳过 $name（无 SKILL.md）"
    }
}
if ($repoSkills.Count -eq 0) { Write-Error "仓库 skills/ 下没有含 SKILL.md 的技能。" ; exit 1 }

# ---------- 3. 增量同步到 SSOT（自适应：新增/改动自动处理） ----------
Write-Step "同步到 CC Switch SSOT ($SsotRoot)"
$copied = @()
foreach ($name in ($repoSkills | Sort-Object)) {
    $src = Join-Path $srcRoot $name
    $dst = Join-Path $SsotRoot $name

    if ($DryRun) {
        $log = & robocopy $src $dst /E /XD .git /L /NFL /NDL /NJH /NJS /NP 2>$null
        $changed = (($log | Select-String -Pattern "New File|Newer").Count)
        if ($changed -gt 0) { Write-Ok "[DryRun] $name 将有 $changed 个文件变更" }
        else                { Write-Ok "[DryRun] $name 无变化" }
        continue
    }

    & robocopy $src $dst /E /XD .git /NFL /NDL /NJH /NJS /NP | Out-Null
    $rc = $LASTEXITCODE
    if ($rc -ge 8) {
        Write-Warning "复制 $name 失败 (robocopy exit $rc)"
    } else {
        $copied += $name
        if ($rc -eq 0) { Write-Ok "$name 同步完成（无变化）" }
        else           { Write-Ok "$name 同步完成（${rc}: 有文件变更）" }
    }
}

# ---------- 4. 删除检测（仅提示，不自动删） ----------
Write-Step "检查仓库已移除的 skill"
$prev = @()
if (Test-Path $manifestPath) {
    try { $prev = @((Get-Content $manifestPath -Raw | ConvertFrom-Json).skills) } catch { $prev = @() }
}
$removed = $prev | Where-Object { $_ -notin $repoSkills }
if ($removed) {
    Write-Warning "以下 skill 已从仓库移除（SSOT 副本保留，确认无误后手动删除）:"
    $removed | ForEach-Object { Write-Warning "    ~/.cc-switch/skills/$_" }
} else {
    Write-Ok "无移除项。"
}

# ---------- 5. 记录本次同步清单 ----------
if (-not $DryRun) {
    @{ updated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss"); skills = $repoSkills } |
        ConvertTo-Json | Set-Content $manifestPath -Encoding UTF8
    Write-Step "完成：本次同步 $($copied.Count) 个 skill → $SsotRoot"
    Write-Host "`n下一步：在 CC Switch 技能页点【刷新】（或重启 CC Switch）即可让新 skill/改动生效。" -ForegroundColor Yellow
} else {
    Write-Step "[DryRun] 结束（未做任何改动）"
}