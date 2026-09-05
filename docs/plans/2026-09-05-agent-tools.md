# agent-tools 仓库化 + 双机统一装载 实施计划

> **Goal:** 把自研 MCP server 与 Skill 收敛到一个私有 GitHub 单仓（agent-tools），A/B 两机经「git clone + bootstrap + CC Switch + WebDAV 云同步」统一装载：Claude Code / Codex 由 CC Switch 管理，QwenPaw / Cursor 由 bootstrap 脚本管理，Hermes 延后接入。
> **背景:** 2026-09-05 方案评审结论（见对话记录）——SKILL.md 已跨 Claude Code/Codex/Cursor/Hermes/QwenPaw 收敛；MCP 代码零平台适配、只需注册配置；CC Switch 只支持 8 款工具（不含 Cursor/QwenPaw）。
> **架构:** 单一事实源 = GitHub 私有仓；CC Switch = Claude/Codex 的 MCP+Skill 记录 SSOT（WebDAV 同步 DB）；bootstrap.ps1 = Cursor/QwenPaw 的装载器；各机 app 目录 = 消费端。

## 已锁定决策（若与本机现状冲突，先停下确认）

| # | 决策 | 理由 |
|---|------|------|
| D1 | 单仓 `agent-tools`，私有（JulianWang7/agent-tools） | 一次 push 全平台同版本；CC Switch custom repo 支持 `subdirectory=skills`；QwenPaw skill_paths 只指一个根 |
| D2 | MCP 统一做成可安装包（`pyproject.toml` + console entry point），command 只写命令名 | 消除跨机绝对路径差异；CC Switch / Cursor / QwenPaw 三处注册同一命令 |
| D3 | Skill frontmatter 只保留最小集 `name` + `description`，不用厂商专属 YAML | 五平台通用 |
| D4 | CC Switch 技能来源 = GitHub custom repo（不是本地 clone）；技能 SSOT 保持默认 `~/.cc-switch/skills/` | CC Switch 的安装/更新机制基于远端仓库 SHA-256 比对 |
| D5 | clone 路径允许 A/B 两机不同（skill_paths / mcp.json 均按本机实路径写） | QwenPaw skill_paths、Cursor mcp.json 是本机配置，天然可异 |
| D6 | Hermes 延后；QwenPaw 绑定型技能与含敏感内容技能不进仓（先分级） | 范围控制 |
| D7 | 沿用 github-commit-sop：分组提交、禁 `git add -A` 混组、无 token 入库 | 既有规范 |
| D8 | CC Switch WebDAV 同步只同步 DB；skill 实体文件靠 git；单写者原则（不同时双机自动同步） | 官方机制边界 |

## 前置假设（执行前需你确认）

- A1: 仓库名就叫 `agent-tools`？clone 到 A 机哪个目录（默认 `D:\Workspace\tools\agent-tools`）？
- A2: MCP 运行依赖用 `pip install -e .`（venv）还是 `uv tool install`？（两机需一致，推荐 uv，理由见 T2.1 注）
- A3: B 机是 Windows 且可跑 PowerShell bootstrap？B 机网络到 github.com 是否走代理？（A 机仓库级 `http.proxy` 先例可复制）
- A4: 首批试点对象：MCP 建议 **JulianWang-workflow（cit-workflow-mcp）**，Skill 建议 **github-commit-sop**（两者均有现成代码与验证链路），不同意则替换。

## 文件地图

| 文件 | 用途 | 动作 |
|------|------|------|
| `docs/plans/2026-09-05-agent-tools.md` | 本计划（移入新仓） | 移动/复制 |
| `README.md` | 仓说明：目录结构、装载矩阵、push-first 工作流 | 创建 |
| `SYNC-MATRIX.md` | 每平台装载/更新方式对照表（防双源漂移） | 创建 |
| `.gitignore` | 忽略 venv/__pycache__/.env/密钥 | 创建 |
| `inventory.csv` | Phase 0 盘点清单：名字/功能/平台绑定/分级 | 创建（不入仓亦可） |
| `skills/<name>/SKILL.md` | 通用技能主体（最小 frontmatter） | 创建（试点 github-commit-sop 移入） |
| `mcp/<name>/server.py` | MCP server 代码 | 创建（试点 JulianWang-workflow 移入） |
| `mcp/<name>/pyproject.toml` | 打包 + entry point（console script） | 创建 |
| `mcp/<name>/README.md` | 该 server 安装/验证说明 | 创建 |
| `registry/mcp.servers.json` | 一份标准 mcpServers JSON（Claude/Cursor/QwenPaw 共用粘贴源） | 创建 |
| `registry/mcp.codex.toml` | Codex 用 TOML（由 JSON 手工/脚本转换） | 创建 |
| `scripts/bootstrap.ps1` | 幂等装载器：QwenPaw skill_paths、Cursor 软链+mcp.json、自检 | 创建 |
| `scripts/check.ps1` | 各平台装载状态自检 | 创建 |

