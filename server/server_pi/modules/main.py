#!/usr/bin/env python3
"""
Main entry point for Raspberry Pi RTMP streamer.

This script orchestrates the camera capture, RTMP streaming, health monitoring,
and retry logic.
"""

import sys
import signal
import argparse
from typing import Optional

from modules.config.load import load_config
from modules.logging.json_logger import JsonLogger
from modules.camera_capture.pipeline import CameraPipeline
from modules.rtmp_pusher.pusher import RtmpPusher
from modules.health.health_http import HealthServer
from modules.watchdog.retry import RetryWatchdog


class StreamerApp:
    """Main application coordinator."""

    def __init__(self, config_path: str, pc_ip: Optional[str] = None) -> None:
        """
        Initialize the streamer application.

        Args:
            config_path: Path to YAML configuration file.
            pc_ip: Optional PC IP to override config RTMP URL.
        """
        # Load configuration
        self.config = load_config(config_path)

        # Override RTMP URL if PC IP provided
        if pc_ip:
            rtmp_url = f"rtmp://{pc_ip}/live/cam"
            self.config["rtmp"]["url"] = rtmp_url

        # Initialize logger
        self.logger = JsonLogger(self.config)
        self.logger.log("service", "main", "app_start", {
            "config": config_path,
            "rtmp_url": self.config["rtmp"]["url"]
        }, "RTMP streamer application starting")

        # Initialize components
        self.pipeline = CameraPipeline(self.config, self.logger)
        self.pusher = RtmpPusher(self.pipeline, self.logger)
        self.health_server = HealthServer(self.config, self.logger)

        # Initialize watchdog if enabled
        self.watchdog: Optional[RetryWatchdog] = None
        if self.config["watchdog"]["enabled"]:
            self.watchdog = RetryWatchdog(
                self.config["watchdog"]["backoff_seconds"],
                self.logger
            )

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame) -> None:
        """Handle shutdown signals gracefully."""
        self.logger.log("info", "main", "shutdown_signal", {
            "signal": signum
        }, f"Received shutdown signal {signum}")
        self.shutdown()
        sys.exit(0)

    def run_stream_task(self) -> None:
        """
        Run one streaming attempt (start and monitor until failure).

        This is the task passed to the watchdog for retry logic.
        """
        # Update health status
        self.health_server.update_camera_status(True)
        self.health_server.update_publish_status("up")

        # Start the pusher
        self.pusher.start()

        # Monitor (blocks until failure)
        try:
            self.pusher.monitor()
        except Exception as e:
            # Update health status on failure
            self.health_server.update_publish_status("down")
            raise

    def run(self) -> None:
        """
        Run the main application loop.

        Starts the health server and either runs the stream task directly
        or wraps it in a retry watchdog.
        """
        # Start health server
        self.health_server.start()

        if self.watchdog:
            # Run with retry logic
            self.logger.log("info", "main", "watchdog_enabled", {}, "Starting with retry watchdog")
            self.watchdog.run(self.run_stream_task)
        else:
            # Run once without retry
            self.logger.log("info", "main", "watchdog_disabled", {}, "Starting without retry")
            self.run_stream_task()

    def shutdown(self) -> None:
        """Shutdown all components gracefully."""
        self.logger.log("service", "main", "app_shutdown", {}, "Shutting down application")

        # Stop pusher
        self.pusher.stop()

        # Stop health server
        self.health_server.stop()

        # Close logger
        self.logger.close()


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="RTMP video streamer for Raspberry Pi"
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to YAML configuration file"
    )
    parser.add_argument(
        "--pc-ip",
        help="Windows PC IP address (overrides config rtmp.url)"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="1.0.0"
    )

    args = parser.parse_args()

    # Create and run application
    app = StreamerApp(args.config, args.pc_ip)
    app.run()


if __name__ == "__main__":
    main()
