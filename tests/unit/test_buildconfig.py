from datetime import timedelta
from unittest.mock import Mock, mock_open, patch

import pytest

from dockerensure.buildconfig import BuildConfig, IntervalOffset
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


def test_unhashable():
    assert BuildConfig(files=FilePolicy.All).is_hashable() is False


@patch("dockerensure.buildconfig.Hasher.add_file", Mock())
def test_interval_hash():
    BuildConfig(
        files=FilePolicy.Nothing, interval=IntervalOffset(timedelta(days=1))
    ).get_hash()

@patch("dockerensure.buildconfig.Hasher.add_file", Mock())
def test_unhashed_args_state():
    """Test that unhashed build args don't contribute to the hash"""
    no_args = BuildConfig(files=FilePolicy.Nothing).get_hash()
    one_arg = BuildConfig(files=FilePolicy.Nothing, unhashed_build_args={"Test": "Hi"}).get_hash()
    two_args = BuildConfig(files=FilePolicy.Nothing, unhashed_build_args={"A":"B","X":"Y"}).get_hash()
    hash_arg = BuildConfig(files=FilePolicy.Nothing, build_args={"A":"B","X":"Y"}).get_hash()

    assert no_args == one_arg
    assert one_arg == two_args
    assert hash_arg != no_args

@patch("subprocess.run")
def test_unhashed_args_used(mock_run):
    """Test that unhashed build args are passed to the build"""
    BuildConfig(files=FilePolicy.Nothing, unhashed_build_args={"Test": "Hi"}).build_image("test")

    assert "Test=Hi" in mock_run.call_args.args[0]