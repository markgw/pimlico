# Add copyright message to any python files that don't already have it
import os
from itertools import takewhile

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PYTHON_DIRS = ["src/python"]
JAVA_DIRS = ["src/java"]

py_copyright_message = """\
# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

"""
correct_top_lines = py_copyright_message.splitlines(keepends=True)[:3]

for dir in PYTHON_DIRS:
    for dirpath, dirnames, filenames in os.walk(os.path.join(BASE_DIR, dir)):
        filenames = [f for f in filenames if f.endswith(".py") and not f.startswith("__")]
        for filename in filenames:
            path = os.path.join(dirpath, filename)
            # Read in the file
            with open(path, "r") as inf:
                text = inf.read()
            lines = text.splitlines(keepends=True)

            # Check whether it's already got a copyright message
            top_lines = list(takewhile(lambda line: line.strip() == "" or line.startswith("#"), lines))
            if any("copyright" in line.lower() for line in top_lines):
                # Check whether this file has an old copyright message that should be updated
                if "This file is part of Pimlico" in top_lines[0] \
                        and "Copyright" in top_lines[1] and "Licensed under" in top_lines[2] and \
                        top_lines[:3] != correct_top_lines:
                    # There's a copyright message here, but it's not the right one
                    print("Updating copyright message in {}".format(path))
                    rest = lines[len(top_lines):]
                    if len(top_lines) == 3 or top_lines[3].strip() != "":
                        # No blank line after copyright message
                        top_lines.insert(3, "\n")
                    with open(path, "w") as outf:
                        outf.write("".join(correct_top_lines + top_lines[3:] + rest))
                else:
                    # Seems to be something copyrighty here: don't add the new copyright message
                    print("Skipping %s which seems to have a copyright message" % path)
                    continue
            else:
                print("Adding to %s" % path)
                with open(path, "w") as outf:
                    outf.write(py_copyright_message)
                    outf.write(text)

java_copyright_message = """\
// This file is part of Pimlico
// Copyright (C) 2020 Mark Granroth-Wilding
// Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

"""

for dir in JAVA_DIRS:
    for dirpath, dirnames, filenames in os.walk(os.path.join(BASE_DIR, dir)):
        filenames = [f for f in filenames if f.endswith(".java")]
        for filename in filenames:
            path = os.path.join(dirpath, filename)
            # Read in the file
            with open(path, "r") as inf:
                text = inf.read()

            # Check whether it's already got a copyright message
            top_lines = list(takewhile(lambda line: line.strip() == "" or line.startswith("//"), text.splitlines()))
            if any("copyright" in line.lower() for line in top_lines):
                # Seems to be something copyrighty here: don't add the new copyright message
                print("Skipping %s which seems to have a copyright message" % path)
                continue

            print("Adding to %s" % path)
            with open(path, "w") as outf:
                outf.write(java_copyright_message)
                outf.write(text)

