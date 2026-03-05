#!/bin/sh
echo "Content-type: text/plain"
echo ""
echo "CGI works!"
echo "REQUEST_METHOD: $REQUEST_METHOD"
env | sort
