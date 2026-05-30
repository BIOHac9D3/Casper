# Core package
from . import config, memory, shell
from .environment import EnvironmentDetector, EnvironmentInfo, Platform, detect_environment, get_platform, is_supported_platform

# Import subpackages for easier access
from . import schemas, parsers, registry

__all__ = [
    # Modules
    'config',
    'memory',
    'shell',
    'environment',
    'schemas',
    'parsers',
    'registry',
    # Environment utilities
    'EnvironmentDetector',
    'EnvironmentInfo',
    'Platform',
    'detect_environment',
    'get_platform',
    'is_supported_platform'
]
