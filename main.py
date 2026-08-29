# -*- coding: utf-8 -*-
"""
Zcode 对话删除程序 —— GUI（Apple 设计语言 · 精致版 v2）
无边框 macOS 风格 / 可点击红绿灯按钮 / 圆角窗口 / 卡片投影 / 渐入动画
"""

from __future__ import annotations

import sys
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
)

import zcode_data as zd

# ---------------------------------------------------------------- 配色（Apple 系）
BG        = "#F5F5F7"
CARD      = "#FFFFFF"
TEXT      = "#1D1D1F"
TEXT_2    = "#86868B"
BLUE      = "#0071E3"
BLUE_H    = "#0077ED"
RED       = "#FF3B30"
RED_DARK  = "#D70015"
GREEN     = "#34C759"
ORANGE    = "#FF9500"
HAIRLINE  = "rgba(0,0,0,0.08)"

# macOS 红绿灯
TL_RED    = "#FF5F57"
TL_YELLOW = "#FEBC2E"
TL_GREEN  = "#28C840"

SHELL_RADIUS = 12
SHELL_MARGIN = 14  # 窗口四周留白，用于投影

AVATAR_GRADS = [
    ("#5AC8FA", "#0071E3"), ("#FF9A8B", "#FF3B30"), ("#A8E063", "#34C759"),
    ("#F6D365", "#FDA085"), ("#B39DDB", "#7E57C2"), ("#80DEEA", "#26A69A"),
    ("#FBC2EB", "#A18CD1"), ("#FDCB6E", "#E17055"),
]

STATUS_COLOR = {
    "已完成": GREEN, "进行中": BLUE, "排队中": ORANGE,
    "已出错": RED, "已取消": TEXT_2, "已停止": TEXT_2, "未知": TEXT_2,
}

