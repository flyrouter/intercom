#!/bin/sh
# Функция для декодирования URL
urldecode() {
    echo -e "$(echo "$1" | sed 's/+/ /g;s/%/\\x/g')"
}

# Функция логирования
log_event() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - BACKUP - $1" >> /var/log/door_monitor.log
}

# Функция проверки и монтирования устройства
mount_device() {
    device=$1
    mount_point="/mnt/$(basename $device)"
    
    if mount | grep -q "$mount_point"; then
        echo "$mount_point"
        return 0
    fi
    
    mkdir -p "$mount_point"
    
    if blkid "$device" | grep -q "vfat"; then
        mount -t vfat "$device" "$mount_point" 2>/dev/null
    elif blkid "$device" | grep -q "ext[234]"; then
        mount -t ext4 "$device" "$mount_point" 2>/dev/null
    else
        mount "$device" "$mount_point" 2>/dev/null
    fi
    
    if [ $? -eq 0 ]; then
        echo "$mount_point"
        return 0
    else
        echo ""
        return 1
    fi
}

# Получаем действие
action=$(echo "$QUERY_STRING" | sed -n 's/.*action=\([^&]*\).*/\1/p')

# Обработка скачивания - должна быть первой
if [ "$action" = "download_backup" ]; then
    storage=$(echo "$QUERY_STRING" | sed -n 's/.*storage=\([^&]*\).*/\1/p')
    storage=$(urldecode "$storage")
    file=$(echo "$QUERY_STRING" | sed -n 's/.*file=\([^&]*\).*/\1/p')
    
    if [ -z "$storage" ] || [ -z "$file" ]; then
        echo "Status: 400 Bad Request"
        echo "Content-type: text/plain"
        echo ""
        echo "Missing parameters"
        exit 1
    fi
    
    if [ "$storage" = "internal" ]; then
        BACKUP_DIR="/root/backups"
    else
        mount_point="/mnt/$(basename $storage)"
        BACKUP_DIR="${mount_point}/backups"
    fi
    
    BACKUP_FILE="${BACKUP_DIR}/${file}"
    
    if [ ! -f "$BACKUP_FILE" ]; then
        echo "Status: 404 Not Found"
        echo "Content-type: text/plain"
        echo ""
        echo "Backup file not found"
        exit 1
    fi
    
    echo "Content-type: application/octet-stream"
    echo "Content-Disposition: attachment; filename=\"$file\""
    echo "Content-Transfer-Encoding: binary"
    echo "Cache-Control: no-cache"
    echo "Pragma: no-cache"
    echo "Content-length: $(stat -c%s "$BACKUP_FILE" 2>/dev/null || stat -f%z "$BACKUP_FILE" 2>/dev/null)"
    echo ""
    cat "$BACKUP_FILE"
    exit 0
fi

# Для всех остальных действий возвращаем JSON
echo "Content-type: application/json"
echo ""

