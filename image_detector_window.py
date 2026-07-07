from __future__ import annotations

import json

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QGuiApplication, QPainter, QPen, QPixmap
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


class ImageDetectorWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Image Detector")
        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            geometry = screen.availableGeometry()
            self.resize(max(1200, int(geometry.width() * 0.82)), max(800, int(geometry.height() * 0.84)))
        else:
            self.resize(1500, 950)

        self.detector = YOLODetector()
        self.current_image_path: str | None = None
        self.current_pixmap: QPixmap | None = None
        self.current_detections = []

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        header = QFrame()
        header.setStyleSheet(
            """
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #101827, stop:1 #0B0F15);
                border: 1px solid #1F2937;
                border-radius: 18px;
            }
            """
        )
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(18, 14, 18, 14)

        title_box = QVBoxLayout()
        title = QLabel("IMAGE DETECTOR")
        title.setStyleSheet("font-size:26px;font-weight:800;color:#00E5FF;")
        subtitle = QLabel("Détection IA d'objets dans les images JPG/PNG")
        subtitle.setStyleSheet("color:#9CA3AF;font-size:10pt;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.status_label = QLabel(self.detector.status.message)
        self.status_label.setStyleSheet("color:#9CA3AF;font-weight:600;")
        header_layout.addWidget(self.status_label)

        root.addWidget(header)

        toolbar = QFrame()
        toolbar.setStyleSheet(
            """
            QFrame {
                background:#0F172A;
                border:1px solid #1F2937;
                border-radius:14px;
            }
            QPushButton {
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #0066FF, stop:1 #00E5FF);
                color:white;
                font-weight:700;
                border:none;
                border-radius:12px;
                padding:10px 14px;
            }
            QPushButton:hover {
                background:#00E5FF;
            }
            """
        )
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(12, 12, 12, 12)

        self.load_btn = QPushButton("Load Image")
        self.export_csv_btn = QPushButton("Export CSV")
        self.export_json_btn = QPushButton("Export JSON")
        self.export_png_btn = QPushButton("Export Annotated PNG")

        toolbar_layout.addWidget(self.load_btn)
        toolbar_layout.addWidget(self.export_csv_btn)
        toolbar_layout.addWidget(self.export_json_btn)
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
                background:#0F172A;
                border:1px solid #1F2937;
                border-radius:14px;
            }
            """
        )
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(10)

        self.preview = QLabel("Load an image to detect objects")
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
        right_card.setMinimumWidth(380)
        right_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        right_card.setStyleSheet(
            """
            QFrame {
                background:#0F172A;
                border:1px solid #1F2937;
                border-radius:14px;
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
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(10)

        side_title = QLabel("OBJETS DETECTES")
        side_title.setObjectName("SideTitle")
        right_layout.addWidget(side_title)

        self.objects_list = QListWidget()
        right_layout.addWidget(self.objects_list)

        content.addWidget(left_card, 7)
        content.addWidget(right_card, 3)
        root.addLayout(content)

        self.load_btn.clicked.connect(self.load_image)
        self.export_csv_btn.clicked.connect(self.export_csv)
        self.export_json_btn.clicked.connect(self.export_json)
        self.export_png_btn.clicked.connect(self.export_annotated_image)

    def load_image(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Load Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp)",
        )
        if not filename:
            return

        self.current_image_path = filename
        self.current_pixmap = QPixmap(filename)
        if self.current_pixmap.isNull():
            QMessageBox.warning(self, "Image", "Impossible de charger l'image sélectionnée")
            return

        self.current_detections = self.detector.detect_image(filename)
        self._render_preview()
        self._update_objects_list()
        self.status_label.setText(f"{len(self.current_detections)} objet(s) détecté(s)")

    def _render_preview(self):
        if self.current_pixmap is None or self.current_pixmap.isNull():
            return

        target = self.current_pixmap.scaled(
            max(600, self.preview.width()),
            max(440, self.preview.height()),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        annotated = QPixmap(target)
        painter = QPainter(annotated)
        painter.setRenderHint(QPainter.Antialiasing)

        scale_x = target.width() / self.current_pixmap.width()
        scale_y = target.height() / self.current_pixmap.height()

        for detection in self.current_detections:
            color = QColor(getattr(detection, "color", "#00E5FF"))
            xmin = float(getattr(detection, "xmin", 0.0)) * scale_x
            ymin = float(getattr(detection, "ymin", 0.0)) * scale_y
            xmax = float(getattr(detection, "xmax", 0.0)) * scale_x
            ymax = float(getattr(detection, "ymax", 0.0)) * scale_y

            painter.setPen(QPen(color, 3))
            painter.drawRect(int(xmin), int(ymin), int(max(1.0, xmax - xmin)), int(max(1.0, ymax - ymin)))

            label = f"{detection.name} ({float(detection.confidence) * 100:.0f}%)"
            painter.fillRect(int(xmin), max(0, int(ymin) - 28), max(140, len(label) * 8), 22, QColor(0, 0, 0, 180))
            painter.setPen(QPen(Qt.white, 1))
            painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
            painter.drawText(int(xmin) + 6, max(16, int(ymin) - 10), label)

        painter.end()
        self.preview.setPixmap(annotated)

    def _update_objects_list(self):
        self.objects_list.clear()

        if not self.current_detections:
            self.objects_list.addItem("Aucun objet détecté")
            return

        for detection in self.current_detections:
            confidence = float(getattr(detection, "confidence", 0.0)) * 100.0
            distance = float(getattr(detection, "distance", 0.0))
            class_name = getattr(detection, "class_name", "object")
            item = QListWidgetItem(f"{detection.name} - {class_name} - {confidence:.0f}% - {distance:.2f} m")
            item.setForeground(QColor(getattr(detection, "color", "#E5E7EB")))
            self.objects_list.addItem(item)

    def export_csv(self):
        if not self.current_detections:
            QMessageBox.information(self, "Export CSV", "Aucune détection à exporter")
            return

        filename, _ = QFileDialog.getSaveFileName(self, "Export CSV", "image_detections.csv", "CSV Files (*.csv)")
        if not filename:
            return

        rows = []
        for detection in self.current_detections:
            rows.append(
                {
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

    def export_json(self):
        if not self.current_detections:
            QMessageBox.information(self, "Export JSON", "Aucune détection à exporter")
            return

        filename, _ = QFileDialog.getSaveFileName(self, "Export JSON", "image_detections.json", "JSON Files (*.json)")
        if not filename:
            return

        payload = []
        for detection in self.current_detections:
            payload.append(
                {
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

        with open(filename, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

        QMessageBox.information(self, "Export JSON", "Export JSON terminé")

    def export_annotated_image(self):
        if self.current_pixmap is None or self.current_pixmap.isNull() or not self.current_detections:
            QMessageBox.information(self, "Export Image", "Charge d'abord une image avec des détections")
            return

        filename, _ = QFileDialog.getSaveFileName(self, "Export Annotated PNG", "annotated_image.png", "PNG Files (*.png)")
        if not filename:
            return

        pixmap = self.preview.pixmap()
        if pixmap is None:
            QMessageBox.warning(self, "Export Image", "Aucune image à exporter")
            return

        pixmap.save(filename, "PNG")
        QMessageBox.information(self, "Export Image", "Image annotée exportée")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.current_pixmap is not None and not self.current_pixmap.isNull() and self.current_detections:
            self._render_preview()
