from unittest.mock import patch

from dockerensure.registry import DockerRegistry


@patch("subprocess.run")
def test_login(mock_run):
    reg = DockerRegistry("docker.io", "user", "pass")
    reg.login()

    assert (
        " ".join(mock_run.call_args.args[0]) == "docker login docker.io -u user -p pass"
    )


@patch("subprocess.run")
def test_login_twice(mock_run):
    reg = DockerRegistry("docker.io", "user", "pass")
    reg.login()
    reg.login()

    assert mock_run.call_count == 1


@patch("subprocess.run")
def test_login_no_user(mock_run):
    reg = DockerRegistry("docker.io")
    reg.login()

    assert mock_run.call_count == 0


def test_prepend_server():
    reg = DockerRegistry("docker.io")
    assert reg.prepend_server("imagename") == "docker.io/imagename"


def test_prepend_server_default():
    reg = DockerRegistry(None)
    assert reg.prepend_server("imagename") == "imagename"


@patch("subprocess.run")
def test_try_pull_exists_prepend(mock_run):
    reg = DockerRegistry("docker.io")

    assert reg.try_pull_image("docker.io/test", False) is True

    assert mock_run.call_count == 1
    assert "docker.io/test" in mock_run.call_args.args[0]


@patch("subprocess.run")
def test_try_pull_exists_prepend(mock_run):
    reg = DockerRegistry("docker.io")

    assert reg.try_pull_image("test", True) is True

    assert mock_run.call_count == 2
    assert "docker.io/test" in mock_run.call_args_list[0].args[0]
    assert " ".join(mock_run.call_args.args[0]) == "docker tag docker.io/test test"


@patch("subprocess.run")
def test_try_pull_not_exists(mock_run):
    reg = DockerRegistry("docker.io")

    mock_run.side_effect = Exception("Bad")

    assert reg.try_pull_image("test", True) is False

    assert mock_run.call_count == 1
    assert "docker.io/test" in mock_run.call_args.args[0]


@patch("subprocess.run")
def test_push(mock_run):
    reg = DockerRegistry("docker.io")

    reg.push_image("test", True)

    assert mock_run.call_count == 2
    assert (
        " ".join(mock_run.call_args_list[0].args[0]) == "docker tag test docker.io/test"
    )
    assert "docker.io/test" in mock_run.call_args.args[0]


def test_docker_image_shortcut():
    reg = DockerRegistry("docker.io")
    image = reg.image("test")
    assert image.registry == reg
