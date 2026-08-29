# -*- coding: utf-8 -*-
"""
Zcode 对话删除程序 —— 数据层
负责扫描 Zcode 客户端对话记录，并在用户确认后彻底删除对话及其全部关联数据。

数据布局（基于对本机 Zcode 的实际逆向确认）：
  ~/.zcode/v2/tasks-index.sqlite        桌面端对话索引（tasks 等表，task_id = sess_<uuid>）
  ~/.zcode/cli/db/db.sqlite             CLI 会话库（session 及 10+ 张 session_id 关联表）
  ~/.zcode/cli/rollout/                 model-io-<task_id>.jsonl 会话输入输出日志
  ~/.zcode/cli/artifacts/<task_id>/     会话产物
  ~/.zcode/cli/exec/<task_id>/          会话执行目录
  ~/.zcode/cli/image-cache/<task_id>/   会话图片缓存
  ~/.zcode/v2/logs/, ~/.zcode/cli/log/  应用日志（可能含会话 ID 明文）
"""

from __future__ import annotations

import json
import shutil
import sqlite3
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

HOME = Path.home()
ZCODE_DIR = HOME / ".zcode"
TASKS_DB = ZCODE_DIR / "v2" / "tasks-index.sqlite"
CLI_DB = ZCODE_DIR / "cli" / "db" / "db.sqlite"
BACKUP_ROOT = HOME / ".zcode-cleaner-backup"

STATUS_LABELS = {
    "completed": "已完成",
    "error": "已出错",
    "running": "进行中",
    "queued": "排队中",
    "cancelled": "已取消",
    "stopped": "已停止",
}


class ScanError(Exception):
    """扫描失败（数据库缺失/损坏/被锁定等）。"""


class DeleteError(Exception):
    """删除失败（数据库被锁定/文件占用等）。"""


@dataclass
class Conversation:
    task_id: str
    title: str
    workspace: str
    status: str  # 原始状态码
    created_at: int  # ms
    updated_at: int  # ms
    message_count: int = 0
    source: str = "桌面端"  # 桌面端 / CLI

    @property
    def status_label(self) -> str:
        return STATUS_LABELS.get(self.status, self.status or "未知")

    @property
    def updated_text(self) -> str:
        try:
            t = time.strftime("%Y-%m-%d %H:%M", time.localtime(self.updated_at / 1000))
        except Exception:
            t = "—"
        return t


# ---------------------------------------------------------------- 扫描

def _open_ro(db: Path) -> sqlite3.Connection:
    """以只读模式打开 SQLite，避免干扰运行中的 Zcode。"""
    if not db.exists():
        raise ScanError(f"未找到数据库文件：{db}\n请确认 Zcode 已安装且至少启动过一次。")
    try:
        con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True, timeout=5)
        con.execute("SELECT 1")
        return con
    except sqlite3.Error as e:
        raise ScanError(f"无法读取数据库 {db.name}：{e}") from e


def _table_has_column(cur: sqlite3.Cursor, table: str, column: str) -> bool:
    try:
        cols = [r[1] for r in cur.execute(f"PRAGMA table_info({table})").fetchall()]
        return column in cols
    except sqlite3.Error:
        return False


