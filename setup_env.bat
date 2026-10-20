@echo off
chcp 65001 >nul
echo ==============================================================================
echo [EV CHARGING ANALYTICS] KHOI TAO VA THIET LAP MOI TRUONG AO .VENV
echo ==============================================================================
echo.

REM Kiem tra Python
where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set PYTHON_CMD=py
) else (
    where python >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        set PYTHON_CMD=python
    ) else (
        echo [ERROR] Khong tim thay Python tren he thong! Vui long cai dat Python 3.10 tro len.
        pause
        exit /b 1
    )
)

echo [1/4] Kiem tra moi truong ao .venv...
if not exist ".venv\Scripts\python.exe" (
    echo     -> Dang tao moi truong ao tai .venv bang lenh: %PYTHON_CMD% -m venv .venv
    %PYTHON_CMD% -m venv .venv
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Tao moi truong ao that bai!
        pause
        exit /b 1
    )
    echo     -> Da tao thanh cong .venv!
) else (
    echo     -> Moi truong ao .venv da ton tai san.
)

echo.
echo [2/4] Nang cap pip trong .venv...
.\.venv\Scripts\python.exe -m pip install --upgrade pip

echo.
echo [3/4] Cai dat cac thu vien phu thuoc tu requirements.txt...
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Cai dat thu vien that bai! Vui long kiem tra lai ket noi mang.
    pause
    exit /b 1
)

echo.
echo [4/4] Dang ky Jupyter Kernel cho .venv...
.\.venv\Scripts\python.exe -m ipykernel install --user --name=ev_charging_ba --display-name="Python (.venv - BA Project)"

echo.
echo ==============================================================================
echo [HOAN TAT] Moi truong .venv da duoc thiet lap thanh cong va tach biet hoan toan!
echo.
echo Cach kich hoat moi truong de su dung:
echo   - Command Prompt (cmd) : .\.venv\Scripts\activate.bat  (hoac chay activate_env.bat)
echo   - PowerShell (ps1)     : .\.venv\Scripts\Activate.ps1
echo.
echo Cach khoi dong Jupyter Lab/Notebook:
echo   - jupyter lab   (hoac jupyter notebook)
echo ==============================================================================
pause

