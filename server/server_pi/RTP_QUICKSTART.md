# RTP Streaming Quick Reference

## Overview
Your Raspberry Pi is now configured for **RTP streaming** as the primary mode.

**Current Configuration:**
- **Mode**: RTP (default)
- **Destination**: 192.168.100.41:5000
- **Resolution**: 1920x1080 @ 30fps
- **Bitrate**: 6 Mbps
- **Service**: `video-streamer.service` (auto-starts on boot)

---

## Service Management

### Check Status
```bash
sudo systemctl status video-streamer.service
```

### Start/Stop/Restart
```bash
# Start streaming
sudo systemctl start video-streamer.service

# Stop streaming
sudo systemctl stop video-streamer.service

# Restart streaming
sudo systemctl restart video-streamer.service
```

### Enable/Disable Auto-Start
```bash
# Disable auto-start on boot
sudo systemctl disable video-streamer.service

# Enable auto-start on boot (already enabled)
sudo systemctl enable video-streamer.service
```

---

## Monitoring

### Check Health
```bash
curl http://localhost:8081/health
```

### View Live Logs
```bash
# System logs (journalctl)
journalctl -u video-streamer.service -f

# Application logs
tail -f /var/log/streamer/video_streamer.log

# Old RTMP logs still available
tail -f /var/log/streamer/rtmp_streamer.log
```

### Check Streaming Processes
```bash
# Check if streaming is running
ps aux | grep -E "rpicam|ffmpeg"

# Check PIDs from service
sudo systemctl status video-streamer.service | grep -E "rpicam|ffmpeg"
```

---

## Manual Streaming (Without Service)

### RTP Mode (Default)
```bash
cd /home/rema/server/server_pi

# Use default config (RTP to 192.168.100.41:5000)
python3 -m modules.main --config config.yaml

# Override PC IP
python3 -m modules.main --config config.yaml --pc-ip 192.168.100.50
```

### RTMP Mode (Fallback)
```bash
# Switch to RTMP mode
python3 -m modules.main --config config.yaml --mode rtmp --pc-ip 192.168.100.41
```

### Standalone RTP Script (Simple)
```bash
# No logging, no health monitoring, no auto-retry
python3 rtp_stream_standalone.py
```

---

## Client Side (Receiving Stream)

### View Stream with FFplay
```bash
# Using SDP file (recommended)
ffplay -protocol_whitelist file,rtp,udp /tmp/stream.sdp

# Direct RTP connection
ffplay -protocol_whitelist file,rtp,udp rtp://192.168.100.41:5000
```

### View Stream with VLC
```bash
vlc rtp://192.168.100.41:5000
```

### View Stream with GStreamer
```bash
gst-launch-1.0 udpsrc port=5000 ! application/x-rtp ! rtph264depay ! h264parse ! avdec_h264 ! autovideosink
```

---

## Configuration

### Edit Config File
```bash
nano /home/rema/server/server_pi/config.yaml
```

**Key Settings:**
```yaml
# Streaming mode: "rtmp" or "rtp"
streaming_mode: rtp

rtp:
  destination_ip: "192.168.100.41"  # Your PC IP
  destination_port: 5000
  generate_sdp: true
  sdp_file: "/tmp/stream.sdp"

camera:
  resolution: "1920x1080"
  fps: 30
  bitrate_kbps: 6000  # 6 Mbps
  gop: 30
```

After editing, restart the service:
```bash
sudo systemctl restart video-streamer.service
```

---

## Switching Between RTP and RTMP

### Change Default Mode in Config
```bash
# Edit config.yaml
nano /home/rema/server/server_pi/config.yaml

# Change this line:
streaming_mode: rtmp  # or rtp

# Restart service
sudo systemctl restart video-streamer.service
```

### Override Mode via Command Line
```bash
# Force RTP mode
python3 -m modules.main --config config.yaml --mode rtp --pc-ip 192.168.100.41

# Force RTMP mode
python3 -m modules.main --config config.yaml --mode rtmp --pc-ip 192.168.100.41
```

### Update Systemd Service Default Mode
```bash
# Edit service file
sudo nano /etc/systemd/system/video-streamer.service

# Modify ExecStart line to add --mode flag:
ExecStart=/usr/bin/python3 -u -m modules.main --config /home/rema/server/server_pi/config.yaml --mode rtp --pc-ip ${PC_IP}

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart video-streamer.service
```

---

## Troubleshooting

### Stream Not Starting
```bash
# Check service status
sudo systemctl status video-streamer.service

# Check logs for errors
journalctl -u video-streamer.service -n 50

# Check application logs
tail -30 /var/log/streamer/video_streamer.log
```

### No Video on Client
```bash
# Check if streaming processes are running
ps aux | grep -E "rpicam|ffmpeg"

# Verify SDP file exists
cat /tmp/stream.sdp

# Check network connectivity
ping 192.168.100.41

# Verify firewall allows UDP port 5000
sudo ufw status
```

### Camera Not Found
```bash
# Test camera directly
rpicam-hello

# Check camera cable connection
vcgencmd get_camera
```

### High CPU or Throttling
```bash
# Check temperature
vcgencmd measure_temp

# Check for throttling
vcgencmd get_throttled

# Monitor CPU usage
htop
```

---

## File Locations

| Item | Path |
|------|------|
| **Config File** | `/home/rema/server/server_pi/config.yaml` |
| **Service File** | `/etc/systemd/system/video-streamer.service` |
| **Application Logs** | `/var/log/streamer/video_streamer.log` |
| **System Logs** | `journalctl -u video-streamer.service` |
| **SDP File** | `/tmp/stream.sdp` |
| **Main Script** | `/home/rema/server/server_pi/modules/main.py` |
| **Standalone Script** | `/home/rema/server/server_pi/rtp_stream_standalone.py` |

---

## Auto-Restart Features

Your system has **TWO layers of protection**:

1. **Application-level watchdog**: Retries with exponential backoff (1s, 2s, 5s, 10s, 20s, 30s)
2. **Systemd auto-restart**: Restarts service if it crashes (10 second delay)

**You should never need to manually restart the stream!**

If you do need to restart manually, there's likely a deeper issue. Check the logs.

---

## Performance Tips

### For WiFi
- Keep bitrate at 4000-6000 kbps
- Reduce GOP to 15 for faster recovery from packet loss

### For Ethernet (Wired)
- Can increase bitrate to 8000-10000 kbps
- GOP can stay at 30

### Lower Latency
- Reduce GOP size (15 or even 10)
- Lower resolution to 720p
- Ensure client has jitter buffer enabled

---

## Quick Commands Cheat Sheet

```bash
# Start streaming
sudo systemctl start video-streamer.service

# Stop streaming
sudo systemctl stop video-streamer.service

# View logs
journalctl -u video-streamer.service -f

# Check health
curl http://localhost:8081/health

# Check if running
ps aux | grep rpicam

# View stream (on PC)
ffplay -protocol_whitelist file,rtp,udp /tmp/stream.sdp
```

---

**Last Updated**: 2025-10-20
**Service**: video-streamer.service
**Default Mode**: RTP
