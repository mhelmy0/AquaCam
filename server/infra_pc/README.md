# PC Infrastructure - Nginx-RTMP Server

This directory contains the Docker setup for the Nginx-RTMP server that receives video streams from the Raspberry Pi.

## Overview

The Nginx-RTMP server acts as a media relay:
1. Raspberry Pi pushes H.264 stream via RTMP to this server
2. Windows client pulls the stream from this server for recording
3. Multiple clients can connect simultaneously for preview/monitoring

## Components

- **Nginx with RTMP module**: Media server for ingesting and serving RTMP streams
- **Docker Compose**: Container orchestration for easy deployment
- **Health endpoint**: HTTP server on port 8080 for monitoring

## Prerequisites

- Docker Desktop for Windows
- At least 1 GB free disk space
- Ports 1935 (RTMP) and 8080 (HTTP) available

## Setup

1. **Start the RTMP server**:
   ```cmd
   cd infra_pc
   docker compose up -d
   ```

2. **Verify it's running**:
   ```cmd
   docker compose ps
   curl http://127.0.0.1:8080
   ```

   Should return: `Nginx-RTMP server is running`

3. **Check logs**:
   ```cmd
   docker compose logs -f
   ```

## Configuration

### Nginx Configuration

The [nginx/nginx.conf](nginx/nginx.conf) file configures:

- **RTMP server**: Listens on port 1935
- **Live application**: Accepts streams at `/live/<stream_key>`
- **HTTP server**: Health checks and statistics on port 8080

### Stream URL

Raspberry Pi pushes to:
```
rtmp://<PC_IP>:1935/live/cam
```

Windows client pulls from:
```
rtmp://127.0.0.1:1935/live/cam
```

### Customization

Edit `nginx/nginx.conf` to:
- Add authentication for publishing
- Enable HLS output for browser playback
- Configure recording on the server
- Set up multiple stream applications

Example with authentication:
```nginx
application live {
    live on;

    # Require password for publishing
    on_publish http://auth-server/check_auth;

    allow publish all;
    allow play all;
}
```

## Management

### Start Server
```cmd
docker compose up -d
```

### Stop Server
```cmd
docker compose down
```

### Restart Server
```cmd
docker compose restart
```

### View Logs
```cmd
docker compose logs -f nginx-rtmp
```

### Update Configuration
After editing `nginx.conf`:
```cmd
docker compose restart
```

## Monitoring

### Health Check
```cmd
curl http://127.0.0.1:8080/
```

### Stream Statistics
View RTMP statistics at:
```
http://127.0.0.1:8080/stat
```

Shows:
- Active streams
- Bitrate
- Connected clients
- Uptime

### Docker Status
```cmd
docker compose ps
docker stats rtmp-server
```

## Troubleshooting

### Port already in use
If port 1935 or 8080 is already in use:

1. Check what's using the port:
   ```cmd
   netstat -ano | findstr :1935
   netstat -ano | findstr :8080
   ```

2. Edit `docker-compose.yml` to use different ports:
   ```yaml
   ports:
     - "11935:1935"  # Use 11935 externally
     - "18080:8080"  # Use 18080 externally
   ```

### Container won't start
```cmd
docker compose logs nginx-rtmp
```

Common issues:
- Invalid nginx.conf syntax
- Missing volumes
- Docker Desktop not running

### Stream not connecting

**From Raspberry Pi**:
- Verify PC IP address is correct
- Check firewall allows port 1935
- Test with VLC: `vlc rtmp://<PC_IP>:1935/live/cam`

**From Windows client**:
- Verify container is running: `docker compose ps`
- Check logs for errors: `docker compose logs`
- Test with FFmpeg: `ffmpeg -i rtmp://127.0.0.1:1935/live/cam -f null -`

### High CPU usage
- Reduce number of connected clients
- Disable server-side recording if enabled
- Check for excessive logging

## Network Configuration

### Firewall Rules

Allow incoming connections on port 1935:
```powershell
# Run as Administrator
New-NetFirewallRule -DisplayName "RTMP Server" -Direction Inbound -Port 1935 -Protocol TCP -Action Allow
```

### Find Your PC IP

```cmd
ipconfig
```

Look for "IPv4 Address" on your active network adapter (Ethernet or Wi-Fi).

## Advanced Configuration

### Enable HLS Output

Edit `nginx.conf` to add HLS support for browser playback:

```nginx
application live {
    live on;

    # HLS configuration
    hls on;
    hls_path /tmp/hls;
    hls_fragment 3;
    hls_playlist_length 60;
}
```

Then serve HLS files via HTTP:
```nginx
http {
    server {
        listen 8080;

        location /hls {
            types {
                application/vnd.apple.mpegurl m3u8;
                video/mp2t ts;
            }
            root /tmp;
            add_header Cache-Control no-cache;
            add_header Access-Control-Allow-Origin *;
        }
    }
}
```

Access in browser: `http://<PC_IP>:8080/hls/cam.m3u8`

### Multiple Stream Keys

```nginx
application live {
    live on;

    # Accept any stream key
    allow publish all;
}
```

Pi can push to different keys:
- `rtmp://<PC_IP>:1935/live/camera1`
- `rtmp://<PC_IP>:1935/live/camera2`

## Performance Tuning

For high-bitrate streams (>10 Mbps):

```nginx
rtmp {
    server {
        chunk_size 8192;  # Increase from 4096

        application live {
            live on;

            # Increase buffer sizes
            buffer 10m;
            max_message 10M;
        }
    }
}
```

## Security Considerations

### Production Deployment

For production use:
1. Add authentication for publishing
2. Restrict publish IPs to Raspberry Pi only
3. Use RTMPS (RTMP over TLS) for encryption
4. Enable access logs for auditing

Example restricted access:
```nginx
application live {
    live on;

    # Only allow Pi to publish
    allow publish 192.168.1.0/24;
    deny publish all;

    # Anyone can play
    allow play all;
}
```

## License

MIT
