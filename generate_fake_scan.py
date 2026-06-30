import numpy as np
import pandas as pd

rows = []

for frame in range(50):

    for angle in range(360):

        distance = 8.0

        if 30 <= angle <= 60:
            distance = np.random.normal(2.5, 0.1)

        elif 120 <= angle <= 150:
            distance = np.random.normal(4.0, 0.1)

        elif 240 <= angle <= 280:
            distance = np.random.normal(6.0, 0.1)

        rows.append(
            [frame, angle, distance, 15]
        )

df = pd.DataFrame(
    rows,
    columns=[
        "timestamp",
        "angle",
        "distance",
        "quality"
    ]
)

df.to_csv(
    "fake_scan.csv",
    index=False
)

print("fake_scan.csv créé")