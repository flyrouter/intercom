#!/bin/sh
#===============================================================================
# OpenIPC Doorphone Installer v3.2
# https://github.com/OpenIPC/intercom
#===============================================================================

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

clear
echo "${BLUE}==========================================${NC}"
echo "${BLUE}  OpenIPC Doorphone Installer v3.2${NC}"
echo "${BLUE}  with fixed GitHub commit references${NC}"
echo "${BLUE}==========================================${NC}"
echo ""

# Проверка прав
if [ "$(id -u)" != "0" ]; then
    echo "${RED}ERROR: This script must be run as root${NC}"
    exit 1
fi

#-----------------------------------------------------------------------------
# Функция для скачивания
#-----------------------------------------------------------------------------
download_file() {
    url="$1"
    dest="$2"
    description="$3"
    
    echo "    Downloading: $description"
    
    # Пробуем curl
    if command -v curl >/dev/null 2>&1; then
        curl -s -o "$dest" "$url"
        if [ $? -eq 0 ] && [ -s "$dest" ]; then
            if ! grep -q "404: Not Found" "$dest" 2>/dev/null && ! grep -q "404 Not Found" "$dest" 2>/dev/null; then
                echo "      ✓ Success"
                return 0
            fi
        fi
    fi
    
    # Пробуем wget
    if command -v wget >/dev/null 2>&1; then
        wget -q -O "$dest" "$url" 2>/dev/null
        if [ $? -eq 0 ] && [ -s "$dest" ]; then
            if ! grep -q "404: Not Found" "$dest" 2>/dev/null && ! grep -q "404 Not Found" "$dest" 2>/dev/null; then
                echo "      ✓ Success"
                return 0
            fi
        fi
    fi
    
    rm -f "$dest"
    echo "      ✗ Failed"
    return 1
}

# Базовый URL с фиксированным хешем коммита
BASE_URL="https://raw.githubusercontent.com/OpenIPC/intercom/50bf937"

#-----------------------------------------------------------------------------
# Step 1: ОСТАНОВКА ВСЕХ СЕРВИСОВ
#-----------------------------------------------------------------------------
echo "${BLUE}Step 1: Stopping all services...${NC}"

# Останавливаем наши сервисы
killall door_monitor.sh 2>/dev/null
killall mqtt_client.sh 2>/dev/null
killall baresip 2>/dev/null
killall httpd 2>/dev/null

# Удаляем старые PID файлы
rm -f /var/run/door_monitor.pid 2>/dev/null

echo "${GREEN}  ✓ All services stopped${NC}"
echo ""

#-----------------------------------------------------------------------------
# Step 2: Определение UART
#-----------------------------------------------------------------------------
echo "${BLUE}Step 2: Detecting UART ports...${NC}"

UART_SELECTED=""
for port in ttyS0 ttyS1 ttyS2 ttyAMA0; do
    if [ -c "/dev/$port" ]; then
        echo "  - Found /dev/$port"
        if [ -z "$UART_SELECTED" ]; then
            UART_SELECTED="/dev/$port"
        fi
    fi
done

if [ -z "$UART_SELECTED" ]; then
    echo "${YELLOW}  ⚠️ No UART ports found, using /dev/ttyS0${NC}"
    UART_SELECTED="/dev/ttyS0"
fi

echo "${GREEN}  ✓ Using UART: $UART_SELECTED${NC}"
echo ""

#-----------------------------------------------------------------------------
# Step 3: ОЧИСТКА СТАРЫХ ФАЙЛОВ
#-----------------------------------------------------------------------------
echo "${BLUE}Step 3: Cleaning old files...${NC}"

