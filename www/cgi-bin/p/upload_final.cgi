#!/bin/sh
echo "Content-type: application/json"
echo ""

# Функция логирования
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> /tmp/upload_debug.log
}

log "=== UPLOAD START ==="
log "REQUEST_METHOD: $REQUEST_METHOD"
log "CONTENT_LENGTH: $CONTENT_LENGTH"

# Получаем storage из QUERY_STRING
storage=$(echo "$QUERY_STRING" | sed -n 's/.*storage=\([^&]*\).*/\1/p')

if [ "$REQUEST_METHOD" != "POST" ]; then
    log "ERROR: Not POST"
    echo '{"status": "error", "message": "Method not allowed"}'
    exit 1
fi

if [ -z "$storage" ]; then
    storage="/dev/mmcblk0p1"
fi

# Определяем директорию
if [ "$storage" = "internal" ]; then
    BACKUP_DIR="/root/backups"
else
    # Извлекаем устройство
    device=$(echo "$storage" | sed 's/[^a-zA-Z0-9/]//g')
    if [ -b "$device" ]; then
        mount_point="/mnt/$(basename $device)"
        mkdir -p "$mount_point"
        mount "$device" "$mount_point" 2>/dev/null
        BACKUP_DIR="${mount_point}/backups"
    else
        BACKUP_DIR="/mnt/mmcblk0p1/backups"
    fi
fi

mkdir -p "$BACKUP_DIR" 2>/dev/null
log "BACKUP_DIR: $BACKUP_DIR"

# Сохраняем входящие данные
TEMP_FILE="/tmp/upload_$$.tmp"
cat > "$TEMP_FILE"
BYTES=$(stat -c%s "$TEMP_FILE" 2>/dev/null)
log "Received $BYTES bytes"

if [ "$BYTES" -eq 0 ]; then
    echo '{"status": "error", "message": "Empty file"}'
    rm -f "$TEMP_FILE"
    exit 1
fi

# Ищем сигнатуру gzip (1f 8b)
SIGNATURE_OFFSET=$(hexdump -C "$TEMP_FILE" | grep -n "1f 8b" | head -1 | cut -d: -f1)

if [ -n "$SIGNATURE_OFFSET" ]; then
    # Вычисляем смещение (каждая строка = 16 байт + смещение в строке)
    BYTE_OFFSET=$(( ($SIGNATURE_OFFSET - 1) * 16 + 2 ))
    log "Found gzip at offset $BYTE_OFFSET"
    
    # Извлекаем gzip
    DATE=$(date '+%Y%m%d_%H%M%S')
    FINAL_FILE="${BACKUP_DIR}/doorphone_backup_${DATE}.tar.gz"
    
    dd if="$TEMP_FILE" bs=1 skip=$BYTE_OFFSET 2>/dev/null > "$FINAL_FILE"
    
    if [ -s "$FINAL_FILE" ]; then
        SIZE=$(du -h "$FINAL_FILE" | cut -f1)
        log "SUCCESS: Saved $SIZE"
        echo "{\"status\": \"success\", \"message\": \"Файл загружен\", \"file\": \"$(basename $FINAL_FILE)\", \"size\": \"$SIZE\"}"
    else
        echo '{"status": "error", "message": "Failed to save file"}'
        rm -f "$FINAL_FILE"
    fi
else
    # Если не нашли gzip, просто сохраняем как есть
    DATE=$(date '+%Y%m%d_%H%M%S')
    FINAL_FILE="${BACKUP_DIR}/uploaded_backup_${DATE}.bin"
    mv "$TEMP_FILE" "$FINAL_FILE"
    SIZE=$(du -h "$FINAL_FILE" | cut -f1)
    log "Saved as raw: $SIZE"
    echo "{\"status\": \"success\", \"message\": \"Файл загружен (raw)\", \"file\": \"$(basename $FINAL_FILE)\", \"size\": \"$SIZE\"}"
    exit 0
fi

rm -f "$TEMP_FILE"
log "=== UPLOAD END ==="
