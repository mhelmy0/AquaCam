# RTMP Streaming System - Startup Guide

Complete guide for starting and managing the RTMP streaming system on Raspberry Pi.

---

## Overview

This system consists of two components running on the Raspberry Pi:
1. **RTMP Server (Nginx)** - Receives and serves video streams (runs in Docker)
2. **Pi Streamer** - Captures camera video and pushes to RTMP server (Python service)

---

## Quick Start

### Start Everything

```bash
# 1. Start RTMP server (if not already running)
cd ~/aqua/infra_pc
docker compose up -d

# 2. Start Pi streamer service
sudo systemctl start rtmp-streamer

# 3. Verify both are running
sudo systemctl status rtmp-streamer
curl http://localhost:8081/health
```

---

## Part 1: RTMP Server (Nginx-RTMP)

The RTMP server receives streams from the camera and serves them to clients.

### Manual Start

```bash
# Navigate to infra directory
cd ~/aqua/infra_pc

# Start the RTMP server
docker compose up -d
```
**Explanation:** Starts Nginx-RTMP server in detached mode as a Docker container.

### Check Status

```bash
# View running containers
docker compose ps

# Check server health
curl http://localhost:8080
```
**Expected output:** `Nginx-RTMP server is running`

### View Logs

```bash
# Follow logs in real-time
docker compose logs -f

# View last 50 lines
docker compose logs --tail=50
```

### Stop Server

```bash
cd ~/aqua/infra_pc
docker compose down
```
**Explanation:** Stops and removes the RTMP server container.

### Restart Server

```bash
cd ~/aqua/infra_pc
docker compose restart
```

### Auto-Start on Boot

Docker containers with `restart: unless-stopped` policy will automatically start on boot if Docker service is enabled.

```bash
# Enable Docker to start on boot
sudo systemctl enable docker

# Verify Docker is enabled
sudo systemctl is-enabled docker
```

---

## Part 2: Pi Streamer (Camera to RTMP)

The Pi streamer captures video from the camera and pushes it to the RTMP server.

### Prerequisites

Ensure dependencies are installed:

```bash
# Install system packages
sudo apt update
sudo apt install -y libcamera-apps ffmpeg python3-pip python3-venv

# Create log directory
sudo mkdir -p /var/log/streamer
sudo chown $USER /var/log/streamer

# Set up Python virtual environment (first time only)
cd ~/aqua/server_pi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Option A: Manual Start

Use this for testing or one-time streaming.

### Start Streamer Manually

```bash
# Navigate to server_pi directory
cd ~/aqua/server_pi

# Activate Python virtual environment
source venv/bin/activate

# Start the streamer
./bin/rtmp_stream.sh --pc-ip 127.0.0.1 --config config.yaml
```

**Explanation:**
- Activates Python venv with required dependencies
- Starts camera capture and RTMP streaming
- `--pc-ip 127.0.0.1` points to local RTMP server
- `--config config.yaml` uses configuration file

### Stop Manual Streamer

Press `Ctrl+C` in the terminal running the streamer.

---

## Option B: Systemd Service (Recommended)

Use this for automatic startup on boot and background operation.

### 1. Install Service

The service file is already installed at `/etc/systemd/system/rtmp-streamer.service`.

To reinstall or update:

```bash
# Copy service file
sudo cp ~/aqua/server_pi/systemd/rtmp-streamer.service /etc/systemd/system/

# Reload systemd to recognize changes
sudo systemctl daemon-reload
```

**Explanation:** Installs the service definition so systemd can manage the streamer.

### 2. Enable Service (Auto-Start on Boot)

```bash
# Enable service to start automatically on boot
sudo systemctl enable rtmp-streamer

# Verify it's enabled
sudo systemctl is-enabled rtmp-streamer
```

**Expected output:** `enabled`

### 3. Start Service

```bash
# Start the service now
sudo systemctl start rtmp-streamer
```

**Explanation:** Starts the streamer immediately without waiting for reboot.

### 4. Verify Service is Running

```bash
# Check service status
sudo systemctl status rtmp-streamer
```

**Expected output:**
- `Active: active (running)`
- Process IDs for `rpicam-vid` and `ffmpeg`
- Log showing "RTMP publishing started successfully"

### 5. Service Management Commands

```bash
# Stop the service
sudo systemctl stop rtmp-streamer

