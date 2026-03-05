#!/bin/sh
echo "Content-type: text/plain"
echo ""

echo "=== HTTPD Test ==="
echo "REQUEST_METHOD: $REQUEST_METHOD"
echo "CONTENT_LENGTH: $CONTENT_LENGTH"
echo "QUERY_STRING: $QUERY_STRING"
echo ""

if [ "$REQUEST_METHOD" = "POST" ]; then
    echo "=== POST DATA ==="
    dd bs=1 count=1024 2>/dev/null | hexdump -C
    echo "=== END ==="
else
    echo "Send POST request to test"
fi
