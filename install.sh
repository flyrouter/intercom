#!/bin/sh
#===============================================================================
# OpenIPC Doorphone Installer v2.3
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
echo "${BLUE}  OpenIPC Doorphone Installer v2.3${NC}"
echo "${BLUE}  with MQTT, Telegram, Sound Support${NC}"
echo "${BLUE}  & Fixed Menu Integration${NC}"
echo "${BLUE}==========================================${NC}"
echo ""

# Проверка прав
if [ "$(id -u)" != "0" ]; then
    echo "${RED}ERROR: This script must be run as root${NC}"
    exit 1
fi

#-----------------------------------------------------------------------------
# Функция для скачивания (ОПРЕДЕЛЯЕМ ДО ИСПОЛЬЗОВАНИЯ!)
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

BASE_URL="https://raw.githubusercontent.com/OpenIPC/intercom/main"

#-----------------------------------------------------------------------------
# Step 1: Определение UART
#-----------------------------------------------------------------------------
echo "${BLUE}Step 1: Detecting UART ports...${NC}"

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
# Step 2: Создание директорий
#-----------------------------------------------------------------------------
echo "${BLUE}Step 2: Creating directories...${NC}"
mkdir -p /var/www/cgi-bin/p
mkdir -p /var/www/a
mkdir -p /usr/share/sounds/doorphone
mkdir -p /root/backups
mkdir -p /etc/baresip
mkdir -p /etc/webui
echo "${GREEN}  ✓ Directories created${NC}"
echo ""

#-----------------------------------------------------------------------------
# Step 3: Сохраняем оригинальный header.cgi
#-----------------------------------------------------------------------------
echo "${BLUE}Step 3: Backing up original header.cgi...${NC}"
if [ -f /var/www/cgi-bin/header.cgi ]; then
    cp /var/www/cgi-bin/header.cgi /var/www/cgi-bin/header.cgi.original
    echo "${GREEN}  ✓ Original header.cgi backed up${NC}"
fi
echo ""

#-----------------------------------------------------------------------------
# Step 4: Настройка UART в rc.local
#-----------------------------------------------------------------------------
echo "${BLUE}Step 4: Configuring UART in rc.local...${NC}"

if [ ! -f /etc/rc.local ]; then
    echo "#!/bin/sh" > /etc/rc.local
    echo "exit 0" >> /etc/rc.local
    chmod +x /etc/rc.local
fi

if ! grep -q "stty -F $UART_SELECTED" /etc/rc.local; then
    sed -i "/exit 0/i stty -F $UART_SELECTED 115200 cs8 -cstopb -parenb raw" /etc/rc.local
fi

if ! grep -q "mqtt_client.sh" /etc/rc.local; then
    cat >> /etc/rc.local << 'EOF'
# Start MQTT client
if [ -f /etc/mqtt.conf ]; then
    . /etc/mqtt.conf
    if [ "$MQTT_ENABLED" = "true" ]; then
        /usr/bin/mqtt_client.sh monitor > /dev/null 2>&1 &
    fi
fi
exit 0
EOF
fi

chmod +x /etc/rc.local
echo "${GREEN}  ✓ UART and services configured${NC}"
echo ""

#-----------------------------------------------------------------------------
# Step 5: Скачивание файлов с GitHub
#-----------------------------------------------------------------------------
echo "${BLUE}Step 5: Downloading files from GitHub...${NC}"

# Счетчики
TOTAL=0
SUCCESS=0
FAILED=""

#-----------------------------------------------------------------------------
# Скачивание header.cgi (ТЕПЕРЬ ФУНКЦИЯ УЖЕ ОПРЕДЕЛЕНА!)
#-----------------------------------------------------------------------------
echo "  - Downloading header.cgi with full menu..."
TOTAL=$((TOTAL + 1))

if download_file "$BASE_URL/www/cgi-bin/header.cgi" "/var/www/cgi-bin/header.cgi" "header.cgi"; then
    chmod +x "/var/www/cgi-bin/header.cgi"
    SUCCESS=$((SUCCESS + 1))
    echo "    ${GREEN}  ✓ header.cgi downloaded from repository${NC}"
