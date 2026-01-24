@echo off
chcp 65001 > nul
title Lazada Crawler Dashboard

echo ========================================
echo    LAZADA CRAWLER WEB DASHBOARD
echo ========================================
echo.

cd /d "%~dp0web"

echo 🚀 Starting web server...
echo 📊 Dashboard will be at: http://localhost:3000
echo.
echo ⚠️  To stop: Press Ctrl+C
echo ========================================
echo.

node server.js

pause
