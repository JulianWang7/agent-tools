# SYNC-MATRIX —— 平台装载对照表

> 目的：每个平台的「配置源 / 文件源 / 更新方式」唯一归属，防止同一 MCP/技能出现两个配置源。
> 更新规则：任何平台装载方式变化，先改这张表，再改实现。

## 当前归属（2026-09-05 定稿）

| 平台 | MCP 配置源 | Skill 装载源 | 更新方式 | 由谁管 |
|------|-----------|-------------|---------|--------|
| Claude Code | CC Switch → `~/.claude.json` | CC Switch 仓库安装 → `~/.claude/skills` | CC Switch Update All | CC Switch |
| Codex | CC Switch → `~/.codex/config.toml` | CC Switch → `~/.codex/skills` | CC Switch Update All | CC Switch |
| Hermes（延后） | CC Switch → `~/.hermes/config.yaml` | CC Switch → `~/.hermes/skills` | CC Switch Update All | CC Switch |
| Cursor | `scripts/bootstrap.ps1` → `~/.cursor/mcp.json`（源 = `registry/mcp.servers.json`） | bootstrap 软链 → `~/.cursor/skills` | `git pull`（软链直读） | bootstrap |
| QwenPaw | 控制台粘贴 `registry/mcp.servers.json` 片段 | `config.json` `skill_paths` → 本仓 clone 目录 | `git pull`（原地读） | bootstrap + 手动一次 |

## 共同约定

- **MCP 文件源（所有平台）**：`mcp/<name>/` 经 `uv tool install -e .` 安装，注册时 command 只写命令名；clone 路径允许各机不同。
- **CC Switch WebDAV 单写者纪律**：同一时刻只允许一台机器执行「上传/下载」写操作；改配置 → Upload → 另一台 Download。`settings.json` 为设备级，不同步。
- **实体文件同步边界**：WebDAV 只同步 `cc-switch.db`（providers / MCP / prompts / skills 记录）；skill 实体文件以本 git 仓为准。
- **仓库私有**：Q/X 级（QwenPaw 绑定、含敏感内容）技能不入仓。
