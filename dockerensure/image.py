import enum
import subprocess
from dataclasses import dataclass
from functools import cached_property
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
    with_hash: If true the build config state hash will be appended to the name

    version: Optional version string to add to the tag

    index:  DockerIndex object for builds using a remote server
    prepend_server: If true, the server url will be prepended to the image name before pushing. Set this to false
        if you have already added the remote repository to the base name (e.g. remote.repo/image_name)
    remote_policy:  How the remote server will be used to push and pull images
    """

    base_name: str
    build_config: BuildConfig = None
    with_hash: bool = False

    version: Optional[str] = None

    index: Optional["DockerIndex"] = None
    prepend_server: bool = True
    remote_policy: RemotePolicy = RemotePolicy.ALL

    class BuildFailedException(Exception):
        pass

    def __post_init__(self):
        if self.with_hash:
            if self.build_config is None:
                raise Exception(
                    f"The image {self.base_name} is configured to have a state hash appended to its tag, but the build config is None. "
                    "Please disable appending the hash on the tag (with_hash = False) or add a build config."
                )

            if not self.build_config.is_hashable():
                raise Exception(
                    f"The image {self.base_name} is configured to have a state hash appended to its tag, but the config is unhashable. "
                    "Please disable appending the hash on the tag (with_hash = False) or change the build config to make it hashable."
                )

    def has_local_image(self):
        """
        Check if the image exists locally
        """
        p = subprocess.run(
            ["docker", "image", "inspect", self.name], stdout=subprocess.DEVNULL
        )
        return p.returncode == 0

    @cached_property
    def name(self):
        """
        Returns the full name and tag for the image using a hash of its dependencies.
        """

        tag_parts = []

        if self.version:
            tag_parts.append(self.version)

        if self.with_hash:
            tag_parts.append(self.build_config.get_hash())

        if not tag_parts:
            return self.base_name

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

        if self.build_config is None:
            raise DockerImage.BuildFailedException(
                f"Image {self.name} has no build config and doesn't already exist, so it can't be ensured."
            )

        self.build_config.build_image(self.name)

        if self.index and self.remote_policy in {
            RemotePolicy.ALL,
            RemotePolicy.PUSH_ONLY,
        }:
            print("Pushing image")
            self.index.push_image(self.name, self.prepend_server)

        print("<<< Built image <<<")

        return
