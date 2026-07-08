from __future__ import annotations

import math
from pathlib import Path

import cv2
import pandas as pd
from PySide6.QtCore import QObject, QPointF, QRectF, Qt, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from yolo_detector import YOLODetector


class VideoDetectionWorker(QObject):
    detections_ready = Signal(int, int, list)

    def __init__(self, detector: YOLODetector, inference_width: int):
        super().__init__()
        self.detector = detector
        self.inference_width = inference_width

    @Slot(int, int, object)
    def detect(self, video_token: int, frame_index: int, frame):
        detections = self.detector.detect_frame(frame, inference_width=self.inference_width)
        self.detections_ready.emit(video_token, frame_index, detections)


class DistanceRadarWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.detections = []
        self.max_distance = 45.0
        self.setMinimumHeight(230)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet("background:#0B0F15;border:1px solid #233248;border-radius:12px;")

    def set_detections(self, detections):
        self.detections = detections or []
        if self.detections:
            farthest = max(float(getattr(detection, "distance", 0.0)) for detection in self.detections)
            self.max_distance = max(12.0, min(60.0, farthest * 1.25))
        else:
            self.max_distance = 45.0
        self.update()

    @staticmethod
    def _qcolor(color: str, alpha: int = 255) -> QColor:
        qcolor = QColor(color if color else "#00E5FF")
        qcolor.setAlpha(alpha)
        return qcolor

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#0B0F15"))

        side = min(self.width() - 28, self.height() - 32)
        if side <= 20:
            painter.end()
            return

        center = QPointF(self.width() / 2.0, self.height() / 2.0 + 10)
        radius = side / 2.0
        radar_rect = QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2)

        painter.setPen(QPen(QColor("#1F3B57"), 1))
        painter.setBrush(QColor(0, 229, 255, 14))
        painter.drawEllipse(radar_rect)

        painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
        for ratio in (0.25, 0.5, 0.75, 1.0):
            ring_radius = radius * ratio
            ring_rect = QRectF(center.x() - ring_radius, center.y() - ring_radius, ring_radius * 2, ring_radius * 2)
            painter.setPen(QPen(QColor("#24445F"), 1))
            painter.drawEllipse(ring_rect)
            painter.setPen(QPen(QColor("#8FB4C7"), 1))
            painter.drawText(int(center.x() + 6), int(center.y() - ring_radius + 14), f"{self.max_distance * ratio:.0f}m")

        painter.setPen(QPen(QColor("#1F3B57"), 1))
        for angle in range(0, 360, 45):
            radians = math.radians(angle)
            end = QPointF(center.x() + radius * math.sin(radians), center.y() - radius * math.cos(radians))
            painter.drawLine(center, end)

        painter.setPen(QPen(QColor("#00E5FF"), 2))
        painter.setBrush(QColor("#00E5FF"))
        painter.drawEllipse(QRectF(center.x() - 5, center.y() - 5, 10, 10))
        painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
        painter.drawText(12, 18, "CAMERA")

        if not self.detections:
            painter.setPen(QPen(QColor("#64748B"), 1))
            painter.drawText(self.rect(), Qt.AlignCenter, "Aucun objet")
            painter.end()
            return

        for detection in self.detections:
            distance = float(getattr(detection, "distance", 0.0))
            angle = float(getattr(detection, "angle", 0.0))
            ratio = min(1.0, max(0.0, distance / max(1.0, self.max_distance)))
            radians = math.radians(angle)
            point = QPointF(center.x() + radius * ratio * math.sin(radians), center.y() - radius * ratio * math.cos(radians))
            color = self._qcolor(getattr(detection, "color", "#00E5FF"))

            painter.setPen(QPen(color, 2))
            painter.drawLine(center, point)
            painter.setBrush(color)
            painter.drawEllipse(QRectF(point.x() - 6, point.y() - 6, 12, 12))
            painter.setPen(QPen(Qt.white, 1))
            painter.drawText(int(point.x() + 8), int(point.y() - 8), f"{getattr(detection, 'name', 'Obj')} {distance:.1f}m")

        painter.end()

