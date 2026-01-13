@echo off
cd /d "%~dp0"

echo Installing node modules...
npm install

echo Starting React client...
npm run dev

pause
