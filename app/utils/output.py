import json
import os

OUTPUT_FILE = "output/records.json"


def save_record(record: dict):
    os.makedirs("output", exist_ok=True)

    records = []

    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as file:
            try:
                records = json.load(file)
            except json.JSONDecodeError:
                records = []

    records.append(record)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(records, file, indent=2)