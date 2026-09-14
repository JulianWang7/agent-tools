# 私有仓库 → CC Switch 本地 SSOT 同步模式

> 适用范围：仓库设为 **private**（GitHub 私有仓库）后，CC Switch 的「仓库安装」通道（硬编码拉 `github.com/{owner}/{name}/archive/refs/heads/{branch}.zip`，匿名访问）无法拿到私有仓库内容。
> 本模式用 **git 私有仓库传内容 + CC Switch 本地 SSOT 装载** 的组合变相实现统一管理。
> 状态：2026-09-14 定稿。

## 为什么不能直接让 CC Switch 装私有仓库

CC Switch 添加技能仓库时，前端把输入解析成 `owner/name/branch`，后端硬编码拼 GitHub 公开 ZIP 地址下载：

```rust
let url = format!(
    "https://github.com/{}/{}/archive/refs/heads/{}.zip",
    repo.owner, repo.name, branch
);
```

私有仓库对该地址返回 **404**，CC Switch 报 `DOWNLOAD_FAILED`。官方 issue [#1387](https://github.com/farion1231/cc-switch/issues/1387)（提出任意 ZIP / 私有鉴权）仍为 Open，短期不会实现。

## SSOT 是什么（本模式的地基）

**SSOT = Single Source of Truth（单一事实源）**。「同一份东西只在一处存权威版本，其它位置都是它的副本/派生」：

- **设计层**：`agent-tools` 私有仓库是 skill 内容的唯一权威版本（改版、历史、回滚都在这里）；
- **CC Switch 实现层**：`~/.cc-switch/skills/` 是 CC Switch 的技能 SSOT——它把技能文件统一收到这个目录，再从这分发到各 app 的技能目录（`~/.claude/skills`、`~/.codex/skills`、`~/.gemini/skills`、`~/.config/opencode/skills`、`~/.hermes/skills`）。

> ⚠️ 不要把 git clone 目录直接当 CC Switch 的 SSOT：CC Switch 对 SSOT 拥有物理管理权（卸载=删目录、更新=替换目录、迁移=v3.13+ 可在 `~/.cc-switch/skills` 与 `~/.agents/skills` 间搬移）。git 目录要求文件系统稳定、由 git 说了算，两者会互相踩。**正确分层：git 是母本（只读来源），SSOT 是副本（CC Switch 管）**。

## 分层图

```
┌─────────────────────────────────┐
│ agent-tools（私有，GitHub）        │ ◄── 唯一事实源（内容/版本）
│ skills/<name>/SKILL.md           │     你只在这里编辑、push
└───────────────┬─────────────────┘
                │ git clone/pull（人 clone；脚本检测+pull）
                ▼
┌─────────────────────────────────┐
│ 任意目录 clone 副本               │
│ e.g. D:\agent-tools / ~\agent-tools（可 -RepoRoot 指定）│
└───────────────┬─────────────────┘
                │ scripts/sync-skills.ps1（单向平铺复制）
                ▼
┌─────────────────────────────────┐
│ ~/.cc-switch/skills/<name>/      │ ◄── CC Switch 的 SSOT（它拥有这里）
│ （平铺：<name>/SKILL.md）         │     扫描识别为「本地 skill」
└───────────────┬─────────────────┘
                │ CC Switch 分发（symlink / 复制）
                ▼
   ~/.claude/skills  ~/.codex/skills  ~/.gemini/skills  ~/.config/opencode/skills  ...
```

## 为什么结构必须平铺

CC Switch v3.12.3+ 只认 `~/.cc-switch/skills/<name>/SKILL.md` 一级结构；`skills/<repo>/skills/<name>/SKILL.md` 这种嵌套识别不了（issue [#3498](https://github.com/farion1231/cc-switch/issues/3498)）。所以同步时把仓库 `skills/*` 逐个子目录复制成 SSOT 根下的平铺目录。

## 双机一致性如何实现

**内容与状态分开，两条链路各管一半：**

| 一致性维度 | 链路 | 机制 |
|---|---|---|
| skill 文件内容 | **git**（GitHub 私有仓库，SSH/强认证/白名单设备） | A 机改后 push；B 机 `git pull` + 跑 sync 脚本 → SSOT 更新 |
| 启停/安装状态（哪个 skill 开、装到哪些 app） | **WebDAV/坚果云**（CC Switch DB 同步） | 只同步 `cc-switch.db`（skills 表 `enabled_*` 等） |

为什么二者不冲突：CC Switch 的 DB 只存技能记录的引用（directory 路径、content_hash），**不存实体文件**；实体永远从 git 来，状态永远从 DB 来。WebDAV 单写者纪律不变——同一时刻只允许一台机器做上传/下载写操作。

## sync-skills.ps1 做了什么（自适应同步）

先决条件：`git clone`（自动由人完成一次）。之后脚本自动处理：

1. **检测远端更新**：`git fetch`（不动工作区）→ 对比本地 HEAD 与 `origin/main`；有更新且工作区干净时自动 `git pull --ff-only`（可用 `-NoAutoPull` 关闭，或网络不行时继续用本地内容先同步）；
2. **扫描新增/改动**：遍历仓库 `skills/*`，凡包含 `SKILL.md` 的目录都算一个 skill；
3. **增量同步**：`robocopy /E /XD .git` 逐目录复制到 SSOT——**新增 skill 自动出现、改动文件自动覆盖、未动文件跳过**（自适应，无需逐个声明）；
4. **删除提示**：记录上次同步清单于 SSOT 下的 `.agent-tools-sync.json`，仓库里已移除的 skill 仅提示、不自动删（防误删）；
5. **结尾提示**：去 CC Switch 技能页刷新 / 重启。

## 运行方式

```powershell
# 首次/默认（自动探测仓库位置）
powershell -ExecutionPolicy Bypass -File scripts\sync-skills.ps1

# 只看不改
powershell -ExecutionPolicy Bypass -File scripts\sync-skills.ps1 -DryRun

# B 机（clone 路径不同，用 -RepoRoot 指定；不必改脚本）
powershell -ExecutionPolicy Bypass -File scripts\sync-skills.ps1 -RepoRoot "D:\tools\agent-tools"

# 远端有更新时不自动 pull，只同步本地已 pull 的内容
powershell -ExecutionPolicy Bypass -File scripts\sync-skills.ps1 -NoAutoPull
```

> PowerShell 执行策略：用 `-ExecutionPolicy Bypass` 即可，无需改系统策略。GUI 双击 .ps1 不会直接跑，请用终端 / 右键「使用 PowerShell 运行」。

## 路径策略（多机零修改）

脚本**不写死仓库路径**，按以下顺序定位：

1. 显式指定 `-RepoRoot`（优先级最高，笔记本 clone 到任意位置都用它）；
2. 未指定时自动探测常见位置：
   - `D:\agent-tools`
   - `~\agent-tools`
   - `~\Desktop\agent-tools`
   - `~\Documents\agent-tools`
   - `~\source\agent-tools`
   - `~\repos\agent-tools`
3. 找到第一个同时包含 `.git` 与 `skills/` 的目录即采用（并打印「自动探测仓库: …」）；
4. 全没找到时报错并列候选清单，提示用 `-RepoRoot`。

所以：
- **本机（台式机）**：仓库在 `D:\agent-tools`，直接跑脚本即可;
- **笔记本**：先 `git clone git@github.com:JulianWang7/agent-tools.git` 到自己喜欢的位置；若没放在候选路径里，加 `-RepoRoot` 指一下；也可以 clone 到 `~\agent-tools` 免参数。
- 两台机器**不必路径一致**——内容是 git 传的、状态是 WebDAV 传的，路径由各机自定。

## 常见问题

- **Q：CC Switch 提示「检测到 skill 已变更 / 需要重新安装」？**
  A：正常。SSOT 文件变了，DB 里的 content_hash 对不上，刷新 / 重新安装一次即可（这正是它的校验机制）。
- **Q：SSOT 里还有别的来源的 skill（如公开仓库装的）会被脚本弄丢吗？**
  A：不会。脚本只遍历本仓库 `skills/*` 并同步对应的同名目录，不清理其它目录。
- **Q：更新后要做什么？**
  A：`git pull` 已由脚本完成（或手动）；重跑 `sync-skills.ps1`；进 CC Switch 技能页点刷新。