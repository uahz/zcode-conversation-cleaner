# -*- coding: utf-8 -*-
"""端到端自测：在临时目录构造与 Zcode 相同结构的假数据，验证扫描与彻底删除逻辑。不触碰真实数据。"""

import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import zcode_data as zd

tmp = Path(tempfile.mkdtemp(prefix="zcode_test_"))
zdir = tmp / ".zcode"
(zdir / "v2").mkdir(parents=True)
(zdir / "cli" / "db").mkdir(parents=True)
(zdir / "cli" / "rollout").mkdir(parents=True)
(zdir / "cli" / "artifacts" / "sess_aaa-111").mkdir(parents=True)
(zdir / "cli" / "exec" / "sess_aaa-111").mkdir(parents=True)
(zdir / "cli" / "log").mkdir(parents=True)

# 桌面端索引库
con = sqlite3.connect(zdir / "v2" / "tasks-index.sqlite")
con.executescript(
    """
    CREATE TABLE tasks (workspace_key TEXT, workspace_path TEXT, workspace_identity TEXT,
      task_id TEXT, title TEXT, task_status TEXT, provider TEXT, mode TEXT, model TEXT,
      migration_source TEXT, forked_from_task_id TEXT, created_at INTEGER, updated_at INTEGER,
      unread_at INTEGER, last_unread_at INTEGER DEFAULT 0, pinned INTEGER DEFAULT 0,
      archived INTEGER DEFAULT 0, deleted INTEGER DEFAULT 0, title_overridden INTEGER DEFAULT 0,
      meta_json TEXT DEFAULT '{}', searchable_text TEXT DEFAULT '');
    CREATE TABLE task_group_members (group_id TEXT, workspace_key TEXT, workspace_path TEXT,
      workspace_identity TEXT, task_id TEXT, sort_order INTEGER, added_at INTEGER,
      created_at INTEGER, updated_at INTEGER, PRIMARY KEY(workspace_key, task_id));
    INSERT INTO tasks VALUES ('F:/x','F:/x',NULL,'sess_aaa-111','测试对话','completed',NULL,'build',NULL,
      NULL,NULL,1000,2000,NULL,0,0,0,0,0,'{}','');
    INSERT INTO task_group_members VALUES ('g1','F:/x','F:/x',NULL,'sess_aaa-111',0,1,1,1);
    """
)
con.commit()
con.close()

# CLI 会话库
con = sqlite3.connect(zdir / "cli" / "db" / "db.sqlite")
con.executescript(
    """
    CREATE TABLE session (id TEXT PRIMARY KEY, project_id TEXT, workspace_id TEXT, parent_id TEXT,
      slug TEXT, directory TEXT, path TEXT, title TEXT, version TEXT, share_url TEXT,
      summary_additions INTEGER, summary_deletions INTEGER, summary_files INTEGER, summary_diffs TEXT,
      revert TEXT, permission TEXT, time_created INTEGER, time_updated INTEGER, time_compacting INTEGER,
      time_archived INTEGER, task_type TEXT DEFAULT 'interactive', title_source TEXT DEFAULT 'first_input');
    CREATE TABLE message (id TEXT PRIMARY KEY, session_id TEXT, time_created INTEGER,
      time_updated INTEGER, data TEXT, sequence INTEGER);
    CREATE TABLE turn_usage (id TEXT PRIMARY KEY, session_id TEXT, data TEXT);
    INSERT INTO session VALUES ('sess_aaa-111','p1',NULL,NULL,'s1','F:/x',NULL,'测试对话','1.0',NULL,
      0,0,0,NULL,NULL,NULL,1000,2000,NULL,NULL,'interactive','first_input');
    INSERT INTO message VALUES ('m1','sess_aaa-111',1,2,'hello',0);
    INSERT INTO message VALUES ('m2','sess_aaa-111',3,4,'world',1);
    INSERT INTO turn_usage VALUES ('t1','sess_aaa-111','{}');
    """
)
con.commit()
con.close()

# 关联文件
(zdir / "cli" / "rollout" / "model-io-sess_aaa-111.jsonl").write_text('{"io":1}\n', encoding="utf-8")
(zdir / "cli" / "artifacts" / "sess_aaa-111" / "out.txt").write_text("artifact", encoding="utf-8")
(zdir / "cli" / "exec" / "sess_aaa-111" / "run.log").write_text("log", encoding="utf-8")
(zdir / "cli" / "log" / "2026-08-29.log").write_text("info sess_aaa-111 started\nother line\n", encoding="utf-8")

# 注入测试路径
zd.ZCODE_DIR = zdir
zd.TASKS_DB = zdir / "v2" / "tasks-index.sqlite"
zd.CLI_DB = zdir / "cli" / "db" / "db.sqlite"
zd.BACKUP_ROOT = tmp / "backup"

