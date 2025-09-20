#!/bin/bash

# =============================================================================
# Raspberry Pi Utilities for BookFinder
# =============================================================================
#
# Collection of utility functions for maintaining and troubleshooting
# the BookFinder system on Raspberry Pi.
#
# Usage:
#   chmod +x pi_utils.sh
#   ./pi_utils.sh [command]
#
# Available commands:
#   status      - Show system status
#   cleanup     - Clean temporary files and logs
#   update      - Update system and conda environment
#   restart     - Restart BookFinder service
#   logs        - Show application logs
#   backup      - Create configuration backup
#   restore     - Restore from backup
#   test        - Run system tests
#
# This script has been written with the help of AI.
# =============================================================================

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
BACKUP_DIR="$HOME/yolo11_backups"
CONDA_ENV="yolo11"

# Logging
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# =============================================================================
# System Status Functions
# =============================================================================

show_status() {
    log_info "BookFinder System - System Status"
    echo "=============================="
    
    # System info
    echo "System Information:"
    echo "  OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'=' -f2 | tr -d '"')"
    echo "  Uptime: $(uptime -p)"
    echo "  Load: $(uptime | awk -F'load average:' '{print $2}')"
    
    # Hardware status
    echo
    echo "Hardware Status:"
    if command -v vcgencmd &> /dev/null; then
        echo "  CPU Temp: $(vcgencmd measure_temp)"
        echo "  Throttling: $(vcgencmd get_throttled)"
        echo "  GPU Memory: $(vcgencmd get_mem gpu)"
    fi
    
    # Memory and storage
    echo
    echo "Memory Usage:"
    free -h
    
    echo
    echo "Disk Usage:"
    df -h /
    
    # Service status
    echo
    echo "Service Status:"
    if systemctl is-active --quiet bookfinder; then
        echo "  BookFinder Service: ${GREEN}Active${NC}"
    else
        echo "  BookFinder Service: ${RED}Inactive${NC}"
    fi
    
    # Process status
    echo
    echo "Process Status:"
    if pgrep -f "python.*app.py" > /dev/null; then
        echo "  BookFinder Application: ${GREEN}Running${NC}"
        echo "  PID: $(pgrep -f "python.*app.py")"
    else
        echo "  BookFinder Application: ${RED}Not Running${NC}"
    fi
    
    # Environment status
    echo
    echo "Environment Status:"
    if command -v micromamba &> /dev/null; then
        echo "  Micromamba: ${GREEN}Installed${NC}"
        if micromamba env list | grep -q "$CONDA_ENV"; then
            echo "  BookFinder Environment: ${GREEN}Available${NC}"
        else
            echo "  BookFinder Environment: ${RED}Missing${NC}"
        fi
    else
        echo "  Micromamba: ${RED}Not Installed${NC}"
    fi
}

# =============================================================================
# Cleanup Functions
# =============================================================================

cleanup_system() {
    log_info "Cleaning up system..."
    
    # Clean temporary files
    log_info "Removing temporary files..."
    sudo apt autoremove -y
    sudo apt autoclean
    
    # Clean conda cache
    if command -v micromamba &> /dev/null; then
        log_info "Cleaning conda cache..."
        micromamba clean --all -y
    fi
    
    # Clean application logs
    log_info "Rotating application logs..."
    if [ -d "$PROJECT_ROOT/logs" ]; then
        find "$PROJECT_ROOT/logs" -name "*.log" -mtime +7 -delete
    fi
    
    # Clean output directory
    log_info "Cleaning old output files..."
    if [ -d "$PROJECT_ROOT/output" ]; then
        find "$PROJECT_ROOT/output" -name "predict*" -mtime +3 -exec rm -rf {} +
    fi
    
    # Clean system logs
    log_info "Cleaning system logs..."
    sudo journalctl --vacuum-time=7d
    
    log_success "System cleanup completed"
}

# =============================================================================
# Update Functions
# =============================================================================

