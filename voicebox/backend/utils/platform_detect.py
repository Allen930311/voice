import os
import platform
from typing import Literal


def is_apple_silicon() -> bool:
    """
    Check if running on Apple Silicon (arm64 macOS).
    
    Returns:
        True if on Apple Silicon, False otherwise
    """
    return platform.system() == "Darwin" and platform.machine() == "arm64"


def is_openvino_available() -> bool:
    """
    Check if OpenVINO and optimum-intel are available in the current environment.
    
    Returns:
        True if OpenVINO is available, False otherwise
    """
    try:
        import openvino  # noqa: F401
        import optimum.intel  # noqa: F401
        return True
    except (ImportError, OSError):
        return False


def get_backend_type() -> Literal["mlx", "pytorch", "openvino"]:
    """
    Detect the best backend for the current platform.

    Returns:
        "mlx" on Apple Silicon (if MLX is available and functional), 
        "openvino" if OpenVINO is available, "pytorch" otherwise.
        Can be overridden by VOICEBOX_BACKEND environment variable.
    """
    # 1. Check for explicit environment override
    env_backend = os.environ.get("VOICEBOX_BACKEND", "").lower()
    if env_backend in ["mlx", "pytorch", "openvino"]:
        return env_backend

    # 2. Prefer MLX on Apple Silicon
    if is_apple_silicon():
        try:
            import mlx.core  # noqa: F401
            return "mlx"
        except (ImportError, OSError, RuntimeError):
            pass

    # 3. Prefer OpenVINO on Intel/AMD platforms if available
    if is_openvino_available():
        return "openvino"

    # 4. Default to PyTorch
    return "pytorch"
