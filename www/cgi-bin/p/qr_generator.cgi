#!/bin/sh
echo "Content-type: text/html; charset=utf-8"
echo ""

cat << 'EOFH'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Генератор QR-кодов</title>
    <link rel="stylesheet" href="/a/bootstrap.min.css">
    <script src="https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.min.js"></script>
    <style>
        body { padding: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; }
        .card { background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .btn { padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        .btn-primary { background: #1976d2; color: white; }
        .btn-success { background: #4caf50; color: white; }
        input { width: 100%; padding: 8px; margin: 5px 0; border: 1px solid #ddd; border-radius: 4px; }
        #qrContainer { text-align: center; padding: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 Генератор QR-кодов</h1>
        
        <div class="card">
            <h3>Создать QR-ключ</h3>
            <input type="text" id="keyValue" placeholder="Номер ключа">
            <input type="text" id="ownerName" placeholder="Имя владельца">
            <button class="btn btn-primary" onclick="generateQR()">Сгенерировать QR</button>
            <button class="btn btn-success" onclick="saveKey()">Сохранить ключ</button>
        </div>
        
        <div class="card" id="qrCard" style="display: none;">
            <div id="qrContainer"></div>
        </div>
    </div>

    <script>
        let currentQR = null;
        
        function generateQR() {
            const key = document.getElementById('keyValue').value;
            if (!key) return alert('Введите ключ');
            
            const qr = qrcode(0, 'M');
            qr.addData(key);
            qr.make();
            
            document.getElementById('qrContainer').innerHTML = qr.createSvgTag({cellSize:8});
            document.getElementById('qrCard').style.display = 'block';
            currentQR = qr;
        }
        
        function saveKey() {
            const key = document.getElementById('keyValue').value;
            const owner = document.getElementById('ownerName').value || 'Unknown';
            
            fetch('/cgi-bin/p/qr_api.cgi?action=add_key&key=' + encodeURIComponent(key) + '&owner=' + encodeURIComponent(owner))
                .then(r => r.json())
                .then(data => alert(data.message));
        }
    </script>
</body>
</html>
EOFH
