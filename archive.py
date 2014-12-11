from tempfile import mkdtemp
from os import getcwd, environ, path, walk
from shutil import make_archive, unpack_archive


# default format for output
FORMAT = "gztar" 


class Archive(object):

    def __init__(self, source):
        if path.isdir(source):
            self.dirname = path.abspath(source)
        else:
            base = mkdtemp(dir=environ.get("TMPDIR", None))
            unpack_archive(source, base)
            (head, tail, _) = next(walk(base))
            if not tail:
                raise ValueError("'{}' is empty.".format(source))
            if len(tail) > 1:
                raise ValueError("'{}' is a bomb.".format(source))
            self.dirname = path.join(head, tail[0])

    def __repr__(self):
        return "{}(dirname={!r})".format(self.__class__.__name__,
                                         self.dirname)

    def dump(self, sink, format=FORMAT):
        """
        Write archive to disk, and return the name of final archive
        """
        (head, tail) = path.split(self.dirname)
        return make_archive(sink, format, head, tail)
