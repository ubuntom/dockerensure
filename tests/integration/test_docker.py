import subprocess
from pathlib import Path

from dockerensure import BuildConfig, DockerImage
from dockerensure.filepolicy import FilePolicy


def test_make_image():
    DockerImage("test-image", BuildConfig(directory="tests/integration/test1")).ensure()


def test_make_image_with_parent():
    parent = DockerImage(
        "test-parent", BuildConfig(directory="tests/integration/test1")
    )

    child = DockerImage(
        "test-child",
        with_hash=True,
        build_config=BuildConfig(
            files=FilePolicy.Nothing,
            directory="tests/integration/test2",
            build_args={"BASE": parent.ref},
            parents=[parent],
        ),
    )

    child.ensure()

    p = subprocess.run(
        ["docker", "run", child.ref, "cat", "myfile"], stdout=subprocess.PIPE
    )
    assert b"1\n2" in p.stdout


def test_ignore_file():
    image = DockerImage(
        "test-ignore",
        BuildConfig(
            files=FilePolicy.Nothing, directory="tests/integration/test_ignore_file"
        ),
    )
    image.ensure()

    p = subprocess.run(
        ["docker", "run", image.ref, "ls", "Dockerfile"], stdout=subprocess.PIPE
    )
    assert b"Dockerfile" not in p.stdout


def test_file_hash():
    test_path = Path("tests/integration/test_hash_file")

    with open(test_path / "test_artifact_hash", "w") as f:
        f.write("abc")

    image_1 = DockerImage(
        "test-hash-1", BuildConfig(files=FilePolicy.All, directory=test_path)
    )

    with open(test_path / "test_artifact_hash", "w") as f:
        f.write("axyz")

    image_2 = DockerImage(
        "test-hash-2", BuildConfig(files=FilePolicy.All, directory=test_path)
    )

    assert image_1.ref != image_2.ref
