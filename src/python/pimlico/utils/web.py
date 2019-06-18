# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from urllib import urlretrieve


def download_file(url, target_file):
    """ Now just an alias for urllib.urlretrieve() """
    # Used to do something using urllib2 to read and then write to a file
    # However, this holds the whole file in memory, which is bad if it's big
    # Now just pass through to urlretrieve, which we should have done all along
    urlretrieve(url, target_file)
