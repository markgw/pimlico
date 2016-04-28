from urllib2 import urlopen

import sys

if len(sys.argv) < 2:
    print >>sys.stderr, "No URL specified"
    sys.exit(1)

# Fetch the requested URL
url = sys.argv[1]
filename = url.rpartition("/")[2]
print >>sys.stderr, "Downloading to %s" % filename
f = urlopen(url)
with open(filename, "w") as outf:
    outf.write(f.read())
