import pyqtgraph as pg

from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import QVBoxLayout


class PolarWidget(QWidget):

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)

        self.plot = pg.PlotWidget()

        layout.addWidget(self.plot)

        self.scatter = pg.ScatterPlotItem()

        self.plot.addItem(self.scatter)

    def update_polar(self, angles, distances):

        self.scatter.setData(
            angles,
            distances
        )
