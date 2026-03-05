#!/bin/sh
echo "Content-type: text/html; charset=utf-8"
echo ""

cat << 'EOFH'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Звуковые эффекты</title>
    <link rel="stylesheet" href="/a/bootstrap.min.css">
    <style>
        body { padding: 20px; background: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; }
        .card { background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .btn { padding: 10px 20px; margin: 5px; border: none; border-radius: 4px; cursor: pointer; }
        .btn-primary { background: #1976d2; color: white; }
        .btn-success { background: #4caf50; color: white; }
        .btn-danger { background: #f44336; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔊 Звуковые эффекты</h1>
        
        <div class="card text-center">
            <button class="btn btn-primary" onclick="playSound('ring')">🔔 Звонок</button>
            <button class="btn btn-success" onclick="playSound('door_open')">🚪 Открытие</button>
            <button class="btn btn-danger" onclick="playSound('denied')">❌ Отказ</button>
        </div>
        <div id="result" class="mt-3"></div>
    </div>

    <script>
        function playSound(name) {
            fetch('/cgi-bin/p/play_sound.cgi?name=' + name)
                .then(r => r.text())
                .then(data => {
                    document.getElementById('result').innerHTML = 
                        '<div class="alert alert-info">' + data + '</div>';
                });
        }
    </script>
</body>
</html>
EOFH