# Restart the service
sudo systemctl restart rtmp-streamer

# Reload systemd after editing service file
sudo systemctl daemon-reload && sudo systemctl restart rtmp-streamer

# Disable auto-start on boot
sudo systemctl disable rtmp-streamer

# View real-time logs
journalctl -u rtmp-streamer -f

# View last 50 log entries
journalctl -u rtmp-streamer -n 50

# View logs since boot
journalctl -u rtmp-streamer -b
```

### 6. Complete Service Restart

Use this after making changes to the service file:

```bash
sudo systemctl daemon-reload && sudo systemctl restart rtmp-streamer && sleep 3 && sudo systemctl status rtmp-streamer --no-pager
```

**Explanation:**
- Reloads systemd configuration
- Restarts the service with new settings
- Waits 3 seconds for startup
- Shows status without pager

---

## Configuration

### RTMP Server Configuration

Location: `~/aqua/infra_pc/nginx/nginx.conf`

After editing:
```bash
cd ~/aqua/infra_pc
docker compose restart
```

### Pi Streamer Configuration

Location: `~/aqua/server_pi/config.yaml`

Key settings:
- `camera.mode`: `csi` (Camera Module) or `usb` (USB webcam)
- `camera.resolution`: `1920x1080`
- `camera.fps`: `30`
- `camera.bitrate_kbps`: `6000` (6 Mbps)
- `rtmp.url`: `rtmp://127.0.0.1/live/cam`
- `health.http_port`: `8081`

After editing:
```bash
sudo systemctl restart rtmp-streamer
```

### Systemd Service Configuration

Location: `/etc/systemd/system/rtmp-streamer.service`

Key settings:
- `User=rema` (your username)
- `WorkingDirectory=/home/rema/aqua/server_pi`
- `Environment="PC_IP=127.0.0.1"`

After editing:
```bash
sudo systemctl daemon-reload
sudo systemctl restart rtmp-streamer
```

---

## Verification & Testing

### 1. Check RTMP Server is Running

```bash
# HTTP health check
curl http://localhost:8080

# View RTMP statistics
curl http://localhost:8080/stat

# Check Docker container
docker ps | grep rtmp-server
```

**Expected:** Server responds with "Nginx-RTMP server is running"

### 2. Check Pi Streamer is Running

```bash
# Service status
sudo systemctl status rtmp-streamer

# Health endpoint
curl http://localhost:8081/health

# Check processes
ps aux | grep -E '(rpicam-vid|ffmpeg)' | grep -v grep
```

**Expected:**
- Service shows `active (running)`
- Health endpoint returns JSON with camera status
- Processes for `rpicam-vid` and `ffmpeg` are visible

### 3. Check Network Ports

```bash
# Verify ports are listening
netstat -tuln | grep -E '(1935|8080|8081)'
```

**Expected output:**
```
tcp        0      0 0.0.0.0:1935            0.0.0.0:*               LISTEN
tcp        0      0 0.0.0.0:8080            0.0.0.0:*               LISTEN
```

### 4. View Live Logs

```bash
# RTMP server logs
cd ~/aqua/infra_pc
docker compose logs -f

# Pi streamer logs (systemd)
journalctl -u rtmp-streamer -f

# Pi streamer logs (file)
tail -f /var/log/streamer/rtmp_streamer.log
```

### 5. Test Stream Playback

```bash
# Using ffplay (if installed)
ffplay rtmp://127.0.0.1/live/cam

# Using VLC (if installed)
vlc rtmp://127.0.0.1/live/cam

# Test with ffprobe
ffprobe -v error rtmp://127.0.0.1/live/cam
```

---

## Troubleshooting

### Issue: Service Fails to Start

**Symptom:** `systemctl status rtmp-streamer` shows `failed` or `activating (auto-restart)`

**Solutions:**

1. **Check service logs:**
   ```bash
   journalctl -u rtmp-streamer -n 50
   ```

2. **Verify user and paths in service file:**
   ```bash
   sudo nano /etc/systemd/system/rtmp-streamer.service
   ```

   Ensure:
   - `User=rema` (your actual username)
   - `WorkingDirectory=/home/rema/aqua/server_pi` (correct path)
   - `ExecStart=/home/rema/aqua/server_pi/venv/bin/python3 ...` (correct venv path)

