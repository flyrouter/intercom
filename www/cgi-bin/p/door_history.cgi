#!/bin/sh
echo "Content-type: text/html; charset=utf-8"
echo ""

cat << 'EOFH'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>История событий</title>
    <link rel="stylesheet" href="/a/bootstrap.min.css">
    <style>
        body { background: #f5f5f5; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .card { background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .log { background: #1e1e1e; color: #00ff00; padding: 15px; border-radius: 4px; font-family: monospace; font-size: 12px; max-height: 600px; overflow-y: auto; white-space: pre-wrap; }
        .btn { padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        .btn-primary { background: #1976d2; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📋 История событий</h1>
        
        <div class="card">
            <div id="historyLog" class="log">Загрузка...</div>
            <div class="mt-2">
                <button class="btn btn-primary" onclick="refreshHistory()">🔄 Обновить</button>
            </div>
        </div>
    </div>

    <script>
        function loadHistory() {
            fetch('/cgi-bin/p/door_api.cgi?action=get_history&lines=100')
                .then(r => r.json())
                .then(data => {
                    const log = document.getElementById('historyLog');
                    if (!data.events || data.events.length === 0) {
                        log.textContent = 'Нет событий';
                        return;
                    }
                    log.innerHTML = data.events.map(e => e.msg).join('\n');
                });
        }
        
        function refreshHistory() {
            location.reload();
        }
        
        loadHistory();
        setInterval(loadHistory, 5000);
    </script>
</body>
</html>
EOFH