def scan_conversations() -> list[Conversation]:
    """扫描全部对话记录：桌面端索引 ∪ CLI 会话库。"""
    result: dict[str, Conversation] = {}

    # 1) 桌面端索引
    try:
        con = _open_ro(TASKS_DB)
    except ScanError as e:
        if CLI_DB.exists():
            con = None  # 桌面端索引缺失时降级，仅扫 CLI 库
        else:
            raise e
    if con is not None:
        try:
            cur = con.cursor()
            rows = cur.execute(
                "SELECT task_id, title, workspace_path, task_status, created_at, updated_at "
                "FROM tasks WHERE deleted = 0"
            ).fetchall()
            for tid, title, wpath, status, created, updated in rows:
                result[tid] = Conversation(
                    task_id=tid,
                    title=title or "(无标题对话)",
                    workspace=wpath or "—",
                    status=status or "",
                    created_at=created or 0,
                    updated_at=updated or created or 0,
                )
        except sqlite3.Error as e:
            raise ScanError(f"读取对话索引失败：{e}") from e
        finally:
            con.close()

    # 2) CLI 会话库（消息正文在这里）
    if CLI_DB.exists():
        try:
            con = _open_ro(CLI_DB)
            cur = con.cursor()
            counts = dict(
                cur.execute(
                    "SELECT session_id, COUNT(*) FROM message GROUP BY session_id"
                ).fetchall()
            )
            rows = cur.execute(
                "SELECT id, title, directory, time_created, time_updated FROM session"
            ).fetchall()
            for sid, title, directory, created, updated in rows:
                if sid in result:
                    c = result[sid]
                    c.message_count = counts.get(sid, 0)
                    if c.title.startswith("(无标题") and title:
                        c.title = title
                else:
                    result[sid] = Conversation(
                        task_id=sid,
                        title=title or "(无标题对话)",
                        workspace=directory or "—",
                        status="",
                        created_at=created or 0,
                        updated_at=updated or created or 0,
                        message_count=counts.get(sid, 0),
                        source="CLI",
                    )
            # 索引里有但 CLI 库没有的，也补消息数 0
            con.close()
        except sqlite3.Error as e:
            raise ScanError(f"读取会话数据库失败：{e}") from e

    # 若两者都无数据
    if not result:
        return []
    return sorted(result.values(), key=lambda c: c.updated_at, reverse=True)


# ---------------------------------------------------------------- 删除

def is_zcode_running() -> bool:
    """检测 Zcode 客户端进程是否正在运行。"""
    try:
        out = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq ZCode.exe"],
            capture_output=True, text=True, timeout=10,
            encoding="gbk", errors="ignore", creationflags=0x08000000,
        ).stdout.lower()
        return "zcode.exe" in out
    except Exception:
        return False


def _related_file_paths(task_id: str) -> list[Path]:
    """收集与该会话相关、文件名/目录名中包含会话 ID 的所有文件与目录。"""
    paths: list[Path] = []
    if not ZCODE_DIR.exists():
        return paths
    for p in ZCODE_DIR.rglob(f"*{task_id}*"):
        paths.append(p)
    return paths


def _remove_path(p: Path) -> tuple[str, int]:
    """删除文件或目录，返回 (相对说明, 释放字节数)。"""
    try:
        if p.is_dir():
            size = sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
            shutil.rmtree(p)
            return f"{p.name}/", size
        if p.is_file():
            size = p.stat().st_size
            p.unlink()
            return p.name, size
    except OSError as e:
        raise DeleteError(f"删除 {p} 失败：{e}") from e
    return p.name, 0


def _scrub_logs(task_id: str, root: Path, log: list[str]) -> int:
    """从应用日志中清除包含会话 ID 的行，返回清理的文件数。"""
    cleaned = 0
    log_dirs = [root / "v2" / "logs", root / "cli" / "log"]
    for d in log_dirs:
        if not d.is_dir():
            continue
        for f in d.iterdir():
            if not f.is_file() or f.suffix not in (".log", ".jsonl", ".txt"):
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
                if task_id not in text:
                    continue
                kept = [ln for ln in text.splitlines() if task_id not in ln]
                f.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
                cleaned += 1
                log.append(f"已清理日志: {f.name}")
            except OSError:
                pass
    return cleaned


