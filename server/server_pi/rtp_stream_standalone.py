#!/usr/bin/env python3
"""
Standalone RTP streaming script for Raspberry Pi.

This is a simple, standalone script that streams video from the Raspberry Pi
camera to a remote destination using RTP protocol.

This script can be used independently of the main streaming infrastructure.
"""

import subprocess
import signal
import sys

# --- Stream Configuration ---
DESTINATION_IP = "192.168.1.100"  # IMPORTANT: Change to your PC's IP address
DESTINATION_PORT = 5000
WIDTH = 1280
HEIGHT = 720
FPS = 30
BITRATE_BPS = 2000000  # 2 Mbps

def main():
    """
    Starts the rpicam-vid and ffmpeg processes, piping the output of
    rpicam-vid into ffmpeg to stream over RTP.
    """
    # Command to capture video from the camera and encode it as H.264
    # -o - : Output to standard output (stdout)
    # --flush: Flush buffers immediately to reduce latency
    # --inline: Insert SPS/PPS headers before each I-frame
    camera_cmd = [
        "rpicam-vid",
        "-t", "0",
        "--width", str(WIDTH),
        "--height", str(HEIGHT),
        "--framerate", str(FPS),
        "--codec", "h264",
        "--bitrate", str(BITRATE_BPS),
        "--profile", "high",
        "--inline",
        "--flush",
        "-o", "-"
    ]

    # Command to take the raw H.264 stream and send it over RTP
    # -f h264: Input format is raw H.264
    # -i - : Input is from standard input (stdin)
    # -c:v copy: Copy the video stream without re-encoding
    # -f rtp: Output format is RTP
    # -sdp_file: Generate SDP file for client configuration
    ffmpeg_cmd = [
        "ffmpeg",
        "-f", "h264",
        "-i", "-",
        "-c:v", "copy",
        "-f", "rtp",
        "-sdp_file", "/tmp/stream.sdp",
        f"rtp://{DESTINATION_IP}:{DESTINATION_PORT}"
    ]

    print("Starting video capture process...")
    camera_process = subprocess.Popen(camera_cmd, stdout=subprocess.PIPE)

    print(f"Starting ffmpeg process to stream to rtp://{DESTINATION_IP}:{DESTINATION_PORT}...")
    ffmpeg_process = subprocess.Popen(ffmpeg_cmd, stdin=camera_process.stdout)

    # Allow camera_process to receive SIGPIPE if ffmpeg dies
    camera_process.stdout.close()

    print("Streaming started. Press Ctrl+C to stop.")
    print(f"SDP file generated at: /tmp/stream.sdp")

    def signal_handler(sig, frame):
        print("\nStopping processes...")
        camera_process.terminate()
        ffmpeg_process.terminate()
        camera_process.wait()
        ffmpeg_process.wait()
        print("Processes stopped.")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.pause()  # Wait for Ctrl+C

if __name__ == "__main__":
    main()
