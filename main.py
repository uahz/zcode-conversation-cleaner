# -*- coding: utf-8 -*-
"""
Zcode 对话删除程序 v2.0 —— GUI
Apple 设计语言：无边框圆角窗口 / 红绿灯 / 双主题 / 内容预览 / 批量删除 / 恢复备份
"""

from __future__ import annotations

import html
import sys
import time
from pathlib import Path

from PySide6.QtCore import (
    Qt, QThread, Signal, QSize, QTimer, QPoint,
    QPropertyAnimation, QEasingCurve,
)
from PySide6.QtGui import QColor, QFontMetrics, QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QListWidget, QListWidgetItem, QFrame, QDialog,
    QGraphicsOpacityEffect, QGraphicsDropShadowEffect, QAbstractItemView,
    QCheckBox, QScrollArea, QSizePolicy,
)

import zcode_data as zd

# ================================================================ 主题

LIGHT = dict(
    name="light", BG="#F5F5F7", CARD="#FFFFFF", TEXT="#1D1D1F", TEXT2="#86868B",
    BLUE="#0071E3", BLUE_H="#0077ED", RED="#FF3B30", RED_DARK="#D70015",
    GREEN="#34C759", ORANGE="#FF9500", HAIRLINE="rgba(0,0,0,0.08)",
    ITEM_HOVER_BORDER="rgba(0,113,227,0.35)", ITEM_HOVER_BG="#FBFDFF",
    SCROLL="rgba(0,0,0,0.16)", SCROLL_H="rgba(0,0,0,0.28)",
    TOAST_BG="rgba(29,29,31,0.90)", TOAST_FG="#FFFFFF",
    BANNER_BG="rgba(255,59,48,0.10)", BANNER_FG="#D70015",
    WARN_BG="rgba(255,149,0,0.12)", WARN_FG="#B25000",
    DEL_BG="rgba(255,59,48,0.09)", SECONDARY_H="#EDEDF0",
    BUBBLE_ASSIST="#F0F0F2", TL_HOVER="rgba(0,0,0,0.20)",
)

DARK = dict(
    name="dark", BG="#1C1C1E", CARD="#2C2C2E", TEXT="#F2F2F7", TEXT2="#98989E",
    BLUE="#0A84FF", BLUE_H="#409CFF", RED="#FF453A", RED_DARK="#FF6961",
    GREEN="#30D158", ORANGE="#FF9F0A", HAIRLINE="rgba(255,255,255,0.10)",
    ITEM_HOVER_BORDER="rgba(10,132,255,0.55)", ITEM_HOVER_BG="#333336",
    SCROLL="rgba(255,255,255,0.22)", SCROLL_H="rgba(255,255,255,0.35)",
    TOAST_BG="rgba(242,242,247,0.92)", TOAST_FG="#1C1C1E",
    BANNER_BG="rgba(255,69,58,0.16)", BANNER_FG="#FF6961",
    WARN_BG="rgba(255,159,10,0.16)", WARN_FG="#FFB340",
    DEL_BG="rgba(255,69,58,0.16)", SECONDARY_H="#3A3A3C",
    BUBBLE_ASSIST="#3A3A3C", TL_HOVER="rgba(255,255,255,0.25)",
)

TL_RED, TL_YELLOW, TL_GREEN = "#FF5F57", "#FEBC2E", "#28C840"
SHELL_RADIUS, SHELL_MARGIN = 12, 14

AVATAR_GRADS = [
    ("#5AC8FA", "#0071E3"), ("#FF9A8B", "#FF3B30"), ("#A8E063", "#34C759"),
    ("#F6D365", "#FDA085"), ("#B39DDB", "#7E57C2"), ("#80DEEA", "#26A69A"),
    ("#FBC2EB", "#A18CD1"), ("#FDCB6E", "#E17055"),
]

STATUS_COLOR = {
    "已完成": "GREEN", "进行中": "BLUE", "排队中": "ORANGE",
    "已出错": "RED", "已取消": "TEXT2", "已停止": "TEXT2", "未知": "TEXT2",
}

THEME_ICONS = {"light": "☀️", "dark": "🌙", "auto": "🖥️"}
THEME_TIPS = {"light": "切换为深色模式", "dark": "切换为跟随系统",
              "auto": "切换为浅色模式"}


