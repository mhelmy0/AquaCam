# Stream Quality Optimization Guide

This guide helps you optimize video streaming quality based on your network conditions and requirements.

---

## Quick Start

### Test Your Current Setup
```bash
# Check stream health
curl http://localhost:8081/health

# Monitor for dropped frames and errors
tail -f /var/log/streamer/video_streamer.log | grep -E "warning|error|dropped|corrupt"

# Test network speed to client
iperf3 -c 192.168.100.41 -t 10
```

---

## Configuration Presets

Choose a configuration based on your network and quality requirements:

### 1. Best Quality (Ethernet Required)
**Use when**: Connected via Ethernet, need highest quality
```yaml
camera:
  resolution: "1920x1080"
  fps: 30
  bitrate_kbps: 8000
  gop: 30
```
- **Bandwidth**: ~8 Mbps
- **Latency**: ~1-2 seconds
- **Quality**: Excellent
- **Network**: Stable Ethernet required

### 2. Balanced (WiFi 5GHz)
**Use when**: WiFi 5GHz connection, good balance of quality and stability
```yaml
camera:
  resolution: "1280x720"
  fps: 30
  bitrate_kbps: 4000
  gop: 15
```
- **Bandwidth**: ~4 Mbps
- **Latency**: ~0.5-1 second
- **Quality**: Very Good
- **Network**: WiFi 5GHz or better

### 3. Low Latency (Any Network)
**Use when**: Latency is critical (remote control, monitoring)
```yaml
camera:
  resolution: "1280x720"
  fps: 30
  bitrate_kbps: 3000
  gop: 10
```
- **Bandwidth**: ~3 Mbps
- **Latency**: ~300-500ms
- **Quality**: Good
- **Network**: Any stable connection

### 4. Unstable Network (WiFi 2.4GHz, Weak Signal)
**Use when**: Frequent packet loss, unreliable connection
```yaml
camera:
  resolution: "1280x720"
  fps: 25
  bitrate_kbps: 2000
  gop: 10
```
- **Bandwidth**: ~2 Mbps
- **Latency**: ~0.5-1 second
- **Quality**: Acceptable
- **Network**: WiFi 2.4GHz, weak signal OK

### 5. Smooth Motion (Sports, Action)
**Use when**: Recording fast-moving subjects
```yaml
camera:
  resolution: "1280x720"
  fps: 60
  bitrate_kbps: 6000
  gop: 30
```
- **Bandwidth**: ~6 Mbps
- **Latency**: ~1-2 seconds
- **Quality**: Excellent for motion
- **Network**: WiFi 5GHz or Ethernet

---

## Apply Configuration

### Method 1: Edit config.yaml (Recommended)
```bash
# Edit the configuration file
nano /home/rema/server/server_pi/config.yaml

# Update the camera section with your chosen preset
# Save and exit (Ctrl+X, Y, Enter)

# Restart the service to apply changes
sudo systemctl restart video-streamer.service

# Verify it's working
sudo systemctl status video-streamer.service
```

### Method 2: Use Optimized Config
```bash
# Copy the optimized template
cp /home/rema/server/server_pi/config.optimized.yaml /home/rema/server/server_pi/config.yaml

# Edit to customize
nano /home/rema/server/server_pi/config.yaml

# Restart service
sudo systemctl restart video-streamer.service
```

### Method 3: Temporary Override (Testing)
```bash
# Test without changing config file
# Stop the service first
sudo systemctl stop video-streamer.service

# Run manually with different settings (edit config.yaml first, then run):
python3 -m modules.main --config config.yaml --pc-ip 192.168.100.41
```

---

## Understanding Parameters

### Resolution
**What it does**: Sets the video dimensions (width x height)

| Resolution | Pixels | Best For | Bandwidth Requirement |
|------------|--------|----------|----------------------|
| 1920x1080 (1080p) | 2.1M | High detail, static scenes | High (6-10 Mbps) |
| 1280x720 (720p) | 0.9M | General purpose, motion | Medium (3-6 Mbps) |
| 640x480 (480p) | 0.3M | Very weak networks | Low (1-2 Mbps) |

**Recommendation**: Start with 720p, increase to 1080p only if on Ethernet

### Frame Rate (FPS)
**What it does**: Number of frames captured per second

| FPS | Best For | Latency Impact |
|-----|----------|----------------|
| 60 | Smooth motion, sports | Higher latency |
| 30 | General purpose (recommended) | Balanced |
| 25 | Low bandwidth situations | Lower latency |
| 15 | Very slow scenes | Lowest latency |

**Recommendation**: 30 FPS for most use cases