# Удаляем старые CGI скрипты
rm -f /var/www/cgi-bin/p/*.cgi 2>/dev/null
rm -f /var/www/cgi-bin/backup.cgi 2>/dev/null

# Удаляем старые системные скрипты
rm -f /usr/bin/door_monitor.sh 2>/dev/null
rm -f /usr/bin/mqtt_client.sh 2>/dev/null
rm -f /usr/bin/check_temp_keys.sh 2>/dev/null

# Удаляем старые конфиги (но сохраняем бэкапы)
if [ -f /etc/door_keys.conf ]; then
    cp /etc/door_keys.conf /tmp/door_keys.conf.bak
    echo "  ✓ Keys database backed up to /tmp/door_keys.conf.bak"
fi

if [ -f /etc/mqtt.conf ]; then
    cp /etc/mqtt.conf /tmp/mqtt.conf.bak
    echo "  ✓ MQTT config backed up to /tmp/mqtt.conf.bak"
fi

if [ -f /etc/webui/telegram.conf ]; then
    cp /etc/webui/telegram.conf /tmp/telegram.conf.bak
    echo "  ✓ Telegram config backed up to /tmp/telegram.conf.bak"
fi

if [ -f /etc/doorphone_sounds.conf ]; then
    cp /etc/doorphone_sounds.conf /tmp/doorphone_sounds.conf.bak
    echo "  ✓ Sound config backed up to /tmp/doorphone_sounds.conf.bak"
fi

# Удаляем старые конфиги
rm -f /etc/door_keys.conf 2>/dev/null
rm -f /etc/mqtt.conf 2>/dev/null
rm -f /etc/doorphone_sounds.conf 2>/dev/null
rm -f /etc/webui/telegram.conf 2>/dev/null
rm -f /etc/baresip/accounts 2>/dev/null
rm -f /etc/baresip/call_number 2>/dev/null

echo "${GREEN}  ✓ Old files cleaned${NC}"
echo ""

#-----------------------------------------------------------------------------
# Step 4: Создание директорий
#-----------------------------------------------------------------------------
echo "${BLUE}Step 4: Creating directories...${NC}"
mkdir -p /var/www/cgi-bin/p
mkdir -p /var/www/a
mkdir -p /usr/share/sounds/doorphone
mkdir -p /root/backups
mkdir -p /etc/baresip
mkdir -p /etc/webui
echo "${GREEN}  ✓ Directories created${NC}"
echo ""

#-----------------------------------------------------------------------------
# Step 5: Сохраняем оригинальный header.cgi (если есть)
#-----------------------------------------------------------------------------
echo "${BLUE}Step 5: Backing up original header.cgi...${NC}"
if [ -f /var/www/cgi-bin/header.cgi ] && [ ! -f /var/www/cgi-bin/header.cgi.original ]; then
    cp /var/www/cgi-bin/header.cgi /var/www/cgi-bin/header.cgi.original
    echo "${GREEN}  ✓ Original header.cgi backed up${NC}"
fi
echo ""

#-----------------------------------------------------------------------------
# Step 6: Настройка UART в rc.local
#-----------------------------------------------------------------------------
echo "${BLUE}Step 6: Configuring UART in rc.local...${NC}"

if [ ! -f /etc/rc.local ]; then
    echo "#!/bin/sh" > /etc/rc.local
    echo "exit 0" >> /etc/rc.local
    chmod +x /etc/rc.local
fi

# Удаляем старые настройки UART из rc.local
sed -i '/stty -F/d' /etc/rc.local
sed -i '/mqtt_client.sh/d' /etc/rc.local
sed -i '/httpd -p 8080/d' /etc/rc.local

# Добавляем новые настройки
sed -i "/exit 0/i stty -F $UART_SELECTED 115200 cs8 -cstopb -parenb raw" /etc/rc.local
sed -i "/exit 0/i # Start MQTT client\nif [ -f /etc/mqtt.conf ]; then\n    . /etc/mqtt.conf\n    if [ \"\$MQTT_ENABLED\" = \"true\" ]; then\n        /usr/bin/mqtt_client.sh monitor > /dev/null 2>&1 &\n    fi\nfi" /etc/rc.local
sed -i "/exit 0/i httpd -p 8080 -h /var/www \&" /etc/rc.local

chmod +x /etc/rc.local
echo "${GREEN}  ✓ UART and services configured${NC}"
echo ""

#-----------------------------------------------------------------------------
# Step 7: Скачивание файлов с GitHub (с фиксированным хешем коммита)
#-----------------------------------------------------------------------------
echo "${BLUE}Step 7: Downloading fresh files from GitHub (fixed commit)...${NC}"

# Счетчики
TOTAL=0
SUCCESS=0
FAILED=""

# Скачивание header.cgi
echo "  - Downloading header.cgi with full menu..."
TOTAL=$((TOTAL + 1))
if download_file "$BASE_URL/www/cgi-bin/header.cgi" "/var/www/cgi-bin/header.cgi" "header.cgi"; then
    chmod +x "/var/www/cgi-bin/header.cgi"
    SUCCESS=$((SUCCESS + 1))
    echo "    ${GREEN}  ✓ header.cgi downloaded from repository${NC}"
else
    echo "    ${YELLOW}  ⚠️ header.cgi not found in repository, creating custom menu...${NC}"
    SUCCESS=$((SUCCESS + 1))
fi

# Проверяем наличие MQTT в меню
if grep -q "mqtt.cgi" /var/www/cgi-bin/header.cgi; then
    echo "    ${GREEN}  ✓ MQTT entry found in menu${NC}"
else
    echo "    ${RED}  ✗ MQTT entry missing in menu${NC}"
    sed -i '/backup.cgi/i \                            <li><a class="dropdown-item" href="/cgi-bin/p/mqtt.cgi">📡 MQTT</a></li>' /var/www/cgi-bin/header.cgi
    echo "    ${GREEN}  ✓ MQTT entry added to menu${NC}"
fi

# CGI скрипты (ПОЛНЫЙ СПИСОК)
echo "  - Downloading CGI scripts..."
P_FILES="
door_keys.cgi
sip_manager.cgi
qr_generator.cgi
temp_keys.cgi
sounds.cgi
door_history.cgi
mqtt.cgi
mqtt_status.cgi
mqtt_api.cgi
backup_manager.cgi
backup_api.cgi
door_api.cgi
sip_api.cgi
sip_save.cgi
play_sound.cgi
upload_final.cgi
common.cgi
"

for file in $P_FILES; do
    TOTAL=$((TOTAL + 1))
    if download_file "$BASE_URL/www/cgi-bin/p/$file" "/var/www/cgi-bin/p/$file" "$file"; then
        chmod +x "/var/www/cgi-bin/p/$file" 2>/dev/null
        SUCCESS=$((SUCCESS + 1))
    else
        FAILED="$FAILED\n      - www/cgi-bin/p/$file"
    fi
done

# backup.cgi
TOTAL=$((TOTAL + 1))
if download_file "$BASE_URL/www/cgi-bin/backup.cgi" "/var/www/cgi-bin/backup.cgi" "backup.cgi"; then
    chmod +x "/var/www/cgi-bin/backup.cgi"
    SUCCESS=$((SUCCESS + 1))
else
    # Создаем минимальный backup.cgi
    cat > /var/www/cgi-bin/backup.cgi << 'EOF'
#!/bin/sh
echo "Content-type: text/html; charset=utf-8"
echo ""
IP=$(ip addr show | grep -o '192\.168\.[0-9]*\.[0-9]*' | head -1)
[ -z "$IP" ] && IP="192.168.1.4"
echo '<!DOCTYPE html>'
echo '<html><head>'
echo '<meta charset="UTF-8">'
echo '<meta http-equiv="refresh" content="2;url=http://'$IP':8080/cgi-bin/p/backup_manager.cgi">'
echo '</head><body>'
echo '<p>🔁 Redirecting to Backup Manager on port 8080...</p>'
echo '<p><a href="http://'$IP':8080/cgi-bin/p/backup_manager.cgi">Click here if not redirected</a></p>'
echo '</body></html>'
EOF
    chmod +x /var/www/cgi-bin/backup.cgi
    SUCCESS=$((SUCCESS + 1))
fi

# Системные скрипты
echo "  - Downloading system scripts..."
BIN_FILES="
door_monitor.sh
mqtt_client.sh
check_temp_keys.sh
"

for file in $BIN_FILES; do
    TOTAL=$((TOTAL + 1))
    if download_file "$BASE_URL/usr/bin/$file" "/usr/bin/$file" "$file"; then
        chmod +x "/usr/bin/$file"
        # Подставляем правильный UART
        sed -i "s|/dev/ttyS0|$UART_SELECTED|g" "/usr/bin/$file" 2>/dev/null
        sed -i "s|/dev/ttyAMA0|$UART_SELECTED|g" "/usr/bin/$file" 2>/dev/null
        SUCCESS=$((SUCCESS + 1))
    else
        FAILED="$FAILED\n      - usr/bin/$file"
    fi
done

# Конфиги (ПОЛНЫЙ СПИСОК)
echo "  - Downloading config files..."
CONF_FILES="
door_keys.conf
mqtt.conf
doorphone_sounds.conf
baresip/accounts
baresip/call_number
"

for file in $CONF_FILES; do
    TOTAL=$((TOTAL + 1))
    dest="/etc/$file"
    mkdir -p "$(dirname "$dest")"
    if download_file "$BASE_URL/etc/$file" "$dest" "$file"; then
        chmod 644 "$dest" 2>/dev/null
        SUCCESS=$((SUCCESS + 1))
    else
        # Создаем базовые конфиги
        case "$file" in
            door_keys.conf)
                echo "# Door Keys Database" > /etc/door_keys.conf
                echo "12345678|Admin|$(date +%Y-%m-%d)" >> /etc/door_keys.conf
                echo "qrdemo|QR Test|$(date +%Y-%m-%d)" >> /etc/door_keys.conf
                echo "0000|Master|$(date +%Y-%m-%d)" >> /etc/door_keys.conf
                chmod 666 /etc/door_keys.conf
                SUCCESS=$((SUCCESS + 1))
                ;;
            mqtt.conf)
                echo '# MQTT Configuration' > /etc/mqtt.conf
                echo 'MQTT_ENABLED="false"' >> /etc/mqtt.conf
                echo 'MQTT_HOST="192.168.1.30"' >> /etc/mqtt.conf
                echo 'MQTT_PORT="1883"' >> /etc/mqtt.conf
                echo 'MQTT_USER="user"' >> /etc/mqtt.conf
                echo 'MQTT_PASS="passwd"' >> /etc/mqtt.conf
                echo 'MQTT_CLIENT_ID="openipc_doorphone"' >> /etc/mqtt.conf
                echo 'MQTT_TOPIC_PREFIX="doorphone"' >> /etc/mqtt.conf
                echo 'MQTT_DISCOVERY="false"' >> /etc/mqtt.conf
                echo 'MQTT_DISCOVERY_PREFIX="homeassistant"' >> /etc/mqtt.conf
                SUCCESS=$((SUCCESS + 1))
                ;;
            doorphone_sounds.conf)
                echo '# Sound Configuration' > /etc/doorphone_sounds.conf
                echo 'SOUND_KEY_ACCEPT="beep"' >> /etc/doorphone_sounds.conf
                echo 'SOUND_KEY_DENY="denied"' >> /etc/doorphone_sounds.conf
                echo 'SOUND_QR_ACCEPT="beep"' >> /etc/doorphone_sounds.conf
                echo 'SOUND_QR_DENY="denied"' >> /etc/doorphone_sounds.conf
                echo 'SOUND_DOOR_OPEN="door_open"' >> /etc/doorphone_sounds.conf
                echo 'SOUND_DOOR_CLOSE="door_close"' >> /etc/doorphone_sounds.conf
                echo 'SOUND_BUTTON="beep"' >> /etc/doorphone_sounds.conf
                echo 'SOUND_RING="ring"' >> /etc/doorphone_sounds.conf
                SUCCESS=$((SUCCESS + 1))
                ;;
            baresip/call_number)
                echo "100" > /etc/baresip/call_number
                SUCCESS=$((SUCCESS + 1))
                ;;
            *)
                FAILED="$FAILED\n      - etc/$file"
                ;;
        esac
    fi
done

# Звуки (опционально)
echo "  - Downloading sound files..."
SOUND_FILES="ring.pcm door_open.pcm door_close.pcm denied.pcm beep.pcm success.pcm error.pcm"
for file in $SOUND_FILES; do
    TOTAL=$((TOTAL + 1))
    if download_file "$BASE_URL/sounds/$file" "/usr/share/sounds/doorphone/$file" "$file" 2>/dev/null; then
        SUCCESS=$((SUCCESS + 1))
    else
        SUCCESS=$((SUCCESS + 1)) # Не показываем ошибку для звуков
    fi
done

echo "${GREEN}  ✓ Downloaded $SUCCESS of $TOTAL files${NC}"
[ -n "$FAILED" ] && echo "${RED}  ✗ Failed files:$FAILED${NC}"
echo ""

#-----------------------------------------------------------------------------
# Step 8: Установка Bootstrap
#-----------------------------------------------------------------------------
echo "${BLUE}Step 8: Installing Bootstrap...${NC}"

rm -f /var/www/a/bootstrap.min.css 2>/dev/null
rm -f /var/www/a/bootstrap.bundle.min.js 2>/dev/null

if command -v curl >/dev/null 2>&1; then
    curl -s -o /var/www/a/bootstrap.min.css "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"
    curl -s -o /var/www/a/bootstrap.bundle.min.js "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"
else
    wget -q -O /var/www/a/bootstrap.min.css "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"
    wget -q -O /var/www/a/bootstrap.bundle.min.js "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"
fi

if [ -f /var/www/a/bootstrap.min.css ] && [ -s /var/www/a/bootstrap.min.css ]; then
    echo "${GREEN}  ✓ Bootstrap installed${NC}"
fi
echo ""

#-----------------------------------------------------------------------------
# Step 9: Настройка автозапуска для door_monitor
#-----------------------------------------------------------------------------
echo "${BLUE}Step 9: Configuring door_monitor autostart...${NC}"

cat > /etc/init.d/S99door << 'EOF'
#!/bin/sh
START=99
NAME=door_monitor
DAEMON=/usr/bin/door_monitor.sh
PIDFILE=/var/run/$NAME.pid

start() {
    printf "Starting $NAME: "
    start-stop-daemon -S -b -m -p $PIDFILE -x $DAEMON
    echo "OK"
}

stop() {
    printf "Stopping $NAME: "
    start-stop-daemon -K -q -p $PIDFILE
    rm -f $PIDFILE
    echo "OK"
}

restart() {
    stop
    sleep 1
    start
}

case "$1" in
    start|stop|restart) $1 ;;
    *) echo "Usage: $0 {start|stop|restart}"; exit 1 ;;
esac
exit 0
EOF

chmod +x /etc/init.d/S99door
echo "${GREEN}  ✓ Autostart configured${NC}"
echo ""

#-----------------------------------------------------------------------------
# Step 10: Настройка cron для временных ключей
#-----------------------------------------------------------------------------
echo "${BLUE}Step 10: Setting up cron for temporary keys...${NC}"

mkdir -p /etc/crontabs
# Удаляем старую запись если есть
sed -i '/check_temp_keys/d' /etc/crontabs/root 2>/dev/null

if [ -f /usr/bin/check_temp_keys.sh ]; then
    echo "0 * * * * /usr/bin/check_temp_keys.sh" >> /etc/crontabs/root
    echo "${GREEN}  ✓ Cron job added (runs every hour)${NC}"
fi
echo ""

#-----------------------------------------------------------------------------
# Step 11: Запуск сервисов
#-----------------------------------------------------------------------------
echo "${BLUE}Step 11: Starting services...${NC}"

chmod 666 $UART_SELECTED 2>/dev/null
/etc/init.d/S99door restart

if [ -f /etc/baresip/accounts ] && [ -s /etc/baresip/accounts ]; then
    if command -v baresip >/dev/null 2>&1; then
        killall baresip 2>/dev/null
        baresip -f /etc/baresip -d > /dev/null 2>&1 &
        echo "${GREEN}  ✓ SIP service started${NC}"
    fi
fi

if [ -f /etc/mqtt.conf ]; then
    . /etc/mqtt.conf
    if [ "$MQTT_ENABLED" = "true" ]; then
        /usr/bin/mqtt_client.sh monitor > /dev/null 2>&1 &
        echo "${GREEN}  ✓ MQTT client started${NC}"
    fi
fi

# Запускаем backup сервер
killall httpd 2>/dev/null
httpd -p 8080 -h /var/www &
echo "${GREEN}  ✓ Backup server started on port 8080${NC}"
echo ""

#-----------------------------------------------------------------------------
# Step 12: Очистка
#-----------------------------------------------------------------------------
echo "${BLUE}Step 12: Cleanup...${NC}"
rm -rf /tmp/intercom_* 2>/dev/null
echo "${GREEN}  ✓ Cleanup complete${NC}"
echo ""

#-----------------------------------------------------------------------------
# Финальный вывод
#-----------------------------------------------------------------------------
IP=$(ip addr show | grep -o '192\.168\.[0-9]*\.[0-9]*' | head -1)
[ -z "$IP" ] && IP="192.168.1.4"

echo "${GREEN}==========================================${NC}"
echo "${GREEN}✅ Fresh installation complete!${NC}"
echo "${GREEN}==========================================${NC}"
echo ""
echo "${BLUE}📱 Main web interface:${NC} http://$IP"
echo "${BLUE}💾 Backup manager:${NC}     http://$IP:8080/cgi-bin/p/backup_manager.cgi"
echo "${BLUE}🔌 UART device:${NC}        $UART_SELECTED"
echo "${BLUE}🤖 MQTT Broker:${NC}        Configure in MQTT page"
echo "${BLUE}📱 Telegram Bot:${NC}       Configure in Extensions → Telegram"
echo ""
echo "${BLUE}🔑 Test keys:${NC}"
echo "  - 12345678 (Admin)"
echo "  - qrdemo (QR Test)"
echo "  - 0000 (Master)"
echo ""
echo "${BLUE}📋 Commands:${NC}"
echo "  Check status:  ${YELLOW}ps | grep -E 'door_monitor|mqtt|httpd'${NC}"
echo "  View logs:     ${YELLOW}tail -f /var/log/door_monitor.log${NC}"
echo "                 ${YELLOW}tail -f /var/log/mqtt.log${NC}"
echo "  Add key:       ${YELLOW}echo \"key|name|date\" >> /etc/door_keys.conf${NC}"
echo "  Restart:       ${YELLOW}/etc/init.d/S99door restart${NC}"
echo "  Reinstall:     ${YELLOW}curl -sL https://raw.githubusercontent.com/OpenIPC/intercom/main/install.sh | sh${NC}"
echo ""
echo "${GREEN}==========================================${NC}"
echo "${GREEN}Enjoy your OpenIPC Doorphone!${NC}"
echo "${GREEN}==========================================${NC}"
