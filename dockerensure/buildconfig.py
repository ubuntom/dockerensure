import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from os import PathLike
from pathlib import Path
from typing import List, Optional, Union

from .filepolicy import FilePolicy
from .hasher import Hasher
from .utils import IntervalOffset


@dataclass
class BuildConfig:
    """
    Stores all data needed to build an image. All inputs to a build should be contained here.

    A hash of all inputs can be produced - if two builds have the same hash they have the same inputs
    and thus should produce the same image.

    Params:
    dockerfile: The dockerfile to build with
    build_args: Docker build_args
    parents: List of images that this image depends on
    dependencies: List of files used by this build.
    excludes: List of files to exclude from this build.
        If this is None and dependencies exist then all other files will be excluded.
    metadata: Additional metadata to include in the hash
    interval: An interval to refresh the hash after. For example, if you want to force a re-build every day set this interval to one day
    directory: Directory to set the build context to. Leave as None for the current directory
    """

    dockerfile: str = "Dockerfile"
    build_args: dict = field(default_factory=dict)
    parents: List["DockerImage"] = field(default_factory=list)
    files: FilePolicy = FilePolicy.All
    metadata: str = ""
    interval: Optional[IntervalOffset] = None
    directory: Union[None, str, PathLike] = None

    def __post_init__(self):
        self.directory = Path(self.directory) if self.directory else None

    def is_hashable(self):
        if self.files == FilePolicy.All or self.files == FilePolicy.AllBut:
            return False

        return True

    def get_relative(self, path):
        if self.directory is None:
            return path

        return self.directory / path

    def add_files_to_hash(self, hasher):
        assert self.files != FilePolicy.All
        assert self.files != FilePolicy.AllBut

        if self.files == FilePolicy.Nothing:
            return

        if type(self.files) == FilePolicy.Only:
            for file in self.files.exceptions:
                hasher.add_file(self.get_relative(file))

    def get_hash(self):

        hasher = Hasher()
        hasher.add_file(self.get_relative(self.dockerfile))
        for arg, value in self.build_args.items():
            hasher.add_str(arg)
            hasher.add_str(value)
        for parent in self.parents:
            hasher.add_str(parent.name)

        self.add_files_to_hash(hasher)

        hasher.add_str(self.metadata)
        if self.interval:
            hasher.add_str(str(self.interval.get_intervals()))

        return hasher.hexdigest()[:16]

    def create_docker_ignore_file(self):
        """
        Create a dockerignore file that either ignores everything but the given dependencies
        or ignores the given exclude paths.
        """

        lines = []
        policy_class = type(self.files)
        if self.files == FilePolicy.Nothing:
            lines = ["**"]
        elif policy_class == FilePolicy.Only:
            lines = ["**"] + [f"!{path}" for path in self.files.exceptions]
        elif policy_class == FilePolicy.AllBut:
            lines = self.files.exceptions
        elif self.files == FilePolicy.All:
            lines = []

        print(lines)
        print(self.files)

        with open(self.get_relative(".dockerignore"), "w") as ignore_file:
            ignore_file.write("\n".join(lines))

    def build_image(self, name):
        """
        Builds an image with the config contained in this class.

        Parent images that this image depends on will be prepared first.
        """
        for parent in self.parents:
            parent.ensure()

        self.create_docker_ignore_file()

        args = ["docker", "build", "-t", name, ".", "-f", self.dockerfile]
        for arg, value in self.build_args.items():
            args.extend(["--build-arg", f"{arg}={value}"])

        subprocess.run(args, check=True, cwd=self.directory)
