@echo off
chcp 65001 >nul
if exist ".venv\Scripts\activate.bat" (
    echo [EV CHARGING] Dang kich hoat moi truong .venv...
    call .\.venv\Scripts\activate.bat
    cmd /k
) else (
    echo [ERROR] Chua tim thay thu muc .venv!
    echo Vui long chay script setup_env.bat truoc de khoi tao moi truong.
    pause
)