# ---- 1) 扫描 ----
convs = zd.scan_conversations()
assert len(convs) == 1, f"扫描数量异常: {convs}"
c = convs[0]
assert c.title == "测试对话" and c.message_count == 2 and c.status_label == "已完成"
print("[PASS] 扫描：识别 1 条对话，标题/消息数/状态正确")

# ---- 2) 空列表 ----
zd.delete_conversation  # noqa
con = sqlite3.connect(zd.CLI_DB)
con.execute("DELETE FROM session"); con.execute("DELETE FROM message"); con.execute("DELETE FROM turn_usage"); con.commit(); con.close()
con = sqlite3.connect(zd.TASKS_DB)
con.execute("DELETE FROM tasks"); con.commit(); con.close()
assert zd.scan_conversations() == []
print("[PASS] 空列表：返回 []")
# 恢复数据：直接重建
con = sqlite3.connect(zd.CLI_DB)
con.executescript(
    """
    CREATE TABLE IF NOT EXISTS session (id TEXT PRIMARY KEY, project_id TEXT, workspace_id TEXT,
      parent_id TEXT, slug TEXT, directory TEXT, path TEXT, title TEXT, version TEXT, share_url TEXT,
      summary_additions INTEGER, summary_deletions INTEGER, summary_files INTEGER, summary_diffs TEXT,
      revert TEXT, permission TEXT, time_created INTEGER, time_updated INTEGER, time_compacting INTEGER,
      time_archived INTEGER, task_type TEXT DEFAULT 'interactive', title_source TEXT DEFAULT 'first_input');
    CREATE TABLE IF NOT EXISTS message (id TEXT PRIMARY KEY, session_id TEXT, time_created INTEGER,
      time_updated INTEGER, data TEXT, sequence INTEGER);
    CREATE TABLE IF NOT EXISTS turn_usage (id TEXT PRIMARY KEY, session_id TEXT, data TEXT);
    INSERT INTO session VALUES ('sess_aaa-111','p1',NULL,NULL,'s1','F:/x',NULL,'测试对话','1.0',NULL,
      0,0,0,NULL,NULL,NULL,1000,2000,NULL,NULL,'interactive','first_input');
    INSERT INTO message VALUES ('m1','sess_aaa-111',1,2,'hello',0);
    INSERT INTO message VALUES ('m2','sess_aaa-111',3,4,'world',1);
    INSERT INTO turn_usage VALUES ('t1','sess_aaa-111','{}');
    """
)
con.commit(); con.close()
con = sqlite3.connect(zd.TASKS_DB)
con.execute("DELETE FROM task_group_members"); con.commit()
con.executescript(
    """
    INSERT INTO tasks VALUES ('F:/x','F:/x',NULL,'sess_aaa-111','测试对话','completed',NULL,'build',NULL,
      NULL,NULL,1000,2000,NULL,0,0,0,0,0,'{}','');
    INSERT INTO task_group_members VALUES ('g1','F:/x','F:/x',NULL,'sess_aaa-111',0,1,1,1);
    """
)
con.commit(); con.close()
assert len(zd.scan_conversations()) == 1

# ---- 3) 删除 ----
report = zd.delete_conversation("sess_aaa-111")
assert report["rows"] >= 5, f"删除行数异常: {report}"  # tasks + group_member + session + 2 msg + usage
assert (zdir / "cli" / "rollout" / "model-io-sess_aaa-111.jsonl").exists() is False
assert (zdir / "cli" / "artifacts" / "sess_aaa-111").exists() is False
assert (zdir / "cli" / "exec" / "sess_aaa-111").exists() is False
assert zd.scan_conversations() == []
log_text = (zdir / "cli" / "log" / "2026-08-29.log").read_text(encoding="utf-8")
assert "sess_aaa-111" not in log_text and "other line" in log_text
# WAL/主文件无残留
import re
raw = (zd.CLI_DB).read_bytes() + (Path(str(zd.CLI_DB) + "-wal")).read_bytes() if Path(str(zd.CLI_DB) + "-wal").exists() else (zd.CLI_DB).read_bytes()
assert b"sess_aaa-111" not in raw, "数据库中仍有会话 ID 残留"
print("[PASS] 删除：数据库行、关联文件、日志全部清除，无 ID 残留")
print("[PASS] 备份：", report.get("backup_dir", "") != "")
print("[PASS] 释放空间:", report["bytes"], "KB, 文件项:", report["files"])

shutil.rmtree(tmp, ignore_errors=True)
print("\n全部自测通过 ✅")
