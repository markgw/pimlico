"""
Tiny script to replace the headers in the API docs after they've been built
using sphinx-apidoc.

See: https://stackoverflow.com/questions/25276164/sphinx-apidoc-dont-print-full-path-to-packages-and-modules

Only works in Python 3: it's assume docs are built in Python 3.

"""
import os
import sys
import re


header_re = re.compile(r"^(?:[a-zA-Z0-9]*\\\.)*([a-zA-Z0-9_\\]+) (package|module)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Specify directory to edit files in")
        sys.exit(1)
    docs_dir = os.path.abspath(sys.argv[1])
    print("Editing headers in {}".format(docs_dir))

    for filename in os.listdir(docs_dir):
        with open(os.path.join(docs_dir, filename), "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
            if header_re.match(lines[0]):
                header = header_re.sub(r"\1", lines[0])
            else:
                print("WARNING: Couldn't match header on first line of {}".format(filename))
                continue
        # Replace the header and keep the rest of the file the same
        text = "\n".join([header, "="*len(header)] + lines[2:])
        with open(os.path.join(docs_dir, filename), "w", encoding="utf-8") as f:
            f.write(text)
