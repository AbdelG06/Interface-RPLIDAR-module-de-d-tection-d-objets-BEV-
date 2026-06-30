class AlertManager:

    def __init__(self, safety_radius=2.0):

        self.safety_radius = safety_radius

    def check(self, detections):

        alerts = []

        for detection in detections:

            if detection.distance <= self.safety_radius:

                alerts.append(
                    f"ALERTE - Objet {detection.object_id} "
                    f"a {detection.distance:.2f} m"
                )

        return alerts