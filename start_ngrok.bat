@echo off
echo Starting Ngrok tunnel for Proxy Scan...
echo.
echo Make sure your Flask app is running on port 5000 first!
echo.
ngrok http 5000
pause
