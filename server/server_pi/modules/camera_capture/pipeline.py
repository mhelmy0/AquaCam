"""
Camera capture pipeline builder for CSI and USB cameras.

This module constructs FFmpeg or libcamera-vid pipelines to capture video
from the Raspberry Pi camera and prepare it for RTMP streaming.
"""

from typing import List, Dict, Any
import subprocess


class CameraPipeline:
    """
    Builds and manages camera capture pipelines.

    The pipeline depends on the camera mode (CSI or USB) and outputs
    H.264 encoded video ready to be pushed to an RTMP server.
    """

    def __init__(self, config: Dict[str, Any], logger) -> None:
        """
        Initialize the camera pipeline.

        Args:
            config: Configuration dictionary with camera and encoding settings.
            logger: JSON logger instance for structured logging.
        """
        self.config = config
        self.logger = logger
        self.mode = config["camera"]["mode"]
        self.resolution = config["camera"]["resolution"]
        self.fps = config["camera"]["fps"]
        self.bitrate_kbps = config["camera"]["bitrate_kbps"]
        self.gop = config["camera"]["gop"]
        self.rtmp_url = config["rtmp"]["url"]

    def build_csi_pipeline(self) -> List[str]:
        """
        Build pipeline for CSI camera using rpicam-vid.

        The Raspberry Pi HQ camera supports 1080p30 maximum via hardware encoder.
        We use rpicam-vid to capture and encode, then pipe to FFmpeg for RTMP push.

        Returns:
            List of command strings for the pipeline.
        """
        width, height = self.resolution.split("x")

        # rpicam-vid captures and encodes H.264 using hardware encoder
        libcamera_cmd = [
            "rpicam-vid",
            "--inline",              # Inline headers for each I-frame
            "-t", "0",               # Run indefinitely
            "--width", width,
            "--height", height,
            "--framerate", str(self.fps),
            "--codec", "h264",
            "--profile", "baseline", # Baseline profile for better compatibility
            "--level", "4",          # H.264 level 4.0
            "--bitrate", str(self.bitrate_kbps * 1000),  # Convert to bps
            "--intra", str(self.gop),
            "-o", "-"                # Output to stdout
        ]

        self.logger.log("info", "camera_capture", "pipeline_built", {
            "mode": "csi",
            "resolution": self.resolution,
            "fps": self.fps,
            "bitrate_kbps": self.bitrate_kbps
        }, "CSI pipeline built successfully")

        return libcamera_cmd

    def build_usb_pipeline(self) -> List[str]:
        """
        Build pipeline for USB camera using FFmpeg with V4L2.

        Captures from /dev/video0 and encodes using h264_v4l2m2m hardware encoder.

        Returns:
            List of command strings for FFmpeg.
        """
        width, height = self.resolution.split("x")

        # FFmpeg captures from V4L2 device and encodes with hardware encoder
        ffmpeg_cmd = [
            "ffmpeg",
            "-f", "v4l2",
            "-input_format", "mjpeg",
            "-video_size", self.resolution,
            "-framerate", str(self.fps),
            "-i", "/dev/video0",
            "-c:v", "h264_v4l2m2m",   # Hardware encoder
            "-b:v", f"{self.bitrate_kbps}k",
            "-g", str(self.gop),
            "-keyint_min", str(self.gop),
            "-f", "flv",
            self.rtmp_url
        ]

        self.logger.log("info", "camera_capture", "pipeline_built", {
            "mode": "usb",
            "resolution": self.resolution,
            "fps": self.fps,
            "bitrate_kbps": self.bitrate_kbps
        }, "USB pipeline built successfully")

        return ffmpeg_cmd

    def build_ffmpeg_pusher(self) -> List[str]:
        """
        Build FFmpeg command to push H.264 stream to RTMP.

        This is used in conjunction with libcamera-vid for CSI cameras.
        Reads H.264 from stdin and pushes to RTMP without re-encoding.

        Returns:
            List of command strings for FFmpeg pusher.
        """
        width, height = self.resolution.split("x")

        ffmpeg_cmd = [
            "ffmpeg",
            "-f", "h264",             # Explicitly specify input format
            "-fflags", "nobuffer",    # Minimize buffering
            "-flags", "low_delay",    # Low delay mode
            "-probesize", "8192",     # Larger probe size for proper frame detection
            "-analyzeduration", "1000000",  # 1 second analysis for proper stream detection
            "-i", "-",                # Read from stdin
            "-c:v", "copy",           # Copy video stream without re-encoding
            "-s", self.resolution,    # Explicitly set dimensions for FLV muxer (must be after -i for copy)
            "-f", "flv",              # RTMP uses FLV container
            "-flvflags", "no_duration_filesize",  # Optimize for live streaming
            "-flush_packets", "1",    # Flush packets immediately
            self.rtmp_url
        ]

        self.logger.log("info", "rtmp_pusher", "pusher_built", {
            "url": self.rtmp_url
        }, "FFmpeg RTMP pusher built")

        return ffmpeg_cmd

    def get_pipeline_commands(self) -> tuple:
        """
        Get the complete pipeline command(s) based on camera mode.

        Returns:
            Tuple of (capture_cmd, pusher_cmd) or (combined_cmd, None).
            For CSI: returns (libcamera_cmd, ffmpeg_pusher_cmd)
            For USB: returns (ffmpeg_cmd, None)
        """
        if self.mode == "csi":
            return self.build_csi_pipeline(), self.build_ffmpeg_pusher()
        elif self.mode == "usb":
            return self.build_usb_pipeline(), None
        else:
            raise ValueError(f"Unknown camera mode: {self.mode}")
