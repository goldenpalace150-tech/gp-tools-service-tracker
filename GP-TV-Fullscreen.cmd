@echo off
setlocal
set "TVURL=https://gp-tv.onrender.com/?lang=ar"
set "PROFILE=%LOCALAPPDATA%\GoldenPalace-TV-Kiosk"
set "EDGE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if not exist "%EDGE%" set "EDGE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
if not exist "%EDGE%" (
  echo Microsoft Edge was not found.
  pause
  exit /b 1
)
start "Golden Palace TV" "%EDGE%" --user-data-dir="%PROFILE%" --kiosk "%TVURL%" --edge-kiosk-type=fullscreen --no-first-run --disable-session-crashed-bubble --autoplay-policy=no-user-gesture-required
endlocal
