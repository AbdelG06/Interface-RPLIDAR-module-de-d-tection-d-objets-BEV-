import numpy as np


class CentroidTracker:

    def __init__(self):

        self.next_id = 1

        self.objects = {}

        self.max_distance = 0.5

    def update(self, detections):

        assigned = []

        for detection in detections:

            best_id = None
            best_distance = 9999

            for obj_id, centroid in self.objects.items():

                d = np.linalg.norm(
                    np.array([
                        detection.x,
                        detection.y
                    ])
                    - centroid
                )

                if d < best_distance:
                    best_distance = d
                    best_id = obj_id

            if best_distance < self.max_distance:

                detection.object_id = best_id

                self.objects[best_id] = np.array([
                    detection.x,
                    detection.y
                ])

                assigned.append(best_id)

            else:

                obj_id = self.next_id

                self.next_id += 1

                detection.object_id = obj_id

                self.objects[obj_id] = np.array([
                    detection.x,
                    detection.y
                ])

                assigned.append(obj_id)

        return detections