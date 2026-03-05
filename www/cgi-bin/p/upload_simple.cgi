#!/bin/sh
echo "Content-type: text/html; charset=utf-8"
echo ""

# Получаем параметры
storage=$(echo "$QUERY_STRING" | sed -n 's/.*storage=\([^&]*\).*/\1/p')

# Декодируем URL если нужно
urldecode() {
    echo -e "$(echo "$1" | sed 's/+/ /g;s/%/\\x/g')"
}
storage=$(urldecode "$storage")

# Определяем директорию для сохранения
if [ "$storage" = "internal" ]; then
    BACKUP_DIR="/root/backups"
else
    mount_point="/mnt/$(basename $storage)"
    BACKUP_DIR="${mount_point}/backups"
fi

mkdir -p "$BACKUP_DIR" 2>/dev/null

# Создаем HTML ответ
cat << EOF
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Загрузка файла</title>
    <style>
        body { font-family: sans-serif; padding: 20px; }
        .success { color: green; }
        .error { color: red; }
    </style>
</head>
<body>
    <h1>Результат загрузки</h1>