def build_qss(t: dict) -> str:
    return f"""
* {{
    font-family: "PingFang SC", "SF Pro Text", "Microsoft YaHei UI", "Segoe UI", sans-serif;
    outline: none;
}}
QMainWindow, QWidget#root {{ background: transparent; }}
QFrame#shell {{ background: {t['BG']}; border-radius: {SHELL_RADIUS}px; }}
QLabel {{ color: {t['TEXT']}; }}

QPushButton.traffic {{
    border: none; border-radius: 7px; min-width: 14px; max-width: 14px;
    min-height: 14px; max-height: 14px; padding: 0;
    font-size: 9px; font-weight: 700; color: rgba(0,0,0,0.55);
}}
QPushButton.traffic:hover {{ border: 1px solid {t['TL_HOVER']}; }}

QLabel#winTitle {{ font-size: 13px; font-weight: 600; color: {t['TEXT2']}; letter-spacing: 0.3px; }}
QPushButton#theme {{
    background: transparent; border: none; border-radius: 8px;
    min-width: 26px; max-width: 26px; min-height: 24px; max-height: 24px;
    font-size: 13px;
}}
QPushButton#theme:hover {{ background: {t['CARD']}; }}

QLabel#title {{ font-size: 26px; font-weight: 700; letter-spacing: 0.2px; }}
QLabel#subtitle {{ font-size: 13px; color: {t['TEXT2']}; }}

QFrame#stat {{
    background: {t['CARD']}; border: 1px solid {t['HAIRLINE']}; border-radius: 13px;
}}
QLabel#statNum {{ font-size: 19px; font-weight: 700; }}
QLabel#statLabel {{ font-size: 11px; color: {t['TEXT2']}; }}

QLineEdit#search {{
    background: {t['CARD']}; border: 1px solid {t['HAIRLINE']}; border-radius: 11px;
    padding: 9px 14px 9px 34px; font-size: 13px; color: {t['TEXT']};
    selection-background-color: {t['BLUE']};
}}
QLineEdit#search:focus {{ border: 1px solid {t['BLUE']}; }}

QFrame#card {{
    background: {t['CARD']}; border-radius: 16px; border: 1px solid {t['HAIRLINE']};
}}

QListWidget#list {{ background: transparent; border: none; outline: none; }}
QListWidget#list::item {{ margin: 0px 2px 10px 2px; }}
QListWidget#list::item:selected {{ background: transparent; }}

QScrollBar:vertical {{ background: transparent; width: 8px; margin: 6px 2px 6px 0px; }}
QScrollBar::handle:vertical {{
    background: {t['SCROLL']}; border-radius: 4px; min-height: 32px;
}}
QScrollBar::handle:vertical:hover {{ background: {t['SCROLL_H']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}

QFrame#item {{
    background: {t['CARD']}; border: 1px solid {t['HAIRLINE']}; border-radius: 14px;
}}
QFrame#item:hover {{ border: 1px solid {t['ITEM_HOVER_BORDER']}; background: {t['ITEM_HOVER_BG']}; }}
QFrame#itemSelected {{
    background: {t['ITEM_HOVER_BG']}; border: 1px solid {t['BLUE']}; border-radius: 14px;
}}

QCheckBox {{
    spacing: 6px; color: {t['TEXT2']}; font-size: 12px;
}}
QCheckBox::indicator {{
    width: 16px; height: 16px; border-radius: 5px;
    border: 1.5px solid {t['TEXT2']}; background: transparent;
}}
QCheckBox::indicator:hover {{ border-color: {t['BLUE']}; }}
QCheckBox::indicator:checked {{
    background: {t['BLUE']}; border-color: {t['BLUE']};
    image: none;
}}

QLabel#avatar {{
    border-radius: 19px; min-width: 38px; max-width: 38px;
    min-height: 38px; max-height: 38px;
    font-size: 15px; font-weight: 700; color: white; border: none;
}}
QLabel#itemTitle {{ font-size: 14px; font-weight: 600; color: {t['TEXT']}; }}
QLabel#itemMeta {{ font-size: 12px; color: {t['TEXT2']}; }}

QPushButton#del {{
    background: {t['DEL_BG']}; color: {t['RED']}; border: none;
    border-radius: 10px; padding: 8px 0px; font-size: 12px; font-weight: 600;
    min-width: 56px; max-width: 56px;
}}
QPushButton#del:hover {{ background: {t['RED']}; color: white; }}
QPushButton#del:pressed {{ background: {t['RED_DARK']}; }}

QPushButton#preview {{
    background: transparent; color: {t['BLUE']}; border: none;
    border-radius: 10px; padding: 8px 0px; font-size: 12px; font-weight: 600;
    min-width: 52px; max-width: 52px;
}}
QPushButton#preview:hover {{ background: {t['BLUE']}22; }}

QPushButton#primary {{
    background: {t['BLUE']}; color: white; border: none; border-radius: 11px;
    padding: 10px 20px; font-size: 13px; font-weight: 600;
}}
QPushButton#primary:hover {{ background: {t['BLUE_H']}; }}
QPushButton#primary:pressed {{ background: {t['BLUE']}; }}
QPushButton#primary:disabled {{ background: {t['TEXT2']}55; }}

QPushButton#secondary {{
    background: {t['CARD']}; color: {t['TEXT']}; border: 1px solid {t['HAIRLINE']};
    border-radius: 11px; padding: 9px 16px; font-size: 12.5px; font-weight: 500;
}}
QPushButton#secondary:hover {{ background: {t['SECONDARY_H']}; }}

QPushButton#danger {{
    background: {t['RED']}; color: white; border: none; border-radius: 11px;
    padding: 10px 26px; font-size: 13px; font-weight: 600;
}}
QPushButton#danger:hover {{ background: {t['RED_DARK']}; }}
QPushButton#danger:disabled {{ background: {t['TEXT2']}55; }}

QPushButton#ghost {{
    background: transparent; color: {t['BLUE']}; border: none;
    padding: 9px 12px; font-size: 13px; font-weight: 500;
}}
QPushButton#ghost:hover {{ color: {t['BLUE_H']}; }}

QDialog#dlg {{ background: {t['BG']}; }}
QLabel#dlgTitle {{ font-size: 18px; font-weight: 700; }}
QLabel#dlgBody {{ font-size: 13px; color: {t['TEXT2']}; }}
QLabel#dlgName {{
    background: {t['CARD']}; border: 1px solid {t['HAIRLINE']}; border-radius: 10px;
    padding: 9px 12px; font-size: 13px; font-weight: 600; color: {t['TEXT']};
}}
QLabel#warn {{
    background: {t['WARN_BG']}; color: {t['WARN_FG']}; border-radius: 10px;
    padding: 10px 12px; font-size: 12px;
}}
QPushButton#cancel {{
    background: {t['CARD']}; color: {t['TEXT']}; border: 1px solid {t['HAIRLINE']};
    border-radius: 11px; padding: 10px 26px; font-size: 13px; font-weight: 500;
}}
QPushButton#cancel:hover {{ background: {t['SECONDARY_H']}; }}

QLabel#toast {{
    background: {t['TOAST_BG']}; color: {t['TOAST_FG']}; border-radius: 13px;
    padding: 11px 22px; font-size: 13px; font-weight: 500;
}}
QLabel#emptyTitle {{ font-size: 17px; font-weight: 600; color: {t['TEXT']}; }}
QLabel#emptyBody {{ font-size: 13px; color: {t['TEXT2']}; }}
QLabel#banner {{
    background: {t['BANNER_BG']}; color: {t['BANNER_FG']}; border-radius: 11px;
    padding: 11px 14px; font-size: 12.5px; font-weight: 500;
}}
QLabel#bigEmoji {{ font-size: 46px; }}
QLabel#foot {{ font-size: 11.5px; color: {t['TEXT2']}; }}
QLabel#selBar {{
    background: {t['CARD']}; border: 1px solid {t['HAIRLINE']}; border-radius: 12px;
    padding: 8px 16px; font-size: 12.5px; color: {t['TEXT']}; font-weight: 500;
}}
QLabel#previewTitle {{ font-size: 15px; font-weight: 600; }}
QLabel#previewTime {{ font-size: 11px; color: {t['TEXT2']}; }}
QLabel#bubble {{
    font-size: 13px; line-height: 150%; padding: 10px 14px; border-radius: 14px;
}}
QLabel#restoreRow {{ font-size: 12.5px; color: {t['TEXT']}; }}
"""


