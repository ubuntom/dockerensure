import enum
import subprocess
from dataclasses import dataclass
from functools import cached_property
from subprocess import run
from typing import Optional

from .buildconfig import BuildConfig


class RemotePolicy(enum.Enum):
    """
    Defines how the remote server is used.
    """

    ALL = (
        enum.auto()
    )  # The server will be queried before building and the built image will be pushed
    PULL_ONLY = enum.auto()  # The build image will not be pushed
    PUSH_ONLY = enum.auto()  # The server will not be queried for the image


@dataclass
class DockerImage:
    """

    Params:
    base_name: The name of the image
    build_config:  Config to describe how to build the image
    no_hash: If true the build config hash will not be appended to the name

    version: Optional version string to add to the tag

    index:  DockerIndex object for builds using a remote server
    prepend_server: If true, the server url will be prepended to the image name before pushing. Set this to false
        if you have already added the remote repository to the base name (e.g. remote.repo/image_name)
    remote_policy:  How the remote server will be used to push and pull images
    """

    base_name: str
    build_config: BuildConfig
    no_hash: bool = False

    version: Optional[str] = None

    index: Optional["DockerIndex"] = None
    prepend_server: bool = True
    remote_policy: RemotePolicy = RemotePolicy.ALL

    def has_local_image(self):
        """
        Check if the image exists locally
        """
        p = run(["docker", "image", "inspect", self.name], stdout=subprocess.DEVNULL)
        return p.returncode == 0

    @cached_property
    def name(self):
        """
        Returns the full name and tag for the image using a hash of its dependencies.
        """

        tag_parts = []

        if self.version:
            tag_parts.append(self.version)

        tag_parts.append(self.build_config.get_hash())

        return self.base_name + ":" + "-".join(tag_parts)

    @cached_property
    def remote_name(self):
        return self.index.prepend_server(self.name)

    def ensure(self):
        """
        Ensures that the image is available on the local system.
        By the time this function returns, the image will exist. It will be downloaded or built if necessary.
        """
        print(f">>> Ensuring image {self.name} >>>")

        if self.has_local_image():
            print("<<< Image already exists locally <<<")
            return

        if self.index and self.remote_policy in {
            RemotePolicy.ALL,
            RemotePolicy.PULL_ONLY,
        }:
            print("Checking for image on server...")
            if self.index.try_pull_image(self.name, self.prepend_server):
                print("<<< Pulled image from server <<<")
                return

        self.build_config.build_image(self.name)

        if self.index and self.remote_policy in {
            RemotePolicy.ALL,
            RemotePolicy.PUSH_ONLY,
        }:
            print("Pushing image")
            self.index.push_image(self.name, self.prepend_server)

        print("<<< Built image <<<")

        return
