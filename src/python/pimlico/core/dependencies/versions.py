

class SoftwareVersion(object):
    """
    Base class for representing version numbers / IDs of software. Different software may use different conventions
    to represent its versions, so it may be necessary to subclass this class to provide the appropriate parsing
    and comparison of versions.

    """
    def __init__(self, string_id):
        self.string_id = string_id

    def __str__(self):
        return self.string_id

    def __cmp__(self, other):
        if self.string_id == "unknown":
            if other.string_id == "unknown":
                return 0
            else:
                # Any known version is considered later than an unknown version
                return -1
        elif other.string_id == "unknown":
            return 1
        else:
            # Compare the string IDs on the assumption that they're dotted version numbers
            return compare_dotted_versions(self.string_id, other.string_id)


# Define here, so that it can easily be used symbolically
unknown_software_version = SoftwareVersion("unknown")


def compare_dotted_versions(version0, version1):
    """
    Comparison function for reasonably standard version numbers, with subversions to any level of nesting specified
    by dots.

    """
    remaining0 = version0
    remaining1 = version1

    while len(remaining0):
        if len(remaining1) == 0:
            # Version 0 has the same prefix, but specifies more subversions, so is a later release
            return 1
        version0_part, __, remaining0 = remaining0.partition(".")
        version1_part, __, remaining1 = remaining1.partition(".")
        # Don't distinguish letters by case
        version0_part, version1_part = version0_part.lower(), version1_part.lower()

        # Try converting both segments to ints
        try:
            version0_part_int = int(version0_part)
        except ValueError:
            # Version 0 isn't an int: see whether version 1 is
            try:
                int(version1_part)
            except ValueError:
                # Neither is an int: first check whether they're identical
                if version0_part == version1_part:
                    # Continue to next part
                    continue
                # Otherwise, compare string lexicographically and return result without looking at deeper parts
                return cmp(version0_part, version1_part)
            else:
                # V1 is an int, V0 isn't: int wins
                return -1
        try:
            version1_part_int = int(version1_part)
        except ValueError:
            # V1 isn't an int, but V0 is: int wins
            return 1
        # Both parts are ints
        if version0_part_int == version1_part_int:
            # Equal: continue to next level
            continue
        else:
            # Not the same: the one that wins at this level wins the whole thing
            return cmp(version0_part_int, version1_part_int)

    if len(remaining1) > 0:
        # Version 1 has same prefix, but more subversions, so is later
        return -1
    else:
        # Got to the end of both versions without reaching a conclusion: they must be equal
        return 0
