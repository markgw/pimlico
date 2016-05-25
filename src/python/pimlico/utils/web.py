import contextlib
from urllib2 import urlopen, URLError


def download_file(url, target_file):
    try:
        with contextlib.closing(urlopen(url)) as reader:
            with open(target_file, "w") as output_file:
                output_file.write(reader.read())
    except URLError, e:
        if len(e.args) and e.args[0] == "unknown url type: https":
            raise RuntimeError("cannot download from https URL, as Python was not installed with openssl support")
