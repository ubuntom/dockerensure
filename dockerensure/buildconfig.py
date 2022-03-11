import subprocess
from dataclasses import dataclass, field
from typing import List, Optional

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
    """

    dockerfile: str
    build_args: dict = field(default_factory=dict)
    parents: List["DockerImage"] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    excludes: Optional[List[str]] = None
    metadata: str = ""
    interval: Optional[IntervalOffset] = None

    def is_hashable(self):
        if self.dependencies is None or self.excludes is not None:
            return False

        return True

    def get_hash(self):

        hasher = Hasher()
        hasher.add_file(self.dockerfile)
        for arg, value in self.build_args.items():
            hasher.add_str(arg)
            hasher.add_str(value)
        for parent in self.parents:
            hasher.add_str(parent.name)
        for dependency in self.dependencies:
            hasher.add_file(dependency)
        if self.excludes:
            for exclude in self.excludes:
                hasher.add_str(exclude)
        else:
            hasher.add_str("!NoExcludes")

        hasher.add_str(self.metadata)
        if self.interval:
            hasher.add_str(str(self.interval.get_intervals()))

        return hasher.hexdigest()[:16]

    @staticmethod
    def create_docker_ignore_file(dependencies=None, excludes=None):
        """
        Create a dockerignore file that either ignores everything but the given dependencies
        or ignores the given exclude paths.
        """
        if excludes is None:
            excludes = ["**"] if dependencies else []

        lines = excludes
        if dependencies:
            lines += [f"!{path}" for path in dependencies]

        print(lines)
        with open(".dockerignore", "w") as ignore_file:
            ignore_file.write("\n".join(lines))

    def build_image(self, name):
        """
        Builds an image with the config contained in this class.

        Parent images that this image depends on will be prepared first.
        """
        for parent in self.parents:
            parent.ensure()

        self.create_docker_ignore_file(self.dependencies, self.excludes)

        args = ["docker", "build", "-t", name, ".", "-f", self.dockerfile]
        for arg, value in self.build_args.items():
            args.extend(["--build-arg", f"{arg}={value}"])

        subprocess.run(args, check=True)