def shadow(widget: QWidget, blur=28, y=6, alpha=36):
    eff = QGraphicsDropShadowEffect(widget)
    eff.setBlurRadius(blur)
    eff.setOffset(0, y)
    eff.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(eff)
    return eff


# ================================================================ 后台线程

class ScanWorker(QThread):
    done = Signal(list)
    failed = Signal(str)

    def run(self):
        try:
            self.done.emit(zd.scan_conversations())
        except zd.ScanError as e:
            self.failed.emit(str(e))
        except Exception as e:
            self.failed.emit(f"扫描时发生意外错误：{e}")


class DeleteWorker(QThread):
    done = Signal(dict)
    failed = Signal(str)

    def __init__(self, task_id: str):
        super().__init__()
        self.task_id = task_id

    def run(self):
        try:
            self.done.emit(zd.delete_conversation(self.task_id))
        except zd.DeleteError as e:
            self.failed.emit(str(e))
        except Exception as e:
            self.failed.emit(f"删除时发生意外错误：{e}")


class BatchDeleteWorker(QThread):
    done = Signal(list)

    def __init__(self, task_ids: list[str]):
        super().__init__()
        self.task_ids = task_ids

    def run(self):
        self.done.emit(zd.delete_conversations(self.task_ids))


class MessagesWorker(QThread):
    done = Signal(list)

    def __init__(self, task_id: str):
        super().__init__()
        self.task_id = task_id

    def run(self):
        self.done.emit(zd.get_messages(self.task_id))


class RestoreWorker(QThread):
    done = Signal(dict)
    failed = Signal(str)

    def __init__(self, backup_dir: str):
        super().__init__()
        self.backup_dir = backup_dir

    def run(self):
        try:
            self.done.emit(zd.restore_backup(Path(self.backup_dir)))
        except zd.DeleteError as e:
            self.failed.emit(str(e))
        except Exception as e:
            self.failed.emit(f"恢复时发生意外错误：{e}")


# ================================================================ 红绿灯

class TrafficLight(QPushButton):
    def __init__(self, color: str, symbol: str, tip: str, callback):
        super().__init__()
        self._color = color
        self._symbol = symbol
        self.setProperty("class", "traffic")
        self.setFixedSize(14, 14)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(tip)
        self.setStyleSheet(f"QPushButton.traffic {{ background: {color}; }}")
        self.clicked.connect(callback)

    def enterEvent(self, e):
        self.setText(self._symbol)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self.setText("")
        super().leaveEvent(e)


# ================================================================ 列表条目

class ConvItem(QFrame):
    def __init__(self, conv: zd.Conversation, index: int,
                 on_toggle, on_preview, on_delete, selected: bool):
        super().__init__()
        self.conv = conv
        self.setObjectName("itemSelected" if selected else "item")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 12, 10, 12)
        lay.setSpacing(12)

        self.check = QCheckBox()
        self.check.setChecked(selected)
        self.check.setCursor(Qt.PointingHandCursor)
        self.check.toggled.connect(lambda on: on_toggle(conv.task_id, on))
        lay.addWidget(self.check, 0, Qt.AlignVCenter)

        c1, c2 = AVATAR_GRADS[index % len(AVATAR_GRADS)]
        av = QLabel(conv.title.strip()[:1] or "·")
        av.setObjectName("avatar")
        av.setAlignment(Qt.AlignCenter)
        av.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            f"stop:0 {c1}, stop:1 {c2});"
        )
        lay.addWidget(av, 0, Qt.AlignVCenter)

        mid = QVBoxLayout()
        mid.setSpacing(4)
        title = QLabel()
        title.setObjectName("itemTitle")
        title.setWordWrap(False)
        fm = QFontMetrics(title.font())
        title.setText(fm.elidedText(conv.title.replace("\n", " "), Qt.ElideRight, 330))
        title.setToolTip(conv.title)
        title.setFixedWidth(330)

        meta_bits = [conv.workspace, f"更新于 {conv.updated_text}"]
        if conv.message_count:
            meta_bits.append(f"{conv.message_count} 条消息")
        if conv.size:
            meta_bits.append(f"占用 {conv.size_text}")
        meta_bits.append(conv.source)
        meta = QLabel("  ·  ".join(meta_bits))
        meta.setObjectName("itemMeta")

        mid.addWidget(title)
        mid.addWidget(meta)
        lay.addLayout(mid, 0)
        lay.addStretch(1)

        color_key = STATUS_COLOR.get(conv.status_label, "TEXT2")
        color = {"GREEN": "GREEN", "BLUE": "BLUE", "ORANGE": "ORANGE",
                 "RED": "RED", "TEXT2": "TEXT2"}[color_key]
        col = {"GREEN": "#34C759", "BLUE": "#0071E3", "ORANGE": "#FF9500",
               "RED": "#FF3B30", "TEXT2": "#86868B"}[color]
        pill = QLabel(conv.status_label)
        pill.setStyleSheet(
            f"color: {col}; background: {col}1A; border-radius: 9px;"
            "font-size: 11px; font-weight: 600; padding: 3px 10px;"
        )
        lay.addWidget(pill, 0, Qt.AlignVCenter)

        prev = QPushButton("预览")
        prev.setObjectName("preview")
        prev.setCursor(Qt.PointingHandCursor)
        prev.clicked.connect(lambda: on_preview(conv))
        lay.addWidget(prev, 0, Qt.AlignVCenter)

        btn = QPushButton("删除")
        btn.setObjectName("del")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: on_delete(conv))
        lay.addWidget(btn, 0, Qt.AlignVCenter)


# ================================================================ 确认对话框

