from PySide6.QtWidgets import *


class MetricsWidget(QWidget):

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)

        self.points_label = QLabel("Points : 0")
        self.objects_label = QLabel("Objects : 0")
        self.fps_label = QLabel("FPS : 0")

        layout.addWidget(self.points_label)
        layout.addWidget(self.objects_label)
        layout.addWidget(self.fps_label)

    def update_metrics(
            self,
            point_count,
            object_count,
            fps):

        self.points_label.setText(
            f"Points : {point_count}"
        )

        self.objects_label.setText(
            f"Objects : {object_count}"
        )

        self.fps_label.setText(
            f"FPS : {fps:.1f}"
        )