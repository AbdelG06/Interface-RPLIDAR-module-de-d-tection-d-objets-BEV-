from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout, QWidget


class Card(QFrame):
    def __init__(self, title):
        super().__init__()

        self.setStyleSheet(
            """
            QFrame {
                background:#111827;
                border:1px solid #223047;
                border-radius:10px;
            }
            QLabel#MetricValue {
                font-size:22px;
                color:#00E5FF;
                font-weight:900;
            }
            QLabel#MetricTitle {
                color:#94A3B8;
                font-size:8.5pt;
                font-weight:800;
            }
            """
        )
        self.setMinimumHeight(72)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(2)

        self.value = QLabel("0")
        self.value.setObjectName("MetricValue")

        text = QLabel(title)
        text.setObjectName("MetricTitle")

        layout.addWidget(self.value)
        layout.addWidget(text)

    def set_value(self, value):
        self.value.setText(str(value))


class MetricsWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        self.points = Card("POINTS")
        self.objects = Card("OBJECTS")
        self.fps = Card("FPS")

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout.addWidget(self.points)
        layout.addWidget(self.objects)
        layout.addWidget(self.fps)

    def update_metrics(self, points, objects, fps):
        self.points.set_value(points)
        self.objects.set_value(objects)
        self.fps.set_value(round(fps, 1))