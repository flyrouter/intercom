#!/bin/sh
echo "Content-type: text/plain"
echo ""

name=$(echo "$QUERY_STRING" | sed -n 's/.*name=\([^&]*\).*/\1/p')

if [ -f "/usr/share/sounds/doorphone/${name}.pcm" ]; then
    echo "/play ${name}.pcm" | nc 127.0.0.1 3000 2>/dev/null
    echo "Воспроизведение: $name"
else
    echo "Файл не найден: ${name}.pcm"
fi
