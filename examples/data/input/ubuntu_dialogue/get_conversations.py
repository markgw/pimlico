#!/usr/bin/env python3
# Script to extract whole conversations from the Ubuntu Dialogue Corpus
import os
import itertools
import csv
import json

input_folder = os.path.join("..", "Ubuntu-dialogue-corpus")
input_files = ["dialogueText_196.csv", "dialogueText_301.csv", "dialogueText.csv"]


def iter_lines():
    for filename in input_files:
        print("Reading", filename)
        with open(os.path.join(input_folder, filename), "r") as f:
            # Skip the first line (headings)
            csv_reader = csv.reader(itertools.islice(f, 1, None))
            for fields in csv_reader:
                # Get just the folder name [0] + dialogue ID (1), timestamp (2) and text (5)
                yield "{}/{}".format(fields[0], fields[1]), fields[2], fields[5]


def iter_dialogues():
    """Aggregate all lines from a dialogue"""
    # Some dialogues are repeated for some reason: skip them
    seen_ids = set()

    lines = iter_lines()
    current_dia, current_timestamp, first_text = next(lines)
    current_lines = [first_text]
    
    for dialogue, timestamp, text in lines:
        if current_dia != dialogue:
            # Started a new dialogue
            if current_dia not in seen_ids:
                yield current_dia, current_timestamp, current_lines
                seen_ids.add(current_dia)

            current_dia = dialogue
            # Always use the first timestamp as the dialogue's timestamp
            current_timestamp = timestamp
            current_lines = [text]
        else:
            current_lines.append(text)

    # Include the last dialogue
    if current_dia not in seen_ids:
        yield current_dia, current_timestamp, current_lines


# Put together the data
data = [
    {"dialogue_id": dialogue_id, "timestamp": timestamp, "text": "\n".join(lines)} 
    for dialogue_id, timestamp, lines in iter_dialogues()
]
print("Read {} dialogues. Writing out to dialogues.json".format(len(data)))
    

with open("dialogues.json", "w") as out_f:
    json.dump(data, out_f)
