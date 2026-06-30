import pandas as pd


class CSVRecorder:

    def save_scan(self, dataframe, filename):

        dataframe.to_csv(
            filename,
            index=False
        )