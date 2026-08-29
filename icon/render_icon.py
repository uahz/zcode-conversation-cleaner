# -*- coding: utf-8 -*-
"""用 PySide6 的 QSvgRenderer 渲染 icon.svg → 多尺寸 PNG → 打包 .ico"""

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QBuffer, QByteArray
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer
from PIL import Image

ROOT = Path(__file__).parent
SVG = ROOT / "icon.svg"
OUT_PNG = ROOT / "icon_1024.png"
OUT_PNG_SMALL = ROOT / "icon_256.png"
OUT_ICO = ROOT.parent / "assets" / "icon.ico"


def render_png(size: int) -> Image.Image:
    svg = QSvgRenderer(str(SVG))
    assert svg.isValid(), "SVG 解析失败"
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    svg.render(p)
    p.end()
    # QImage → PIL
    buf = QBuffer()
    buf.open(QBuffer.WriteOnly)
    img.save(buf, "PNG")
    import io
    return Image.open(io.BytesIO(bytes(buf.data()))).convert("RGBA")


def main():
    big = render_png(1024)
    big.save(OUT_PNG)
    big.resize((256, 256), Image.LANCZOS).save(OUT_PNG_SMALL)

    OUT_ICO.parent.mkdir(exist_ok=True)
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    big.resize((256, 256), Image.LANCZOS).save(
        OUT_ICO, format="ICO", sizes=sizes
    )
    print("已生成:", OUT_PNG, OUT_PNG_SMALL, OUT_ICO)


if __name__ == "__main__":
    sys.exit(main())
