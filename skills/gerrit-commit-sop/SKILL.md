---
name: gerrit-commit-sop
description: >
  Commit and upload changes to Gerrit (refs/for/<branch>), e.g. MeigExpertTeam /
  Android_temp. Use when the user says 上库, Gerrit 提交, push refs/for, or upload
  for review on a Gerrit remote (port 29418 / non-github.com). Not for GitHub
  (use github-commit-sop). Covers Change-Id, MeigExpertTeam commit message, and
  post-merge tip cleanup (EXP-GIT-001).
---

# Gerrit 上库 SOP（commit + refs/for）

> 经验库（本机常见根）：`D:\Workspace\GDocuments\embedded-workflow-lab\knowledge-base\`  
> - `standards/STD-001-Git协作规范文档.md`  
> - `topics/git/EXP-GIT-001-Gerrit场景化提交流程与幽灵ahead排障.md`  
> - `topics/git/EXP-GIT-003-Gerrit幽灵叠推与developer本地身份拒收.md`  
> - `topics/git/EXP-GIT-006-fetch-pull-merge-rebase-push-reset对照手册.md`  
> 样例仓：`MeigExpertTeam` · 默认评审目标：`Android_temp` · 本地开发分支常为 `Android_temp_wanglingqi`（跟踪 `origin/Android_temp`）  
> **不适用** GitHub（走 `github-commit-sop` / STD-011）

## 触发与 Hard-gate

用户明确要求上库 / 推 Gerrit / `refs/for` 时执行。先确认 remote：

```powershell
git remote -v
git branch -vv
```

<HARD-GATE>
仅当 origin 为 Gerrit（典型：`ssh://…:29418/…`，且 **不是** github.com）才走本 skill。  
若是 github.com → 改用 github-commit-sop。  
未确认 remote 前禁止 push。
</HARD-GATE>

默认目标分支（可被用户改口覆盖）：

| 项 | 默认 |
|:---|:---|
| 评审目标 | `Android_temp` |
| 推送 ref | `refs/for/Android_temp` |
| 跟踪 tip | `origin/Android_temp` |

## 硬规则（须遵守）

1. **只推评审**：`git push origin HEAD:refs/for/<目标>`。禁止 `git push origin <个人分支名>`、禁止直推 `HEAD:<目标>`（除非管理员明确授权）。  
2. **显式 `git add` 文件列表**：禁止 `git add .` / `git add -A` 混入无关改动。  
3. **一次 Change 一个主题**：勿把无关模块、merge commit 绑进同一包。  
4. **须有 Change-Id**：确认 `.git/hooks/commit-msg` 存在；缺则从 Gerrit 拉 hook 后再 commit。  
5. **PowerShell**：`stash@{n}` 必须加引号，如 `"stash@{0}"`。  
6. **合入后对齐 tip**：Merged 后 `fetch` + `reset --hard origin/<目标>`（有脏先 stash），消灭幽灵 ahead。细节见 EXP-GIT-001。

## 标准流程（用户说「上库」时）

### 0. 探测

```powershell
git status --short
git fetch origin
git rev-list --left-right --count HEAD...origin/<目标>
# 输出：ahead behind
```

按 EXP-GIT-001 §3 决策表处理同步（摘要）：

| ahead / behind | 动作 |
|:---|:---|
| `0 N`（N≥1）仅落后 | 脏区先 `stash -u` → `merge --ff-only origin/<目标>` → `stash pop` |
| `M N` 有未上库本地 commit | `rebase origin/<目标>`（保留要上库的 commit） |
| `1 0` 已 push 审核中且**不再改** | 确认 Gerrit Change 后可 `reset --hard` 清本地副本（§5.5） |
| `1 0` 审核中还要**继续改同文件再上** | **保留**幽灵为父 → 新 commit（新 Change-Id）→ 再 `refs/for`（EXP-GIT-003）；勿 amend 幽灵 |

### 1. 选文件并提交

```powershell
git add <文件1> <文件2> ...
git diff --cached --stat
git commit -m "<message>"
git log -1 --format=full   # 确认含 Change-Id: I…
```

缺 hook 时（示例主机）：

```powershell
scp -p -P 29418 <user>@<gerrit-host>:hooks/commit-msg .git/hooks/
```

### 2. 推评审

```powershell
git push origin HEAD:refs/for/<目标>
```

成功后从 remote 输出抄 **Change URL** 回报用户。

### 3. 合入后收工（Merged 后 / 用户要求收工时）

```powershell
git fetch origin
# 有未提交改动先：git stash push -u -m "wip"
git reset --hard origin/<目标>
```

## Commit message（MeigExpertTeam / AI 任务）

优先仓库既有风格（单行可含多标签）：

```text
[AI][TaskId]<ID或项目>[Description]<做了什么>[Solution]<怎么做的>[Owner]<名字>
```

示例（auto-test）：

```text
[AI][TaskId]MT9801[Description]auto-test 接入 MT9801 冒烟项目档案并做兼容增强[Solution]新增 mt9801.json/unmapped 并登记 index；buttons 扩展 expected_keys；气压 SensorProbe OR；PWM 全通道；步骤号自然序；马达 WARNING 结案不假绿[Owner]wanglingqi
```

非 AI 任务可沿用仓内其它前缀（如 `[MeigExpertTeam][模块]…`），与近期 `git log` 对齐即可。

## 与「补丁文件」的关系

- 上库走 **commit + `refs/for`**，不依赖经验库里的 `PATCH-*.diff`。  
- `git diff` / `.patch` 仅作备份或评审附件；**不能代替** Gerrit Change。

## 检查清单

- [ ] remote 已确认为 Gerrit（非 github.com）  
- [ ] 目标分支已确认（默认 `Android_temp`）  
- [ ] ahead/behind 已按 EXP-GIT-001 处理  
- [ ] 仅 staged 本主题文件；无 `git add -A`  
- [ ] commit 含 `Change-Id`  
- [ ] 已 `push origin HEAD:refs/for/<目标>` 并回报 Change URL  
- [ ] （合入后）已 `reset --hard` 对齐 tip  

## 反模式

| 禁止 | 正确 |
|:---|:---|
| `git push origin Android_temp_wanglingqi` | `refs/for/Android_temp` |
| `git push origin HEAD:Android_temp` | `refs/for/Android_temp` |
| Merged 后仍 `ahead`，却 `pull`/`merge` 再长 merge | `reset --hard origin/<目标>` |
| 把 GitHub 仓当 Gerrit 推 | 换 github-commit-sop |
| 无用户「上库」意图就自动 push | 仅用户明确要求时 push |

## 回报用户

完成后给出：commit hash、Change-Id、Gerrit Change URL、本地 `ahead/behind` 状态，以及合入后收工命令一行。
