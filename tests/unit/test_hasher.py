import hashlib
import tempfile

from dockerensure.hasher import Hasher


def test_hash_string():
    hasher = Hasher()
    hasher.add_str("test")

    assert (
        hasher.hexdigest()
        == "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
    )


def test_hash_strings():
    hasher = Hasher()
    hasher.add_str("test")
    hasher.add_str("string")

    assert (
        hasher.hexdigest()
        == "3c8727e019a42b444667a587b6001251becadabbb36bfed8087a92c18882d111"
    )


def test_hash_file():
    expected = hashlib.sha256()

    with tempfile.NamedTemporaryFile("w") as f:
        expected.update(f.name.encode("utf-8"))
        expected.update(b"test")

        f.write("test")
        f.flush()

        hasher = Hasher()
        hasher.add_file(f.name)

    assert hasher.hexdigest() == expected.hexdigest()
