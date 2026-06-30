import pyqtgraph as pg

from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import QVBoxLayout


class BEVWidget(QWidget):

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)

        self.plot = pg.PlotWidget()

        layout.addWidget(self.plot)

        self.plot.setBackground("#202124")

        self.plot.showGrid(
            x=True,
            y=True
        )

        self.plot.setAspectLocked(True)

        self.scatter = pg.ScatterPlotItem(
            size=5,
            brush="lime"
        )

        self.plot.addItem(self.scatter)

    def update_points(self, points):

        self.scatter.setData(
            points[:, 0],
            points[:, 1]
        )
