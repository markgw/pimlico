# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

import shutil

from future import standard_library
standard_library.install_aliases()

from urllib.request import urlretrieve, Request, urlopen


def download_file(url, target_file, headers=None):
    """ Now just an alias for urllib.urlretrieve() """
    # Used to do something using urllib2 to read and then write to a file
    # However, this holds the whole file in memory, which is bad if it's big
    # Now just pass through to urlretrieve, which we should have done all along
    _headers = {}
    if headers is not None:
        _headers.update(headers)
    request = Request(url, headers=_headers)
    with urlopen(request) as response:
        with open(target_file, "wb") as f_out:
            shutil.copyfileobj(response, f_out)
