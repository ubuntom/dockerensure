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
    NONE = enum.auto()  # The server will not be used for anything


@dataclass
class DockerImage:
    """

    Params:
    name: The name of the image
    build_config:  Config to describe how to build the image
    with_hash: If true the build config state hash will be appended to the tag
    force_build: Force building of the image even if it already exists

    version: Optional version string to add to the tag
    hash_len: Length of the hash to append if ` with_hash` is True. Default is 16

    registry:  DockerRegistry object for builds using a remote server
    prepend_server: If true, the server url will be prepended to the image name before pushing. Set this to false
        if you have already prepended the registry to the image name (e.g. docker.io/image_name)
    remote_policy:  How the remote server will be used to push and pull images
    """

    name: str
    build_config: BuildConfig = None
    with_hash: bool = False
    force_build: bool = False

    version: Optional[str] = None
    hash_len: int = 16

    registry: Optional["DockerRegistry"] = None
    prepend_server: bool = True
    remote_policy: RemotePolicy = RemotePolicy.ALL

    class BuildFailedException(Exception):
        pass

    class UnhashableReferenceException(Exception):
        pass

    def __post_init__(self):
        if self.with_hash:
            if self.build_config is None:
                raise DockerImage.UnhashableReferenceException(
                    f"The image {self.name} is configured to have a state hash appended to its tag, but the build config is None. "
                    "Please disable appending the hash on the tag (with_hash = False) or add a build config."
                )

            if not self.build_config.is_hashable():
                raise DockerImage.UnhashableReferenceException(
                    f"The image {self.name} is configured to have a state hash appended to its tag, but the config is unhashable. "
                    "Please disable appending the hash on the tag (with_hash = False) or change the build config to make it hashable."
                )

    def has_local_image(self):
        """
        Check if the image exists locally
        """
        p = subprocess.run(
            ["docker", "image", "inspect", self.ref], stdout=subprocess.DEVNULL
        )
        return p.returncode == 0

    @cached_property
    def reference(self):
        """
        Returns the reference string (e.g. image:tag-1.0-ab01) for the image using a hash of its dependencies.
        """

        tag_parts = []

        if self.version:
            tag_parts.append(self.version)

        if self.with_hash:
            tag_parts.append(self.build_config.get_hash()[: self.hash_len])

        if not tag_parts:
            return self.name

        return self.name + ":" + "-".join(tag_parts)

    @property
    def ref(self):
        return self.reference

    @cached_property
    def registry_reference(self):
        """
        Returns the registry prepended to the reference string (e.g. docker.io/image:tag).
        """

        return self.registry.prepend_server(self.reference)

    def check_existence(self):
        if self.has_local_image():
            print("<<< Image already exists locally <<<")
            return True

        if self.registry and self.remote_policy in {
            RemotePolicy.ALL,
            RemotePolicy.PULL_ONLY,
        }:
            print("Checking for image on server...")
            if self.registry.try_pull_image(self.ref, self.prepend_server):
                print("<<< Pulled image from server <<<")
                return True

        return False

    def ensure(self):
        """
        Ensures that the image is available on the local system.
        By the time this function returns, the image will exist. It will be downloaded or built if necessary.
        """
        print(f">>> Ensuring image {self.ref} >>>")

        if not self.force_build and self.check_existence():
            return

        if self.build_config is None:
            raise DockerImage.BuildFailedException(
                f"Image {self.ref} needs to be built but it has no build config, so it can't be ensured."
            )

        print(f"Building {self.ref}")
        self.build_config.build_image(self.ref)

        if self.registry and self.remote_policy in {
            RemotePolicy.ALL,
            RemotePolicy.PUSH_ONLY,
        }:
            print("Pushing image")
            self.registry.push_image(self.ref, self.prepend_server)

        print("<<< Built image <<<")

        return
