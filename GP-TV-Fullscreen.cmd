@echo off
setlocal
set "TVURL=https://gp.18-232-7-146.sslip.io/tv?lang=ar"
set "PROFILE=%LOCALAPPDATA%\GoldenPalace-TV-Kiosk"
set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME%" set "CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
set "EDGE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if not exist "%EDGE%" set "EDGE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
if exist "%CHROME%" (start "Golden Palace TV" "%CHROME%" --user-data-dir="%PROFILE%-Chrome" --kiosk "%TVURL%" --no-first-run --disable-session-crashed-bubble --autoplay-policy=no-user-gesture-required & exit /b 0)
if exist "%EDGE%" (start "Golden Palace TV" "%EDGE%" --user-data-dir="%PROFILE%-Edge" --kiosk "%TVURL%" --edge-kiosk-type=fullscreen --no-first-run --disable-session-crashed-bubble --autoplay-policy=no-user-gesture-required & exit /b 0)
echo Golden Palace TV requires Chrome or Microsoft Edge for automatic kiosk startup.
echo The voice itself is server-generated and is not tied to either browser.
pause
endlocal
