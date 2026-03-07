#!/bin/sh

# MQTT Client for OpenIPC Doorphone
CONFIG_FILE="/etc/mqtt.conf"
LOG_FILE="/var/log/mqtt.log"

# Загружаем конфиг
if [ -f "$CONFIG_FILE" ]; then
    . "$CONFIG_FILE" 2>/dev/null
fi

# Значения по умолчанию
[ -z "$MQTT_HOST" ] && MQTT_HOST="192.168.1.30"
[ -z "$MQTT_PORT" ] && MQTT_PORT="1883"
[ -z "$MQTT_USER" ] && MQTT_USER="user"
[ -z "$MQTT_PASS" ] && MQTT_PASS="passwd"
[ -z "$MQTT_TOPIC_PREFIX" ] && MQTT_TOPIC_PREFIX="doorphone"
[ -z "$MQTT_DISCOVERY_PREFIX" ] && MQTT_DISCOVERY_PREFIX="homeassistant"

# Получаем уникальный ID устройства (hostname)
DEVICE_ID=$(hostname -s 2>/dev/null | tr -d '\n' | tr '.' '_' | tr '-' '_')
[ -z "$DEVICE_ID" ] && DEVICE_ID="openipc_doorphone"

# Очищаем DEVICE_ID от недопустимых символов
DEVICE_ID=$(echo "$DEVICE_ID" | sed 's/[^a-zA-Z0-9_-]//g')

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