class VideoDetectorWindow(QMainWindow):
    detect_frame_requested = Signal(int, int, object)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Radar Vision Video")
        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            geometry = screen.availableGeometry()
            self.resize(max(1200, int(geometry.width() * 0.82)), max(800, int(geometry.height() * 0.84)))
        else:
            self.resize(1500, 950)

        self.detector = YOLODetector()
        self.video_path: str | None = None
        self.video_cap: cv2.VideoCapture | None = None
        self.current_frame = None
        self.current_pixmap: QPixmap | None = None
        self.current_detections = []
        self.is_playing = False
        self.frame_index = 0
        self.video_token = 0
        self.inference_pending = False
        self.detection_interval = 10
        self.inference_width = 416
        self.playback_interval_ms = 33
        self.frame_source_width = 1
        self.frame_source_height = 1

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._advance_frame)

        self.detection_thread = QThread(self)
        self.detection_worker = VideoDetectionWorker(self.detector, self.inference_width)
        self.detection_worker.moveToThread(self.detection_thread)
        self.detect_frame_requested.connect(self.detection_worker.detect)
        self.detection_worker.detections_ready.connect(self._handle_detections_ready)
        self.detection_thread.start()

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)

        header = QFrame()
        header.setStyleSheet(
            """
            QFrame {
                background:#0F172A;
                border:1px solid #223047;
                border-radius:14px;
            }
            """
        )
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 14, 20, 14)

        title_box = QVBoxLayout()
        title = QLabel("RADAR VISION VIDEO")
        title.setStyleSheet("font-size:24px;font-weight:900;color:#00E5FF;")
        subtitle = QLabel("Detection camera + distance estimee en temps reel")
        subtitle.setStyleSheet("color:#94A3B8;font-size:10pt;font-weight:600;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.status_label = QLabel(self.detector.status.message)
        self.status_label.setStyleSheet("color:#00FF95;font-weight:800;background:#0B0F15;border:1px solid #223047;border-radius:10px;padding:7px 12px;")
        header_layout.addWidget(self.status_label)

        root.addWidget(header)

        toolbar = QFrame()
        toolbar.setStyleSheet(
            """
            QFrame {
                background:#0D1422;
                border:1px solid #223047;
                border-radius:12px;
            }
            QPushButton {
                background:#111827;
                color:#E5E7EB;
                font-weight:800;
                border:1px solid #223047;
                border-radius:10px;
                padding:9px 13px;
            }
            QPushButton:hover {
                background:#172033;
                border:1px solid #00E5FF;
            }
            QPushButton:disabled {
                background:#1E293B;
                color:#64748B;
                border:1px solid #273449;
            }
            """
        )
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 10, 10, 10)

        self.load_btn = QPushButton("Importer video")
        self.play_btn = QPushButton("Lecture")
        self.play_btn.setEnabled(False)
        self.export_csv_btn = QPushButton("Export CSV")
        self.export_png_btn = QPushButton("Export PNG")

        toolbar_layout.addWidget(self.load_btn)
        toolbar_layout.addWidget(self.play_btn)
        toolbar_layout.addWidget(self.export_csv_btn)
        toolbar_layout.addWidget(self.export_png_btn)
        toolbar_layout.addStretch()
        root.addWidget(toolbar)

        content = QHBoxLayout()
        content.setSpacing(14)

        left_card = QFrame()
        left_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_card.setStyleSheet(
            """
            QFrame {
                background:#0D1422;
                border:1px solid #223047;
                border-radius:12px;
            }
            """
        )
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(10)

        self.preview = QLabel("Load a video to detect objects")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumSize(600, 440)
        self.preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.preview.setStyleSheet(
            """
            QLabel {
                background:#0B0F15;
                border:1px dashed #233248;
                border-radius:14px;
                color:#9CA3AF;
            }
            """
        )
        left_layout.addWidget(self.preview)

        right_card = QFrame()
        right_card.setMinimumWidth(360)
        right_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        right_card.setStyleSheet(
            """
            QFrame {
                background:#0D1422;
                border:1px solid #223047;
                border-radius:12px;
            }
            QLabel#SideTitle {
                color:#00E5FF;
                font-weight:800;
                font-size:12pt;
            }
            QListWidget {
                background:#0B0F15;
                border:1px solid #233248;
                border-radius:12px;
                padding:6px;
            }
            QListWidget::item {
                padding:10px;
                margin:4px;
                border-radius:8px;
                background:#111827;
            }
            """
        )
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(10)

        radar_title = QLabel("RADAR CAMERA")
        radar_title.setObjectName("SideTitle")
        right_layout.addWidget(radar_title)

        self.distance_radar = DistanceRadarWidget()
        right_layout.addWidget(self.distance_radar)

        side_title = QLabel("DETECTIONS")
        side_title.setObjectName("SideTitle")
        right_layout.addWidget(side_title)

        self.objects_list = QListWidget()
        right_layout.addWidget(self.objects_list)

        content.addWidget(left_card, 7)
        content.addWidget(right_card, 3)
        root.addLayout(content)

        self.load_btn.clicked.connect(self.load_video)
        self.play_btn.clicked.connect(self.toggle_play)
        self.export_csv_btn.clicked.connect(self.export_csv)
        self.export_png_btn.clicked.connect(self.export_annotated_image)

    def load_video(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Load Video",
            "",
            "Videos (*.mp4 *.avi *.mov)",
        )
        if not filename:
            return

        self._stop_playback()

        capture = cv2.VideoCapture(filename)
        if not capture.isOpened():
            QMessageBox.warning(self, "Video", "Impossible d'ouvrir le fichier video selectionne")
            return

        self.video_token += 1
        self.video_path = filename
        self.video_cap = capture
        self.frame_index = 0
        self.inference_pending = False
        self.current_detections = []
        self.frame_source_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 1)
        self.frame_source_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 1)
        fps = float(capture.get(cv2.CAP_PROP_FPS) or 30.0)
        if fps <= 1.0 or fps > 120.0:
            fps = 30.0
        self.playback_interval_ms = max(16, int(1000.0 / min(fps, 30.0)))
        if hasattr(self, "distance_radar"):
            self.distance_radar.set_detections([])
        self.objects_list.clear()
        self.objects_list.addItem("Detection en cours...")
        self.play_btn.setEnabled(True)
        self.status_label.setText(f"Video chargee: {Path(filename).name}")

        self._advance_frame()

    def toggle_play(self):
        if self.video_cap is None:
            return

        if self.is_playing:
            self.timer.stop()
            self.play_btn.setText("Lecture")
        else:
            self.timer.start(self.playback_interval_ms)
            self.play_btn.setText("Pause")

        self.is_playing = not self.is_playing

    def _advance_frame(self):
        if self.video_cap is None:
            return

        ret, frame = self.video_cap.read()
        if not ret:
            self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.frame_index = 0
            ret, frame = self.video_cap.read()
            if not ret:
                return

        frame_id = self.frame_index
        self.frame_index += 1
        self.current_frame = frame
        self.frame_source_height, self.frame_source_width = frame.shape[:2]
        self.current_pixmap = self._frame_to_pixmap(
            frame,
            max(600, self.preview.width()),
            max(440, self.preview.height()),
        )

        if not self.inference_pending and frame_id % self.detection_interval == 0:
            self.inference_pending = True
            self.detect_frame_requested.emit(self.video_token, frame_id, frame.copy())

        self._render_preview()

    @Slot(int, int, list)
    def _handle_detections_ready(self, video_token: int, frame_index: int, detections: list):
        if video_token != self.video_token:
            return

        self.inference_pending = False
        self.current_detections = detections
        if hasattr(self, "distance_radar"):
            self.distance_radar.set_detections(detections)
        self._render_preview()
        self._update_objects_list()

        if detections:
            closest = min(float(getattr(detection, "distance", 0.0)) for detection in detections)
            self.status_label.setText(f"{len(detections)} objet(s) detecte(s) | plus proche: {closest:.2f} m")
        else:
            self.status_label.setText("0 objet detecte")

    def _stop_playback(self):
        self.timer.stop()
        self.is_playing = False
        self.inference_pending = False
        self.frame_index = 0
        if hasattr(self, "play_btn"):
            self.play_btn.setText("Lecture")
            self.play_btn.setEnabled(False)
        if self.video_cap is not None:
            self.video_cap.release()
            self.video_cap = None

    @staticmethod
    def _frame_to_pixmap(frame, target_width: int, target_height: int) -> QPixmap:
        height, width = frame.shape[:2]
        max_width = max(1, int(target_width))
        max_height = max(1, int(target_height))
        scale = min(max_width / max(1, width), max_height / max(1, height), 1.0)
        if scale < 1.0:
            frame = cv2.resize(
                frame,
                (max(1, int(width * scale)), max(1, int(height * scale))),
                interpolation=cv2.INTER_AREA,
            )

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channels = rgb_frame.shape
        image = QImage(rgb_frame.data, width, height, channels * width, QImage.Format_RGB888)
        return QPixmap.fromImage(image.copy())

    def _render_preview(self):
        if self.current_pixmap is None or self.current_pixmap.isNull():
            return

        target = self.current_pixmap

        annotated = QPixmap(target)
        painter = QPainter(annotated)
        painter.setRenderHint(QPainter.Antialiasing, False)

        scale_x = target.width() / max(1, self.frame_source_width)
        scale_y = target.height() / max(1, self.frame_source_height)

        for detection in self.current_detections:
            color = QColor(getattr(detection, "color", "#00E5FF"))
            xmin = float(getattr(detection, "xmin", 0.0)) * scale_x
            ymin = float(getattr(detection, "ymin", 0.0)) * scale_y
            xmax = float(getattr(detection, "xmax", 0.0)) * scale_x
            ymax = float(getattr(detection, "ymax", 0.0)) * scale_y
            confidence = float(getattr(detection, "confidence", 0.0)) * 100.0
            distance = float(getattr(detection, "distance", 0.0))

            painter.setPen(QPen(color, 3))
            painter.drawRect(int(xmin), int(ymin), int(max(1.0, xmax - xmin)), int(max(1.0, ymax - ymin)))

            label = f"{detection.name} {confidence:.0f}% | {distance:.1f} m"
            label_width = max(170, len(label) * 8)
            painter.fillRect(int(xmin), max(0, int(ymin) - 28), label_width, 22, QColor(0, 0, 0, 180))
            painter.setPen(QPen(Qt.white, 1))
            painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
            painter.drawText(int(xmin) + 6, max(16, int(ymin) - 10), label)

        painter.end()
        self.preview.setPixmap(annotated)

    def _update_objects_list(self):
        self.objects_list.clear()

        if not self.current_detections:
            self.objects_list.addItem("Aucun objet detecte")
            return

        for detection in self.current_detections:
            confidence = float(getattr(detection, "confidence", 0.0)) * 100.0
            distance = float(getattr(detection, "distance", 0.0))
            class_name = getattr(detection, "class_name", "object")
            item = QListWidgetItem(
                f"{detection.name} - {class_name} - {confidence:.0f}% - distance detecteur: {distance:.2f} m"
            )
            item.setForeground(QColor(getattr(detection, "color", "#E5E7EB")))
            self.objects_list.addItem(item)

    def export_csv(self):
        if not self.current_detections:
            QMessageBox.information(self, "Export CSV", "Aucune detection a exporter")
            return

        filename, _ = QFileDialog.getSaveFileName(self, "Export CSV", "video_detections.csv", "CSV Files (*.csv)")
        if not filename:
            return

        rows = []
        for detection in self.current_detections:
            rows.append(
                {
                    "name": detection.name,
                    "class": detection.class_name,
                    "confidence": detection.confidence,
                    "distance_detector_m": detection.distance,
                    "x": detection.x,
                    "y": detection.y,
                    "z": detection.z,
                    "color": detection.color,
                }
            )

        pd.DataFrame(rows).to_csv(filename, index=False)
        QMessageBox.information(self, "Export CSV", "Export CSV termine")

    def export_annotated_image(self):
        if self.current_pixmap is None or self.current_pixmap.isNull() or not self.current_detections:
            QMessageBox.information(self, "Export Image", "Charge d'abord une video avec des detections")
            return

        filename, _ = QFileDialog.getSaveFileName(self, "Export Annotated PNG", "annotated_frame.png", "PNG Files (*.png)")
        if not filename:
            return

        pixmap = self.preview.pixmap()
        if pixmap is None:
            QMessageBox.warning(self, "Export Image", "Aucune image a exporter")
            return

        pixmap.save(filename, "PNG")
        QMessageBox.information(self, "Export Image", "Frame annotee exportee")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.current_pixmap is not None and not self.current_pixmap.isNull():
            self._render_preview()

    def closeEvent(self, event):
        self._stop_playback()
        self.detection_thread.quit()
        self.detection_thread.wait(3000)
        event.accept()

