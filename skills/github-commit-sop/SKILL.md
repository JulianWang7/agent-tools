---
description: Use this skill when committing to or pushing a GitHub repository (remote
  github.com) — e.g. 上库、推送、push、提交到 GitHub。仅向 GitHub push 时生效，从下一次提交起，不追溯历史 commit。为后续增强预留
  gate：可升级为仅当账号 JulianWang 执行 push 时生效。
name: github-commit-sop
---

# GitHub Commit SOP（分组提交 + Commit Message 规范）

> 来源：个人经验库 `knowledge-base/standards/STD-011-GitHub上库操作标准.md`
> 场景：向 **GitHub 仓库**（remote 为 `github.com`，如 `embedded-workflow-lab` 知识库）提交/推送变更时执行。
> 注意：**不适用于** Gerrit 上库（`refs/for/...`，见 STD-001 / EXP-GIT-001）；也不追溯已经 push 过的历史 commit。

## 触发与生效范围

- **仅当**对 GitHub 远程仓库执行 `git add / commit / push` 时触发本 skill。
- **从下一次提交开始生效**：已完成并推送的旧 commit（如 `2172e45`）不再重写、不追溯。
- 判断依据：`git remote -v` 中 remote URL 含 `github.com`。

<HARD-GATE>
未确认 remote 为 github.com（而非 Gerrit / GitLab / 本地 bare 仓库）前，不要开始分组；不属于 GitHub 场景则直接沿用仓库自身约定。
</HARD-GATE>

## Gate 扩展区（后续增强用）

默认 gate（当前生效）：

| Gate | 条件 | 说明 |
|---|---|---|
| Remote | remote URL 含 `github.com` | 必选，防误用于 Gerrit |

预留 Gate（**当前未强制**，需要时把状态改为 `生效`）：

| Gate | 条件 | 说明 |
|---|---|---|
| Account | push 账号为 `JulianWang`（`git config user.name` 或远程提交者身份） | 建议值；实际生效前需与 git 账号核对 |

增强方式：仅需把上表状态改为「生效」，并在分组提交前增加一项自检：
1. 读取 `git config user.name` / 上一次提交作者；
2. 若作者不是 `JulianWang`，停止提交并向用户确认。

## 核心流程（四步）

```text
git status 查看全部变更
      ↓
按功能/修改内容划分逻辑分组
      ↓
逐组  git add <该组文件>  →  git commit -m "<type>: <subject>"
      ↓
循环直至全部处理完毕 → git status 复查无遗漏 → git push
```

### 第 1 步：查看全部变更

```bash
git status
git diff --stat   # 概览改动规模
```

确认修改（M）、新增（??）、删除（D）三类变更全部可见。

### 第 2 步：逻辑分组

判定标准二选一：
1. **同一类型改动**：如"全部是新增文档"、"全部是 bug 修复"；
2. **共同完成一个功能目标**：如"迁移 diagrams 目录到 plantuml/drawio"。

分组注意事项：
- 粒度适中：过细（一文件一 commit）碎片化；过粗（全部混一起）违背单一职责；
- 按文件路径维度：同一目录/模块的改动通常归一组；
- 特殊文件单列：配置、依赖锁文件、CI 配置建议独立提交；
- 目录迁移通常 `refactor`，新增文档 `docs`，模板/规范更新 `docs` 或 `chore`。

### 第 3 步：分组提交

```bash
git add <文件1> <文件2> ...   # 显式文件列表，禁止 git add . / git add -A 混组
git commit -m "<type>: <subject>"
```

- 需要补充细节用两段式：`git commit -m "docs: 更新上库操作说明" -m "补充：新增检查清单与示例"`。
- 每个 commit 只解决一个问题、完成一个目标。

### 第 4 步：循环直至处理完毕

重复第 3 步直到所有分组提交完成；**全部完成后**统一：

```bash
git status              # 确认无遗漏变更
git log --oneline -n 5  # 确认提交历史与 message 清晰
git push                # 用户确认后再 push
```

## Commit Message 规范

统一格式：`<type>: <subject>`

| type | 含义 | 示例 |
|---|---|---|
| `feat` | 新功能 | `feat: 新增自动化测试框架` |
| `fix` | 修复 bug | `fix: 修复配置加载失败的问题` |
| `docs` | 文档类改动 | `docs: 更新上库操作说明` |
| `refactor` | 重构（不改变功能） | `refactor: 迁移 diagrams 目录到 plantuml/drawio` |
| `chore` | 构建、工具、依赖、杂项 | `chore: 升级依赖版本` |
| `test` | 测试相关 | `test: 补充边界用例` |
| `style` | 格式调整（不改逻辑） | `style: 统一代码缩进` |
| `perf` | 性能优化 | `perf: 缓存设备列表查询结果` |

subject 写法：
- 简洁动词短语，说清"改了什么、为什么"（建议 10~50 字）；
- 可带模块前缀：`docs(git): 更新上库操作说明`、`fix(auto-test): 修复 NFC 误判`；
- 禁止含糊类型（如只写 `update`）与不吸收的一次类型（`fix`/`test` 临时修改混入 `docs`）。

## 检查清单

- [ ] `git remote -v` 确认为 github.com（否则不适用本 skill）
- [ ] `git status` 已确认全部变更（修改 / 新增 / 删除）
- [ ] 变更已按"同类型改动"或"同一功能目标"划分逻辑分组
- [ ] 每组单独 `git add <显式文件>` + `git commit`，message 为 `<type>: <subject>`
- [ ] 未使用 `git add .` / `git add -A` 一次性混组
- [ ] 没有把所有文件一次性提交到一个 commit
- [ ] 提交完成后 `git status` 复查无遗漏，`git log` 分组清晰
- [ ] Gate 扩展区中标记为「生效」的 Gate 已全部自检通过
- [ ] push 前经用户确认

## 反模式

- **"这次改动多，一个 commit 省事"**：违背单一职责，历史无法追溯单项改动；`revert`/`cherry-pick`/评审都难定位。
- **"我已经 push 过了，补一个 amend 吧"**：本 skill 不追溯已完成提交；需要更正请开新 commit 或显式征得用户同意。
- **"git add -A 反正都在一个仓库里"**：会混入其他分组的文件，禁止。