---

## Task 0: 盘点与分级（决定迁移清单）

> 输入：本机现状（`.cursor\mcp.json` 8 个 MCP、QwenPaw 工作区 40+ skills、`~/.claude/skills` 等）。输出：`inventory.csv`。

- [ ] 0.1 导出 `.cursor\mcp.json` 的 MCP 清单 → 记入 inventory.csv
- [ ] 0.2 列出 QwenPaw 工作区 `skills\` 目录全部技能名 → 记入 inventory.csv
- [ ] 0.3 列出 `~/.claude\skills`、`~/.cursor\skills`（若存在）现有技能 → 记入 inventory.csv
- [ ] 0.4 对每项打标：`P`=可移植通用、`Q`=QwenPaw 绑定、`X`=含内部敏感、`D`=废弃
  - 判据：技能是否引用 QwenPaw 专有能力（channel_message/cron/agents chat/workspace 记忆/qwenpaw CLI）→ Q；内容涉及 Meig 质检/XTS/GMSMD/具体服务器路径→ X；两者皆否且逻辑通用 → P。
- [ ] 0.5 确认首批试点（A4）
- Verify: `inventory.csv` 完整、每项有分级；试点 MCP 与 skill 已选出
- 备注：本任务多数为人工盘点，可与 Task 1 并行

## Task 1: 建仓 + 骨架（A 机）

- [ ] 1.1 在 GitHub 新建私有空仓 `JulianWang7/agent-tools`（不勾选 README/.gitignore，本地生成）
- [ ] 1.2 `git clone` 到 A 机约定目录（A1；HTTPS remote + 仓库级 `http.proxy`，参照 cit-workflow 先例：`git config http.proxy http://127.0.0.1:7897`）
- [ ] 1.3 建骨架：`skills/`、`mcp/`、`registry/`、`scripts/`、`README.md`、`SYNC-MATRIX.md`、`.gitignore`（忽略 `__pycache__/`、`*.pyc`、`.venv/`、`.env`、`*.sql`）
- [ ] 1.4 把本计划文件复制进 `docs/plans/`
- [ ] 1.5 写 `SYNC-MATRIX.md` 骨架（下表模板见文末「附录 A」）
- Verify: `git status` 只见预期文件；`tree /f` 结构正确
- Commit（分组，勿混组）:
  - `chore: 初始化 agent-tools 仓库骨架与计划`
- 说明：首次提交只含骨架，不含任何迁移代码

## Task 2: 试点 MCP 入仓 + 可安装化

- [ ] 2.1 将试点 MCP（JulianWang-workflow）代码复制到 `mcp/julianwang-workflow/`
  - 结构：`server.py`、`pyproject.toml`、`README.md`、`tests/`（原样迁移，目录内自带依赖声明）
- [ ] 2.2 写 `mcp/julianwang-workflow/pyproject.toml`：
  ```toml
  [project]
  name = "julianwang-workflow-mcp"
  version = "0.1.0"
  requires-python = ">=3.10"
  dependencies = ["mcp>=1.0", "fastmcp>=2.0"]   # 以实际为准

  [project.scripts]
  julianwang-workflow = "server:main"          # console entry point（command 名）
  ```
  - 注：需给 `server.py` 加 `def main(): ...` 入口并保证 `import` 安全
- [ ] 2.3 本机安装并验证命令名可用：
  ```cmd
  cd mcp\julianwang-workflow
  pip install -e .
  julianwang-workflow --help     (或启动后 Ctrl+C)
  ```
  - 若选 uv：`uv tool install -e .`（A2 决策）
