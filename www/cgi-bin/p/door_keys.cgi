#!/bin/sh
echo "Content-type: text/html; charset=utf-8"
echo ""

cat << 'EOFH'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Управление ключами</title>
    <link rel="stylesheet" href="/a/bootstrap.min.css">
</head>
<body>
    <div class="container mt-4">
        <h1>🔑 Управление ключами</h1>
        
        <div class="card mb-4">
            <div class="card-header">Статус</div>
            <div class="card-body">
                <div id="status">Загрузка...</div>
            </div>
        </div>
        
        <div class="card mb-4">
            <div class="card-header">Ключи</div>
            <div class="card-body">
                <div id="keys">Загрузка...</div>
            </div>
        </div>
    </div>
    
    <script>
        fetch('/cgi-bin/p/door_api.cgi?action=get_status')
            .then(r => r.json())
            .then(data => {
                document.getElementById('status').innerHTML = 
                    'ESP: ' + data.esp + '<br>Ключей: ' + data.keys;
            });
            
        fetch('/cgi-bin/p/door_api.cgi?action=list_keys')
            .then(r => r.json())
            .then(data => {
                let html = '<ul>';
                if (data.keys && data.keys.length > 0) {
                    data.keys.forEach(item => {
                        html += '<li>' + item.key + ' - ' + (item.owner || '') + ' (' + (item.date || '') + ')</li>';
                    });
                } else {
                    html += '<li>Нет ключей</li>';
                }
                html += '</ul>';
                document.getElementById('keys').innerHTML = html;
            });
    </script>
</body>
</html>
EOFH
