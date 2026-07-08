import pyqtgraph as pg

from PySide6.QtWidgets import QSizePolicy, QWidget
from PySide6.QtWidgets import QVBoxLayout


class PolarWidget(QWidget):

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)

        self.plot = pg.PlotWidget()
        self.plot.setMinimumSize(360, 260)
        self.plot.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout.addWidget(self.plot)

        self.scatter = pg.ScatterPlotItem()

        self.plot.addItem(self.scatter)

    def update_polar(self, angles, distances):

        if len(angles) > 4000:
            step = max(1, len(angles) // 4000)
            angles = angles[::step]
            distances = distances[::step]

        self.scatter.setData(
            angles,
            distances
        )
