#!/usr/bin/env bash
# Setup script for ultrawork demo
# Run this BEFORE recording with VHS

set -euo pipefail

DEMO_DIR="/tmp/myapp"

echo "Setting up demo environment at $DEMO_DIR..."

# Clean slate - empty directory for "from scratch" build
rm -rf "$DEMO_DIR"
mkdir -p "$DEMO_DIR"

echo ""
echo "Demo environment ready at $DEMO_DIR (empty directory)"
echo ""
echo "Now run: vhs demo/ultrawork-demo.tape"
