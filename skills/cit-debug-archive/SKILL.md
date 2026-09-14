---
description: Use this skill when 用户说「归档」、把某次与 Cursor 的 debug/调研/规划对话总结到经验库，或要求把对话内容落到
  debug-records 并更新 daily-notes 后 git 提交推送；也用于「本周提炼」「周复盘」把近期复盘卡提炼成 EXP 条目并更新 INDEX/README。输入是一次对话的复盘摘要（直接文本或
  inbox 文件路径），输出是新的 debug-records 复盘卡、当日 daily-notes 更新与 git 提交推送。同对话再次归档用 mode=supplement 追加，勿重复新建。
name: cit-debug-archive
---

# CIT Debug 对话归档（实时 + 周提炼）

把「与 Cursor 的一次 debug/调研/规划对话」沉淀为一张复盘卡，落到经验库 `D:\Workspace\GDocuments\embedded-workflow-lab\knowledge-base`，更新当日 daily-notes，最后 git 提交并推送 GitHub。周末/阶段末再提炼可复用经验为 EXP 条目。

## 前置约定（先读）

- 知识库根：`D:\Workspace\GDocuments\embedded-workflow-lab\knowledge-base`
- 复盘卡目录：`knowledge-base\debug-records\`
- **编号规则**：列 `debug-records\*.md`，取 `EXP-DEBUG-NNN`（或 `NN_`）最大号 +1。优先 EXP 风格。
- **文件名**：`EXP-DEBUG-NNN_YYYY-MM-DD_<主题短名>.md`
- inbox：`D:\Workspace\.archive-inbox\`；上次归档标记：`.archive-inbox\.last-archive.json`
- 粒度：**一个主主题一张卡**；同对话后续进展用 **补充归档**，不要为同一主题连开多张新卡。
- 归档即推送：`git commit` + `git push origin main`（分组提交，参考 STD-011）。

## 新建 vs 补充

| 模式 | 何时 | 行为 |
|------|------|------|
| **new** | 本对话第一次归档 / 新主题 | 新建 `EXP-DEBUG-NNN_…` |
| **supplement** | 同一 Cursor 对话里再次说「归档」/ 补充进展 | 在已有卡末尾追加 `## 补充归档（时间）`；目标默认读 `.last-archive.json`，或传 `target_card` |

## 输入来源

1. 指令内摘要文本，或  
2. inbox 路径（Cursor 已写好 What/How/Why/…）  

半成品也按下方模板整理成规范复盘卡，不是原样粘贴。

## ALWAYS use this template（复盘卡）

权威模板：`knowledge-base\_templates\debug复盘卡模板.md`。

```markdown
---
日期: YYYY-MM-DD
项目: CIT自动化工作流搭建
模块: cit3.0 / cit4 / Auto / Jenkins / QFIL / 110编译 / 其他
关联: （可选）
状态: 已解决 / 进行中 / 已阻塞
---

# <主题标题>

## 问题（What）
## 排查过程（How）
## 根因（Why）
## 结论 / 改动（Change）
## 验证（Verify）
## 踩坑 / 教训（Lesson）
## 下一步（Next）
```

> ⚠️ **frontmatter 硬规则**：`关联` 字段只填**纯 ID**（`EXP-TOOLS-007, EXP-TOOLS-014`、`EXP-CIT-003`、`Bug97203`、`#97203` 等，逗号分隔）。**禁止写 `[[…]]` wiki 双向链接**——YAML 里裸写 `[[…]]`（以 `[` 开头、未加引号）会让解析器误判为数组，导致整个 frontmatter 解析失败、Obsidian「属性」面板里日期/项目/关联/状态**一起**显示错乱。同理其它 frontmatter 字段值若需含 `[`、`:`、`#` 等特殊字符，须用双引号包裹。

## 归档执行步骤（压缩工具轮次 — 最多 3 次工具）

禁止「先 ls 再读模板再读 daily 再逐个 git」的碎步骤。按下面做：

1. **一次 shell 探路+读入**（单次 `execute_shell_command`）  
   ```bash
   python -c "import pathlib,re; d=pathlib.Path(r'D:/Workspace/GDocuments/embedded-workflow-lab/knowledge-base/debug-records');
   xs=sorted(d.glob('*.md'));
   print('NEXT', max([int(re.match(r'EXP-DEBUG-(\d+)',p.name).group(1)) for p in xs if re.match(r'EXP-DEBUG-(\d+)',p.name)]+[0])+1);
   print('---INBOX---'); print(pathlib.Path(r'<inbox>').read_text(encoding='utf-8'));
   print('---LAST---'); p=pathlib.Path(r'D:/Workspace/.archive-inbox/.last-archive.json');
   print(p.read_text(encoding='utf-8') if p.exists() else '')"
   ```
2. **一次写入**（单次或紧挨两次 `write_file`）：新卡 **或** 追加补充块 + 更新 `daily-notes/今天.md`（沉淀区一行）。
3. **一次 git**（单次 shell）：  
   `git add <card> <daily> && git commit -m "docs: …" && git push origin main`

**首选（Cursor）**：直接调个人 MCP `user-JulianWang-workflow` / `archive_obsidian`（代码 `D:\Workspace\tools\cit-workflow-mcp\`），0 次手工读写，返回短文本。本 skill 的手动步骤仅在无 MCP / Console 人工归档时使用。

## 周提炼模式（周末 / 阶段末）

触发：「本周提炼」「周复盘」。扫近 7 天复盘卡 → 能复用则写 `EXP-CIT-xxx` + 更新 INDEX/README → 分组 commit/push。一次性事件留在 debug-records。

## 检查清单

- [ ] 编号无冲突；同主题优先 supplement 而非连建新卡  
- [ ] frontmatter 齐全；`关联` 为纯 ID（无 `[[…]]`）；daily-notes 已记沉淀行  
- [ ] git commit + push 完成  

## 与 Cursor 规则的关系

`D:\Workspace\.cursor\rules\cit-debug-archive.mdc`：写 inbox → **一次** `user-JulianWang-workflow.archive_obsidian`（new 或 supplement）→ 报告短结果。

- **推荐**：个人 MCP `JulianWang-workflow`（`D:\Workspace\tools\cit-workflow-mcp\`），独立于 android-bugfix-flow  
- **不要** `misc-mcp`、`qwenpaw task`、`agents chat --json-output`  
- Console 人工归档时仍可加载本 skill，但须遵守「最多 3 次工具」