send_discovery() {
    log "Sending discovery configurations for device: $DEVICE_ID"
    
    # 1. Door sensor (binary_sensor)
    mosquitto_pub -h "$MQTT_HOST" -p "$MQTT_PORT" -u "$MQTT_USER" -P "$MQTT_PASS" \
        -t "${MQTT_DISCOVERY_PREFIX}/binary_sensor/${DEVICE_ID}/door/config" \
        -m "{
            \"name\": \"Door Status\",
            \"unique_id\": \"${DEVICE_ID}_door\",
            \"state_topic\": \"${MQTT_TOPIC_PREFIX}/${DEVICE_ID}/door\",
            \"device_class\": \"door\",
            \"payload_on\": \"open\",
            \"payload_off\": \"closed\",
            \"availability_topic\": \"${MQTT_TOPIC_PREFIX}/${DEVICE_ID}/status\",
            \"device\": {
                \"identifiers\": [\"${DEVICE_ID}\"],
                \"name\": \"OpenIPC Doorphone\",
                \"model\": \"SIP Doorphone\",
                \"manufacturer\": \"OpenIPC\",
                \"sw_version\": \"2.0\"
            }
        }" -r 2>&1 >> "$LOG_FILE"
    log "Published door sensor"
    
    # 2. RFID sensor
    mosquitto_pub -h "$MQTT_HOST" -p "$MQTT_PORT" -u "$MQTT_USER" -P "$MQTT_PASS" \
        -t "${MQTT_DISCOVERY_PREFIX}/sensor/${DEVICE_ID}/rfid/config" \
        -m "{
            \"name\": \"RFID Key\",
            \"unique_id\": \"${DEVICE_ID}_rfid\",
            \"state_topic\": \"${MQTT_TOPIC_PREFIX}/${DEVICE_ID}/rfid\",
            \"availability_topic\": \"${MQTT_TOPIC_PREFIX}/${DEVICE_ID}/status\",
            \"device\": {
                \"identifiers\": [\"${DEVICE_ID}\"]
            }
        }" -r 2>&1 >> "$LOG_FILE"
    log "Published RFID sensor"
    
    # 3. Access sensor
    mosquitto_pub -h "$MQTT_HOST" -p "$MQTT_PORT" -u "$MQTT_USER" -P "$MQTT_PASS" \
        -t "${MQTT_DISCOVERY_PREFIX}/sensor/${DEVICE_ID}/access/config" \
        -m "{
            \"name\": \"Access Status\",
            \"unique_id\": \"${DEVICE_ID}_access\",
            \"state_topic\": \"${MQTT_TOPIC_PREFIX}/${DEVICE_ID}/access\",
            \"availability_topic\": \"${MQTT_TOPIC_PREFIX}/${DEVICE_ID}/status\",
            \"device\": {
                \"identifiers\": [\"${DEVICE_ID}\"]
            }
        }" -r 2>&1 >> "$LOG_FILE"
    log "Published access sensor"
    
    # 4. Relay switch
    mosquitto_pub -h "$MQTT_HOST" -p "$MQTT_PORT" -u "$MQTT_USER" -P "$MQTT_PASS" \
        -t "${MQTT_DISCOVERY_PREFIX}/switch/${DEVICE_ID}/relay/config" \
        -m "{
            \"name\": \"Door Relay\",
            \"unique_id\": \"${DEVICE_ID}_relay\",
            \"command_topic\": \"${MQTT_TOPIC_PREFIX}/${DEVICE_ID}/relay/set\",
            \"state_topic\": \"${MQTT_TOPIC_PREFIX}/${DEVICE_ID}/relay\",
            \"payload_on\": \"ON\",
            \"payload_off\": \"OFF\",
            \"availability_topic\": \"${MQTT_TOPIC_PREFIX}/${DEVICE_ID}/status\",
            \"device\": {
                \"identifiers\": [\"${DEVICE_ID}\"]
            }
        }" -r 2>&1 >> "$LOG_FILE"
    log "Published relay switch"
    
    # 5. Exit button (binary_sensor)
    mosquitto_pub -h "$MQTT_HOST" -p "$MQTT_PORT" -u "$MQTT_USER" -P "$MQTT_PASS" \
        -t "${MQTT_DISCOVERY_PREFIX}/binary_sensor/${DEVICE_ID}/button_exit/config" \
        -m "{
            \"name\": \"Exit Button\",
            \"unique_id\": \"${DEVICE_ID}_button_exit\",
            \"state_topic\": \"${MQTT_TOPIC_PREFIX}/${DEVICE_ID}/button/exit\",
            \"device_class\": \"button\",
            \"payload_on\": \"pressed\",
            \"payload_off\": \"released\",
            \"availability_topic\": \"${MQTT_TOPIC_PREFIX}/${DEVICE_ID}/status\",
            \"device\": {
                \"identifiers\": [\"${DEVICE_ID}\"]
            }
        }" -r 2>&1 >> "$LOG_FILE"
    log "Published exit button"
    
    # 6. Call button (binary_sensor)
    mosquitto_pub -h "$MQTT_HOST" -p "$MQTT_PORT" -u "$MQTT_USER" -P "$MQTT_PASS" \
        -t "${MQTT_DISCOVERY_PREFIX}/binary_sensor/${DEVICE_ID}/button_call/config" \
        -m "{
            \"name\": \"Call Button\",
            \"unique_id\": \"${DEVICE_ID}_button_call\",
            \"state_topic\": \"${MQTT_TOPIC_PREFIX}/${DEVICE_ID}/button/call\",
            \"device_class\": \"button\",
            \"payload_on\": \"pressed\",
            \"payload_off\": \"released\",
            \"availability_topic\": \"${MQTT_TOPIC_PREFIX}/${DEVICE_ID}/status\",
            \"device\": {
                \"identifiers\": [\"${DEVICE_ID}\"]
            }
        }" -r 2>&1 >> "$LOG_FILE"
    log "Published call button"
    
    # Publish online status
    mosquitto_pub -h "$MQTT_HOST" -p "$MQTT_PORT" -u "$MQTT_USER" -P "$MQTT_PASS" \
        -t "${MQTT_TOPIC_PREFIX}/${DEVICE_ID}/status" -m "online" -r 2>&1 >> "$LOG_FILE"
    
    log "Discovery configurations sent"
}

