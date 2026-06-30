from PySide6.QtWidgets import *
from PySide6.QtCore import Qt


class DetectionsTable(QTableWidget):

    def __init__(self):

        super().__init__()

        self.setColumnCount(6)

        self.setHorizontalHeaderLabels([
            "ID",
            "Distance",
            "Angle",
            "X",
            "Y",
            "Points"
        ])

        self.horizontalHeader().setStretchLastSection(True)

    def update_table(self, detections):

        self.setRowCount(len(detections))

        for row, d in enumerate(detections):

            self.setItem(row, 0, QTableWidgetItem(str(d.object_id)))
            self.setItem(row, 1, QTableWidgetItem(f"{d.distance:.2f}"))
            self.setItem(row, 2, QTableWidgetItem(f"{d.angle:.2f}"))
            self.setItem(row, 3, QTableWidgetItem(f"{d.x:.2f}"))
            self.setItem(row, 4, QTableWidgetItem(f"{d.y:.2f}"))
            self.setItem(row, 5, QTableWidgetItem(str(d.point_count)))