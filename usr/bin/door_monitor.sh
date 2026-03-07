#!/bin/sh

# Door Monitor for OpenIPC Doorphone
# Communicates with ESP32 via UART
# Supports: RFID keys, buttons, door sensor, relay control

CONFIG_FILE="/etc/door_keys.conf"
LOG_FILE="/var/log/door_monitor.log"
FIFO="/tmp/mqtt_fifo"
SIP_CONTROL="/tmp/sip_control"

# UART device (auto-detect)
UART_DEV=""
if [ -c /dev/ttyS0 ]; then
    UART_DEV="/dev/ttyS0"
elif [ -c /dev/ttyAMA0 ]; then
    UART_DEV="/dev/ttyAMA0"
else
    echo "No UART device found!"
    exit 1
fi

# Настройки звуков
SOUND_CONFIG="/etc/doorphone_sounds.conf"
[ -f "$SOUND_CONFIG" ] && . "$SOUND_CONFIG"

# Значения по умолчанию для звуков
[ -z "$SOUND_KEY_ACCEPT" ] && SOUND_KEY_ACCEPT="beep"
[ -z "$SOUND_KEY_DENY" ] && SOUND_KEY_DENY="denied"
[ -z "$SOUND_DOOR_OPEN" ] && SOUND_DOOR_OPEN="door_open"
[ -z "$SOUND_DOOR_CLOSE" ] && SOUND_DOOR_CLOSE="door_close"
[ -z "$SOUND_BUTTON" ] && SOUND_BUTTON="beep"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Воспроизведение звука
play_sound() {
    local sound="$1"
    if [ -n "$sound" ] && [ "$sound" != "none" ] && [ -f "/usr/share/sounds/doorphone/${sound}.pcm" ]; then
        echo "/play ${sound}.pcm" | nc 127.0.0.1 3000 2>/dev/null
        log "Playing sound: $sound"
    fi
}

# Проверка ключа
check_key() {
    local key="$1"
    local current_time=$(date +%s)
    
    if [ ! -f "$CONFIG_FILE" ]; then
        return 1
    fi
    
    while IFS='|' read -r k o d e; do
        if [ "$k" = "$key" ]; then
            # Проверяем временный ключ
            if [ -n "$e" ] && [ "$e" -eq "$e" ] 2>/dev/null; then
                if [ "$e" -gt "$current_time" ]; then
                    log "Key $key allowed (temporary, expires: $(date -d @$e))"
                    play_sound "$SOUND_KEY_ACCEPT"
                    return 0
                else
                    log "Key $key denied (expired)"
                    play_sound "$SOUND_KEY_DENY"
                    return 1
                fi
            else
                # Постоянный ключ
                log "Key $key allowed (permanent)"
                play_sound "$SOUND_KEY_ACCEPT"
                return 0
            fi
        fi
    done < "$CONFIG_FILE"
    
    log "Key $key denied (not found)"
    play_sound "$SOUND_KEY_DENY"
    return 1
}

# Открытие двери
open_door() {
    local source="$1"
    log "Door opened by $source"
    echo "OPEN" > "$UART_DEV"
    play_sound "$SOUND_DOOR_OPEN"
    
    # Уведомляем MQTT
    if [ -p "$FIFO" ]; then
        echo "DOOR:OPEN" > "$FIFO" &
    fi
}

# Закрытие двери
close_door() {
    local source="$1"
    log "Door closed by $source"
    echo "CLOSE" > "$UART_DEV"
    play_sound "$SOUND_DOOR_CLOSE"
    
    # Уведомляем MQTT
    if [ -p "$FIFO" ]; then
        echo "DOOR:CLOSED" > "$FIFO" &
    fi
}

# Совершение звонка
make_call() {
    local number="$1"
    [ -z "$number" ] && number=$(cat /etc/baresip/call_number 2>/dev/null || echo "100")
    
    log "Making SIP call to $number"
    echo "/dial $number" | nc 127.0.0.1 3000 2>/dev/null
    
    # Можно также отправить команду на ESP (если нужно)
    # echo "CALL:$number" > "$UART_DEV"
}

