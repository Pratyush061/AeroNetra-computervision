#!/usr/bin/env bash
# scripts/run_agent.sh
# Run this script in Terminal 2.

if ! command -v MicroXRCEAgent &> /dev/null; then
    echo "Error: MicroXRCEAgent command not found. Please ensure it is installed and in your PATH."
    exit 1
fi

echo "Starting Micro XRCE-DDS Agent on UDP port 8888..."
MicroXRCEAgent udp4 -p 8888