class ConfirmDialog(QDialog):
    def __init__(self, title: str, lines: list[str], danger_text: str,
                 warn_text: str | None, note: str, parent=None):
        super().__init__(parent)
        self.setObjectName("dlg")
        self.setWindowTitle("确认操作")
        self.setModal(True)
        self.setFixedSize(450, 330 + (40 if warn_text else 0))

        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 28, 30, 24)
        lay.setSpacing(12)

        emoji = QLabel("🗑️" if "删除" in danger_text else "♻️")
        emoji.setStyleSheet("font-size: 40px;")
        emoji.setAlignment(Qt.AlignCenter)
        lay.addWidget(emoji)

        t = QLabel(title)
        t.setObjectName("dlgTitle")
        t.setAlignment(Qt.AlignCenter)
        lay.addWidget(t)

        name = QLabel()
        name.setObjectName("dlgName")
        fm = QFontMetrics(name.font())
        text = "\n".join(lines[:3])
        name.setText(fm.elidedText(text, Qt.ElideMiddle, 360))
        name.setAlignment(Qt.AlignCenter)
        if len(lines) > 3:
            name.setText(name.text() + f"\n… 等 {len(lines)} 条")
        name.setWordWrap(True)
        lay.addWidget(name)

        b = QLabel("该操作将永久删除以上对话的消息记录、会话数据、\n执行产物及全部关联文件，不可撤销。"
                   if "删除" in danger_text else "将把备份中的数据库恢复到原位置，当前数据会被覆盖。")
        b.setObjectName("dlgBody")
        b.setAlignment(Qt.AlignCenter)
        lay.addWidget(b)

        if warn_text:
            warn = QLabel(warn_text)
            warn.setObjectName("warn")
            warn.setAlignment(Qt.AlignCenter)
            lay.addWidget(warn)

        note_l = QLabel(note)
        note_l.setObjectName("dlgBody")
        note_l.setAlignment(Qt.AlignCenter)
        lay.addWidget(note_l)

        lay.addStretch(1)
        btns = QHBoxLayout()
        btns.setSpacing(10)
        cancel = QPushButton("取消")
        cancel.setObjectName("cancel")
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        ok = QPushButton(danger_text)
        ok.setObjectName("danger")
        ok.setCursor(Qt.PointingHandCursor)
        ok.clicked.connect(self.accept)
        btns.addWidget(cancel)
        btns.addWidget(ok)
        lay.addLayout(btns)


# ================================================================ 消息预览

class PreviewDialog(QDialog):
    def __init__(self, conv: zd.Conversation, theme: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("dlg")
        self.setWindowTitle("对话内容预览")
        self.setModal(True)
        self.resize(760, 600)
        self.theme = theme

        v = QVBoxLayout(self)
        v.setContentsMargins(26, 22, 26, 20)
        v.setSpacing(12)

        head = QHBoxLayout()
        t = QLabel()
        t.setObjectName("previewTitle")
        fm = QFontMetrics(t.font())
        t.setText(fm.elidedText(conv.title, Qt.ElideMiddle, 520))
        t.setToolTip(conv.title)
        head.addWidget(t)
        head.addStretch(1)
        close = QPushButton("关闭")
        close.setObjectName("secondary")
        close.setCursor(Qt.PointingHandCursor)
        close.clicked.connect(self.accept)
        head.addWidget(close)
        v.addLayout(head)

        self.status = QLabel("正在加载消息…")
        self.status.setObjectName("dlgBody")
        self.status.setAlignment(Qt.AlignCenter)
        v.addWidget(self.status)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet(
            f"QScrollArea {{ background: {self.theme['BG']}; border: none; }}"
            f"QWidget#bubbleArea {{ background: {self.theme['BG']}; }}"
        )
        self.area = QWidget()
        self.area.setObjectName("bubbleArea")
        self.area_lay = QVBoxLayout(self.area)
        self.area_lay.setContentsMargins(6, 6, 10, 6)
        self.area_lay.setSpacing(10)
        self.area_lay.addStretch(1)
        self.scroll.setWidget(self.area)
        v.addWidget(self.scroll, 1)

        self.worker = MessagesWorker(conv.task_id)
        self.worker.done.connect(self._render)
        self.worker.start()

    def _render(self, messages: list[dict]):
        # 清空（移除 stretch 与旧气泡）
        while self.area_lay.count():
            item = self.area_lay.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        if not messages:
            self.status.setText("该对话没有可预览的文本消息")
            self.area_lay.addStretch(1)
            return
        self.status.hide()
        for m in messages:
            self._add_bubble(m)
        self.area_lay.addStretch(1)
        QTimer.singleShot(30, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()))

    def _add_bubble(self, m: dict):
        if m["role"] == "user":
            bg, fg, align = self.theme["BLUE"], "#FFFFFF", Qt.AlignRight
        else:
            bg, fg, align = self.theme["BUBBLE_ASSIST"], self.theme["TEXT"], Qt.AlignLeft

        row = QHBoxLayout()
        bubble = QLabel(
            f"<div style='background:{bg};color:{fg};border-radius:14px;"
            f"padding:10px 14px;font-size:13px;line-height:1.55;max-width:540px;'>"
            f"{html.escape(m['text'])}</div>"
        )
        bubble.setObjectName("bubble")
        bubble.setTextFormat(Qt.RichText)
        bubble.setWordWrap(True)
        bubble.setTextInteractionFlags(Qt.TextSelectableByMouse)
        bubble.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        if align == Qt.AlignRight:
            row.addStretch(1)
            row.addWidget(bubble)
        else:
            row.addWidget(bubble)
            row.addStretch(1)
        try:
            ts = time.strftime("%H:%M", time.localtime(m["time"] / 1000))
        except Exception:
            ts = ""
        if ts:
            tl = QLabel(ts)
            tl.setObjectName("previewTime")
            if align == Qt.AlignRight:
                row.addSpacing(6)
                row.addWidget(tl, 0, Qt.AlignBottom)
            else:
                row.addWidget(tl, 0, Qt.AlignBottom)
                row.addSpacing(6)
        wrap = QWidget()
        wrap.setLayout(row)
        self.area_lay.insertWidget(self.area_lay.count(), wrap)

    def closeEvent(self, e):
        try:
            if self.worker.isRunning():
                self.worker.wait(800)
        except Exception:
            pass
        super().closeEvent(e)


