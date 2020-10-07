# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

"""
Software licenses, for referring to in software dependency documentation.

Literals here are used to refer to the licenses that software uses.

See https://choosealicense.com/licenses/ for more details and comparison.

"""


class SoftwareLicense(object):
    def __init__(self, name, description=None, url=None):
        self.url = url
        self.description = description
        self.name = name


GNU_AGPL_V3 = SoftwareLicense(
    "GNU AGPLv3",
    description="""\
Permissions of this strongest copyleft license are conditioned on making available complete source code of 
licensed works and modifications, which include larger works using a licensed work, under the same license. Copyright 
and license notices must be preserved. Contributors provide an express grant of patent rights. When a modified 
version is used to provide a service over a network, the complete source code of the modified version must be made 
available.
""",
    url="https://www.gnu.org/licenses/agpl-3.0.en.html"
)

GNU_GPL_V3 = SoftwareLicense(
    "GNU GPLv3",
    description="""\
Permissions of this strong copyleft license are conditioned on making available complete source code of licensed 
works and modifications, which include larger works using a licensed work, under the same license. Copyright and 
license notices must be preserved. Contributors provide an express grant of patent rights.
""",
    url="https://www.gnu.org/licenses/gpl-3.0.html"
)

GNU_LGPL_V3 = SoftwareLicense(
    "GNU LGPLv3",
    description="""\
Permissions of this copyleft license are conditioned on making available complete source code of licensed works 
and modifications under the same license or the GNU GPLv3. Copyright and license notices must be preserved. 
Contributors provide an express grant of patent rights. However, a larger work using the licensed work through 
interfaces provided by the licensed work may be distributed under different terms and without source code for the 
larger work. 
""",
    url="https://www.gnu.org/licenses/lgpl-3.0.html"
)

GNU_LGPL_V2 = SoftwareLicense(
    "GNU LGPLv2",
    description="""\
Permissions of this copyleft license are conditioned on making available complete source code of licensed works 
and modifications under the same license or the GNU GPLv2. Copyright and license notices must be preserved. 
Contributors provide an express grant of patent rights. However, a larger work using the licensed work through 
interfaces provided by the licensed work may be distributed under different terms and without source code for the 
larger work. 
""",
    url="https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html"
)

MOZILLA_V2 = SoftwareLicense(
    "Mozilla Public License 2.0",
    description="""\
Permissions of this weak copyleft license are conditioned on making available source code of licensed files and 
modifications of those files under the same license (or in certain cases, one of the GNU licenses). Copyright and 
license notices must be preserved. Contributors provide an express grant of patent rights. However, a larger work 
using the licensed work may be distributed under different terms and without source code for files added in the 
larger work.
""",
    url="https://www.mozilla.org/en-US/MPL/"
)

APACHE_V2 = SoftwareLicense(
    "Apache License 2.0",
    description="""\
A permissive license whose main conditions require preservation of copyright and license notices. Contributors 
provide an express grant of patent rights. Licensed works, modifications, and larger works may be distributed under 
different terms and without source code. 
""",
    url="https://www.apache.org/licenses/LICENSE-2.0"
)

MIT = SoftwareLicense(
    "MIT License",
    description="""\
A short and simple permissive license with conditions only requiring preservation of copyright and license notices. 
Licensed works, modifications, and larger works may be distributed under different terms and without source code. 
""",
    url="https://opensource.org/licenses/MIT"
)

BOOST = SoftwareLicense(
    "Boost Software License 1.0",
    description="""\
A simple permissive license only requiring preservation of copyright and license notices for source (and not binary) 
distribution. Licensed works, modifications, and larger works may be distributed under different terms and without 
source code. 
""",
    url="https://www.boost.org/users/license.html"
)

UNLICENSE = SoftwareLicense(
    "The Unlicense",
    description="""\
A license with no conditions whatsoever which dedicates works to the public domain. Unlicensed works, modifications, 
and larger works may be distributed under different terms and without source code.
""",
    url="https://unlicense.org/"
)

BSD = SoftwareLicense(
    "BSD License, 3-clause",
    url="https://opensource.org/licenses/BSD-3-Clause",
)

BSD_2CLAUSE = SoftwareLicense(
    "BSD License, 2-clause",
    url="https://opensource.org/licenses/BSD-2-Clause"
)

PSF = SoftwareLicense(
    "Python Software Foundation License",
    url="https://docs.python.org/3/license.html"
)

NOT_RELEVANT = SoftwareLicense(
    "Not relevant for licensing",
    description="This is simply a placeholder to denote that it is not relevant to say what the license of "
                "the software in question is. For example, it might be part of some other licensed software, "
                "whose license is already covered elsewhere."
)