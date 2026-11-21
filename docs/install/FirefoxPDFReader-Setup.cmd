@echo off
rem Firefox PDF Reader setup for Windows: double-click to install.
rem Downloads and runs https://gregory-schwing-md-phd.github.io/firefox-pdf-reader/install/windows.ps1
title Firefox PDF Reader setup
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm 'https://gregory-schwing-md-phd.github.io/firefox-pdf-reader/install/windows.ps1' | iex"
echo.
pause
