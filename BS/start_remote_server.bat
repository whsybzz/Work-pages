@echo off
setlocal
cd /d "%~dp0"
set "PCB_BS_ALLOWED_ORIGINS=https://whsybzz.github.io"
python server.py --remote --host 127.0.0.1 --port 8766
pause
