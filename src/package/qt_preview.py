"""PyQt を使用した最終解析画像の確認ダイアログ。"""

import logging

import numpy as np
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import (
    QColor,
    QImage,
    QLinearGradient,
    QPaintEvent,
    QPainter,
    QPen,
)
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QWidget

from src.package.qt_dialogs import ensure_qapplication

LOGGER = logging.getLogger("sunspot.qt_preview")


class _FinalPreviewCanvas(QWidget):
    """最終画像とピクセル値のカラーバーを描画するキャンバス。"""

    def __init__(self, image: np.ndarray, parent: QWidget | None = None) -> None:
        """表示用のグレースケール画像を作成する。

        Parameters
        ----------
        image : numpy.ndarray
            最終確認する2次元画像。
        parent : QWidget | None, optional
            親ウィジェット。
        """
        super().__init__(parent)
        if image.ndim != 2 or image.size == 0:
            raise ValueError("最終確認画像は空でない2次元配列にしてください。")

        values = np.nan_to_num(
            image.astype(np.float64),
            nan=0.0,
            posinf=0.0,
            neginf=0.0,
        )
        self._minimum = float(values.min())
        self._maximum = float(values.max())
        if self._maximum > self._minimum:
            normalized = np.rint(
                (values - self._minimum)
                / (self._maximum - self._minimum)
                * 255
            ).astype(np.uint8)
        else:
            normalized = np.full(values.shape, 127, dtype=np.uint8)

        # Matplotlib の origin="lower" と同じ向きにする。
        normalized = np.ascontiguousarray(np.flipud(normalized))
        self._image_height, self._image_width = normalized.shape
        image_bytes = normalized.tobytes()
        self._qimage = QImage(
            image_bytes,
            self._image_width,
            self._image_height,
            int(normalized.strides[0]),
            QImage.Format.Format_Grayscale8,
        ).copy()
        self.setMinimumSize(480, 360)

    def paintEvent(self, event: QPaintEvent | None) -> None:
        """画像、軸ラベル、ピクセル値カラーバーをベクター描画する。

        Parameters
        ----------
        event : QPaintEvent | None
            Qt の描画イベント。
        """
        del event
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(30, 30, 30))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        plot_area = QRectF(
            72,
            18,
            max(1, self.width() - 174),
            max(1, self.height() - 76),
        )
        scale = min(
            plot_area.width() / self._image_width,
            plot_area.height() / self._image_height,
        )
        shown_width = self._image_width * scale
        shown_height = self._image_height * scale
        image_rect = QRectF(
            plot_area.left() + (plot_area.width() - shown_width) / 2,
            plot_area.top() + (plot_area.height() - shown_height) / 2,
            shown_width,
            shown_height,
        )

        painter.drawImage(image_rect, self._qimage)
        border_pen = QPen(QColor(235, 235, 235), 1)
        border_pen.setCosmetic(True)
        painter.setPen(border_pen)
        painter.drawRect(image_rect)

        painter.setPen(QColor(240, 240, 240))
        painter.drawText(
            QRectF(image_rect.left(), image_rect.bottom() + 8, image_rect.width(), 24),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
            "X [pixel]",
        )
        painter.save()
        painter.translate(image_rect.left() - 48, image_rect.center().y())
        painter.rotate(-90)
        painter.drawText(
            QRectF(-image_rect.height() / 2, -12, image_rect.height(), 24),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            "Y [pixel]",
        )
        painter.restore()

        colorbar = QRectF(image_rect.right() + 18, image_rect.top(), 18, image_rect.height())
        gradient = QLinearGradient(
            colorbar.left(),
            colorbar.top(),
            colorbar.left(),
            colorbar.bottom(),
        )
        gradient.setColorAt(0.0, QColor(255, 255, 255))
        gradient.setColorAt(1.0, QColor(0, 0, 0))
        painter.fillRect(colorbar, gradient)
        painter.setPen(border_pen)
        painter.drawRect(colorbar)

        painter.drawText(
            QRectF(colorbar.right() + 7, colorbar.top() - 8, 78, 20),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            f"{self._maximum:g}",
        )
        painter.drawText(
            QRectF(colorbar.right() + 7, colorbar.bottom() - 12, 78, 20),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            f"{self._minimum:g}",
        )
        painter.end()


class _FinalPreviewDialog(QDialog):
    """解析結果を確認する PyQt ダイアログ。"""

    def __init__(self, image: np.ndarray, parent: QWidget | None = None) -> None:
        """画像キャンバスと閉じるボタンを構築する。"""
        super().__init__(parent)
        self.setWindowTitle("Final Result Preview")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(_FinalPreviewCanvas(image), 1)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.accept)
        layout.addWidget(button_box)
        self.setMinimumSize(520, 400)
        self.resize(1050, 800)


def show_final_preview(image: np.ndarray) -> None:
    """PyQt ダイアログで最終解析画像を表示する。

    Parameters
    ----------
    image : numpy.ndarray
        表示する2次元の最終解析画像。
    """
    ensure_qapplication()
    LOGGER.info(
        "Displaying final result preview: shape=%s, dtype=%s",
        image.shape,
        image.dtype,
    )
    dialog = _FinalPreviewDialog(image)
    dialog.exec()
    LOGGER.info("Final result preview closed.")
