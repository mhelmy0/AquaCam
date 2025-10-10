"""
HTTP health endpoint for monitoring streamer status.

Exposes a simple HTTP server that returns JSON with system and stream health.
"""

import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any
import os


class HealthStatus:
    """Maintains current health status of the streaming system."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize health status tracker.

        Args:
            config: Configuration dictionary with camera and RTMP settings.
        """
        self.config = config
        self.publish_status = "down"
        self.camera_present = False
        self.start_time = time.time()

    def update_publish_status(self, status: str) -> None:
        """Update RTMP publish status (up/down)."""
        self.publish_status = status

    def update_camera_status(self, present: bool) -> None:
        """Update camera presence status."""
        self.camera_present = present

    def get_cpu_celsius(self) -> float:
        """
        Read CPU temperature from thermal zone.

        Returns:
            CPU temperature in Celsius, or -1 if unavailable.
        """
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = int(f.read().strip())
                return temp / 1000.0
        except:
            return -1.0

    def get_uptime_seconds(self) -> float:
        """Return system uptime in seconds."""
        return time.time() - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        """
        Generate health status dictionary.

        Returns:
            Dictionary with all health metrics.
        """
        overall_status = "ok"
        if not self.camera_present or self.publish_status == "down":
            overall_status = "degraded"
        if not self.camera_present and self.publish_status == "down":
            overall_status = "down"

        return {
            "status": overall_status,
            "camera": {
                "present": self.camera_present,
                "mode": self.config["camera"]["mode"],
                "res": self.config["camera"]["resolution"],
                "fps": self.config["camera"]["fps"]
            },
            "publish": {
                "rtmp": self.publish_status,
                "url": self.config["rtmp"]["url"]
            },
            "encoder": {
                "bitrate_kbps": self.config["camera"]["bitrate_kbps"],
                "gop": self.config["camera"]["gop"]
            },
            "system": {
                "cpu_c": self.get_cpu_celsius(),
                "uptime_s": self.get_uptime_seconds()
            }
        }


class HealthHandler(BaseHTTPRequestHandler):
    """HTTP request handler for health endpoint."""

    health_status: HealthStatus = None  # Set by server

    def do_GET(self) -> None:
        """Handle GET requests to /health endpoint."""
        if self.path == "/health" or self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            health_dict = self.health_status.to_dict()
            response = json.dumps(health_dict, indent=2)
            self.wfile.write(response.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress default HTTP server logs."""
        pass


class HealthServer:
    """HTTP server for health monitoring."""

    def __init__(self, config: Dict[str, Any], logger) -> None:
        """
        Initialize health server.

        Args:
            config: Configuration dictionary.
            logger: JSON logger instance.
        """
        self.config = config
        self.logger = logger
        self.port = config["health"]["http_port"]
        self.health_status = HealthStatus(config)
        self.server: HTTPServer = None
        self.thread: threading.Thread = None

    def start(self) -> None:
        """Start the HTTP server in a background thread."""
        HealthHandler.health_status = self.health_status

        self.server = HTTPServer(("0.0.0.0", self.port), HealthHandler)

        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

        self.logger.log("service", "health", "http_started", {
            "port": self.port
        }, f"Health HTTP server started on port {self.port}")

    def stop(self) -> None:
        """Stop the HTTP server."""
        if self.server:
            self.server.shutdown()
            self.logger.log("info", "health", "http_stopped", {}, "Health HTTP server stopped")

    def update_publish_status(self, status: str) -> None:
        """Update publish status in health data."""
        self.health_status.update_publish_status(status)

    def update_camera_status(self, present: bool) -> None:
        """Update camera status in health data."""
        self.health_status.update_camera_status(present)
