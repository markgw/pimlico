import random


def limited_shuffle(iterable, buffer_size):
    """
    Some algorithms require the order of data to be randomized. An obvious solution is to put it all in
    a list and shuffle, but if you don't want to load it all into memory that's not an option. This method
    iterates over the data, keeping a buffer and choosing at random from the buffer what to put next.
    It's less shuffled than the simpler solution, but limits the amount of memory used at any one time
    to the buffer size.

    """
    buffer = []
    try:
        while len(buffer) < buffer_size:
            buffer.append(iterable.next())

        for next_val in iterable:
            # Pick a random item from the buffer to remove
            index = random.randint(0, len(buffer)-1)
            yield buffer.pop(index)
            # Add the new value to the buffer to replace the old one
            buffer.append(next_val)
    except StopIteration:
        # No more to take in, just return the rest in a random order
        random.shuffle(buffer)
        for v in buffer:
            yield v
