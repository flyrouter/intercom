#!/bin/sh
echo "Content-type: text/plain"
echo ""

echo "=== DEBUG INFO ==="
echo "REQUEST_METHOD: $REQUEST_METHOD"
echo "CONTENT_LENGTH: $CONTENT_LENGTH"
echo "QUERY_STRING: $QUERY_STRING"
echo ""

echo "=== RAW POST DATA (first 1000 bytes) ==="
dd bs=1 count=1000 2>/dev/null | hexdump -C
echo ""
echo "=== END ==="
