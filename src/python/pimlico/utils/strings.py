# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html



def truncate(s, length, ellipsis=u"..."):
    if len(s) > length:
        return u"%s%s" % (s[:length-len(ellipsis)].strip(), ellipsis)
    else:
        return s