# ================================================================ 恢复备份

class RestoreDialog(QDialog):
    def __init__(self, on_restore, parent=None):
        super().__init__(parent)
        self.setObjectName("dlg")
        self.setWindowTitle("恢复备份")
        self.setModal(True)
        self.resize(680, 480)
        self.on_restore = on_restore
        self._busy = False

        v = QVBoxLayout(self)
        v.setContentsMargins(26, 22, 26, 20)
        v.setSpacing(12)

        head = QHBoxLayout()
        t = QLabel("从备份恢复对话")
        t.setObjectName("dlgTitle")
        head.addWidget(t)
        head.addStretch(1)
        close = QPushButton("关闭")
        close.setObjectName("secondary")
        close.setCursor(Qt.PointingHandCursor)
        close.clicked.connect(self.accept)
        head.addWidget(close)
        v.addLayout(head)

        note = QLabel("备份在每次删除前自动创建于 ~/.zcode-cleaner-backup。恢复会覆盖当前数据库，恢复前会自动再备份当前状态。")
        note.setObjectName("dlgBody")
        note.setWordWrap(True)
        v.addWidget(note)

        self.list_box = QVBoxLayout()
        v.addLayout(self.list_box)
        v.addStretch(1)

        self._reload()

    def _reload(self):
        while self.list_box.count():
            item = self.list_box.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        backups = zd.list_backups()
        if not backups:
            e = QLabel("暂无备份。执行过删除操作后，这里才会出现可恢复的备份。")
            e.setObjectName("dlgBody")
            e.setAlignment(Qt.AlignCenter)
            self.list_box.addWidget(e)
            return
        for b in backups:
            info = zd.backup_info(b)
            self._add_row(info)

    def _add_row(self, info: dict):
        row = QFrame()
        row.setStyleSheet(
            f"QFrame {{ background: transparent; border: 1px solid {HAIRLINE_PLACEHOLDER};"
            "border-radius: 12px; }" if False else
            "QFrame { background: transparent; border-radius: 0px; }"
        )
        h = QHBoxLayout(row)
        h.setContentsMargins(2, 4, 2, 4)
        h.setSpacing(10)
        dbs = "、".join(info["dbs"]) or "无数据库"
        label = QLabel(
            f"🕐 {info['time']}　·　会话 {info['task_id'][:24] or '未知'}\n"
            f"包含 {dbs}　·　约 {zd.fmt_size(info['size'])}"
        )
        label.setObjectName("restoreRow")
        h.addWidget(label)
        h.addStretch(1)
        btn = QPushButton("恢复")
        btn.setObjectName("secondary")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self._restore(info["dir"]))
        h.addWidget(btn)
        self.list_box.addWidget(row)

    def _restore(self, backup_dir: str):
        if self._busy:
            return
        dlg = ConfirmDialog(
            "恢复此备份？",
            [f"备份时间：{backup_dir.split(chr(92))[-1]}"],
            "确认恢复", None,
            "恢复前会自动备份当前数据库，恢复后需重新扫描。",
            self,
        )
        if dlg.exec() != QDialog.Accepted:
            return
        self._busy = True
        self.on_restore(backup_dir)
        self.accept()


HAIRLINE_PLACEHOLDER = "rgba(0,0,0,0.1)"  # noqa


# ================================================================ 标题栏

