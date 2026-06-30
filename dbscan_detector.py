import numpy as np

from sklearn.cluster import DBSCAN

from object_detection import ObjectDetection


class DBSCANDetector:

    def __init__(self,
                 eps=0.3,
                 min_samples=4):

        self.eps = eps
        self.min_samples = min_samples

    def detect(self, points):

        if len(points) == 0:
            return []

        clustering = DBSCAN(
            eps=self.eps,
            min_samples=self.min_samples
        )

        labels = clustering.fit_predict(points)

        detections = []

        unique_labels = set(labels)

        for label in unique_labels:

            if label == -1:
                continue

            cluster = points[labels == label]

            centroid = cluster.mean(axis=0)

            xmin = cluster[:, 0].min()
            ymin = cluster[:, 1].min()

            xmax = cluster[:, 0].max()
            ymax = cluster[:, 1].max()

            width = xmax - xmin
            height = ymax - ymin

            distance = np.linalg.norm(centroid)

            angle = np.degrees(
                np.arctan2(
                    centroid[1],
                    centroid[0]
                )
            )

            detections.append(
                ObjectDetection(
                    object_id=-1,

                    x=centroid[0],
                    y=centroid[1],

                    distance=distance,
                    angle=angle,

                    width=width,
                    height=height,

                    xmin=xmin,
                    ymin=ymin,

                    xmax=xmax,
                    ymax=ymax,

                    point_count=len(cluster)
                )
            )

        return detections