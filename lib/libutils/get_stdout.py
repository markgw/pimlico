from urllib2 import urlopen

import sys

if len(sys.argv) < 2:
    print >>sys.stderr, "No URL specified"
    sys.exit(1)

# Fetch the requested URL
url = sys.argv[1]
f = urlopen(url)
sys.stdout.write(f.read())
