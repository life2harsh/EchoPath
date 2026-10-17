@echo off
setlocal
cd /d "%~dp0"
title EchoPath Research
if not exist "%~dp0scripts\windows\Run-EchoPathResearch.ps1" (
  echo ERROR: This file was opened from inside a ZIP, or the folder is incomplete.
  echo Right-click the ZIP, choose "Extract All...", move the folder to C:\EchoPath,
  echo then double-click RUN_ECHOPATH_RESEARCH.bat inside that folder.
  set "ECHOPATH_EXIT=1"
  goto :finish
)
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
  echo Send echopath_research_results.zip from this folder.
) else (
  echo EchoPath research workflow stopped with error code %ECHOPATH_EXIT%.
  echo Send echopath_research_FAILED_logs.zip from this folder, if it exists,
  echo or the files in research\windows\logs.
)
echo.
pause
exit /b %ECHOPATH_EXIT%
