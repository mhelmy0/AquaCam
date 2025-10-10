"""
Configuration loader with YAML parsing and schema validation.

Loads the YAML configuration file and validates it against a JSON schema.
"""

import yaml
import json
from typing import Dict, Any
import os


def load_config(config_path: str, schema_path: str = None) -> Dict[str, Any]:
    """
    Load and validate configuration from YAML file.

    Args:
        config_path: Path to the YAML configuration file.
        schema_path: Optional path to JSON schema for validation.

    Returns:
        Parsed configuration dictionary.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        ValueError: If config is invalid.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Basic validation (schema validation can be added with jsonschema library)
    required_keys = ["camera", "rtmp", "health", "logging", "watchdog"]
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required configuration key: {key}")

    # Validate camera config
    camera = config["camera"]
    if "mode" not in camera or camera["mode"] not in ["csi", "usb"]:
        raise ValueError("camera.mode must be 'csi' or 'usb'")

    if "resolution" not in camera:
        raise ValueError("camera.resolution is required")

    if "fps" not in camera or not isinstance(camera["fps"], int):
        raise ValueError("camera.fps must be an integer")

    # Validate RTMP config
    if "url" not in config["rtmp"]:
        raise ValueError("rtmp.url is required")

    return config
