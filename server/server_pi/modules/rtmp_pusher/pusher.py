"""
RTMP pusher manages the video streaming pipeline to the RTMP server.

This module launches the camera capture and RTMP publishing processes,
monitors their health, and handles failures.
"""

import subprocess
import time
from typing import Optional, Dict, Any


class RtmpPusher:
    """
    Manages the RTMP streaming pipeline.

    Launches capture and pusher processes, monitors their status,
    and logs events for troubleshooting.
    """

    def __init__(self, pipeline, logger) -> None:
        """
        Initialize the RTMP pusher.

        Args:
            pipeline: CameraPipeline instance that builds commands.
            logger: JSON logger instance for structured logging.
        """
        self.pipeline = pipeline
        self.logger = logger
        self.capture_process: Optional[subprocess.Popen] = None
        self.pusher_process: Optional[subprocess.Popen] = None

    def start(self) -> None:
        """
        Start the streaming pipeline.

        Depending on the camera mode, this may launch one or two processes:
        - CSI: libcamera-vid piped to FFmpeg
        - USB: single FFmpeg process

        Raises:
            RuntimeError: If the processes fail to start.
        """
        capture_cmd, pusher_cmd = self.pipeline.get_pipeline_commands()

        try:
            if pusher_cmd is not None:
                # CSI mode: libcamera-vid → FFmpeg
                self.logger.log("info", "rtmp_pusher", "capture_start", {
                    "cmd": " ".join(capture_cmd)
                }, "Starting libcamera-vid capture")

                self.capture_process = subprocess.Popen(
                    capture_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE  # Capture stderr for debugging
                    # stderr=subprocess.DEVNULL  # Don't buffer stderr
                )

                self.logger.log("info", "rtmp_pusher", "pusher_start", {
                    "cmd": " ".join(pusher_cmd),
                    "url": self.pipeline.rtmp_url
                }, "Starting FFmpeg RTMP pusher")

                self.pusher_process = subprocess.Popen(
                    pusher_cmd,
                    stdin=self.capture_process.stdout,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE  # Capture stderr for debugging
                    # stderr=subprocess.DEVNULL  # Don't buffer stderr
                )

                # Allow capture_process to receive SIGPIPE if pusher dies
                if self.capture_process.stdout:
                    self.capture_process.stdout.close()

                self.logger.log("service", "rtmp_pusher", "publish_ok", {
                    "mode": "csi",
                    "pid_capture": self.capture_process.pid,
                    "pid_pusher": self.pusher_process.pid
                }, "RTMP publishing started successfully")
            else:
                # USB mode: single FFmpeg process
                self.logger.log("info", "rtmp_pusher", "stream_start", {
                    "cmd": " ".join(capture_cmd),
                    "url": self.pipeline.rtmp_url
                }, "Starting FFmpeg USB capture and push")

                self.pusher_process = subprocess.Popen(
                    capture_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                self.logger.log("service", "rtmp_pusher", "publish_ok", {
                    "mode": "usb",
                    "pid": self.pusher_process.pid
                }, "RTMP publishing started successfully")

        except Exception as e:
            self.logger.log("error", "rtmp_pusher", "start_failed", {
                "error": str(e)
            }, f"Failed to start RTMP pusher: {e}")
            raise RuntimeError(f"Failed to start RTMP pusher: {e}")

    def monitor(self) -> None:
        """
        Monitor the running processes and raise exception if they die.

        This method blocks while processes are running and raises an
        exception if any process exits.

        Raises:
            RuntimeError: If any process exits unexpectedly.
        """
        try:
            # Wait for pusher process to exit (it shouldn't in normal operation)
            if self.pusher_process:
                returncode = self.pusher_process.wait()

                # Capture stderr to log the error
                stderr_output = ""
                if self.pusher_process.stderr:
                    try:
                        stderr_output = self.pusher_process.stderr.read().decode('utf-8', errors='replace')
                    except:
                        pass

                self.logger.log("error", "rtmp_pusher", "publish_drop", {
                    "returncode": returncode,
                    "stderr": stderr_output[:2000] if stderr_output else "No stderr available"
                }, f"RTMP pusher exited with code {returncode}")

                raise RuntimeError(f"RTMP pusher exited with code {returncode}")

        except Exception as e:
            self.logger.log("error", "rtmp_pusher", "monitor_error", {
                "error": str(e)
            }, f"Monitor error: {e}")
            raise

    def stop(self) -> None:
        """
        Stop all running processes gracefully.
        """
        if self.pusher_process:
            self.logger.log("info", "rtmp_pusher", "stopping", {
                "pid": self.pusher_process.pid
            }, "Stopping pusher process")
            self.pusher_process.terminate()
            try:
                self.pusher_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.pusher_process.kill()

        if self.capture_process:
            self.logger.log("info", "rtmp_pusher", "stopping", {
                "pid": self.capture_process.pid
            }, "Stopping capture process")
            self.capture_process.terminate()
            try:
                self.capture_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.capture_process.kill()

        self.logger.log("service", "rtmp_pusher", "stopped", {}, "All processes stopped")
