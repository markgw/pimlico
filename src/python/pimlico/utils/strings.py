

def truncate(s, length, ellipsis=u"..."):
    if len(s) > length:
        return u"%s%s" % (s[:length-len(ellipsis)].strip(), ellipsis)
    else:
        return s
