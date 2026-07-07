from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush
from PySide6.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem


class DetectionsTable(QTableWidget):
    def __init__(self):
        super().__init__()

        self.setColumnCount(7)
        self.setHorizontalHeaderLabels(
            [
                "ID",
                "Nom",
                "Classe",
                "Confiance",
                "Distance",
                "Position",
                "Couleur",
            ]
        )
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setEditTriggers(QTableWidget.NoEditTriggers)

    @staticmethod
    def _get(detection, *names, default="-"):
        for name in names:
            if hasattr(detection, name):
                value = getattr(detection, name)
                if value is not None:
                    return value
        return default

    @staticmethod
    def _item(text):
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(Qt.AlignCenter)
        return item

    def update_table(self, detections):
        self.clearContents()

        if not detections:
            self.setRowCount(1)
            self.setItem(0, 0, self._item("-"))
            self.setItem(0, 1, self._item("Aucune détection"))
            self.setItem(0, 2, self._item("-"))
            self.setItem(0, 3, self._item("-"))
            self.setItem(0, 4, self._item("-"))
            self.setItem(0, 5, self._item("-"))
            self.setItem(0, 6, self._item("-"))
            return

        self.setRowCount(len(detections))

        for row, detection in enumerate(detections):
            track_id = self._get(detection, "track_id", "object_id", default="-")
            name = self._get(detection, "name", default="Object")
            class_name = self._get(detection, "class_name", default="object")
            confidence = self._get(detection, "confidence", default=1.0)
            distance = self._get(detection, "distance", default=0.0)
            x = float(self._get(detection, "x", default=0.0))
            y = float(self._get(detection, "y", default=0.0))
            color = self._get(detection, "color", default="#60A5FA")

            self.setItem(row, 0, self._item(track_id))
            self.setItem(row, 1, self._item(name))
            self.setItem(row, 2, self._item(class_name))
            self.setItem(row, 3, self._item(f"{float(confidence) * 100:.1f}%"))
            self.setItem(row, 4, self._item(f"{float(distance):.2f} m"))
            self.setItem(row, 5, self._item(f"({x:.2f}, {y:.2f})"))

            color_item = self._item(color)
            color_item.setBackground(QBrush(QColor(color)))
            color_item.setForeground(QBrush(QColor("white")))
            self.setItem(row, 6, color_item)