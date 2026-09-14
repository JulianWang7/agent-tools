# agent-tools

个人工作流工具箱：用来**整理、备份、学习与适配**自己用过的 Agent Skill 与自研 MCP，而不是替代各平台里已有的业务仓（如 android-bugfix-flow）。

## 仓库定位（先读）

| 要做什么 | 本仓角色 |
|:---|:---|
| 把 Cursor / Claude 上自己写的 skill、自研 MCP **归档一份** | ✅ 主用途：复制进 `skills/`、`mcp/`，便于对照、改版、跨平台复用 |
| 学习「怎样写 skill / 怎样挂 MCP」并逐步适配自己的习惯 | ✅ 主用途：以本仓为演练与定稿处 |
| android-bugfix-flow 全套 skill、第三方 drawio/utools | ❌ 不进本仓（仍归原项目 / 原厂商） |
| Cursor 产品自带 `skills-cursor` | ❌ 不进本仓 |

**一句话：** 本仓是「个人向 skill/MCP 的整理柜 + 学习笔记本」；平台装载可以继续用副本、联接或 CC Switch，按 `SYNC-MATRIX.md` 选一种，避免两处各改各的却不知道哪份为准。

## SSOT 是什么意思？

**SSOT = Single Source of Truth（单一事实来源）。**

意思是：同一份 skill/MCP **约定以本仓（或你指定的一份）为权威**，其它位置只是安装/联接/同步结果，避免 Cursor 一份、Claude 一份、桌面又一份，改乱了无法对齐。

- **整理阶段**：先把现有内容**复制**进本仓即可（备份 + 可追溯）。  
- **装载阶段（可选）**：再决定用目录联接 / `skill_paths` / CC Switch 指向本仓。  
若你只要求「复制整理、不要动平台安装」，则只做复制、不改 `~\.cursor\skills` 等路径。

## 目录结构

| 路径 | 用途 |
|------|------|
| `skills/<name>/SKILL.md` | 个人向技能。frontmatter 仅保留 `name` + `description`（跨平台最小集） |
| `mcp/<name>/` | 自研 MCP。建议带 `pyproject.toml`，注册时 command 尽量只写命令名 |
| `registry/mcp.servers.json` | mcpServers JSON 粘贴源（Cursor / Claude / QwenPaw） |
| `registry/mcp.codex.toml` | Codex 注册片段 |
| `scripts/` | bootstrap / check（可选；装载自动化） |
| `docs/plans/` | 实施计划 |

## 当前已收录（个人向）

| 名称 | 类型 | 说明 |
|------|------|------|
| `github-commit-sop` | skill | GitHub 上库 |
| `gerrit-commit-sop` | skill | Gerrit `refs/for` 上库 |
| `create-review-uml-diagrams` | skill | STD-004 UML |
| `standards-to-skills` | skill | 规范→Skill 路由（工具仓仍可在 `D:\Workspace\tools\standards-to-skills`） |
| `julianwang-workflow` | mcp | 个人归档等工作流 MCP |

## 装载矩阵

见 `SYNC-MATRIX.md`。各平台「配置源 / 文件源 / 更新方式」尽量单一归属，减少双源漂移。

## push-first 工作流（维护纪律）

1. 本地改（skill / MCP）  
2. 分组提交（`github-commit-sop`：显式 `git add`、`<type>: <subject>`）  
3. `git push`  
4. 各平台按 SYNC-MATRIX 更新（软链直读 / `git pull` / CC Switch Update All）  
5. 有则跑 `scripts/check.ps1`

> CC Switch 若绑的是 **GitHub 远端**：本地改完必须 push，再在面板 Update All。

## 新增技能规范

- 目录：`skills/<skill-name>/SKILL.md`（+ 可选 `references/`、`scripts/`）  
- frontmatter：

```markdown
---
name: <skill-name>
description: <触发词+同义词，建议 ≤200 字>
---
```

- 平台专属、强绑定某厂商 channel 的 skill 可不进本仓，留在对应工作区。
