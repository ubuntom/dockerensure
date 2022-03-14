import hashlib


class Hasher:
    """
    Simple class to handle hashing of file data and strings.
    """

    def __init__(self):
        self.hash = hashlib.sha256()

    def add_file(self, path):
        self.add_str(str(path))
        with open(path, "rb") as f:
            self.hash.update(f.read())

    def add_str(self, string):
        self.hash.update(string.encode("utf-8"))

    def hexdigest(self):
        return self.hash.hexdigest()
