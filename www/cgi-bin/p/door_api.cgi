#!/bin/sh
echo "Content-type: application/json; charset=utf-8"
echo ""

urldecode() {
    echo -e "$(echo "$1" | sed 's/+/ /g;s/%/\\x/g')"
}

json_escape() {
    echo "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

log_event() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> /var/log/door_monitor.log
}

action=$(echo "$QUERY_STRING" | sed -n 's/.*action=\([^&]*\).*/\1/p')

if [ "$REQUEST_METHOD" = "POST" ]; then
    read POST_STRING
    key=$(echo "$POST_STRING" | sed -n 's/.*key=\([^&]*\).*/\1/p')
    owner=$(echo "$POST_STRING" | sed -n 's/.*owner=\([^&]*\).*/\1/p')
    
    if [ -n "$key" ]; then
        key=$(urldecode "$key")
    fi
    if [ -n "$owner" ]; then
        owner=$(urldecode "$owner")
    fi
fi

case "$action" in
    "list_keys")
        echo -n '{"keys": ['
        if [ -f /etc/door_keys.conf ]; then
            first=true
            cat /etc/door_keys.conf | while IFS='|' read k o d; do
                if [ -n "$k" ]; then
                    if [ "$first" = true ]; then
                        first=false
                    else
                        echo -n ','
                    fi
                    k=$(json_escape "$k")
                    o=$(json_escape "$o")
                    d=$(json_escape "$d")
                    echo -n "{\"key\":\"$k\",\"owner\":\"$o\",\"date\":\"$d\"}"
                fi
            done
        fi
        echo ']}'
        ;;
        
    "add_key")
        if [ -n "$key" ]; then
            if [ -z "$owner" ]; then
                owner="Unknown"
            fi
            if grep -q "^$key|" /etc/door_keys.conf 2>/dev/null; then
                echo '{"status": "error", "message": "Ключ уже существует"}'
            else
                echo "$key|$owner|$(date '+%Y-%m-%d')" >> /etc/door_keys.conf
                log_event "KEY_ADDED - Ключ $key добавлен"
                echo '{"status": "success", "message": "Ключ добавлен"}'
            fi
        else
            echo '{"status": "error", "message": "Не указан ключ"}'
        fi
        ;;
        
    "remove_key")
        if [ -n "$key" ] && [ -f /etc/door_keys.conf ]; then
            grep -v "^$key|" /etc/door_keys.conf > /tmp/keys.tmp
            mv /tmp/keys.tmp /etc/door_keys.conf
            log_event "KEY_REMOVED - Ключ $key удален"
            echo '{"status": "success", "message": "Ключ удален"}'
        else
            echo '{"status": "error", "message": "Ключ не найден"}'
        fi
        ;;
        
    "open_door")
        if [ -c /dev/ttyS0 ] || [ -c /dev/ttyAMA0 ]; then
            echo "OPEN" > /dev/ttyS0 2>/dev/null || echo "OPEN" > /dev/ttyAMA0 2>/dev/null
            log_event "MANUAL_OPEN - Дверь открыта вручную"
            echo '{"status": "success", "message": "Дверь открыта"}'
        else
            echo '{"status": "error", "message": "ESP не подключен"}'
        fi
        ;;
        
    "get_status")
        esp_status="disconnected"
        if [ -c /dev/ttyS0 ] || [ -c /dev/ttyAMA0 ]; then
            esp_status="connected"
        fi
        
        keys_count=$(cat /etc/door_keys.conf 2>/dev/null | wc -l)
        echo "{\"esp\": \"$esp_status\", \"keys\": $keys_count}"
        ;;
        
    "get_history")
        lines=$(echo "$QUERY_STRING" | sed -n 's/.*lines=\([0-9]*\).*/\1/p')
        [ -z "$lines" ] && lines=50
        
        echo -n '{"events": ['
        if [ -f /var/log/door_monitor.log ]; then
            first=true
            tail -n $lines /var/log/door_monitor.log | while read line; do
                if [ -n "$line" ]; then
                    if [ "$first" = true ]; then
                        first=false
                    else
                        echo -n ','
                    fi
                    line=$(json_escape "$line")
                    echo -n "{\"msg\":\"$line\"}"
                fi
            done
        fi
        echo ']}'
        ;;
        
    *)
        echo '{"status": "error", "message": "Неизвестное действие"}'
        ;;
esac
