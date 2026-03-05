#!/bin/sh
# Door monitor for OpenIPC

# Определяем UART устройство
if [ -c /dev/ttyS0 ]; then
    UART_DEV="/dev/ttyS0"
elif [ -c /dev/ttyAMA0 ]; then
    UART_DEV="/dev/ttyAMA0"
else
    UART_DEV=""
fi

UART_BAUD="115200"
KEYS_FILE="/etc/door_keys.conf"
LOG_FILE="/var/log/door_monitor.log"
PID_FILE="/var/run/door_monitor.pid"
CALL_NUMBER_FILE="/etc/baresip/call_number"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

load_keys() {
    if [ -f "$KEYS_FILE" ]; then
        cp "$KEYS_FILE" /tmp/door_keys.tmp
        log "Loaded $(wc -l < /tmp/door_keys.tmp) keys"
    else
        touch "$KEYS_FILE"
        touch /tmp/door_keys.tmp
        log "Created empty keys file"
    fi
}

check_key() {
    key="$1"
    if grep -q "^$key|" /tmp/door_keys.tmp 2>/dev/null; then
        owner=$(grep "^$key|" /tmp/door_keys.tmp | head -1 | cut -d'|' -f2)
        log "Key $key ALLOWED for $owner"
        return 0
    else
        log "Key $key DENIED"
        return 1
    fi
}

send_command() {
    cmd="$1"
    if [ -n "$UART_DEV" ] && [ -c "$UART_DEV" ]; then
        echo "$cmd" > "$UART_DEV" 2>/dev/null
        log "Sent to ESP: $cmd"
    fi
}

open_door() {
    send_command "OPEN"
    log "Door opened"
}

get_call_number() {
    if [ -f "$CALL_NUMBER_FILE" ]; then
        cat "$CALL_NUMBER_FILE"
    else
        echo "100"
    fi
}

run_daemon() {
    log "Door monitor starting..."
    if [ -n "$UART_DEV" ] && [ -c "$UART_DEV" ]; then
        stty -F "$UART_DEV" "$UART_BAUD" cs8 -cstopb -parenb 2>/dev/null
        log "UART $UART_DEV configured"
    fi
    
    load_keys
    log "Ready"
    
    while true; do
        if [ -n "$UART_DEV" ] && [ -c "$UART_DEV" ]; then
            read -t 1 line < "$UART_DEV" 2>/dev/null
            if [ -n "$line" ]; then
                line=$(echo "$line" | tr -d '\r\n')
                log "Received: $line"
                
                case "$line" in
                    KEY:*)
                        key=$(echo "$line" | cut -d':' -f2-)
                        if check_key "$key"; then
                            open_door
                            send_command "KEY_ACCEPTED"
                        else
                            send_command "KEY_DENIED"
                        fi
                        ;;
                    STATUS:*)
                        log "ESP Status: $line"
                        ;;
                    CALL:*)
                        number=$(echo "$line" | cut -d':' -f2)
                        log "Call button pressed - calling $number"
                        echo "/dial $number" | nc 127.0.0.1 3000
                        ;;
                    ESP32_READY)
                        log "ESP ready"
                        send_command "OPENIPC_READY"
                        ;;
                esac
            fi
        fi
        sleep 0.1
    done
}

case "$1" in
    start) ($0 run_daemon >/dev/null 2>&1 &) ;;
    stop) killall door_monitor.sh ;;
    restart) $0 stop; sleep 1; $0 start ;;
    status) pgrep -f door_monitor.sh >/dev/null && echo "Running" || echo "Stopped" ;;
    *) run_daemon ;;
esac
