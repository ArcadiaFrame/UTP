@echo off
rem Windows: double-click to open the UTP app on Vulcan.
title UTP: Vulcan
set "REPO=%~dp0.."
where py >nul 2>nul
if %errorlevel%==0 ( py -3 "%REPO%\utp\app\launch.py" --language vulcan %* & goto :eof )
python "%REPO%\utp\app\launch.py" --language vulcan %*
