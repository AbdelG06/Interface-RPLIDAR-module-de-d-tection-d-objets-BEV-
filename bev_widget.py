from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QSizePolicy, QVBoxLayout, QWidget


class BEVWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.plot = pg.PlotWidget()
        layout.addWidget(self.plot)

        self.plot.setBackground("#0B0F15")
        self.plot.setAspectLocked(True)
        self.plot.setMouseEnabled(x=True, y=True)
        self.plot.enableAutoRange(False)
        self.plot.setMinimumSize(520, 360)
        self.plot.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.plot.hideAxis("bottom")
        self.plot.hideAxis("left")
        self.plot.showGrid(x=True, y=True, alpha=0.25)
        self.plot.setXRange(-12, 12)
        self.plot.setYRange(-12, 12)

        for radius in [2, 4, 6, 8, 10, 12]:
            circle = pg.QtWidgets.QGraphicsEllipseItem(-radius, -radius, radius * 2, radius * 2)
            circle.setPen(pg.mkPen(color="#233248", width=1))
            self.plot.addItem(circle)

        self.scatter = pg.ScatterPlotItem(size=7, brush=pg.mkBrush("#00E5FF"), pen=None)
        self.plot.addItem(self.scatter)
        self.show_points = True

        self.sensor = pg.ScatterPlotItem(size=16, brush=pg.mkBrush("#00FF95"), pen=pg.mkPen("#002B1F", width=1))
        self.sensor.setData([0], [0])
        self.plot.addItem(self.sensor)

        self.detection_items = []

    @staticmethod
    def _to_xy(points):
        if points is None:
            return np.zeros((0, 2), dtype=float)

        points = np.asarray(points, dtype=float)
        if points.size == 0:
            return np.zeros((0, 2), dtype=float)

        if points.ndim == 1:
            points = points.reshape(1, -1)

        if points.shape[1] >= 2:
            return points[:, :2]

        return np.column_stack([points[:, 0], np.zeros(len(points))])

    def _clear_detections(self):
        for item in self.detection_items:
            self.plot.removeItem(item)
        self.detection_items = []

    def update_points(self, points):
        if not self.show_points:
            self.scatter.setData([], [])
            return

        xy = self._to_xy(points)
        if xy.size == 0:
            self.scatter.setData([], [])
            return

        if xy.shape[0] > 6000:
            step = max(1, xy.shape[0] // 6000)
            xy = xy[::step]

        self.scatter.setData(x=xy[:, 0], y=xy[:, 1])

    @staticmethod
    def _to_qcolor(color):
        qcolor = pg.mkColor(color)
        qcolor.setAlpha(180)
        return qcolor

    def update_detections(self, detections):
        self._clear_detections()

        if not detections:
            return

        for detection in detections:
            xmin = float(getattr(detection, "xmin", detection.x - detection.width / 2.0))
            ymin = float(getattr(detection, "ymin", detection.y - detection.height / 2.0))
            xmax = float(getattr(detection, "xmax", detection.x + detection.width / 2.0))
            ymax = float(getattr(detection, "ymax", detection.y + detection.height / 2.0))
            color = self._to_qcolor(getattr(detection, "color", "#00E5FF"))

            box_x = [xmin, xmax, xmax, xmin, xmin]
            box_y = [ymin, ymin, ymax, ymax, ymin]
            box_item = pg.PlotDataItem(box_x, box_y, pen=pg.mkPen(color=color, width=2))
            self.plot.addItem(box_item)
            self.detection_items.append(box_item)

            center_item = pg.ScatterPlotItem(size=10, brush=pg.mkBrush(color), pen=pg.mkPen("#000000", width=1))
            center_item.setData([detection.x], [detection.y])
            self.plot.addItem(center_item)
            self.detection_items.append(center_item)

            text = pg.TextItem(
                text=f"ID {getattr(detection, 'track_id', getattr(detection, 'object_id', 0))} | {detection.name}",
                color=color,
                anchor=(0, 1),
            )
            text.setPos(detection.x, detection.y)
            self.plot.addItem(text)
            self.detection_items.append(text)

    def update_scene(self, points, detections=None):
        self.update_points(points)
        self.update_detections(detections)

    def set_points_visible(self, visible: bool):
        self.show_points = bool(visible)
        if not self.show_points:
            self.scatter.setData([], [])

