# -*- coding: utf-8 -*-
"""GUI 离屏自测：主窗口构建、扫描渲染、主题切换、选择逻辑、各对话框实例化。"""

import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from PySide6.QtWidgets import QApplication

import zcode_data as zd
import main as m

app = QApplication([])
win = m.MainWindow()
win.apply_theme("light")
convs = zd.scan_conversations()
win._on_scan_done(convs)
assert win.stat_convs.text() == str(len(convs)), "统计卡片未更新"
assert win.list.count() == len(convs), "列表行数不正确"
print("[PASS] 主窗口 + 扫描渲染：", win.list.count(), "行")

# 主题循环
win.cycle_theme(); assert win.theme_key == "dark" and "dark" in win.theme["name"]
win.cycle_theme(); assert win.theme_key == "auto"
win.cycle_theme(); assert win.theme_key == "light"
assert win.title_bar.theme_btn.text() == "☀️"
print("[PASS] 主题切换：light → dark → auto → light")

# 选择逻辑
if convs:
    c = convs[0]
    win._toggle_select(c.task_id, True)
    assert c.task_id in win.selected
    win._update_sel_bar()
    assert not win.sel_bar.isHidden() and win.batch_btn.isEnabled()
    win._toggle_select(c.task_id, False)
    assert win.sel_bar.isHidden()
    win._clear_selection()
    print("[PASS] 勾选/取消选择栏")

    # 预览对话框（强制渲染假数据）
    dlg = m.PreviewDialog(c, win.theme, win)
    dlg._render([{"role": "user", "time": 1000, "text": "你好"},
                 {"role": "assistant", "time": 2000, "text": "回复 <b>内容</b>"}])
    assert dlg.area_lay.count() >= 2, "气泡未渲染"
    dlg.close()
    print("[PASS] 预览对话框气泡渲染")

# 恢复 / 确认对话框实例化
rd = m.RestoreDialog(win._do_restore, win)
rd._reload()
assert rd.list_box.count() >= 0
rd.close()
cd = m.ConfirmDialog("删除测试", ["条目A", "条目B"], "确认删除", None, "说明", win)
assert cd.windowTitle() == "确认操作"
cd.close()
print("[PASS] 恢复/确认对话框构建")

win.close()
print("\nGUI 离屏自测通过 ✅")
