from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import logging
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from alert_manager import AlertManager
from bev_widget import BEVWidget
from controls_panel import ControlsPanel
from csv_player import CSVPlayer
from dbscan_detector import DBSCANDetector
from detections_table import DetectionsTable
from image_detector_window import ImageDetectorWindow
from lidar_3d_widget import Lidar3DWidget
from metrics_widget import MetricsWidget
from object_tracker import ObjectTracker, TrackedDetection
from polar_widget import PolarWidget
from video_detector_window import VideoDetectorWindow
from yolo_detector import YOLODetector


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Radar Vision Control")
        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            geometry = screen.availableGeometry()
            self.resize(max(1280, int(geometry.width() * 0.92)), max(820, int(geometry.height() * 0.90)))
        else:
            self.resize(1600, 980)

        self.config = self._load_config()
        self.csv_player = CSVPlayer()
        self.detector = DBSCANDetector(
            eps=self.config["dbscan_eps"],
            min_samples=self.config["dbscan_min_samples"],
        )
        self.yolo_detector = YOLODetector()
        self.tracker = ObjectTracker(max_distance=self.config["tracking_distance_threshold"], max_missed=8)
        self.alert_manager = AlertManager(safety_radius=self.config["safety_radius"])

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_scene)
        self.refresh_interval_ms = max(50, int(1000 / self.config["display_refresh_hz"]))

        self.last_time = time.time()
        self.mode = "demo"
        self.demo_tick = 0.0
        self.current_points = np.zeros((0, 3), dtype=float)
        self.current_detections: list[TrackedDetection] = []
        self.demo_objects = self._build_demo_objects()
        self.image_detector_window = None
        self.video_detector_window = None

        self.build_ui()
        self._set_mode("demo")

    def _load_config(self):
        defaults = {
            "display_refresh_hz": 10,
            "dbscan_eps": 0.30,
            "dbscan_min_samples": 4,
            "safety_radius": 2.0,
            "tracking_distance_threshold": 1.2,
        }

        config_path = Path(__file__).with_name("config.json")
        if config_path.exists():
            try:
                with config_path.open("r", encoding="utf-8") as handle:
                    loaded = json.load(handle)
                defaults.update(loaded)
            except Exception as exc:
                logging.exception("Failed to load config.json: %s", exc)

        return defaults

    def _screen_metrics(self):
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return self.width(), self.height()

        geometry = screen.availableGeometry()
        return geometry.width(), geometry.height()

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)
        central.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        header = QFrame()
        header.setObjectName("HeaderCard")
        header.setStyleSheet(
            """
            QFrame#HeaderCard {
                background:#0F172A;
                border:1px solid #223047;
                border-radius:14px;
            }
            """
        )
        header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        header.setMinimumHeight(78)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 14, 20, 14)

        title_box = QVBoxLayout()
        title = QLabel("RADAR VISION CONTROL")
        title.setStyleSheet("font-size:24px;font-weight:900;color:#00E5FF;")
        subtitle = QLabel("LiDAR + Camera + YOLOv8 + Tracking temps reel")
        subtitle.setStyleSheet("color:#94A3B8;font-size:10pt;font-weight:600;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.mode_label = QLabel("MODE: DEMO")
        self.mode_label.setStyleSheet(
            """
            color:#00FF95;
            font-weight:800;
            font-size:10pt;
            padding:7px 13px;
            background:#0B0F15;
            border:1px solid #223047;
            border-radius:10px;
            """
        )
        self.status_label = QLabel(self._status_text())
        self.status_label.setStyleSheet("color:#94A3B8;font-size:9.5pt;font-weight:600;padding:4px 0;")
        status_box = QVBoxLayout()
        status_box.addWidget(self.mode_label, alignment=Qt.AlignRight)
        status_box.addWidget(self.status_label, alignment=Qt.AlignRight)
        header_layout.addLayout(status_box)

        main_layout.addWidget(header)

        body_splitter = QSplitter(Qt.Horizontal)
        body_splitter.setChildrenCollapsible(False)
        body_splitter.setHandleWidth(10)
        body_splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.body_splitter = body_splitter

        left_panel = QFrame()
        left_panel.setObjectName("SideCard")
        left_panel.setStyleSheet(
            """
            QFrame#SideCard {
                background:#0D1422;
                border:1px solid #223047;
                border-radius:14px;
            }
            """
        )
        left_panel.setMinimumWidth(300)
        left_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(14, 14, 14, 14)
        left_layout.setSpacing(12)

        self.controls = ControlsPanel()
        self.metrics = MetricsWidget()
        self.alert_card = self._build_text_card("ALERTE PROXIMITE", "Aucune alerte")
        self.model_card = self._build_text_card("YOLO", self.yolo_detector.status.message)

        left_layout.addWidget(self.controls)
        left_layout.addWidget(self.metrics)
        left_layout.addWidget(self.model_card)
        left_layout.addWidget(self.alert_card)
        left_layout.addStretch()

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.NoFrame)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        left_scroll.setWidget(left_panel)

        right_panel = QWidget()
        right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(14)

        scene_splitter = QSplitter(Qt.Horizontal)
        scene_splitter.setChildrenCollapsible(False)
        scene_splitter.setHandleWidth(10)
        scene_splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scene_splitter = scene_splitter
        self.bev = BEVWidget()
        self.lidar_3d = Lidar3DWidget()
        scene_splitter.addWidget(self.bev)
        scene_splitter.addWidget(self.lidar_3d)
        scene_splitter.setStretchFactor(0, 6)
        scene_splitter.setStretchFactor(1, 5)

        lower_splitter = QSplitter(Qt.Horizontal)
        lower_splitter.setChildrenCollapsible(False)
        lower_splitter.setHandleWidth(10)
        lower_splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.lower_splitter = lower_splitter
        self.polar = PolarWidget()
        self.table = DetectionsTable()
        lower_splitter.addWidget(self.polar)
        lower_splitter.addWidget(self.table)
        lower_splitter.setStretchFactor(0, 4)
        lower_splitter.setStretchFactor(1, 5)

        right_layout.addWidget(scene_splitter, 6)
        right_layout.addWidget(lower_splitter, 4)

        body_splitter.addWidget(left_scroll)
        body_splitter.addWidget(right_panel)
        body_splitter.setStretchFactor(0, 1)
        body_splitter.setStretchFactor(1, 5)

        main_layout.addWidget(body_splitter)

        self.controls.connect_btn.clicked.connect(self.connect_sensor)
        self.controls.start_btn.clicked.connect(self.start_scan)
        self.controls.stop_btn.clicked.connect(self.stop_scan)
        self.controls.import_btn.clicked.connect(self.import_csv)
        self.controls.load_image_btn.clicked.connect(self.open_image_detector)
        self.controls.load_video_btn.clicked.connect(self.open_video_detector)
        self.controls.demo_btn.clicked.connect(self.activate_demo_mode)
        self.controls.export_btn.clicked.connect(self.export_csv)

        self._apply_splitter_sizes()

    def _build_text_card(self, title_text: str, value_text: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            """
            QFrame {
                background:#111827;
                border:1px solid #223047;
                border-radius:10px;
            }
            QLabel#CardTitle {
                color:#00E5FF;
                font-size:8.5pt;
                font-weight:800;
            }
            QLabel#CardValue {
                color:#E5E7EB;
                font-size:10pt;
                font-weight:600;
            }
            """
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)
        title = QLabel(title_text)
        title.setObjectName("CardTitle")
        value = QLabel(value_text)
        value.setObjectName("CardValue")
        value.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(value)
        card.value_label = value
        return card

    def _status_text(self) -> str:
        return f"Refresh: {self.config['display_refresh_hz']} Hz | {self.yolo_detector.status.message}"

    def _set_mode(self, mode: str):
        self.mode = mode
        self.mode_label.setText(f"MODE: {mode.upper()}")

        if hasattr(self, "bev"):
            self.bev.set_points_visible(mode != "demo")

        if mode == "demo":
            color = "#00FF95"
        elif mode == "image":
            color = "#FFD166"
        else:
            color = "#60A5FA"

        self.mode_label.setStyleSheet(
            f"""
            color:{color};
            font-weight:800;
            font-size:10pt;
            padding:7px 13px;
            background:#0B0F15;
            border:1px solid #223047;
            border-radius:10px;
            """
        )

    def connect_sensor(self):
        QMessageBox.information(
            self,
            "Connect",
            "Cette version fonctionne en mode démonstration / CSV / image. Le capteur réel peut être branché plus tard sans casser l'architecture.",
        )

    def import_csv(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Import CSV", "", "CSV Files (*.csv)")
        if not filename:
            return

        self.csv_player.load_file(filename)
        self.tracker.reset()
        self._set_mode("csv")
        self.status_label.setText(f"CSV loaded: {Path(filename).name}")
        QMessageBox.information(self, "CSV", "CSV chargé avec succès")

    def open_image_detector(self):
        if self.image_detector_window is None:
            self.image_detector_window = ImageDetectorWindow()

        self.image_detector_window.show()
        self.image_detector_window.raise_()
        self.image_detector_window.activateWindow()

    def open_video_detector(self):
        if self.video_detector_window is None:
            self.video_detector_window = VideoDetectorWindow()

        self.video_detector_window.show()
        self.video_detector_window.raise_()
        self.video_detector_window.activateWindow()

    def activate_demo_mode(self):
        self.tracker.reset()
        self.demo_objects = self._build_demo_objects()
        self._set_mode("demo")
        self.status_label.setText("Demo mode ready")
        self.timer.start(self.refresh_interval_ms)
        self.update_scene()

    def start_scan(self):
        if self.mode == "image":
            self.process_image_frame()
            return

        self.timer.start(self.refresh_interval_ms)
        self.update_scene()

    def stop_scan(self):
        self.timer.stop()
        self.status_label.setText("Acquisition stopped")

    def update_scene(self):
        if self.mode == "csv":
            points, detections = self._update_from_csv()
            self._present_scene(points, detections, None)
        elif self.mode == "demo":
            points, detections = self._update_from_demo()
            self._present_scene(points, detections, None)

    def _update_from_csv(self):
        frame = self.csv_player.get_frame()
        if frame is None:
            return np.zeros((0, 3), dtype=float), []

        cartesian = self.csv_player.polar_to_cartesian(frame)
        points = np.column_stack([cartesian, np.zeros((len(cartesian), 1), dtype=float)])

        raw_detections = self.detector.detect(cartesian)
        detections = [self._convert_cluster_detection(detection) for detection in raw_detections]
        detections = self.tracker.update(detections)

        self.polar.update_polar(frame["angle"].to_numpy(), frame["distance"].to_numpy())
        return points, detections

    def _update_from_demo(self):
        points = []
        detections = []
        rng = np.random.default_rng()
        self.demo_tick += 0.12

        # Ego vehicle and LiDAR-style reference geometry.
        ego_center = np.array([0.0, 0.0, 1.0], dtype=float)

        # Ego vehicle silhouette so the demo feels like a real mounted LiDAR view.
        body_x = np.linspace(-2.35, 2.35, 42)
        body_y = np.linspace(-1.0, 1.0, 18)
        body_z = np.linspace(0.10, 0.92, 20)
        bx, by, bz = np.meshgrid(body_x, body_y, body_z)
        ego_vehicle = np.column_stack([bx.ravel(), by.ravel(), bz.ravel()])
        ego_vehicle[:, 2] += 0.06 * np.sin(self.demo_tick * 1.5 + ego_vehicle[:, 0] * 0.8)
        points.append(ego_vehicle)

        roof_x = np.linspace(-1.25, 1.25, 30)
        roof_y = np.linspace(-0.8, 0.8, 16)
        roof_z = np.linspace(0.88, 1.65, 16)
        rx, ry, rz = np.meshgrid(roof_x, roof_y, roof_z)
        roof = np.column_stack([rx.ravel(), ry.ravel(), rz.ravel()])
        roof[:, 2] += 0.04 * np.cos(self.demo_tick * 2.0)
        points.append(roof)

        windshield_x = np.linspace(-1.15, 1.15, 20)
        windshield_z = np.linspace(0.60, 1.55, 18)
        wx, wz = np.meshgrid(windshield_x, windshield_z)
        windshield = np.column_stack([
            wx.ravel(),
            np.full(wx.size, 0.86),
            wz.ravel(),
        ])
        points.append(windshield)

        # Road surface with lane-like markings.
        x_grid = np.linspace(-18.0, 42.0, 96)
        y_grid = np.linspace(-15.0, 15.0, 70)
        xx, yy = np.meshgrid(x_grid, y_grid)
        road = np.column_stack(
            [
                xx.ravel(),
                yy.ravel(),
                rng.normal(0.02, 0.018, size=xx.size),
            ]
        )
        road_mask = (np.abs(yy.ravel()) < 12.0) & (xx.ravel() > 3.0)
        road_mask &= ~((xx.ravel() ** 2) / 12.0 + (yy.ravel() ** 2) / 10.0 < 1.0)
        road = road[road_mask]
        points.append(road)

        # Scan-like horizontal slices across the road and buildings.
        sweep_y = np.linspace(-13.0, 13.0, 54)
        for sweep_index, y_value in enumerate(sweep_y):
            if abs(y_value) < 1.2:
                x_start, x_end = -1.0, 40.0
            else:
                x_start, x_end = 3.0, 40.0
            sweep_x = np.linspace(x_start, x_end, 220)
            sweep_z = 0.02 + 0.014 * np.sin(self.demo_tick * 0.55 + sweep_index * 0.10)
            sweep = np.column_stack([
                sweep_x,
                np.full_like(sweep_x, y_value),
                np.full_like(sweep_x, sweep_z),
            ])
            if abs(y_value) > 8.4 or abs(y_value) < 1.0 or sweep_index % 3 == 0:
                points.append(sweep)

        lane_y = [-3.5, 0.0, 3.5]
        for lane_index, lane_pos in enumerate(lane_y):
            lane_x = np.linspace(-1.0, 36.0, 190)
            lane_z = np.full_like(lane_x, 0.03 + 0.01 * np.sin(self.demo_tick + lane_index))
            lane = np.column_stack([lane_x, np.full_like(lane_x, lane_pos), lane_z])
            points.append(lane)

        # Arc rings around the ego vehicle to echo a LiDAR scan overlay.
        ring_points = []
        for radius in [2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 17.5]:
            angles = np.linspace(0.0, 2.0 * np.pi, 220)
            z = np.full_like(angles, 0.04 + radius * 0.002)
            ring = np.column_stack([
                ego_center[0] + radius * np.cos(angles),
                ego_center[1] + radius * np.sin(angles),
                z,
            ])
            ring_points.append(ring)
        points.extend(ring_points)

        # Simple city blocks on both sides of the road.
        for side in (-1, 1):
            for block_x in [8.0, 18.0, 30.0]:
                block_width = 4.0 + 1.0 * (block_x / 30.0)
                block_depth = 3.0 + 0.5 * rng.uniform(0.6, 1.4)
                block_height = 6.0 + 6.0 * rng.uniform(0.3, 1.0)

                wall_y = side * (9.5 + rng.uniform(0.0, 2.5))
                xs = np.linspace(block_x, block_x + block_width, 26)
                zs = np.linspace(0.0, block_height, 34)
                xw, zw = np.meshgrid(xs, zs)
                yw = np.full_like(xw, wall_y)
                wall = np.column_stack([xw.ravel(), yw.ravel(), zw.ravel()])
                points.append(wall)

                # Vertical facade scan lines.
                facade_y = np.linspace(wall_y - block_depth * 0.5, wall_y + block_depth * 0.5, 12)
                for y_value in facade_y:
                    points.append(
                        np.column_stack([
                            np.linspace(block_x, block_x + block_width, 120),
                            np.full(120, y_value),
                            np.linspace(0.0, block_height, 120),
                        ])
                    )

        canopy_x = np.linspace(4.0, 38.0, 50)
        canopy_y = np.linspace(-12.5, 12.5, 26)
        cx, cy = np.meshgrid(canopy_x, canopy_y)
        canopy_z = 9.0 + 1.5 * np.sin(cx * 0.15 + self.demo_tick * 0.4) + 1.0 * np.cos(cy * 0.30)
        canopy = np.column_stack([cx.ravel(), cy.ravel(), canopy_z.ravel()])
        canopy = canopy[(np.abs(canopy[:, 1]) > 6.0) | (canopy[:, 0] > 12.0)]
        points.append(canopy)

        # Utility poles / trees for extra vertical LiDAR structure.
        for pole_x in [-8.0, -2.0, 6.0, 14.0, 24.0, 34.0]:
            pole_y = 7.8 * np.sign(np.sin(pole_x * 0.5))
            theta = np.linspace(0.0, 2.0 * np.pi, 18)
            z = np.linspace(0.0, 6.0, 22)
            tt, zz = np.meshgrid(theta, z)
            radius = 0.18 + 0.03 * np.sin(self.demo_tick + pole_x)
            pole = np.column_stack([
                pole_x + radius * np.cos(tt).ravel(),
                pole_y + radius * np.sin(tt).ravel(),
                zz.ravel(),
            ])
            points.append(pole)

        # Distant skyline / overpass points for the cinematic LiDAR background.
        skyline_x = np.linspace(-10.0, 38.0, 48)
        skyline_y = np.linspace(-13.0, 13.0, 22)
        sx, sy = np.meshgrid(skyline_x, skyline_y)
        skyline_z = 5.0 + 5.0 * np.exp(-((sx - 18.0) ** 2) / 180.0) + 2.0 * np.sin(sy * 0.35 + self.demo_tick)
        skyline = np.column_stack([sx.ravel(), sy.ravel(), skyline_z.ravel()])
        skyline = skyline[(np.abs(skyline[:, 1]) > 7.5) | (skyline[:, 0] > 12.0)]
        points.append(skyline)

        for object_state in self.demo_objects:
            position = object_state["position"]
            velocity = object_state["velocity"]
            size = object_state["size"]
            class_name = object_state["class_name"]

            position[:] = position + velocity
            for axis in (0, 1):
                if position[axis] > 14.0 or position[axis] < -14.0:
                    velocity[axis] *= -1.0
                    position[axis] = float(np.clip(position[axis], -14.0, 14.0))

            sample_count = object_state["sample_count"]
            if class_name == "truck":
                local_points = self._sample_truck_points(rng, position, size, sample_count)
            elif class_name == "car":
                local_points = self._sample_vehicle_points(rng, position, size, sample_count)
            elif class_name == "person":
                local_points = self._sample_person_points(rng, position, size, sample_count)
            elif class_name == "bicycle":
                local_points = self._sample_bicycle_points(rng, position, size, sample_count)
            else:
                local_points = self._sample_obstacle_points(rng, position, size, sample_count)
            points.append(local_points)

            edge_x = np.linspace(position[0] - size[0] / 2.0, position[0] + size[0] / 2.0, 12)
            edge_y = np.linspace(position[1] - size[1] / 2.0, position[1] + size[1] / 2.0, 10)
            ex, ey = np.meshgrid(edge_x, edge_y)
            top = np.column_stack([ex.ravel(), ey.ravel(), np.full(ex.size, position[2] + size[2] * 0.92)])
            if class_name == "truck":
                roof_x = np.linspace(position[0] - 0.32 * size[0], position[0] + 0.58 * size[0], 24)
                roof = np.column_stack([roof_x, np.full_like(roof_x, position[1]), np.full_like(roof_x, position[2] + 0.84 * size[2])])
                points.append(roof)
            points.append(top)

            width, height, depth = size
            detection = TrackedDetection(
                name=object_state["name"],
                class_name=object_state["class_name"],
                confidence=object_state["confidence"],
                x=float(position[0]),
                y=float(position[1]),
                z=float(position[2]),
                distance=float(np.hypot(position[0], position[1])),
                angle=float(np.degrees(np.arctan2(position[1], position[0]))),
                width=float(width),
                height=float(height),
                depth=float(depth),
                xmin=float(position[0] - width / 2.0),
                ymin=float(position[1] - height / 2.0),
                xmax=float(position[0] + width / 2.0),
                ymax=float(position[1] + height / 2.0),
                zmin=float(max(0.0, position[2] - depth / 2.0)),
                zmax=float(position[2] + depth / 2.0),
                point_count=sample_count,
                color=object_state["color"],
                source="demo",
            )
            detections.append(detection)

        background = rng.uniform(low=[-12.0, -15.0, 0.0], high=[42.0, 15.0, 0.20], size=(120, 3))
        background = background[(background[:, 0] > 3.0) & (~((background[:, 0] ** 2) / 12.0 + (background[:, 1] ** 2) / 10.0 < 1.0))]
        points.append(background)

        # Sensor noise to make the frame feel more like live LiDAR.
        noise = rng.normal(loc=[0.0, 0.0, 0.0], scale=[0.22, 0.22, 0.012], size=(42, 3))
        noise[:, 0] += 4.0 * np.cos(self.demo_tick)
        noise[:, 1] += 4.0 * np.sin(self.demo_tick * 0.7)
        noise[:, 2] = np.clip(noise[:, 2] + 0.03, 0.0, 0.12)
        points.append(noise)

        stacked_points = np.vstack(points) if points else np.zeros((0, 3), dtype=float)
        detections = self.tracker.update(detections)
        self.polar.update_polar(
            np.degrees(np.arctan2(stacked_points[:, 1], stacked_points[:, 0])) if len(stacked_points) else np.array([]),
            np.hypot(stacked_points[:, 0], stacked_points[:, 1]) if len(stacked_points) else np.array([]),
        )
        return stacked_points, detections

    def _build_demo_objects(self):
        return [
            {
                "name": "Car",
                "class_name": "car",
                "confidence": 0.95,
                "position": np.array([10.0, 1.8, 0.7], dtype=float),
                "velocity": np.array([-0.05, 0.01, 0.0], dtype=float),
                "size": np.array([4.4, 1.9, 1.5], dtype=float),
                "sample_count": 220,
                "color": "#34D399",
            },
            {
                "name": "Person",
                "class_name": "person",
                "confidence": 0.98,
                "position": np.array([4.0, -2.6, 0.9], dtype=float),
                "velocity": np.array([0.03, 0.015, 0.0], dtype=float),
                "size": np.array([0.7, 0.7, 1.7], dtype=float),
                "sample_count": 120,
                "color": "#22D3EE",
            },
            {
                "name": "Bicycle",
                "class_name": "bicycle",
                "confidence": 0.91,
                "position": np.array([15.0, -3.5, 0.7], dtype=float),
                "velocity": np.array([0.04, 0.025, 0.0], dtype=float),
                "size": np.array([1.8, 0.6, 1.4], dtype=float),
                "sample_count": 140,
                "color": "#FACC15",
            },
            {
                "name": "Truck",
                "class_name": "truck",
                "confidence": 0.93,
                "position": np.array([22.0, 4.5, 1.2], dtype=float),
                "velocity": np.array([-0.03, 0.015, 0.0], dtype=float),
                "size": np.array([6.0, 2.5, 3.0], dtype=float),
                "sample_count": 260,
                "color": "#FB923C",
            },
            {
                "name": "Obstacle",
                "class_name": "obstacle",
                "confidence": 0.88,
                "position": np.array([28.0, -6.5, 0.5], dtype=float),
                "velocity": np.array([0.0, 0.0, 0.0], dtype=float),
                "size": np.array([1.2, 1.2, 1.0], dtype=float),
                "sample_count": 100,
                "color": "#94A3B8",
            },
        ]

    @staticmethod
    def _sample_ellipse_shell(rng, center, radii, count, z_range=None):
        angles = rng.uniform(0.0, 2.0 * np.pi, count)
        if z_range is None:
            vertical = rng.uniform(-1.0, 1.0, count)
        else:
            vertical = rng.uniform(z_range[0], z_range[1], count)

        x = center[0] + np.cos(angles) * radii[0] * (0.78 + 0.22 * rng.random(count))
        y = center[1] + np.sin(angles) * radii[1] * (0.78 + 0.22 * rng.random(count))
        z = center[2] + vertical * radii[2]
        return np.column_stack([x, y, z])

    def _sample_truck_points(self, rng, position, size, count):
        center = np.array(position, dtype=float)
        length, width, height = map(float, size)

        cargo_center = center + np.array([0.45 * length, 0.0, 0.60 * height])
        cargo = self._sample_ellipse_shell(rng, cargo_center, [0.36 * length, 0.40 * width, 0.36 * height], int(count * 0.48))
        cargo[:, 0] = np.clip(cargo[:, 0], center[0] - 0.05 * length, center[0] + 1.0 * length)
        cargo[:, 2] += 0.08 * np.sin((cargo[:, 0] - center[0]) * 1.5)

        cab_center = center + np.array([-0.28 * length, 0.0, 0.50 * height])
        cab = self._sample_ellipse_shell(rng, cab_center, [0.22 * length, 0.28 * width, 0.28 * height], int(count * 0.28))
        cab[:, 0] = np.minimum(cab[:, 0], center[0] + 0.20 * length)
        cab[:, 2] += np.maximum(0.0, 0.10 * (cab_center[0] - cab[:, 0]))

        spine_x = np.linspace(center[0] - 0.52 * length, center[0] + 0.60 * length, int(count * 0.12))
        spine_y = center[1] + 0.06 * width * np.sin(np.linspace(0.0, 2.0 * np.pi, len(spine_x)))
        spine_z = np.full(len(spine_x), center[2] + 0.78 * height)
        spine = np.column_stack([spine_x, spine_y, spine_z])

        wheel_points = []
        for wx in (-0.34 * length, 0.36 * length):
            for wy in (-0.38 * width, 0.38 * width):
                wheel_center = np.array([center[0] + wx, center[1] + wy, center[2] + 0.12 * height])
                wheel_points.append(self._sample_ellipse_shell(rng, wheel_center, [0.11 * length, 0.11 * width, 0.08 * height], max(8, int(count * 0.02))))

        points = np.vstack([cargo, cab, spine, *wheel_points])
        if points.shape[0] > count:
            points = points[rng.choice(points.shape[0], count, replace=False)]
        return points

    def _sample_vehicle_points(self, rng, position, size, count):
        center = np.array(position, dtype=float)
        length, width, height = map(float, size)
        body_center = center + np.array([0.0, 0.0, 0.45 * height])

        roof = self._sample_ellipse_shell(rng, body_center + np.array([-0.02 * length, 0.0, 0.16 * height]), [0.30 * length, 0.34 * width, 0.24 * height], int(count * 0.46))
        hood = self._sample_ellipse_shell(rng, body_center + np.array([-0.20 * length, 0.0, -0.02 * height]), [0.18 * length, 0.28 * width, 0.16 * height], int(count * 0.20))
        tail = self._sample_ellipse_shell(rng, body_center + np.array([0.24 * length, 0.0, 0.02 * height]), [0.20 * length, 0.28 * width, 0.16 * height], int(count * 0.18))
        windows = self._sample_ellipse_shell(rng, body_center + np.array([-0.02 * length, 0.0, 0.18 * height]), [0.16 * length, 0.22 * width, 0.12 * height], int(count * 0.10))

        wheel_points = []
        for wx in (-0.28 * length, 0.28 * length):
            for wy in (-0.34 * width, 0.34 * width):
                wheel_center = np.array([center[0] + wx, center[1] + wy, center[2] + 0.10 * height])
                wheel_points.append(self._sample_ellipse_shell(rng, wheel_center, [0.10 * length, 0.10 * width, 0.08 * height], max(6, int(count * 0.015))))

        points = np.vstack([roof, hood, tail, windows, *wheel_points])
        if points.shape[0] > count:
            points = points[rng.choice(points.shape[0], count, replace=False)]
        return points

    def _sample_person_points(self, rng, position, size, count):
        center = np.array(position, dtype=float)
        radius_x = max(0.14, float(size[0]) * 0.30)
        radius_y = max(0.14, float(size[1]) * 0.30)
        height = max(1.0, float(size[2]))
        theta = rng.uniform(0.0, 2.0 * np.pi, count)
        z = rng.uniform(center[2], center[2] + height, count)
        wobble = 0.05 * np.sin(z * 4.0 + self.demo_tick * 1.6)
        x = center[0] + np.cos(theta) * (radius_x + wobble)
        y = center[1] + np.sin(theta) * (radius_y + wobble)
        return np.column_stack([x, y, z])

    def _sample_bicycle_points(self, rng, position, size, count):
        center = np.array(position, dtype=float)
        length, width, height = map(float, size)
        wheel_theta = np.linspace(0.0, 2.0 * np.pi, max(10, count // 7))
        front_wheel = np.column_stack([
            center[0] - 0.30 * length + 0.17 * np.cos(wheel_theta),
            center[1] - 0.18 * width + 0.17 * np.sin(wheel_theta),
            np.full_like(wheel_theta, center[2] + 0.12 * height),
        ])
        rear_wheel = np.column_stack([
            center[0] + 0.30 * length + 0.17 * np.cos(wheel_theta),
            center[1] + 0.18 * width + 0.17 * np.sin(wheel_theta),
            np.full_like(wheel_theta, center[2] + 0.12 * height),
        ])
        frame = np.column_stack([
            np.linspace(center[0] - 0.32 * length, center[0] + 0.34 * length, max(16, count // 3)),
            center[1] + 0.05 * np.sin(np.linspace(0.0, 3.0 * np.pi, max(16, count // 3))),
            np.linspace(center[2] + 0.18 * height, center[2] + 0.65 * height, max(16, count // 3)),
        ])
        handle = self._sample_ellipse_shell(rng, center + np.array([0.32 * length, 0.0, 0.72 * height]), [0.08 * length, 0.08 * width, 0.06 * height], max(8, count // 6))
        points = np.vstack([front_wheel, rear_wheel, frame, handle])
        if points.shape[0] > count:
            points = points[rng.choice(points.shape[0], count, replace=False)]
        return points

    def _sample_obstacle_points(self, rng, position, size, count):
        center = np.array(position, dtype=float)
        cloud = rng.normal(loc=center, scale=[float(size[0]) / 4.0, float(size[1]) / 4.0, float(size[2]) / 4.0], size=(count, 3))
        cloud[:, 2] = np.clip(cloud[:, 2], center[2], center[2] + float(size[2]))
        cloud[:, 0] += 0.08 * np.sin(cloud[:, 1] * 3.0)
        return cloud

    def _convert_cluster_detection(self, detection):
        width = max(0.4, float(getattr(detection, "width", 0.8)))
        height = max(0.4, float(getattr(detection, "height", 0.8)))
        depth = max(0.8, float(getattr(detection, "depth", 1.5)))

        return TrackedDetection(
            name="Object",
            class_name="cluster",
            confidence=1.0,
            x=float(getattr(detection, "x", 0.0)),
            y=float(getattr(detection, "y", 0.0)),
            z=0.0,
            distance=float(getattr(detection, "distance", 0.0)),
            angle=float(getattr(detection, "angle", 0.0)),
            width=width,
            height=height,
            depth=depth,
            xmin=float(getattr(detection, "xmin", -width / 2.0)),
            ymin=float(getattr(detection, "ymin", -height / 2.0)),
            xmax=float(getattr(detection, "xmax", width / 2.0)),
            ymax=float(getattr(detection, "ymax", height / 2.0)),
            zmin=0.0,
            zmax=depth,
            point_count=int(getattr(detection, "point_count", 0)),
            color="#60A5FA",
            source="lidar",
        )

    def _detections_to_points(self, detections):
        if not detections:
            return np.zeros((0, 3), dtype=float)

        return np.array([[detection.x, detection.y, detection.z] for detection in detections], dtype=float)

    def _present_scene(self, points, detections, image_path):
        self.current_points = points if points is not None else np.zeros((0, 3), dtype=float)
        self.current_detections = detections or []

        self.bev.update_scene(self.current_points, self.current_detections)
        self.lidar_3d.update_scene(self.current_points, self.current_detections)
        self.table.update_table(self.current_detections)

        if self.current_detections:
            labels = self.alert_manager.check(self.current_detections)
            if labels:
                self._set_alert_text(labels[0], danger=True)
            else:
                closest = min(self.current_detections, key=lambda detection: detection.distance)
                self._set_alert_text(
                    f"Aucune alerte de proximité | objet le plus proche: ID {closest.track_id} - {closest.name} - {closest.distance:.2f} m",
                    danger=False,
                )
        else:
            self._set_alert_text("Aucune alerte", danger=False)

        # Image detection lives in ImageDetectorWindow now.

        fps = 1.0 / max(0.001, time.time() - self.last_time)
        self.last_time = time.time()
        self.metrics.update_metrics(len(self.current_points), len(self.current_detections), fps)
        self.model_card.value_label.setText(self.yolo_detector.status.message)
        self.status_label.setText(self._status_text())

    def _set_alert_text(self, text: str, danger: bool):
        self.alert_card.value_label.setText(text)
        if danger:
            self.alert_card.value_label.setStyleSheet("color:#FF4D6D;font-size:11pt;font-weight:700;")
        else:
            self.alert_card.value_label.setStyleSheet("color:#E5E7EB;font-size:11pt;font-weight:600;")

    def export_csv(self):
        if not self.current_detections:
            QMessageBox.information(self, "Export CSV", "Aucune détection à exporter")
            return

        filename, _ = QFileDialog.getSaveFileName(self, "Export CSV", "detections.csv", "CSV Files (*.csv)")
        if not filename:
            return

        rows = []
        for detection in self.current_detections:
            rows.append(
                {
                    "id": detection.track_id,
                    "name": detection.name,
                    "class": detection.class_name,
                    "confidence": detection.confidence,
                    "distance": detection.distance,
                    "x": detection.x,
                    "y": detection.y,
                    "z": detection.z,
                    "color": detection.color,
                }
            )

        pd.DataFrame(rows).to_csv(filename, index=False)
        QMessageBox.information(self, "Export CSV", "Export CSV terminé")

    def _apply_splitter_sizes(self):
        if not hasattr(self, "body_splitter"):
            return

        window_width = max(1200, self.width())
        window_height = max(800, self.height())
        screen_width, screen_height = self._screen_metrics()

        left_ratio = 0.16 if screen_width >= 1900 else 0.20 if screen_width >= 1500 else 0.24
        left_width = max(260, int(window_width * left_ratio))
        right_width = max(800, window_width - left_width - 48)

        if self.mode == "demo":
            scene_ratio = 0.32
            lower_ratio = 0.28
        else:
            scene_ratio = 0.58 if screen_width >= 1700 else 0.52
            lower_ratio = 0.44 if screen_height >= 1000 else 0.50

        self.body_splitter.setSizes([left_width, right_width])
        self.scene_splitter.setSizes([int(right_width * scene_ratio), int(right_width * (1.0 - scene_ratio))])
        self.lower_splitter.setSizes([int(right_width * lower_ratio), int(right_width * (1.0 - lower_ratio))])

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_splitter_sizes()