class TitleBar(QFrame):
    def __init__(self, window: "MainWindow"):
        super().__init__(window)
        self.window_ref = window
        self._drag_pos: QPoint | None = None
        self.setFixedHeight(46)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 0, 18, 0)
        lay.setSpacing(8)

        lay.addWidget(TrafficLight(TL_RED, "✕", "关闭", window.close))
        lay.addWidget(TrafficLight(TL_YELLOW, "–", "最小化", window.showMinimized))
        lay.addWidget(TrafficLight(TL_GREEN, "+", "最大化 / 还原", window.toggle_max))

        lay.addStretch(1)
        t = QLabel("Zcode 对话删除程序")
        t.setObjectName("winTitle")
        lay.addWidget(t)
        lay.addStretch(1)

        self.theme_btn = QPushButton()
        self.theme_btn.setObjectName("theme")
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.clicked.connect(window.cycle_theme)
        lay.addWidget(self.theme_btn, 0, Qt.AlignVCenter)
        lay.addSpacing(40)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.window_ref.frameGeometry().topLeft()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._drag_pos is not None and e.buttons() & Qt.LeftButton:
            if self.window_ref.isMaximized():
                self.window_ref.showNormal()
            self.window_ref.move(e.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None
        super().mouseReleaseEvent(e)

    def mouseDoubleClickEvent(self, e):
        self.window_ref.toggle_max()
        super().mouseDoubleClickEvent(e)


# ================================================================ 主窗口

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Zcode 对话删除程序")
        self.resize(960, 700)
        self.setMinimumSize(QSize(840, 580))
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.convs: list[zd.Conversation] = []
        self.selected: set[str] = set()
        self.theme_key = self._initial_theme()
        self.scan_worker: ScanWorker | None = None
        self.delete_worker: DeleteWorker | None = None
        self.batch_worker: BatchDeleteWorker | None = None
        self.restore_worker: RestoreWorker | None = None
        self._pending_delete: zd.Conversation | None = None
        self._pending_batch: list[zd.Conversation] = []

        self._build_ui()
        self.apply_theme(self.theme_key, initial=True)
        QTimer.singleShot(60, self.refresh)

    # ---------- 主题 ----------
    def _initial_theme(self) -> str:
        cfg = zd.load_config()
        saved = cfg.get("theme", "auto")
        if saved == "auto":
            return "dark" if zd.system_dark_theme() else "light"
        return saved if saved in ("light", "dark") else "light"

    def cycle_theme(self):
        order = {"light": "dark", "dark": "auto", "auto": "light"}
        self.apply_theme(order[self.theme_key])

    def apply_theme(self, key: str, initial=False):
        self.theme_key = key
        if key == "auto":
            key = "dark" if zd.system_dark_theme() else "light"
        self.theme = LIGHT if key == "light" else DARK
        self.setStyleSheet(build_qss(self.theme))
        self.title_bar.theme_btn.setText(THEME_ICONS[self.theme_key])
        self.title_bar.theme_btn.setToolTip(THEME_TIPS[self.theme_key])
        cfg = zd.load_config()
        cfg["theme"] = self.theme_key
        zd.save_config(cfg)
        if not initial:
            self._fade_in()

    # ---------- 窗口 ----------
    def toggle_max(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
        QTimer.singleShot(0, self._update_shell_shape)

    def _update_shell_shape(self):
        if self.isMaximized():
            self.root_lay.setContentsMargins(0, 0, 0, 0)
            self.shell.setStyleSheet(f"QFrame#shell {{ background: {self.theme['BG']}; border-radius: 0px; }}")
        else:
            self.root_lay.setContentsMargins(SHELL_MARGIN, SHELL_MARGIN, SHELL_MARGIN, SHELL_MARGIN)
            self.shell.setStyleSheet(f"QFrame#shell {{ background: {self.theme['BG']}; border-radius: {SHELL_RADIUS}px; }}")

    # ---------- UI ----------
    def _build_ui(self):
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        self.root_lay = QVBoxLayout(root)
        self.root_lay.setContentsMargins(SHELL_MARGIN, SHELL_MARGIN, SHELL_MARGIN, SHELL_MARGIN)
        self.root_lay.setSpacing(0)

        self.shell = QFrame()
        self.shell.setObjectName("shell")
        self.root_lay.addWidget(self.shell)
        shadow(self.shell, blur=44, y=10, alpha=60)

        v = QVBoxLayout(self.shell)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        self.title_bar = TitleBar(self)
        v.addWidget(self.title_bar)

        body = QWidget()
        bv = QVBoxLayout(body)
        bv.setContentsMargins(30, 8, 30, 18)
        bv.setSpacing(12)
        v.addWidget(body, 1)

        # 头部
        head = QHBoxLayout()
        head.setSpacing(10)
        titles = QVBoxLayout()
        titles.setSpacing(3)
        t = QLabel("Zcode 对话记录")
        t.setObjectName("title")
        self.subtitle = QLabel("正在扫描…")
        self.subtitle.setObjectName("subtitle")
        titles.addWidget(t)
        titles.addWidget(self.subtitle)
        head.addLayout(titles)
        head.addStretch(1)
        refresh = QPushButton("重新扫描")
        refresh.setObjectName("primary")
        refresh.setCursor(Qt.PointingHandCursor)
        refresh.clicked.connect(self.refresh)
        head.addWidget(refresh, 0, Qt.AlignBottom)
        bv.addLayout(head)

        # 统计卡片
        stats = QHBoxLayout()
        stats.setSpacing(12)
        self.stat_convs = self._stat_tile(stats, "—", "条对话")
        self.stat_msgs = self._stat_tile(stats, "—", "条消息")
        self.stat_size = self._stat_tile(stats, "—", "总占用")
        self.stat_files = self._stat_tile(stats, "~/.zcode", "数据位置")
        bv.addLayout(stats)

        # 快捷操作
        acts = QHBoxLayout()
        acts.setSpacing(8)
        for text, tip, cb in (
            ("🧹 清理已完成", "批量删除所有「已完成」的对话", lambda: self._quick_clean("completed")),
            ("⚠️ 清理已出错", "批量删除所有「已出错」的对话", lambda: self._quick_clean("error")),
            ("📅 清理30天前", "批量删除 30 天前更新过的对话", lambda: self._quick_clean("old")),
        ):
            b = QPushButton(text)
            b.setObjectName("secondary")
            b.setCursor(Qt.PointingHandCursor)
            b.setToolTip(tip)
            b.clicked.connect(cb)
            acts.addWidget(b)
        acts.addStretch(1)
        restore = QPushButton("🗄️ 恢复备份")
        restore.setObjectName("secondary")
        restore.setCursor(Qt.PointingHandCursor)
        restore.clicked.connect(self._open_restore)
        acts.addWidget(restore)
        bv.addLayout(acts)

        # 错误横幅
        self.banner = QLabel()
        self.banner.setObjectName("banner")
        self.banner.setWordWrap(True)
        self.banner.hide()
        bv.addWidget(self.banner)

        # 搜索
        self.search = QLineEdit()
        self.search.setObjectName("search")
        self.search.setPlaceholderText("🔍   搜索对话标题、工作区…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._apply_filter)
        bv.addWidget(self.search)

        # 列表卡片
        card = QFrame()
        card.setObjectName("card")
        cv = QVBoxLayout(card)
        cv.setContentsMargins(12, 12, 12, 12)
        self.list = QListWidget()
        self.list.setObjectName("list")
        self.list.setSelectionMode(QAbstractItemView.NoSelection)
        self.list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.list.setFocusPolicy(Qt.NoFocus)
        cv.addWidget(self.list)

        self.empty = QWidget()
        ev = QVBoxLayout(self.empty)
        ev.setAlignment(Qt.AlignCenter)
        ev.setSpacing(8)
        e1 = QLabel("🫧")
        e1.setObjectName("bigEmoji")
        e1.setAlignment(Qt.AlignCenter)
        e2 = QLabel("没有找到对话记录")
        e2.setObjectName("emptyTitle")
        e2.setAlignment(Qt.AlignCenter)
        e3 = QLabel("Zcode 客户端中当前没有任何对话，或数据尚未生成")
        e3.setObjectName("emptyBody")
        e3.setAlignment(Qt.AlignCenter)
        ev.addWidget(e1)
        ev.addWidget(e2)
        ev.addWidget(e3)
        cv.addWidget(self.empty)
        self.empty.hide()

        bv.addWidget(card, 1)

        # 选择操作栏
        self.sel_bar = QFrame()
        self.sel_bar.setStyleSheet("background: transparent;")
        sb = QHBoxLayout(self.sel_bar)
        sb.setContentsMargins(2, 0, 2, 0)
        sb.setSpacing(10)
        self.sel_label = QLabel("已选 0 条")
        self.sel_label.setObjectName("selBar")
        sb.addWidget(self.sel_label)
        sb.addStretch(1)
        cancel_sel = QPushButton("取消选择")
        cancel_sel.setObjectName("ghost")
        cancel_sel.setCursor(Qt.PointingHandCursor)
        cancel_sel.clicked.connect(self._clear_selection)
        sb.addWidget(cancel_sel)
        self.batch_btn = QPushButton("批量删除")
        self.batch_btn.setObjectName("danger")
        self.batch_btn.setCursor(Qt.PointingHandCursor)
        self.batch_btn.clicked.connect(self._batch_delete)
        self.batch_btn.setEnabled(False)
        sb.addWidget(self.batch_btn)
        bv.addWidget(self.sel_bar)
        self.sel_bar.hide()

        # 底部
        foot = QHBoxLayout()
        f1 = QLabel("扫描范围：桌面端索引 + CLI 会话库 + 关联文件")
        f1.setObjectName("foot")
        foot.addWidget(f1)
        foot.addStretch(1)
        f2 = QLabel("删除前自动备份 · 可在「恢复备份」中还原")
        f2.setObjectName("foot")
        foot.addWidget(f2)
        bv.addLayout(foot)

        self.toast = QLabel("", self.shell)
        self.toast.setObjectName("toast")
        self.toast.hide()
        self._toast_effect = QGraphicsOpacityEffect(self.toast)
        self.toast.setGraphicsEffect(self._toast_effect)

    def _stat_tile(self, layout: QHBoxLayout, num: str, label: str) -> QLabel:
        card = QFrame()
        card.setObjectName("stat")
        card.setFixedHeight(58)
        h = QHBoxLayout(card)
        h.setContentsMargins(16, 8, 16, 8)
        h.setSpacing(8)
        n = QLabel(num)
        n.setObjectName("statNum")
        l = QLabel(label)
        l.setObjectName("statLabel")
        h.addWidget(n)
        h.addStretch(1)
        h.addWidget(l, 0, Qt.AlignBottom | Qt.AlignRight)
        layout.addWidget(card, 1)
        return n

    # ---------- 扫描 ----------
    def refresh(self):
        self.subtitle.setText("正在扫描…")
        self.banner.hide()
        self.search.setEnabled(False)
        self.scan_worker = ScanWorker()
        self.scan_worker.done.connect(self._on_scan_done)
        self.scan_worker.failed.connect(self._on_scan_fail)
        self.scan_worker.start()

    def _fade_in(self):
        self.setWindowOpacity(0.6)
        anim = QPropertyAnimation(self, b"windowOpacity", self)
        anim.setDuration(260)
        anim.setStartValue(0.6)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start(QPropertyAnimation.DeleteWhenStopped)

    def _on_scan_done(self, convs: list):
        self.convs = convs
        self.search.setEnabled(True)
        n = len(convs)
        msgs = sum(c.message_count for c in convs)
        total = sum(c.size for c in convs)
        self.subtitle.setText(f"共发现 {n} 条对话记录" + (f"，{msgs} 条消息" if msgs else ""))
        self.stat_convs.setText(str(n))
        self.stat_msgs.setText(str(msgs))
        self.stat_size.setText(zd.fmt_size(total))
        self.search.clear()
        self.selected = {s for s in self.selected
                         if any(c.task_id == s for c in convs)}
        self._render(self.convs)
        self._update_sel_bar()
        self._fade_in()

    def _on_scan_fail(self, msg: str):
        self.search.setEnabled(True)
        self.subtitle.setText("扫描失败")
        self.stat_convs.setText("0")
        self.stat_msgs.setText("0")
        self.stat_size.setText("—")
        self.banner.setText(f"⚠ 扫描失败：{msg}")
        self.banner.show()
        self._render([])

    # ---------- 渲染 ----------
    def _render(self, convs: list):
        self.list.clear()
        self.empty.setVisible(len(convs) == 0)
        for i, c in enumerate(convs):
            item = QListWidgetItem(self.list)
            item.setSizeHint(QSize(0, 76))
            w = ConvItem(c, i, self._toggle_select, self._open_preview,
                         self._ask_delete, c.task_id in self.selected)
            self.list.addItem(item)
            self.list.setItemWidget(item, w)

    def _filtered(self) -> list:
        text = self.search.text().strip().lower()
        if not text:
            return self.convs
        return [c for c in self.convs
                if text in c.title.lower() or text in c.workspace.lower()]

    def _apply_filter(self, text: str):
        self._render([c for c in self.convs if
                      (not text.strip()) or text.strip().lower() in c.title.lower()
                      or text.strip().lower() in c.workspace.lower()])

    # ---------- 选择与批量 ----------
    def _toggle_select(self, task_id: str, on: bool):
        if on:
            self.selected.add(task_id)
        else:
            self.selected.discard(task_id)
        self._update_sel_bar()

    def _update_sel_bar(self):
        n = len(self.selected)
        if n:
            total = sum(c.size for c in self.convs if c.task_id in self.selected)
            self.sel_label.setText(f"已选 {n} 条 · 预计释放 {zd.fmt_size(total)}")
            self.batch_btn.setEnabled(True)
            self.sel_bar.show()
        else:
            self.sel_bar.hide()
            self.batch_btn.setEnabled(False)

    def _clear_selection(self):
        self.selected.clear()
        self._update_sel_bar()
        self._render(self._filtered())

    def _batch_delete(self):
        convs = [c for c in self.convs if c.task_id in self.selected]
        if not convs:
            return
        self._confirm_batch(convs)

    def _quick_clean(self, kind: str):
        now_ms = time.time() * 1000
        if kind == "completed":
            convs = [c for c in self.convs if c.status == "completed"]
            label = "全部「已完成」对话"
        elif kind == "error":
            convs = [c for c in self.convs if c.status == "error"]
            label = "全部「已出错」对话"
        else:
            convs = [c for c in self.convs
                     if c.updated_at < now_ms - 30 * 24 * 3600 * 1000]
            label = "30 天前更新过的对话"
        if not convs:
            self._show_toast(f"没有符合条件的对话（{label}）")
            return
        self._confirm_batch(convs)

    def _confirm_batch(self, convs: list[zd.Conversation]):
        zc = zd.is_zcode_running()
        total = sum(c.size for c in convs)
        dlg = ConfirmDialog(
            f"删除 {len(convs)} 条对话？",
            [c.title for c in convs],
            "确认删除",
            ("⚠ 检测到 Zcode 正在运行。建议先完全退出 Zcode，\n"
             "否则数据可能被写回、删除不彻底。" if zc else None),
            f"删除前会自动创建备份（~/.zcode-cleaner-backup）\n预计释放 {zd.fmt_size(total)}",
            self,
        )
        if dlg.exec() != QDialog.Accepted:
            return
        self._pending_batch = convs
        self.subtitle.setText(f"正在批量删除 {len(convs)} 条对话…")
        self.batch_worker = BatchDeleteWorker([c.task_id for c in convs])
        self.batch_worker.done.connect(self._on_batch_done)
        self.batch_worker.start()

    def _on_batch_done(self, reports: list[dict]):
        ok = [r for r in reports if "error" not in r]
        fail = [r for r in reports if "error" in r]
        removed_ids = {r["task_id"] for r in ok}
        self.convs = [c for c in self.convs if c.task_id not in removed_ids]
        self.selected -= removed_ids
        self.subtitle.setText(f"已删除 {len(ok)} 条对话"
                              + (f"，失败 {len(fail)} 条" if fail else ""))
        self._render(self._filtered())
        self._update_sel_bar()
        self._fade_in()
        freed = sum(r.get("bytes", 0) for r in ok)
        msg = f"已删除 {len(ok)} 条对话 · 释放 {freed} KB"
        self._show_toast(msg)
        if fail:
            self.banner.setText(
                "⚠ 部分对话删除失败：" + "；".join(r["error"][:60] for r in fail))
            self.banner.show()

    # ---------- 预览 ----------
    def _open_preview(self, conv: zd.Conversation):
        dlg = PreviewDialog(conv, self.theme, self)
        dlg.setStyleSheet(build_qss(self.theme))
        dlg.exec()

    # ---------- 恢复 ----------
    def _open_restore(self):
        dlg = RestoreDialog(self._do_restore, self)
        dlg.setStyleSheet(build_qss(self.theme))
        dlg.exec()

    def _do_restore(self, backup_dir: str):
        self.subtitle.setText("正在恢复备份…")
        self.banner.hide()
        self.restore_worker = RestoreWorker(backup_dir)
        self.restore_worker.done.connect(self._on_restore_done)
        self.restore_worker.failed.connect(self._on_restore_fail)
        self.restore_worker.start()

    def _on_restore_done(self, report: dict):
        self.subtitle.setText("恢复完成 · 正在重新扫描")
        self._show_toast(f"已恢复 {len(report.get('restored', []))} 个数据库文件")
        QTimer.singleShot(400, self.refresh)

    def _on_restore_fail(self, msg: str):
        self.subtitle.setText("恢复失败")
        self.banner.setText(f"⚠ 恢复失败：{msg}")
        self.banner.show()

    # ---------- 单条删除 ----------
    def _ask_delete(self, conv: zd.Conversation):
        dlg = ConfirmDialog(
            "删除这条对话？",
            [conv.title],
            "确认删除",
            ("⚠ 检测到 Zcode 正在运行。建议先完全退出 Zcode，\n"
             "否则数据可能被写回、删除不彻底。" if zd.is_zcode_running() else None),
            "删除前会自动创建备份（~/.zcode-cleaner-backup）",
            self,
        )
        if dlg.exec() != QDialog.Accepted:
            return
        self._pending_delete = conv
        self.subtitle.setText("正在删除…")
        self.search.setEnabled(False)
        self.delete_worker = DeleteWorker(conv.task_id)
        self.delete_worker.done.connect(self._on_delete_done)
        self.delete_worker.failed.connect(self._on_delete_fail)
        self.delete_worker.start()

    def _on_delete_done(self, report: dict):
        self.search.setEnabled(True)
        conv = self._pending_delete
        self.convs = [c for c in self.convs if c.task_id != report["task_id"]]
        n = len(self.convs)
        msgs = sum(c.message_count for c in self.convs)
        self.stat_convs.setText(str(n))
        self.stat_msgs.setText(str(msgs))
        self.stat_size.setText(zd.fmt_size(sum(c.size for c in self.convs)))
        self.subtitle.setText(f"已删除 1 条对话 · 剩余 {n} 条")
        self.selected.discard(report["task_id"])
        self._render(self._filtered())
        self._update_sel_bar()
        self._fade_in()
        short = (conv.title[:18] + "…") if conv and len(conv.title) > 18 else (conv.title if conv else report["task_id"])
        msg = f"已彻底删除「{short}」"
        if report.get("files"):
            msg += f" · 清理 {len(report['files'])} 项关联文件 · 释放 {report.get('bytes', 0)} KB"
        self._show_toast(msg)

    def _on_delete_fail(self, msg: str):
        self.search.setEnabled(True)
        self.subtitle.setText("删除失败 · 列表未变更")
        self.banner.setText(f"⚠ 删除失败：{msg}")
        self.banner.show()
        self._show_toast("删除失败，请查看顶部提示")

    # ---------- Toast ----------
    def _show_toast(self, text: str):
        self.toast.setText(text)
        self.toast.adjustSize()
        self.toast.move((self.shell.width() - self.toast.width()) // 2,
                        self.shell.height() - 74)
        self.toast.show()
        self.toast.raise_()
        self._toast_effect.setOpacity(1.0)
        anim = QPropertyAnimation(self._toast_effect, b"opacity", self)
        anim.setDuration(1500)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.InQuad)
        try:
            if anim.finished.isConnected():
                anim.finished.disconnect()
        except Exception:
            pass
        anim.finished.connect(self.toast.hide)
        anim.start(QPropertyAnimation.DeleteWhenStopped)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("Zcode 对话删除程序")
    icon_path = Path(__file__).parent / "assets" / "icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