case "$action" in
    "scan_storage")
        devices=""
        first=true
        
        # Внутренняя память
        ROOT_FREE=$(df -h / | tail -1 | awk '{print $4}')
        ROOT_TOTAL=$(df -h / | tail -1 | awk '{print $2}')
        devices="${devices}{\"path\":\"internal\",\"name\":\"Internal Storage\",\"mount\":\"/root/backups\",\"free\":\"${ROOT_FREE}\",\"total\":\"${ROOT_TOTAL}\",\"icon\":\"📁\",\"available\":true}"
        first=false
        
        # SD-карта
        if [ -e /dev/mmcblk0p1 ]; then
            if blkid /dev/mmcblk0p1 >/dev/null 2>&1; then
                LABEL=$(blkid /dev/mmcblk0p1 | sed -n 's/.*LABEL="\([^"]*\)".*/\1/p')
                NAME="SD Card${LABEL:+ ($LABEL)}"
                mount_point=$(mount_device "/dev/mmcblk0p1")
                if [ -n "$mount_point" ]; then
                    FREE=$(df -h "$mount_point" | tail -1 | awk '{print $4}')
                    TOTAL=$(df -h "$mount_point" | tail -1 | awk '{print $2}')
                    devices="${devices},{\"path\":\"/dev/mmcblk0p1\",\"name\":\"${NAME}\",\"mount\":\"$mount_point\",\"free\":\"${FREE}\",\"total\":\"${TOTAL}\",\"icon\":\"💾\",\"available\":true}"
                else
                    devices="${devices},{\"path\":\"/dev/mmcblk0p1\",\"name\":\"SD Card\",\"mount\":\"\",\"free\":\"0\",\"total\":\"0\",\"icon\":\"💾\",\"available\":false,\"error\":\"Mount failed\"}"
                fi
            else
                devices="${devices},{\"path\":\"/dev/mmcblk0p1\",\"name\":\"SD Card\",\"mount\":\"\",\"free\":\"0\",\"total\":\"0\",\"icon\":\"💾\",\"available\":false,\"error\":\"No filesystem\"}"
            fi
        else
            devices="${devices},{\"path\":\"sdcard\",\"name\":\"SD Card\",\"mount\":\"\",\"free\":\"0\",\"total\":\"0\",\"icon\":\"💾\",\"available\":false,\"error\":\"Not detected\"}"
        fi
        
        # USB устройства
        usb_found=false
        for usb in /dev/sd*[0-9]; do
            if [ -e "$usb" ] && [ -b "$usb" ]; then
                if blkid "$usb" >/dev/null 2>&1; then
                    LABEL=$(blkid "$usb" | sed -n 's/.*LABEL="\([^"]*\)".*/\1/p')
                    NAME="USB Flash${LABEL:+ ($LABEL)}"
                    mount_point=$(mount_device "$usb")
                    if [ -n "$mount_point" ]; then
                        FREE=$(df -h "$mount_point" | tail -1 | awk '{print $4}')
                        TOTAL=$(df -h "$mount_point" | tail -1 | awk '{print $2}')
                        devices="${devices},{\"path\":\"$usb\",\"name\":\"${NAME}\",\"mount\":\"$mount_point\",\"free\":\"${FREE}\",\"total\":\"${TOTAL}\",\"icon\":\"💿\",\"available\":true}"
                        usb_found=true
                    fi
                fi
            fi
        done
        
        if [ "$usb_found" = false ]; then
            devices="${devices},{\"path\":\"usb\",\"name\":\"USB Flash Drive\",\"mount\":\"\",\"free\":\"0\",\"total\":\"0\",\"icon\":\"💿\",\"available\":false,\"error\":\"Not detected\"}"
        fi
        
        echo "{\"status\":\"success\",\"devices\":[$devices]}"
        ;;
        
    "create_backup")
        storage=$(echo "$QUERY_STRING" | sed -n 's/.*storage=\([^&]*\).*/\1/p')
        storage=$(urldecode "$storage")
        components=$(echo "$QUERY_STRING" | sed -n 's/.*components=\([^&]*\).*/\1/p')
        
        if [ -z "$storage" ]; then
            echo '{"status": "error", "message": "Не выбрано место для бэкапа"}'
            exit 1
        fi
        
        if [ "$storage" = "internal" ]; then
            BACKUP_DIR="/root/backups"
            mkdir -p "${BACKUP_DIR}"
        else
            if [ ! -e "$storage" ]; then
                echo "{\"status\": \"error\", \"message\": \"Устройство $storage не найдено\"}"
                exit 1
            fi
            mount_point=$(mount_device "$storage")
            if [ -z "$mount_point" ]; then
                echo "{\"status\": \"error\", \"message\": \"Не удалось примонтировать устройство $storage\"}"
                exit 1
            fi
            BACKUP_DIR="${mount_point}/backups"
            mkdir -p "${BACKUP_DIR}"
        fi
        
        # Проверяем свободное место
        df_cmd=$(df -k "$(dirname ${BACKUP_DIR})" | tail -1)
        FREE_SPACE=$(echo "$df_cmd" | awk '{print $4}')
        if [ "$FREE_SPACE" -lt 1024 ]; then
            echo '{"status": "error", "message": "Мало места на устройстве"}'
            exit 1
        fi
        
        DATE=$(date '+%Y%m%d_%H%M%S')
        BACKUP_NAME="doorphone_backup_${DATE}"
        TEMP_DIR="/tmp/${BACKUP_NAME}"
        
        mkdir -p "${TEMP_DIR}"
        
        # Создаем структуру папок
        mkdir -p "${TEMP_DIR}/www/cgi-bin/p"
        mkdir -p "${TEMP_DIR}/etc/baresip"
        mkdir -p "${TEMP_DIR}/usr/bin"
        mkdir -p "${TEMP_DIR}/etc/init.d"
        
        # Копируем выбранные компоненты
        if echo "$components" | grep -q "cgi"; then
            cp -r /var/www/cgi-bin/p/*.cgi "${TEMP_DIR}/www/cgi-bin/p/" 2>/dev/null
        fi
        
        if echo "$components" | grep -q "baresip"; then
            [ -f /etc/baresip/accounts ] && cp /etc/baresip/accounts "${TEMP_DIR}/etc/baresip/" 2>/dev/null
            [ -f /etc/baresip/call_number ] && cp /etc/baresip/call_number "${TEMP_DIR}/etc/baresip/" 2>/dev/null
        fi
        
        if echo "$components" | grep -q "keys"; then
            [ -f /etc/door_keys.conf ] && cp /etc/door_keys.conf "${TEMP_DIR}/" 2>/dev/null
        fi
        
        if echo "$components" | grep -q "scripts"; then
            [ -f /usr/bin/door_monitor.sh ] && cp /usr/bin/door_monitor.sh "${TEMP_DIR}/usr/bin/" 2>/dev/null
            [ -f /usr/bin/start_baresip.sh ] && cp /usr/bin/start_baresip.sh "${TEMP_DIR}/usr/bin/" 2>/dev/null
        fi
        
        if echo "$components" | grep -q "init"; then
            [ -f /etc/init.d/S99door ] && cp /etc/init.d/S99door "${TEMP_DIR}/etc/init.d/" 2>/dev/null
        fi
        
        if echo "$components" | grep -q "majestic"; then
            [ -f /etc/majestic.yaml ] && cp /etc/majestic.yaml "${TEMP_DIR}/etc/" 2>/dev/null
        fi
        
        if echo "$components" | grep -q "uart"; then
            [ -f /etc/rc.local ] && cp /etc/rc.local "${TEMP_DIR}/etc/" 2>/dev/null
            stty -F /dev/ttyS0 -a 2>/dev/null > "${TEMP_DIR}/uart_settings.txt"
            stty -F /dev/ttyAMA0 -a 2>/dev/null >> "${TEMP_DIR}/uart_settings.txt"
        fi
        
        # Информация о бэкапе
        {
            echo "Backup created: $(date)"
            echo "Camera: $(hostname)"
            echo "IP: $(ip addr show | grep -o '192\.168\.[0-9]*\.[0-9]*' | head -1)"
            echo "Storage: $storage"
            echo "Components: $components"
        } > "${TEMP_DIR}/backup_info.txt"
        
        # Создаем архив
        cd /tmp
        tar -cf "${BACKUP_DIR}/${BACKUP_NAME}.tar" "${BACKUP_NAME}/" 2>/tmp/tar_error
        TAR_RESULT=$?
        
        if [ $TAR_RESULT -ne 0 ] || [ ! -f "${BACKUP_DIR}/${BACKUP_NAME}.tar" ]; then
            ERROR_MSG=$(cat /tmp/tar_error 2>/dev/null)
            echo "{\"status\": \"error\", \"message\": \"Не удалось создать архив: $ERROR_MSG\"}"
            rm -rf "${TEMP_DIR}"
            exit 1
        fi
        
        if command -v gzip >/dev/null 2>&1; then
            gzip -f "${BACKUP_DIR}/${BACKUP_NAME}.tar"
            BACKUP_FILE="${BACKUP_NAME}.tar.gz"
        else
            BACKUP_FILE="${BACKUP_NAME}.tar"
        fi
        
        rm -rf "${TEMP_DIR}"
        
        cd "${BACKUP_DIR}"
        ls -t doorphone_backup_* 2>/dev/null | tail -n +11 | xargs -r rm
        
        if [ -f "${BACKUP_DIR}/${BACKUP_FILE}" ]; then
            SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_FILE}" | cut -f1)
            COUNT=$(ls -1 ${BACKUP_DIR}/doorphone_backup_* ${BACKUP_DIR}/uploaded_backup_* 2>/dev/null | wc -l)
            
            log_event "Бэкап создан: ${BACKUP_FILE} (${SIZE}) на ${storage}"
            
            echo "{\"status\": \"success\", \"message\": \"Бэкап создан\", \"file\": \"${BACKUP_FILE}\", \"size\": \"${SIZE}\", \"total\": ${COUNT}}"
        else
            echo "{\"status\": \"error\", \"message\": \"Не удалось создать архив\"}"
        fi
        ;;
        
    "list_backups")
        storage=$(echo "$QUERY_STRING" | sed -n 's/.*storage=\([^&]*\).*/\1/p')
        storage=$(urldecode "$storage")
        
        if [ -z "$storage" ]; then
            echo '{"status": "error", "message": "Не указано место хранения"}'
            exit 1
        fi
        
        if [ "$storage" = "internal" ]; then
            BACKUP_DIR="/root/backups"
        else
            mount_point="/mnt/$(basename $storage)"
            BACKUP_DIR="${mount_point}/backups"
        fi
        
        mkdir -p "${BACKUP_DIR}" 2>/dev/null
        
        echo -n '{"status": "success", "backups": ['
        first=true
        cd "${BACKUP_DIR}" 2>/dev/null
        if [ $? -eq 0 ]; then
            # Показываем ВСЕ .tar и .tar.gz файлы
            ls -t *.tar *.tar.gz 2>/dev/null | while read file; do
                if [ -n "$file" ] && [ -f "$file" ]; then
                    if [ "$first" = true ]; then
                        first=false
                    else
                        echo -n ','
                    fi
                    size=$(du -h "$file" 2>/dev/null | cut -f1)
                    [ -z "$size" ] && size="0B"
                    
                    # Извлекаем дату из имени файла
                    if echo "$file" | grep -q "doorphone_backup_"; then
                        date=$(echo "$file" | sed 's/doorphone_backup_\(.*\)\.tar.*/\1/')
                    elif echo "$file" | grep -q "uploaded_backup_"; then
                        date=$(echo "$file" | sed 's/uploaded_backup_\(.*\)\.tar.*/\1/')
                    else
                        date=$(date -r "$file" '+%Y%m%d_%H%M%S' 2>/dev/null || echo "unknown")
                    fi
                    
                    echo -n "{\"file\":\"$file\",\"size\":\"$size\",\"date\":\"$date\"}"
                fi
            done
        fi
        echo ']}'
        ;;
        
    "upload_backup")
        # Проверяем, что это POST запрос
        if [ "$REQUEST_METHOD" != "POST" ]; then
            echo '{"status": "error", "message": "Метод не поддерживается"}'
            exit 1
        fi
        
        storage=$(echo "$QUERY_STRING" | sed -n 's/.*storage=\([^&]*\).*/\1/p')
        storage=$(urldecode "$storage")
        
        if [ -z "$storage" ]; then
            echo '{"status": "error", "message": "Не указано место хранения"}'
            exit 1
        fi
        
        # Определяем директорию для бэкапов
        if [ "$storage" = "internal" ]; then
            BACKUP_DIR="/root/backups"
        else
            mount_point="/mnt/$(basename $storage)"
            BACKUP_DIR="${mount_point}/backups"
        fi
        
        mkdir -p "${BACKUP_DIR}"
        
        # Генерируем имя для загруженного файла
        DATE=$(date '+%Y%m%d_%H%M%S')
        SAVED_FILE="${BACKUP_DIR}/uploaded_backup_${DATE}.tar"
        
        # Сохраняем POST данные напрямую в файл
        cat > "$SAVED_FILE"
        
        # Проверяем размер
        if [ -f "$SAVED_FILE" ]; then
            FILE_SIZE=$(stat -c%s "$SAVED_FILE" 2>/dev/null || stat -f%z "$SAVED_FILE" 2>/dev/null)
            if [ "$FILE_SIZE" -gt 0 ]; then
                SIZE=$(du -h "$SAVED_FILE" | cut -f1)
                log_event "Бэкап загружен: uploaded_backup_${DATE}.tar (${SIZE}) на ${storage}"
                echo "{\"status\": \"success\", \"message\": \"Файл загружен\", \"file\": \"uploaded_backup_${DATE}.tar\", \"size\": \"${SIZE}\"}"
            else
                rm -f "$SAVED_FILE"
                echo "{\"status\": \"error\", \"message\": \"Файл пустой\"}"
            fi
        else
            echo "{\"status\": \"error\", \"message\": \"Не удалось сохранить файл\"}"
        fi
        ;;
        
    "restore_backup")
        storage=$(echo "$QUERY_STRING" | sed -n 's/.*storage=\([^&]*\).*/\1/p')
        storage=$(urldecode "$storage")
        file=$(echo "$QUERY_STRING" | sed -n 's/.*file=\([^&]*\).*/\1/p')
        
        if [ -z "$storage" ] || [ -z "$file" ]; then
            echo '{"status": "error", "message": "Не указаны параметры"}'
            exit 1
        fi
        
        if [ "$storage" = "internal" ]; then
            BACKUP_DIR="/root/backups"
        else
            mount_point="/mnt/$(basename $storage)"
            BACKUP_DIR="${mount_point}/backups"
        fi
        
        if [ ! -f "${BACKUP_DIR}/${file}" ]; then
            echo '{"status": "error", "message": "Файл бэкапа не найден"}'
            exit 1
        fi
        
        TEMP_DIR="/tmp/restore_$$"
        mkdir -p "${TEMP_DIR}"
        
        case "$file" in
            *.tar.gz)
                tar -xzf "${BACKUP_DIR}/${file}" -C "${TEMP_DIR}" 2>/tmp/untar_error
                ;;
            *.tar)
                tar -xf "${BACKUP_DIR}/${file}" -C "${TEMP_DIR}" 2>/tmp/untar_error
                ;;
            *)
                echo '{"status": "error", "message": "Неподдерживаемый формат архива"}'
                rm -rf "${TEMP_DIR}"
                exit 1
                ;;
        esac
        
        if [ $? -ne 0 ]; then
            ERROR_MSG=$(cat /tmp/untar_error 2>/dev/null)
            echo "{\"status\": \"error\", \"message\": \"Ошибка распаковки: $ERROR_MSG\"}"
            rm -rf "${TEMP_DIR}"
            exit 1
        fi
        
        # Ищем распакованную директорию
        EXTRACTED_DIR=$(find "${TEMP_DIR}" -type d | grep -v "^${TEMP_DIR}$" | head -1)
        
        if [ -z "$EXTRACTED_DIR" ]; then
            EXTRACTED_DIR="$TEMP_DIR"
        fi
        
        cd "$EXTRACTED_DIR"
        
        # Восстанавливаем файлы
        if [ -d "www/cgi-bin/p" ]; then
            cp -rf www/cgi-bin/p/*.cgi /var/www/cgi-bin/p/ 2>/dev/null
            chmod +x /var/www/cgi-bin/p/*.cgi 2>/dev/null
        fi
        
        if [ -d "etc/baresip" ]; then
            cp -rf etc/baresip/* /etc/baresip/ 2>/dev/null
        fi
        
        if [ -f "door_keys.conf" ]; then
            cp -f door_keys.conf /etc/door_keys.conf
            chmod 666 /etc/door_keys.conf
        fi
        
        if [ -d "usr/bin" ]; then
            cp -rf usr/bin/* /usr/bin/ 2>/dev/null
            chmod +x /usr/bin/*.sh 2>/dev/null
        fi
        
        if [ -d "etc/init.d" ]; then
            cp -rf etc/init.d/* /etc/init.d/ 2>/dev/null
            chmod +x /etc/init.d/S99door 2>/dev/null
        fi
        
        if [ -f "etc/majestic.yaml" ]; then
            cp -f etc/majestic.yaml /etc/majestic.yaml 2>/dev/null
        fi
        
        if [ -f "etc/rc.local" ]; then
            cp -f etc/rc.local /etc/rc.local 2>/dev/null
            chmod +x /etc/rc.local
        fi
        
        rm -rf "${TEMP_DIR}"
        
        log_event "Восстановлен бэкап: ${file} с ${storage}"
        
        echo '{"status": "success", "message": "Бэкап восстановлен. Рекомендуется перезагрузить камеру."}'
        ;;
        
    "delete_backup")
        storage=$(echo "$QUERY_STRING" | sed -n 's/.*storage=\([^&]*\).*/\1/p')
        storage=$(urldecode "$storage")
        file=$(echo "$QUERY_STRING" | sed -n 's/.*file=\([^&]*\).*/\1/p')
        
        if [ -z "$storage" ] || [ -z "$file" ]; then
            echo '{"status": "error", "message": "Не указаны параметры"}'
            exit 1
        fi
        
        if [ "$storage" = "internal" ]; then
            BACKUP_DIR="/root/backups"
        else
            mount_point="/mnt/$(basename $storage)"
            BACKUP_DIR="${mount_point}/backups"
        fi
        
        if [ -f "${BACKUP_DIR}/${file}" ]; then
            rm -f "${BACKUP_DIR}/${file}"
            log_event "Удален бэкап: ${file} с ${storage}"
            echo '{"status": "success", "message": "Бэкап удален"}'
        else
            echo '{"status": "error", "message": "Файл не найден"}'
        fi
        ;;
        
    *)
        echo '{"status": "error", "message": "Неизвестное действие"}'
        ;;
esac
