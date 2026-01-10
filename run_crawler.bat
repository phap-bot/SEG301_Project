@echo off
chcp 65001 > nul
echo ╔════════════════════════════════════════════════════════════╗
echo ║           AUTO-RESTART CRAWLER - WINDOWS                   ║
echo ║                                                            ║
echo ║  Press Ctrl+C to stop the crawler                         ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

:loop
echo ════════════════════════════════════════════════════════════
echo 🚀 Starting crawler...
echo ════════════════════════════════════════════════════════════
echo.

node index.js

if %ERRORLEVEL% EQU 0 (
  echo.
  echo ✅ Crawler exited normally
  echo 🔄 Auto-restarting in 3 seconds...
  echo.
  timeout /t 3 /nobreak > nul
  goto loop
) else (
  echo.
  echo ❌ Crawler exited with error code: %ERRORLEVEL%
  echo 🔄 Restarting in 5 seconds...
  echo.
  timeout /t 5 /nobreak > nul
  goto loop
)
