@echo off
REM Build SlackTime as a standalone folder app and install it for auto-start.
REM Uses --onedir (not --onefile) so python3xx.dll lives in a fixed folder,
REM avoiding Application Control / WDAC policies that block DLLs from %TEMP%.

setlocal
cd /d "%~dp0"

echo [1/3] Building SlackTime.exe with PyInstaller...
pyinstaller --noconfirm --onedir --windowed --name SlackTime ^
    --collect-all screeninfo --collect-all pystray slacktime.py
if errorlevel 1 (
    echo Build failed. Is PyInstaller installed?  pip install pyinstaller
    exit /b 1
)

echo [2/3] Installing to %LOCALAPPDATA%\SlackTime ...
set "APPDIR=%LOCALAPPDATA%\SlackTime"
if exist "%APPDIR%" rmdir /s /q "%APPDIR%"
xcopy /e /i /q "dist\SlackTime" "%APPDIR%" >nul

echo [3/3] Creating Startup shortcut (auto-start at login)...
powershell -NoProfile -Command ^
  "$s=[Environment]::GetFolderPath('Startup');" ^
  "$t=Join-Path $env:LOCALAPPDATA 'SlackTime\SlackTime.exe';" ^
  "$w=New-Object -ComObject WScript.Shell;" ^
  "$l=$w.CreateShortcut((Join-Path $s 'SlackTime.lnk'));" ^
  "$l.TargetPath=$t; $l.WorkingDirectory=(Split-Path $t);" ^
  "$l.Description='SlackTime - water and stretch reminder'; $l.Save()"

echo.
echo Done. SlackTime is installed and will start automatically at login.
echo Launching it now...
start "" "%APPDIR%\SlackTime.exe"
endlocal
