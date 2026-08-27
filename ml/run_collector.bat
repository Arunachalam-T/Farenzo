@echo off
REM Farenzo RedBus Data Collector - Auto Runner
REM This batch file is called by Windows Task Scheduler every 4 hours

cd /d "C:\Users\Arunachalam\OneDrive\Desktop\Farenzo\ml"

echo ============================================
echo Farenzo Price Tracker - %DATE% %TIME%
echo ============================================

python redbus_collector.py

echo.
echo Run complete at %TIME%
echo ============================================
