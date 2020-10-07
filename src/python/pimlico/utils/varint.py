# This file is not part of Pimlico, but largely copied
# Copyright (C) 2016 Peter Ruibal
# Licensed under the MIT License

"""Varint encoder/decoder

Implementation of a variable-length integer encoding scheme.

Based on implementation by Peter Ruibal:
  https://github.com/fmoo/python-varint

It's copied here so we can use it stably without adding a dependency.

**License**:
Since this is copied from someone else's code, its license is that of the original code,
the MIT license. See LICENSE below for details.

Varints are a common encoding for variable-length integer data, used in
libraries such as sqlite, protobuf, v8, and more.

Here's a quick and dirty module to help avoid reimplementing the same thing
over and over again.

"""
# Byte-oriented StringIO was moved to io.BytesIO in py3k
try:
    from io import BytesIO
except ImportError:
    from StringIO import StringIO as BytesIO

import sys

if sys.version > '3':
    def _byte(b):
        return bytes((b, ))
else:
    def _byte(b):
        return chr(b)


def encode(number):
    """Pack `number` into varint bytes"""
    buf = b''
    while True:
        towrite = number & 0x7f
        number >>= 7
        if number:
            buf += _byte(towrite | 0x80)
        else:
            buf += _byte(towrite)
            break
    return buf


def decode_stream(stream):
    """Read a varint from `stream`"""
    shift = 0
    result = 0
    while True:
        i = _read_one(stream)
        result |= (i & 0x7f) << shift
        shift += 7
        if not (i & 0x80):
            break

    return result


def decode_bytes(buf):
    """Read a varint from from `buf` bytes"""
    return decode_stream(BytesIO(buf))


def _read_one(stream):
    """Read a byte from the file (as an integer)

    raises EOFError if the stream ends while reading bytes.
    """
    c = stream.read(1)
    if c == b'':
        raise EOFError("Unexpected EOF while reading bytes")
    return ord(c)


LICENSE = """
The MIT License (MIT)

Copyright (c) 2016 Peter Ruibal

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""