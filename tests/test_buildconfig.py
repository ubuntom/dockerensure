from unittest.mock import Mock, mock_open, patch

import pytest

from dockerensure.buildconfig import BuildConfig


@pytest.mark.parametrize(
    "dependencies,excludes,output",
    [
        (["includeme"], ["excludeme"], "excludeme\n!includeme"),
        (["includeme", "andme"], None, "**\n!includeme\n!andme"),
        (["includeme"], [], "!includeme"),
        ([], None, ""),
    ],
)
def test_ignore_file(dependencies, excludes, output):
    with patch("dockerensure.buildconfig.open", mock_open()) as mo:
        BuildConfig.create_docker_ignore_file(dependencies, excludes)

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