update_system() {
    log_info "Updating system and environment..."
    
    # Update system packages
    log_info "Updating system packages..."
    sudo apt update && sudo apt upgrade -y
    
    # Update conda environment
    if command -v micromamba &> /dev/null && micromamba env list | grep -q "$CONDA_ENV"; then
        log_info "Updating conda environment..."
        cd "$PROJECT_ROOT"
        micromamba env update -n "$CONDA_ENV" -f yolo11.condaenv.yml
    fi
    
    # Update project from git if available
    if [ -d "$PROJECT_ROOT/.git" ]; then
        log_info "Checking for project updates..."
        cd "$PROJECT_ROOT"
        git fetch
        if [ $(git rev-list HEAD...origin/master --count) -gt 0 ]; then
            log_warning "Updates available. Review changes before pulling."
            git log --oneline HEAD..origin/master
        else
            log_success "Project is up to date"
        fi
    fi
    
    log_success "Update completed"
}

# =============================================================================
# Service Management
# =============================================================================

restart_service() {
    log_info "Restarting BookFinder service..."
    
    if systemctl is-active --quiet bookfinder; then
        sudo systemctl restart bookfinder
        sleep 2
        if systemctl is-active --quiet bookfinder; then
            log_success "Service restarted successfully"
        else
            log_error "Service failed to restart"
            sudo systemctl status bookfinder
        fi
    else
        log_warning "Service is not running. Starting..."
        sudo systemctl start bookfinder
        sleep 2
        if systemctl is-active --quiet bookfinder; then
            log_success "Service started successfully"
        else
            log_error "Service failed to start"
            sudo systemctl status bookfinder
        fi
    fi
}

show_logs() {
    log_info "Showing application logs..."
    
    if systemctl is-active --quiet bookfinder; then
        log_info "Service logs (last 50 lines):"
        sudo journalctl -u bookfinder -n 50 --no-pager
    else
        log_warning "Service is not running"
    fi
    
    # Show application log files if they exist
    if [ -d "$PROJECT_ROOT/logs" ]; then
        log_info "Application log files:"
        ls -la "$PROJECT_ROOT/logs/"
        
        # Show latest log file
        local latest_log=$(ls -t "$PROJECT_ROOT/logs/"*.log 2>/dev/null | head -1)
        if [ -n "$latest_log" ]; then
            log_info "Latest log file content (last 20 lines):"
            tail -20 "$latest_log"
        fi
    fi
}

# =============================================================================
# Backup and Restore
# =============================================================================

create_backup() {
    log_info "Creating system backup..."
    
    mkdir -p "$BACKUP_DIR"
    local backup_name="yolo11_backup_$(date +%Y%m%d_%H%M%S)"
    local backup_path="$BACKUP_DIR/$backup_name"
    
    mkdir -p "$backup_path"
    
    # Backup configuration files
    log_info "Backing up configuration files..."
    cp "$PROJECT_ROOT/config.py" "$backup_path/" 2>/dev/null || true
    cp "$PROJECT_ROOT/yolo11.condaenv.yml" "$backup_path/"
    
    # Backup service file if it exists
    if [ -f "/etc/systemd/system/bookfinder.service" ]; then
        sudo cp "/etc/systemd/system/bookfinder.service" "$backup_path/"
    fi
    
    # Backup system configuration
    cp /etc/dphys-swapfile "$backup_path/" 2>/dev/null || true
    cp /boot/config.txt "$backup_path/" 2>/dev/null || true
    
    # Create backup info
    cat > "$backup_path/backup_info.txt" << EOF
Backup created: $(date)
System: $(uname -a)
Python environment: $CONDA_ENV
Project path: $PROJECT_ROOT
EOF
    
    log_success "Backup created: $backup_path"
}

