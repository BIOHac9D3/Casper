import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.environment import (
    EnvironmentDetector,
    EnvironmentInfo,
    Platform,
    detect_environment,
    get_platform,
    is_supported_platform
)


def test_platform_enum():
    assert Platform.TERMUX.value == "termux"
    assert Platform.LINUX.value == "linux"
    assert Platform.MACOS.value == "macos"
    assert Platform.WINDOWS.value == "windows"
    assert Platform.DOCKER.value == "docker"
    assert Platform.UNKNOWN.value == "unknown"


def test_environment_info_is_supported():
    for platform in [Platform.TERMUX, Platform.LINUX, Platform.MACOS, Platform.WINDOWS, Platform.DOCKER]:
        info = EnvironmentInfo(
            platform=platform,
            is_termux=False,
            is_docker=False,
            python_version="3.12.0",
            python_executable="/usr/bin/python3",
            node_version=None,
            node_executable=None,
            architecture="x86_64",
            home_directory=Path("/home/user"),
            temp_directory=Path("/tmp"),
            current_directory=Path("/app")
        )
        assert info.is_supported() is True
    
    info = EnvironmentInfo(
        platform=Platform.UNKNOWN,
        is_termux=False,
        is_docker=False,
        python_version="3.12.0",
        python_executable="/usr/bin/python3",
        node_version=None,
        node_executable=None,
        architecture="x86_64",
        home_directory=Path("/home/user"),
        temp_directory=Path("/tmp"),
        current_directory=Path("/app")
    )
    assert info.is_supported() is False


def test_detect_environment():
    result = detect_environment()
    assert isinstance(result, EnvironmentInfo)
    assert isinstance(result.platform, Platform)


def test_get_platform():
    platform = get_platform()
    assert isinstance(platform, Platform)


def test_is_supported_platform():
    result = is_supported_platform()
    assert isinstance(result, bool)