#!/bin/bash

# =============================================================================
# Raspberry Pi Setup Script for BookFinder
# =============================================================================
#
# This script prepares a Raspberry Pi for running the BookFinder system.
# It installs all necessary dependencies and configures the system for 
# optimal performance.
#
# Usage:
#   chmod +x setup_raspberrypi.sh
#   ./setup_raspberrypi.sh
#
# This script has been written with the help of AI.
# =============================================================================

set -e  # Exit on any error

# Color codes for output formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration variables
TARGET_SWAP_SIZE="2048"  # 2GB in MB
CONDA_ENV_NAME="yolo11"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# =============================================================================
# System Information and Validation
# =============================================================================

print_system_info() {
    log_info "Raspberry Pi Setup for BookFinder System"
    log_info "========================================"
    echo
    log_info "System Information:"
    echo "  OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'=' -f2 | tr -d '"')"
    echo "  Kernel: $(uname -r)"
    echo "  Architecture: $(uname -m)"
    echo "  RAM: $(free -h | grep Mem | awk '{print $2}')"
    echo "  CPU: $(nproc) cores"
    echo "  Disk Space: $(df -h / | tail -1 | awk '{print $4}') available"
    echo
}

check_raspberry_pi() {
    if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        log_warning "This script is optimized for Raspberry Pi hardware."
        log_warning "Continuing anyway, but some optimizations may not apply."
    else
        log_success "Raspberry Pi detected"
    fi
}

check_disk_space() {
    local available_gb=$(df / | tail -1 | awk '{print int($4/1024/1024)}')
    if [ "$available_gb" -lt 8 ]; then
        log_error "Insufficient disk space. At least 8GB free space required."
        log_error "Available: ${available_gb}GB"
        exit 1
    fi
    log_success "Sufficient disk space available: ${available_gb}GB"
}

# =============================================================================
# Swap Configuration
# =============================================================================

configure_swap() {
    log_info "Configuring swap space..."
    
    # Check current swap size
    local current_swap=$(free -m | grep Swap | awk '{print $2}')
    log_info "Current swap size: ${current_swap}MB"
    
    if [ "$current_swap" -ge "$TARGET_SWAP_SIZE" ]; then
        log_success "Swap size is already ${current_swap}MB (>= ${TARGET_SWAP_SIZE}MB). No changes needed."
        return 0
    fi
    
    log_info "Increasing swap size to ${TARGET_SWAP_SIZE}MB..."
    
    # Stop swap
    sudo dphys-swapfile swapoff || true
    
    # Configure new swap size
    if [ -f /etc/dphys-swapfile ]; then
        # Backup original config
        sudo cp /etc/dphys-swapfile /etc/dphys-swapfile.backup
        
        # Update swap size
        sudo sed -i "s/^CONF_SWAPSIZE=.*/CONF_SWAPSIZE=${TARGET_SWAP_SIZE}/" /etc/dphys-swapfile
        
        # If CONF_SWAPSIZE doesn't exist, add it
        if ! grep -q "^CONF_SWAPSIZE=" /etc/dphys-swapfile; then
            echo "CONF_SWAPSIZE=${TARGET_SWAP_SIZE}" | sudo tee -a /etc/dphys-swapfile
        fi
    else
        # Create new config file
        echo "CONF_SWAPSIZE=${TARGET_SWAP_SIZE}" | sudo tee /etc/dphys-swapfile
    fi
    
    # Setup and start new swap
    sudo dphys-swapfile setup
    sudo dphys-swapfile swapon
    
    # Verify new swap size (allow small rounding differences)
    local new_swap=$(free -m | grep Swap | awk '{print $2}')
    local minimum_acceptable=$((TARGET_SWAP_SIZE - 10))  # Allow 10MB tolerance
    
    if [ "$new_swap" -ge "$minimum_acceptable" ]; then
        log_success "Swap successfully configured to ${new_swap}MB (target: ${TARGET_SWAP_SIZE}MB)"
    else
        log_error "Failed to configure swap. Current size: ${new_swap}MB, expected: ~${TARGET_SWAP_SIZE}MB"
        exit 1
    fi
}

# =============================================================================
# System Updates and Dependencies
# =============================================================================

update_system() {
    log_info "Updating system packages..."
    sudo apt update && sudo apt upgrade -y
    log_success "System packages updated"
}

install_system_dependencies() {
    log_info "Installing essential system dependencies..."
    
    # Only essential system-level packages that cannot be installed via conda
    local packages=(
        # Essential system tools
        "build-essential"  # Required for compiling some conda packages
        "git"              # For cloning repositories
        "wget"             # For downloading files
        "curl"             # Alternative download tool
        "unzip"            # For extracting archives
        "zsh"              # Required for project setup script
        
        # System monitoring utilities
        "htop"             # Process monitoring
        
        # Only system-level libraries that conda packages depend on
        "cmake"            # Build system for some conda packages
        "pkg-config"       # Package configuration tool
    )
    
    log_info "Installing minimal system packages..."
    
    for package in "${packages[@]}"; do
        log_info "Installing ${package}..."
        sudo apt install -y "$package"
    done
    
    log_success "Essential system dependencies installed"
}

