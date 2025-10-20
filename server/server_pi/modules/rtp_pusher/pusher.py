"""
RTP pusher manages the video streaming pipeline to RTP destinations.

This module launches the camera capture and RTP streaming processes,
monitors their health, and handles failures.
"""

import subprocess
import time
import os
import threading
import queue
from typing import Optional, Dict, Any


class RtpPusher:
    """
    Manages the RTP streaming pipeline.

    Launches capture and pusher processes, monitors their status,
    and logs events for troubleshooting.
    """

    def __init__(self, pipeline, logger) -> None:
        """
        Initialize the RTP pusher.

        Args:
            pipeline: CameraPipeline instance that builds commands.
            logger: JSON logger instance for structured logging.
        """
        self.pipeline = pipeline
        self.logger = logger
        self.capture_process: Optional[subprocess.Popen] = None
        self.pusher_process: Optional[subprocess.Popen] = None
        self.stderr_queue: queue.Queue = queue.Queue()
        self.stderr_thread: Optional[threading.Thread] = None
        self.monitor_running: bool = False

    def start(self) -> None:
        """
        Start the RTP streaming pipeline.

        Depending on the camera mode, this may launch one or two processes:
        - CSI: rpicam-vid piped to FFmpeg
        - USB: single FFmpeg process

        Raises:
            RuntimeError: If the processes fail to start.
        """
        capture_cmd, pusher_cmd = self.pipeline.get_pipeline_commands()

        try:
            if pusher_cmd is not None:
                # CSI mode: rpicam-vid → FFmpeg
                self.logger.log("info", "rtp_pusher", "capture_start", {
                    "cmd": " ".join(capture_cmd)
                }, "Starting rpicam-vid capture")

                self.capture_process = subprocess.Popen(
                    capture_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE  # Capture stderr for debugging
                )

                self.logger.log("info", "rtp_pusher", "pusher_start", {
                    "cmd": " ".join(pusher_cmd),
                    "destination": f"{self.pipeline.rtp_destination_ip}:{self.pipeline.rtp_destination_port}"
                }, "Starting FFmpeg RTP pusher")

                self.pusher_process = subprocess.Popen(
                    pusher_cmd,
                    stdin=self.capture_process.stdout,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE  # Capture stderr for debugging
                )

                # Allow capture_process to receive SIGPIPE if pusher dies
                if self.capture_process.stdout:
                    self.capture_process.stdout.close()

                self.logger.log("service", "rtp_pusher", "publish_ok", {
                    "mode": "csi",
                    "pid_capture": self.capture_process.pid,
                    "pid_pusher": self.pusher_process.pid,
                    "destination": f"{self.pipeline.rtp_destination_ip}:{self.pipeline.rtp_destination_port}"
                }, "RTP streaming started successfully")

                # Start stderr monitoring thread
                self._start_stderr_monitor()
            else:
                # USB mode: single FFmpeg process
                self.logger.log("info", "rtp_pusher", "stream_start", {
                    "cmd": " ".join(capture_cmd),
                    "destination": f"{self.pipeline.rtp_destination_ip}:{self.pipeline.rtp_destination_port}"
                }, "Starting FFmpeg USB capture and RTP stream")

                self.pusher_process = subprocess.Popen(
                    capture_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                self.logger.log("service", "rtp_pusher", "publish_ok", {
                    "mode": "usb",
                    "pid": self.pusher_process.pid,
                    "destination": f"{self.pipeline.rtp_destination_ip}:{self.pipeline.rtp_destination_port}"
                }, "RTP streaming started successfully")

                # Start stderr monitoring thread
                self._start_stderr_monitor()

        except Exception as e:
            self.logger.log("error", "rtp_pusher", "start_failed", {
                "error": str(e)
            }, f"Failed to start RTP pusher: {e}")
            raise RuntimeError(f"Failed to start RTP pusher: {e}")

    def _stderr_reader(self, process: subprocess.Popen, process_name: str) -> None:
        """
        Read stderr from process in a background thread.

        Args:
            process: The subprocess to monitor.
            process_name: Name for logging (e.g., "ffmpeg", "rpicam-vid").
        """
        if not process.stderr:
            return

        try:
            for line in iter(process.stderr.readline, b''):
                if not self.monitor_running:
                    break

                line_str = line.decode('utf-8', errors='replace').strip()
                if not line_str:
                    continue

                # Check for important warnings/errors
                line_lower = line_str.lower()

                # Dropped frames
                if 'dropped' in line_lower or 'drop' in line_lower:
                    self.logger.log("warning", "rtp_pusher", "frames_dropped", {
                        "process": process_name,
                        "message": line_str[:500]
                    }, f"{process_name}: Frames dropped detected")

                # Corruption
                elif 'corrupt' in line_lower or 'error' in line_lower:
                    self.logger.log("warning", "rtp_pusher", "stream_error", {
                        "process": process_name,
                        "message": line_str[:500]
                    }, f"{process_name}: Stream error detected")

                # Buffer issues
                elif 'buffer' in line_lower and ('overflow' in line_lower or 'full' in line_lower):
                    self.logger.log("warning", "rtp_pusher", "buffer_issue", {
                        "process": process_name,
                        "message": line_str[:500]
                    }, f"{process_name}: Buffer issue detected")

                # Network issues
                elif 'network' in line_lower or 'connection' in line_lower:
                    self.logger.log("warning", "rtp_pusher", "network_issue", {
                        "process": process_name,
                        "message": line_str[:500]
                    }, f"{process_name}: Network issue detected")

        except Exception as e:
            self.logger.log("error", "rtp_pusher", "stderr_monitor_error", {
                "process": process_name,
                "error": str(e)
            }, f"Error monitoring stderr for {process_name}")
        finally:
            if process.stderr:
                process.stderr.close()

    def _start_stderr_monitor(self) -> None:
        """Start background threads to monitor stderr from processes."""
        self.monitor_running = True

        if self.pusher_process and self.pusher_process.stderr:
            thread = threading.Thread(
                target=self._stderr_reader,
                args=(self.pusher_process, "ffmpeg"),
                daemon=True,
                name="ffmpeg-stderr-monitor"
            )
            thread.start()
            self.logger.log("info", "rtp_pusher", "stderr_monitor_started", {
                "process": "ffmpeg"
            }, "Started stderr monitoring for FFmpeg")

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

                # Stop stderr monitoring
                self.monitor_running = False

                self.logger.log("error", "rtp_pusher", "stream_drop", {
                    "returncode": returncode
                }, f"RTP pusher exited with code {returncode}")

                raise RuntimeError(f"RTP pusher exited with code {returncode}")

        except Exception as e:
            self.monitor_running = False
            self.logger.log("error", "rtp_pusher", "monitor_error", {
                "error": str(e)
            }, f"Monitor error: {e}")
            raise

    def stop(self) -> None:
        """
        Stop all running processes gracefully.
        """
        # Stop stderr monitoring
        self.monitor_running = False

        if self.pusher_process:
            self.logger.log("info", "rtp_pusher", "stopping", {
                "pid": self.pusher_process.pid
            }, "Stopping pusher process")
            self.pusher_process.terminate()
            try:
                self.pusher_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.pusher_process.kill()

        if self.capture_process:
            self.logger.log("info", "rtp_pusher", "stopping", {
                "pid": self.capture_process.pid
            }, "Stopping capture process")
            self.capture_process.terminate()
            try:
                self.capture_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.capture_process.kill()

        self.logger.log("service", "rtp_pusher", "stopped", {}, "All processes stopped")