- [ ] 2.4 写 `registry/mcp.servers.json`，加入试点：
  ```json
  {
    "mcpServers": {
      "JulianWang-workflow": {
        "command": "julianwang-workflow",
        "args": []
      }
    }
  }
  ```
  - 此文件即 Claude Code / Cursor / QwenPaw 的粘贴源；Codex TOML 由 `registry/mcp.codex.toml` 同步
- Verify:
  - `where julianwang-workflow` 能找到命令
  - 用 `npx @modelcontextprotocol/inspector` 或最小客户端握手一次成功（可选）
- Commit: `feat: 试点 MCP 可安装化（pyproject entry point + registry 模板）`

## Task 3: 试点 Skill 入仓（最小 frontmatter）

- [ ] 3.1 将试点 skill（github-commit-sop）SKILL.md 及附属文件复制到 `skills/github-commit-sop/`
- [ ] 3.2 检查并裁剪 frontmatter 为最小集：
  ```markdown
  ---
  name: github-commit-sop
  description: 触发条件描述（≤200 字，含同义词触发词）
  ---
  ```
  - 删掉任何厂商专属字段；正文若引用 QwenPaw 专有能力需改造或降级为通用说明
- [ ] 3.3 本地用一个测试技能目录人工验证：将 `skills/github-commit-sop` 软链到 `~/.claude/skills/`，在 Claude Code 里 `/skills` 可见且描述正确
  - Windows 建目录软链需管理员或开发者模式：`mklink /D "%USERPROFILE%\.claude\skills\github-commit-sop" "...\agent-tools\skills\github-commit-sop"`
- Verify: `/skills` 列表出现且触发描述符合预期
- Commit: `feat: 试点 skill 入仓并裁剪为跨平台最小 frontmatter`

## Task 4: CC Switch 接入（A 机，试点）

- [ ] 4.1 打开 CC Switch → 若已装，先「导入现有 CLI 配置」保留 provider
- [ ] 4.2 技能：Skills 页 → Repository Management → Add Repository：owner=`JulianWang7`、name=`agent-tools`、branch=`main`、subdirectory=`skills` → 刷新 → 试点 skill 卡片出现 → Install（对 Claude）
  - Verify: `~/.claude\skills\github-commit-sop` 存在（软链指向 `~/.cc-switch\skills\...`）
- [ ] 4.3 MCP：MCP 页 → Add → Custom（stdio）→ Server ID=`JulianWang-workflow`、command=`julianwang-workflow`、args 空 → 保存 → 打开 Claude toggle
  - Verify: `~/.claude.json` 的 `mcpServers` 出现该项；重启 `claude` 后 `/mcp` 显示 connected
- [ ] 4.4 Codex toggle 也打开（若本机装了 codex）
  - Verify: `~/.codex\config.toml` 出现 `[mcp_servers.julianwang-workflow]`
- Commit: 无（CC Switch 配置不入仓；记录在 SYNC-MATRIX）

## Task 5: QwenPaw / Cursor 装载器 bootstrap（A 机，试点）