QSS = f"""
* {{
    font-family: "PingFang SC", "SF Pro Text", "Microsoft YaHei UI", "Segoe UI", sans-serif;
    outline: none;
}}
QMainWindow, QWidget#root {{ background: transparent; }}
QFrame#shell {{ background: {BG}; border-radius: {SHELL_RADIUS}px; }}
QLabel {{ color: {TEXT}; }}

/* ---------- 标题栏红绿灯 ---------- */
QPushButton.traffic {{
    border: none; border-radius: 7px; min-width: 14px; max-width: 14px;
    min-height: 14px; max-height: 14px; padding: 0;
    font-size: 9px; font-weight: 700; color: rgba(0,0,0,0.55);
}}
QPushButton.traffic:hover {{ border: 1px solid rgba(0,0,0,0.20); }}
QPushButton.traffic:pressed {{ }}

QLabel#winTitle {{
    font-size: 13px; font-weight: 600; color: {TEXT_2}; letter-spacing: 0.3px;
}}

/* ---------- 头部 ---------- */
QLabel#title {{ font-size: 26px; font-weight: 700; letter-spacing: 0.2px; }}
QLabel#subtitle {{ font-size: 13px; color: {TEXT_2}; }}

QFrame#stat {{
    background: {CARD}; border: 1px solid {HAIRLINE}; border-radius: 13px;
}}
QLabel#statNum {{ font-size: 19px; font-weight: 700; }}
QLabel#statLabel {{ font-size: 11px; color: {TEXT_2}; }}

/* ---------- 搜索 ---------- */
QLineEdit#search {{
    background: {CARD}; border: 1px solid {HAIRLINE}; border-radius: 11px;
    padding: 9px 14px 9px 34px; font-size: 13px; color: {TEXT};
    selection-background-color: {BLUE};
}}
QLineEdit#search:focus {{ border: 1px solid {BLUE}; }}

/* ---------- 主卡片 ---------- */
QFrame#card {{
    background: {CARD}; border-radius: 16px; border: 1px solid {HAIRLINE};
}}

/* ---------- 列表 ---------- */
QListWidget#list {{ background: transparent; border: none; outline: none; }}
QListWidget#list::item {{ margin: 0px 2px 10px 2px; }}
QListWidget#list::item:selected {{ background: transparent; }}

QScrollBar:vertical {{
    background: transparent; width: 8px; margin: 6px 2px 6px 0px;
}}
QScrollBar::handle:vertical {{
    background: rgba(0,0,0,0.16); border-radius: 4px; min-height: 32px;
}}
QScrollBar::handle:vertical:hover {{ background: rgba(0,0,0,0.28); }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}

/* ---------- 对话条目 ---------- */
QFrame#item {{
    background: {CARD}; border: 1px solid {HAIRLINE}; border-radius: 14px;
}}
QFrame#item:hover {{ border: 1px solid rgba(0,113,227,0.35); background: #FBFDFF; }}

QLabel#avatar {{
    border-radius: 19px; min-width: 38px; max-width: 38px;
    min-height: 38px; max-height: 38px;
    font-size: 15px; font-weight: 700; color: white; border: none;
}}
QLabel#itemTitle {{ font-size: 14px; font-weight: 600; color: {TEXT}; }}
QLabel#itemMeta {{ font-size: 12px; color: {TEXT_2}; }}

QPushButton#del {{
    background: rgba(255,59,48,0.09); color: {RED}; border: none;
    border-radius: 10px; padding: 8px 0px; font-size: 12px; font-weight: 600;
    min-width: 62px; max-width: 62px;
}}
QPushButton#del:hover {{ background: {RED}; color: white; }}
QPushButton#del:pressed {{ background: {RED_DARK}; }}

/* ---------- 按钮 ---------- */
QPushButton#primary {{
    background: {BLUE}; color: white; border: none; border-radius: 11px;
    padding: 10px 20px; font-size: 13px; font-weight: 600;
}}
QPushButton#primary:hover {{ background: {BLUE_H}; }}
QPushButton#primary:pressed {{ background: #0068D1; }}
QPushButton#primary:disabled {{ background: #B8D4F5; }}

/* ---------- 确认对话框 ---------- */
QDialog#confirm {{ background: {BG}; }}
QLabel#dlgTitle {{ font-size: 18px; font-weight: 700; }}
QLabel#dlgBody {{ font-size: 13px; color: {TEXT_2}; }}
QLabel#dlgName {{
    background: {CARD}; border: 1px solid {HAIRLINE}; border-radius: 10px;
    padding: 9px 12px; font-size: 13px; font-weight: 600; color: {TEXT};
}}
QLabel#warn {{
    background: rgba(255,149,0,0.12); color: #B25000; border-radius: 10px;
    padding: 10px 12px; font-size: 12px;
}}
QPushButton#danger {{
    background: {RED}; color: white; border: none; border-radius: 11px;
    padding: 10px 26px; font-size: 13px; font-weight: 600;
}}
QPushButton#danger:hover {{ background: {RED_DARK}; }}
QPushButton#cancel {{
    background: {CARD}; color: {TEXT}; border: 1px solid {HAIRLINE};
    border-radius: 11px; padding: 10px 26px; font-size: 13px; font-weight: 500;
}}
QPushButton#cancel:hover {{ background: #EDEDF0; }}

/* ---------- Toast / 横幅 / 空状态 ---------- */
QLabel#toast {{
    background: rgba(29,29,31,0.90); color: white; border-radius: 13px;
    padding: 11px 22px; font-size: 13px; font-weight: 500;
}}
QLabel#emptyTitle {{ font-size: 17px; font-weight: 600; color: {TEXT}; }}
QLabel#emptyBody {{ font-size: 13px; color: {TEXT_2}; }}
QLabel#banner {{
    background: rgba(255,59,48,0.10); color: {RED_DARK}; border-radius: 11px;
    padding: 11px 14px; font-size: 12.5px; font-weight: 500;
}}
QLabel#bigEmoji {{ font-size: 46px; }}
QLabel#foot {{ font-size: 11.5px; color: {TEXT_2}; }}
"""


def shadow(widget: QWidget, blur=28, y=6, alpha=36):
    eff = QGraphicsDropShadowEffect(widget)
    eff.setBlurRadius(blur)
    eff.setOffset(0, y)
    eff.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(eff)
    return eff


# ---------------------------------------------------------------- 后台线程

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


# ---------------------------------------------------------------- 红绿灯按钮（可点击）

class TrafficLight(QPushButton):
    """macOS 红绿灯：悬停显示符号、按下有按压反馈、点击执行动作。"""

    def __init__(self, color: str, symbol: str, tip: str, callback):
        super().__init__()
        self._color = color
        self._symbol = symbol
        self.setObjectName("traffic")
        self.setProperty("class", "traffic")
        self.setFixedSize(14, 14)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(tip)
        self.setStyleSheet(
            f"QPushButton.traffic {{ background: {color}; }}"
            f"QPushButton.traffic:pressed {{ background: {color}; }}"
        )
        self.clicked.connect(callback)

    def enterEvent(self, e):
        self.setText(self._symbol)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self.setText("")
        super().leaveEvent(e)


# ---------------------------------------------------------------- 列表条目

