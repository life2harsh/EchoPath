@echo off
setlocal
cd /d "%~dp0"
title EchoPath Research
where powershell.exe >nul 2>&1
if errorlevel 1 (
  echo ERROR: Windows PowerShell was not found.
  echo Install or enable Windows PowerShell, then run this file again.
  set "ECHOPATH_EXIT=1"
  goto :finish
)
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\windows\Run-EchoPathResearch.ps1"
set "ECHOPATH_EXIT=%ERRORLEVEL%"
:finish
echo.
if "%ECHOPATH_EXIT%"=="0" (
  echo EchoPath research workflow finished successfully.
) else (
  echo EchoPath research workflow stopped with error code %ECHOPATH_EXIT%.
)
echo Review research\windows\logs for details.
echo.
pause
exit /b %ECHOPATH_EXIT%
