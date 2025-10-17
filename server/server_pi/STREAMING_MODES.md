# Raspberry Pi Video Streaming - RTMP and RTP Modes

This streaming system supports two modes of operation: **RTMP** and **RTP**. Both modes include logging, health monitoring, configuration management, and watchdog functionality.

## Table of Contents
- [Quick Start](#quick-start)
- [Streaming Modes](#streaming-modes)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Standalone RTP Script](#standalone-rtp-script)
- [Architecture](#architecture)

## Quick Start

### RTMP Mode (Default)
```bash
# Using config file (streaming_mode: rtmp)
python3 -m modules.main --config config.yaml

# Override with command line
python3 -m modules.main --config config.yaml --mode rtmp --pc-ip 192.168.1.100
```

### RTP Mode
```bash
# Using config file (streaming_mode: rtp)
python3 -m modules.main --config config.yaml

# Override with command line
python3 -m modules.main --config config.yaml --mode rtp --pc-ip 192.168.1.100
```

## Streaming Modes

### RTMP (Real-Time Messaging Protocol)
**Best for:** Low-latency streaming to media servers (Nginx-RTMP, OBS, etc.)

**Features:**
- Streams to RTMP server (can be local or remote)
- Uses FLV container format
- Requires RTMP server running
- Sub-second latency
- Reliable connection handling

**Use Cases:**
- Streaming to Nginx-RTMP server
- Broadcasting to multiple clients via media server
- Recording and live streaming simultaneously

**Configuration:**
```yaml
streaming_mode: rtmp

rtmp:
  url: "rtmp://127.0.0.1/live/cam"
```

### RTP (Real-time Transport Protocol)
**Best for:** Direct point-to-point streaming, minimal latency

**Features:**
- Direct streaming to client (no server needed)
- UDP-based for minimal latency
- Generates SDP file for client configuration
- Lightweight and efficient

**Use Cases:**
- Direct streaming to VLC, ffplay, or GStreamer
- Minimal latency requirements
- Network testing and development

**Configuration:**
```yaml
streaming_mode: rtp

rtp:
  destination_ip: "192.168.1.100"
  destination_port: 5000
  generate_sdp: true
  sdp_file: "/tmp/stream.sdp"
```

## Configuration

### Full Configuration Example

```yaml
# Raspberry Pi Video Streamer Configuration
# Supports both RTMP and RTP streaming modes

# Streaming mode: "rtmp" or "rtp"
streaming_mode: rtmp

camera:
  # Camera mode: "csi" for CSI camera module, "usb" for USB webcam
  mode: csi

  # Video resolution (maximum 1080p for Pi HQ camera hardware encoder)
  resolution: "1920x1080"

  # Frame rate (maximum 30 fps for 1080p)
  fps: 30

  # Bitrate in kilobits per second (6000 = 6 Mbps for WiFi, increase to 8000-10000 for Ethernet)
  bitrate_kbps: 6000

  # GOP size - keyframe interval in frames (30 = 1 second at 30 fps for lower latency)
  gop: 30

rtmp:
  # RTMP server URL - Pi's localhost since RTMP server runs on Pi
  url: "rtmp://127.0.0.1/live/cam"

rtp:
  # RTP destination IP address (your PC's IP address)
  destination_ip: "192.168.1.100"

  # RTP destination port
  destination_port: 5000

  # Generate SDP file for client configuration (optional)
  generate_sdp: true

  # SDP file path (if generate_sdp is true)
  sdp_file: "/tmp/stream.sdp"

health:
  # HTTP port for health monitoring endpoint
  http_port: 8081

logging:
  # Log level: debug, info, service, error
  level: info

  # Log file path
  file: "/var/log/streamer/rtmp_streamer.log"

  # Maximum log file size in MB before rotation
  rotate_max_mb: 10

  # Number of rotated log files to keep
  rotate_backups: 5

watchdog:
  # Enable automatic retry on failure
  enabled: true

  # Backoff schedule in seconds (with ±10% jitter added automatically)
  # After the list is exhausted, the last value (30) is repeated indefinitely
  backoff_seconds: [1, 2, 5, 10, 20, 30]
```

## Usage Examples

### 1. RTMP Streaming to Local Server
```bash
# Start RTMP stream to local Nginx server
python3 -m modules.main --config config.yaml --mode rtmp

# View stream with VLC
vlc rtmp://192.168.1.X/live/cam
```

### 2. RTMP Streaming to Remote Server
```bash
# Stream to remote PC running RTMP server
python3 -m modules.main --config config.yaml --mode rtmp --pc-ip 192.168.1.100

# View stream with VLC
vlc rtmp://192.168.1.100/live/cam
```

### 3. RTP Streaming to PC
```bash
# Stream directly to PC via RTP
python3 -m modules.main --config config.yaml --mode rtp --pc-ip 192.168.1.100

# On PC, view stream with ffplay using SDP file
ffplay -protocol_whitelist file,rtp,udp /tmp/stream.sdp

# Or with VLC
vlc rtp://192.168.1.100:5000
```

### 4. Switching Modes at Runtime
```bash
# Config file has streaming_mode: rtmp, but override to rtp
python3 -m modules.main --config config.yaml --mode rtp --pc-ip 192.168.1.100
```

### 5. Health Monitoring
```bash
# Check health status (works for both modes)
curl http://localhost:8081/health

# Response example:
# {
#   "status": "healthy",
#   "camera": true,
#   "publish": "up",
#   "uptime": 123.45
# }
```

## Standalone RTP Script

For simple RTP streaming without the full infrastructure (logging, health, watchdog), use the standalone script:

```bash
# Edit configuration in the script
nano rtp_stream_standalone.py

# Set DESTINATION_IP, DESTINATION_PORT, WIDTH, HEIGHT, FPS, BITRATE_BPS

# Run the script
python3 rtp_stream_standalone.py

# View on PC
ffplay -protocol_whitelist file,rtp,udp /tmp/stream.sdp
```

**Standalone script features:**
- Simple, single-file implementation
- No dependencies on the module infrastructure
- Easy to understand and modify
- Generates SDP file for client configuration
- Graceful shutdown with Ctrl+C

## Architecture

### Components

1. **CameraPipeline** ([camera_capture/pipeline.py](modules/camera_capture/pipeline.py))
   - Builds camera capture commands (rpicam-vid or FFmpeg)
   - Supports both RTMP and RTP output formats
   - Handles CSI and USB camera modes

2. **RtmpPusher** ([rtmp_pusher/pusher.py](modules/rtmp_pusher/pusher.py))
   - Manages RTMP streaming pipeline
   - Monitors process health
   - Handles graceful shutdown

3. **RtpPusher** ([rtp_pusher/pusher.py](modules/rtp_pusher/pusher.py))
   - Manages RTP streaming pipeline
   - Monitors process health
   - Handles graceful shutdown

4. **HealthServer** ([health/health_http.py](modules/health/health_http.py))
   - HTTP endpoint for health checks
   - Reports camera and streaming status

5. **RetryWatchdog** ([watchdog/retry.py](modules/watchdog/retry.py))
   - Automatic retry with exponential backoff
   - Configurable backoff schedule

6. **JsonLogger** ([logging/json_logger.py](modules/logging/json_logger.py))
   - Structured JSON logging
   - Log rotation and archiving

### Pipeline Flow

#### RTMP Mode (CSI Camera)
```
rpicam-vid → H.264 → FFmpeg → RTMP Server
```

#### RTMP Mode (USB Camera)
```
FFmpeg (V4L2) → H.264 → RTMP Server
```

#### RTP Mode (CSI Camera)
```
rpicam-vid → H.264 → FFmpeg → RTP (UDP)
```

#### RTP Mode (USB Camera)
```
FFmpeg (V4L2) → H.264 → RTP (UDP)
```

## Troubleshooting

### RTMP Issues
- **Connection refused**: Ensure RTMP server is running
- **Stream drops**: Check network stability, increase bitrate if on Ethernet
- **High latency**: Reduce GOP size, use baseline profile

### RTP Issues
- **No video on client**: Verify firewall allows UDP on destination port
- **Choppy playback**: Check network quality, may need to switch to RTMP
- **SDP file not found**: Ensure generate_sdp is true in config

### General Issues
- **Camera not found**: Check camera connection, try `rpicam-hello`
- **FFmpeg errors**: Check logs at `/var/log/streamer/rtmp_streamer.log`
- **Process crashes**: Watchdog will auto-retry if enabled

## Comparison: RTMP vs RTP

| Feature | RTMP | RTP |
|---------|------|-----|
| Latency | Sub-second | Minimal (200-500ms) |
| Reliability | High (TCP) | Medium (UDP) |
| Server Required | Yes | No |
| Multiple Clients | Yes (via server) | No (point-to-point) |
| Complexity | Medium | Low |
| Best For | Broadcasting | Direct streaming |

## License

This project is provided as-is for educational and development purposes.