### Bitrate
**What it does**: Amount of data used per second (higher = better quality)

**Formula**: `resolution * fps * compression_factor`

| Bitrate | Quality | Network Required |
|---------|---------|------------------|
| 10000 kbps (10 Mbps) | Excellent | Gigabit Ethernet |
| 8000 kbps (8 Mbps) | Very Good | 100Mbps Ethernet |
| 6000 kbps (6 Mbps) | Good | WiFi 5GHz or Ethernet |
| 4000 kbps (4 Mbps) | Acceptable | WiFi 5GHz |
| 2000 kbps (2 Mbps) | Fair | WiFi 2.4GHz |

**Recommendation**:
- Ethernet: 6000-8000 kbps
- WiFi 5GHz: 4000-6000 kbps
- WiFi 2.4GHz: 2000-3000 kbps

### GOP (Group of Pictures)
**What it does**: Keyframe interval - how often a full frame is sent

**Lower GOP (10-15)**:
- ✅ Faster recovery from packet loss
- ✅ Lower latency
- ✅ Better for unstable networks
- ❌ Higher bandwidth usage
- ❌ Less compression efficiency

**Higher GOP (30-60)**:
- ✅ Better compression
- ✅ Lower bandwidth usage
- ❌ Slower recovery from errors
- ❌ Higher latency

**Formula**: `GOP = FPS * desired_keyframe_interval_seconds`

**Recommendation**:
- Unstable network: GOP = 10-15 (0.3-0.5 seconds at 30fps)
- Stable network: GOP = 30 (1 second at 30fps)
- Very stable: GOP = 60 (2 seconds at 30fps)

---

## Advanced Optimizations

### Camera Encoder Settings (CSI Camera)

The following settings are now automatically applied:

#### Profile: Main (Updated from Baseline)
- Better compression than baseline
- Wider device compatibility
- Slightly higher CPU usage on decoder

#### Level: 4.1 (Updated from 4.0)
- Supports 1080p30 and 720p60
- Better for higher resolutions

#### Flush: Enabled
- Reduces buffering
- Lower latency
- May increase CPU usage slightly

#### Denoise: Disabled (cdn_off)
- Reduces processing latency
- Raw image quality (good in good lighting)
- Enable if image is noisy: change to `--denoise cdn_hq`

### FFmpeg RTP Settings

The following optimizations are now applied:

#### Buffer Size: 2MB
```yaml
-buffer_size 2M
```
- Smooths out network jitter
- Prevents packet loss during brief congestion

#### Max Delay: 500ms
```yaml
-max_delay 500000
```
- Maximum buffering delay
- Lower = less latency, higher = more tolerance to jitter

#### Flush Packets: Enabled
```yaml
-flush_packets 1
```
- Immediately send packets
- Reduces latency

#### RTP Flags: latm+send_bye
```yaml
-rtpflags latm+send_bye
```
- `latm`: Lower latency audio/video muxing
- `send_bye`: Clean shutdown signal to client

---

## Client-Side Optimization

### FFplay (Recommended for Testing)
```bash
# Basic playback
ffplay -protocol_whitelist file,rtp,udp /tmp/stream.sdp

# With jitter buffer (reduces stuttering)
ffplay -protocol_whitelist file,rtp,udp -max_delay 5000000 -reorder_queue_size 500 /tmp/stream.sdp

# Low latency mode
ffplay -protocol_whitelist file,rtp,udp -fflags nobuffer -flags low_delay -framedrop /tmp/stream.sdp
```

### VLC
```bash
# With caching (smoother playback)
vlc --network-caching=1000 --file-caching=1000 rtp://192.168.100.41:5000

# Low latency mode
vlc --network-caching=0 --clock-jitter=0 --clock-synchro=0 rtp://192.168.100.41:5000
```

### GStreamer
```bash
# Basic playback
gst-launch-1.0 udpsrc port=5000 ! application/x-rtp ! rtph264depay ! h264parse ! avdec_h264 ! autovideosink

# With jitter buffer
gst-launch-1.0 udpsrc port=5000 ! application/x-rtp,encoding-name=H264 ! rtpjitterbuffer latency=100 ! rtph264depay ! h264parse ! avdec_h264 ! autovideosink
```

---

## Troubleshooting Quality Issues

### Problem: Choppy/Stuttering Video

**Cause**: Network packet loss or insufficient bandwidth

**Solutions**:
1. Lower bitrate (e.g., 6000 → 4000 kbps)
2. Lower resolution (1080p → 720p)
3. Reduce GOP (30 → 15)
4. Check network with `iperf3`
5. Use wired Ethernet instead of WiFi
6. Increase client-side buffer

