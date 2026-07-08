from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np
import logging

from object_tracker import TrackedDetection


@dataclass
class YoloStatus:
    ready: bool
    message: str


class YOLODetector:
    def __init__(self, model_name: str = "yolov8n.pt", confidence: float = 0.25):
        self.model_name = model_name
        self.confidence = confidence
        self.model = None
        self.status = YoloStatus(False, "YOLO non chargÃ©")

        try:
            from ultralytics import YOLO

            self.model = YOLO(model_name)
            self.status = YoloStatus(True, f"YOLO prÃªt: {model_name}")
        except Exception as exc:  # pragma: no cover - runtime dependency guard
            self.status = YoloStatus(False, f"YOLO indisponible: {exc}")

    def is_ready(self) -> bool:
        return self.status.ready and self.model is not None

    @staticmethod
    def _class_color(class_name: str) -> str:
        palette = {
            "person": "#00E5FF",
            "car": "#00FF95",
            "truck": "#FF8A00",
            "bus": "#FF4D6D",
            "bicycle": "#FFD166",
            "motorcycle": "#A78BFA",
        }
        return palette.get(class_name.lower(), "#60A5FA")

    @staticmethod
    def _estimate_3d_from_box(
        class_name: str,
        box: Iterable[float],
        image_width: int,
        image_height: int,
    ) -> TrackedDetection:
        xmin, ymin, xmax, ymax = map(float, box)
        box_width = max(1.0, xmax - xmin)
        box_height = max(1.0, ymax - ymin)
        center_x = (xmin + xmax) / 2.0
        center_y = (ymin + ymax) / 2.0

        class_bias = {
            "person": (1.0, 0.6, 1.7),
            "car": (4.2, 1.8, 1.5),
            "truck": (6.0, 2.5, 2.9),
            "bus": (8.0, 2.7, 3.0),
            "bicycle": (1.8, 0.6, 1.4),
            "motorcycle": (2.0, 0.8, 1.4),
        }
        width_m, height_m, depth_m = class_bias.get(class_name.lower(), (2.0, 1.0, 1.5))

        normalized_offset = (center_x - image_width / 2.0) / max(1.0, image_width / 2.0)
        pixel_height_ratio = box_height / max(1.0, image_height)
        distance = max(1.0, min(45.0, (depth_m * 18.0) / max(0.1, pixel_height_ratio)))
        lateral = normalized_offset * distance * 0.85
        z = height_m / 2.0
        angle = float(np.degrees(np.arctan2(lateral, distance)))

        return TrackedDetection(
            name=class_name.title(),
            class_name=class_name,
            confidence=0.0,
            x=lateral,
            y=distance,
            z=z,
            distance=float(np.hypot(lateral, distance)),
            angle=angle,
            width=width_m,
            height=height_m,
            depth=depth_m,
            xmin=xmin,
            ymin=ymin,
            xmax=xmax,
            ymax=ymax,
            zmin=0.0,
            zmax=height_m,
            point_count=0,
            color=YOLODetector._class_color(class_name),
            source="image",
        )

    def detect_image(self, image_path: str) -> list[TrackedDetection]:
        if not self.is_ready():
            return []

        path = Path(image_path)
        if not path.exists():
            return []

        try:
            results = self.model.predict(
                source=str(path),
                conf=self.confidence,
                verbose=False,
            )
        except Exception as exc:  # pragma: no cover - runtime dependency guard
            logging.exception("YOLO detect_image failed")
            return []

        if not results:
            return []

        result = results[0]
        image_height, image_width = result.orig_shape[:2]
        detections: list[TrackedDetection] = []

        boxes = getattr(result, "boxes", None)
        if boxes is None:
            return []

        names = result.names if hasattr(result, "names") else {}

        for box in boxes:
            xyxy = box.xyxy[0].cpu().numpy().tolist()
            confidence = float(box.conf[0].cpu().numpy())
            class_id = int(box.cls[0].cpu().numpy())
            class_name = str(names.get(class_id, f"class_{class_id}"))

            detection = self._estimate_3d_from_box(
                class_name=class_name,
                box=xyxy,
                image_width=image_width,
                image_height=image_height,
            )
            detection.confidence = confidence
            detection.color = self._class_color(class_name)
            detections.append(detection)

        return detections

    def detect_frame(self, frame: np.ndarray, inference_width: int | None = None) -> list[TrackedDetection]:
        if not self.is_ready() or frame is None:
            return []

        original_height, original_width = frame.shape[:2]
        inference_frame = frame
        scale = 1.0
        if inference_width is not None and original_width > inference_width:
            scale = inference_width / float(original_width)
            inference_height = max(1, int(original_height * scale))
            inference_frame = cv2.resize(frame, (inference_width, inference_height), interpolation=cv2.INTER_AREA)

        try:
            results = self.model.predict(
                source=inference_frame,
                conf=self.confidence,
                imgsz=int(inference_width or 640),
                max_det=20,
                verbose=False,
            )
        except Exception as exc:  # pragma: no cover - runtime dependency guard
            logging.exception("YOLO detect_frame failed")
            return []

        if not results:
            return []

        result = results[0]
        detections: list[TrackedDetection] = []

        boxes = getattr(result, "boxes", None)
        if boxes is None:
            return []

        names = result.names if hasattr(result, "names") else {}
        inverse_scale = 1.0 / scale

        for box in boxes:
            xyxy = box.xyxy[0].cpu().numpy().astype(float)
            if scale != 1.0:
                xyxy *= inverse_scale
            xyxy = xyxy.tolist()
            confidence = float(box.conf[0].cpu().numpy())
            class_id = int(box.cls[0].cpu().numpy())
            class_name = str(names.get(class_id, f"class_{class_id}"))

            detection = self._estimate_3d_from_box(
                class_name=class_name,
                box=xyxy,
                image_width=original_width,
                image_height=original_height,
            )
            detection.confidence = confidence
            detection.color = self._class_color(class_name)
            detections.append(detection)

        return detections


