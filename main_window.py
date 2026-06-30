from PySide6.QtWidgets import *
from PySide6.QtCore import *

import time

from bev_widget import BEVWidget
from polar_widget import PolarWidget
from controls_panel import ControlsPanel
from detections_table import DetectionsTable
from metrics_widget import MetricsWidget

from csv_player import CSVPlayer
from dbscan_detector import DBSCANDetector


class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "RPLIDAR BEV Detection"
        )

        self.resize(1800, 1000)

        self.csv_player = CSVPlayer()

        self.detector = DBSCANDetector()

        self.timer = QTimer()

        self.timer.timeout.connect(
            self.update_scan
        )

        self.last_time = time.time()

        self.build_ui()

    def build_ui(self):

        central = QWidget()

        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)

        # HEADER

        header = QFrame()

        header.setFixedHeight(70)

        header.setStyleSheet("""
        background:#111827;
        border-radius:15px;
        """)

        h = QHBoxLayout(header)

        title = QLabel(
            "RPLIDAR BEV DETECTION SYSTEM"
        )

        title.setStyleSheet("""
        color:#00E5FF;
        font-size:24px;
        font-weight:bold;
        """)

        status = QLabel(
            "● ONLINE"
        )

        status.setStyleSheet("""
        color:#00FF95;
        font-weight:bold;
        """)

        h.addWidget(title)

        h.addStretch()

        h.addWidget(status)

        main_layout.addWidget(header)

        # BODY

        body = QHBoxLayout()

        main_layout.addLayout(body)

        left_panel = QFrame()

        left_panel.setFixedWidth(280)

        left_panel.setStyleSheet("""
        background:#111827;
        border-radius:15px;
        """)

        left_layout = QVBoxLayout(left_panel)

        self.controls = ControlsPanel()

        self.metrics = MetricsWidget()

        left_layout.addWidget(self.controls)

        left_layout.addWidget(self.metrics)

        left_layout.addStretch()

        body.addWidget(left_panel)

        right_panel = QVBoxLayout()

        self.bev = BEVWidget()

        self.polar = PolarWidget()

        self.table = DetectionsTable()

        right_panel.addWidget(
            self.bev,
            5
        )

        splitter = QSplitter(
            Qt.Horizontal
        )

        splitter.addWidget(
            self.polar
        )

        splitter.addWidget(
            self.table
        )

        splitter.setSizes(
            [300, 700]
        )

        right_panel.addWidget(
            splitter,
            2
        )

        body.addLayout(
            right_panel
        )

        self.controls.import_btn.clicked.connect(
            self.import_csv
        )

        self.controls.start_btn.clicked.connect(
            self.start_scan
        )

        self.controls.stop_btn.clicked.connect(
            self.stop_scan
        )

    def import_csv(self):

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Import CSV",
            "",
            "CSV Files (*.csv)"
        )

        if filename:

            self.csv_player.load_file(
                filename
            )

            QMessageBox.information(
                self,
                "CSV",
                "CSV chargé avec succès"
            )

    def start_scan(self):

        print("START")

        self.timer.start(100)

    def stop_scan(self):

        print("STOP")

        self.timer.stop()

    def update_scan(self):

        frame = self.csv_player.get_frame()

        if frame is None:
            return

        points = self.csv_player.polar_to_cartesian(
            frame
        )

        detections = self.detector.detect(
            points
        )

        # BEV

        self.bev.update_points(
            points
        )

        # POLAR

        self.polar.update_polar(
            frame["angle"],
            frame["distance"]
        )

        # TABLE

        self.table.update_table(
            detections
        )

        # KPI

        fps = 1 / max(
            0.001,
            time.time() - self.last_time
        )

        self.last_time = time.time()

        self.metrics.update_metrics(
            len(points),
            len(detections),
            fps
        )