**Verify**:
```bash
# Check for dropped frames
tail -f /var/log/streamer/video_streamer.log | grep dropped

# Monitor network quality
ping -i 0.1 192.168.100.41
```

### Problem: High Latency (Delay)

**Cause**: Buffering, high GOP, network delay

**Solutions**:
1. Reduce GOP (30 → 10)
2. Lower FPS (30 → 25)
3. Disable client-side buffering
4. Use `--flush` flag (already enabled)
5. Reduce max_delay (500ms → 200ms)

**Test latency**:
```bash
# Measure round-trip time
ping 192.168.100.41

# Should be < 10ms for LAN
```

### Problem: Blocky/Pixelated Video

**Cause**: Bitrate too low for resolution

**Solutions**:
1. Increase bitrate (4000 → 6000 kbps)
2. Lower resolution (1080p → 720p)
3. Increase GOP (15 → 30) for more compression efficiency

**Note**: More bitrate = better quality, but requires better network

### Problem: Frequent Freezes/Disconnections

**Cause**: Network instability, interference

**Solutions**:
1. Use Ethernet instead of WiFi
2. Change WiFi channel (less interference)
3. Lower bitrate significantly (e.g., 2000 kbps)
4. Increase GOP for better error recovery
5. Check for other devices using bandwidth

**Check network stability**:
```bash
# Monitor packet loss
mtr 192.168.100.41

# Check WiFi signal (if applicable)
iwconfig wlan0
```

### Problem: Color Banding or Artifacts

**Cause**: Compression artifacts, low bitrate

**Solutions**:
1. Increase bitrate (current + 2000 kbps)
2. Enable denoise: `--denoise cdn_hq`
3. Ensure good lighting (camera performs better)

---

## Network Testing

### Test Bandwidth
```bash
# Install iperf3
sudo apt install iperf3

# On client PC (192.168.100.41), run:
iperf3 -s

# On Raspberry Pi, test upload speed:
iperf3 -c 192.168.100.41 -t 30

# Results should show available bandwidth
# Minimum recommended: 2x your bitrate setting
```

### Test Packet Loss
```bash
# Continuous ping test
ping -c 100 192.168.100.41

# Look for:
# - RTT (round-trip time): Should be < 10ms on LAN
# - Packet loss: Should be 0%
# - Jitter: Variation in RTT, should be < 5ms
```

### Test Network Consistency
```bash
# Install mtr
sudo apt install mtr

# Monitor network path
mtr -r -c 100 192.168.100.41

# Check for packet loss percentage (should be 0%)
```

---

## Monitoring in Real-Time

### Watch for Errors
```bash
# Monitor all warnings and errors
tail -f /var/log/streamer/video_streamer.log | grep -E '"lvl":"(warning|error)"'

# Monitor only dropped frames
tail -f /var/log/streamer/video_streamer.log | grep dropped

# Monitor buffer issues
tail -f /var/log/streamer/video_streamer.log | grep buffer
```

### Check System Health
```bash
# CPU temperature (should be < 80°C)
vcgencmd measure_temp

# Check for throttling (should return throttled=0x0)
vcgencmd get_throttled

# Monitor CPU usage
htop
```

---

## Performance Benchmarks

### Expected CPU Usage (Raspberry Pi 4)

| Configuration | CPU Usage | Temperature |
|--------------|-----------|-------------|
| 1080p30 @ 8Mbps | 25-35% | 55-65°C |
| 720p30 @ 4Mbps | 15-25% | 50-60°C |
| 720p60 @ 6Mbps | 30-40% | 60-70°C |

### Expected Latency

| Network | Configuration | Expected Latency |
|---------|--------------|------------------|
| Gigabit Ethernet | 1080p30, GOP 30 | 500-800ms |
| WiFi 5GHz | 720p30, GOP 15 | 400-600ms |
| WiFi 2.4GHz | 720p25, GOP 10 | 600-900ms |

---

## Quick Reference Commands

```bash
# Apply new configuration
sudo systemctl restart video-streamer.service

# Check stream health
curl http://localhost:8081/health

# Monitor logs
journalctl -u video-streamer.service -f

# Test network
iperf3 -c 192.168.100.41 -t 10

# View stream (client PC)
ffplay -protocol_whitelist file,rtp,udp /tmp/stream.sdp

# Check system stats
vcgencmd measure_temp
vcgencmd get_throttled
```

---

**Last Updated**: 2025-10-20
**Optimized for**: RTP Streaming over LAN
