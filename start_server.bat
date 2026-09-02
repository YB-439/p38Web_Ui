@echo off
title p38a MAPK Predictor Web Server
echo ===============================================================
echo   p38a MAPK Activity & Applicability Domain Predictor
echo ===============================================================
echo Activating Conda rdkit_env...
call "C:\Users\drugd\anaconda3\Scripts\activate.bat" rdkit_env
cd /d "G:\Desktop\AI-ML\Predictions"
echo Starting FastAPI Web Server at http://127.0.0.1:8000 ...
python app\run_server.py
pause
