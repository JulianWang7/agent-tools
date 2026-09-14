---
description: 培训任务执行流程路由器。当用户提到培训任务、W3Dn、每日项目、工程批次、交付批次、任务规格、FACT-LOCKED、FINAL、每日流程图、deliverables、提交包、规格批次、检查清单等培训关键词时触发。按阶段从
  Z 盘 skill流 加载对应模块，不一次性加载全部规范。
name: training-flow
---

# 培训任务执行流程（Skill 流路由器）

> ⚠️ **历史状态（2026-09-14 归档）**：本 skill 已基本停用。培训任务流程已改由其他方式执行，本文件仅作历史存档保留，不再随培训流程迭代更新。历史触发词与路由表仅供参考，请勿据此执行当前培训任务。

## 历史来源

- 原位置：QwenPaw workspace `skills/training-flow/`（2026-09-14 备份入 agent-tools）
- 规范源：`D:\Github\wlq-training-archive\mds\training-skill\`（培训统一规范，仍以该仓库最新版本为准）

本 skill 是培训统一规范的按阶段加载路由器。**不内嵌规范全文**，而是根据当前阶段从 `D:\Github\wlq-training-archive\mds\training-skill\` 读取对应模块文件。

## 触发指令

以下任一方式触发本 skill：

- **自动触发**：对话中提到「培训任务」「W3D1」「规格批次」「工程批次」「交付批次」「提交包」「验收」「FACT-LOCKED」「FINAL」等关键词
- **手动触发**：`/training-flow`
- **阶段指令**：直接说阶段名 + 任务编号

| 用户输入 | QwenPaw 动作 | 加载模块 |
|----------|-------------|----------|
| `规格批次 W{n}D{m}` | 生成任务规格 + 截图计划 + 交付清单（DRAFT） | `01_规格批次.md` |
| `工程批次 W{n}D{m}` | 代码→构建→测试→截图→FACT-LOCKED（A→G 七阶段） | `02_工程批次.md` |
| `工程批次 W{n}D{m} 续` | 从上次中断处继续，不重复已完成步骤 | `02_工程批次.md` |
| `交付批次 W{n}D{m}` | 图示→文档→审核→日报→FINAL（A→F 六阶段） | `03_交付批次.md` |
| `提交包 W{n}D{m}` | 整理 deliverables/ + MPE 配置 | `04_提交包整理.md` |
| `验收检查 W{n}D{m}` | verify-all + 检查清单 + Git 状态 | `05_检查清单.md` |
| `核心规则` 或任意培训问题 | 加载目录/编码/状态机/阻塞格式等全阶段规则 | `00_核心规则.md` |

**QwenPaw 可执行全部阶段**，包括工程批次。与 Cursor/Codex 不同，无需在工程批次时切换平台。

## 规范引用策略

**所有规范文件以核心中文名 + "（最新版本）"引用，不硬编码版本号。** 首次引用时执行预检命令确认实际文件名：

```powershell
dir D:\Github\wlq-training-archive\mds\ /b /o:-d | findstr /i "培训统一规范"
dir D:\Github\wlq-training-archive\mds\ /b /o:-d | findstr /i "UML图文档规范"
```

同名多版本时取修改时间最新者。

## 阶段路由表

根据用户当前所处阶段，用 `read_file` 读取对应模块：

| 阶段 | 触发关键词 | 加载模块 |
|------|-----------|----------|
| 全阶段 | 培训任务、目录、编码、阻塞 | `D:\Github\wlq-training-archive\mds\training-skill\00_核心规则.md` |
| 规格生成 | 任务规格、规格批次、WnDn | `D:\Github\wlq-training-archive\mds\training-skill\01_规格批次.md` |
| 工程执行 | 代码实现、构建、测试、截图、FACT-LOCKED | `D:\Github\wlq-training-archive\mds\training-skill\02_工程批次.md` |
| 交付 | 图示、四类文档、审核、日报、FINAL | `D:\Github\wlq-training-archive\mds\training-skill\03_交付批次.md` |
| 提交包 | Dn交付、提交包、MPE | `D:\Github\wlq-training-archive\mds\training-skill\04_提交包整理.md` |
| 验收 | verify-all、Git、检查清单、推送 | `D:\Github\wlq-training-archive\mds\training-skill\05_检查清单.md` |

## 执行规则

1. **每次只加载当前阶段需要的模块**，不预加载全部；
2. 加载模块后，按模块中的 Prompt 和规则执行；
3. 需要引用专项规范时，先 `dir` 确认文件名再 `read_file`；
4. 阶段切换时，先确认上一阶段已完成（如 FACT-LOCKED → 交付）；
5. 全流程索引见 `D:\Github\wlq-training-archive\mds\training-skill\INDEX.md`。

## 七步流程速查

```
[1] 人工准备 → [2] 规格 → [3] 工程 → [4] 交付 → [5] 提交包 → [6] 验收 → [7] Git 推送
```

QwenPaw/Claude Code 可负责步骤 [2][3][4][5][6]；Cursor/Codex 负责步骤 [3]；人工负责步骤 [1][7]。

## 四平台分工

| 平台 | 可执行阶段 | 部署方式 |
|------|-----------|----------|
| **QwenPaw** | **全部阶段（规格/工程/交付/提交包/验收）** | 全局 skill（一次性） |
| Cursor | 工程批次 | 项目 `.cursor/rules/`（每周复制） |
| Codex | 工程批次 | 项目 `AGENTS.md`（每周复制） |
| **Claude Code** | **全部阶段（含工程）** | **全局 skill（一次性）** |