monitor() {
    log "MQTT client started for $DEVICE_ID. Waiting for events..."
    
    # Отправляем статус онлайн
    mosquitto_pub -h "$MQTT_HOST" -p "$MQTT_PORT" -u "$MQTT_USER" -P "$MQTT_PASS" \
        -t "${MQTT_TOPIC_PREFIX}/${DEVICE_ID}/status" -m "online" -r 2>&1 >> "$LOG_FILE"
    
    # Создаем FIFO для чтения событий от door_monitor
    FIFO="/tmp/mqtt_fifo"
    [ -p "$FIFO" ] || mkfifo "$FIFO"
    
    log "Listening for events via FIFO"
    
    # Читаем события из FIFO
    while true; do
        if read line < "$FIFO"; then
            log "Received event: $line"
            
            case "$line" in
                "DOOR:OPEN")
                    mosquitto_pub -h "$MQTT_HOST" -p "$MQTT_PORT" -u "$MQTT_USER" -P "$MQTT_PASS" \
                        -t "${MQTT_TOPIC_PREFIX}/${DEVICE_ID}/door" -m "open" 2>&1 >> "$LOG_FILE"
                    log "Published door open"
                    ;;
                "DOOR:CLOSED")
                    mosquitto_pub -h "$MQTT_HOST" -p "$MQTT_PORT" -u "$MQTT_USER" -P "$MQTT_PASS" \
                        -t "${MQTT_TOPIC_PREFIX}/${DEVICE_ID}/door" -m "closed" 2>&1 >> "$LOG_FILE"
                    log "Published door closed"
                    ;;
                KEY:*)
                    key=$(echo "$line" | cut -d: -f2)
                    mosquitto_pub -h "$MQTT_HOST" -p "$MQTT_PORT" -u "$MQTT_USER" -P "$MQTT_PASS" \
                        -t "${MQTT_TOPIC_PREFIX}/${DEVICE_ID}/rfid" -m "$key" 2>&1 >> "$LOG_FILE"
                    log "Published RFID key: $key"
                    ;;
                ACCESS:*)
                    status=$(echo "$line" | cut -d: -f2)
                    mosquitto_pub -h "$MQTT_HOST" -p "$MQTT_PORT" -u "$MQTT_USER" -P "$MQTT_PASS" \
                        -t "${MQTT_TOPIC_PREFIX}/${DEVICE_ID}/access" -m "$status" 2>&1 >> "$LOG_FILE"
                    log "Published access: $status"
                    ;;
                "BUTTON:EXIT")
                    mosquitto_pub -h "$MQTT_HOST" -p "$MQTT_PORT" -u "$MQTT_USER" -P "$MQTT_PASS" \
                        -t "${MQTT_TOPIC_PREFIX}/${DEVICE_ID}/button/exit" -m "pressed" 2>&1 >> "$LOG_FILE"
                    log "Published exit button"
                    ;;
                "BUTTON:CALL")
                    mosquitto_pub -h "$MQTT_HOST" -p "$MQTT_PORT" -u "$MQTT_USER" -P "$MQTT_PASS" \
                        -t "${MQTT_TOPIC_PREFIX}/${DEVICE_ID}/button/call" -m "pressed" 2>&1 >> "$LOG_FILE"
                    log "Published call button"
                    ;;
                RELAY:*)
                    state=$(echo "$line" | cut -d: -f2)
                    mosquitto_pub -h "$MQTT_HOST" -p "$MQTT_PORT" -u "$MQTT_USER" -P "$MQTT_PASS" \
                        -t "${MQTT_TOPIC_PREFIX}/${DEVICE_ID}/relay" -m "$state" 2>&1 >> "$LOG_FILE"
                    log "Published relay: $state"
                    ;;
            esac
        fi
        sleep 0.1
    done
}

# Слушаем команды из MQTT для управления реле
listen_commands() {
    log "Listening for MQTT commands"
    
    while true; do
        # Слушаем команды для реле
        mosquitto_sub -h "$MQTT_HOST" -p "$MQTT_PORT" -u "$MQTT_USER" -P "$MQTT_PASS" \
            -t "${MQTT_TOPIC_PREFIX}/${DEVICE_ID}/relay/set" -W 1 2>/dev/null | while read cmd; do
            log "Relay command received: $cmd"
            
            # Отправляем команду в ESP через UART
            if [ -c /dev/ttyS0 ]; then
                echo "RELAY:$cmd" > /dev/ttyS0 2>&1
                log "Sent RELAY:$cmd to ESP via ttyS0"
            elif [ -c /dev/ttyAMA0 ]; then
                echo "RELAY:$cmd" > /dev/ttyAMA0 2>&1
                log "Sent RELAY:$cmd to ESP via ttyAMA0"
            fi
            
            # Обновляем состояние в MQTT
            mosquitto_pub -h "$MQTT_HOST" -p "$MQTT_PORT" -u "$MQTT_USER" -P "$MQTT_PASS" \
                -t "${MQTT_TOPIC_PREFIX}/${DEVICE_ID}/relay" -m "$cmd" -r 2>&1 >> "$LOG_FILE"
        done
        sleep 1
    done
}

case "$1" in
    "discovery")
        send_discovery
        ;;
    "monitor")
        monitor &
        listen_commands
        ;;
    "restart")
        killall mqtt_client.sh 2>/dev/null
        sleep 1
        /usr/bin/mqtt_client.sh monitor > /dev/null 2>&1 &
        log "MQTT client restarted"
        ;;
    *)
        echo "Usage: $0 {discovery|monitor|restart}"
        ;;
esac