restore_backup() {
    log_info "Available backups:"
    if [ -d "$BACKUP_DIR" ]; then
        ls -la "$BACKUP_DIR/"
        echo
        read -p "Enter backup directory name to restore: " backup_name
        
        local backup_path="$BACKUP_DIR/$backup_name"
        if [ -d "$backup_path" ]; then
            log_info "Restoring from: $backup_path"
            
            # Restore configuration files
            if [ -f "$backup_path/config.py" ]; then
                cp "$backup_path/config.py" "$PROJECT_ROOT/"
                log_info "Restored config.py"
            fi
            
            if [ -f "$backup_path/bookfinder.service" ]; then
                sudo cp "$backup_path/bookfinder.service" "/etc/systemd/system/"
                sudo systemctl daemon-reload
                log_info "Restored systemd service"
            fi
            
            log_success "Restore completed"
        else
            log_error "Backup directory not found: $backup_path"
        fi
    else
        log_warning "No backups found"
    fi
}

# =============================================================================
# Testing Functions
# =============================================================================

run_tests() {
    log_info "Running system tests..."
    
    # Test 1: Check dependencies
    log_info "Test 1: Checking dependencies..."
    local deps_ok=true
    
    if ! command -v micromamba &> /dev/null; then
        log_error "Micromamba not found"
        deps_ok=false
    fi
    
    if ! command -v tesseract &> /dev/null; then
        log_error "Tesseract not found"
        deps_ok=false
    fi
    
    if $deps_ok; then
        log_success "Dependencies OK"
    fi
    
    # Test 2: Check Python environment
    log_info "Test 2: Checking Python environment..."
    if micromamba env list | grep -q "$CONDA_ENV"; then
        log_success "Python environment OK"
    else
        log_error "Python environment missing"
    fi
    
    # Test 3: Check models
    log_info "Test 3: Checking models..."
    local models_ok=true
    
    if [ ! -f "$PROJECT_ROOT/models/detect-book-spines.pt" ]; then
        log_warning "BookFinder model not found"
        models_ok=false
    fi
    
    if [ ! -f "$PROJECT_ROOT/models/east_text_detection.pb" ]; then
        log_warning "EAST model not found"
        models_ok=false
    fi
    
    if $models_ok; then
        log_success "Models OK"
    else
        log_warning "Some models missing - functionality may be limited"
    fi
    
    # Test 4: Check system resources
    log_info "Test 4: Checking system resources..."
    local mem_total=$(free -m | grep Mem | awk '{print $2}')
    local swap_total=$(free -m | grep Swap | awk '{print $2}')
    
    if [ "$mem_total" -lt 3500 ]; then
        log_warning "Low memory: ${mem_total}MB (recommended: 4GB+)"
    else
        log_success "Memory OK: ${mem_total}MB"
    fi
    
    if [ "$swap_total" -lt 1500 ]; then
        log_warning "Low swap: ${swap_total}MB (recommended: 2GB+)"
    else
        log_success "Swap OK: ${swap_total}MB"
    fi
    
    log_info "System tests completed"
}

# =============================================================================
# Help and Main
# =============================================================================

show_help() {
    echo "Raspberry Pi Utilities for BookFinder"
    echo
    echo "Usage: $0 [command]"
    echo
    echo "Available commands:"
    echo "  status      Show system status and health"
    echo "  cleanup     Clean temporary files and logs"
    echo "  update      Update system and conda environment"
    echo "  restart     Restart BookFinder service"
    echo "  logs        Show application logs"
    echo "  backup      Create configuration backup"
    echo "  restore     Restore from backup"
    echo "  test        Run system tests"
    echo "  help        Show this help message"
    echo
    echo "Examples:"
    echo "  $0 status"
    echo "  $0 cleanup"
    echo "  $0 restart"
}

# Main function
main() {
    case "${1:-help}" in
        "status")
            show_status
            ;;
        "cleanup")
            cleanup_system
            ;;
        "update")
            update_system
            ;;
        "restart")
            restart_service
            ;;
        "logs")
            show_logs
            ;;
        "backup")
            create_backup
            ;;
        "restore")
            restore_backup
            ;;
        "test")
            run_tests
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Run main function with all arguments
main "$@"