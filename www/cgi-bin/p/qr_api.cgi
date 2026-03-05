#!/bin/sh
echo "Content-type: application/json"
echo ""

urldecode() {
    echo -e "$(echo "$1" | sed 's/+/ /g;s/%/\\x/g')"
}

action=$(echo "$QUERY_STRING" | sed -n 's/.*action=\([^&]*\).*/\1/p')
key=$(echo "$QUERY_STRING" | sed -n 's/.*key=\([^&]*\).*/\1/p')
owner=$(echo "$QUERY_STRING" | sed -n 's/.*owner=\([^&]*\).*/\1/p')

if [ -n "$key" ]; then
    key=$(urldecode "$key")
fi
if [ -n "$owner" ]; then
    owner=$(urldecode "$owner")
fi

if [ "$action" = "add_key" ] && [ -n "$key" ] && [ -n "$owner" ]; then
    echo "$key|$owner|$(date '+%Y-%m-%d')" >> /etc/door_keys.conf
    echo '{"status": "success", "message": "QR-ключ добавлен"}'
else
    echo '{"status": "error", "message": "Неверные параметры"}'
fi
