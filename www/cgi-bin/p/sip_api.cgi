#!/bin/sh
echo "Content-type: application/json"
echo ""

urldecode() {
    echo -e "$(echo "$1" | sed 's/+/ /g;s/%/\\x/g')"
}

action=$(echo "$QUERY_STRING" | sed -n 's/.*action=\([^&]*\).*/\1/p')

case "$action" in
    "get_sip_status")
        if pgrep -f "baresip" > /dev/null; then
            echo '{"status": "running"}'
        else
            echo '{"status": "stopped"}'
        fi
        ;;
        
    "save_sip_get")
        user=$(echo "$QUERY_STRING" | sed -n 's/.*user=\([^&]*\).*/\1/p')
        server=$(echo "$QUERY_STRING" | sed -n 's/.*server=\([^&]*\).*/\1/p')
        pass=$(echo "$QUERY_STRING" | sed -n 's/.*pass=\([^&]*\).*/\1/p')
        
        if [ -n "$user" ] && [ -n "$server" ] && [ -n "$pass" ]; then
            ACCOUNT="<sip:$user@$server>;auth_pass=$pass;regint=60"
            mkdir -p /etc/baresip
            echo "# SIP account" > /etc/baresip/accounts
            echo "$ACCOUNT" >> /etc/baresip/accounts
            
            # Перезапускаем baresip
            killall baresip 2>/dev/null
            sleep 1
            if [ -f /usr/bin/baresip ]; then
                /usr/bin/baresip -f /etc/baresip -d > /dev/null 2>&1 &
            fi
            
            echo '{"status": "success", "message": "SIP настройки сохранены"}'
        else
            echo '{"status": "error", "message": "Не все поля заполнены"}'
        fi
        ;;
        
    "save_call_number")
        number=$(echo "$QUERY_STRING" | sed -n 's/.*number=\([^&]*\).*/\1/p')
        if [ -n "$number" ]; then
            number=$(urldecode "$number")
            echo "$number" > /etc/baresip/call_number
            echo "{\"status\": \"success\", \"message\": \"Номер сохранен\"}"
        else
            echo "{\"status\": \"error\", \"message\": \"Нет номера\"}"
        fi
        ;;
        
    "restart_sip")
        killall baresip 2>/dev/null
        sleep 1
        if [ -f /usr/bin/baresip ]; then
            /usr/bin/baresip -f /etc/baresip -d > /dev/null 2>&1 &
        fi
        echo '{"status": "success", "message": "SIP перезапущен"}'
        ;;
        
    *)
        echo "{\"status\": \"error\", \"message\": \"Неизвестное действие: $action\"}"
        ;;
esac
