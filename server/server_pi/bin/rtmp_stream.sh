#!/bin/bash
# RTMP Streamer launcher script for Raspberry Pi
#
# This script starts the Python RTMP streamer with the specified configuration.
# It can be run manually or via systemd service.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_DIR="$(dirname "$SCRIPT_DIR")"

# Default values
CONFIG_FILE="${SERVER_DIR}/config.yaml"
PC_IP=""

# Parse command line arguments
show_help() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Start the RTMP video streamer on Raspberry Pi.

OPTIONS:
    --pc-ip IP          IP address of the Windows PC running RTMP server (required)
    --config PATH       Path to config.yaml (default: ${CONFIG_FILE})
    -h, --help          Show this help message

EXAMPLES:
    $(basename "$0") --pc-ip 192.168.1.100
    $(basename "$0") --pc-ip 192.168.1.100 --config /etc/streamer/config.yaml

NOTES:
    - Camera must be enabled via raspi-config
    - For CSI camera: libcamera-apps must be installed
    - For USB camera: /dev/video0 must be accessible
    - RTMP server must be running on PC at rtmp://<PC_IP>/live/cam

EOF
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --pc-ip)
            PC_IP="$2"
            shift 2
            ;;
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Error: Unknown option $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate required arguments
if [[ -z "$PC_IP" ]]; then
    echo "Error: --pc-ip is required"
    show_help
    exit 1
fi

if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Error: Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Update RTMP URL in config with provided PC IP
# Note: This is a simple approach. In production, consider using environment variables
# or generating a temporary config file.
export RTMP_PC_IP="$PC_IP"

echo "Starting RTMP streamer..."
echo "  PC IP: $PC_IP"
echo "  Config: $CONFIG_FILE"

# Add server_pi to Python path
export PYTHONPATH="${SERVER_DIR}:${PYTHONPATH:-}"

# Run the Python streamer
cd "$SERVER_DIR"
exec python3 -u -m modules.main --config "$CONFIG_FILE" --pc-ip "$PC_IP"
