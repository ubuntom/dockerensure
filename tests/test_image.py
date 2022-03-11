import os
import tempfile
from unittest.mock import Mock, patch

import pytest

from dockerensure.image import BuildConfig, DockerImage, RemotePolicy
from dockerensure.index import DockerIndex


@pytest.fixture
def hashable_buildconfig():
    with open("testfile", "w") as f:
        f.write("# Dockerfile")
        f.flush()

        yield BuildConfig(f.name, dependencies=[f.name])

    os.remove("testfile")


class TestName:
    def test_basename(self):
        assert DockerImage("base").name == "base"

    def test_versioned_name(self):
        assert DockerImage("base", version="1.1").name == "base:1.1"

    def test_hashed_name(self, hashable_buildconfig):
        assert (
            DockerImage("base", with_hash=True, build_config=hashable_buildconfig).name
            == "base:ca1c0c0c6dc9944f"
        )


class TestLocalImage:
    @patch("subprocess.run")
    def test_image_exists(self, mock_run):
        mock_run.return_value.returncode = 0

        assert DockerImage("test").has_local_image() is True

    @patch("subprocess.run")
    def test_image_not_exists(self, mock_run):
        mock_run.return_value.returncode = 1

        assert DockerImage("test").has_local_image() is False


class TestEnsure:
    def test_exists_locally(self, capsys):
        di = DockerImage("test")
        di.has_local_image = Mock(return_value=True)

        di.ensure()

        assert "exists locally" in capsys.readouterr().out

    def test_remote_pull_no_index(self):
        di = DockerImage("test")
        di.has_local_image = Mock(return_value=False)

        with pytest.raises(DockerImage.BuildFailedException):
            di.ensure()

    def test_remote_pull_with_index(self):
        mock_index = Mock(spec=DockerIndex)
        di = DockerImage("test", index=mock_index)
        di.has_local_image = Mock(return_value=False)

        di.ensure()

        mock_index.try_pull_image.assert_called_once()

    def test_remote_pull_with_index_no_pull(self):
        mock_index = Mock(spec=DockerIndex)
        di = DockerImage("test", index=mock_index, remote_policy=RemotePolicy.PUSH_ONLY)
        di.has_local_image = Mock(return_value=False)

        with pytest.raises(DockerImage.BuildFailedException):
            di.ensure()

    def test_build(self, capsys):
        mock_bc = Mock(spec=BuildConfig)
        di = DockerImage("test", build_config=mock_bc)
        di.has_local_image = Mock(return_value=False)

        di.ensure()

        assert "Built image" in capsys.readouterr().out

    def test_push(self, capsys):
        mock_bc = Mock(spec=BuildConfig)
        mock_index = Mock(spec=DockerIndex)
        di = DockerImage(
            "test",
            build_config=mock_bc,
            index=mock_index,
            remote_policy=RemotePolicy.PUSH_ONLY,
        )
        di.has_local_image = Mock(return_value=False)

        di.ensure()

        mock_index.push_image.assert_called_once()

        out = capsys.readouterr().out
        assert "Pushing image" in out
        assert "Built image" in out
