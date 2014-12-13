# Copyright (c) 2011-2014 Kyle Gorman and Michael Wagner
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
Serialization/deserialization functionality using `shutil`
"""

from tempfile import mkdtemp
from os import getcwd, environ, path, walk
from shutil import rmtree, make_archive, unpack_archive


# default format for output
FORMAT = "gztar"


class Archive(object):

    """
    Class representing data in a directory or archive file (zip, tar, 
    tar.gz/tgz)
    """

    def __init__(self, source):
        self.is_tmpdir = False
        if path.isdir(source):
            self.dirname = path.abspath(source)
        else:
            # place to put the archive once its unpacked
            base = mkdtemp(dir=environ.get("TMPDIR", None))
            # where it will be unpacked to
            unpack_archive(source, base)
            (head, tail, _) = next(walk(base))
            if not tail:
                raise ValueError("'{}' is empty.".format(source))
            if len(tail) > 1:
                raise ValueError("'{}' is a bomb.".format(source))
            self.dirname = path.join(head, tail[0])
            self.is_tmpdir = True

    def __repr__(self):
        return "{}(dirname={!r})".format(self.__class__.__name__,
                                         self.dirname)

    def dump(self, sink, archive_fmt=FORMAT):
        """
        Write archive to disk, and return the name of final archive
        """
        (head, tail) = path.split(self.dirname)
        return make_archive(sink, archive_fmt, head, tail)

    def __del__(self):
        if self.is_tmpdir:
            rmtree(self.dirname)
