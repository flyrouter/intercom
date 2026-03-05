#!/bin/sh
echo "Content-type: text/plain"
echo ""

echo "=== ENVIRONMENT ==="
env | sort
echo "=== ==="

if [ "$REQUEST_METHOD" = "POST" ]; then
    echo "=== POST DATA ==="
    # Читаем данные
    dd bs=1 count=1024 2>/dev/null | hexdump -C
    echo "=== END POST DATA ==="
else
    echo "Not a POST request"
fi
