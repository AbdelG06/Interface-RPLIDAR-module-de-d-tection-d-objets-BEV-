from dataclasses import dataclass


@dataclass
class ObjectDetection:

    object_id: int

    x: float
    y: float

    distance: float
    angle: float

    width: float
    height: float

    xmin: float
    ymin: float

    xmax: float
    ymax: float

    point_count: int