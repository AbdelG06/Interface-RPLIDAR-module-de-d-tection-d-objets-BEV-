class AlertManager:

    def __init__(self, safety_radius=2.0):

        self.safety_radius = safety_radius

    def check(self, detections):

        alerts = []

        for detection in detections:

            if detection.distance <= self.safety_radius:

                object_id = getattr(detection, "track_id", getattr(detection, "object_id", "?"))
                name = getattr(detection, "name", "Objet")

                alerts.append(
                    f'ALERTE - Objet "{name}" '
                    f"(ID {object_id}) à {detection.distance:.2f} m"
                )

        return alerts