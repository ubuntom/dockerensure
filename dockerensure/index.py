from dataclasses import dataclass
from subprocess import run
from typing import Optional

from .image import DockerImage


@dataclass
class DockerIndex:
    """
    Provides functions to interact with a remote Docker server: logging in, pushing and pulling images.
    """

    server: Optional[str]
    username: str
    password: str

    def __post_init__(self):
        self.loggedin = False

    def login(self):
        if self.loggedin:
            return

        self.loggedin = True

        args = ["docker", "login", "-u", self.username, "-p", self.password]
        if self.server:
            args += [self.server]
        run(args, check=True)

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
            run(["docker", "pull", remote_name], check=True)
        except Exception as e:
            return False

        if prepend_server:
            run(["docker", "tag", remote_name, local_name], check=True)

        return True

    def push_image(self, local_name, prepend_server):
        self.login()

        remote_name = local_name
        if prepend_server:
            remote_name = self.prepend_server(local_name)

            run(["docker", "tag", local_name, remote_name], check=True)

        run(["docker", "push", remote_name], check=True)

    def image(self, *args, **kwargs):
        """
        Constructs a DockerImage that uses this index
        """
        return DockerImage(*args, index=self, **kwargs)