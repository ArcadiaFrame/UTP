@echo off
rem Windows: double-click to open the UTP app. Keep this window open while you use it; close it to stop.
title UTP
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 ( py -3 utp\app\launch.py %* & goto :eof )
where python >nul 2>nul
if %errorlevel%==0 ( python utp\app\launch.py %* & goto :eof )
echo UTP needs Python 3. Install it from https://www.python.org/downloads/ (tick "Add python.exe to PATH"),
echo then double-click Start UTP again.
pause