3. **Reload and restart:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart rtmp-streamer
   sudo systemctl status rtmp-streamer
   ```

### Issue: Camera Not Detected

**Symptom:** Logs show "camera not found" or "failed to open camera"

**Solutions:**

1. **For CSI Camera:**
   ```bash
   # Test camera
   rpicam-hello

   # Enable camera in raspi-config
   sudo raspi-config
   # Navigate to: Interface Options → Camera → Enable
   ```

2. **For USB Camera:**
   ```bash
   # Check if camera is detected
   ls -l /dev/video*

   # View camera info
   v4l2-ctl --list-devices
   ```

3. **Update config.yaml:**
   ```bash
   nano ~/aqua/server_pi/config.yaml
   # Set camera.mode to 'csi' or 'usb'
   ```

### Issue: RTMP Server Not Running

**Symptom:** Streamer can't connect to RTMP server

**Solutions:**

1. **Check if container is running:**
   ```bash
   docker ps
   ```

2. **Start RTMP server:**
   ```bash
   cd ~/aqua/infra_pc
   docker compose up -d
   ```

3. **Check logs for errors:**
   ```bash
   docker compose logs
   ```

4. **Verify health:**
   ```bash
   curl http://localhost:8080
   ```

### Issue: Port Already in Use

**Symptom:** Docker fails to start: "port is already allocated"

**Solutions:**

1. **Find what's using the port:**
   ```bash
   sudo netstat -tuln | grep -E '(1935|8080)'
   sudo lsof -i :1935
   sudo lsof -i :8080
   ```

2. **Stop conflicting service or change ports:**
   ```bash
   # Edit docker-compose.yml to use different ports
   nano ~/aqua/infra_pc/docker-compose.yml
   ```

### Issue: No Video Output / Black Screen

**Symptom:** Stream connects but shows no video

**Solutions:**

1. **Check camera is working:**
   ```bash
   rpicam-vid -t 5000 -o test.h264
   ```

2. **Verify bitrate and resolution:**
   ```bash
   nano ~/aqua/server_pi/config.yaml
   # Try lower resolution: 1280x720
   # Try lower bitrate: 3000
   ```

3. **Check FFmpeg process:**
   ```bash
   ps aux | grep ffmpeg
   journalctl -u rtmp-streamer -n 100
   ```

### Issue: High CPU Usage

**Symptom:** System is slow, CPU at 100%

**Solutions:**

1. **Reduce bitrate:**
   ```yaml
   # In config.yaml
   camera:
     bitrate_kbps: 3000  # Reduce from 6000
   ```

2. **Lower resolution:**
   ```yaml
   # In config.yaml
   camera:
     resolution: "1280x720"  # Reduce from 1920x1080
   ```

3. **Lower frame rate:**
   ```yaml
   # In config.yaml
   camera:
     fps: 15  # Reduce from 30
   ```

### Issue: Stream Keeps Disconnecting

**Symptom:** Service restarts frequently, logs show connection failures

**Solutions:**

1. **Check network stability:**
   ```bash
   ping 127.0.0.1
   ```

2. **Verify RTMP server is stable:**
   ```bash
   docker compose ps
   curl http://localhost:8080
   ```

3. **Check system resources:**
   ```bash
   # Memory usage
   free -h

   # Disk space
   df -h

   # CPU load
   top
   ```

4. **Review watchdog settings:**
   ```bash
   nano ~/aqua/server_pi/config.yaml
   # Check watchdog.backoff_seconds
   ```

### Issue: Permission Denied Errors

**Symptom:** Logs show "permission denied" for camera or log files

**Solutions:**

1. **Add user to video group:**
   ```bash
   sudo usermod -a -G video $USER
   # Log out and back in
   ```

2. **Fix log directory permissions:**
   ```bash
   sudo mkdir -p /var/log/streamer
   sudo chown rema:rema /var/log/streamer
   ```

3. **Check camera device permissions:**
   ```bash
   ls -l /dev/video*
   # Should show crw-rw---- with 'video' group
   ```

### Complete Health Check Script

Run this to verify everything is working:

```bash
#!/bin/bash
echo "=== RTMP Streaming System Health Check ==="
echo ""

