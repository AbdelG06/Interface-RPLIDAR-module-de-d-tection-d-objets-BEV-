import pyqtgraph as pg


class BEVOverlay:

    def __init__(self, plot_widget):

        self.plot_widget = plot_widget

        self.items = []

    def clear(self):

        for item in self.items:

            self.plot_widget.removeItem(item)

        self.items.clear()

    def draw_detections(self, detections):

        self.clear()

        for d in detections:

            rect = pg.QtWidgets.QGraphicsRectItem(
                d.xmin,
                d.ymin,
                d.width,
                d.height
            )

            rect.setPen(pg.mkPen("red", width=2))

            self.plot_widget.addItem(rect)

            text = pg.TextItem(
                text=f"ID {d.object_id}",
                color="yellow"
            )

            text.setPos(d.x, d.y)

            self.plot_widget.addItem(text)

            self.items.append(rect)
            self.items.append(text)