import pandas as pd
import numpy as np


class CSVPlayer:

    def __init__(self):
        self.data = None
        self.current_index = 0

    def load_file(self, filename):

        self.data = pd.read_csv(filename)

        self.current_index = 0

    def get_frame(self):

        if self.data is None:
            return None

        if self.current_index >= len(self.data):
            self.current_index = 0

        frame = self.data.iloc[
            self.current_index:self.current_index + 360
        ]

        self.current_index += 360

        return frame

    @staticmethod
    def polar_to_cartesian(frame):

        angle = np.deg2rad(frame["angle"].values)

        distance = frame["distance"].values

        x = distance * np.cos(angle)
        y = distance * np.sin(angle)

        return np.column_stack((x, y))