# Обработка команд от ESP32
handle_esp_command() {
    local line="$1"
    
    case "$line" in
        KEY:*)
            # Формат: KEY:bits:code
            local key=$(echo "$line" | cut -d: -f3)
            log "RFID key received: $key"
            
            if check_key "$key"; then
                open_door "RFID"
                
                # Уведомляем MQTT
                if [ -p "$FIFO" ]; then
                    echo "KEY:$key" > "$FIFO" &
                    echo "ACCESS:allowed" > "$FIFO" &
                fi
            else
                if [ -p "$FIFO" ]; then
                    echo "KEY:$key" > "$FIFO" &
                    echo "ACCESS:denied" > "$FIFO" &
                fi
            fi
            ;;
            
        "BUTTON:EXIT")
            log "Exit button pressed"
            play_sound "$SOUND_BUTTON"
            open_door "EXIT_BUTTON"
            
            if [ -p "$FIFO" ]; then
                echo "BUTTON:EXIT" > "$FIFO" &
            fi
            ;;
            
        "BUTTON:CALL")
            log "Call button pressed"
            play_sound "$SOUND_BUTTON"
            make_call
            
            if [ -p "$FIFO" ]; then
                echo "BUTTON:CALL" > "$FIFO" &
            fi
            ;;
            
        CALL_BUTTON_HELD:*)
            local duration=$(echo "$line" | cut -d: -f2)
            log "Call button held for ${duration}ms"
            # Можно выполнить какое-то специальное действие
            ;;
            
        "DOOR:OPEN")
            log "Door opened (sensor)"
            if [ -p "$FIFO" ]; then
                echo "DOOR:OPEN" > "$FIFO" &
            fi
            ;;
            
        "DOOR:CLOSED")
            log "Door closed (sensor)"
            if [ -p "$FIFO" ]; then
                echo "DOOR:CLOSED" > "$FIFO" &
            fi
            ;;
            
        DOOR_OPENED:*)
            local source=$(echo "$line" | cut -d: -f2)
            log "Door opened by $source (from ESP)"
            play_sound "$SOUND_DOOR_OPEN"
            ;;
            
        STATUS:*)
            log "ESP status: ${line#STATUS:}"
            ;;
            
        ESP32_READY)
            log "ESP32 is ready"
            # Отправляем текущие настройки
            echo "SET_DEFAULT_TIME:5000" > "$UART_DEV"
            ;;
            
        FW_VERSION:*)
            log "ESP32 firmware: ${line#FW_VERSION:}"
            ;;
            
        *)
            log "Unknown ESP command: $line"
            ;;
    esac
}

# Обработка команд от MQTT (через FIFO)
handle_mqtt_command() {
    local line="$1"
    
    case "$line" in
        RELAY:ON)
            log "MQTT command: relay ON"
            echo "RELAY:ON" > "$UART_DEV"
            ;;
        RELAY:OFF)
            log "MQTT command: relay OFF"
            echo "RELAY:OFF" > "$UART_DEV"
            ;;
        RELAY:TOGGLE)
            log "MQTT command: relay TOGGLE"
            echo "RELAY:TOGGLE" > "$UART_DEV"
            ;;
    esac
}

# Основной цикл
main() {
    log "Door monitor starting on $UART_DEV"
    
    # Создаем FIFO если нет
    [ -p "$FIFO" ] || mkfifo "$FIFO"
    
    # Настраиваем UART
    stty -F "$UART_DEV" 115200 cs8 -cstopb -parenb raw
    
    # Отправляем приветствие ESP
    echo "CAMERA_READY" > "$UART_DEV"
    
    log "UART configured, waiting for ESP32..."
    
    # Читаем из UART
    cat "$UART_DEV" | while read line; do
        [ -n "$line" ] && handle_esp_command "$line"
    done &
    
    # Читаем из FIFO (команды от MQTT)
    while true; do
        if read line < "$FIFO"; then
            handle_mqtt_command "$line"
        fi
        sleep 0.1
    done
}

# Запуск
main
