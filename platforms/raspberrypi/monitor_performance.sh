#!/bin/bash

# =============================================================================
# Raspberry Pi Performance Monitor for BookFinder
# =============================================================================
#
# This script monitors system performance on Raspberry Pi while running
# the BookFinder system. It provides real-time feedback on system
# resources and potential bottlenecks.
#
# Usage:
#   chmod +x monitor_performance.sh
#   ./monitor_performance.sh
#
# 
# This script has been written with the help of AI.
# =============================================================================

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
REFRESH_INTERVAL=2  # seconds
LOG_FILE="/tmp/pi_performance.log"

# Functions for system monitoring
get_cpu_temp() {
    if command -v vcgencmd &> /dev/null; then
        vcgencmd measure_temp | cut -d= -f2 | cut -d\' -f1
    else
        echo "N/A"
    fi
}

get_throttle_status() {
    if command -v vcgencmd &> /dev/null; then
        local throttled=$(vcgencmd get_throttled | cut -d= -f2)
        if [ "$throttled" = "0x0" ]; then
            echo -e "${GREEN}No throttling${NC}"
        else
            echo -e "${RED}Throttled: $throttled${NC}"
        fi
    else
        echo "N/A"
    fi
}

get_memory_usage() {
    free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}'
}

get_swap_usage() {
    free | grep Swap | awk '{if($2>0) printf "%.1f", $3/$2 * 100.0; else print "0.0"}'
}

get_cpu_usage() {
    top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d% -f1
}

get_disk_usage() {
    df / | tail -1 | awk '{print $5}' | cut -d% -f1
}

get_load_average() {
    uptime | awk -F'load average:' '{print $2}' | cut -d, -f1 | xargs
}

check_yolo_process() {
    if pgrep -f "python.*app.py" > /dev/null || pgrep -f "micromamba.*python" > /dev/null; then
        echo -e "${GREEN}Running${NC}"
    else
        echo -e "${YELLOW}Not detected${NC}"
    fi
}

print_header() {
    clear
    echo -e "${CYAN}=========================================${NC}"
    echo -e "${CYAN}  Raspberry Pi Performance Monitor${NC}"
    echo -e "${CYAN}  BookFinder System${NC}"
    echo -e "${CYAN}=========================================${NC}"
    echo -e "${BLUE}$(date)${NC}"
    echo
}

print_system_info() {
    local cpu_temp=$(get_cpu_temp)
    local throttle_status=$(get_throttle_status)
    local mem_usage=$(get_memory_usage)
    local swap_usage=$(get_swap_usage)
    local cpu_usage=$(get_cpu_usage)
    local disk_usage=$(get_disk_usage)
    local load_avg=$(get_load_average)
    local yolo_status=$(check_yolo_process)
    
    echo -e "${BLUE}System Status:${NC}"
    echo "  CPU Temperature: ${cpu_temp}°C"
    echo "  Throttling:      $throttle_status"
    echo "  Load Average:    $load_avg"
    echo
    
    echo -e "${BLUE}Resource Usage:${NC}"
    printf "  CPU Usage:       %s%%\n" "$cpu_usage"
    printf "  Memory Usage:    %.1f%%\n" "$mem_usage"
    printf "  Swap Usage:      %.1f%%\n" "$swap_usage"
    printf "  Disk Usage:      %s%%\n" "$disk_usage"
    echo
    
    echo -e "${BLUE}Application Status:${NC}"
    echo "  BookFinder Process:    $yolo_status"
    echo
    
    # Warning thresholds
    echo -e "${BLUE}Warnings:${NC}"
    local warnings=0
    
    if (( $(echo "$cpu_temp > 75" | bc -l) )); then
        echo -e "  ${RED}⚠ High CPU temperature: ${cpu_temp}°C${NC}"
        warnings=$((warnings + 1))
    fi
    
    if (( $(echo "$mem_usage > 90" | bc -l) )); then
        echo -e "  ${RED}⚠ High memory usage: ${mem_usage}%${NC}"
        warnings=$((warnings + 1))
    fi
    
    if (( $(echo "$swap_usage > 50" | bc -l) )); then
        echo -e "  ${YELLOW}⚠ High swap usage: ${swap_usage}%${NC}"
        warnings=$((warnings + 1))
    fi
    
    if [ "$disk_usage" -gt 90 ]; then
        echo -e "  ${RED}⚠ High disk usage: ${disk_usage}%${NC}"
        warnings=$((warnings + 1))
    fi
    
    if [ "$warnings" -eq 0 ]; then
        echo -e "  ${GREEN}✓ All systems normal${NC}"
    fi
    
    echo
}

print_recommendations() {
    local cpu_temp=$(get_cpu_temp)
    local mem_usage=$(get_memory_usage)
    
    echo -e "${BLUE}Recommendations:${NC}"
    
    if (( $(echo "$cpu_temp > 70" | bc -l) )); then
        echo "  • Consider adding cooling (fan/heatsink)"
        echo "  • Reduce processing intensity"
    fi
    
    if (( $(echo "$mem_usage > 85" | bc -l) )); then
        echo "  • Close unnecessary applications"
        echo "  • Consider using smaller YOLO model (nano instead of small)"
        echo "  • Reduce image processing resolution"
    fi
    
    echo "  • Use Ctrl+C to exit monitor"
    echo
}

log_performance() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local cpu_temp=$(get_cpu_temp)
    local mem_usage=$(get_memory_usage)
    local cpu_usage=$(get_cpu_usage)
    
    echo "$timestamp,$cpu_temp,$mem_usage,$cpu_usage" >> "$LOG_FILE"
}

# Main monitoring loop
main() {
    # Create log file header if it doesn't exist
    if [ ! -f "$LOG_FILE" ]; then
        echo "timestamp,cpu_temp,memory_usage,cpu_usage" > "$LOG_FILE"
    fi
    
    echo -e "${GREEN}Starting performance monitoring...${NC}"
    echo -e "${GREEN}Refresh interval: ${REFRESH_INTERVAL} seconds${NC}"
    echo -e "${GREEN}Log file: $LOG_FILE${NC}"
    echo
    echo "Press Ctrl+C to stop monitoring"
    sleep 2
    
    # Main monitoring loop
    while true; do
        print_header
        print_system_info
        print_recommendations
        log_performance
        
        sleep "$REFRESH_INTERVAL"
    done
}

# Signal handlers
cleanup() {
    echo
    echo -e "${GREEN}Performance monitoring stopped.${NC}"
    echo -e "${GREEN}Log saved to: $LOG_FILE${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Check dependencies
if ! command -v bc &> /dev/null; then
    echo -e "${YELLOW}Installing bc for calculations...${NC}"
    sudo apt install -y bc
fi

# Start monitoring
main "$@"