import contextlib
from urllib2 import urlopen


def download_file(url, target_file):
    with contextlib.closing(urlopen(url)) as reader:
        with open(target_file, "w") as output_file:
            output_file.write(reader.read())
