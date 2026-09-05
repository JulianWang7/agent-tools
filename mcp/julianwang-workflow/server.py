"""JulianWang-workflow — 个人工作流 MCP（独立于 cit-workflow 业务仓 / android-bugfix-flow）。

本 MCP 是个人工作流起点：归档、后续可扩展的智能化能力都维护在这里。
cit-workflow 仓库是当前待完善的业务工程，二者不得混淆。

工具：
  archive_obsidian — 工作记录归档（debug|experience|knowledge）到 Obsidian 经验库
  get_archive_status — 查看 active lineage（fork 续档自检）
  get_standards_skill_status — 查看规范、canonical Skill 与安装副本漂移
  build_standards_skill — 从规范源文件重建受控参考与模板
  sync_standards_skill — 预览或同步安装规范 Skill
  sync_standards_manager — 预览或同步安装 standards-to-skills 管理 Skill
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

# standards_to_skills 已 vendored 到本目录（与 server.py 同目录），无需外部同级路径

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print(
        "ERROR: mcp SDK 未安装。请: pip install 'mcp[cli]'",
        file=sys.stderr,
    )
    sys.exit(1)

from archive import archive_inbox, archive_status
from standards_to_skills import (
    build_standard_skill,
    get_standard_skill_status,
    sync_manager_skill,
    sync_standard_skill,
)

mcp = FastMCP("JulianWang-workflow")


def _run_archive(
    inbox_path: str,
    mode: str = "new",
    target_card: str = "",
    title: str = "",
    module: str = "其他",
    status: str = "已解决",
    related: str = "",
    category: str = "debug",
    lineage_id: str = "",
    push: bool = True,
) -> str:
    try:
        return archive_inbox(
            inbox_path=inbox_path,
            mode=mode,
            target_card=target_card,
            title=title,
            module=module,
            status=status,
            related=related,
            category=category,
            lineage_id=lineage_id,
            push=push,
        )
    except Exception as e:
        return f"[ERR] 归档失败: {e}"


@mcp.tool()
def archive_obsidian(
    inbox_path: str,
    mode: str = "auto",
    target_card: str = "",
    title: str = "",
    category: str = "debug",
    lineage_id: str = "",
    module: str = "其他",
    status: str = "已解决",
    related: str = "",
    push: bool = True,
) -> str:
    """个人工作流归档（广泛工作记录，不只 debug）。

    写入经验库对应目录 + daily-notes，并 git commit/push。

    Fork 子会话通常是新主题：mode=auto **默认新建独立 md**，不会默默拼到父卡。
    仅当显式传 target_card / lineage_id，或 mode=supplement 时才追加已有卡。

    Args:
        inbox_path: inbox 绝对路径
        mode: new|supplement|auto（默认 auto=新开卡；显式 lineage_id/target_card 才续写）
        target_card: 显式目标卡（文件名 / EXP-DEBUG-010 / 绝对路径）
        title: 完整标题（建议必填）
        category: debug→debug-records；experience→work-records；knowledge→knowledge/KB-NOTE
        lineage_id: 显式续写父卡时传入（不要 fork 后盲目传）
        module: 模块标签
        status: 状态
        related: 关联条目
        push: 是否 git push
    """
    return _run_archive(
        inbox_path=inbox_path,
        mode=mode,
        target_card=target_card,
        title=title,
        module=module,
        status=status,
        related=related,
        category=category,
        lineage_id=lineage_id,
        push=push,
    )


@mcp.tool()
def get_archive_status() -> str:
    """查看当前 active lineage / last-archive（fork 前自检用）。"""
    try:
        return archive_status()
    except Exception as e:
        return f"[ERR] status 失败: {e}"


def _json_result(operation) -> str:
    try:
        return json.dumps(
            {"ok": True, "result": operation()},
            ensure_ascii=False,
            indent=2,
        )
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False, indent=2)


@mcp.tool()
def get_standards_skill_status(standard_id: str = "STD-004") -> str:
    """检查规范源、canonical Skill 及 Cursor/Claude/QwenPaw 安装副本是否漂移。"""
    return _json_result(lambda: get_standard_skill_status(standard_id))


@mcp.tool()
def build_standards_skill(standard_id: str = "STD-004") -> str:
    """从维护清单声明的规范源文件重建 canonical Skill 参考与模板资产。"""
    return _json_result(lambda: build_standard_skill(standard_id))


@mcp.tool()
def sync_standards_skill(
    standard_id: str = "STD-004",
    targets: str = "cursor,claude",
    apply: bool = False,
) -> str:
    """预览或同步规范 Skill；targets 为逗号分隔目标，apply 默认 false。"""
    target_names = [item.strip() for item in targets.split(",") if item.strip()]
    return _json_result(
        lambda: sync_standard_skill(standard_id, target_names, apply=apply)
    )


@mcp.tool()
def sync_standards_manager(
    targets: str = "cursor,claude",
    apply: bool = False,
) -> str:
    """预览或同步 standards-to-skills 管理 Skill；apply 默认 false。"""
    target_names = [item.strip() for item in targets.split(",") if item.strip()]
    return _json_result(lambda: sync_manager_skill(target_names, apply=apply))


def main() -> None:
    """Console entry point（pyproject [project.scripts]）。"""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
