@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-docker.ps1" %*
endlocal
