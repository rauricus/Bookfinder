# Raspberry Pi Platform Support

This directory contains scripts and documentation for running the BookFinder system on Raspberry Pi hardware.

## Overview

The Raspberry Pi platform is intended to provide an affordable way to run the BookFinder system on dedicated hardware. While performance is expected to be lower than desktop systems, it should be sufficient for many use cases and offers the advantage of a compact, low-power solution.


## Hardware Requirements

The following recommendations are based on similar AI/ML projects and general best practices. Actual requirements may vary and need validation through testing.

### Expected minimum requirements
- **Raspberry Pi 4 Model B** (4GB RAM) - *Required for ARM64 and sufficient memory*
- **32GB microSD card** (Class 10 or better) - *Based on typical OS + ML libraries size*
- **Power supply** (official 5V 3A recommended) - *Essential for stable operation*

### Expected recommended starting configuration
- **Raspberry Pi 4 Model B** (8GB RAM) - *More headroom for larger models*
- **64GB microSD card** (Class 10 or better, A2 rating preferred)
- **Active cooling** (fan or heatsink case) - *AI workloads generate heat*
- **Fast microSD card** or USB 3.0 SSD for better I/O performance


## Software Requirements

- **Raspberry Pi OS** (64-bit, Bullseye or newer) - *Required for modern Python ML libraries*
- **Internet connection** for setup and package downloads
- **At least 8GB free disk space** after OS installation - *Estimated for conda environment and models*

Actual disk space requirements will depend on which models and features are used.

## Quick Setup

1. **Flash Raspberry Pi OS** to your microSD card using Raspberry Pi Imager
2. **Enable SSH** (optional, for headless setup)
3. **Boot your Pi** and complete initial setup
4. **Clone the project** to your Pi
5. **Run the setup script**:

```bash
cd /path/to/Objekterkennung.yolo11/platforms/raspberrypi
chmod +x setup_raspberrypi.sh
./setup_raspberrypi.sh
```

## What the Setup Script Does

The `setup_raspberrypi.sh` script automatically:

### System Configuration
- ✅ **Updates** all system packages
- ✅ **Increases swap space** to 2GB (if not already configured)
- ✅ **Optimizes GPU memory** allocation for better system performance

### Software Installation
- ✅ **Installs essential system dependencies** (build tools, git, wget)
- ✅ **Downloads and configures Micromamba** for package management
- ✅ **Runs existing project setup script** (`1_create-conda-env.sh`) which handles:
  - Python environment creation with all required packages
  - EAST text detection model download
  - SymSpell dictionaries download
  - Directory structure setup

### Performance Optimization
- ✅ **Configures memory split** for optimal performance
- ✅ **Sets up CMA** for better video processing
- ✅ **Creates systemd service** (optional) for auto-start functionality


## Network Access

The BookFinder system includes a web interface that will be accessible at:
- **Local access**: `http://localhost:5000`
- **Network access**: `http://[PI_IP_ADDRESS]:5000`

Find your Pi's IP address with: `hostname -I`

## Service Management

If you enabled the systemd service during setup:

```bash
# Start service
sudo systemctl start bookfinder

# Stop service
sudo systemctl stop bookfinder

# Enable auto-start on boot
sudo systemctl enable bookfinder

# Check service status
sudo systemctl status bookfinder

# View service logs
sudo journalctl -u bookfinder -f
```