class ConvItem(QFrame):
    def __init__(self, conv: zd.Conversation, index: int, on_delete):
        super().__init__()
        self.setObjectName("item")
        self.conv = conv

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 12, 12, 12)
        lay.setSpacing(13)

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
        title.setText(fm.elidedText(conv.title.replace("\n", " "), Qt.ElideRight, 400))
        title.setToolTip(conv.title)
        title.setFixedWidth(400)

        meta_bits = [conv.workspace, f"更新于 {conv.updated_text}"]
        if conv.message_count:
            meta_bits.append(f"{conv.message_count} 条消息")
        meta_bits.append(conv.source)
        meta = QLabel("  ·  ".join(meta_bits))
        meta.setObjectName("itemMeta")

        mid.addWidget(title)
        mid.addWidget(meta)
        lay.addLayout(mid, 0)
        lay.addStretch(1)

        color = STATUS_COLOR.get(conv.status_label, TEXT_2)
        pill = QLabel(conv.status_label)
        pill.setStyleSheet(
            f"color: {color}; background: {color}1A; border-radius: 9px;"
            "font-size: 11px; font-weight: 600; padding: 3px 10px;"
        )
        lay.addWidget(pill, 0, Qt.AlignVCenter)

        btn = QPushButton("删除")
        btn.setObjectName("del")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: on_delete(conv))
        lay.addWidget(btn, 0, Qt.AlignVCenter)


# ---------------------------------------------------------------- 确认对话框

class ConfirmDialog(QDialog):
    def __init__(self, conv: zd.Conversation, zcode_running: bool, parent=None):
        super().__init__(parent)
        self.setObjectName("confirm")
        self.setWindowTitle("确认删除")
        self.setModal(True)
        self.setFixedSize(440, 372)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 28, 30, 24)
        lay.setSpacing(12)

        emoji = QLabel("🗑️")
        emoji.setObjectName("bigEmoji")
        emoji.setAlignment(Qt.AlignCenter)
        emoji.setStyleSheet("font-size: 40px;")

        t = QLabel("删除这条对话？")
        t.setObjectName("dlgTitle")
        t.setAlignment(Qt.AlignCenter)

        name = QLabel()
        name.setObjectName("dlgName")
        fm = QFontMetrics(name.font())
        name.setText(fm.elidedText(conv.title, Qt.ElideMiddle, 350))
        name.setAlignment(Qt.AlignCenter)
        name.setWordWrap(False)
        name.setToolTip(conv.title)

        b = QLabel(
            "将永久删除该对话的消息记录、会话数据、\n执行产物及全部关联文件，此操作不可撤销。"
        )
        b.setObjectName("dlgBody")
        b.setAlignment(Qt.AlignCenter)

        lay.addWidget(emoji)
        lay.addWidget(t)
        lay.addWidget(name)
        lay.addWidget(b)

        if zcode_running:
            warn = QLabel("⚠ 检测到 Zcode 正在运行。建议先完全退出 Zcode，\n否则数据可能被写回、删除不彻底。")
            warn.setObjectName("warn")
            warn.setAlignment(Qt.AlignCenter)
            lay.addWidget(warn)

        note = QLabel("删除前会自动创建备份（~/.zcode-cleaner-backup）")
        note.setObjectName("dlgBody")
        note.setAlignment(Qt.AlignCenter)
        lay.addWidget(note)

        lay.addStretch(1)

        btns = QHBoxLayout()
        btns.setSpacing(10)
        cancel = QPushButton("取消")
        cancel.setObjectName("cancel")
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        ok = QPushButton("确认删除")
        ok.setObjectName("danger")
        ok.setCursor(Qt.PointingHandCursor)
        ok.clicked.connect(self.accept)
        btns.addWidget(cancel)
        btns.addWidget(ok)
        lay.addLayout(btns)


# ---------------------------------------------------------------- 标题栏（红绿灯 + 拖拽）

class TitleBar(QFrame):
    def __init__(self, window: "MainWindow"):
        super().__init__(window)
        self.window_ref = window
        self._drag_pos: QPoint | None = None
        self.setFixedHeight(46)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 0, 18, 0)
        lay.setSpacing(8)

        # 真正可点击的红绿灯按钮
        lay.addWidget(TrafficLight(TL_RED, "✕", "关闭", window.close))
        lay.addWidget(TrafficLight(TL_YELLOW, "–", "最小化", window.showMinimized))
        lay.addWidget(TrafficLight(TL_GREEN, "+", "最大化 / 还原", window.toggle_max))

        lay.addStretch(1)
        t = QLabel("Zcode 对话删除程序")
        t.setObjectName("winTitle")
        lay.addWidget(t)
        lay.addStretch(1)
        lay.addSpacing(64)  # 平衡左侧红绿灯，让标题视觉居中

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


