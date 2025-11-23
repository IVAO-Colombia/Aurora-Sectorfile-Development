@echo off
rem Build single-file or one-folder exe for the GUI using PyInstaller (Windows).
rem Usage: build.bat [onefile|onedir]
setlocal

rem Move to the directory containing this script so relative paths are stable
cd /d "%~dp0"

rem Default mode
set MODE=onefile

if "%~1"=="" (
  rem keep default
) else (
  if /I "%~1"=="onefile" (
    set MODE=onefile
  ) else if /I "%~1"=="onedir" (
    set MODE=onedir
  ) else (
    echo Usage: %~n0 [onefile^|onedir]
    echo Example: %~n0 onefile
    exit /b 1
  )
)

echo Building in mode: %MODE%
echo Ensuring pyinstaller is installed...
python -m pip install --upgrade pyinstaller || (
  echo Failed to install pyinstaller. Check your Python/venv and network.
  pause
  exit /b 1
)

rem Determine where the Development folder is (current dir or parent)
set "ADDDATA_SOURCE="
if exist "src" (
  set "ADDDATA_SOURCE=src"
) else if exist "..\src" (
  rem use relative path from script location to Development in parent folder
  set "ADDDATA_SOURCE=..\src"
) else (
  echo ERROR: Could not find a Development folder in "%CD%" or its parent.
  echo Please place your Development folder next to this build script or update the script.
  pause
  exit /b
)

set "ADDDATA=%ADDDATA_SOURCE%;src"

rem Adjust the GUI entrypoint filename if different
set "GUI=gui.py"

if "%MODE%"=="onefile" (
  echo Running: pyinstaller --onefile --noconsole --name AuroraSectorfileInstaller --add-data "%ADDDATA%" "%GUI%"
  pyinstaller --onefile --noconsole --name AuroraSectorfileInstaller --add-data "%ADDDATA%" "%GUI%"
) else (
  echo Running: pyinstaller --onedir --noconsole --name AuroraSectorfileInstaller --add-data "%ADDDATA%" "%GUI%"
  pyinstaller --onedir --noconsole --name AuroraSectorfileInstaller --add-data "%ADDDATA%" "%GUI%"
)

if %ERRORLEVEL% NEQ 0 (
  echo PyInstaller failed with error %ERRORLEVEL%.
  pause
  exit /b %ERRORLEVEL%
)

echo Build complete.
if "%MODE%"=="onefile" (
  echo Output: dist\AuroraSectorfileInstaller.exe
) else (
  echo Output: dist\AuroraSectorfileInstaller\ (folder, exe inside)
)
pause
endlocal