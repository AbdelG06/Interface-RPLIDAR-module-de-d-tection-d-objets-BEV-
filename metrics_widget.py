from PySide6.QtWidgets import *


class Card(QFrame):

    def __init__(self,title):

        super().__init__()

        self.setStyleSheet("""
        background:#111827;
        border:1px solid #223047;
        border-radius:14px;
        """)

        self.setMinimumHeight(70)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        self.value = QLabel("0")

        self.value.setStyleSheet("""
        font-size:20px;
        color:#00E5FF;
        font-weight:bold;
        """)

        text = QLabel(title)

        text.setStyleSheet("""
        color:#94A3B8;
        font-size:8.5pt;
        letter-spacing:1px;
        """)

        layout.addWidget(self.value)
        layout.addWidget(text)

    def set_value(self,value):

        self.value.setText(
            str(value)
        )


class MetricsWidget(QWidget):

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)

        self.points = Card(
            "POINTS"
        )

        self.objects = Card(
            "OBJECTS"
        )

        self.fps = Card(
            "FPS"
        )

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(self.points)
        layout.addWidget(self.objects)
        layout.addWidget(self.fps)

    def update_metrics(
        self,
        points,
        objects,
        fps
    ):

        self.points.set_value(points)

        self.objects.set_value(objects)

        self.fps.set_value(
            round(fps,1)
        )