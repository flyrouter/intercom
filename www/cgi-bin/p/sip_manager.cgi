#!/bin/sh
echo "Content-type: text/html; charset=utf-8"
echo ""

if [ -f /etc/baresip/accounts ]; then
    ACCOUNT_LINE=$(grep -v "^#" /etc/baresip/accounts | head -1)
    SIP_USER=$(echo "$ACCOUNT_LINE" | sed -n 's/.*<sip:\([^@]*\)@.*/\1/p')
    SIP_SERVER=$(echo "$ACCOUNT_LINE" | sed -n 's/.*@\([^;>]*\).*/\1/p')
    SIP_PASS=$(echo "$ACCOUNT_LINE" | sed -n 's/.*auth_pass=\([^;]*\).*/\1/p')
fi

if [ -f /etc/baresip/call_number ]; then
    CALL_NUMBER=$(cat /etc/baresip/call_number)
else
    CALL_NUMBER="100"
fi

cat << EOF
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>SIP Настройки</title>
    <link rel="stylesheet" href="/a/bootstrap.min.css">
    <style>
        body { background: #f5f5f5; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .card { background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .btn { padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        .btn-primary { background: #1976d2; color: white; }
        .btn-success { background: #4caf50; color: white; }
        .btn-info { background: #17a2b8; color: white; }
        input, select { width: 100%; padding: 8px; margin: 5px 0; border: 1px solid #ddd; border-radius: 4px; }
        .status { padding: 10px; border-radius: 4px; margin-bottom: 10px; }
        .status.running { background: #d4edda; color: #155724; }
        .status.stopped { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📞 SIP Настройки</h1>
        
        <div class="card">
            <h3>Статус SIP</h3>
            <div id="sipStatus" class="status">Загрузка...</div>
            <button class="btn btn-info" onclick="checkStatus()">🔄 Проверить статус</button>
            <button class="btn btn-warning" onclick="restartSIP()">🔄 Перезапустить SIP</button>
        </div>
        
        <div class="card">
            <h3>SIP Аккаунт</h3>
            <div>
                <label>Пользователь:</label>
                <input type="text" id="sipUser" value="$SIP_USER">
            </div>
            <div>
                <label>Сервер:</label>
                <input type="text" id="sipServer" value="$SIP_SERVER">
            </div>
            <div>
                <label>Пароль:</label>
                <input type="password" id="sipPass" value="$SIP_PASS">
            </div>
            <button class="btn btn-success" onclick="saveSip()">💾 Сохранить SIP</button>
        </div>
        
        <div class="card">
            <h3>Номер вызова</h3>
            <div>
                <label>Номер для кнопки:</label>
                <input type="text" id="callNumber" value="$CALL_NUMBER">
            </div>
            <button class="btn btn-primary" onclick="saveCallNumber()">💾 Сохранить номер</button>
        </div>
    </div>

    <script>
        function checkStatus() {
            fetch('/cgi-bin/p/sip_api.cgi?action=get_sip_status')
                .then(r => r.json())
                .then(data => {
                    const statusDiv = document.getElementById('sipStatus');
                    statusDiv.className = 'status ' + data.status;
                    statusDiv.innerHTML = data.status === 'running' ? 
                        '✅ SIP работает' : '❌ SIP остановлен';
                });
        }
        
        function saveSip() {
            const user = document.getElementById('sipUser').value;
            const server = document.getElementById('sipServer').value;
            const pass = document.getElementById('sipPass').value;
            
            if (!user || !server || !pass) {
                alert('Заполните все поля');
                return;
            }
            
            // Используем GET вместо POST (надежнее работает в BusyBox)
            const url = '/cgi-bin/p/sip_api.cgi?action=save_sip_get&user=' + 
                        encodeURIComponent(user) + '&server=' + encodeURIComponent(server) + 
                        '&pass=' + encodeURIComponent(pass);
            
            fetch(url)
                .then(r => r.json())
                .then(data => {
                    alert(data.message);
                    if (data.status === 'success') setTimeout(checkStatus, 2000);
                })
                .catch(error => alert('Ошибка: ' + error));
        }
        
        function saveCallNumber() {
            const number = document.getElementById('callNumber').value;
            fetch('/cgi-bin/p/sip_api.cgi?action=save_call_number&number=' + encodeURIComponent(number))
                .then(r => r.json())
                .then(data => alert(data.message))
                .catch(error => alert('Ошибка: ' + error));
        }
        
        function restartSIP() {
            if (!confirm('Перезапустить SIP?')) return;
            fetch('/cgi-bin/p/sip_api.cgi?action=restart_sip', { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    alert(data.message);
                    setTimeout(checkStatus, 2000);
                })
                .catch(error => alert('Ошибка: ' + error));
        }
        
        checkStatus();
        setInterval(checkStatus, 10000);
    </script>
</body>
</html>