@echo off
title Push to GitHub (YB-439/p38Web_Ui)
echo ===============================================================
echo   Pushing p38a MAPK Predictor to GitHub
echo   Repository: https://github.com/YB-439/p38Web_Ui
echo ===============================================================
set "GIT_EXE=C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\TeamFoundation\Team Explorer\Git\cmd\git.exe"
cd /d "%~dp0"
"%GIT_EXE%" push -u origin main
echo.
pause
