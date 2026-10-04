"""Regenerate app_logo.ico from assets/app_logo.svg with multi-resolution antialiasing."""
import io
import os
from pathlib import Path
from PIL import Image
from PySide6.QtCore import QByteArray, QBuffer, QIODevice, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication

def generate():
    app = QApplication.instance() or QApplication(["-platform", "offscreen"])
    root = Path(__file__).resolve().parents[1]
    svg_path = root / "assets" / "app_logo.svg"
    ico_path = os.path.normpath(str((root / "assets" / "app_logo.ico").resolve()))

    with open(str(svg_path), "r", encoding="utf-8") as f:
        svg_data = f.read()

    renderer = QSvgRenderer(QByteArray(svg_data.encode("utf-8")))

    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = []
    for s in sizes:
        img = QImage(s, s, QImage.Format_ARGB32)
        img.fill(Qt.transparent)
        p = QPainter(img)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)
        renderer.render(p)
        p.end()

        buf = QBuffer()
        buf.open(QIODevice.ReadWrite)
        img.save(buf, "PNG")
        images.append(Image.open(io.BytesIO(bytes(buf.data()))))

    # Save to BytesIO first then write to file
    out_buf = io.BytesIO()
    images[-1].save(out_buf, format="ICO", sizes=[(s, s) for s in sizes])
    with open(ico_path, "wb") as f:
        f.write(out_buf.getvalue())
    print(f"Successfully generated {ico_path} ({os.path.getsize(ico_path)} bytes)")

if __name__ == "__main__":
    generate()
