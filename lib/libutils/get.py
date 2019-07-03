from __future__ import print_function
from future import standard_library

standard_library.install_aliases()
from urllib.request import urlopen

import sys

if len(sys.argv) < 2:
    print("No URL specified", file=sys.stderr)
    sys.exit(1)

# Fetch the requested URL
url = sys.argv[1]
filename = url.rpartition("/")[2]
print("Downloading to %s" % filename, file=sys.stderr)
f = urlopen(url)
with open(filename, "w") as outf:
    outf.write(f.read())
