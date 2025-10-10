"""
JSON structured logger with rotation support.

Writes one JSON object per line (JSONL format) with rotation based on file size.
Each log entry includes timestamp, level, component, event, context and message.
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import os
import glob


class JsonLogger:
    """
    Structured JSON logger with size-based rotation.

    Log entries follow the format:
    {
      "ts": "2025-10-03T12:34:56.789Z",
      "lvl": "info",
      "comp": "camera_capture",
      "evt": "pipeline_built",
      "ctx": {"mode": "csi", "fps": 30},
      "msg": "CSI pipeline built successfully"
    }
    """

    LEVELS = ["debug", "info", "service", "error"]

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the JSON logger.

        Args:
            config: Configuration dictionary with logging settings.
        """
        self.log_file = config["logging"]["file"]
        self.level = config["logging"]["level"]
        self.max_bytes = config["logging"]["rotate_max_mb"] * 1024 * 1024
        self.backup_count = config["logging"]["rotate_backups"]

        # Ensure log directory exists
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        self.file_handle: Optional[Any] = None
        self._open_log_file()

    def _open_log_file(self) -> None:
        """Open the log file for appending."""
        self.file_handle = open(self.log_file, "a", encoding="utf-8")

    def _should_rotate(self) -> bool:
        """Check if log file exceeds size limit."""
        if not os.path.exists(self.log_file):
            return False
        return os.path.getsize(self.log_file) >= self.max_bytes

    def _rotate(self) -> None:
        """
        Rotate log files.

        Renames current log to .1, shifts existing backups, and removes oldest.
        """
        if self.file_handle:
            self.file_handle.close()

        # Remove oldest backup if it exists
        oldest = f"{self.log_file}.{self.backup_count}"
        if os.path.exists(oldest):
            os.remove(oldest)

        # Shift existing backups
        for i in range(self.backup_count - 1, 0, -1):
            src = f"{self.log_file}.{i}"
            dst = f"{self.log_file}.{i + 1}"
            if os.path.exists(src):
                os.rename(src, dst)

        # Rename current log to .1
        if os.path.exists(self.log_file):
            os.rename(self.log_file, f"{self.log_file}.1")

        # Open new log file
        self._open_log_file()

    def log(self, level: str, component: str, event: str, context: Dict[str, Any], message: str) -> None:
        """
        Write a structured log entry.

        Args:
            level: Log level (debug, info, service, error).
            component: Component name (e.g., camera_capture, rtmp_pusher).
            event: Event name (e.g., pipeline_built, publish_ok).
            context: Dictionary with additional context data.
            message: Human-readable message.
        """
        # Check log level
        if self.LEVELS.index(level) < self.LEVELS.index(self.level):
            return

        # Check rotation before writing
        if self._should_rotate():
            self._rotate()

        # Build log entry
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "lvl": level,
            "comp": component,
            "evt": event,
            "ctx": context,
            "msg": message
        }

        # Write JSON line
        self.file_handle.write(json.dumps(entry) + "\n")
        self.file_handle.flush()

        # Also print to stdout for systemd journal
        print(json.dumps(entry))

    def close(self) -> None:
        """Close the log file."""
        if self.file_handle:
            self.file_handle.close()