def delete_conversation(task_id: str, make_backup: bool = True) -> dict:
    """
    彻底删除一条对话：
      1. 备份（可选）
      2. 清除 CLI 会话库（session 及所有 session_id 关联表）+ VACUUM
      3. 清除桌面端索引（tasks 及关联表）+ VACUUM
      4. 删除 rollout / artifacts / exec / image-cache 等关联文件
      5. 清理应用日志中的会话记录
    返回删除报告 dict；失败抛 DeleteError。
    """
    report = {"task_id": task_id, "rows": 0, "files": [], "bytes": 0, "logs": []}
    now = time.strftime("%Y%m%d_%H%M%S")
    backup_dir = BACKUP_ROOT / f"{now}_{task_id[:24]}"

    # ---------- 0) 备份 ----------
    if make_backup:
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            for db in (TASKS_DB, CLI_DB):
                if db.exists():
                    shutil.copy2(db, backup_dir / db.name)
                    for suffix in ("-wal", "-shm"):
                        side = Path(str(db) + suffix)
                        if side.exists():
                            shutil.copy2(side, backup_dir / (db.name + suffix))
            (backup_dir / "manifest.json").write_text(
                json.dumps({"task_id": task_id, "time": now}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            report["backup_dir"] = str(backup_dir)
        except OSError as e:
            raise DeleteError(f"创建备份失败，已中止删除：{e}") from e

    # ---------- 1) CLI 会话库 ----------
    if CLI_DB.exists():
        try:
            con = sqlite3.connect(str(CLI_DB), timeout=8)
            con.execute("PRAGMA foreign_keys=ON")
            cur = con.cursor()
            tables = [
                r[0]
                for r in cur.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            ]
            in_transaction = False
            try:
                con.execute("BEGIN")
                in_transaction = True
                # 所有含 session_id 的子表
                for t in tables:
                    if t != "session" and _table_has_column(cur, t, "session_id"):
                        n = cur.execute(
                            f"DELETE FROM {t} WHERE session_id = ?", (task_id,)
                        ).rowcount
                        report["rows"] += max(n, 0)
                # 会话主表
                n = cur.execute(
                    "DELETE FROM session WHERE id = ?", (task_id,)
                ).rowcount
                report["rows"] += max(n, 0)
                con.execute("COMMIT")
                in_transaction = False
            except sqlite3.Error:
                if in_transaction:
                    con.execute("ROLLBACK")
                raise
            # 消除残留：WAL 收缩 + VACUUM
            try:
                cur.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                cur.execute("VACUUM")
            except sqlite3.Error:
                pass
            con.close()
        except sqlite3.Error as e:
            msg = str(e)
            if "locked" in msg or "busy" in msg:
                raise DeleteError(
                    "会话数据库被占用（Zcode 可能正在运行）。\n请完全退出 Zcode 客户端后重试。"
                ) from e
            raise DeleteError(f"清除会话数据失败：{e}") from e

    # ---------- 2) 桌面端索引 ----------
    if TASKS_DB.exists():
        try:
            con = sqlite3.connect(str(TASKS_DB), timeout=8)
            cur = con.cursor()
            tables = [
                r[0]
                for r in cur.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            ]
            con.execute("BEGIN")
            for t in tables:
                if _table_has_column(cur, t, "task_id"):
                    n = cur.execute(
                        f"DELETE FROM {t} WHERE task_id = ?", (task_id,)
                    ).rowcount
                    report["rows"] += max(n, 0)
                if _table_has_column(cur, t, "session_id") and "task_id" not in [
                    r[1] for r in cur.execute(f"PRAGMA table_info({t})").fetchall()
                ]:
                    n = cur.execute(
                        f"DELETE FROM {t} WHERE session_id = ?", (task_id,)
                    ).rowcount
                    report["rows"] += max(n, 0)
                # 分组视图节点
                if _table_has_column(cur, t, "node_key"):
                    n = cur.execute(
                        f"DELETE FROM {t} WHERE node_key LIKE '%' || ? || '%'", (task_id,)
                    ).rowcount
                    report["rows"] += max(n, 0)
            con.execute("COMMIT")
            try:
                cur.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                cur.execute("VACUUM")
            except sqlite3.Error:
                pass
            con.close()
        except sqlite3.Error as e:
            msg = str(e)
            if "locked" in msg or "busy" in msg:
                raise DeleteError(
                    "索引数据库被占用（Zcode 可能正在运行）。\n请完全退出 Zcode 客户端后重试。"
                ) from e
            raise DeleteError(f"清除桌面端索引失败：{e}") from e

    # ---------- 3) 关联文件 ----------
    if ZCODE_DIR.exists():
        for p in _related_file_paths(task_id):
            name, size = _remove_path(p)
            report["files"].append(name)
            report["bytes"] += size

    # ---------- 4) 日志清洗 ----------
    _scrub_logs(task_id, ZCODE_DIR, report["logs"])

    report["bytes"] = round(report["bytes"] / 1024, 1)  # KB
    return report


def list_backups() -> list[Path]:
    if not BACKUP_ROOT.exists():
        return []
    return sorted(BACKUP_ROOT.iterdir(), reverse=True)
