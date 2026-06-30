from PySide6.QtWidgets import *

class ControlsPanel(QWidget):

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)

        self.connect_btn = QPushButton("Connect")

        self.start_btn = QPushButton("Start Scan")

        self.stop_btn = QPushButton("Stop Scan")

        self.import_btn = QPushButton("Import CSV")

        self.export_btn = QPushButton("Export CSV")

        self.export_json_btn = QPushButton("Export JSON")

        layout.addWidget(self.connect_btn)
        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)

        layout.addSpacing(20)

        layout.addWidget(self.import_btn)
        layout.addWidget(self.export_btn)
        layout.addWidget(self.export_json_btn)

        layout.addStretch()