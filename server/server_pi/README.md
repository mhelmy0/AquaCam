# Raspberry Pi RTMP Streamer

This directory contains the server-side code for streaming video from a Raspberry Pi to a Windows PC using RTMP.

## Features

- **CSI or USB camera support** - Works with Raspberry Pi Camera Module or USB webcams
- **Hardware H.264 encoding** - Uses Pi's built-in encoder for 1080p30 video
- **RTMP streaming** - Low-latency push to Nginx-RTMP server on PC
- **Automatic retry** - Reconnects with exponential backoff on failures
- **Health monitoring** - HTTP endpoint for system status
- **Structured logging** - JSON Lines format with rotation

## Prerequisites

### Hardware
- Raspberry Pi 4B (or compatible model)
- Camera Module v2/HQ (for CSI mode) or USB webcam
- Network connection to Windows PC

### Software
- Raspberry Pi OS (Bullseye or Bookworm)
- Python 3.7+
- libcamera-apps (for CSI camera)
- FFmpeg

## Installation

1. **Enable camera** (for CSI mode):
   ```bash
   sudo raspi-config
   # Navigate to Interface Options → Camera → Enable
   ```

2. **Install system dependencies**:
   ```bash
   sudo apt update
   sudo apt install -y libcamera-apps ffmpeg python3-pip python3-venv
   ```

3. **Set up Python environment**:
   ```bash
   cd ~/aqua/server_pi
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Create log directory**:
   ```bash
   sudo mkdir -p /var/log/streamer
   sudo chown $USER /var/log/streamer
   ```

5. **Configure RTMP server IP**:
   Edit `config.yaml` and set `rtmp.url` to point to your Windows PC:
   ```yaml
   rtmp:
     url: "rtmp://192.168.1.100/live/cam"  # Replace with your PC IP
   ```

## Configuration

Edit `config.yaml` to customize settings:

- **camera.mode**: `csi` (Camera Module) or `usb` (USB webcam)
- **camera.resolution**: `1920x1080` (maximum for 1080p30)
- **camera.fps**: `30` (maximum for 1080p)
- **camera.bitrate_kbps**: `6000` (6 Mbps, increase for Ethernet)
- **rtmp.url**: RTMP server endpoint on Windows PC
- **health.http_port**: Port for health endpoint (default 8080)
- **logging**: Log level, file path, and rotation settings
- **watchdog**: Retry backoff schedule

## Usage

### Manual Start

```bash
cd ~/aqua/server_pi
source venv/bin/activate
./bin/rtmp_stream.sh --pc-ip 192.168.1.100 --config config.yaml
```

### Install as systemd Service

1. **Edit service file** to set your PC IP:
   ```bash
   nano systemd/rtmp-streamer.service
   # Update Environment="PC_IP=192.168.1.100"
   ```

2. **Install and enable**:
   ```bash
   sudo cp systemd/rtmp-streamer.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable rtmp-streamer
   sudo systemctl start rtmp-streamer
   ```

3. **Check status**:
   ```bash
   systemctl status rtmp-streamer
   journalctl -u rtmp-streamer -f
   ```

### Health Check

```bash
curl http://<raspberry-pi-ip>:8080/health
```

Returns JSON with camera status, RTMP publish state, encoder settings, and system metrics.

## Project Structure

```
server_pi/
├── modules/
│   ├── camera_capture/    # Camera pipeline builders
│   ├── rtmp_pusher/       # RTMP streaming logic
│   ├── health/            # Health HTTP server
│   ├── logging/           # JSON structured logger
│   ├── watchdog/          # Retry and backoff
│   ├── config/            # Configuration loader
│   └── main.py            # Application entry point
├── bin/
│   └── rtmp_stream.sh     # Launch script
├── systemd/
│   └── rtmp-streamer.service  # systemd unit file
├── config.yaml            # Configuration file
└── requirements.txt       # Python dependencies
```

## Troubleshooting

### Camera not detected
- CSI: Run `libcamera-hello` to verify camera
- USB: Check `/dev/video0` exists with `ls -l /dev/video*`

### Stream not connecting
- Verify RTMP server is running on PC: `curl http://<pc-ip>:8080`
- Check network connectivity: `ping <pc-ip>`
- Review logs: `tail -f /var/log/streamer/rtmp_streamer.log`

### High CPU usage
- Reduce bitrate in `config.yaml`
- Ensure hardware encoder is being used (not software encoding)

## License

MIT
