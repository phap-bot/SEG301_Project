@echo off
REM CellphoneS Crawler - Double-click để chạy
REM ==========================================

echo.
echo ========================================
echo   CellphoneS Crawler
echo ========================================
echo.

REM Kiểm tra xem node_modules đã được install chưa
if not exist "node_modules\" (
    echo [!] Chua cai dat dependencies...
    echo [*] Dang cai dat npm packages...
    echo.
    call npm install
    echo.
)

echo [*] Bat dau crawl...
echo.

REM Chạy crawler
call node crawl_cellphones.js

echo.
echo ========================================
echo   Hoan thanh!
echo ========================================
echo.
echo Output files: output\cellphones_*.jsonl
echo.

pause
