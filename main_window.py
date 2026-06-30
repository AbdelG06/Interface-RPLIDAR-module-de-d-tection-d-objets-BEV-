import time

from PySide6.QtWidgets import *
from PySide6.QtCore import QTimer

from bev_widget import BEVWidget
from polar_widget import PolarWidget
from controls_panel import ControlsPanel
from detections_table import DetectionsTable
from metrics_widget import MetricsWidget

from csv_player import CSVPlayer

from dbscan_detector import DBSCANDetector
from tracker import CentroidTracker

from alert_manager import AlertManager


class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "RPLIDAR BEV Detection"
        )

        self.resize(1600, 900)

        self.csv_player = CSVPlayer()

        self.detector = DBSCANDetector()

        self.tracker = CentroidTracker()

        self.alert_manager = AlertManager()

        self.timer = QTimer()

        self.timer.timeout.connect(
            self.update_scan
        )

        self.init_ui()

        self.last_time = time.time()

    def init_ui(self):

        central = QWidget()

        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)

        self.controls = ControlsPanel()

        self.bev = BEVWidget()

        self.polar = PolarWidget()

        self.table = DetectionsTable()

        self.metrics = MetricsWidget()

        left = QVBoxLayout()

        left.addWidget(self.controls)
        left.addWidget(self.metrics)

        right = QVBoxLayout()

        right.addWidget(self.bev, 3)
        right.addWidget(self.polar, 1)
        right.addWidget(self.table, 1)

        main_layout.addLayout(left, 1)
        main_layout.addLayout(right, 4)

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
            "Open CSV",
            "",
            "*.csv"
        )

        if filename:

            self.csv_player.load_file(
                filename
            )

    def start_scan(self):

        self.timer.start(100)

    def stop_scan(self):

        self.timer.stop()

    def update_scan(self):

        frame = self.csv_player.get_frame()

        if frame is None:
            return

        points = self.csv_player.polar_to_cartesian(
            frame
        )

        detections = self.detector.detect(points)

        detections = self.tracker.update(
            detections
        )

        alerts = self.alert_manager.check(
            detections
        )

        for a in alerts:
            print(a)

        self.bev.update_points(points)

        self.bev.update_detections(
            detections
        )

        self.polar.update_polar(
            frame["angle"],
            frame["distance"]
        )

        fps = 1.0 / (
                time.time()
                - self.last_time
        )

        self.last_time = time.time()

        self.metrics.update_metrics(
            len(points),
            len(detections),
            fps
        )

        self.table.update_table(
            detections
        )
