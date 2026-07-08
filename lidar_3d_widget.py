from __future__ import annotations

import numpy as np
import logging
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class Lidar3DWidget(QWidget):
    def __init__(self):
        super().__init__()

        self._fallback = False
        self._mesh_items = []
        self._frame_index = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        try:
            import pyqtgraph.opengl as gl

            self.gl = gl
            self.view = gl.GLViewWidget()
            self.view.setBackgroundColor((6, 8, 14))
            self.view.opts["distance"] = 40
            self.view.opts["azimuth"] = 110
            self.view.opts["elevation"] = 68

            self.grid = gl.GLGridItem()
            self.grid.setSize(58, 58)
            self.grid.setSpacing(2, 2)
            self.grid.setColor((0.14, 0.22, 0.32, 0.03))
            self.view.addItem(self.grid)

            self.scatter = gl.GLScatterPlotItem()
            self.view.addItem(self.scatter)

            self.detection_scatter = gl.GLScatterPlotItem()
            self.view.addItem(self.detection_scatter)

            layout.addWidget(self.view)
        except Exception as exc:
            logging.exception("3D view initialization failed")
            self._fallback = True
            label = QLabel("Vue 3D indisponible - installez PyQtGraph OpenGL")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("color:#9CA3AF;background:#0B0F15;border:1px solid #1F2937;border-radius:12px;")
            layout.addWidget(label)

    @staticmethod
    def _to_xyz(points):
        if points is None:
            return np.zeros((0, 3), dtype=float)

        points = np.asarray(points, dtype=float)
        if points.size == 0:
            return np.zeros((0, 3), dtype=float)

        if points.ndim == 1:
            points = points.reshape(1, -1)

        if points.shape[1] >= 3:
            return points[:, :3]

        z = np.zeros((points.shape[0], 1), dtype=float)
        return np.hstack([points[:, :2], z])

    def _clear_meshes(self):
        if self._fallback:
            return

        for item in self._mesh_items:
            self.view.removeItem(item)
        self._mesh_items = []
        self._frame_index = 0

    @staticmethod
    def _rgba_tuple(color):
        color = color.lstrip("#")
        if len(color) == 6:
            r, g, b = tuple(int(color[index:index + 2], 16) / 255.0 for index in (0, 2, 4))
        else:
            r, g, b = 0.0, 0.9, 1.0
        return (r, g, b, 1.0)

    @staticmethod
    def _ellipse_ring(count, radius_x, radius_y, z_value, center=(0.0, 0.0, 0.0), phase=0.0):
        angles = np.linspace(0.0, 2.0 * np.pi, count, endpoint=False) + phase
        x = center[0] + radius_x * np.cos(angles)
        y = center[1] + radius_y * np.sin(angles)
        z = np.full_like(x, center[2] + z_value)
        return np.column_stack([x, y, z])

    @staticmethod
    def _make_prism_mesh(length, width, height, roof_scale=1.0, nose_drop=0.0, rear_drop=0.0):
        xs = np.array([-0.5, -0.18, 0.16, 0.5], dtype=float) * length
        ys = np.array([-0.5, 0.5], dtype=float) * width
        zs = np.array([0.0, 0.62, 1.0], dtype=float) * height

        vertices = []
        for z_index, z in enumerate(zs):
            roof_factor = roof_scale if z_index > 0 else 1.0
            for x in xs:
                for y in ys:
                    taper = 1.0 - 0.18 * (abs(x) / (0.5 * length))
                    vertices.append([x, y * taper, z * roof_factor])

        vertices = np.asarray(vertices, dtype=float)
        vertices[:, 0] += 0.08 * length * np.tanh(vertices[:, 0] / max(0.01, length))
        if nose_drop:
            front_mask = vertices[:, 0] < -0.12 * length
            vertices[front_mask, 2] -= nose_drop * (1.0 - np.abs(vertices[front_mask, 0]) / (0.5 * length))
        if rear_drop:
            rear_mask = vertices[:, 0] > 0.2 * length
            vertices[rear_mask, 2] -= rear_drop * ((vertices[rear_mask, 0] - 0.2 * length) / (0.3 * length))

        faces = []

        def vid(x_idx, y_idx, z_idx):
            return z_idx * len(xs) * len(ys) + x_idx * len(ys) + y_idx

        for z_idx in range(len(zs) - 1):
            for x_idx in range(len(xs) - 1):
                for y_idx in range(len(ys) - 1):
                    a = vid(x_idx, y_idx, z_idx)
                    b = vid(x_idx + 1, y_idx, z_idx)
                    c = vid(x_idx + 1, y_idx + 1, z_idx)
                    d = vid(x_idx, y_idx + 1, z_idx)
                    e = vid(x_idx, y_idx, z_idx + 1)
                    f = vid(x_idx + 1, y_idx, z_idx + 1)
                    g = vid(x_idx + 1, y_idx + 1, z_idx + 1)
                    h = vid(x_idx, y_idx + 1, z_idx + 1)
                    faces.extend([[a, b, c], [a, c, d], [e, f, g], [e, g, h], [a, b, f], [a, f, e], [b, c, g], [b, g, f], [c, d, h], [c, h, g], [d, a, e], [d, e, h]])

        return vertices, np.asarray(faces, dtype=int)

    @staticmethod
    def _make_capsule_mesh(length, width, height):
        ring_segments = 14
        rings = 6
        angles = np.linspace(0.0, 2.0 * np.pi, ring_segments, endpoint=False)
        x_positions = np.linspace(-0.5 * length, 0.5 * length, rings)
        vertices = []
        for index, x in enumerate(x_positions):
            z_scale = np.sin(np.pi * index / max(1, rings - 1))
            radius_y = width * (0.36 + 0.15 * z_scale)
            radius_z = height * (0.24 + 0.24 * z_scale)
            for angle in angles:
                vertices.append([x, radius_y * np.cos(angle), 0.5 * height + radius_z * np.sin(angle)])

        vertices = np.asarray(vertices, dtype=float)
        faces = []
        for ring in range(rings - 1):
            base = ring * ring_segments
            next_base = (ring + 1) * ring_segments
            for seg in range(ring_segments):
                a = base + seg
                b = base + (seg + 1) % ring_segments
                c = next_base + (seg + 1) % ring_segments
                d = next_base + seg
                faces.extend([[a, b, c], [a, c, d]])
        return vertices, np.asarray(faces, dtype=int)

    def _add_mesh(self, meshdata, color, scale, translation=(0.0, 0.0, 0.0), rotation=None):
        mesh = self.gl.GLMeshItem(
            meshdata=meshdata,
            color=color,
            smooth=True,
            drawFaces=True,
            drawEdges=False,
            shader="shaded",
        )
        mesh.scale(scale[0], scale[1], scale[2])
        mesh.translate(translation[0], translation[1], translation[2])
        if rotation is not None:
            axis, angle = rotation
            mesh.rotate(angle, axis[0], axis[1], axis[2])
        self._mesh_items.append(mesh)
        self.view.addItem(mesh)
        return mesh

    def _mesh_for_detection(self, detection):
        class_name = getattr(detection, "class_name", "object").lower()
        width = max(0.5, float(getattr(detection, "width", 1.0)))
        height = max(0.5, float(getattr(detection, "height", 1.0)))
        depth = max(0.5, float(getattr(detection, "depth", 1.0)))
        color = self._rgba_tuple(getattr(detection, "color", "#00E5FF"))

        if class_name == "truck":
            vertices, faces = self._make_prism_mesh(depth, width, height, roof_scale=0.92, nose_drop=0.08 * height, rear_drop=0.04 * height)
        elif class_name == "car":
            vertices, faces = self._make_prism_mesh(depth * 0.92, width * 0.92, height, roof_scale=0.86, nose_drop=0.13 * height, rear_drop=0.06 * height)
        elif class_name == "person":
            vertices, faces = self._make_capsule_mesh(depth * 0.55, width * 0.55, height * 1.05)
        elif class_name == "bicycle":
            vertices, faces = self._make_prism_mesh(depth * 0.75, width * 0.32, height * 0.58, roof_scale=0.66, nose_drop=0.05 * height, rear_drop=0.05 * height)
        elif class_name == "bus":
            vertices, faces = self._make_prism_mesh(depth * 1.10, width * 1.05, height * 1.05, roof_scale=0.90, nose_drop=0.06 * height, rear_drop=0.04 * height)
        else:
            vertices, faces = self._make_prism_mesh(depth * 0.72, width * 0.72, height * 0.72, roof_scale=0.80, nose_drop=0.08 * height, rear_drop=0.08 * height)

        meshdata = self.gl.MeshData(vertexes=vertices, faces=faces)
        return meshdata, color

    def update_scene(self, points, detections=None):
        if self._fallback:
            return

        xyz = self._to_xyz(points)
        if xyz.size:
            if xyz.shape[0] > 9000:
                step = max(1, xyz.shape[0] // 9000)
                xyz = xyz[::step]

            radial = np.hypot(xyz[:, 0], xyz[:, 1])
            keep = radial < 40.0
            xyz = xyz[keep]
            if xyz.size == 0:
                self.scatter.setData(pos=np.zeros((0, 3)), color=np.zeros((0, 4)), size=2.0)
                self._clear_boxes()
                self.detection_scatter.setData(pos=np.zeros((0, 3)), color=np.zeros((0, 4)), size=8)
                return

            radial = np.hypot(xyz[:, 0], xyz[:, 1])
            z = xyz[:, 2]
            z_min = float(np.min(z))
            z_max = float(np.max(z))
            z_span = max(0.3, z_max - z_min)
            radial_span = max(1.0, float(np.max(radial)) - float(np.min(radial)))

            z_norm = (z - z_min) / z_span
            r_norm = (radial - float(np.min(radial))) / radial_span

            core = np.clip(1.0 - (radial / 40.0), 0.0, 1.0)
            red = np.clip(0.08 + 0.84 * np.power(z_norm, 0.78), 0.0, 1.0)
            green = np.clip(0.12 + 0.88 * np.power(core, 0.38), 0.0, 1.0)
            blue = np.clip(0.22 + 0.78 * (1.0 - np.power(z_norm, 0.60)), 0.0, 1.0)
            alpha = np.clip(0.62 + 0.38 * np.power(core, 0.18), 0.0, 1.0)
            colors = np.column_stack([red, green, blue, alpha])
            self.scatter.setData(pos=xyz, color=colors, size=2.6)
        else:
            self.scatter.setData(pos=np.zeros((0, 3)), color=np.zeros((0, 4)), size=2.6)

        self._frame_index += 1
        if self._frame_index % 3 != 0:
            return

        self._clear_meshes()

        self.detection_scatter.setData(pos=np.zeros((0, 3)), color=np.zeros((0, 4)), size=0)

        if not detections:
            return

        for detection in detections:
            meshdata, color = self._mesh_for_detection(detection)
            translation = (float(detection.x), float(detection.y), float(detection.z))
            self._add_mesh(meshdata, color, scale=(1.0, 1.0, 1.0), translation=translation)
