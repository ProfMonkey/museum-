@echo off
setlocal
set "SCRIPT=%TEMP%\WonderAtlas-V42-PublicPreview.ps1"
echo Downloading the Wonder Atlas V42 one-click launcher...
curl.exe -L --fail --silent --show-error "https://raw.githubusercontent.com/ProfMonkey/museum-/feature/v42-unified-exhibit-search-20261029/deploy/start-public-preview.ps1" -o "%SCRIPT%"
if errorlevel 1 (
  echo.
  echo Download failed. Please check your network and try again.
  pause
  exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%"
echo.
pause
