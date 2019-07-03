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
f = urlopen(url)
sys.stdout.write(f.read())
