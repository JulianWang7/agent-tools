# julianwang-workflow（MCP）

**个人工作流 MCP**（工作流起点：归档 / 标准技能维护）。
**不是** `D:\Workspace\cit-workflow` 业务仓库；二者用途与范围不得混淆。

> 仓库内副本：移自 `D:\Workspace\tools\cit-workflow-mcp`（SSOT = 本仓库）。
> `standards_to_skills.py` 已 vendored 进本目录（原为外部同级目录 `standards-to-skills`），保证命令独立可装。

## 安装（可安装化，command 名 = `julianwang-workflow`）

```cmd
cd <clone>\mcp\julianwang-workflow
uv tool install --editable .
where julianwang-workflow      # 应能定位到 ~/.local\bin\julianwang-workflow.exe
julianwang-workflow            # stdio MCP server（等输入，正常应挂起不退出）
```

注册配置中只写命令名，不写绝对路径（跨机一致）：

```json
{ "mcpServers": { "JulianWang-workflow": { "command": "julianwang-workflow", "args": [] } } }
```

## 工具

| 工具 | 说明 |
|------|------|
| `archive_obsidian` | 主入口。`mode=auto` **默认新开 md**；仅显式 `lineage_id`/`target_card` 才续写 |
| `get_archive_status` | 查看 active lineage |
| `get_standards_skill_status` | 查看规范源、canonical Skill 与 Cursor/Claude/QwenPaw 副本是否漂移 |
| `build_standards_skill` | 按维护清单从规范源文件重建 Skill 参考与模板资产 |
| `sync_standards_skill` | 预览或同步安装；`apply=false` 默认不写入 |
| `sync_standards_manager` | 预览或同步安装 `standards-to-skills` 管理 Skill；`apply=false` 默认不写入 |

## Fork 与续写

Fork 子会话通常是另一条直线任务/新主题 → **单开一张 md**。

| 意图 | 调用 |
|------|------|
| Fork / 新主题 / 新任务 | `mode="auto"` 或 `new`（默认新卡） |
| 同主题继续补充 | `mode="supplement"`，或 `auto` + `lineage_id` / `target_card` |

## 类别落点

| category | 目录 | 文件前缀 |
|----------|------|----------|
| debug | `knowledge-base/debug-records/` | `EXP-DEBUG-*` |
| experience | `knowledge-base/work-records/` | `EXP-WORK-*` |
| knowledge | `knowledge-base/knowledge/` | `KB-NOTE-*` |

## 自测

```powershell
cd <clone>\mcp\julianwang-workflow
python tests\test_archive_lineage.py
```

改代码后请 **Reload MCP（JulianWang-workflow）**。

## ⚠️ 本机化注意（跨机适配待办）

- `archive.py` 顶部硬编码 `DEFAULT_KB` / `DEFAULT_REPO` / `INBOX_DIR` 为 A 机绝对路径（D:\Workspace\...），B 机需改或后续抽成环境变量。
- `standards-manifest.json` 与 `skills/` 模板资产为**本机安装状态**（含绝对路径），**未随包入仓**；规范技能类工具在 B 机需各自维护清单（默认读取 `standards_to_skills.py` 同目录的 manifest）。