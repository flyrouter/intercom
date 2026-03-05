#!/bin/sh
echo "Content-type: text/plain"
echo ""

echo "REQUEST_METHOD: $REQUEST_METHOD"
echo "CONTENT_LENGTH: '$CONTENT_LENGTH'"
echo "QUERY_STRING: $QUERY_STRING"
echo "---"

if [ "$REQUEST_METHOD" = "POST" ]; then
    echo "Reading POST data (reading until EOF)..."
    
    # Сохраняем всё из stdin во временный файл
    TEMP_FILE="/tmp/test_upload_$$.tmp"
    cat > "$TEMP_FILE"
    
    FILE_SIZE=$(stat -c%s "$TEMP_FILE" 2>/dev/null || stat -f%z "$TEMP_FILE" 2>/dev/null)
    echo "--- Received $FILE_SIZE bytes ---"
    
    if [ "$FILE_SIZE" -gt 0 ]; then
        echo "--- First 200 bytes as hex ---"
        head -c 200 "$TEMP_FILE" | hexdump -C
        
        echo "--- First 10 lines as text ---"
        head -10 "$TEMP_FILE" | cat -A
    else
        echo "--- FILE IS EMPTY! ---"
    fi
    
    rm -f "$TEMP_FILE"
    echo "--- Done"
else
    echo "Not a POST request"
fi