# ---------------------------------------------------------------- 主窗口

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Zcode 对话删除程序")
        self.resize(920, 680)
        self.setMinimumSize(QSize(800, 560))
        # 无边框 + 半透明背景 → 圆角窗口壳
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.convs: list[zd.Conversation] = []
        self.scan_worker: ScanWorker | None = None
        self.delete_worker: DeleteWorker | None = None
        self._pending_delete: zd.Conversation | None = None
        self._build_ui()
        self.setStyleSheet(QSS)
        QTimer.singleShot(60, self.refresh)

    def toggle_max(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
        QTimer.singleShot(0, self._update_shell_shape)

    def _update_shell_shape(self):
        """最大化时去掉外边距与圆角，还原时恢复。"""
        if self.isMaximized():
            self.root_lay.setContentsMargins(0, 0, 0, 0)
            self.shell.setStyleSheet(
                f"QFrame#shell {{ background: {BG}; border-radius: 0px; }}"
            )
        else:
            self.root_lay.setContentsMargins(
                SHELL_MARGIN, SHELL_MARGIN, SHELL_MARGIN, SHELL_MARGIN
            )
            self.shell.setStyleSheet(
                f"QFrame#shell {{ background: {BG}; border-radius: {SHELL_RADIUS}px; }}"
            )

    # ---------- UI 构建 ----------
    def _build_ui(self):
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        self.root_lay = QVBoxLayout(root)
        self.root_lay.setContentsMargins(
            SHELL_MARGIN, SHELL_MARGIN, SHELL_MARGIN, SHELL_MARGIN
        )
        self.root_lay.setSpacing(0)

        # 圆角窗口壳（承载全部内容 + 窗口投影）
        self.shell = QFrame()
        self.shell.setObjectName("shell")
        self.root_lay.addWidget(self.shell)
        shadow(self.shell, blur=44, y=10, alpha=60)

        v = QVBoxLayout(self.shell)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # 标题栏
        self.title_bar = TitleBar(self)
        v.addWidget(self.title_bar)

        body = QWidget()
        bv = QVBoxLayout(body)
        bv.setContentsMargins(30, 8, 30, 20)
        bv.setSpacing(14)
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

        # 统计卡片行
        stats = QHBoxLayout()
        stats.setSpacing(12)
        self.stat_convs = self._stat_tile(stats, "—", "条对话")
        self.stat_msgs = self._stat_tile(stats, "—", "条消息")
        self.stat_files = self._stat_tile(stats, "~/.zcode", "数据位置")
        bv.addLayout(stats)

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

        # 空状态
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

        # 底部
        foot = QHBoxLayout()
        f1 = QLabel("扫描范围：桌面端索引 + CLI 会话库 + 关联文件")
        f1.setObjectName("foot")
        foot.addWidget(f1)
        foot.addStretch(1)
        f2 = QLabel("删除前自动备份至 ~/.zcode-cleaner-backup")
        f2.setObjectName("foot")
        foot.addWidget(f2)
        bv.addLayout(foot)

        # Toast（挂在圆角壳上）
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
        """窗口级淡入（合成器实现，避免 QGraphicsEffect 与列表子控件的渲染冲突）。"""
        self.setWindowOpacity(0.55)
        anim = QPropertyAnimation(self, b"windowOpacity", self)
        anim.setDuration(260)
        anim.setStartValue(0.55)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start(QPropertyAnimation.DeleteWhenStopped)

    def _on_scan_done(self, convs: list):
        self.convs = convs
        self.search.setEnabled(True)
        n = len(convs)
        msgs = sum(c.message_count for c in convs)
        self.subtitle.setText(f"共发现 {n} 条对话记录" + (f"，{msgs} 条消息" if msgs else ""))
        self.stat_convs.setText(str(n))
        self.stat_msgs.setText(str(msgs))
        self.search.clear()
        self._render(convs)
        self._fade_in()

    def _on_scan_fail(self, msg: str):
        self.search.setEnabled(True)
        self.subtitle.setText("扫描失败")
        self.stat_convs.setText("0")
        self.stat_msgs.setText("0")
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
            w = ConvItem(c, i, self._ask_delete)
            self.list.addItem(item)
            self.list.setItemWidget(item, w)

    def _apply_filter(self, text: str):
        text = text.strip().lower()
        if not text:
            self._render(self.convs)
            return
        shown = [
            c for c in self.convs
            if text in c.title.lower() or text in c.workspace.lower()
        ]
        self._render(shown)

    # ---------- 删除 ----------
    def _ask_delete(self, conv: zd.Conversation):
        dlg = ConfirmDialog(conv, zd.is_zcode_running(), self)
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
        self.subtitle.setText(f"已删除 1 条对话 · 剩余 {n} 条")
        self._render(self._filtered())
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

    def _filtered(self) -> list:
        text = self.search.text().strip().lower()
        if not text:
            return self.convs
        return [
            c for c in self.convs
            if text in c.title.lower() or text in c.workspace.lower()
        ]

    # ---------- Toast ----------
    def _show_toast(self, text: str):
        self.toast.setText(text)
        self.toast.adjustSize()
        self.toast.move(
            (self.shell.width() - self.toast.width()) // 2,
            self.shell.height() - 70,
        )
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
