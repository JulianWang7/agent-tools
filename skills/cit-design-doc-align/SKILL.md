---
description: Use this skill when 用户说「设计文档对齐项目颗粒度」，或要求把 cit 设计文档（topics/cit/cit设计文档，EXP-CIT-012~018）与项目
  D:\Workspace\cit-workflow 实际代码对齐、同步、校正。触发后扫描项目代码与全部设计文档，逐项核对颗粒度（命名、流程步骤/判断/异常分支、时序/流程/状态图、接口/数据结构/参数/返回值/错误码、配置项/环境变量/外部依赖/版本），以项目代码为唯一权威来源更新文档，并输出每文档变更摘要及「待确认」清单。
name: cit-design-doc-align
---

# CIT 设计文档对齐项目颗粒度

把 CIT 自动化工作流的设计文档，与项目真实代码/框架/实测结果逐项对齐到「颗粒度」级别，
使文档中的模块、接口、流程、图示、配置等细节都与 `D:\Workspace\cit-workflow` 的实际实现一致。

## 触发条件

当用户说「设计文档对齐项目颗粒度」，或其近义表述时触发：

- 设计文档对齐项目颗粒度
- 对齐 / 同步 / 校正 设计文档
- 文档对齐代码 / 文档跟代码对齐 / 文档更新到与代码一致
- 让 cit 设计文档贴合项目实际实现

## 固定路径（每次触发均使用，勿让用户重新提供）

| 项 | 路径 |
|---|---|
| 项目代码根 | `D:\Workspace\cit-workflow` |
| 设计文档目录 | `D:\Workspace\GDocuments\embedded-workflow-lab\knowledge-base\topics\cit\cit设计文档` |
| 知识库仓库 | `D:\Workspace\GDocuments\embedded-workflow-lab\knowledge-base`（git，remote 指向 GitHub `JulianWang7/embedded-workflow-lab`） |

项目为 **Python 项目**（`pyproject.toml` 声明 `requires-python = ">=3.10"`，包名 `cit-workflow`，版本 `0.1.0`）。
Windows 环境，默认 shell 为 `cmd.exe`。

## 核心原则（贯穿全程）

1. **项目代码是唯一权威来源。** 文档描述若与代码冲突，一律以代码为准，改文档不改代码。
2. **唯一例外**：仅当代码即将发生重大重构、且后续细节仍会频繁调整时，才可暂缓对齐并显式标注「待重构后对齐」；否则始终紧密对齐真实实现。
3. **不要凭空删除文档内容。** 文档中描述但项目里找不到实际对应的内容，标记为「⚠️ 待确认」（保留原文 + 标注），而不是擅自删除。
4. 这是一项**语义比对任务**，无法纯脚本自动化；每一步都需要读懂代码与文档后判断，必须逐步执行，不要图快跳过。

## 执行步骤

### 步骤 1：扫描项目代码，建立「真实实现」清单

对 `D:\Workspace\cit-workflow` 做全面扫描，摸清当前真实框架与结构。

**1a. 看目录与文件结构**

```cmd
dir /b "D:\Workspace\cit-workflow"
```

