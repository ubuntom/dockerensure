import subprocess
from dataclasses import dataclass
from typing import Optional

from .image import DockerImage


@dataclass
class DockerRegistry:
    """
    Provides functions to interact with a remote Docker server: logging in, pushing and pulling images.
    """

    server: Optional[str]  # Set to None for the default Docker registry
    username: Optional[str] = None
    password: Optional[str] = None

    def __post_init__(self):
        self.loggedin = False

    def login(self):
        if self.loggedin:
            return

        if not self.username:
            return

        self.loggedin = True

        args = ["docker", "login"]
        if self.server:
            args += [self.server]
        args += ["-u", self.username, "-p", self.password]
        subprocess.run(args, check=True)

    def prepend_server(self, name):
        if not self.server:
            return name
        return self.server + "/" + name

    def try_pull_image(self, local_name, prepend_server):
        self.login()

        remote_name = local_name
        if prepend_server:
            remote_name = self.prepend_server(local_name)

        try:
            subprocess.run(["docker", "pull", remote_name], check=True)
        except Exception as e:
            return False

        if prepend_server:
            subprocess.run(["docker", "tag", remote_name, local_name], check=True)

        return True

    def push_image(self, local_name, prepend_server):
        self.login()

        remote_name = local_name
        if prepend_server:
            remote_name = self.prepend_server(local_name)

            subprocess.run(["docker", "tag", local_name, remote_name], check=True)

        subprocess.run(["docker", "push", remote_name], check=True)

    def image(self, *args, **kwargs):
        """
        Constructs a DockerImage that uses this index
        """
        return DockerImage(*args, registry=self, **kwargs)
