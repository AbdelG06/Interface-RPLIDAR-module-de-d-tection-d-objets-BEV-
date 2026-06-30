import json


class JSONExporter:

    @staticmethod
    def export(detections, filename):

        data = []

        for d in detections:

            data.append(
                {
                    "id": d.object_id,
                    "x": d.x,
                    "y": d.y,
                    "distance": d.distance,
                    "angle": d.angle,
                    "width": d.width,
                    "height": d.height
                }
            )

        with open(filename, "w") as f:
            json.dump(data, f, indent=4)