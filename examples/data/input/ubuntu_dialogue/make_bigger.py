#!/usr/bin/env python3
# Post-processes the dialogues.json file to get a small subsampled corpus
import json
from datetime import datetime
import random

# Subsample this number of dialogues from each month
dialogues_per_month = 100


with open("dialogues.json", "r") as f:
    data = json.load(f)

print("{:,} dialogues".format(len(data)))
dias_by_date = {}
for dialogue in data:
    # Parse the timestamp to get the month only
    ts = datetime.strptime(dialogue["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ")
    dias_by_date.setdefault((ts.year, ts.month), []).append(dialogue)

print("{:,} distinct months".format(len(dias_by_date)))

print("Subsampling {} from each".format(dialogues_per_month))
subsampled = []
for (year, month), dialogues in sorted(dias_by_date.items()):
    # Randomly choose some
    if len(dialogues) > dialogues_per_month:
        chosen_dias = random.sample(dialogues, dialogues_per_month)
    else:
        chosen_dias = list(dialogues)
    # Keep them sorted by their timestamps
    chosen_dias.sort(key=lambda d: d["timestamp"])
    subsampled.extend(chosen_dias)


print("Writing out to dialogues_bigger.json")
with open("dialogues_bigger.json", "w") as f:
    json.dump(subsampled, f)