# =============================================================================
# Micromamba Installation
# =============================================================================

install_micromamba() {
    log_info "Installing Micromamba..."
    
    if command -v micromamba &> /dev/null; then
        log_success "Micromamba is already installed"
        return 0
    fi
    
    # Download and install micromamba
    local micromamba_dir="${HOME}/.local/bin"
    mkdir -p "$micromamba_dir"
    
    curl -Ls https://micro.mamba.pm/api/micromamba/linux-aarch64/latest | tar -xvj -C "$micromamba_dir" --strip-components=1 bin/micromamba
    
    # Add to PATH if not already there
    if ! grep -q "micromamba" ~/.bashrc; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    fi
    
    # Initialize micromamba
    "$micromamba_dir/micromamba" shell init -s bash -p ~/micromamba
    
    log_success "Micromamba installed successfully"
    log_warning "Please restart your shell or run 'source ~/.bashrc' to use micromamba"
}

# =============================================================================
# Python Environment Setup
# =============================================================================

setup_conda_environment() {
    log_info "Setting up Python environment using existing project script..."
    
    # Source micromamba
    export PATH="$HOME/.local/bin:$PATH"
    eval "$(micromamba shell hook --shell bash)"
    
    # Use the existing project setup script which handles everything
    cd "$PROJECT_ROOT"
    
    if [ -f "1_create-conda-env.sh" ]; then
        log_info "Running existing conda environment setup script..."
        # Execute with zsh as the script requires zsh-specific syntax
        zsh "1_create-conda-env.sh"
        log_success "Python environment '$CONDA_ENV_NAME' configured via project script"
    else
        log_error "Project setup script '1_create-conda-env.sh' not found!"
        log_error "Please ensure you're in the correct project directory"
        exit 1
    fi
}

# =============================================================================
# Performance Optimization
# =============================================================================

optimize_performance() {
    log_info "Applying Raspberry Pi performance optimizations..."
    
    # GPU memory split (more RAM for system)
    if ! grep -q "gpu_mem=" /boot/config.txt; then
        echo "gpu_mem=64" | sudo tee -a /boot/config.txt
        log_info "GPU memory set to 64MB"
    fi
    
    # Increase CMA (Contiguous Memory Allocator) for better video processing
    if ! grep -q "cma=" /boot/cmdline.txt; then
        sudo sed -i 's/$/ cma=128M/' /boot/cmdline.txt
        log_info "CMA set to 128MB"
    fi
    
    # Optional: Enable camera interface (currently disabled)
    # Uncomment the following lines if camera support is needed:
    # if ! grep -q "start_x=1" /boot/config.txt; then
    #     echo "start_x=1" | sudo tee -a /boot/config.txt
    #     log_info "Camera interface enabled"
    # fi
    
    log_success "Performance optimizations applied"
}

# =============================================================================
# Service Configuration (Optional)
# =============================================================================

create_systemd_service() {
    log_info "Creating systemd service for BookFinder..."
    
    local service_file="/etc/systemd/system/bookfinder.service"
    
    sudo tee "$service_file" > /dev/null <<EOF
[Unit]
Description=BookFinder System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=${PROJECT_ROOT}
Environment=PATH=${HOME}/.local/bin:\$PATH
ExecStart=${HOME}/.local/bin/micromamba run -n ${CONDA_ENV_NAME} python app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    
    log_success "Systemd service created (not enabled by default)"
    log_info "To enable: sudo systemctl enable bookfinder"
    log_info "To start: sudo systemctl start bookfinder"
}

# =============================================================================
# Main Installation Process
# =============================================================================

main() {
    log_info "Starting Raspberry Pi setup for BookFinder System..."
    echo
    
    print_system_info
    check_raspberry_pi
    check_disk_space
    
    log_info "Starting installation process..."
    
    # System setup
    update_system
    install_system_dependencies
    configure_swap
    
    # Python environment
    install_micromamba
    setup_conda_environment
    
    # Performance and service setup
    optimize_performance
    
    # Optional service
    read -p "Do you want to create a systemd service for auto-start? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        create_systemd_service
    fi
    
    echo
    log_success "==================================================="
    log_success "Raspberry Pi setup completed successfully!"
    log_success "==================================================="
    echo
    log_info "Next steps:"
    echo "  1. Restart your Pi: sudo reboot"
    echo "  2. Activate the environment: micromamba activate ${CONDA_ENV_NAME}"
    echo "  3. Navigate to project: cd ${PROJECT_ROOT}"
    echo "  4. Run the application: python app.py"
    echo
    log_info "For web interface, the app will be available at: http://$(hostname -I | awk '{print $1}'):5000"
    echo
    
    # Check if reboot is needed
    if [ -f /var/run/reboot-required ]; then
        log_warning "A reboot is required to complete the setup."
        read -p "Reboot now? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo reboot
        fi
    fi
}

# =============================================================================
# Script Execution
# =============================================================================

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    log_error "Please do not run this script as root (use your regular user account)"
    exit 1
fi

# Run main function
main "$@"