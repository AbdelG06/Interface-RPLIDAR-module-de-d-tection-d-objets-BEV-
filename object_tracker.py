from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import numpy as np


@dataclass
class TrackedDetection:
    track_id: int = 0
    name: str = "Object"
    class_name: str = "object"
    confidence: float = 1.0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    distance: float = 0.0
    angle: float = 0.0
    width: float = 0.0
    height: float = 0.0
    depth: float = 0.0
    xmin: float = 0.0
    ymin: float = 0.0
    xmax: float = 0.0
    ymax: float = 0.0
    zmin: float = 0.0
    zmax: float = 0.0
    point_count: int = 0
    color: str = "#00E5FF"
    source: str = "yolo"
    is_alert: bool = False
    metadata: dict = field(default_factory=dict)


class ObjectTracker:
    def __init__(self, max_distance: float = 1.5, max_missed: int = 6):
        self.max_distance = max_distance
        self.max_missed = max_missed
        self.reset()

    def reset(self):
        self.next_id = 1
        self.tracks: dict[int, dict] = {}

    @staticmethod
    def _class_color(class_name: str) -> str:
        palette = {
            "person": "#00E5FF",
            "car": "#00FF95",
            "truck": "#FF8A00",
            "bus": "#FF4D6D",
            "bicycle": "#FFD166",
            "motorcycle": "#A78BFA",
            "obstacle": "#94A3B8",
            "unknown": "#60A5FA",
            "object": "#60A5FA",
            "cluster": "#60A5FA",
        }
        return palette.get(class_name.lower(), "#60A5FA")

    @staticmethod
    def _read_attr(obj, *names, default=None):
        for name in names:
            if hasattr(obj, name):
                value = getattr(obj, name)
                if value is not None:
                    return value
        return default

    def _normalize(self, detection) -> TrackedDetection:
        if isinstance(detection, TrackedDetection):
            return detection

        name = self._read_attr(detection, "name", "label", default="Object")
        class_name = self._read_attr(detection, "class_name", "class", default=str(name).lower())
        track_id = int(self._read_attr(detection, "track_id", "object_id", default=0) or 0)
        confidence = float(self._read_attr(detection, "confidence", default=1.0) or 1.0)
        x = float(self._read_attr(detection, "x", default=0.0) or 0.0)
        y = float(self._read_attr(detection, "y", default=0.0) or 0.0)
        z = float(self._read_attr(detection, "z", default=0.0) or 0.0)
        distance = float(self._read_attr(detection, "distance", default=float(np.hypot(x, y))) or float(np.hypot(x, y)))
        angle = float(self._read_attr(detection, "angle", default=float(np.degrees(np.arctan2(y, x))) if x or y else 0.0) or 0.0)
        width = float(self._read_attr(detection, "width", default=0.0) or 0.0)
        height = float(self._read_attr(detection, "height", default=0.0) or 0.0)
        depth = float(self._read_attr(detection, "depth", default=max(width, height, 0.5)) or max(width, height, 0.5))
        xmin = float(self._read_attr(detection, "xmin", default=x - width / 2) or (x - width / 2))
        ymin = float(self._read_attr(detection, "ymin", default=y - height / 2) or (y - height / 2))
        xmax = float(self._read_attr(detection, "xmax", default=x + width / 2) or (x + width / 2))
        ymax = float(self._read_attr(detection, "ymax", default=y + height / 2) or (y + height / 2))
        zmin = float(self._read_attr(detection, "zmin", default=z - depth / 2) or (z - depth / 2))
        zmax = float(self._read_attr(detection, "zmax", default=z + depth / 2) or (z + depth / 2))
        point_count = int(self._read_attr(detection, "point_count", default=0) or 0)
        source = self._read_attr(detection, "source", default="yolo")
        metadata = dict(self._read_attr(detection, "metadata", default={}) or {})

        return TrackedDetection(
            track_id=track_id,
            name=str(name),
            class_name=str(class_name),
            confidence=confidence,
            x=x,
            y=y,
            z=z,
            distance=distance,
            angle=angle,
            width=width,
            height=height,
            depth=depth,
            xmin=xmin,
            ymin=ymin,
            xmax=xmax,
            ymax=ymax,
            zmin=zmin,
            zmax=zmax,
            point_count=point_count,
            color=self._class_color(str(class_name)),
            source=str(source),
            metadata=metadata,
        )

    def update(self, detections: Iterable) -> list[TrackedDetection]:
        normalized = [self._normalize(detection) for detection in detections]
        if not normalized:
            for track_id in list(self.tracks.keys()):
                self.tracks[track_id]["missed"] += 1
                if self.tracks[track_id]["missed"] > self.max_missed:
                    self.tracks.pop(track_id, None)
            return []

        assigned_tracks: set[int] = set()
        available_tracks = dict(self.tracks)

        for detection in normalized:
            best_track_id = None
            best_distance = float("inf")

            for track_id, track in available_tracks.items():
                if track_id in assigned_tracks:
                    continue

                class_penalty = 0.0 if track["class_name"] == detection.class_name else 0.25
                distance = float(np.hypot(detection.x - track["x"], detection.y - track["y"])) + class_penalty

                if distance < best_distance:
                    best_distance = distance
                    best_track_id = track_id

            if best_track_id is not None and best_distance <= self.max_distance:
                detection.track_id = best_track_id
                assigned_tracks.add(best_track_id)
                self.tracks[best_track_id].update(
                    {
                        "x": detection.x,
                        "y": detection.y,
                        "z": detection.z,
                        "class_name": detection.class_name,
                        "name": detection.name,
                        "color": self._class_color(detection.class_name),
                        "missed": 0,
                    }
                )
            else:
                detection.track_id = self.next_id
                self.tracks[self.next_id] = {
                    "x": detection.x,
                    "y": detection.y,
                    "z": detection.z,
                    "class_name": detection.class_name,
                    "name": detection.name,
                    "color": self._class_color(detection.class_name),
                    "missed": 0,
                }
                assigned_tracks.add(self.next_id)
                self.next_id += 1

            detection.color = self._class_color(detection.class_name)

        for track_id in list(self.tracks.keys()):
            if track_id not in assigned_tracks:
                self.tracks[track_id]["missed"] += 1
                if self.tracks[track_id]["missed"] > self.max_missed:
                    self.tracks.pop(track_id, None)

        return normalized
