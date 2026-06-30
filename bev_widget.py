import pyqtgraph as pg

from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import QVBoxLayout


class BEVWidget(QWidget):

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)

        self.plot = pg.PlotWidget()

        layout.addWidget(self.plot)

        self.plot.setBackground("#0B0F15")

        self.plot.setAspectLocked(True)
        self.plot.setMouseEnabled(x=True, y=True)
        self.plot.enableAutoRange(False)


        self.plot.hideAxis("bottom")
        self.plot.hideAxis("left")

        self.plot.showGrid(
            x=True,
            y=True,
            alpha=0.30
        )

        self.plot.setXRange(-12,12)
        self.plot.setYRange(-12,12)

        # radar rings

        for r in [2,4,6,8,10,12]:

            circle = pg.QtWidgets.QGraphicsEllipseItem(
                -r,
                -r,
                r*2,
                r*2
            )

            circle.setPen(
                pg.mkPen(
                    color="#233248",
                    width=1
                )
            )

            self.plot.addItem(circle)

        self.scatter = pg.ScatterPlotItem(
            size=9,
            brush="#00E5FF",
            pen=None
        )

        self.plot.addItem(self.scatter)

        # center sensor

        self.sensor = pg.ScatterPlotItem(
            size=18,
            brush="#00FF95"
        )

        self.sensor.setData([0],[0])

        self.plot.addItem(
            self.sensor
        )

    def update_points(self, points):

        if len(points) == 0:
            return

        self.scatter.setData(
        x=points[:,0],
         y=points[:,1]
    )

        