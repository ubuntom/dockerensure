import os
from unittest.mock import Mock, patch

import pytest

from dockerensure.image import DockerImage, RemotePolicy
from dockerensure.registry import DockerRegistry
from dockerensure.buildconfig import BuildConfig, FilePolicy


@pytest.fixture
def hashable_buildconfig():
    with open("testfile", "w") as f:
        f.write("# Dockerfile")
        f.flush()

        yield BuildConfig(f.name, files=FilePolicy.Only([f.name]))

    os.remove("testfile")


class TestName:
    def test_basename(self):
        assert DockerImage("base").reference == "base"

    def test_versioned_name(self):
        assert DockerImage("base", version="1.1").reference == "base:1.1"

    def test_hashed_name(self, hashable_buildconfig):
        image = DockerImage("base", with_hash=True, build_config=hashable_buildconfig)
        assert image.reference == "base:76cb7a29a968388f"

    def test_hash_without_config(self):
        with pytest.raises(DockerImage.UnhashableReferenceException):
            DockerImage("base", with_hash=True)

    def test_hash_unhashable_config(self):
        with pytest.raises(DockerImage.UnhashableReferenceException):
            DockerImage("base", with_hash=True, build_config=BuildConfig())

    def test_prepend_server(self):
        image = DockerImage("base", registry=DockerRegistry("docker.io"))
        assert image.registry_reference == "docker.io/base"


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

    def test_remote_pull_no_registry(self):
        di = DockerImage("test")
        di.has_local_image = Mock(return_value=False)

        with pytest.raises(DockerImage.BuildFailedException):
            di.ensure()

    def test_remote_pull_with_registry(self):
        mock_registry = Mock(spec=DockerRegistry)
        di = DockerImage("test", registry=mock_registry)
        di.has_local_image = Mock(return_value=False)

        di.ensure()

        mock_registry.try_pull_image.assert_called_once()

    def test_remote_pull_with_registry_no_pull(self):
        mock_registry = Mock(spec=DockerRegistry)
        di = DockerImage(
            "test", registry=mock_registry, remote_policy=RemotePolicy.PUSH_ONLY
        )
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
        mock_registry = Mock(spec=DockerRegistry)
        di = DockerImage(
            "test",
            build_config=mock_bc,
            registry=mock_registry,
            remote_policy=RemotePolicy.PUSH_ONLY,
        )
        di.has_local_image = Mock(return_value=False)

        di.ensure()

        mock_registry.push_image.assert_called_once()

        out = capsys.readouterr().out
        assert "Pushing image" in out
        assert "Built image" in out
