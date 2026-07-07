from PySide6.QtWidgets import QSizePolicy, QVBoxLayout, QWidget, QPushButton


class ControlsPanel(QWidget):

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)

        self.connect_btn = QPushButton("Connect")

        self.start_btn = QPushButton("Start")

        self.stop_btn = QPushButton("Stop")

        self.import_btn = QPushButton("Load CSV")

        self.load_image_btn = QPushButton("Image Detector")

        self.demo_btn = QPushButton("Demo Mode")

        self.export_btn = QPushButton("Export CSV")

        self.export_json_btn = QPushButton("Export JSON")

        buttons = [
            self.connect_btn,
            self.start_btn,
            self.stop_btn,
            self.import_btn,
            self.load_image_btn,
            self.demo_btn,
            self.export_btn,
            self.export_json_btn,
        ]

        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)

        for button in buttons:
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            button.setMinimumHeight(38)
            button.setStyleSheet(
                """
                QPushButton {
                    text-align:left;
                    padding-left:14px;
                    font-size:9.7pt;
                    background:#111827;
                    border:1px solid #223047;
                    border-radius:12px;
                    color:#E5E7EB;
                }
                QPushButton:hover {
                    background:#172033;
                    border:1px solid #00E5FF;
                }
                """
            )
            layout.addWidget(button)

        layout.addSpacing(6)

        layout.addStretch()