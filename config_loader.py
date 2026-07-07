import json
from pathlib import Path


class ConfigLoader:

    @staticmethod
    def load(path="config/config.json"):

        candidate = Path(path)
        if not candidate.exists():
            root_candidate = Path(__file__).with_name("config.json")
            if root_candidate.exists():
                candidate = root_candidate

        with candidate.open("r", encoding="utf-8") as f:
            return json.load(f)