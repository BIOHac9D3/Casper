from __future__ import annotations

import os
import platform
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class Platform(Enum):
    """Supported platform types."""
    TERMUX = "termux"
    LINUX = "linux"
    MACOS = "macos"
    WINDOWS = "windows"
    DOCKER = "docker"
    UNKNOWN = "unknown"


@dataclass
class EnvironmentInfo:
    """Comprehensive environment information."""
    platform: Platform
    is_termux: bool
    is_docker: bool
    python_version: str
    python_executable: str
    node_version: Optional[str]
    node_executable: Optional[str]
    architecture: str
    home_directory: Path
    temp_directory: Path
    current_directory: Path
    
    def is_supported(self) -> bool:
        """Check if the current platform is supported."""
        return self.platform in {
            Platform.TERMUX,
            Platform.LINUX,
            Platform.MACOS,
            Platform.WINDOWS,
            Platform.DOCKER
        }


class EnvironmentDetector:
    """Detects and provides information about the execution environment."""
    
    @classmethod
    def detect(cls) -> EnvironmentInfo:
        """
        Detect the current execution environment.
        
        Returns:
            EnvironmentInfo: Complete environment information
        """
        platform_type = cls._detect_platform()
        is_termux = cls._detect_termux()
        is_docker = cls._detect_docker()
        
        python_version = cls._get_python_version()
        python_executable = cls._get_python_executable()
        
        node_version, node_executable = cls._get_node_info()
        
        architecture = platform.machine()
        home_directory = Path.home()
        temp_directory = Path(cls._get_temp_dir())
        current_directory = Path.cwd()
        
        return EnvironmentInfo(
            platform=platform_type,
            is_termux=is_termux,
            is_docker=is_docker,
            python_version=python_version,
            python_executable=python_executable,
            node_version=node_version,
            node_executable=node_executable,
            architecture=architecture,
            home_directory=home_directory,
            temp_directory=temp_directory,
            current_directory=current_directory
        )
    
    @classmethod
    def _detect_platform(cls) -> Platform:
        """Detect the operating system platform."""
        system = platform.system().lower()
        
        if system == "linux":
            if cls._detect_termux():
                return Platform.TERMUX
            return Platform.LINUX
        elif system == "darwin":
            return Platform.MACOS
        elif system == "windows":
            return Platform.WINDOWS
        else:
            return Platform.UNKNOWN

    @classmethod
    def _detect_termux(cls) -> bool:
        """Check if running in Termux environment."""
        prefix = os.environ.get("PREFIX", "")
        if prefix and "com.termux" in prefix:
            return True
        
        home = str(Path.home())
        if "/data/data/com.termux" in home:
            return True
        
        return False
    
    @classmethod
    def _detect_docker(cls) -> bool:
        """Check if running inside a Docker container."""
        if Path("/.dockerenv").exists():
            return True
        
        if os.environ.get("DOCKER_CONTAINER") == "true":
            return True
        
        try:
            with Path("/proc/1/cgroup").open() as f:
                content = f.read()
                if "docker" in content or "lxc" in content:
                    return True
        except (FileNotFoundError, PermissionError, OSError):
            pass
        
        return False

    @classmethod
    def _get_python_version(cls) -> str:
        """Get the Python version string."""
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    @classmethod
    def _get_python_executable(cls) -> str:
        """Get the path to the Python executable."""
        return sys.executable
    
    @classmethod
    def _get_node_info(cls) -> tuple[Optional[str], Optional[str]]:
        """Get Node.js version and executable path."""
        node_executable = cls._find_executable("node")
        
        if node_executable:
            try:
                import subprocess
                result = subprocess.run(
                    [node_executable, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    version = result.stdout.strip().lstrip("v")
                    return version, node_executable
            except Exception:
                pass
        
        return None, node_executable
    
    @classmethod
    def _find_executable(cls, name: str) -> Optional[str]:
        """Find an executable in PATH."""
        import shutil
        return shutil.which(name)
    
    @classmethod
    def _get_temp_dir(cls) -> str:
        """Get the system temporary directory."""
        import tempfile
        return tempfile.gettempdir()

    @staticmethod
    def normalize_path(path: str) -> str:
        """
        Normalize a path for the current platform.
        
        Args:
            path: The path to normalize
            
        Returns:
            Normalized path string
        """
        path_obj = Path(path)
        return str(path_obj.resolve())
    
    @staticmethod
    def join_path(*parts: str) -> str:
        """
        Join path parts using platform-appropriate separator.
        
        Args:
            *parts: Path parts to join
            
        Returns:
            Joined path string
        """
        return str(Path(*parts))


def detect_environment() -> EnvironmentInfo:
    """
    Detect the current execution environment.
    
    Returns:
        EnvironmentInfo: Complete environment information
    """
    return EnvironmentDetector.detect()


def is_supported_platform() -> bool:
    """
    Check if the current platform is supported.
    
    Returns:
        bool: True if platform is supported, False otherwise
    """
    return detect_environment().is_supported()


def get_platform() -> Platform:
    """
    Get the current platform type.
    
    Returns:
        Platform: The detected platform
    """
    return detect_environment().platform
