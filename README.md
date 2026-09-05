# agent-tools

私有仓库：自研 MCP server 与 Skill 的唯一事实源（SSOT），跨平台（Claude Code / Codex / Cursor / QwenPaw / Hermes*）统一装载。
Hermes 延后接入，见 `docs/plans/2026-09-05-agent-tools.md`。

## 目录结构

| 路径 | 用途 |
|------|------|
| `skills/<name>/SKILL.md` | 通用技能。frontmatter 仅保留 `name` + `description`（跨平台最小集），不用厂商专属 YAML |
| `mcp/<name>/` | 自研 MCP server。各自带 `pyproject.toml`，安装后 command 只写命令名（消除跨机绝对路径差异） |
| `registry/mcp.servers.json` | 标准 mcpServers JSON：Claude Code / Cursor / QwenPaw 共用的注册粘贴源 |
| `registry/mcp.codex.toml` | Codex 的 `[mcp_servers]` 注册（与 JSON 同步维护） |
| `scripts/` | `bootstrap.ps1`（QwenPaw skill_paths + Cursor 软链/mcp.json merge，幂等）；`check.ps1`（装载自检） |
| `docs/plans/` | 实施计划 |

## 装载矩阵

见 `SYNC-MATRIX.md`：每个平台的「配置源 / 文件源 / 更新方式」唯一归属，避免双源漂移。

## push-first 工作流（维护纪律）

1. 本地改（skill / MCP 代码）
2. 分组提交（沿用 github-commit-sop：显式 `git add <文件>`、`<type>: <subject>`、禁止 `git add -A` 混组）
3. `git push`
4. 各平台更新：
   - CC Switch 管的三家（Claude Code / Codex / Hermes*）：Skills 面板 Update All（SHA-256 比对远端）
   - QwenPaw：`git pull`（`skill_paths` 原地读）
   - Cursor：`git pull`（软链直读）
5. `scripts/check.ps1` 自检

> 注意：CC Switch 的技能来源是 **GitHub 仓库**（不是本地 clone），本地改动不生效，必须先 push 再 Update All。

## 新增技能规范

- 目录：`skills/<skill-name>/SKILL.md`（+ 附属 scripts/ 等）
- frontmatter 最小集：
  ```markdown
  ---
  name: <skill-name>
  description: <触发词+同义词，≤200 字>
  ---
  ```
- 含平台专属能力（如 QwenPaw 的 channel_message / cron）的技能不进本仓，留在对应平台工作区。