echo "1. RTMP Server (Docker):"
docker ps | grep rtmp-server && echo "✓ Running" || echo "✗ Not running"
curl -s http://localhost:8080 | grep -q "running" && echo "✓ Responding" || echo "✗ Not responding"
echo ""

echo "2. Pi Streamer Service:"
systemctl is-active rtmp-streamer && echo "✓ Running" || echo "✗ Not running"
curl -s http://localhost:8081/health > /dev/null && echo "✓ Health endpoint OK" || echo "✗ Health endpoint failed"
echo ""

echo "3. Processes:"
pgrep -f "rpicam-vid" > /dev/null && echo "✓ Camera capture running" || echo "✗ Camera capture not running"
pgrep -f "ffmpeg.*rtmp" > /dev/null && echo "✓ FFmpeg streaming running" || echo "✗ FFmpeg not running"
echo ""

echo "4. Network Ports:"
netstat -tuln | grep -q ":1935" && echo "✓ Port 1935 (RTMP) listening" || echo "✗ Port 1935 not listening"
netstat -tuln | grep -q ":8080" && echo "✓ Port 8080 (HTTP) listening" || echo "✗ Port 8080 not listening"
netstat -tuln | grep -q ":8081" && echo "✓ Port 8081 (Health) listening" || echo "✗ Port 8081 not listening"
echo ""

echo "5. Camera Device:"
ls /dev/video* > /dev/null 2>&1 && echo "✓ Camera device found" || echo "✗ No camera device"
echo ""

echo "=== End Health Check ==="
```

Save this as `health_check.sh`, make it executable, and run:
```bash
chmod +x health_check.sh
./health_check.sh
```

---

## System Architecture

```
┌─────────────────────────────────────────────────┐
│              Raspberry Pi                       │
│                                                 │
│  ┌──────────────┐         ┌─────────────────┐  │
│  │   Camera     │────────▶│  Pi Streamer    │  │
│  │ (CSI/USB)    │         │  (Python)       │  │
│  └──────────────┘         │  Port: 8081     │  │
│                           └────────┬────────┘  │
│                                    │            │
│                                    │ RTMP       │
│                                    ▼            │
│                           ┌─────────────────┐  │
│                           │  RTMP Server    │  │
│                           │  (Nginx)        │  │
│                           │  Port: 1935     │  │
│                           │  HTTP: 8080     │  │
│                           └─────────────────┘  │
└─────────────────────────────────────────────────┘
                                    │
                                    │ RTMP/HTTP
                                    ▼
                           ┌─────────────────┐
                           │  Clients        │
                           │  (VLC, FFmpeg)  │
                           └─────────────────┘
```

---

## Quick Reference

### Essential Commands

```bash
# Start everything
cd ~/aqua/infra_pc && docker compose up -d
sudo systemctl start rtmp-streamer

# Check status
docker compose ps
sudo systemctl status rtmp-streamer
curl http://localhost:8081/health

# View logs
docker compose logs -f
journalctl -u rtmp-streamer -f

# Stop everything
sudo systemctl stop rtmp-streamer
cd ~/aqua/infra_pc && docker compose down

# Restart after config change
sudo systemctl restart rtmp-streamer
cd ~/aqua/infra_pc && docker compose restart
```

### File Locations

- **RTMP Server Config:** `~/aqua/infra_pc/nginx/nginx.conf`
- **Streamer Config:** `~/aqua/server_pi/config.yaml`
- **Service File:** `/etc/systemd/system/rtmp-streamer.service`
- **Logs:** `/var/log/streamer/rtmp_streamer.log`
- **Virtual Environment:** `~/aqua/server_pi/venv/`

### Default Ports

- **1935** - RTMP streaming
- **8080** - RTMP server HTTP/stats
- **8081** - Pi streamer health check

---

## Additional Resources

- **Project Structure:** See [server_pi/README.md](server_pi/README.md)
- **RTMP Server Details:** See [infra_pc/README.md](infra_pc/README.md)
- **Stream URL:** `rtmp://127.0.0.1:1935/live/cam`

---

## License

MIT
