from PySide6.QtWidgets import *


class Card(QFrame):

    def __init__(self,title):

        super().__init__()

        self.setStyleSheet("""
        background:#1A2333;
        border-radius:12px;
        """)

        layout = QVBoxLayout(self)

        self.value = QLabel("0")

        self.value.setStyleSheet("""
        font-size:28px;
        color:#00E5FF;
        font-weight:bold;
        """)

        text = QLabel(title)

        text.setStyleSheet("""
        color:#9CA3AF;
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

        layout.addWidget(
            self.points
        )

        layout.addWidget(
            self.objects
        )

        layout.addWidget(
            self.fps
        )

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