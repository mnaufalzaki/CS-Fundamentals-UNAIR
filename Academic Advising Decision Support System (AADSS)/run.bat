@echo off
rem Menjalankan AADSS di Windows.
cd /d "%~dp0"
python -c "import streamlit,pandas,plotly" >nul 2>&1
if errorlevel 1 (
  echo Dependensi belum tersedia. Jalankan: pip install -r requirements.txt
  pause
  exit /b 1
)
python -m streamlit run app.py --server.address 127.0.0.1
