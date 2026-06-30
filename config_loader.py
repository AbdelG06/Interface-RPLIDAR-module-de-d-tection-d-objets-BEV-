import json


class ConfigLoader:

    @staticmethod
    def load(path="config/config.json"):

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)