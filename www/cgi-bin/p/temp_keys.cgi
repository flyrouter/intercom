#!/bin/sh
echo "Content-type: text/html; charset=utf-8"
echo ""

cat << 'EOFH'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Временные ключи</title>
    <link rel="stylesheet" href="/a/bootstrap.min.css">
    <style>
        body { padding: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; }
        .card { background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .btn { padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        .btn-primary { background: #1976d2; color: white; }
        input { width: 100%; padding: 8px; margin: 5px 0; border: 1px solid #ddd; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>⏱️ Временные ключи</h1>
        
        <div class="card">
            <h3>Создать временный ключ</h3>
            <input type="text" id="keyValue" placeholder="Номер ключа">
            <input type="text" id="ownerName" placeholder="Имя владельца">
            <input type="number" id="hours" placeholder="Срок действия (часов)" value="24">
            <button class="btn btn-primary" onclick="createTempKey()">Создать</button>
        </div>
    </div>

    <script>
        function createTempKey() {
            const key = document.getElementById('keyValue').value;
            const owner = document.getElementById('ownerName').value;
            const hours = parseInt(document.getElementById('hours').value);
            
            if (!key || !owner) return alert('Заполните поля');
            
            const expiry = Math.floor(Date.now()/1000) + hours * 3600;
            
            fetch('/cgi-bin/p/door_api.cgi', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: 'action=add_key&key=' + encodeURIComponent(key) + '&owner=' + encodeURIComponent(owner) + '&expiry=' + expiry
            })
            .then(r => r.json())
            .then(data => alert(data.message));
        }
    </script>
</body>
</html>
EOFH
