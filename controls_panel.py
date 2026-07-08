from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget, QPushButton


class ControlsPanel(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("COMMAND CENTER")
        title.setStyleSheet(
            """
            color:#00E5FF;
            font-size:9pt;
            font-weight:800;
            padding:0 2px 4px 2px;
            """
        )
        layout.addWidget(title)

        self.connect_btn = QPushButton("Connecter capteur")
        self.start_btn = QPushButton("Demarrer scan")
        self.stop_btn = QPushButton("Arreter")
        self.import_btn = QPushButton("Importer CSV")
        self.load_image_btn = QPushButton("Analyser image")
        self.load_video_btn = QPushButton("Analyser video")
        self.demo_btn = QPushButton("Mode demo")
        self.export_btn = QPushButton("Exporter CSV")

        buttons = [
            self.connect_btn,
            self.start_btn,
            self.stop_btn,
            self.import_btn,
            self.load_image_btn,
            self.load_video_btn,
            self.demo_btn,
            self.export_btn,
        ]

        for button in buttons:
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            button.setMinimumHeight(42)
            button.setStyleSheet(
                """
                QPushButton {
                    text-align:left;
                    padding-left:14px;
                    padding-right:14px;
                    font-size:9.5pt;
                    font-weight:700;
                    background:#111827;
                    border:1px solid #223047;
                    border-radius:10px;
                    color:#E5E7EB;
                }
                QPushButton:hover {
                    background:#172033;
                    border:1px solid #00E5FF;
                    color:#FFFFFF;
                }
                QPushButton:pressed {
                    background:#0F172A;
                    border:1px solid #0066FF;
                }
                """
            )
            layout.addWidget(button)

        layout.addStretch()