# Setup script for PowerShell
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "[EV CHARGING ANALYTICS] KHOI TAO VA THIET LAP MOI TRUONG AO .VENV (PowerShell)" -ForegroundColor Cyan
Write-Host "==============================================================================" -ForegroundColor Cyan

# Kiem tra Python
$pyCmd = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    $pyCmd = "py"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pyCmd = "python"
} else {
    Write-Host "[ERROR] Khong tim thay Python tren he thong!" -ForegroundColor Red
    exit 1
}

Write-Host "`n[1/4] Kiem tra moi truong ao .venv..." -ForegroundColor Yellow
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "    -> Dang tao moi truong ao tai .venv bang lenh: $pyCmd -m venv .venv"
    & $pyCmd -m venv .venv
    Write-Host "    -> Da tao thanh cong .venv!" -ForegroundColor Green
} else {
    Write-Host "    -> Moi truong ao .venv da ton tai san." -ForegroundColor Green
}

Write-Host "`n[2/4] Nang cap pip trong .venv..." -ForegroundColor Yellow
& .\.venv\Scripts\python.exe -m pip install --upgrade pip

Write-Host "`n[3/4] Cai dat cac thu vien tu requirements.txt..." -ForegroundColor Yellow
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

Write-Host "`n[4/4] Dang ky Jupyter Kernel cho .venv..." -ForegroundColor Yellow
& .\.venv\Scripts\python.exe -m ipykernel install --user --name=ev_charging_ba --display-name="Python (.venv - BA Project)"

Write-Host "`n==============================================================================" -ForegroundColor Cyan
Write-Host "[HOAN TAT] Moi truong .venv da duoc thiet lap thanh cong va tach biet hoan toan!" -ForegroundColor Green
Write-Host "`nDe kich hoat moi truong trong PowerShell, go:"
Write-Host "    .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "==============================================================================" -ForegroundColor Cyan