- [ ] 5.1 写 `scripts/bootstrap.ps1`，参数化：
  ```powershell
  param(
    [string]$RepoRoot,        # 本机 clone 路径（必填，不写死）
    [switch]$SkipQwenPaw,
    [switch]$SkipCursor,
    [switch]$CopyMode         # Cursor 技能用复制代替软链（软链失败时）
  )
  ```
  动作：
  1. 校验 `$RepoRoot\skills`、`$RepoRoot\registry\mcp.servers.json` 存在
  2. QwenPaw：读 `$env:USERPROFILE\.qwenpaw\config.json`（工作区配置在 `QWENPAW_WORKING_DIR`，默认 `~/.qwenpaw`），向顶层 `skill_paths` 数组插入 `$RepoRoot\skills`（若已存在则跳过 → 幂等）
  3. Cursor：确保 `~/.cursor\skills\` 存在；对 `skills\*` 逐个建软链（失败则回退 `CopyMode` 复制）
  4. Cursor MCP：把 `registry\mcp.servers.json` 的 `mcpServers` merge 进 `~/.cursor\mcp.json`（保留既有 8 个 MCP，只新增/更新试点项）→ 覆盖前自动备份 `mcp.json.bak`
  5. 输出摘要：每步 done/skip/fail
- [ ] 5.2 执行 `.\scripts\bootstrap.ps1 -RepoRoot D:\Workspace\tools\agent-tools`
- [ ] 5.3 验证 QwenPaw：控制台/技能池刷新后试点 skill 可见（外部路径来源）；`config.json` 不重复添加（再跑一次脚本仍幂等）
- [ ] 5.4 验证 Cursor：`~/.cursor\skills\github-commit-sop` 可读；`~/.cursor\mcp.json` 含试点且旧 MCP 未丢
- Commit: `feat: bootstrap.ps1（QwenPaw skill_paths + Cursor 软链/mcp.json merge，幂等）`

## Task 6: 自检脚本 check.ps1

- [ ] 6.1 写 `scripts/check.ps1`，逐项输出 PASS/FAIL：
  - QwenPaw config.json 含 `skill_paths` 且路径存在
  - `~/.cursor\skills` 内试点软链目标存在
  - `~/.cursor\mcp.json` 含试点 server
  - `~/.claude.json` / `~/.codex\config.toml` 含试点 server（CC Switch 侧）
  - `~/.claude\skills` 试点可见（CC Switch 分发）
- [ ] 6.2 跑一遍，全部 PASS
- Commit: `feat: check.ps1 平台装载自检`

## Task 7: CC Switch WebDAV 云同步（A 机）

- [ ] 7.1 CC Switch → Settings（齿轮）→ Advanced → Cloud Sync (WebDAV)
- [ ] 7.2 填写：Service Preset=坚果云（或 Custom）；Server URL / Username / Password（坚果云应用密码）；Remote Directory 默认 `cc-switch-sync`；Profile Name 默认 `default`
- [ ] 7.3 Test Connection → 成功
- [ ] 7.4 手动 Upload（当前库含试点 MCP/skill 记录）
- [ ] 7.5 Auto Sync：建议先关闭或设较长间隔（6h/12h）；写入 SYNC-MATRIX 的单写者纪律
- Verify: 远端目录出现同步产物；本机 `~/.cc-switch\backups\` 机制正常
- 风险备注：DB 内含 provider API Key → 会明文到坚果云，接受则继续

## Task 8: 存量迁移（分批，每批独立验证 + 提交）

> 顺序：先 MCP 后 skill，每批 ≤3 项。迁移对象以 Task 0 的 P 级清单为准；Q/X 级留在原地。

- [ ] 8.1 每批 MCP：代码移入 `mcp/<name>/` → 补 pyproject/README → `pip install -e` → 更新 `registry/mcp.servers.json` 与 `mcp.codex.toml` → CC Switch MCP 面板更新（或删旧加新）→ 冒烟：真实调用一次核心工具
- [ ] 8.2 每批 skill：移入 `skills/<name>/` → 裁剪 frontmatter → CC Switch 中该 skill 由「仓库安装」重新装 → 冒烟：触发一次
- [ ] 8.3 提交遵循分组规范，type 前缀 `feat`/`refactor`/`docs`/`chore`，不 `git add -A`
- Verify: 每批结束跑 `scripts/check.ps1` + 一个真实用例；inventory.csv 迁移状态列更新
- 里程碑：存量 P 级全部迁移完成，Q/X 级在 SYNC-MATRIX 注明「原地管理」

## Task 9: B 机装载与一致性验证

- [ ] 9.1 B 机：clone agent-tools（HTTPS + 代理先例）；按 README 装 Python/uv
- [ ] 9.2 B 机：进入 `mcp/<name>` 逐个 `pip install -e .`（或 `uv tool install -e .`）
- [ ] 9.3 B 机：跑 `scripts/bootstrap.ps1 -RepoRoot <B机路径>`（QwenPaw/Cursor 侧）
- [ ] 9.4 B 机：CC Switch 首次配置 → WebDAV 同步页填同账号 → Download（下载前自动安全备份）→ 确认 provider/MCP/skill 记录出现
- [ ] 9.5 B 机：CC Switch Skills 页对试点 skill Install（仓库安装，把实体文件抓到本机 SSOT）→ 打开 Claude/Codex toggle
- [ ] 9.6 一致性冒烟：在 B 机跑 A 机相同的 3 个真实用例（MCP 工具调用、skill 触发、check.ps1），结果一致
- Verify: A/B `scripts/check.ps1` 输出对齐；用例全过
- 备注：若 B 机配置与 A 机不同（目录/工具版本），在 SYNC-MATRIX 记录差异

## Task 10: 日常维护 SOP 固化（写进 README）

- [ ] 10.1 push-first 工作流写进 README：
  ```
  改 skill/MCP → 本机试（MCP: 直接跑；skill: 软链直读）
  → commit（分组）→ push
  → CC Switch 技能: Skills 页 Update All（SHA-256 检测）
  → QwenPaw: git pull（skill_paths 原地读）
  → Cursor: git pull（软链直读）
  → check.ps1
  ```
- [ ] 10.2 新技能入仓模板说明（最小 frontmatter + 目录约定）写入 README
- [ ] 10.3 CC Switch 单写者纪律 + WebDAV 操作顺序写入 README
- [ ] 10.4 备份策略：CC Switch 定期 Export；仓库 `git tag` 每里程碑
- Commit: `docs: push-first 工作流与维护 SOP`

## Task 11（延后项，不执行，仅留档）

- [ ] Hermes：CC Switch 已支持（Skills/MCP 分发到 `~/.hermes/skills` 与 `config.yaml`），接入时只需：B 机/A 机装 Hermes → CC Switch 打开 Hermes toggle → 对试点 skill/MCP Install/Enable。无需改仓库结构。
- [ ] 公开分享：将来把通用 skill 拆到公开仓，主仓保持私有。

---

## 验收清单（全部完成判定）

- [ ] `JulianWang7/agent-tools` 私有仓含全部 P 级 MCP 与 skill，frontmatter 全为最小集
- [ ] A/B 两机 `scripts/check.ps1` 全部 PASS
- [ ] CC Switch（A/B）WebDAV 同步后试点记录一致，Claude Code + Codex 侧 `/mcp` 与技能均生效
- [ ] QwenPaw 与 Cursor 侧经 bootstrap 装载且幂等（重跑不重复、不破坏旧配置）
- [ ] 真实用例冒烟：MCP 工具一次真实调用 + skill 一次真实触发，两机结果一致
- [ ] SYNC-MATRIX.md 覆盖每个平台「配置源/文件源/更新方式」，无双重配置源
- [ ] 全部提交符合 github-commit-sop（无混组、无 token）

---

## 附录 A：SYNC-MATRIX.md 模板

| 平台 | MCP 配置源 | MCP 文件源 | Skill 装载源 | Skill 更新方式 | 由谁管 |
|------|-----------|-----------|-------------|---------------|--------|
| Claude Code | CC Switch → `~/.claude.json` | 命令名（pip 入口） | CC Switch 仓库安装 → `~/.claude/skills` | CC Switch Update All | CC Switch |
| Codex | CC Switch → `~/.codex/config.toml` | 命令名 | CC Switch → `~/.codex/skills` | CC Switch Update All | CC Switch |
| Hermes（延后） | CC Switch → `~/.hermes/config.yaml` | 命令名 | CC Switch → `~/.hermes/skills` | CC Switch Update All | CC Switch |
| Cursor | `scripts/bootstrap.ps1` → `~/.cursor/mcp.json`（源=`registry/mcp.servers.json`） | 命令名 | bootstrap 软链 → `~/.cursor/skills` | `git pull`（软链直读） | bootstrap |
| QwenPaw | 控制台粘贴 `registry/mcp.servers.json` 片段 | 命令名 | `skill_paths` → clone 目录 | `git pull`（原地读） | bootstrap + 手动一次 |

## 附录 B：风险与缓解

| 风险 | 缓解 |
|------|------|
| CC Switch 仓库安装 vs 本地编辑不生效 | push-first 纪律（Task 10）；高频迭代 skill 先走本地软链不入 CC Switch |
| WebDAV 双机同时自动同步 → DB 冲突 | 单写者：默认关自动同步或 ≥6h；操作顺序=改→Upload→另一机 Download |
| Cursor 软链不支持/被杀软拦 | bootstrap `-CopyMode` 回退复制；check.ps1 兜底 |
| QwenPaw skill_paths 改动影响现有 40+ 技能 | 只增不改：保留工作区原技能，新增共享技能走 skill_paths |
| pip 入口命令名与全局包冲突 | 命名加前缀（如 `jw-workflow`），registry 内唯一 |
| 公司敏感内容误入仓 | Task 0 分级 X 级不入仓；github-commit-sop 凭据扫描；仓库保持私有 |