重点理解这些顶层目录的职责（以实际存在为准）：
- `.cursor\skills\` — Cursor 侧的 `cit-*` 技能（如 cit-context-prepare、cit-plan-bank、citfix、cit-analyze、cit-compile、cit-flash、cit-review、cit-verify 等）
- `bugflow\` — bug 流转（含 `core\git.py`、`core\zentao.py`、`cli\setup.py`）
- `citfix\` — 改码修复核心模块
- `config\` — 配置（含 `citfix\`、`compile\` 子目录及 `*.yaml.example` 样例）
- `contracts\` — 契约/接口定义
- `docs\` — 项目内文档（如 cit-env-and-context、cit-mcp-reference、citfix-* 系列）
- `fixtures\` — 测试夹具（如 `context_prepare\context.json`）
- `mcp\` — MCP server（如 `citfix_server.py`）
- `plan_bank\` — 计划库（按项目分子目录，如 `MT5825\`、`plan_bank_SLB783-A14\`）
- `runs\` / `runs_work\` — 运行产物目录
- `scripts\` — 入口脚本（`citfix.py`、`citfix_batch.py`、`cit_*.py` 等）
- `schemas\` — JSON Schema（如 `cit_context_snapshot.schema.json`）
- `tests\` — 测试用例
- `workflow\` — 工作流 JSON（如 citfix_pipeline.json）
- `pyproject.toml` / `requirements-*.txt` / `setup_env.cmd` — 构建与环境

**1b. 提取关键实现细节**（用 `read_file` / `grep_search` 逐个读关键文件）：
- 模块划分与依赖关系
- 数据流（谁调谁、数据如何流转）
- 接口定义（函数签名、类名、方法名、参数、返回值）
- 状态管理（状态机、状态枚举、状态转移）
- 异常处理（抛什么异常、错误码/错误信息）
- 关键算法（核心处理逻辑）
- 数据结构 / JSON Schema 字段（尤其 `schemas\*.schema.json`、`contracts\`、`fixtures\*.json`）

**1c. 查近期代码变更痕迹**（判断文档可能滞后点）：

```cmd
cd /d "D:\Workspace\cit-workflow" && git status -s
cd /d "D:\Workspace\cit-workflow" && git log --oneline -20
cd /d "D:\Workspace\cit-workflow" && git diff --stat HEAD
```

`git status -s` 里 `M`（修改）/`D`（删除）/`??`（未跟踪新增）的文件，往往正是文档最容易脱节的地方，
逐一看这些文件的 diff（`git diff HEAD -- <path>`）和未跟踪新文件的内容。
也可用文件修改时间辅助判断：`dir /o-d /t:w /s "D:\Workspace\cit-workflow"`。

### 步骤 2：读取全部现有设计文档

```cmd
dir /b "D:\Workspace\GDocuments\embedded-workflow-lab\knowledge-base\topics\cit\cit设计文档"
```

当前应有 7 篇（以实际为准，可能增减）：`EXP-CIT-012` ~ `EXP-CIT-018`。
用 `read_file` 逐个读取每一篇的完整内容，记录每篇的：
- 文档标题 / 编号 / 日期
- 各章节标题（尤其是描述模块、接口、流程、图示、配置的部分）
- 文中出现的所有代码级标识符（模块名、文件路径、类名、函数名、变量名、错误码、配置项、版本号）

### 步骤 3：逐项对比代码与文档，核对颗粒度

以「文档中的每一项声明」为核对单位，逐项到代码里找对应，判定是否一致。
按以下清单逐项过（这是本 skill 的核心）：

1. **命名一致**：文档中的模块/组件名称、文件路径、类名、函数名、变量名是否与代码完全一致。
   - 例：文档写 `citfix.py`，代码实际入口是 `scripts\citfix.py` 还是 `mcp\citfix_server.py`？路径要精确。
2. **流程一致**：文档描述的每一步骤、判断条件、异常分支是否与代码逻辑一一对应。
   - 缺失的步骤要补，多写的、代码里不存在的分支要标「待确认」。
3. **图示一致**：文档中的时序图、流程图、状态图，其参与者、调用箭头、状态节点是否与实现代码相符。
   - 图内如果引用了函数名/模块名/状态名，同样要核对命名是否过时。
4. **接口/数据结构/参数/返回值/错误码一致**：这些细节必须与代码中定义逐字一致。
5. **配置/环境/依赖/版本一致**：任何配置项、环境变量、外部依赖、版本信息均与项目实际保持一致。
   - 例如 `pyproject.toml` 的 `requires-python`、依赖列表、`config\*.yaml.example` 的字段名。

**判定结果三分类**：
- ✅ 一致：无需改动
- 🔧 不一致：文档需按代码修正
- ⚠️ 待确认：文档有、但代码里找不到实际对应（或代码即将重构暂缓对齐）

### 步骤 4：以代码为唯一权威来源更新文档

按步骤 3 的判定结果，用 `edit_file` 对每篇文档做**外科手术式**修改：
- 只改不一致的地方，不顺手重构文档排版或措辞。
- 改命名时，注意同步该文档内部的交叉引用与图示说明文字。
- 「待确认」项：保留原文，在其后追加标注，例如 `> ⚠️ 待确认：代码中未找到对应实现（对齐日期 YYYY-MM-DD）`。
- 不要动文档的 frontmatter 之外无关内容；若文档含 YAML frontmatter（如日期/项目/状态），如无必要不改。
- 不自动 `git add/commit/push`——对齐完成后**先向用户汇报变更摘要**，由用户决定是否提交。
  若用户要求提交，则遵守知识库的 STD-011 分组提交规范（`git status` → 逻辑分组 → 逐组 `git add <文件>` + `<type>: <subject>`，禁止 `git add -A` 混组）。

### 步骤 5：输出变更摘要

完成更新后，向用户输出一份结构化变更摘要：

```
## 设计文档对齐变更摘要（<对齐日期>）

### 对齐范围
- 项目：D:\Workspace\cit-workflow
- 文档：<文档数> 篇（EXP-CIT-012 ~ EXP-CIT-018）

### 各文档修改明细
#### <文档文件名>
- [命名] ...（改了什么，原→新）
- [流程] ...
- [图示] ...
- [接口/数据结构] ...
- [配置/依赖/版本] ...

### 待确认项
- <文档> → <内容>：代码中未找到对应实现 / 即将重构暂缓对齐

### 未改动文档
- <列表>（如有：已与代码一致，无需修改）
```

## 注意事项

- **不要凭记忆或猜测代码内容**。每个判定都要落到 `read_file` / `grep_search` 读到的真实代码上，再下结论。
- **路径必须绝对精确**。项目里有 `scripts\citfix.py` 与 `mcp\citfix_server.py` 两个易混文件；`config\` 下有子目录与 `.example` 样例，引用时写全。
- **代码正在高频变动**（当前 `git status` 有大量 `M/D/??`）。优先以 `git status -s` + 文件修改时间锁定的「近期改动」文件为对齐重点。
- **图示核对**：文档若含 PlantUML/Draw.io 源（可能在 `plantuml\source\`、`drawio\source\` 或文档内嵌），其中的标识符同样要核对。
- 每次触发都**完整重跑**上述 1→5 步，不要只做增量、也不要复用上次的结论——代码变了，结论要重新得出。