else
    echo "    ${YELLOW}  ⚠️ header.cgi not found in repository, creating custom menu...${NC}"
    
    # Создаем кастомный header.cgi с полным меню
    cat > /var/www/cgi-bin/header.cgi << 'EOF'
#!/usr/bin/haserl
Content-type: text/html; charset=UTF-8
Cache-Control: no-store
Pragma: no-cache

<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title><% html_title %></title>
    <link rel="stylesheet" href="/a/bootstrap.min.css">
    <link rel="stylesheet" href="/a/bootstrap.override.css">
    <script src="/a/bootstrap.bundle.min.js"></script>
    <script src="/a/main.js"></script>
</head>

<body id="page-<%= $pagename %>" class="<%= $fw_variant %>">
    <nav class="navbar navbar-expand-lg bg-body-tertiary">
        <div class="container">
            <a class="navbar-brand" href="status.cgi">
                <img alt="OpenIPC logo" height="32" src="/a/logo.svg">
                <span class="x-small ms-1"><%= $fw_variant %></span>
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse justify-content-end" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle" href="#" data-bs-toggle="dropdown">Information</a>
                        <ul class="dropdown-menu">
                            <li><a class="dropdown-item" href="status.cgi">Status</a></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><a class="dropdown-item" href="info-majestic.cgi">Majestic</a></li>
                            <li><a class="dropdown-item" href="info-kernel.cgi">Kernel</a></li>
                            <li><a class="dropdown-item" href="info-overlay.cgi">Overlay</a></li>
                        </ul>
                    </li>
                    <li class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle" href="#" data-bs-toggle="dropdown">Majestic</a>
                        <ul class="dropdown-menu">
                            <li><a class="dropdown-item" href="mj-settings.cgi">Settings</a></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><a class="dropdown-item" href="mj-configuration.cgi">Configuration</a></li>
                            <li><a class="dropdown-item" href="mj-endpoints.cgi">Endpoints</a></li>
                        </ul>
                    </li>
                    <li class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle" href="#" data-bs-toggle="dropdown">Firmware</a>
                        <ul class="dropdown-menu">
                            <li><a class="dropdown-item" href="fw-network.cgi">Network</a></li>
                            <li><a class="dropdown-item" href="fw-time.cgi">Time</a></li>
                            <li><a class="dropdown-item" href="fw-interface.cgi">Interface</a></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><a class="dropdown-item" href="fw-update.cgi">Update</a></li>
                            <li><a class="dropdown-item" href="fw-settings.cgi">Settings</a></li>
                        </ul>
                    </li>
                    <li class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle" href="#" data-bs-toggle="dropdown">Tools</a>
                        <ul class="dropdown-menu">
                            <li><a class="dropdown-item" href="tool-console.cgi">Console</a></li>
                            <li><a class="dropdown-item" href="tool-files.cgi">Files</a></li>
                            <% if [ -e /dev/mmcblk0 ]; then %>
                                <li><a class="dropdown-item" href="tool-sdcard.cgi">SDcard</a></li>
                            <% fi %>
                        </ul>
                    </li>
                    <li class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle" href="#" data-bs-toggle="dropdown">Extensions</a>
                        <ul class="dropdown-menu dropdown-menu-lg-end">
                            <!-- OpenIPC Doorphone Pages -->
                            <li><a class="dropdown-item" href="/cgi-bin/p/door_keys.cgi">🔑 Door Phone</a></li>
                            <li><a class="dropdown-item" href="/cgi-bin/p/sip_manager.cgi">📞 SIP</a></li>
                            <li><a class="dropdown-item" href="/cgi-bin/p/qr_generator.cgi">🎯 QR Keys</a></li>
                            <li><a class="dropdown-item" href="/cgi-bin/p/temp_keys.cgi">⏱️ Temp Keys</a></li>
                            <li><a class="dropdown-item" href="/cgi-bin/p/sounds.cgi">🔊 Sounds</a></li>
                            <li><a class="dropdown-item" href="/cgi-bin/p/door_history.cgi">📋 History</a></li>
                            <li><a class="dropdown-item" href="/cgi-bin/p/mqtt.cgi">📡 MQTT</a></li>
                            <li><a class="dropdown-item" href="/cgi-bin/backup.cgi">💾 Backups</a></li>
                            <li><hr class="dropdown-divider"></li>
                            
                            <!-- Original Extensions -->
                            <li><a class="dropdown-item" href="ext-openwall.cgi">OpenWall</a></li>
                            <li><a class="dropdown-item" href="ext-telegram.cgi">Telegram</a></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><a class="dropdown-item" href="https://openipc.cloud">P2P network</a></li>
                            <li><a class="dropdown-item" href="ext-vtun.cgi">VTun</a></li>
                            <li><a class="dropdown-item" href="ext-wireguard.cgi">WireGuard</a></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><a class="dropdown-item" href="ext-proxy.cgi">Proxy</a></li>
                        </ul>
                    </li>
                    <li class="nav-item"><a class="nav-link" href="preview.cgi">Preview</a></li>
                </ul>
            </div>
        </div>
    </nav>

    <main class="pb-4">
        <div class="container" style="min-height: 85vh">
            <div class="row mt-1 x-small">
                <div class="col-lg-2">
                    <div id="pb-memory" class="progress my-1"><div class="progress-bar"></div></div>
                    <div id="pb-overlay" class="progress my-1"><div class="progress-bar"></div></div>
                </div>
                <div class="col-md-6 mb-2">
                    <%= $(signature) %>
                </div>
                <div class="col-1" id="daynight_value"></div>
                <div class="col-md-4 col-lg-3 mb-2 text-end">
                    <div id="time-now"></div>
                    <div class="text-secondary" id="soc-temp"></div>
                </div>
            </div>

