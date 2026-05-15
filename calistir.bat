@echo off
echo N-Puzzle Solver baslatiliyor...
python main.py
if errorlevel 1 (
    echo.
    echo HATA: Python bulunamadi. Python 3.8+ yuklu oldugunu dogrulayin.
    pause
)
