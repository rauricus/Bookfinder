# Memory Optimization for BookFinder on Raspberry Pi

This document explains the intended memory optimizations in the BookFinder setup script for Raspberry Pi hardware, specifically the GPU memory split and CMA (Contiguous Memory Allocator) configuration.

## Overview

The Raspberry Pi shares its physical RAM between the CPU (system) and GPU (VideoCore). For AI/ML applications like BookFinder, optimizing this memory allocation should improve performance and reduce the likelihood of out-of-memory errors. 


## GPU Memory Split (`gpu_mem`)

### What is GPU Memory Split?

The Raspberry Pi divides its physical RAM between:
- **System RAM (CPU)**: Used by the operating system, applications, and AI models
- **GPU RAM (VideoCore)**: Used for graphics processing, video encoding/decoding, and camera operations

This split is static and configured at boot time via `/boot/config.txt`.

### Default vs. Optimized Configuration

| Configuration | GPU Memory | System Memory (4GB Pi) | Use Case |
|---------------|------------|------------------------|----------|
| **Default** | 76MB | ~3.86GB | General desktop use |
| **BookFinder Optimized** | 64MB | ~3.87GB | AI/ML applications |

### Implementation in Setup Script

```bash
# GPU memory split (more RAM for system)
if ! grep -q "gpu_mem=" /boot/config.txt; then
    echo "gpu_mem=64" | sudo tee -a /boot/config.txt
    log_info "GPU memory set to 64MB"
fi
```

### Why 64MB for BookFinder?

#### Expected BookFinder Memory Requirements:
- **YOLO11 Models**: Estimated 200-500MB depending on model size (nano, small, medium, etc.)
- **OpenCV Operations**: Image matrices and processing buffers
- **Tesseract OCR**: Text recognition and language models
- **Python Environment**: Libraries and runtime overhead
- **Web Interface**: Flask application and WebSocket connections

#### Expected Minimal GPU Requirements:
- **No 3D Graphics**: BookFinder should use simple web UI
- **No Hardware Video Decode**: Planned for direct image/camera processing
- **Basic Display Output**: Console and simple graphics only
- **Limited Video Processing**: Basic camera frame handling anticipated

**Expected Result**: +12MB more system RAM for AI models while maintaining sufficient GPU functionality.

## CMA (Contiguous Memory Allocator)

### What is CMA?

CMA reserves a contiguous block of physical memory for devices that require large, physically continuous memory regions. This is essential for:
- Camera modules (Pi Camera, USB cameras)
- DMA (Direct Memory Access) operations
- Video processing hardware
- Large buffer allocations

### Default vs. Optimized Configuration

| Configuration | CMA Size | Benefits |
|---------------|----------|----------|
| **Default** | 64MB | Basic camera/video support |
| **BookFinder Optimized** | 128MB | Enhanced image processing stability |

### Implementation in Setup Script

```bash
# Increase CMA for better video processing
if ! grep -q "cma=" /boot/cmdline.txt; then
    sudo sed -i 's/$/ cma=128M/' /boot/cmdline.txt
    log_info "CMA set to 128MB"
fi
```

### Why 128MB CMA for BookFinder?

#### Expected Enhanced Performance For:
1. **Pi Camera Module**: Should provide stable high-resolution image capture
2. **USB Cameras**: May improve compatibility with UVC devices
3. **OpenCV Operations**: Should handle large image matrix operations better
4. **YOLO Inference**: May improve model input/output buffer management
5. **Real-time Processing**: Could reduce frame drops during live processing

#### Expected Memory Layout:

```
Raspberry Pi 4GB Memory Layout (Theoretical):
┌─────────────────────────────────────────────────┐
│ Total RAM: 4096MB                               │
├─────────────────────────────────────────────────┤
│ GPU Memory: 64MB                                │
├─────────────────────────────────────────────────┤
│ CMA (Contiguous): 128MB                         │
├─────────────────────────────────────────────────┤
│ System RAM: ~3904MB                             │
│ ├─ OS Kernel: ~200MB (estimated)                │
│ ├─ BookFinder App: ~800-1200MB (estimated)      │
│ ├─- Available: ~2500-2900MB (estimated)         │
└─────────────────────────────────────────────────┘
```

## Monitoring and Verification

### Check Current Configuration

```bash
# GPU memory allocation
vcgencmd get_mem arm    # Shows system RAM allocation
vcgencmd get_mem gpu    # Shows GPU RAM allocation

# CMA information
cat /proc/meminfo | grep Cma
# CmaTotal: Shows total CMA size
# CmaFree:  Shows available CMA memory

# Overall memory usage
free -h
```

## Setup and monitoring

Run the setup script to set up the above:

```bash
cd platforms/raspberrypi
./setup_raspberrypi.sh
```

The included `monitor_performance.sh` script provides real-time monitoring:

```bash
./monitor_performance.sh
```

### Reverting Changes

If you need to revert the optimizations:

```bash
# Remove GPU memory setting
sudo sed -i '/gpu_mem=64/d' /boot/config.txt

# Remove CMA setting  
sudo sed -i 's/ cma=128M//g' /boot/cmdline.txt

# Reboot to apply changes
sudo reboot
```

*These optimizations have been suggested and documented by AI.*
*I've screened the changes and have tuned down the marketing speech afterwards.*