<% if [ -z "$network_gateway" ]; then %>
<div class="alert alert-warning">
    <p class="mb-0">Internet connection not available, please <a href="fw-network.cgi">check your network settings</a>.</p>
</div>
<% fi %>

<% if [ "$network_macaddr" = "00:00:23:34:45:66" ] && [ -f /etc/shadow- ] && [ -n $(grep root /etc/shadow- | cut -d: -f2) ]; then %>
<div class="alert alert-danger">
    <%in p/address.cgi %>
</div>
<% fi %>

<% if [ ! -e $(get_config) ]; then %>
<div class="alert alert-danger">
    <p class="mb-0">Majestic configuration not found, please <a href="mj-configuration.cgi">check your Majestic settings</a>.</p>
</div>
<% fi %>

<% if [ "$(cat /etc/TZ)" != "$TZ" ] || [ -e /tmp/system-reboot ]; then %>
<div class="alert alert-danger">
    <h3>Warning.</h3>
    <p>System settings have been updated, restart to apply pending changes.</p>
    <span class="d-flex gap-3">
        <a class="btn btn-danger" href="fw-restart.cgi">Restart camera</a>
    </span>
</div>
<% fi %>

<h2><%= $page_title %></h2>
<% log_read %>
EOF
    chmod +x /var/www/cgi-bin/header.cgi
    SUCCESS=$((SUCCESS + 1))
    echo "    ${GREEN}  ✓ Custom header.cgi created with doorphone menu${NC}"
fi

# Проверяем наличие MQTT в меню
if grep -q "mqtt.cgi" /var/www/cgi-bin/header.cgi; then
    echo "    ${GREEN}  ✓ MQTT entry found in menu${NC}"
else
    echo "    ${RED}  ✗ MQTT entry missing in menu${NC}"
    # Добавляем MQTT в меню если его нет
    sed -i '/backup.cgi/i <li><a class="dropdown-item" href="/cgi-bin/p/mqtt.cgi">📡 MQTT</a></li>' /var/www/cgi-bin/header.cgi
    echo "    ${GREEN}  ✓ MQTT entry added to menu${NC}"
fi
echo ""

#-----------------------------------------------------------------------------
# Далее остальная часть скрипта (CGI, system scripts, configs, etc.)
#-----------------------------------------------------------------------------
# ... (остальной код как в предыдущей версии) ...
