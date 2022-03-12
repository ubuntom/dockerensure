from unittest.mock import Mock, mock_open, patch

import pytest

from dockerensure.buildconfig import BuildConfig
from dockerensure.filepolicy import FilePolicy


@pytest.mark.parametrize(
    "policy,output",
    [
        (FilePolicy.All, ""),
        (FilePolicy.Nothing, "**"),
        (FilePolicy.AllBut(["this"]), "this"),
        (FilePolicy.Only(["this"]), "**\n!this"),
    ],
)
def test_ignore_file(policy, output):
    with patch("dockerensure.buildconfig.open", mock_open()) as mo:
        config = BuildConfig(files=policy)
        config.create_docker_ignore_file()

        mo().write.assert_called_once_with(output)


@patch.object(BuildConfig, "create_docker_ignore_file", Mock())
@patch("subprocess.run", Mock())
def test_parents_ensured():
    parent = Mock()
    BuildConfig(".", parents=[parent]).build_image("test")

    parent.ensure.assert_called_once()


@patch.object(BuildConfig, "create_docker_ignore_file", Mock())
@patch("subprocess.run")
def test_build_args(mock_run):
    dockerfile = "Dockerfile"
    img_name = "test"
    BuildConfig(dockerfile, build_args={"PROD": "true"}).build_image(img_name)

    assert (
        " ".join(mock_run.call_args.args[0])
        == f"docker build -t {img_name} . -f {dockerfile} --build-arg PROD=true"
    )
